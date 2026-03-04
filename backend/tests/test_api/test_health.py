def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_docs_available(client):
    response = client.get("/docs")
    assert response.status_code == 200
    assert "Swagger UI" in response.text
