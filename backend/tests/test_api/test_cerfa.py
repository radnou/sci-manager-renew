from app.core.config import settings


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


def test_generate_cerfa_2044(client, auth_headers, fake_supabase):
    _enable_pro_subscription(fake_supabase)
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


def test_generate_cerfa_2044_disabled(client, auth_headers, monkeypatch, fake_supabase):
    _enable_pro_subscription(fake_supabase)
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


def test_cerfa_2044_blocked_for_free_plan(client, auth_headers):
    """Free users cannot access CERFA 2044 (cerfa_enabled=False for FREE plan)."""
    payload = {
        "annee": 2025,
        "total_revenus": 24000.0,
        "total_charges": 7000.0,
    }

    response = client.post("/api/v1/cerfa/2044", json=payload, headers=auth_headers)
    assert response.status_code == 402
    data = response.json()
    assert data["code"] == "upgrade_required"


def test_cerfa_2044_pdf_blocked_for_free_plan(client, auth_headers):
    """Free users cannot access CERFA 2044 PDF (cerfa_enabled=False for FREE plan)."""
    payload = {
        "annee": 2025,
        "total_revenus": 24000.0,
        "total_charges": 7000.0,
    }

    response = client.post("/api/v1/cerfa/2044/pdf", json=payload, headers=auth_headers)
    assert response.status_code == 402
    data = response.json()
    assert data["code"] == "upgrade_required"
