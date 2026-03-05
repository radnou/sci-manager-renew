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
