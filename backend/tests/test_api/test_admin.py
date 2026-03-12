"""Tests for admin API endpoints."""

from __future__ import annotations

from jose import jwt

from app.core.config import settings


def _admin_headers(user_id: str = "admin-user") -> dict[str, str]:
    token = jwt.encode(
        {"sub": user_id, "role": "authenticated"},
        settings.supabase_jwt_secret,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


def _setup_admin(fake_supabase, user_id: str = "admin-user"):
    """Add user to admins table so get_current_admin passes."""
    fake_supabase.store.setdefault("admins", []).append({"user_id": user_id})


def _patch_admin_service_client(monkeypatch, fake_supabase):
    """Patch get_service_client in the admin module."""
    from app.api.v1 import admin
    monkeypatch.setattr(admin, "get_service_client", lambda: fake_supabase)


def test_admin_stats(client, auth_headers, fake_supabase, monkeypatch):
    """Admin stats returns platform-wide counts."""
    _setup_admin(fake_supabase)
    _patch_admin_service_client(monkeypatch, fake_supabase)

    fake_supabase.store["subscriptions"] = [
        {"user_id": "u1", "plan_key": "pro", "is_active": True},
        {"user_id": "u2", "plan_key": "starter", "is_active": True},
        {"user_id": "u3", "plan_key": "pro", "is_active": False},
    ]

    resp = client.get("/api/v1/admin/stats", headers=_admin_headers())
    assert resp.status_code == 200
    data = resp.json()

    assert "total_users" in data
    assert "total_scis" in data
    assert "total_biens" in data
    assert data["active_subscriptions"] == 2
    assert data["plan_breakdown"]["pro"] == 1
    assert data["plan_breakdown"]["starter"] == 1


def test_admin_stats_no_subscriptions(client, auth_headers, fake_supabase, monkeypatch):
    """Admin stats with no subscriptions shows zero active."""
    _setup_admin(fake_supabase)
    _patch_admin_service_client(monkeypatch, fake_supabase)

    fake_supabase.store["subscriptions"] = []

    resp = client.get("/api/v1/admin/stats", headers=_admin_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert data["active_subscriptions"] == 0
    assert data["plan_breakdown"] == {}


def test_admin_stats_forbidden_for_non_admin(client, auth_headers):
    """Non-admin user gets 403."""
    resp = client.get("/api/v1/admin/stats", headers=auth_headers)
    assert resp.status_code == 403


def test_admin_list_subscriptions(client, auth_headers, fake_supabase, monkeypatch):
    """Admin can list all subscriptions."""
    _setup_admin(fake_supabase)
    _patch_admin_service_client(monkeypatch, fake_supabase)

    fake_supabase.store["subscriptions"] = [
        {
            "user_id": "u1",
            "plan_key": "pro",
            "status": "active",
            "created_at": "2026-01-01",
        },
        {
            "user_id": "u2",
            "plan_key": "starter",
            "status": "cancelled",
            "created_at": "2025-12-01",
        },
    ]

    resp = client.get("/api/v1/admin/subscriptions", headers=_admin_headers())
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["subscriptions"]) == 2


def test_admin_list_subscriptions_forbidden_for_non_admin(client, auth_headers):
    """Non-admin user gets 403 for subscriptions list."""
    resp = client.get("/api/v1/admin/subscriptions", headers=auth_headers)
    assert resp.status_code == 403
