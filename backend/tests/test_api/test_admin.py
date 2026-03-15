"""Tests for admin panel endpoints — target ≥95% coverage of app/api/v1/admin.py."""

import jwt
import pytest
from unittest.mock import patch

from app.core.config import settings


# ── Helper: build auth headers for a non-admin user ─────────────────────

def _non_admin_headers(user_id: str = "user-non-admin") -> dict[str, str]:
    token = jwt.encode(
        {"sub": user_id, "role": "authenticated"},
        settings.supabase_jwt_secret,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


# ═══════════════════════════════════════════════════════════════════════
# GET /api/v1/admin/metrics
# ═══════════════════════════════════════════════════════════════════════


class TestAdminMetrics:
    """Tests for the admin_metrics endpoint."""

    def test_no_auth_returns_401(self, client):
        response = client.get("/api/v1/admin/metrics")
        assert response.status_code == 401

    def test_non_admin_returns_403(self, client, fake_supabase):
        fake_supabase.store["admins"] = []
        response = client.get("/api/v1/admin/metrics", headers=_non_admin_headers())
        assert response.status_code == 403

    @patch("app.api.v1.admin.compute_hero_metrics")
    def test_returns_metrics(self, mock_compute, client, auth_headers):
        mock_compute.return_value = {
            "north_star": {"value": 5, "previous": 3, "trend": "up", "change_pct": 66.7},
        }
        response = client.get("/api/v1/admin/metrics", headers=auth_headers)
        assert response.status_code == 200
        assert "north_star" in response.json()


# ═══════════════════════════════════════════════════════════════════════
# GET /api/v1/admin/alerts
# ═══════════════════════════════════════════════════════════════════════


class TestAdminAlerts:
    """Tests for the admin_alerts endpoint."""

    def test_no_auth_returns_401(self, client):
        response = client.get("/api/v1/admin/alerts")
        assert response.status_code == 401

    def test_non_admin_returns_403(self, client, fake_supabase):
        fake_supabase.store["admins"] = []
        response = client.get("/api/v1/admin/alerts", headers=_non_admin_headers())
        assert response.status_code == 403

    @patch("app.api.v1.admin.compute_business_alerts")
    def test_returns_alerts(self, mock_compute, client, auth_headers):
        mock_compute.return_value = {"alerts": []}
        response = client.get("/api/v1/admin/alerts", headers=auth_headers)
        assert response.status_code == 200
        assert "alerts" in response.json()


# ═══════════════════════════════════════════════════════════════════════
# GET /api/v1/admin/funnel
# ═══════════════════════════════════════════════════════════════════════


class TestAdminFunnel:
    """Tests for the admin_funnel endpoint."""

    def test_no_auth_returns_401(self, client):
        response = client.get("/api/v1/admin/funnel")
        assert response.status_code == 401

    def test_non_admin_returns_403(self, client, fake_supabase):
        fake_supabase.store["admins"] = []
        response = client.get("/api/v1/admin/funnel", headers=_non_admin_headers())
        assert response.status_code == 403

    @patch("app.api.v1.admin.compute_activation_funnel")
    def test_returns_funnel(self, mock_compute, client, auth_headers):
        mock_compute.return_value = {
            "steps": [{"label": "Inscrits", "count": 10, "rate": 100.0}],
            "bottleneck_index": 0,
        }
        response = client.get("/api/v1/admin/funnel", headers=auth_headers)
        assert response.status_code == 200
        assert "steps" in response.json()


# ═══════════════════════════════════════════════════════════════════════
# GET /api/v1/admin/users
# ═══════════════════════════════════════════════════════════════════════


class TestAdminListUsers:
    """Tests for the admin_list_users endpoint."""

    def test_no_auth_returns_401(self, client):
        response = client.get("/api/v1/admin/users")
        assert response.status_code == 401

    def test_non_admin_returns_403(self, client, fake_supabase):
        fake_supabase.store["admins"] = []
        response = client.get("/api/v1/admin/users", headers=_non_admin_headers())
        assert response.status_code == 403

    @patch("app.api.v1.admin.compute_enriched_users")
    def test_returns_user_list(self, mock_compute, client, auth_headers):
        mock_compute.return_value = {"users": [], "total": 0, "page": 1, "per_page": 50}
        response = client.get("/api/v1/admin/users", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data

    @patch("app.api.v1.admin.compute_enriched_users")
    def test_default_pagination(self, mock_compute, client, auth_headers):
        mock_compute.return_value = {"users": [], "total": 0, "page": 1, "per_page": 50}
        client.get("/api/v1/admin/users", headers=auth_headers)
        mock_compute.assert_called_once_with(
            search=None,
            status_filter=None,
            plan_filter=None,
            sort="created_at",
            page=1,
            per_page=50,
        )

    @patch("app.api.v1.admin.compute_enriched_users")
    def test_custom_pagination(self, mock_compute, client, auth_headers):
        mock_compute.return_value = {"users": [], "total": 0, "page": 2, "per_page": 10}
        response = client.get("/api/v1/admin/users?page=2&per_page=10", headers=auth_headers)
        data = response.json()
        assert data["page"] == 2
        assert data["per_page"] == 10

    def test_page_validation_min(self, client, auth_headers):
        """page < 1 should fail validation."""
        response = client.get("/api/v1/admin/users?page=0", headers=auth_headers)
        assert response.status_code == 422

    def test_per_page_validation_max(self, client, auth_headers):
        """per_page > 100 should fail validation."""
        response = client.get("/api/v1/admin/users?per_page=200", headers=auth_headers)
        assert response.status_code == 422

    @patch("app.api.v1.admin.compute_enriched_users")
    def test_filters_forwarded(self, mock_compute, client, auth_headers):
        mock_compute.return_value = {"users": [], "total": 0, "page": 1, "per_page": 50}
        client.get(
            "/api/v1/admin/users?search=test@example.com&status=power_user&plan=pro&sort=last_activity",
            headers=auth_headers,
        )
        mock_compute.assert_called_once_with(
            search="test@example.com",
            status_filter="power_user",
            plan_filter="pro",
            sort="last_activity",
            page=1,
            per_page=50,
        )


# ═══════════════════════════════════════════════════════════════════════
# GET /api/v1/admin/users/{user_id}
# ═══════════════════════════════════════════════════════════════════════


class TestAdminGetUser:
    """Tests for the admin_get_user endpoint."""

    def test_no_auth_returns_401(self, client):
        response = client.get("/api/v1/admin/users/user-123")
        assert response.status_code == 401

    def test_non_admin_returns_403(self, client, fake_supabase):
        fake_supabase.store["admins"] = []
        response = client.get("/api/v1/admin/users/user-123", headers=_non_admin_headers())
        assert response.status_code == 403

    def test_returns_user_data(self, client, auth_headers, fake_supabase):
        fake_supabase.store["subscriptions"] = [
            {"user_id": "user-123", "stripe_price_id": "price_pro_demo", "status": "active"},
        ]
        response = client.get("/api/v1/admin/users/user-123", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "scis" in data
        assert "subscription" in data

    def test_user_fields_populated(self, client, auth_headers):
        response = client.get("/api/v1/admin/users/user-123", headers=auth_headers)
        data = response.json()
        user = data["user"]
        assert user["id"] == "user-123"
        assert "email" in user
        assert "created_at" in user

    def test_scis_for_user(self, client, auth_headers, fake_supabase):
        """SCIs are returned via associes join."""
        response = client.get("/api/v1/admin/users/user-123", headers=auth_headers)
        data = response.json()
        assert isinstance(data["scis"], list)
        assert len(data["scis"]) >= 1

    def test_user_with_subscription(self, client, auth_headers, fake_supabase):
        """Subscription data is returned when it exists."""
        fake_supabase.store["subscriptions"] = [
            {"user_id": "user-123", "stripe_price_id": "price_pro", "status": "active"},
        ]
        response = client.get("/api/v1/admin/users/user-123", headers=auth_headers)
        data = response.json()
        assert data["subscription"] is not None

    def test_user_without_subscription(self, client, auth_headers, fake_supabase):
        """No subscription -> subscription=None."""
        fake_supabase.store["subscriptions"] = []
        response = client.get("/api/v1/admin/users/user-123", headers=auth_headers)
        data = response.json()
        assert data["subscription"] is None

    def test_unknown_user_id(self, client, auth_headers, fake_supabase):
        """Looking up an unknown user_id still returns (via FakeAuthAdmin)."""
        response = client.get("/api/v1/admin/users/user-unknown", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["id"] == "user-unknown"
        assert data["scis"] == []
        assert data["subscription"] is None


# ═══════════════════════════════════════════════════════════════════════
# Cross-cutting: Auth & admin gating on ALL endpoints
# ═══════════════════════════════════════════════════════════════════════


class TestAdminGating:
    """Ensure all admin endpoints are protected by the admin dependency."""

    ENDPOINTS = [
        "/api/v1/admin/metrics",
        "/api/v1/admin/alerts",
        "/api/v1/admin/funnel",
        "/api/v1/admin/users",
        "/api/v1/admin/users/user-123",
    ]

    @pytest.mark.parametrize("endpoint", ENDPOINTS)
    def test_all_endpoints_reject_unauthenticated(self, client, endpoint):
        response = client.get(endpoint)
        assert response.status_code == 401

    @pytest.mark.parametrize("endpoint", ENDPOINTS)
    def test_all_endpoints_reject_non_admin(self, client, fake_supabase, endpoint):
        fake_supabase.store["admins"] = []
        response = client.get(endpoint, headers=_non_admin_headers())
        assert response.status_code == 403

    def test_invalid_token_returns_401(self, client):
        """A completely invalid JWT token should return 401."""
        response = client.get(
            "/api/v1/admin/metrics",
            headers={"Authorization": "Bearer invalid.jwt.token"},
        )
        assert response.status_code == 401

    def test_missing_bearer_prefix(self, client):
        """Auth header without 'Bearer ' prefix should fail."""
        token = jwt.encode(
            {"sub": "user-123", "role": "authenticated"},
            settings.supabase_jwt_secret,
            algorithm="HS256",
        )
        response = client.get(
            "/api/v1/admin/metrics",
            headers={"Authorization": token},
        )
        assert response.status_code == 401
