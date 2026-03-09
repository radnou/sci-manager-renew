# backend/tests/test_config.py
import os
import pytest
from pydantic import ValidationError


def test_development_environment_allows_debug(monkeypatch):
    """Test que le mode development permet debug=True"""
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("DEBUG", "true")

    # Doit passer en development
    from app.core.config import Settings, Environment

    settings = Settings()
    assert settings.app_env == Environment.DEVELOPMENT
    assert settings.debug is True


def test_production_environment_forbids_debug(monkeypatch):
    """Test que le mode production interdit debug=True"""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("CORS_ORIGINS", '["https://gerersci.fr"]')
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_real_key_example")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_real_secret")
    monkeypatch.setenv("RESEND_API_KEY", "re_real_key_example")

    # Doit échouer en production
    from app.core.config import Settings

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    assert "Debug mode must be disabled in production" in str(exc_info.value)


def test_production_environment_forbids_localhost_cors(monkeypatch):
    """Test que le mode production interdit localhost dans CORS"""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("CORS_ORIGINS", '["http://localhost:3000"]')
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_real_key_example")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_real_secret")
    monkeypatch.setenv("RESEND_API_KEY", "re_real_key_example")

    from app.core.config import Settings

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    assert "Production CORS must not include localhost" in str(exc_info.value)


def test_production_environment_forbids_placeholder_secrets(monkeypatch):
    """Test que le mode production interdit les placeholders"""
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("CORS_ORIGINS", '["https://gerersci.fr"]')
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_placeholder")

    from app.core.config import Settings

    with pytest.raises(ValidationError) as exc_info:
        Settings()

    assert "Production secrets must be real values" in str(exc_info.value)


def test_feature_flags_are_configurable(monkeypatch):
    """Test que les feature flags sont configurables"""
    monkeypatch.setenv("FEATURE_CERFA_GENERATION", "false")
    monkeypatch.setenv("FEATURE_STRIPE_PAYMENTS", "true")
    monkeypatch.setenv("FEATURE_PLAN_ENTITLEMENTS_ENFORCEMENT", "warn")

    from app.core.config import Settings

    settings = Settings()

    assert settings.feature_cerfa_generation is False
    assert settings.feature_stripe_payments is True
    assert settings.feature_plan_entitlements_enforcement == "warn"


def test_staging_environment_allows_test_secrets(monkeypatch):
    """Test que le mode staging permet les secrets de test"""
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("DEBUG", "false")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_staging_key")

    from app.core.config import Settings

    settings = Settings()
    assert settings.stripe_secret_key == "sk_test_staging_key"


def test_local_env_file_overrides_base_env(tmp_path, monkeypatch):
    """Test que .env.local surcharge .env en developpement local"""
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("SUPABASE_JWT_SECRET", raising=False)

    (tmp_path / ".env").write_text("SUPABASE_JWT_SECRET=base-secret\n", encoding="utf-8")
    (tmp_path / ".env.local").write_text("SUPABASE_JWT_SECRET=local-secret\n", encoding="utf-8")

    from app.core.config import Settings

    settings = Settings()
    assert settings.supabase_jwt_secret == "local-secret"


def test_env_file_cors_origins_json_like_string_is_accepted(tmp_path, monkeypatch):
    """Test que le format CORS_ORIGINS du .env local est accepté au boot."""
    monkeypatch.chdir(tmp_path)

    (tmp_path / ".env").write_text(
        'CORS_ORIGINS=["http://localhost:5173"]\nALLOWED_HOSTS=["localhost","127.0.0.1"]\n',
        encoding="utf-8",
    )

    from app.core.config import Settings

    settings = Settings()
    assert settings.cors_origins == ["http://localhost:5173"]
    assert settings.allowed_hosts == ["localhost", "127.0.0.1"]
