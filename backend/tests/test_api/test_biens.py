def test_get_biens_requires_auth(client):
    response = client.get("/api/v1/biens/")
    assert response.status_code == 401


def test_get_biens_empty(client, auth_headers):
    response = client.get("/api/v1/biens/", headers=auth_headers)
    assert response.status_code == 200
    assert response.json() == []


def test_create_bien(client, auth_headers):
    payload = {
        "id_sci": "sci-1",
        "adresse": "10 rue Test",
        "ville": "Paris",
        "code_postal": "75001",
        "type_locatif": "nu",
        "loyer_cc": 1500.0,
        "charges": 200.0,
        "tmi": 30.0,
        "prix_acquisition": 300000.0,
    }
    response = client.post("/api/v1/biens/", json=payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["adresse"] == "10 rue Test"
    assert data["rentabilite_brute"] == 6.0
    assert data["rentabilite_nette"] == 5.2


def test_update_and_delete_bien(client, auth_headers):
    payload = {
        "id_sci": "sci-1",
        "adresse": "11 rue Test",
        "ville": "Lyon",
        "code_postal": "69001",
        "type_locatif": "meuble",
        "loyer_cc": 1000.0,
        "charges": 100.0,
        "tmi": 20.0,
        "prix_acquisition": 200000.0,
    }
    created = client.post("/api/v1/biens/", json=payload, headers=auth_headers)
    bien_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/biens/{bien_id}",
        json={"ville": "Marseille", "charges": 150.0},
        headers=auth_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["ville"] == "Marseille"

    deleted = client.delete(f"/api/v1/biens/{bien_id}", headers=auth_headers)
    assert deleted.status_code == 204
