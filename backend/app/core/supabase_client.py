from functools import lru_cache

from fastapi import Request
from supabase import Client, create_client

from .config import settings


@lru_cache
def get_supabase_anon_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_anon_key)


@lru_cache
def get_supabase_service_client() -> Client:
    """Service-role client — bypasses RLS. Use ONLY for admin, webhooks, cron."""
    return create_client(settings.supabase_url, settings.supabase_service_role_key)


def get_supabase_user_client(request: Request) -> Client:
    """Per-request client using the user's JWT — RLS policies apply.

    Use this for all user-facing data endpoints to enforce row-level security.
    The anon key + user JWT combination ensures Supabase applies RLS policies.
    """
    auth_header = request.headers.get("authorization", "")
    token = auth_header.removeprefix("Bearer ").removeprefix("bearer ").strip()
    if not token:
        from .exceptions import AuthenticationError
        raise AuthenticationError("Missing authorization token")

    return create_client(
        settings.supabase_url,
        settings.supabase_anon_key,
        options={"headers": {"Authorization": f"Bearer {token}"}},
    )
