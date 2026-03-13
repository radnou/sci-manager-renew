def _enable_pro_subscription(fake_supabase):
    fake_supabase.store["subscriptions"] = [
        {
            "user_id": "user-123",
            "plan_key": "pro",
            "status": "active",
            "is_active": True,
            "max_scis": 10,
            "max_biens": 20,
            "features": {
                "multi_sci_enabled": True,
                "charges_enabled": True,
                "fiscalite_enabled": True,
                "quitus_enabled": True,
                "cerfa_enabled": True,
                "priority_support": True,
            },
        }
    ]


def test_get_fiscalite_requires_auth(client):
    response = client.get("/api/v1/fiscalite/")
    assert response.status_code == 401


def test_create_update_and_delete_fiscalite(client, auth_headers, fake_supabase):
    _enable_pro_subscription(fake_supabase)

    created = client.post(
        "/api/v1/fiscalite/",
        json={
            "id_sci": "sci-1",
            "annee": 2025,
            "total_revenus": 36000,
            "total_charges": 7200,
        },
        headers=auth_headers,
    )
    assert created.status_code == 201
    payload = created.json()
    assert payload["resultat_fiscal"] == 28800
    assert payload["regime_fiscal"] == "IR"
    fiscalite_id = payload["id"]

    listed = client.get("/api/v1/fiscalite/?id_sci=sci-1", headers=auth_headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = client.patch(
        f"/api/v1/fiscalite/{fiscalite_id}",
        json={"total_charges": 8200},
        headers=auth_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["resultat_fiscal"] == 27800

    deleted = client.delete(f"/api/v1/fiscalite/{fiscalite_id}", headers=auth_headers)
    assert deleted.status_code == 204


def test_list_fiscalite_requires_feature_upgrade(client, auth_headers, free_plan):
    response = client.get("/api/v1/fiscalite/?id_sci=sci-1", headers=auth_headers)
    assert response.status_code == 402
    assert response.json()["code"] == "upgrade_required"
