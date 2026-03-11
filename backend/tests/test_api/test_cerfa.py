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


def test_cerfa_2044_requires_auth(client):
    """Unauthenticated request to CERFA 2044 is rejected."""
    payload = {"annee": 2025, "total_revenus": 1000, "total_charges": 500}
    response = client.post("/api/v1/cerfa/2044", json=payload)
    assert response.status_code == 401


def test_cerfa_2044_pdf_requires_auth(client):
    """Unauthenticated request to CERFA 2044 PDF is rejected."""
    payload = {"annee": 2025, "total_revenus": 1000, "total_charges": 500}
    response = client.post("/api/v1/cerfa/2044/pdf", json=payload)
    assert response.status_code == 401


def test_cerfa_2044_pdf_success(client, auth_headers, fake_supabase):
    """CERFA 2044 PDF endpoint returns a valid PDF for pro users."""
    _enable_pro_subscription(fake_supabase)
    payload = {
        "annee": 2025,
        "total_revenus": 24000.0,
        "total_charges": 8000.0,
        "sci_nom": "SCI Test",
        "siren": "123456789",
    }

    response = client.post("/api/v1/cerfa/2044/pdf", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert "application/pdf" in response.headers.get("content-type", "")
    assert response.content[:4] == b"%PDF"


def test_cerfa_2044_invalid_annee(client, auth_headers, fake_supabase):
    """Year below 2000 is rejected by Pydantic validation."""
    _enable_pro_subscription(fake_supabase)
    payload = {"annee": 1999, "total_revenus": 1000, "total_charges": 500}
    response = client.post("/api/v1/cerfa/2044", json=payload, headers=auth_headers)
    assert response.status_code == 422


def test_cerfa_2044_negative_revenus(client, auth_headers, fake_supabase):
    """Negative revenus is rejected by Pydantic validation."""
    _enable_pro_subscription(fake_supabase)
    payload = {"annee": 2025, "total_revenus": -1000, "total_charges": 500}
    response = client.post("/api/v1/cerfa/2044", json=payload, headers=auth_headers)
    assert response.status_code == 422


def test_cerfa_2044_zero_charges(client, auth_headers, fake_supabase):
    """Zero charges should work — resultat_fiscal equals total_revenus."""
    _enable_pro_subscription(fake_supabase)
    payload = {"annee": 2025, "total_revenus": 12000.0, "total_charges": 0.0}
    response = client.post("/api/v1/cerfa/2044", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["resultat_fiscal"] == 12000.0


def test_cerfa_2044_pdf_without_sci_nom(client, auth_headers, fake_supabase):
    """PDF generation works even without sci_nom and siren."""
    _enable_pro_subscription(fake_supabase)
    payload = {"annee": 2025, "total_revenus": 5000.0, "total_charges": 2000.0}
    response = client.post("/api/v1/cerfa/2044/pdf", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"


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
