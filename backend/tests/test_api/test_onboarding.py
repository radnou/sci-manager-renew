"""Tests for onboarding endpoints — verifies B-5 fix (sci_id returned)."""


def test_onboarding_status_requires_auth(client):
    response = client.get("/api/v1/onboarding")
    assert response.status_code == 401


def test_onboarding_status_returns_sci_id(client, auth_headers, fake_supabase):
    """When user has a SCI, sci_id should be returned in the status."""
    fake_supabase.store["subscriptions"] = [
        {"user_id": "user-123", "onboarding_completed": False},
    ]
    response = client.get("/api/v1/onboarding", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["sci_created"] is True
    assert data["sci_id"] == "sci-1"


def test_onboarding_status_no_sci(client, auth_headers, fake_supabase):
    """When user has no SCI, sci_id should be null."""
    fake_supabase.store["associes"] = []
    fake_supabase.store["subscriptions"] = [
        {"user_id": "user-123", "onboarding_completed": False},
    ]
    response = client.get("/api/v1/onboarding", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["sci_created"] is False
    assert data["sci_id"] is None


def test_onboarding_complete(client, auth_headers, fake_supabase):
    fake_supabase.store["subscriptions"] = [
        {"user_id": "user-123", "onboarding_completed": False},
    ]
    response = client.post("/api/v1/onboarding/complete", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is True
