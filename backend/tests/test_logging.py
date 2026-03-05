# backend/tests/test_logging.py
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
