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

    import io
    import json
    import sys

    client = TestClient(app)

    # Capturer stdout
    captured_output = io.StringIO()
    sys.stdout = captured_output

    response = client.get("/health")

    # Restaurer stdout
    sys.stdout = sys.__stdout__

    logs = captured_output.getvalue().split('\n')

    # Vérifier qu'il y a des logs avec request_id
    log_found = False
    for log_line in logs:
        if not log_line.strip():
            continue
        try:
            log_data = json.loads(log_line)
            if 'request_id' in log_data:
                # Vérifier que c'est un UUID valide
                try:
                    uuid.UUID(log_data['request_id'])
                    log_found = True
                    break
                except ValueError:
                    pass
        except json.JSONDecodeError:
            pass

    assert log_found, "No log with valid request_id found"

def test_request_logging_middleware_logs_request_details():
    """Test que les détails de requête sont loggués"""
    from fastapi.testclient import TestClient
    from app.main import app

    import io
    import json
    import sys

    client = TestClient(app)

    # Capturer stdout
    captured_output = io.StringIO()
    sys.stdout = captured_output

    response = client.get("/health")

    # Restaurer stdout
    sys.stdout = sys.__stdout__

    logs = captured_output.getvalue().split('\n')

    # Parser les logs JSON
    request_started_log = None
    request_completed_log = None

    for log_line in logs:
        if not log_line.strip():
            continue
        try:
            log_data = json.loads(log_line)
            if log_data.get("event") == "request_started":
                request_started_log = log_data
            elif log_data.get("event") == "request_completed":
                request_completed_log = log_data
        except json.JSONDecodeError:
            pass

    # Vérifications
    assert request_started_log is not None
    assert request_started_log["method"] == "GET"
    assert request_started_log["path"] == "/health"

    assert request_completed_log is not None
    assert "status_code" in request_completed_log
    assert "duration_ms" in request_completed_log
