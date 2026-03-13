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


def test_cerfa_2044_blocked_for_free_plan(client, auth_headers, free_plan):
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


def test_cerfa_2044_pdf_blocked_for_free_plan(client, auth_headers, free_plan):
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


# ── Deficit foncier (charges > revenus) ────────────────────────────────

def test_cerfa_2044_deficit_foncier(client, auth_headers, fake_supabase):
    """When charges exceed revenus, resultat_fiscal is negative (deficit foncier)."""
    _enable_pro_subscription(fake_supabase)
    payload = {"annee": 2025, "total_revenus": 5000.0, "total_charges": 18000.0}
    response = client.post("/api/v1/cerfa/2044", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["resultat_fiscal"] == -13000.0
    assert data["status"] == "generated"


def test_cerfa_2044_pdf_deficit_foncier(client, auth_headers, fake_supabase):
    """PDF generation works with deficit foncier (negative resultat_fiscal)."""
    _enable_pro_subscription(fake_supabase)
    payload = {"annee": 2025, "total_revenus": 3000.0, "total_charges": 20000.0}
    response = client.post("/api/v1/cerfa/2044/pdf", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"
    content_disp = response.headers.get("content-disposition", "")
    assert "cerfa_2044_2025_sci.pdf" in content_disp


# ── Boundary values for annee (Pydantic ge=2000, le=2100) ─────────────

def test_cerfa_2044_annee_lower_bound(client, auth_headers, fake_supabase):
    """Year 2000 (minimum valid) is accepted."""
    _enable_pro_subscription(fake_supabase)
    payload = {"annee": 2000, "total_revenus": 1000.0, "total_charges": 500.0}
    response = client.post("/api/v1/cerfa/2044", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["annee"] == 2000


def test_cerfa_2044_annee_upper_bound(client, auth_headers, fake_supabase):
    """Year 2100 (maximum valid) is accepted."""
    _enable_pro_subscription(fake_supabase)
    payload = {"annee": 2100, "total_revenus": 1000.0, "total_charges": 500.0}
    response = client.post("/api/v1/cerfa/2044", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["annee"] == 2100


def test_cerfa_2044_annee_above_upper_bound(client, auth_headers, fake_supabase):
    """Year 2101 (above max) is rejected."""
    _enable_pro_subscription(fake_supabase)
    payload = {"annee": 2101, "total_revenus": 1000.0, "total_charges": 500.0}
    response = client.post("/api/v1/cerfa/2044", json=payload, headers=auth_headers)
    assert response.status_code == 422


def test_cerfa_2044_negative_charges(client, auth_headers, fake_supabase):
    """Negative charges is rejected by Pydantic validation (ge=0)."""
    _enable_pro_subscription(fake_supabase)
    payload = {"annee": 2025, "total_revenus": 5000.0, "total_charges": -100.0}
    response = client.post("/api/v1/cerfa/2044", json=payload, headers=auth_headers)
    assert response.status_code == 422


# ── Zero revenus ──────────────────────────────────────────────────────

def test_cerfa_2044_zero_revenus(client, auth_headers, fake_supabase):
    """Zero revenus and zero charges produces zero resultat_fiscal."""
    _enable_pro_subscription(fake_supabase)
    payload = {"annee": 2025, "total_revenus": 0.0, "total_charges": 0.0}
    response = client.post("/api/v1/cerfa/2044", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["resultat_fiscal"] == 0.0


def test_cerfa_2044_zero_revenus_with_charges(client, auth_headers, fake_supabase):
    """Zero revenus with charges produces negative resultat_fiscal."""
    _enable_pro_subscription(fake_supabase)
    payload = {"annee": 2025, "total_revenus": 0.0, "total_charges": 5000.0}
    response = client.post("/api/v1/cerfa/2044", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["resultat_fiscal"] == -5000.0


# ── Floating-point precision ─────────────────────────────────────────

def test_cerfa_2044_floating_point_rounding(client, auth_headers, fake_supabase):
    """Verify rounding to 2 decimal places for resultat_fiscal."""
    _enable_pro_subscription(fake_supabase)
    # 0.1 + 0.2 floating point issue: 10000.10 - 3000.20 = 6999.90
    payload = {"annee": 2025, "total_revenus": 10000.10, "total_charges": 3000.20}
    response = client.post("/api/v1/cerfa/2044", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["resultat_fiscal"] == 6999.90


def test_cerfa_2044_large_values(client, auth_headers, fake_supabase):
    """Large monetary values are handled correctly."""
    _enable_pro_subscription(fake_supabase)
    payload = {"annee": 2025, "total_revenus": 9999999.99, "total_charges": 1234567.89}
    response = client.post("/api/v1/cerfa/2044", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["resultat_fiscal"] == 8765432.10


# ── PDF feature-disabled path ────────────────────────────────────────

def test_cerfa_2044_pdf_generates_when_feature_flag_on(client, auth_headers, fake_supabase):
    """PDF endpoint generates successfully when feature_cerfa_generation is enabled (default)."""
    _enable_pro_subscription(fake_supabase)
    payload = {"annee": 2025, "total_revenus": 10000.0, "total_charges": 3000.0}
    response = client.post("/api/v1/cerfa/2044/pdf", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"
    assert "application/pdf" in response.headers.get("content-type", "")


# ── PDF Content-Disposition header and filename ──────────────────────

def test_cerfa_2044_pdf_filename_with_sci_nom(client, auth_headers, fake_supabase):
    """PDF filename contains the SCI name when provided."""
    _enable_pro_subscription(fake_supabase)
    payload = {
        "annee": 2025,
        "total_revenus": 12000.0,
        "total_charges": 4000.0,
        "sci_nom": "SCI Horizon",
    }
    response = client.post("/api/v1/cerfa/2044/pdf", json=payload, headers=auth_headers)
    assert response.status_code == 200
    content_disp = response.headers["content-disposition"]
    assert "cerfa_2044_2025_SCI Horizon.pdf" in content_disp


def test_cerfa_2044_pdf_filename_without_sci_nom(client, auth_headers, fake_supabase):
    """PDF filename falls back to 'sci' when sci_nom is empty."""
    _enable_pro_subscription(fake_supabase)
    payload = {"annee": 2025, "total_revenus": 12000.0, "total_charges": 4000.0}
    response = client.post("/api/v1/cerfa/2044/pdf", json=payload, headers=auth_headers)
    assert response.status_code == 200
    content_disp = response.headers["content-disposition"]
    assert "cerfa_2044_2025_sci.pdf" in content_disp


# ── PDF with only sci_nom (no siren) ─────────────────────────────────

def test_cerfa_2044_pdf_sci_nom_only(client, auth_headers, fake_supabase):
    """PDF with sci_nom but no siren renders without error."""
    _enable_pro_subscription(fake_supabase)
    payload = {
        "annee": 2025,
        "total_revenus": 15000.0,
        "total_charges": 6000.0,
        "sci_nom": "SCI Test Nom Only",
    }
    response = client.post("/api/v1/cerfa/2044/pdf", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"
    assert len(response.content) > 500  # sanity check: non-trivial PDF size


def test_cerfa_2044_pdf_siren_only(client, auth_headers, fake_supabase):
    """PDF with siren but no sci_nom renders without error."""
    _enable_pro_subscription(fake_supabase)
    payload = {
        "annee": 2025,
        "total_revenus": 15000.0,
        "total_charges": 6000.0,
        "siren": "999888777",
    }
    response = client.post("/api/v1/cerfa/2044/pdf", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"


# ── PDF large values render without error ────────────────────────────

def test_cerfa_2044_pdf_large_values(client, auth_headers, fake_supabase):
    """PDF generation handles large monetary values without layout errors."""
    _enable_pro_subscription(fake_supabase)
    payload = {
        "annee": 2025,
        "total_revenus": 9999999.99,
        "total_charges": 1234567.89,
        "sci_nom": "SCI Grande Fortune",
        "siren": "111222333",
    }
    response = client.post("/api/v1/cerfa/2044/pdf", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"
    assert "application/pdf" in response.headers.get("content-type", "")


# ── Missing required fields ──────────────────────────────────────────

def test_cerfa_2044_missing_annee(client, auth_headers, fake_supabase):
    """Request without annee field is rejected."""
    _enable_pro_subscription(fake_supabase)
    payload = {"total_revenus": 5000.0, "total_charges": 2000.0}
    response = client.post("/api/v1/cerfa/2044", json=payload, headers=auth_headers)
    assert response.status_code == 422


def test_cerfa_2044_missing_total_revenus(client, auth_headers, fake_supabase):
    """Request without total_revenus field is rejected."""
    _enable_pro_subscription(fake_supabase)
    payload = {"annee": 2025, "total_charges": 2000.0}
    response = client.post("/api/v1/cerfa/2044", json=payload, headers=auth_headers)
    assert response.status_code == 422


def test_cerfa_2044_missing_total_charges(client, auth_headers, fake_supabase):
    """Request without total_charges field is rejected."""
    _enable_pro_subscription(fake_supabase)
    payload = {"annee": 2025, "total_revenus": 5000.0}
    response = client.post("/api/v1/cerfa/2044", json=payload, headers=auth_headers)
    assert response.status_code == 422


def test_cerfa_2044_empty_body(client, auth_headers, fake_supabase):
    """Empty JSON body is rejected."""
    _enable_pro_subscription(fake_supabase)
    response = client.post("/api/v1/cerfa/2044", json={}, headers=auth_headers)
    assert response.status_code == 422


# ── PDF boundary annee values ────────────────────────────────────────

def test_cerfa_2044_pdf_annee_lower_bound(client, auth_headers, fake_supabase):
    """PDF generation works with minimum valid annee (2000)."""
    _enable_pro_subscription(fake_supabase)
    payload = {"annee": 2000, "total_revenus": 5000.0, "total_charges": 2000.0}
    response = client.post("/api/v1/cerfa/2044/pdf", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"


def test_cerfa_2044_pdf_annee_upper_bound(client, auth_headers, fake_supabase):
    """PDF generation works with maximum valid annee (2100)."""
    _enable_pro_subscription(fake_supabase)
    payload = {"annee": 2100, "total_revenus": 5000.0, "total_charges": 2000.0}
    response = client.post("/api/v1/cerfa/2044/pdf", json=payload, headers=auth_headers)
    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"


# ── JSON response type correctness ──────────────────────────────────

def test_cerfa_2044_response_types(client, auth_headers, fake_supabase):
    """Verify response field types match the declared return type."""
    _enable_pro_subscription(fake_supabase)
    payload = {"annee": 2025, "total_revenus": 10000.0, "total_charges": 3000.0}
    response = client.post("/api/v1/cerfa/2044", json=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["status"], str)
    assert isinstance(data["annee"], int)
    assert isinstance(data["total_revenus"], (int, float))
    assert isinstance(data["total_charges"], (int, float))
    assert isinstance(data["resultat_fiscal"], (int, float))
    assert isinstance(data["formulaire"], str)


# ── PDF validation endpoints also reject invalid input ───────────────

def test_cerfa_2044_pdf_invalid_annee(client, auth_headers, fake_supabase):
    """PDF endpoint also rejects invalid annee."""
    _enable_pro_subscription(fake_supabase)
    payload = {"annee": 1999, "total_revenus": 1000.0, "total_charges": 500.0}
    response = client.post("/api/v1/cerfa/2044/pdf", json=payload, headers=auth_headers)
    assert response.status_code == 422


def test_cerfa_2044_pdf_negative_revenus(client, auth_headers, fake_supabase):
    """PDF endpoint also rejects negative revenus."""
    _enable_pro_subscription(fake_supabase)
    payload = {"annee": 2025, "total_revenus": -1.0, "total_charges": 500.0}
    response = client.post("/api/v1/cerfa/2044/pdf", json=payload, headers=auth_headers)
    assert response.status_code == 422


def test_cerfa_2044_pdf_empty_body(client, auth_headers, fake_supabase):
    """PDF endpoint rejects empty body."""
    _enable_pro_subscription(fake_supabase)
    response = client.post("/api/v1/cerfa/2044/pdf", json={}, headers=auth_headers)
    assert response.status_code == 422
