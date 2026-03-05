import json
from functools import lru_cache
from typing import Any, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    supabase_url: str = "http://localhost:54321"
    supabase_anon_key: str = "anon-key-placeholder"
    supabase_service_role_key: str = "service-role-key-placeholder"
    supabase_jwt_secret: str = "test-jwt-secret"
    database_url: str = "postgresql://postgres:postgres@localhost:5432/postgres"
    stripe_secret_key: str = "sk_test_placeholder"
    stripe_webhook_secret: str = "whsec_placeholder"
    stripe_starter_price_id: str = "price_1T7MW5BCxd3SKdGJP2xjawrj"
    stripe_pro_price_id: str = "price_1T7MW6BCxd3SKdGJKzcNqdkJ"
    stripe_lifetime_price_id: str = "price_1T7MW7BCxd3SKdGJVrHWprJ8"
    resend_api_key: str = "re_placeholder"
    resend_from_email: str = "noreply@scimanager.fr"
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    frontend_url: str = "http://localhost:5173"

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "console"] = "json"
    app_name: str = "sci-manager"
    app_env: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: Any) -> list[str]:
        if value is None:
            return ["http://localhost:5173", "http://127.0.0.1:5173"]
        if isinstance(value, list):
            return [str(item) for item in value]
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            if text.startswith("["):
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return [str(item) for item in parsed]
            return [item.strip() for item in text.split(",") if item.strip()]
        raise TypeError("cors_origins must be a list or comma-separated string")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
