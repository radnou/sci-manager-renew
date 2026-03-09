def test_get_loyers_requires_auth(client):
    response = client.get("/api/v1/loyers/")
    assert response.status_code == 401


def test_create_and_filter_loyers(client, auth_headers):
    bien_payload = {
        "id_sci": "sci-1",
        "adresse": "10 rue Loyer",
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

    payload_1 = {
        "id_bien": bien_id,
        "id_locataire": "loc-1",
        "date_loyer": "2026-01-01",
        "montant": 1200.0,
        "statut": "en_attente",
        "quitus_genere": False,
    }
    payload_2 = {
        "id_bien": bien_id,
        "id_locataire": "loc-1",
        "date_loyer": "2026-03-01",
        "montant": 1200.0,
        "statut": "paye",
        "quitus_genere": True,
    }

    create_1 = client.post("/api/v1/loyers/?id_sci=sci-1", json=payload_1, headers=auth_headers)
    create_2 = client.post("/api/v1/loyers/?id_sci=sci-1", json=payload_2, headers=auth_headers)
    assert create_1.status_code == 201
    assert create_2.status_code == 201

    filtered = client.get(
        "/api/v1/loyers/?date_from=2026-02-01&date_to=2026-04-01",
        headers=auth_headers,
    )
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1
    assert filtered.json()[0]["date_loyer"] == "2026-03-01"


def test_update_and_delete_loyer(client, auth_headers):
    bien_payload = {
        "id_sci": "sci-1",
        "adresse": "11 rue Loyer",
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

    payload = {
        "id_bien": bien_id,
        "id_locataire": "loc-2",
        "date_loyer": "2026-02-01",
        "montant": 950.0,
        "statut": "en_attente",
        "quitus_genere": False,
    }
    created = client.post("/api/v1/loyers/?id_sci=sci-1", json=payload, headers=auth_headers)
    loyer_id = created.json()["id"]

    updated = client.patch(
        f"/api/v1/loyers/{loyer_id}",
        json={"statut": "paye", "quitus_genere": True},
        headers=auth_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["statut"] == "paye"

    deleted = client.delete(f"/api/v1/loyers/{loyer_id}", headers=auth_headers)
    assert deleted.status_code == 204


def test_list_loyers_rejects_invalid_date_range(client, auth_headers):
    response = client.get(
        "/api/v1/loyers/?date_from=2026-04-01&date_to=2026-02-01",
        headers=auth_headers,
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "validation_error"
    assert payload["error"] == "date_from must be earlier than or equal to date_to"


def test_update_loyer_rejects_empty_payload(client, auth_headers):
    bien_payload = {
        "id_sci": "sci-1",
        "adresse": "12 rue Loyer",
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

    created = client.post(
        "/api/v1/loyers/?id_sci=sci-1",
        json={
            "id_bien": bien_id,
            "id_locataire": "loc-3",
            "date_loyer": "2026-05-01",
            "montant": 900.0,
            "statut": "en_attente",
            "quitus_genere": False,
        },
        headers=auth_headers,
    )
    assert created.status_code == 201

    response = client.patch(
        f"/api/v1/loyers/{created.json()['id']}",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 400
    payload = response.json()
    assert payload["code"] == "validation_error"
    assert payload["error"] == "No update fields provided"
