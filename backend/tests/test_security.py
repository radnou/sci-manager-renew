from __future__ import annotations

import json

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
import base64

import jwt
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


def test_decode_bearer_token_accepts_hs256():
    token = jwt.encode({"sub": "user-hs"}, settings.supabase_jwt_secret, algorithm="HS256")

    payload = security._decode_bearer_token(token)

    assert payload["sub"] == "user-hs"


def test_decode_bearer_token_accepts_es256(monkeypatch):
    private_pem, jwk = _make_es256_keypair()
    token = jwt.encode(
        {"sub": "user-es"},
        private_pem,
        algorithm="ES256",
        headers={"kid": jwk["kid"]},
    )

    monkeypatch.setattr(security, "_get_supabase_jwks", lambda: [jwk])

    payload = security._decode_bearer_token(token)

    assert payload["sub"] == "user-es"


def test_decode_bearer_token_rejects_missing_matching_key(monkeypatch):
    private_pem, jwk = _make_es256_keypair()
    token = jwt.encode(
        {"sub": "user-es"},
        private_pem,
        algorithm="ES256",
        headers={"kid": jwk["kid"]},
    )

    monkeypatch.setattr(security, "_get_supabase_jwks", lambda: [])

    try:
        security._decode_bearer_token(token)
    except PyJWTError as exc:
        assert "No matching bearer token key" in str(exc)
    else:  # pragma: no cover - defensive
        raise AssertionError("Expected PyJWTError for missing JWKS key")


def test_get_supabase_jwks_uses_cache(monkeypatch):
    security._jwks_cache["expires_at"] = 0.0
    security._jwks_cache["keys"] = []
    calls = {"count": 0}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self, *_args, **_kwargs):
            return json.dumps({"keys": [{"kid": "cached-key"}]}).encode()

    def fake_urlopen(url: str, timeout: float):
        calls["count"] += 1
        assert url == f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        assert timeout == settings.supabase_request_timeout_seconds
        return FakeResponse()

    monkeypatch.setattr(security, "urlopen", fake_urlopen)

    first = security._get_supabase_jwks()
    second = security._get_supabase_jwks()

    assert first == [{"kid": "cached-key"}]
    assert second == [{"kid": "cached-key"}]
    assert calls["count"] == 1
