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


def test_generate_cerfa_2044_pdf_success(client, auth_headers, fake_supabase):
    """Pro user can generate CERFA 2044 PDF."""
    _enable_pro_subscription(fake_supabase)
    payload = {
        "annee": 2025,
        "total_revenus": 24000.0,
        "total_charges": 7000.0,
        "sci_nom": "SCI Mosa Belleville",
        "siren": "123456789",
    }

    response = client.post("/api/v1/cerfa/2044/pdf", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "cerfa_2044_2025" in response.headers["content-disposition"]
    assert response.content.startswith(b"%PDF")


def test_generate_cerfa_2044_pdf_without_sci_info(client, auth_headers, fake_supabase):
    """PDF generation works without optional sci_nom and siren."""
    _enable_pro_subscription(fake_supabase)
    payload = {
        "annee": 2025,
        "total_revenus": 10000.0,
        "total_charges": 3000.0,
    }

    response = client.post("/api/v1/cerfa/2044/pdf", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.content.startswith(b"%PDF")


def test_generate_cerfa_2044_returns_all_fields(client, auth_headers, fake_supabase):
    """JSON response includes all expected fields."""
    _enable_pro_subscription(fake_supabase)
    payload = {
        "annee": 2025,
        "total_revenus": 30000.0,
        "total_charges": 12000.0,
    }

    response = client.post("/api/v1/cerfa/2044", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "generated"
    assert data["annee"] == 2025
    assert data["total_revenus"] == 30000.0
    assert data["total_charges"] == 12000.0
    assert data["resultat_fiscal"] == 18000.0
    assert data["formulaire"] == "cerfa_2044"


def test_cerfa_2044_invalid_annee(client, auth_headers, fake_supabase):
    """Invalid year returns 422 validation error."""
    _enable_pro_subscription(fake_supabase)
    payload = {
        "annee": 1999,  # below minimum of 2000
        "total_revenus": 10000.0,
        "total_charges": 5000.0,
    }

    response = client.post("/api/v1/cerfa/2044", json=payload, headers=auth_headers)
    assert response.status_code == 422
