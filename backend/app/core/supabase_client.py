from functools import lru_cache

from fastapi import Request
from supabase import Client, ClientOptions, create_client

from .config import settings


def _default_client_options(**extra_headers: str) -> ClientOptions:
    """Build ClientOptions with timeout from settings."""
    timeout_sec = settings.supabase_request_timeout_seconds
    headers = {k: v for k, v in extra_headers.items() if v}
    return ClientOptions(
        postgrest_client_timeout=timeout_sec,
        storage_client_timeout=int(timeout_sec),
        headers=headers,
    )


_test_client = None

@lru_cache
def _get_cached_supabase_anon_client() -> Client:
    return create_client(
        settings.supabase_url,
        settings.supabase_anon_key,
        options=_default_client_options(),
    )

def get_supabase_anon_client() -> Client:
    import sys
    if "pytest" in sys.modules and _test_client is not None:
        return _test_client
    return _get_cached_supabase_anon_client()


@lru_cache
def _get_cached_supabase_service_client() -> Client:
    return create_client(
        settings.supabase_url,
        settings.supabase_service_role_key,
        options=_default_client_options(),
    )

def get_supabase_service_client() -> Client:
    """Service-role client — bypasses RLS. Use ONLY for admin, webhooks, cron."""
    import sys
    if "pytest" in sys.modules and _test_client is not None:
        return _test_client
    return _get_cached_supabase_service_client()


def get_supabase_user_client(request: Request) -> Client:
    """Per-request client using the user's JWT — RLS policies apply.

    Use this for all user-facing data endpoints to enforce row-level security.
    The anon key + user JWT combination ensures Supabase applies RLS policies.
    """
    import sys
    if "pytest" in sys.modules and _test_client is not None:
        return _test_client
    auth_header = request.headers.get("authorization", "")
    token = auth_header.removeprefix("Bearer ").removeprefix("bearer ").strip()
    if not token:
        from .exceptions import AuthenticationError
        raise AuthenticationError("Missing authorization token")

    return create_client(
        settings.supabase_url,
        settings.supabase_anon_key,
        options=_default_client_options(Authorization=f"Bearer {token}"),
    )
