from functools import lru_cache

from supabase import Client, create_client

from .config import settings


@lru_cache
def get_supabase_anon_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_anon_key)


@lru_cache
def get_supabase_service_client() -> Client:
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
