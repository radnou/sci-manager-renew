def test_get_locataires_requires_auth(client):
    response = client.get("/api/v1/locataires/")
    assert response.status_code == 401


def test_create_and_filter_locataires(client, auth_headers):
    bien_payload = {
        "id_sci": "sci-1",
        "adresse": "10 rue Locataire",
        "ville": "Paris",
        "code_postal": "75001",
        "type_locatif": "nu",
        "loyer_cc": 1200.0,
        "charges": 100.0,
        "tmi": 30.0,
    }
    bien_created = client.post("/api/v1/biens/", json=bien_payload, headers=auth_headers)
    assert bien_created.status_code == 201
    bien_id = bien_created.json()["id"]

    create_response = client.post(
        "/api/v1/locataires/",
        json={
            "id_bien": bien_id,
            "nom": "Jean Martin",
            "email": "jean.martin@example.com",
            "date_debut": "2026-01-15",
        },
        headers=auth_headers,
    )
    assert create_response.status_code == 201
    assert create_response.json()["nom"] == "Jean Martin"
    assert create_response.json()["id_sci"] == "sci-1"

    filtered = client.get(f"/api/v1/locataires/?id_bien={bien_id}", headers=auth_headers)
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1
    assert filtered.json()[0]["nom"] == "Jean Martin"


def test_update_and_delete_locataire(client, auth_headers):
    bien_payload = {
        "id_sci": "sci-1",
        "adresse": "11 rue Bail",
        "ville": "Lyon",
        "code_postal": "69001",
        "type_locatif": "meuble",
        "loyer_cc": 950.0,
        "charges": 80.0,
        "tmi": 20.0,
    }
    bien_created = client.post("/api/v1/biens/", json=bien_payload, headers=auth_headers)
    assert bien_created.status_code == 201
    bien_id = bien_created.json()["id"]

    created = client.post(
        "/api/v1/locataires/",
        json={
            "id_bien": bien_id,
            "nom": "Alice Bernard",
            "email": "alice@example.com",
            "date_debut": "2026-02-01",
        },
        headers=auth_headers,
    )
    assert created.status_code == 201
    locataire_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/locataires/{locataire_id}",
        json={"email": "alice.bernard@example.com", "date_fin": "2026-12-31"},
        headers=auth_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["email"] == "alice.bernard@example.com"
    assert updated.json()["date_fin"] == "2026-12-31"

    deleted = client.delete(f"/api/v1/locataires/{locataire_id}", headers=auth_headers)
    assert deleted.status_code == 204


def test_create_locataire_rejects_invalid_dates(client, auth_headers):
    bien_payload = {
        "id_sci": "sci-1",
        "adresse": "12 rue Bail",
        "ville": "Marseille",
        "code_postal": "13001",
        "type_locatif": "nu",
        "loyer_cc": 900.0,
        "charges": 50.0,
        "tmi": 20.0,
    }
    bien_created = client.post("/api/v1/biens/", json=bien_payload, headers=auth_headers)
    assert bien_created.status_code == 201
    bien_id = bien_created.json()["id"]

    response = client.post(
        "/api/v1/locataires/",
        json={
            "id_bien": bien_id,
            "nom": "Bail incohérent",
            "date_debut": "2026-05-01",
            "date_fin": "2026-04-01",
        },
        headers=auth_headers,
    )
    assert response.status_code == 422
