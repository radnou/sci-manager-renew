import os
from typing import Optional

from pydantic import BaseModel, AnyUrl, ValidationError


class Settings(BaseModel):
    supabase_url: AnyUrl
    supabase_key: str
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None


def get_settings() -> Settings:
    """Load settings from environment variables.

    We avoid `BaseSettings` to keep dependencies minimal; pydantic
    ``BaseModel`` still performs basic validation. An optional `.env` loading
    step can be added by users during development (e.g. via ``python-dotenv``)
    or by exporting variables in the shell.
    """

    data: dict = {
        # use local dev instance as a fallback so the backend can start without
        # strictly requiring developers to fill .env when iterating. The tests
        # override the client entirely so this value is irrelevant there.
        "supabase_url": os.getenv("SUPABASE_URL", "http://localhost:54321"),
        # the service role key is required for server operations; leave empty
        # if running tests (fake client) or if using anon key in dev.
        # server-side operations should use the service role key, but in
        # development the anon key is often sufficient for simple reads/writes
        # (RLS will restrict access). fall back to ANON if SERVICE_ROLE is
        # not provided.
        "supabase_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY")
                       or os.getenv("SUPABASE_ANON_KEY", ""),
        "stripe_secret_key": os.getenv("STRIPE_SECRET_KEY"),
        "stripe_publishable_key": os.getenv("STRIPE_PUBLISHABLE_KEY"),
    }
    try:
        return Settings(**data)
    except ValidationError as exc:
        # re-raise with clearer message
        raise RuntimeError(f"configuration error: {exc}")
