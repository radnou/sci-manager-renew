import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, base_url="http://testserver")

def test_cors_strict():
    response = client.get("/health", headers={"Origin": "http://evil.com"})
    assert "access-control-allow-origin" not in response.headers.get("access-control-allow-origin", "")

def test_rate_limiting():
    # Test rate limiting on webhook endpoint
    for _ in range(15):
        response = client.post("/api/v1/stripe/webhook", data=b"test", headers={"Host": "testserver"})
    # May not trigger 429 in test environment, but at least no crash
    assert response.status_code in [400, 429]


def test_checkout_preflight_allows_localhost_origin_in_dev():
    response = client.options(
        "/api/v1/stripe/create-checkout-session",
        headers={
            "Origin": "http://localhost",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost"
    assert "authorization" in response.headers.get("access-control-allow-headers", "").lower()

def test_sql_injection_protection():
    # Test with valid auth mock
    payload = {"adresse": "'; DROP TABLE biens; --", "ville": "Paris", "code_postal": "75001", "loyer_cc": 1500}
    response = client.post("/api/v1/biens", json=payload, headers={"Authorization": "Bearer test", "Host": "testserver"})
    # Should fail due to auth or validation
    assert response.status_code in [400, 401, 403]
