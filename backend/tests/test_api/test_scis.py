def test_get_scis_requires_auth(client):
    response = client.get("/api/v1/scis/")
    assert response.status_code == 401


def test_get_scis_returns_portfolio_overview(client, auth_headers):
    response = client.get("/api/v1/scis/", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2
    assert data[0]["nom"] == "SCI Horizon Lyon"
    assert data[1]["nom"] == "SCI Mosa Belleville"
    assert data[1]["associes_count"] == 2
    assert data[1]["user_role"] == "gerant"


def test_get_sci_detail_returns_identity_card(client, auth_headers, fake_supabase):
    fake_supabase.store["biens"] = [
        {
            "id": "bien-1",
            "id_sci": "sci-1",
            "adresse": "1 rue Seed",
            "ville": "Paris",
            "code_postal": "75001",
            "type_locatif": "nu",
            "loyer_cc": 1200,
            "charges": 150,
            "tmi": 30,
            "rentabilite_brute": 5.8,
            "rentabilite_nette": 4.9,
            "cashflow_annuel": 12600,
        },
        {
            "id": "bien-2",
            "id_sci": "sci-1",
            "adresse": "42 avenue QA",
            "ville": "Lyon",
            "code_postal": "69002",
            "type_locatif": "meuble",
            "loyer_cc": 1650,
            "charges": 120,
            "tmi": 28,
            "rentabilite_brute": 6.1,
            "rentabilite_nette": 5.5,
            "cashflow_annuel": 18360,
        },
    ]
    fake_supabase.store["loyers"] = [
        {
            "id": "loyer-1",
            "id_bien": "bien-1",
            "id_sci": "sci-1",
            "id_locataire": "loc-1",
            "date_loyer": "2026-03-01",
            "montant": 1200,
            "statut": "paye",
            "quitus_genere": True,
        },
        {
            "id": "loyer-2",
            "id_bien": "bien-2",
            "id_sci": "sci-1",
            "id_locataire": "loc-2",
            "date_loyer": "2026-03-05",
            "montant": 1650,
            "statut": "en_attente",
            "quitus_genere": False,
        },
    ]
    fake_supabase.store["charges"] = [
        {
            "id": "charge-1",
            "id_bien": "bien-1",
            "type_charge": "assurance",
            "montant": 240,
            "date_paiement": "2026-02-10",
        },
        {
            "id": "charge-2",
            "id_bien": "bien-2",
            "type_charge": "travaux",
            "montant": 600,
            "date_paiement": "2026-03-02",
        },
    ]
    fake_supabase.store["fiscalite"] = [
        {
            "id": "fisc-1",
            "id_sci": "sci-1",
            "annee": 2025,
            "total_revenus": 34200,
            "total_charges": 5400,
            "resultat_fiscal": 28800,
        }
    ]

    response = client.get("/api/v1/scis/sci-1", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["nom"] == "SCI Mosa Belleville"
    assert data["associes_count"] == 2
    assert data["biens_count"] == 2
    assert data["loyers_count"] == 2
    assert data["charges_count"] == 2
    assert data["total_monthly_rent"] == 2850
    assert data["total_monthly_property_charges"] == 270
    assert data["paid_loyers_total"] == 1200
    assert data["pending_loyers_total"] == 1650
    assert data["recent_loyers"][0]["id"] == "loyer-2"
    assert data["recent_charges"][0]["id"] == "charge-2"
    assert data["fiscalite"][0]["annee"] == 2025


def test_create_sci_creates_membership(client, auth_headers, fake_supabase):
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
    response = client.post(
        "/api/v1/scis/",
        json={"nom": "SCI Delta Paris", "siren": "111222333", "regime_fiscal": "IR"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    payload = response.json()
    assert payload["nom"] == "SCI Delta Paris"

    associes = fake_supabase.store["associes"]
    created_membership = next(row for row in associes if row["id_sci"] == payload["id"])
    assert created_membership["user_id"] == "user-123"
    assert created_membership["role"] == "gerant"


def test_update_sci_patch(client, auth_headers):
    response = client.patch(
        "/api/v1/scis/sci-1",
        json={"nom": "SCI Mosa Belleville Renommée"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["nom"] == "SCI Mosa Belleville Renommée"


def test_update_sci_empty_payload(client, auth_headers):
    response = client.patch(
        "/api/v1/scis/sci-1",
        json={},
        headers=auth_headers,
    )
    assert response.status_code == 404


def test_update_sci_requires_gerant(client, auth_headers):
    response = client.patch(
        "/api/v1/scis/sci-2",
        json={"nom": "Nope"},
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_delete_sci(client, auth_headers):
    response = client.delete("/api/v1/scis/sci-1", headers=auth_headers)
    assert response.status_code == 204


def test_delete_sci_requires_gerant(client, auth_headers):
    response = client.delete("/api/v1/scis/sci-2", headers=auth_headers)
    assert response.status_code == 403
