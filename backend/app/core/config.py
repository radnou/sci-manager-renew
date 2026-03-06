import json
from enum import Enum
from functools import lru_cache
from typing import Any, Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Environnements supportés"""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    # Environment
    app_name: str = "gerersci"
    app_env: Environment = Environment.DEVELOPMENT
    debug: bool = False

    # Supabase
    supabase_url: str = "http://localhost:54321"
    supabase_anon_key: str = "anon-key-placeholder"
    supabase_service_role_key: str = "service-role-key-placeholder"
    supabase_jwt_secret: str = "test-jwt-secret"
    database_url: str | None = None

    # Stripe
    stripe_secret_key: str = "sk_test_placeholder"
    stripe_webhook_secret: str = "whsec_placeholder"
    stripe_starter_price_id: str = "price_starter_placeholder"
    stripe_pro_price_id: str = "price_pro_placeholder"
    stripe_lifetime_price_id: str = "price_lifetime_placeholder"

    # Email
    resend_api_key: str = "re_placeholder"
    resend_from_email: str = "noreply@gerersci.fr"

    # Frontend
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "testserver", "*.gerersci.fr"]
    frontend_url: str = "http://localhost:5173"

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    log_format: Literal["json", "console"] = "json"

    # Feature Flags
    feature_cerfa_generation: bool = True
    feature_stripe_payments: bool = True
    feature_plan_entitlements_enforcement: Literal["observe", "warn", "enforce"] = "enforce"
    feature_new_checkout_catalog: bool = True
    feature_pdf_render_direct: bool = True
    feature_multi_sci_dashboard_v2: bool = True

    # External service controls
    external_retry_attempts: int = 3
    external_retry_base_delay_ms: int = 200
    stripe_request_timeout_seconds: float = 10.0
    supabase_request_timeout_seconds: float = 10.0
    resend_request_timeout_seconds: float = 10.0
    database_socket_timeout_seconds: float = 2.0

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: Any) -> bool:
        """Parse debug value from string to bool"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            value_lower = value.lower().strip()
            if value_lower in ("true", "1", "yes", "on"):
                return True
            if value_lower in ("false", "0", "no", "off", "release", ""):
                return False
        return False  # Default to False for safety

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

    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, value: Any) -> list[str]:
        if value is None:
            return ["localhost", "127.0.0.1", "testserver", "*.gerersci.fr"]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return []
            if text.startswith("["):
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            return [item.strip() for item in text.split(",") if item.strip()]
        raise TypeError("allowed_hosts must be a list or comma-separated string")

    @model_validator(mode="after")
    def validate_production_environment(self):
        """Valide que la configuration production est sécurisée"""
        if self.app_env == Environment.PRODUCTION:
            # 1. Debug doit être désactivé en production
            if self.debug:
                raise ValueError("Debug mode must be disabled in production")

            # 2. CORS ne doit pas contenir localhost en production
            for origin in self.cors_origins:
                if "localhost" in origin or "127.0.0.1" in origin:
                    raise ValueError("Production CORS must not include localhost or 127.0.0.1")

            # 3. Secrets ne doivent pas être des placeholders en production
            placeholder_keywords = ["placeholder", "test", "example", "demo"]
            secrets_to_check = {
                "STRIPE_SECRET_KEY": self.stripe_secret_key,
                "STRIPE_WEBHOOK_SECRET": self.stripe_webhook_secret,
                "RESEND_API_KEY": self.resend_api_key,
                "SUPABASE_SERVICE_ROLE_KEY": self.supabase_service_role_key,
            }

            for secret_name, secret_value in secrets_to_check.items():
                if any(keyword in secret_value.lower() for keyword in placeholder_keywords):
                    raise ValueError(
                        f"Production secrets must be real values, not placeholders ({secret_name})"
                    )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
