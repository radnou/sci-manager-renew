"""Tests for admin panel endpoints — protected by X-Admin-Key header."""

import pytest
from unittest.mock import patch

from app.core.config import settings

# Ensure ADMIN_SECRET_KEY is set for tests
if not settings.admin_secret_key:
    settings.admin_secret_key = "test-admin-key"

# ── Helper: build admin headers ──────────────────────────────────────

ADMIN_KEY = settings.admin_secret_key


def _admin_headers(key: str | None = ADMIN_KEY) -> dict[str, str]:
    """Build admin auth headers."""
    if key is None:
        return {}
    return {"X-Admin-Key": key}


# ═══════════════════════════════════════════════════════════════════════
# GET /api/v1/admin/metrics
# ═══════════════════════════════════════════════════════════════════════


class TestAdminMetrics:
    def test_no_key_returns_403(self, client):
        response = client.get("/api/v1/admin/metrics")
        assert response.status_code == 403

    def test_wrong_key_returns_403(self, client):
        response = client.get("/api/v1/admin/metrics", headers={"X-Admin-Key": "wrong-key"})
        assert response.status_code == 403

    def test_query_param_key_returns_403(self, client):
        """Verify that legacy query param auth is rejected."""
        response = client.get(f"/api/v1/admin/metrics?key={ADMIN_KEY}")
        assert response.status_code == 403

    @patch("app.api.v1.admin.compute_hero_metrics")
    def test_returns_metrics(self, mock_compute, client):
        mock_compute.return_value = {
            "north_star": {"value": 5, "previous": 3, "trend": "up", "change_pct": 66.7},
        }
        response = client.get("/api/v1/admin/metrics", headers=_admin_headers())
        assert response.status_code == 200
        assert "north_star" in response.json()


# ═══════════════════════════════════════════════════════════════════════
# GET /api/v1/admin/alerts
# ═══════════════════════════════════════════════════════════════════════


class TestAdminAlerts:
    def test_no_key_returns_403(self, client):
        response = client.get("/api/v1/admin/alerts")
        assert response.status_code == 403

    @patch("app.api.v1.admin.compute_business_alerts")
    def test_returns_alerts(self, mock_compute, client):
        mock_compute.return_value = {"alerts": []}
        response = client.get("/api/v1/admin/alerts", headers=_admin_headers())
        assert response.status_code == 200
        assert "alerts" in response.json()


# ═══════════════════════════════════════════════════════════════════════
# GET /api/v1/admin/funnel
# ═══════════════════════════════════════════════════════════════════════


class TestAdminFunnel:
    def test_no_key_returns_403(self, client):
        response = client.get("/api/v1/admin/funnel")
        assert response.status_code == 403

    @patch("app.api.v1.admin.compute_activation_funnel")
    def test_returns_funnel(self, mock_compute, client):
        mock_compute.return_value = {
            "steps": [{"label": "Inscrits", "count": 10, "rate": 100.0}],
            "bottleneck_index": 0,
        }
        response = client.get("/api/v1/admin/funnel", headers=_admin_headers())
        assert response.status_code == 200
        assert "steps" in response.json()


# ═══════════════════════════════════════════════════════════════════════
# GET /api/v1/admin/users
# ═══════════════════════════════════════════════════════════════════════


class TestAdminListUsers:
    def test_no_key_returns_403(self, client):
        response = client.get("/api/v1/admin/users")
        assert response.status_code == 403

    @patch("app.api.v1.admin.compute_enriched_users")
    def test_returns_user_list(self, mock_compute, client):
        mock_compute.return_value = {"users": [], "total": 0, "page": 1, "per_page": 50}
        response = client.get("/api/v1/admin/users", headers=_admin_headers())
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data

    @patch("app.api.v1.admin.compute_enriched_users")
    def test_default_pagination(self, mock_compute, client):
        mock_compute.return_value = {"users": [], "total": 0, "page": 1, "per_page": 50}
        client.get("/api/v1/admin/users", headers=_admin_headers())
        mock_compute.assert_called_once_with(
            search=None,
            status_filter=None,
            plan_filter=None,
            sort="created_at",
            page=1,
            per_page=50,
        )

    @patch("app.api.v1.admin.compute_enriched_users")
    def test_custom_pagination(self, mock_compute, client):
        mock_compute.return_value = {"users": [], "total": 0, "page": 2, "per_page": 10}
        response = client.get(
            "/api/v1/admin/users?page=2&per_page=10", headers=_admin_headers()
        )
        data = response.json()
        assert data["page"] == 2
        assert data["per_page"] == 10

    @patch("app.api.v1.admin.compute_enriched_users")
    def test_filters_forwarded(self, mock_compute, client):
        mock_compute.return_value = {"users": [], "total": 0, "page": 1, "per_page": 50}
        client.get(
            "/api/v1/admin/users?search=test@example.com&status=power_user&plan=pro&sort=last_activity",
            headers=_admin_headers(),
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
    def test_no_key_returns_403(self, client):
        response = client.get("/api/v1/admin/users/user-123")
        assert response.status_code == 403

    def test_returns_user_data(self, client, fake_supabase):
        fake_supabase.store["subscriptions"] = [
            {"user_id": "user-123", "stripe_price_id": "price_pro_demo", "status": "active"},
        ]
        response = client.get("/api/v1/admin/users/user-123", headers=_admin_headers())
        assert response.status_code == 200
        data = response.json()
        assert "user" in data
        assert "scis" in data
        assert "subscription" in data

    def test_user_fields_populated(self, client):
        response = client.get("/api/v1/admin/users/user-123", headers=_admin_headers())
        data = response.json()
        user = data["user"]
        assert user["id"] == "user-123"
        assert "email" in user
        assert "created_at" in user

    def test_user_without_subscription(self, client, fake_supabase):
        fake_supabase.store["subscriptions"] = []
        response = client.get("/api/v1/admin/users/user-123", headers=_admin_headers())
        data = response.json()
        assert data["subscription"] is None


# ═══════════════════════════════════════════════════════════════════════
# Cross-cutting: Secret key gating on ALL endpoints
# ═══════════════════════════════════════════════════════════════════════


class TestAdminGating:
    ENDPOINTS = [
        "/api/v1/admin/metrics",
        "/api/v1/admin/alerts",
        "/api/v1/admin/funnel",
        "/api/v1/admin/users",
        "/api/v1/admin/users/user-123",
    ]

    @pytest.mark.parametrize("endpoint", ENDPOINTS)
    def test_all_endpoints_reject_no_key(self, client, endpoint):
        response = client.get(endpoint)
        assert response.status_code == 403

    @pytest.mark.parametrize("endpoint", ENDPOINTS)
    def test_all_endpoints_reject_wrong_header_key(self, client, endpoint):
        response = client.get(endpoint, headers={"X-Admin-Key": "totally-wrong"})
        assert response.status_code == 403

    @pytest.mark.parametrize("endpoint", ENDPOINTS)
    def test_all_endpoints_reject_query_param_key(self, client, endpoint):
        """Legacy query param auth must be rejected."""
        response = client.get(f"{endpoint}?key={ADMIN_KEY}")
        assert response.status_code == 403
