import threading
from time import monotonic

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt.exceptions import PyJWTError

from .config import settings

security = HTTPBearer(auto_error=False)
_JWKS_CACHE_TTL_SECONDS = 300.0
_jwks_cache: dict[str, object] = {"expires_at": 0.0, "keys": []}
_jwks_lock = threading.Lock()


def _raise_unauthorized(detail: str) -> None:
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _get_supabase_jwks() -> list[dict]:
    now = monotonic()

    # Fast path: check cache without lock
    if _jwks_cache["expires_at"] > now:
        return list(_jwks_cache["keys"])

    with _jwks_lock:
        # Re-check after acquiring lock (another thread may have refreshed)
        now = monotonic()
        if _jwks_cache["expires_at"] > now:
            return list(_jwks_cache["keys"])

        jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        response = httpx.get(jwks_url, timeout=settings.supabase_request_timeout_seconds)
        response.raise_for_status()
        payload = response.json()

        keys = payload.get("keys")
        if not isinstance(keys, list):
            raise ValueError("Supabase JWKS response is invalid")

        _jwks_cache["keys"] = keys
        _jwks_cache["expires_at"] = monotonic() + _JWKS_CACHE_TTL_SECONDS
        return list(keys)


def _decode_bearer_token(token: str) -> dict:
    header = jwt.get_unverified_header(token)
    algorithm = header.get("alg", "HS256")

    if algorithm == "HS256":
        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )

    if algorithm not in {"ES256", "RS256"}:
        raise PyJWTError("Unsupported bearer token algorithm")

    key_id = header.get("kid")
    if not isinstance(key_id, str) or not key_id:
        raise PyJWTError("Missing bearer token key id")

    for jwk in _get_supabase_jwks():
        if jwk.get("kid") != key_id:
            continue
        public_key = jwt.PyJWK(jwk).key
        return jwt.decode(
            token,
            public_key,
            algorithms=[algorithm],
            options={"verify_aud": False},
        )

    raise PyJWTError("No matching bearer token key")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    if credentials is None or not credentials.credentials:
        _raise_unauthorized("Missing bearer token")

    token = credentials.credentials

    try:
        payload = _decode_bearer_token(token)
    except (PyJWTError, httpx.HTTPError, ValueError):
        _raise_unauthorized("Invalid bearer token")

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        _raise_unauthorized("Invalid bearer token payload")

    return user_id


async def get_current_admin(
    user_id: str = Depends(get_current_user),
) -> str:
    """Require the current user to be an admin."""
    from .supabase_client import get_supabase_service_client as get_service_client

    client = get_service_client()
    result = client.table("admins").select("user_id").eq("user_id", user_id).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return user_id
