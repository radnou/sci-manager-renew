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


def test_get_charges_requires_auth(client):
    response = client.get("/api/v1/charges/")
    assert response.status_code == 401


def test_create_update_and_delete_charge(client, auth_headers, fake_supabase):
    _enable_pro_subscription(fake_supabase)
    bien_created = client.post(
        "/api/v1/biens/",
        json={
            "id_sci": "sci-1",
            "adresse": "17 rue Charges",
            "ville": "Paris",
            "code_postal": "75017",
            "type_locatif": "nu",
            "loyer_cc": 1100.0,
            "charges": 90.0,
            "tmi": 20.0,
        },
        headers=auth_headers,
    )
    bien_id = bien_created.json()["id"]

    created = client.post(
        "/api/v1/charges/",
        json={
            "id_bien": bien_id,
            "type_charge": "assurance",
            "montant": 240.0,
            "date_paiement": "2026-03-05",
        },
        headers=auth_headers,
    )
    assert created.status_code == 201
    payload = created.json()
    assert payload["id_sci"] == "sci-1"
    assert payload["bien_adresse"] == "17 rue Charges"
    charge_id = payload["id"]

    listed = client.get("/api/v1/charges/?id_sci=sci-1", headers=auth_headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    updated = client.patch(
        f"/api/v1/charges/{charge_id}",
        json={"montant": 310.0, "type_charge": "travaux"},
        headers=auth_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["montant"] == 310.0
    assert updated.json()["type_charge"] == "travaux"

    deleted = client.delete(f"/api/v1/charges/{charge_id}", headers=auth_headers)
    assert deleted.status_code == 204


def test_create_charge_requires_feature_upgrade(client, auth_headers):
    response = client.post(
        "/api/v1/charges/",
        json={
            "id_bien": "bien-unknown",
            "type_charge": "assurance",
            "montant": 120.0,
            "date_paiement": "2026-03-05",
        },
        headers=auth_headers,
    )
    assert response.status_code == 402
    assert response.json()["code"] == "upgrade_required"
