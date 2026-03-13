"""Tests for admin panel endpoints — target ≥95% coverage of app/api/v1/admin.py."""

import jwt
import pytest

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
# GET /api/v1/admin/stats
# ═══════════════════════════════════════════════════════════════════════


class TestAdminStats:
    """Tests for the admin_stats endpoint."""

    def test_no_auth_returns_401(self, client):
        response = client.get("/api/v1/admin/stats")
        assert response.status_code == 401

    def test_non_admin_returns_403(self, client, fake_supabase):
        fake_supabase.store["admins"] = []
        response = client.get("/api/v1/admin/stats", headers=_non_admin_headers())
        assert response.status_code == 403

    def test_admin_removed_returns_403(self, client, auth_headers, fake_supabase):
        """Even a previously-valid admin gets 403 if removed from admins table."""
        fake_supabase.store["admins"] = []
        response = client.get("/api/v1/admin/stats", headers=auth_headers)
        assert response.status_code == 403

    def test_returns_all_stat_keys(self, client, auth_headers):
        response = client.get("/api/v1/admin/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        for key in ("total_users", "total_scis", "total_biens", "active_subscriptions", "plan_breakdown"):
            assert key in data

    def test_counts_match_seed_data(self, client, auth_headers, fake_supabase):
        """Verify counts reflect the seed data in the fake store."""
        response = client.get("/api/v1/admin/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_users"] == len(fake_supabase.store["associes"])
        assert data["total_scis"] == len(fake_supabase.store["sci"])
        assert data["total_biens"] == len(fake_supabase.store["biens"])

    def test_active_subscriptions_count(self, client, auth_headers, fake_supabase):
        """Only active/trialing/paid subscriptions are counted."""
        fake_supabase.store["subscriptions"] = [
            {"user_id": "u1", "stripe_price_id": "price_pro_demo", "status": "active"},
            {"user_id": "u2", "stripe_price_id": "price_starter_demo", "status": "trialing"},
            {"user_id": "u3", "stripe_price_id": "price_pro_demo", "status": "paid"},
            {"user_id": "u4", "stripe_price_id": "price_pro_demo", "status": "canceled"},
            {"user_id": "u5", "stripe_price_id": None, "status": "past_due"},
        ]
        response = client.get("/api/v1/admin/stats", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["active_subscriptions"] == 3

    def test_plan_breakdown_keys(self, client, auth_headers, fake_supabase):
        """Plan breakdown groups by resolved plan key."""
        fake_supabase.store["subscriptions"] = [
            {"user_id": "u1", "stripe_price_id": settings.stripe_pro_price_id, "status": "active"},
            {"user_id": "u2", "stripe_price_id": settings.stripe_starter_price_id, "status": "active"},
            {"user_id": "u3", "stripe_price_id": "unknown_price", "status": "active"},
        ]
        response = client.get("/api/v1/admin/stats", headers=auth_headers)
        data = response.json()
        breakdown = data["plan_breakdown"]
        assert isinstance(breakdown, dict)
        # The unknown price_id resolves to "free" via resolve_plan_key_from_price_id
        assert breakdown.get("free", 0) >= 1

    def test_empty_subscriptions(self, client, auth_headers, fake_supabase):
        """No subscriptions at all -> active_subscriptions=0, empty breakdown."""
        fake_supabase.store["subscriptions"] = []
        response = client.get("/api/v1/admin/stats", headers=auth_headers)
        data = response.json()
        assert data["active_subscriptions"] == 0
        assert data["plan_breakdown"] == {}

    def test_no_scis_or_biens(self, client, auth_headers, fake_supabase):
        """Empty tables return zero counts."""
        fake_supabase.store["sci"] = []
        fake_supabase.store["biens"] = []
        fake_supabase.store["associes"] = []
        response = client.get("/api/v1/admin/stats", headers=auth_headers)
        data = response.json()
        assert data["total_scis"] == 0
        assert data["total_biens"] == 0
        assert data["total_users"] == 0

    def test_null_stripe_price_id_in_active_sub(self, client, auth_headers, fake_supabase):
        """Active subscription with null price_id resolves to 'free' plan."""
        fake_supabase.store["subscriptions"] = [
            {"user_id": "u1", "stripe_price_id": None, "status": "active"},
        ]
        response = client.get("/api/v1/admin/stats", headers=auth_headers)
        data = response.json()
        assert data["active_subscriptions"] == 1
        # resolve_plan_key_from_price_id(None) returns None -> key falls to "free"
        assert data["plan_breakdown"].get("free") == 1


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

    def test_returns_user_list(self, client, auth_headers):
        response = client.get("/api/v1/admin/users", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "page" in data
        assert "per_page" in data

    def test_default_pagination(self, client, auth_headers):
        response = client.get("/api/v1/admin/users", headers=auth_headers)
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 50

    def test_custom_pagination(self, client, auth_headers):
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

    def test_user_fields(self, client, auth_headers, fake_supabase):
        """Each user object has expected fields."""
        fake_supabase.store["subscriptions"] = [
            {"user_id": "user-123", "stripe_price_id": settings.stripe_pro_price_id, "status": "active", "stripe_customer_id": "cus_test"},
        ]
        response = client.get("/api/v1/admin/users", headers=auth_headers)
        data = response.json()
        assert len(data["users"]) > 0
        user = data["users"][0]
        for field in ("id", "email", "created_at", "plan_key", "is_active", "stripe_customer_id"):
            assert field in user

    def test_user_with_active_subscription(self, client, auth_headers, fake_supabase):
        """User with active subscription shows is_active=True."""
        fake_supabase.store["subscriptions"] = [
            {"user_id": "user-123", "stripe_price_id": settings.stripe_pro_price_id, "status": "active", "stripe_customer_id": "cus_x"},
        ]
        response = client.get("/api/v1/admin/users", headers=auth_headers)
        user = response.json()["users"][0]
        assert user["is_active"] is True

    def test_user_with_no_subscription(self, client, auth_headers, fake_supabase):
        """User without any subscription shows plan_key='free' and is_active=False."""
        fake_supabase.store["subscriptions"] = []
        response = client.get("/api/v1/admin/users", headers=auth_headers)
        user = response.json()["users"][0]
        assert user["plan_key"] == "free"
        assert user["is_active"] is False

    def test_user_with_canceled_subscription(self, client, auth_headers, fake_supabase):
        """Canceled subscription -> is_active=False."""
        fake_supabase.store["subscriptions"] = [
            {"user_id": "user-123", "stripe_price_id": settings.stripe_pro_price_id, "status": "canceled", "stripe_customer_id": "cus_c"},
        ]
        response = client.get("/api/v1/admin/users", headers=auth_headers)
        user = response.json()["users"][0]
        assert user["is_active"] is False


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
        # user-123 is associe in sci-1 and sci-2 per seed data
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
# GET /api/v1/admin/subscriptions
# ═══════════════════════════════════════════════════════════════════════


class TestAdminListSubscriptions:
    """Tests for the admin_list_subscriptions endpoint."""

    def test_no_auth_returns_401(self, client):
        response = client.get("/api/v1/admin/subscriptions")
        assert response.status_code == 401

    def test_non_admin_returns_403(self, client, fake_supabase):
        fake_supabase.store["admins"] = []
        response = client.get("/api/v1/admin/subscriptions", headers=_non_admin_headers())
        assert response.status_code == 403

    def test_returns_subscriptions_list(self, client, auth_headers, fake_supabase):
        fake_supabase.store["subscriptions"] = [
            {"user_id": "u1", "stripe_price_id": "p1", "status": "active", "created_at": "2026-01-01"},
            {"user_id": "u2", "stripe_price_id": "p2", "status": "canceled", "created_at": "2026-02-01"},
        ]
        response = client.get("/api/v1/admin/subscriptions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "subscriptions" in data
        assert len(data["subscriptions"]) == 2

    def test_empty_subscriptions(self, client, auth_headers, fake_supabase):
        fake_supabase.store["subscriptions"] = []
        response = client.get("/api/v1/admin/subscriptions", headers=auth_headers)
        data = response.json()
        assert data["subscriptions"] == []

    def test_ordered_by_created_at_desc(self, client, auth_headers, fake_supabase):
        """Subscriptions are ordered by created_at descending."""
        fake_supabase.store["subscriptions"] = [
            {"user_id": "u1", "stripe_price_id": "p1", "status": "active", "created_at": "2026-01-01"},
            {"user_id": "u2", "stripe_price_id": "p2", "status": "active", "created_at": "2026-03-01"},
            {"user_id": "u3", "stripe_price_id": "p3", "status": "active", "created_at": "2026-02-01"},
        ]
        response = client.get("/api/v1/admin/subscriptions", headers=auth_headers)
        subs = response.json()["subscriptions"]
        dates = [s["created_at"] for s in subs]
        assert dates == sorted(dates, reverse=True)


# ═══════════════════════════════════════════════════════════════════════
# Cross-cutting: Auth & admin gating on ALL endpoints
# ═══════════════════════════════════════════════════════════════════════


class TestAdminGating:
    """Ensure all admin endpoints are protected by the admin dependency."""

    ENDPOINTS = [
        "/api/v1/admin/stats",
        "/api/v1/admin/users",
        "/api/v1/admin/users/user-123",
        "/api/v1/admin/subscriptions",
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
            "/api/v1/admin/stats",
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
            "/api/v1/admin/stats",
            headers={"Authorization": token},
        )
        assert response.status_code == 401
