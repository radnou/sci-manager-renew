from __future__ import annotations

import asyncio

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
import base64

import httpx
import jwt
import pytest
from jwt.exceptions import PyJWTError

from app.core import security
from app.core.config import settings


def _make_es256_keypair() -> tuple[bytes, dict[str, str]]:
    private_key = ec.generate_private_key(ec.SECP256R1(), default_backend())
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_numbers = private_key.public_key().public_numbers()

    def encode_coord(value: int) -> str:
        return base64.urlsafe_b64encode(value.to_bytes(32, "big")).rstrip(b"=").decode()

    jwk = {
        "kty": "EC",
        "crv": "P-256",
        "alg": "ES256",
        "use": "sig",
        "kid": "test-key",
        "x": encode_coord(public_numbers.x),
        "y": encode_coord(public_numbers.y),
    }
    return private_pem, jwk


@pytest.fixture(autouse=True)
def _reset_jwks_cache():
    """Reset the JWKS cache and lock before each test."""
    security._jwks_cache["expires_at"] = 0.0
    security._jwks_cache["keys"] = []
    # Replace the lock so tests get a fresh one (avoids cross-test lock state)
    security._jwks_lock = asyncio.Lock()
    yield
    security._jwks_cache["expires_at"] = 0.0
    security._jwks_cache["keys"] = []


@pytest.mark.asyncio
async def test_decode_bearer_token_accepts_hs256():
    token = jwt.encode({"sub": "user-hs"}, settings.supabase_jwt_secret, algorithm="HS256")

    payload = await security._decode_bearer_token(token)

    assert payload["sub"] == "user-hs"


@pytest.mark.asyncio
async def test_decode_bearer_token_accepts_es256(monkeypatch):
    private_pem, jwk = _make_es256_keypair()
    token = jwt.encode(
        {"sub": "user-es"},
        private_pem,
        algorithm="ES256",
        headers={"kid": jwk["kid"]},
    )

    async def fake_get_jwks():
        return [jwk]

    monkeypatch.setattr(security, "_get_supabase_jwks", fake_get_jwks)

    payload = await security._decode_bearer_token(token)

    assert payload["sub"] == "user-es"


@pytest.mark.asyncio
async def test_decode_bearer_token_rejects_missing_matching_key(monkeypatch):
    private_pem, jwk = _make_es256_keypair()
    token = jwt.encode(
        {"sub": "user-es"},
        private_pem,
        algorithm="ES256",
        headers={"kid": jwk["kid"]},
    )

    async def fake_get_jwks():
        return []

    monkeypatch.setattr(security, "_get_supabase_jwks", fake_get_jwks)

    try:
        await security._decode_bearer_token(token)
    except PyJWTError as exc:
        assert "No matching bearer token key" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected PyJWTError for missing JWKS key")


@pytest.mark.asyncio
async def test_get_supabase_jwks_uses_cache(monkeypatch):
    calls = {"count": 0}

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url: str, timeout: float):
            calls["count"] += 1
            assert url == f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
            assert timeout == settings.supabase_request_timeout_seconds
            return httpx.Response(
                200,
                json={"keys": [{"kid": "cached-key"}]},
                request=httpx.Request("GET", url),
            )

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    first = await security._get_supabase_jwks()
    second = await security._get_supabase_jwks()

    assert first == [{"kid": "cached-key"}]
    assert second == [{"kid": "cached-key"}]
    assert calls["count"] == 1


@pytest.mark.asyncio
async def test_get_supabase_jwks_refreshes_after_ttl(monkeypatch):
    """Verify that the cache is refreshed when the TTL expires."""
    from time import monotonic

    calls = {"count": 0}

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url: str, timeout: float):
            calls["count"] += 1
            return httpx.Response(
                200,
                json={"keys": [{"kid": f"key-{calls['count']}"}]},
                request=httpx.Request("GET", url),
            )

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    # First call populates cache
    first = await security._get_supabase_jwks()
    assert first == [{"kid": "key-1"}]
    assert calls["count"] == 1

    # Expire the cache
    security._jwks_cache["expires_at"] = monotonic() - 1.0

    # Second call should refresh
    second = await security._get_supabase_jwks()
    assert second == [{"kid": "key-2"}]
    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_get_supabase_jwks_invalid_response(monkeypatch):
    """Verify ValueError when JWKS response has no 'keys' list."""

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url: str, timeout: float):
            return httpx.Response(
                200,
                json={"not_keys": "invalid"},
                request=httpx.Request("GET", url),
            )

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    with pytest.raises(ValueError, match="invalid"):
        await security._get_supabase_jwks()


@pytest.mark.asyncio
async def test_jwks_lock_prevents_concurrent_fetches(monkeypatch):
    """Verify that concurrent calls only trigger one HTTP fetch."""
    calls = {"count": 0}

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def get(self, url: str, timeout: float):
            calls["count"] += 1
            # Simulate network latency
            await asyncio.sleep(0.05)
            return httpx.Response(
                200,
                json={"keys": [{"kid": "concurrent-key"}]},
                request=httpx.Request("GET", url),
            )

    monkeypatch.setattr(httpx, "AsyncClient", FakeAsyncClient)

    # Launch multiple concurrent fetches
    results = await asyncio.gather(
        security._get_supabase_jwks(),
        security._get_supabase_jwks(),
        security._get_supabase_jwks(),
    )

    # All should get the same result
    for result in results:
        assert result == [{"kid": "concurrent-key"}]

    # But only one HTTP call should have been made
    assert calls["count"] == 1
