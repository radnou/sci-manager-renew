import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app, base_url="http://testserver")

def test_rls_isolation():
    # Test that endpoints require authentication
    payload = {
        "id_sci": "test-sci",
        "adresse": "10 rue Test",
        "ville": "Paris",
        "code_postal": "75001",
        "loyer_cc": 1500.0
    }
    response = client.post("/api/v1/biens", json=payload, headers={"Host": "localhost"})
    assert response.status_code == 401  # Unauthorized without token

    # Test with invalid token
    response = client.get("/api/v1/biens", headers={"Authorization": "Bearer invalid", "Host": "localhost"})
    assert response.status_code == 401