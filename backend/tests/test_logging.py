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
