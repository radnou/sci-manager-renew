from typing import Optional

from supabase import Client, create_client

from .config import get_settings

_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Return a cached Supabase client initialized with service role key.

    Uses settings from environment via ``app.core.config``. Calling multiple
    times returns the same instance which is safe for reuse.
    """

    global _client
    if _client is None:
        settings = get_settings()
        # use service role key on the server side so we can bypass RLS when
        # necessary and perform inserts/updates.
        _client = create_client(str(settings.supabase_url), settings.supabase_key)
    return _client
