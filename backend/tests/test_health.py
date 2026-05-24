# backend/tests/test_health.py
import pytest
from fastapi.testclient import TestClient
from app.main import app


def test_liveness_probe_returns_200():
    """Test que /health/live retourne toujours 200"""
    client = TestClient(app)
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_readiness_probe_checks_all_services():
    """Test que /health/ready vérifie tous les services"""
    client = TestClient(app)
    response = client.get("/health/ready")

    # Peut retourner 200 (ready) ou 503 (not ready)
    assert response.status_code in [200, 503]

    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "summary" in data
    assert "timestamp" in data

    # Vérifier que tous les services sont vérifiés
    checks = data["checks"]
    assert "database" in checks
    assert "supabase_storage" in checks
    assert "stripe" in checks
    assert "resend" in checks

    # Chaque check doit avoir un champ "healthy"
    for service_name, check_result in checks.items():
        assert "healthy" in check_result
        assert isinstance(check_result["healthy"], bool)

    summary = data["summary"]
    assert "critical_services" in summary
    assert "ready_for_traffic" in summary


def test_readiness_returns_503_when_service_down():
    """Test que /health/ready retourne 503 si un service est down"""
    from unittest.mock import patch, AsyncMock

    client = TestClient(app)

    # Simuler une DB down
    with patch('app.api.v1.health._check_database', new_callable=AsyncMock) as mock_db:
        mock_db.return_value = {"healthy": False, "error": "Connection refused"}

        response = client.get("/health/ready")

        assert response.status_code == 503
        assert response.json()["status"] == "not_ready"
        assert response.json()["checks"]["database"]["healthy"] is False
        assert "database" in response.json()["summary"]["critical_unhealthy"]


def test_readiness_returns_200_when_only_non_critical_service_is_unhealthy():
    from unittest.mock import patch, AsyncMock

    client = TestClient(app)

    with (
        patch("app.api.v1.health._check_database", new_callable=AsyncMock) as mock_db,
        patch("app.api.v1.health._check_supabase_storage", new_callable=AsyncMock) as mock_storage,
        patch("app.api.v1.health._check_stripe", new_callable=AsyncMock) as mock_stripe,
        patch("app.api.v1.health._check_resend", new_callable=AsyncMock) as mock_resend,
    ):
        mock_db.return_value = {"healthy": True}
        mock_storage.return_value = {"healthy": True}
        mock_stripe.return_value = {"healthy": True}
        mock_resend.return_value = {"healthy": False, "error": "invalid resend key format"}

        response = client.get("/health/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["summary"]["ready_for_traffic"] is True
    assert payload["summary"]["unhealthy_services"] == ["resend"]


@pytest.mark.asyncio
async def test_database_health_check_queries_database():
    """Test que le health check DB fait une vraie requête"""
    from app.api.v1.health import _check_database

    result = await _check_database()

    # Si la DB est accessible
    if result["healthy"]:
        # Vérifier que latency_ms est présent ou pas d'erreur
        assert "latency_ms" in result or "error" not in result
    else:
        # Si la DB est inaccessible
        assert "error" in result


@pytest.mark.asyncio
async def test_storage_health_check_verifies_bucket():
    """Test que le health check Storage vérifie le bucket"""
    from app.api.v1.health import _check_supabase_storage

    result = await _check_supabase_storage()

    # Doit retourner healthy (True ou False) et éventuellement une erreur
    assert "healthy" in result
    assert isinstance(result["healthy"], bool)


@pytest.mark.asyncio
async def test_stripe_health_check_validates_api_key():
    """Test que le health check Stripe valide la clé API"""
    from app.api.v1.health import _check_stripe

    result = await _check_stripe()

    # Doit retourner healthy (True ou False)
    assert "healthy" in result
    assert isinstance(result["healthy"], bool)


@pytest.mark.asyncio
async def test_resend_health_check_validates_api_key():
    """Test que le health check Resend valide la clé API"""
    from app.api.v1.health import _check_resend

    result = await _check_resend()

    # Doit retourner healthy (True ou False)
    assert "healthy" in result
    assert isinstance(result["healthy"], bool)


# ── Additional coverage tests ─────────────────────────────────────────────


def test_simple_health_endpoint():
    """Test /health returns ok."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_stripe_check_live_key(monkeypatch):
    """Stripe check with sk_live key returns healthy + mode live."""
    from app.core.config import settings
    from app.api.v1.health import _check_stripe
    from unittest.mock import patch

    with patch("app.api.v1.health.settings") as mock_settings, \
         patch("app.core.entitlements.settings", mock_settings):
        mock_settings.stripe_secret_key = "sk_live_abc123"
        mock_settings.stripe_starter_price_id = "price_starter_month"
        mock_settings.stripe_starter_annual_price_id = "price_starter_year"
        mock_settings.stripe_pro_price_id = "price_pro_month"
        mock_settings.stripe_pro_annual_price_id = "price_pro_year"
        mock_settings.stripe_cabinet_price_id = "price_cabinet_month"
        mock_settings.stripe_cabinet_annual_price_id = "price_cabinet_year"
        mock_settings.stripe_gestion_monthly_price_id = None
        mock_settings.stripe_gestion_annual_price_id = None
        mock_settings.stripe_pilotage_monthly_price_id = None
        mock_settings.stripe_pilotage_annual_price_id = None
        mock_settings.stripe_fondateur_price_id = None
        mock_settings.stripe_lifetime_price_id = None
        with patch("app.api.v1.health.stripe.Price.retrieve_async", return_value={"active": True}) as retrieve:
            result = await _check_stripe()
    assert retrieve.call_count == 6
    assert result["healthy"] is True
    assert result["mode"] == "live"
    assert result["validated_price_count"] == 6


@pytest.mark.asyncio
async def test_stripe_check_invalid_key(monkeypatch):
    """Stripe check with invalid key format returns unhealthy."""
    from app.core.config import settings
    from app.api.v1.health import _check_stripe

    monkeypatch.setattr(settings, "stripe_secret_key", "rk_invalid_format")
    result = await _check_stripe()
    assert result["healthy"] is False
    assert "invalid stripe key format" in result["error"]


@pytest.mark.asyncio
async def test_stripe_check_missing_key(monkeypatch):
    """Stripe check with no key returns unhealthy."""
    from app.core.config import settings
    from app.api.v1.health import _check_stripe

    monkeypatch.setattr(settings, "stripe_secret_key", "")
    result = await _check_stripe()
    assert result["healthy"] is False
    assert "missing" in result["error"]


@pytest.mark.asyncio
async def test_stripe_check_detects_invalid_price_id(monkeypatch):
    """Stripe readiness fails when one configured price id cannot be retrieved."""
    from app.core.config import settings
    from app.api.v1.health import _check_stripe
    from app.core.entitlements import PlanKey
    from unittest.mock import patch

    def mock_resolve(plan_key, billing_period="month"):
        mapping = {
            (PlanKey.STARTER, "month"): "price_starter_month",
            (PlanKey.STARTER, "year"): "price_starter_year",
            (PlanKey.PRO, "month"): "price_pro_month",
            (PlanKey.PRO, "year"): "price_pro_year",
            (PlanKey.CABINET, "month"): "price_cabinet_month",
            (PlanKey.CABINET, "year"): "price_cabinet_year",
        }
        return mapping.get((plan_key, billing_period))

    monkeypatch.setattr(settings, "stripe_secret_key", "sk_live_abc123")
    with patch("app.api.v1.health.resolve_price_id_for_plan", side_effect=mock_resolve):
        async def retrieve(price_id: str):
            if price_id == "price_starter_month":
                raise Exception("No such price")
            return {"active": True}

        with patch("app.api.v1.health.stripe.Price.retrieve_async", side_effect=retrieve):
            result = await _check_stripe()

    assert result["healthy"] is False
    assert result["error"] == "stripe checkout catalog invalid"
    assert result["invalid_price_ids"] == ["starter_monthly"]
    assert result["inactive_price_ids"] == []


@pytest.mark.asyncio
async def test_resend_check_invalid_key(monkeypatch):
    """Resend check with invalid key format returns unhealthy."""
    from app.core.config import settings
    from app.api.v1.health import _check_resend

    monkeypatch.setattr(settings, "resend_api_key", "invalid_key")
    result = await _check_resend()
    assert result["healthy"] is False
    assert "invalid resend key format" in result["error"]


@pytest.mark.asyncio
async def test_resend_check_valid_key(monkeypatch):
    """Resend check with re_ prefixed key returns healthy."""
    from app.core.config import settings
    from app.api.v1.health import _check_resend

    monkeypatch.setattr(settings, "resend_api_key", "re_valid_key_123")
    result = await _check_resend()
    assert result["healthy"] is True


def test_database_socket_check_success():
    """_check_database_socket returns healthy when socket connects."""
    from unittest.mock import patch, MagicMock
    from app.api.v1.health import _check_database_socket

    with patch("app.api.v1.health.socket.create_connection") as mock_conn:
        mock_conn.return_value.__enter__ = MagicMock()
        mock_conn.return_value.__exit__ = MagicMock(return_value=False)
        result = _check_database_socket("postgresql://myhost:5432/mydb")
    assert result["healthy"] is True
    assert "latency_ms" in result
    assert result["mode"] == "postgres_socket"


def test_database_socket_check_failure():
    """_check_database_socket returns unhealthy on connection error."""
    from unittest.mock import patch
    from app.api.v1.health import _check_database_socket

    with patch("app.api.v1.health.socket.create_connection", side_effect=OSError("Connection refused")):
        result = _check_database_socket("postgresql://myhost:5432/mydb")
    assert result["healthy"] is False
    assert "Connection refused" in result["error"]


def test_database_socket_check_missing_host():
    """_check_database_socket returns unhealthy when host is missing."""
    from app.api.v1.health import _check_database_socket

    result = _check_database_socket("postgresql:///mydb")
    assert result["healthy"] is False
    assert "missing host" in result["error"]


def test_database_socket_check_default_port():
    """_check_database_socket uses default port 5432 when not specified."""
    from unittest.mock import patch, MagicMock
    from app.api.v1.health import _check_database_socket

    with patch("app.api.v1.health.socket.create_connection") as mock_conn:
        mock_conn.return_value.__enter__ = MagicMock()
        mock_conn.return_value.__exit__ = MagicMock(return_value=False)
        result = _check_database_socket("postgresql://myhost/mydb")
    assert result["healthy"] is True
    # Verify it used port 5432
    mock_conn.assert_called_once()
    call_args = mock_conn.call_args[0][0]
    assert call_args == ("myhost", 5432)


def test_readiness_degraded_with_degraded_services():
    """Readiness returns 'degraded' when a service has degraded flag."""
    from unittest.mock import patch, AsyncMock

    client = TestClient(app)
    with (
        patch("app.api.v1.health._check_database", new_callable=AsyncMock) as mock_db,
        patch("app.api.v1.health._check_supabase_storage", new_callable=AsyncMock) as mock_storage,
        patch("app.api.v1.health._check_stripe", new_callable=AsyncMock) as mock_stripe,
        patch("app.api.v1.health._check_resend", new_callable=AsyncMock) as mock_resend,
    ):
        mock_db.return_value = {"healthy": True, "degraded": True, "warning": "fallback mode"}
        mock_storage.return_value = {"healthy": True}
        mock_stripe.return_value = {"healthy": True}
        mock_resend.return_value = {"healthy": True}

        response = client.get("/health/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "degraded"
    assert "database" in payload["summary"]["degraded_services"]


def test_readiness_all_healthy():
    """Readiness returns 'ready' when all services are healthy."""
    from unittest.mock import patch, AsyncMock

    client = TestClient(app)
    with (
        patch("app.api.v1.health._check_database", new_callable=AsyncMock) as mock_db,
        patch("app.api.v1.health._check_supabase_storage", new_callable=AsyncMock) as mock_storage,
        patch("app.api.v1.health._check_stripe", new_callable=AsyncMock) as mock_stripe,
        patch("app.api.v1.health._check_resend", new_callable=AsyncMock) as mock_resend,
    ):
        mock_db.return_value = {"healthy": True}
        mock_storage.return_value = {"healthy": True}
        mock_stripe.return_value = {"healthy": True}
        mock_resend.return_value = {"healthy": True}

        response = client.get("/health/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["summary"]["ready_for_traffic"] is True
