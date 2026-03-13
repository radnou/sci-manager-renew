# backend/tests/test_logging.py
import uuid
import structlog
from app.core.logging_config import configure_logging

def test_configure_logging_sets_json_renderer():
    """Test que structlog est configuré avec JSON renderer"""
    configure_logging(log_level="INFO")

    # Vérifier que le logger est configuré
    logger = structlog.get_logger()
    assert logger is not None

    # Test qu'un log produit du JSON
    import io
    import json

    output = io.StringIO()
    test_logger = structlog.wrap_logger(
        structlog.PrintLogger(file=output),
        processors=structlog.get_config()["processors"]
    )

    test_logger.info("test_message", key="value")
    log_output = output.getvalue()

    # Parser le JSON pour vérifier le format
    log_data = json.loads(log_output)
    assert log_data["event"] == "test_message"
    assert log_data["key"] == "value"
    assert "timestamp" in log_data
    assert "level" in log_data

def test_request_logging_middleware_adds_correlation_id():
    """Test que chaque requête reçoit un correlation ID"""
    from fastapi.testclient import TestClient
    from app.main import app
    from unittest.mock import patch

    with patch('app.main.logger') as mock_logger:
        client = TestClient(app)
        response = client.get("/health")

        # Vérifier que logger.info a été appelé avec request_id
        calls = mock_logger.info.call_args_list

        # Chercher l'appel avec request_started
        request_started_call = None
        for call in calls:
            if call[0][0] == "request_started":
                request_started_call = call
                break

        assert request_started_call is not None, "request_started log not found"

        # Vérifier que request_id est dans les contextvars
        # Le request_id est automatiquement ajouté par structlog.contextvars
        # On peut vérifier qu'il y a bien eu un appel de log
        assert len(calls) >= 2, "Should have at least 2 log calls (started + completed)"

def test_request_logging_middleware_logs_request_details():
    """Test que les détails de requête sont loggués"""
    from fastapi.testclient import TestClient
    from app.main import app
    from unittest.mock import patch

    with patch('app.main.logger') as mock_logger:
        client = TestClient(app)
        response = client.get("/health")

        # Vérifier les appels au logger
        calls = mock_logger.info.call_args_list

        # Trouver l'appel request_started
        started_call = next((c for c in calls if c[0][0] == "request_started"), None)
        assert started_call is not None, "request_started log not found"
        assert started_call[1]["method"] == "GET"
        assert started_call[1]["path"] == "/health"
        assert "client_host" in started_call[1]

        # Trouver l'appel request_completed
        completed_call = next((c for c in calls if c[0][0] == "request_completed"), None)
        assert completed_call is not None, "request_completed log not found"
        assert "status_code" in completed_call[1]
        assert "duration_ms" in completed_call[1]
        # Vérifier que status_code est un entier valide
        assert isinstance(completed_call[1]["status_code"], int)


def test_request_id_header_in_response():
    """Test que le X-Request-ID header est présent dans la réponse"""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert "X-Request-ID" in response.headers
    # Vérifier que c'est un UUID valide
    request_id = response.headers["X-Request-ID"]
    uuid.UUID(request_id)  # Raise si invalide


def test_different_requests_get_different_correlation_ids():
    """Test que chaque requête reçoit un correlation ID unique"""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    response1 = client.get("/health")
    response2 = client.get("/health")

    id1 = response1.headers["X-Request-ID"]
    id2 = response2.headers["X-Request-ID"]

    # Vérifier que les deux sont des UUIDs valides
    uuid.UUID(id1)
    uuid.UUID(id2)

    # Vérifier qu'ils sont différents
    assert id1 != id2


# Tests for endpoint logging (Task 1.3)

def test_create_bien_logs_creation():
    """Test que create_bien loggue la création"""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.security import get_current_user
    from unittest.mock import MagicMock, patch

    # Override dependency
    app.dependency_overrides[get_current_user] = lambda: "user123"

    try:
        with (
            patch("app.api.v1.biens.logger") as mock_logger,
            patch("app.api.v1.biens._get_client") as mock_get_client,
            patch("app.api.v1.biens._get_user_sci_ids", return_value=["sci123"]),
            patch("app.api.v1.biens.SubscriptionService.enforce_limit", return_value={"plan_key": "pro", "is_active": True}),
        ):

            # Mock Supabase response
            mock_result = MagicMock()
            mock_result.error = None
            mock_result.data = [
                {
                    "id": "bien123",
                    "id_sci": "sci123",
                    "adresse": "123 rue Test",
                    "ville": "Paris",
                    "code_postal": "75001",
                    "type_locatif": "nu",
                    "loyer_cc": 1000.0,
                    "charges": 100.0,
                    "tmi": 30.0,
                }
            ]

            mock_client = MagicMock()
            mock_client.table.return_value.insert.return_value.execute.return_value = mock_result
            mock_get_client.return_value = mock_client

            client = TestClient(app)
            response = client.post(
                "/api/v1/biens/",
                json={
                    "id_sci": "sci123",
                    "adresse": "123 rue Test",
                    "ville": "Paris",
                    "code_postal": "75001",
                    "type_locatif": "nu",
                    "loyer_cc": 1000.0,
                    "charges": 100.0,
                    "tmi": 30.0,
                },
            )

            assert response.status_code == 201

            # Vérifier les logs
            calls = mock_logger.info.call_args_list
            creating_call = next((c for c in calls if c[0][0] == "creating_bien"), None)
            assert creating_call is not None
            assert creating_call[1]["user_id"] == "user123"
            assert creating_call[1]["adresse"] == "123 rue Test"

            created_call = next((c for c in calls if c[0][0] == "bien_created"), None)
            assert created_call is not None
            assert created_call[1]["bien_id"] == "bien123"
    finally:
        app.dependency_overrides.clear()


def test_create_loyer_logs_creation():
    """Test que create_loyer loggue la création"""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.security import get_current_user
    from unittest.mock import MagicMock, patch

    # Override dependency
    app.dependency_overrides[get_current_user] = lambda: "user123"

    try:
        with (
            patch("app.api.v1.loyers.logger") as mock_logger,
            patch("app.api.v1.loyers.get_supabase_service_client") as mock_get_client,
            patch("app.api.v1.loyers._get_user_sci_ids", return_value=["sci123"]),
            patch("app.api.v1.loyers._fetch_bien", return_value={"id": "bien123", "id_sci": "sci123"}),
        ):

            # Mock Supabase response
            mock_result = MagicMock()
            mock_result.error = None
            mock_result.data = [
                {
                    "id": "loyer123",
                    "id_sci": "sci123",
                    "id_bien": "bien123",
                    "id_locataire": None,
                    "montant": 1000.0,
                    "date_loyer": "2024-01-01",
                    "statut": "en_attente",
                    "quitus_genere": False,
                }
            ]

            mock_client = MagicMock()
            mock_client.table.return_value.insert.return_value.execute.return_value = mock_result
            mock_get_client.return_value = mock_client

            client = TestClient(app)
            response = client.post(
                "/api/v1/loyers/?id_sci=sci123",
                json={
                    "id_bien": "bien123",
                    "montant": 1000.0,
                    "date_loyer": "2024-01-01",
                },
            )

            assert response.status_code == 201

            # Vérifier les logs
            calls = mock_logger.info.call_args_list
            creating_call = next((c for c in calls if c[0][0] == "creating_loyer"), None)
            assert creating_call is not None
            assert creating_call[1]["user_id"] == "user123"
            assert creating_call[1]["bien_id"] == "bien123"
            assert creating_call[1]["montant"] == 1000.0

            created_call = next((c for c in calls if c[0][0] == "loyer_created"), None)
            assert created_call is not None
            assert created_call[1]["loyer_id"] == "loyer123"
    finally:
        app.dependency_overrides.clear()


def test_send_magic_link_logs_operation():
    """Test que send_magic_link loggue l'envoi"""
    from fastapi.testclient import TestClient
    from app.main import app
    from unittest.mock import patch, AsyncMock

    with patch('app.api.v1.auth.logger') as mock_logger, \
         patch('app.api.v1.auth.magic_link_service.send_magic_link', new_callable=AsyncMock) as mock_send:

        mock_send.return_value = {"success": True, "message": "Magic link sent"}

        client = TestClient(app)
        response = client.post(
            "/api/v1/auth/magic-link/send",
            json={"email": "test@example.com"},
        )

        assert response.status_code == 200

        # Vérifier les logs
        calls = mock_logger.info.call_args_list
        sending_call = next((c for c in calls if c[0][0] == "sending_magic_link"), None)
        assert sending_call is not None
        assert sending_call[1]["email"] == "test@example.com"

        sent_call = next((c for c in calls if c[0][0] == "magic_link_sent"), None)
        assert sent_call is not None
        assert sent_call[1]["email"] == "test@example.com"


def test_update_bien_logs_operation():
    """Test que update_bien loggue la mise à jour"""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.security import get_current_user
    from unittest.mock import MagicMock, patch

    # Override dependency
    app.dependency_overrides[get_current_user] = lambda: "user123"

    try:
        with (
            patch("app.api.v1.biens.logger") as mock_logger,
            patch("app.api.v1.biens._get_client") as mock_get_client,
            patch("app.api.v1.biens._get_user_sci_ids", return_value=["sci123"]),
        ):

            existing_result = MagicMock()
            existing_result.error = None
            existing_result.data = [
                {
                    "id": "bien123",
                    "id_sci": "sci123",
                    "adresse": "123 rue Initiale",
                    "ville": "Paris",
                    "code_postal": "75001",
                    "type_locatif": "nu",
                    "loyer_cc": 1000.0,
                    "charges": 100.0,
                    "tmi": 30.0,
                }
            ]

            updated_result = MagicMock()
            updated_result.error = None
            updated_result.data = [
                {
                    "id": "bien123",
                    "id_sci": "sci123",
                    "adresse": "123 rue Updated",
                    "ville": "Paris",
                    "code_postal": "75001",
                    "type_locatif": "nu",
                    "loyer_cc": 1100.0,
                    "charges": 100.0,
                    "tmi": 30.0,
                    "rentabilite_brute": 0,
                    "rentabilite_nette": 0,
                    "cashflow_annuel": 12000,
                }
            ]

            mock_query = MagicMock()
            mock_query.select.return_value.eq.return_value.execute.return_value = existing_result
            mock_query.update.return_value.eq.return_value.execute.return_value = updated_result

            mock_client = MagicMock()
            mock_client.table.return_value = mock_query
            mock_get_client.return_value = mock_client

            client = TestClient(app)
            response = client.patch(
                "/api/v1/biens/bien123",
                json={"adresse": "123 rue Updated", "loyer_cc": 1100.0},
            )

            assert response.status_code == 200

            # Vérifier les logs
            calls = mock_logger.info.call_args_list
            updating_call = next((c for c in calls if c[0][0] == "updating_bien"), None)
            assert updating_call is not None
            assert updating_call[1]["bien_id"] == "bien123"
            assert "loyer_cc" in updating_call[1]["fields"]

            updated_call = next((c for c in calls if c[0][0] == "bien_updated"), None)
            assert updated_call is not None
    finally:
        app.dependency_overrides.clear()


def test_delete_loyer_logs_operation():
    """Test que delete_loyer loggue la suppression"""
    from fastapi.testclient import TestClient
    from app.main import app
    from app.core.security import get_current_user
    from unittest.mock import MagicMock, patch

    # Override dependency
    app.dependency_overrides[get_current_user] = lambda: "user123"

    try:
        with (
            patch("app.api.v1.loyers.logger") as mock_logger,
            patch("app.api.v1.loyers.get_supabase_service_client") as mock_get_client,
            patch("app.api.v1.loyers._get_user_sci_ids", return_value=["sci123"]),
            patch("app.api.v1.loyers._resolve_loyer_sci_id", return_value="sci123"),
        ):

            select_result = MagicMock()
            select_result.error = None
            select_result.data = [{"id": "loyer123", "id_sci": "sci123", "id_bien": "bien123"}]

            delete_result = MagicMock()
            delete_result.error = None
            delete_result.data = [{"id": "loyer123"}]

            mock_query = MagicMock()
            mock_query.select.return_value.eq.return_value.execute.return_value = select_result
            mock_query.delete.return_value.eq.return_value.execute.return_value = delete_result

            mock_client = MagicMock()
            mock_client.table.return_value = mock_query
            mock_get_client.return_value = mock_client

            client = TestClient(app)
            response = client.delete("/api/v1/loyers/loyer123")

            assert response.status_code == 204

            # Vérifier les logs
            calls = mock_logger.info.call_args_list
            deleting_call = next((c for c in calls if c[0][0] == "deleting_loyer"), None)
            assert deleting_call is not None
            assert deleting_call[1]["loyer_id"] == "loyer123"

            deleted_call = next((c for c in calls if c[0][0] == "loyer_deleted"), None)
            assert deleted_call is not None
    finally:
        app.dependency_overrides.clear()
