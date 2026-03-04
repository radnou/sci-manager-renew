def test_get_loyers_requires_auth(client):
    response = client.get("/api/v1/loyers/")
    assert response.status_code == 401


def test_create_and_filter_loyers(client, auth_headers):
    payload_1 = {
        "id_bien": "bien-1",
        "id_locataire": "loc-1",
        "date_loyer": "2026-01-01",
        "montant": 1200.0,
        "statut": "en_attente",
        "quitus_genere": False,
    }
    payload_2 = {
        "id_bien": "bien-1",
        "id_locataire": "loc-1",
        "date_loyer": "2026-03-01",
        "montant": 1200.0,
        "statut": "paye",
        "quitus_genere": True,
    }

    create_1 = client.post("/api/v1/loyers/", json=payload_1, headers=auth_headers)
    create_2 = client.post("/api/v1/loyers/", json=payload_2, headers=auth_headers)
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
    payload = {
        "id_bien": "bien-2",
        "id_locataire": "loc-2",
        "date_loyer": "2026-02-01",
        "montant": 950.0,
        "statut": "en_attente",
        "quitus_genere": False,
    }
    created = client.post("/api/v1/loyers/", json=payload, headers=auth_headers)
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
