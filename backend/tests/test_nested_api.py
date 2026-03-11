"""
Integration tests for new Sprint 2-7 API endpoints.

Uses the same sync TestClient + FakeSupabaseClient pattern from conftest.py.
"""


def test_dashboard_requires_auth(client):
    response = client.get("/api/v1/dashboard")
    assert response.status_code == 401


def test_dashboard_returns_200(client, auth_headers, fake_supabase):
    fake_supabase.store["subscriptions"] = [
        {
            "user_id": "user-123",
            "plan_key": "pro",
            "status": "active",
            "is_active": True,
            "onboarding_completed": True,
            "max_scis": 10,
            "max_biens": 20,
            "features": {},
        }
    ]
    response = client.get("/api/v1/dashboard", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "alertes" in data
    assert "kpis" in data
    assert "scis" in data
    assert "activite" in data


def test_dashboard_kpis_structure(client, auth_headers, fake_supabase):
    fake_supabase.store["subscriptions"] = [
        {
            "user_id": "user-123",
            "plan_key": "pro",
            "is_active": True,
            "onboarding_completed": True,
            "max_scis": 10,
            "max_biens": 20,
            "features": {},
        }
    ]
    response = client.get("/api/v1/dashboard", headers=auth_headers)
    assert response.status_code == 200
    kpis = response.json()["kpis"]
    assert "sci_count" in kpis
    assert "biens_count" in kpis
    assert "taux_recouvrement" in kpis
    assert "cashflow_net" in kpis


def test_onboarding_requires_auth(client):
    response = client.get("/api/v1/onboarding")
    assert response.status_code == 401


def test_onboarding_status_returns_200(client, auth_headers, fake_supabase):
    fake_supabase.store["subscriptions"] = [
        {
            "user_id": "user-123",
            "plan_key": "pro",
            "is_active": True,
            "onboarding_completed": False,
            "max_scis": 10,
            "max_biens": 20,
            "features": {},
        }
    ]
    response = client.get("/api/v1/onboarding", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "completed" in data
    assert "sci_created" in data
    assert "bien_created" in data


def test_onboarding_complete_returns_200(client, auth_headers, fake_supabase):
    fake_supabase.store["subscriptions"] = [
        {
            "user_id": "user-123",
            "plan_key": "pro",
            "is_active": True,
            "onboarding_completed": False,
            "max_scis": 10,
            "max_biens": 20,
            "features": {},
        }
    ]
    response = client.post("/api/v1/onboarding/complete", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["completed"] is True


def test_notification_preferences_requires_auth(client):
    response = client.get("/api/v1/user/notification-preferences")
    assert response.status_code == 401


def test_notification_preferences_returns_defaults(client, auth_headers, fake_supabase):
    fake_supabase.store["notification_preferences"] = []
    response = client.get("/api/v1/user/notification-preferences", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "preferences" in data
    prefs = data["preferences"]
    assert len(prefs) == 7
    types = {p["type"] for p in prefs}
    assert "late_payment" in types
    assert "bail_expiring" in types


def test_notification_preferences_update(client, auth_headers, fake_supabase):
    fake_supabase.store["notification_preferences"] = []
    payload = {
        "preferences": [
            {"type": "late_payment", "email_enabled": False, "in_app_enabled": True},
        ]
    }
    response = client.put(
        "/api/v1/user/notification-preferences",
        json=payload,
        headers=auth_headers,
    )
    assert response.status_code == 200


def test_finances_requires_auth(client):
    response = client.get("/api/v1/finances")
    assert response.status_code == 401


def test_finances_returns_200(client, auth_headers, fake_supabase):
    # Seed subscription in format expected by SubscriptionService
    fake_supabase.store["subscriptions"] = [
        {
            "user_id": "user-123",
            "plan_key": "pro",
            "plan_name": "Pro",
            "status": "active",
            "mode": "subscription",
            "is_active": True,
            "onboarding_completed": True,
            "max_scis": 10,
            "max_biens": 20,
            "max_associes": None,
            "features": {},
            "stripe_price_id": "price_test",
        }
    ]
    response = client.get("/api/v1/finances", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "revenus_total" in data
    assert "charges_total" in data
    assert "cashflow_net" in data
    assert "evolution_mensuelle" in data
    assert "repartition_sci" in data


def test_finances_with_period_param(client, auth_headers, fake_supabase):
    fake_supabase.store["subscriptions"] = [
        {
            "user_id": "user-123",
            "plan_key": "pro",
            "plan_name": "Pro",
            "status": "active",
            "mode": "subscription",
            "is_active": True,
            "onboarding_completed": True,
            "max_scis": 10,
            "max_biens": 20,
            "max_associes": None,
            "features": {},
            "stripe_price_id": "price_test",
        }
    ]
    response = client.get("/api/v1/finances?period=6m", headers=auth_headers)
    assert response.status_code == 200


def test_nested_biens_list_requires_auth(client):
    """Nested biens endpoint requires authentication."""
    response = client.get("/api/v1/scis/sci-1/biens")
    assert response.status_code == 401


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_rentabilite_service():
    """Unit test for the rentabilite calculation service."""
    from app.services.rentabilite_service import calculate_rentabilite

    result = calculate_rentabilite(
        prix_acquisition=200000,
        loyer_mensuel=1000,
        charges_mensuelles=200,
        prime_pno_annuelle=360,
        frais_agence_annuel=1200,
    )
    assert result["brute"] == 6.0  # (1000*12) / 200000 * 100
    assert result["cashflow_annuel"] > 0
    assert "nette" in result
    assert "cashflow_mensuel" in result


def test_rentabilite_service_zero_acquisition():
    from app.services.rentabilite_service import calculate_rentabilite

    result = calculate_rentabilite(prix_acquisition=0, loyer_mensuel=1000)
    assert result["brute"] == 0
    assert result["nette"] == 0
