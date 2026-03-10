"""
Tests HTTP pour l'enforcement des limites de plan (quota biens / SCIs).

Verifie que les endpoints create renvoient les bons codes d'erreur
quand un utilisateur depasse le quota autorise par son plan.

- PlanLimitError -> 402 (quota atteint, paiement requis pour upgrade)
- UpgradeRequiredError -> 402 (multi-SCI non autorise)
"""

import pytest


BIEN_PAYLOAD = {
    "id_sci": "sci-1",
    "adresse": "10 rue du Test",
    "ville": "Paris",
    "code_postal": "75010",
    "type_locatif": "nu",
    "loyer_cc": 800,
    "charges": 50,
    "tmi": 30,
}

SCI_PAYLOAD = {
    "nom": "SCI Nouvelle",
    "siren": "999888777",
    "regime_fiscal": "IR",
}


@pytest.fixture(autouse=True)
def enforce_mode(monkeypatch):
    """Force enforcement mode to 'enforce' so limits are actually enforced."""
    monkeypatch.setattr(
        "app.services.subscription_service.settings.feature_plan_entitlements_enforcement",
        "enforce",
    )


# ---------------------------------------------------------------------------
# Biens - quota enforcement
# ---------------------------------------------------------------------------


def test_create_bien_over_quota_returns_402(client, auth_headers, fake_supabase):
    """FREE plan: max_biens=1, user already has 1 bien -> 402 PlanLimitError."""
    # Seed: user-123 is associated to sci-1 (via conftest default associes).
    # Put one existing bien so the user is at the limit.
    fake_supabase.store["biens"] = [
        {
            "id": "bien-existing",
            "id_sci": "sci-1",
            "adresse": "1 rue Existante",
            "ville": "Lyon",
            "code_postal": "69001",
            "type_locatif": "nu",
            "loyer_cc": 900,
            "charges": 0,
            "tmi": 0,
        },
    ]
    # No subscription row -> defaults to FREE (max_biens=1).
    fake_supabase.store["subscriptions"] = []

    response = client.post("/api/v1/biens/", json=BIEN_PAYLOAD, headers=auth_headers)

    assert response.status_code == 402, f"Expected 402, got {response.status_code}: {response.text}"
    body = response.json()
    assert body["code"] == "plan_limit_reached"
    assert body["details"]["resource"] == "biens"
    assert body["details"]["plan_key"] == "free"


def test_create_bien_over_quota_error_format(client, auth_headers, fake_supabase):
    """Verify the full error response structure for biens quota enforcement."""
    fake_supabase.store["biens"] = [
        {
            "id": "bien-existing",
            "id_sci": "sci-1",
            "adresse": "1 rue Existante",
            "ville": "Lyon",
            "code_postal": "69001",
            "type_locatif": "nu",
            "loyer_cc": 900,
            "charges": 0,
            "tmi": 0,
        },
    ]
    fake_supabase.store["subscriptions"] = []

    response = client.post("/api/v1/biens/", json=BIEN_PAYLOAD, headers=auth_headers)

    assert response.status_code == 402
    body = response.json()
    # Verify all required fields in the error response
    assert "error" in body
    assert body["code"] == "plan_limit_reached"
    assert body["details"]["resource"] == "biens"
    assert body["details"]["limit"] == 1
    assert body["details"]["current"] == 1
    assert body["details"]["plan_key"] == "free"
    assert "request_id" in body


def test_create_bien_within_quota_allowed(client, auth_headers, fake_supabase):
    """PRO plan: max_biens=20, user has 2 biens -> creation allowed (201)."""
    fake_supabase.store["biens"] = [
        {
            "id": "bien-1",
            "id_sci": "sci-1",
            "adresse": "1 rue Existante",
            "ville": "Lyon",
            "code_postal": "69001",
            "type_locatif": "nu",
            "loyer_cc": 900,
            "charges": 0,
            "tmi": 0,
        },
        {
            "id": "bien-2",
            "id_sci": "sci-1",
            "adresse": "2 rue Existante",
            "ville": "Lyon",
            "code_postal": "69002",
            "type_locatif": "meuble",
            "loyer_cc": 1100,
            "charges": 80,
            "tmi": 25,
        },
    ]
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

    response = client.post("/api/v1/biens/", json=BIEN_PAYLOAD, headers=auth_headers)

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    body = response.json()
    assert body["adresse"] == BIEN_PAYLOAD["adresse"]
    assert body["id_sci"] == "sci-1"


# ---------------------------------------------------------------------------
# SCIs - quota enforcement
# ---------------------------------------------------------------------------


def test_create_sci_over_quota_returns_402(client, auth_headers, fake_supabase):
    """FREE plan: max_scis=1, user already has 1 SCI -> 402 PlanLimitError.

    The scis endpoint first calls enforce_limit (which raises 402 PlanLimitError),
    then checks multi_sci_enabled (raising 402 UpgradeRequiredError). Since enforce_limit
    is called first and current_scis >= max_scis, PlanLimitError fires first.

    Note: The conftest seeds 2 associe rows for user-123 (sci-1 and sci-2), so current_scis=2.
    We override to have only 1 to test the boundary.
    """
    # Override associes so user-123 has exactly 1 SCI membership (at the limit).
    fake_supabase.store["associes"] = [
        {
            "id": "associe-1",
            "id_sci": "sci-1",
            "user_id": "user-123",
            "nom": "Test User",
            "email": "test@sci.local",
            "part": 100,
            "role": "gerant",
        },
    ]
    fake_supabase.store["subscriptions"] = []

    response = client.post("/api/v1/scis/", json=SCI_PAYLOAD, headers=auth_headers)

    # enforce_limit fires first: current_scis=1 >= max_scis=1 -> PlanLimitError (402)
    assert response.status_code == 402, f"Expected 402, got {response.status_code}: {response.text}"
    body = response.json()
    assert body["code"] == "plan_limit_reached"
    assert body["details"]["resource"] == "scis"
    assert body["details"]["plan_key"] == "free"


def test_create_sci_over_quota_error_format(client, auth_headers, fake_supabase):
    """Verify the full error response structure for scis quota enforcement."""
    fake_supabase.store["associes"] = [
        {
            "id": "associe-1",
            "id_sci": "sci-1",
            "user_id": "user-123",
            "nom": "Test User",
            "email": "test@sci.local",
            "part": 100,
            "role": "gerant",
        },
    ]
    fake_supabase.store["subscriptions"] = []

    response = client.post("/api/v1/scis/", json=SCI_PAYLOAD, headers=auth_headers)

    assert response.status_code == 402
    body = response.json()
    # Verify all required fields in the error response
    assert "error" in body
    assert body["code"] == "plan_limit_reached"
    assert body["details"]["resource"] == "scis"
    assert body["details"]["limit"] == 1
    assert body["details"]["current"] == 1
    assert body["details"]["plan_key"] == "free"
    assert "request_id" in body


def test_create_sci_upgrade_required_returns_402(client, auth_headers, fake_supabase):
    """Custom plan: max_scis=5, multi_sci_enabled=False, user already has 1 SCI.

    enforce_limit passes (current_scis=1 < max_scis=5), but multi_sci_enabled=False
    with current_scis > 0 triggers UpgradeRequiredError (402).

    This is an artificial scenario to isolate the UpgradeRequired code path, since
    in practice FREE and STARTER both have max_scis=1 with multi_sci_enabled=False,
    so enforce_limit always fires first.
    """
    fake_supabase.store["associes"] = [
        {
            "id": "associe-1",
            "id_sci": "sci-1",
            "user_id": "user-123",
            "nom": "Test User",
            "email": "test@sci.local",
            "part": 100,
            "role": "gerant",
        },
    ]
    fake_supabase.store["subscriptions"] = [
        {
            "user_id": "user-123",
            "plan_key": "starter",
            "status": "active",
            "is_active": True,
            "max_scis": 5,  # Artificially high to let enforce_limit pass
            "max_biens": 5,
            "features": {
                "multi_sci_enabled": False,  # This triggers UpgradeRequiredError
                "charges_enabled": True,
                "fiscalite_enabled": False,
                "quitus_enabled": True,
                "cerfa_enabled": False,
                "priority_support": False,
            },
        }
    ]

    response = client.post("/api/v1/scis/", json=SCI_PAYLOAD, headers=auth_headers)

    assert response.status_code == 402, f"Expected 402, got {response.status_code}: {response.text}"
    body = response.json()
    assert body["code"] == "upgrade_required"


def test_create_sci_within_quota_allowed(client, auth_headers, fake_supabase):
    """PRO plan: max_scis=10, multi_sci_enabled=True, user has 2 SCIs -> creation allowed."""
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

    response = client.post("/api/v1/scis/", json=SCI_PAYLOAD, headers=auth_headers)

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
    body = response.json()
    assert body["nom"] == SCI_PAYLOAD["nom"]


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


def test_create_bien_exactly_at_limit_returns_402(client, auth_headers, fake_supabase):
    """STARTER plan: max_biens=5, user has exactly 5 biens -> 402."""
    fake_supabase.store["biens"] = [
        {
            "id": f"bien-{i}",
            "id_sci": "sci-1",
            "adresse": f"{i} rue Limite",
            "ville": "Paris",
            "code_postal": "75001",
            "type_locatif": "nu",
            "loyer_cc": 500,
            "charges": 0,
            "tmi": 0,
        }
        for i in range(5)
    ]
    fake_supabase.store["subscriptions"] = [
        {
            "user_id": "user-123",
            "plan_key": "starter",
            "status": "active",
            "is_active": True,
            "max_scis": 1,
            "max_biens": 5,
            "features": {
                "multi_sci_enabled": False,
                "charges_enabled": True,
                "fiscalite_enabled": False,
                "quitus_enabled": True,
                "cerfa_enabled": False,
                "priority_support": False,
            },
        }
    ]

    response = client.post("/api/v1/biens/", json=BIEN_PAYLOAD, headers=auth_headers)

    assert response.status_code == 402, f"Expected 402, got {response.status_code}: {response.text}"
    body = response.json()
    assert body["code"] == "plan_limit_reached"
    assert body["details"]["current"] == 5
    assert body["details"]["limit"] == 5


def test_create_bien_one_below_limit_allowed(client, auth_headers, fake_supabase):
    """STARTER plan: max_biens=5, user has 4 biens -> creation allowed (201)."""
    fake_supabase.store["biens"] = [
        {
            "id": f"bien-{i}",
            "id_sci": "sci-1",
            "adresse": f"{i} rue Presque",
            "ville": "Paris",
            "code_postal": "75001",
            "type_locatif": "nu",
            "loyer_cc": 500,
            "charges": 0,
            "tmi": 0,
        }
        for i in range(4)
    ]
    fake_supabase.store["subscriptions"] = [
        {
            "user_id": "user-123",
            "plan_key": "starter",
            "status": "active",
            "is_active": True,
            "max_scis": 1,
            "max_biens": 5,
            "features": {
                "multi_sci_enabled": False,
                "charges_enabled": True,
                "fiscalite_enabled": False,
                "quitus_enabled": True,
                "cerfa_enabled": False,
                "priority_support": False,
            },
        }
    ]

    response = client.post("/api/v1/biens/", json=BIEN_PAYLOAD, headers=auth_headers)

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"


def test_lifetime_plan_no_limit_on_biens(client, auth_headers, fake_supabase):
    """LIFETIME plan: max_biens=None (unlimited) -> creation always allowed."""
    fake_supabase.store["biens"] = [
        {
            "id": f"bien-{i}",
            "id_sci": "sci-1",
            "adresse": f"{i} rue Infini",
            "ville": "Paris",
            "code_postal": "75001",
            "type_locatif": "nu",
            "loyer_cc": 500,
            "charges": 0,
            "tmi": 0,
        }
        for i in range(50)
    ]
    fake_supabase.store["subscriptions"] = [
        {
            "user_id": "user-123",
            "plan_key": "lifetime",
            "status": "paid",
            "is_active": True,
            "max_scis": None,
            "max_biens": None,
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

    response = client.post("/api/v1/biens/", json=BIEN_PAYLOAD, headers=auth_headers)

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"


def test_lifetime_plan_no_limit_on_scis(client, auth_headers, fake_supabase):
    """LIFETIME plan: max_scis=None (unlimited) -> creation always allowed."""
    fake_supabase.store["subscriptions"] = [
        {
            "user_id": "user-123",
            "plan_key": "lifetime",
            "status": "paid",
            "is_active": True,
            "max_scis": None,
            "max_biens": None,
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

    response = client.post("/api/v1/scis/", json=SCI_PAYLOAD, headers=auth_headers)

    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"


def test_create_sci_over_quota_with_multiple_existing(client, auth_headers, fake_supabase):
    """PRO plan: max_scis=10, user already has 10 SCIs -> 402 PlanLimitError."""
    fake_supabase.store["associes"] = [
        {
            "id": f"associe-{i}",
            "id_sci": f"sci-{i}",
            "user_id": "user-123",
            "nom": "Test User",
            "email": "test@sci.local",
            "part": 100,
            "role": "gerant",
        }
        for i in range(10)
    ]
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

    response = client.post("/api/v1/scis/", json=SCI_PAYLOAD, headers=auth_headers)

    assert response.status_code == 402, f"Expected 402, got {response.status_code}: {response.text}"
    body = response.json()
    assert body["code"] == "plan_limit_reached"
    assert body["details"]["resource"] == "scis"
    assert body["details"]["current"] == 10
    assert body["details"]["limit"] == 10
