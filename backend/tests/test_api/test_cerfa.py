from app.core.config import settings


def test_generate_cerfa_2044(client, auth_headers):
    payload = {
        "annee": 2025,
        "total_revenus": 24000.0,
        "total_charges": 7000.0,
    }

    response = client.post("/api/v1/cerfa/2044", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["formulaire"] == "cerfa_2044"
    assert data["resultat_fiscal"] == 17000.0


def test_generate_cerfa_2044_disabled(client, auth_headers, monkeypatch):
    monkeypatch.setattr(settings, "feature_cerfa_generation", False)

    payload = {
        "annee": 2025,
        "total_revenus": 24000.0,
        "total_charges": 7000.0,
    }

    response = client.post("/api/v1/cerfa/2044", json=payload, headers=auth_headers)
    assert response.status_code == 503
    data = response.json()
    assert data["code"] == "feature_disabled"
    assert data["details"]["flag"] == "feature_cerfa_generation"
