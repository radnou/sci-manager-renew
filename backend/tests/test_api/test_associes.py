def test_get_associes_requires_auth(client):
    response = client.get("/api/v1/associes/")
    assert response.status_code == 401


def test_create_update_and_delete_associe(client, auth_headers, fake_supabase):
    # Libère de la capacité sur sci-2 pour accueillir un nouvel associé métier non connecté.
    for associe in fake_supabase.store["associes"]:
        if associe["id"] == "associe-2":
            associe["part"] = 60

    created = client.post(
        "/api/v1/associes/",
        json={
            "id_sci": "sci-2",
            "nom": "Sophie Martin",
            "email": "sophie.martin@example.com",
            "part": 40,
            "role": "associe",
            "user_id": None,
        },
        headers=auth_headers,
    )
    assert created.status_code == 201
    payload = created.json()
    assert payload["nom"] == "Sophie Martin"
    assert payload["is_account_member"] is False
    associe_id = payload["id"]

    updated = client.patch(
        f"/api/v1/associes/{associe_id}",
        json={"role": "co_gerant", "part": 35},
        headers=auth_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["role"] == "co_gerant"
    assert updated.json()["part"] == 35

    deleted = client.delete(f"/api/v1/associes/{associe_id}", headers=auth_headers)
    assert deleted.status_code == 204


def test_create_associe_rejects_over_allocated_capital(client, auth_headers):
    response = client.post(
        "/api/v1/associes/",
        json={
            "id_sci": "sci-1",
            "nom": "Part en trop",
            "email": "part@example.com",
            "part": 5,
            "role": "associe",
            "user_id": None,
        },
        headers=auth_headers,
    )
    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"


def test_delete_associe_blocks_self_access_row(client, auth_headers):
    response = client.delete("/api/v1/associes/associe-1", headers=auth_headers)
    assert response.status_code == 400
    assert response.json()["code"] == "validation_error"
