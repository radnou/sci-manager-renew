from app.services.loyers_service import healthcheck


def test_loyers_service_healthcheck():
    assert healthcheck() == {"status": "ok"}
