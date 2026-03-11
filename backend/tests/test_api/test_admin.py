"""Tests for admin panel endpoints."""


def test_admin_stats_requires_admin(client, auth_headers, fake_supabase):
    """Non-admin users should get 403."""
    fake_supabase.store["admins"] = []
    response = client.get("/api/v1/admin/stats", headers=auth_headers)
    assert response.status_code == 403


def test_admin_stats_returns_data(client, auth_headers, fake_supabase):
    """Admin user should get platform stats."""
    fake_supabase.store["subscriptions"] = [
        {"user_id": "user-123", "plan_key": "pro", "is_active": True},
        {"user_id": "user-456", "plan_key": "starter", "is_active": True},
        {"user_id": "user-789", "plan_key": "free", "is_active": False},
    ]
    response = client.get("/api/v1/admin/stats", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data
    assert "total_scis" in data
    assert "total_biens" in data
    assert "active_subscriptions" in data
    assert data["active_subscriptions"] == 2
    assert "plan_breakdown" in data


def test_admin_stats_no_auth(client):
    """Unauthenticated request should get 401."""
    response = client.get("/api/v1/admin/stats")
    assert response.status_code == 401


def test_admin_list_users(client, auth_headers, fake_supabase):
    """Admin should be able to list users."""
    fake_supabase.store["subscriptions"] = [
        {"user_id": "user-123", "plan_key": "pro", "is_active": True},
    ]
    response = client.get("/api/v1/admin/users", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "page" in data


def test_admin_get_user(client, auth_headers, fake_supabase):
    """Admin should be able to get a specific user."""
    fake_supabase.store["subscriptions"] = [
        {"user_id": "user-123", "plan_key": "pro", "is_active": True},
    ]
    response = client.get("/api/v1/admin/users/user-123", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "user" in data
    assert "scis" in data
    assert "subscription" in data


def test_admin_list_subscriptions(client, auth_headers, fake_supabase):
    """Admin should be able to list all subscriptions."""
    fake_supabase.store["subscriptions"] = [
        {"user_id": "user-123", "plan_key": "pro", "is_active": True, "created_at": "2026-01-01"},
    ]
    response = client.get("/api/v1/admin/subscriptions", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "subscriptions" in data
