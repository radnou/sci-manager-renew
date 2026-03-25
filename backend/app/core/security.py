import asyncio
from time import monotonic

import httpx
import structlog
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import jwt
from jwt.exceptions import PyJWTError

from .config import settings

logger = structlog.get_logger(__name__)

security = HTTPBearer(auto_error=False)

# _JWKS_CACHE_TTL_SECONDS is intentionally kept as a module-level sentinel so
# the cache dict can be initialised before `settings` is referenced at import time.
# The actual runtime value is read from settings.jwks_cache_ttl_seconds each time
# the cache is refreshed (see _get_supabase_jwks).
_jwks_cache: dict[str, object] = {"expires_at": 0.0, "keys": []}
_jwks_lock = asyncio.Lock()


def _raise_unauthorized() -> None:
    """Raise a generic 401 with a deliberately opaque message.

    All authentication failures use the same user-facing detail so that
    attackers cannot distinguish between a missing token, an invalid token,
    or an unrecognised key.
    """
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication failed",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def _get_supabase_jwks() -> list[dict]:
    now = monotonic()

    # Fast path: read cache without awaiting the lock.
    # dict reads are atomic in CPython so this is safe for a staleness check.
    if _jwks_cache["expires_at"] > now:
        return list(_jwks_cache["keys"])

    async with _jwks_lock:
        # Re-check after acquiring lock (another coroutine may have refreshed).
        now = monotonic()
        if _jwks_cache["expires_at"] > now:
            return list(_jwks_cache["keys"])

        jwks_url = f"{settings.supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
        async with httpx.AsyncClient() as client:
            response = await client.get(
                jwks_url, timeout=settings.supabase_request_timeout_seconds
            )
        response.raise_for_status()
        payload = response.json()

        keys = payload.get("keys")
        if not isinstance(keys, list):
            raise ValueError("Supabase JWKS response is invalid")

        _jwks_cache["keys"] = keys
        # Use the configurable TTL from settings (default 600 s / 10 min).
        _jwks_cache["expires_at"] = monotonic() + settings.jwks_cache_ttl_seconds
        return list(keys)


async def _decode_bearer_token(token: str) -> dict:
    header = jwt.get_unverified_header(token)
    algorithm = header.get("alg", "HS256")

    if algorithm == "HS256":
        return jwt.decode(
            token,
            settings.supabase_jwt_secret,
            algorithms=["HS256"],
            options={"verify_aud": True},
            audience="authenticated",
        )

    if algorithm not in {"ES256", "RS256"}:
        raise PyJWTError("Unsupported bearer token algorithm")

    key_id = header.get("kid")
    if not isinstance(key_id, str) or not key_id:
        raise PyJWTError("Missing bearer token key id")

    for jwk in await _get_supabase_jwks():
        if jwk.get("kid") != key_id:
            continue
        public_key = jwt.PyJWK(jwk).key
        return jwt.decode(
            token,
            public_key,
            algorithms=[algorithm],
            options={"verify_aud": True},
            audience="authenticated",
        )

    raise PyJWTError("No matching bearer token key")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    if credentials is None or not credentials.credentials:
        logger.debug("auth.missing_token")
        _raise_unauthorized()

    token = credentials.credentials

    try:
        payload = await _decode_bearer_token(token)
    except PyJWTError as exc:
        logger.debug("auth.invalid_token", jwt_error=str(exc))
        _raise_unauthorized()
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("auth.jwks_fetch_error", error=str(exc))
        _raise_unauthorized()

    user_id = payload.get("sub")
    if not isinstance(user_id, str) or not user_id:
        logger.debug("auth.missing_sub_claim")
        _raise_unauthorized()

    return user_id


async def get_current_admin(
    user_id: str = Depends(get_current_user),
) -> str:
    """Require the current user to be an admin (via admins table)."""
    from .supabase_client import get_supabase_service_client as get_service_client

    client = get_service_client()
    result = client.table("admins").select("user_id").eq("user_id", user_id).execute()

    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return user_id


def verify_admin_secret(request: Request) -> None:
    """Verify admin secret from X-Admin-Key header only.

    Query-parameter delivery (?secret= / ?key=) has been removed because secrets
    in URLs are logged by load balancers, proxies, and browser history.
    Uses hmac.compare_digest for timing-safe comparison.
    """
    import hmac

    if not settings.admin_secret_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin not configured",
        )

    # Warn and reject if a caller still tries the old query-param approach.
    if request.query_params.get("secret") or request.query_params.get("key"):
        logger.warning(
            "admin.deprecated_query_param_secret",
            path=str(request.url.path),
            message=(
                "Admin secret via query params (?secret= / ?key=) is no longer supported. "
                "Use the X-Admin-Key header instead."
            ),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin key",
        )

    key = request.headers.get("X-Admin-Key")
    if not key or not hmac.compare_digest(key, settings.admin_secret_key):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin key",
        )
