"""Tests for core.paywall — subscription and membership gating."""

from __future__ import annotations

import pytest
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient
from jose import jwt

from app.core.config import settings
from app.core.paywall import (
    AssocieMembership,
    SubscriptionInfo,
    require_active_subscription,
    require_gerant_role,
    require_sci_membership,
)
from app.core.rate_limit import limiter

# Disable rate limiting in tests
limiter.enabled = False

# Fixed UUIDs for test data
SCI_1_UUID = "00000000-0000-0000-0000-000000000001"
SCI_2_UUID = "00000000-0000-0000-0000-000000000002"
SCI_UNKNOWN_UUID = "00000000-0000-0000-0000-000000000999"


# ---------------------------------------------------------------------------
# Helper: build a minimal FastAPI app with paywall-protected routes
# ---------------------------------------------------------------------------

def _build_app():
    test_app = FastAPI()

    @test_app.get("/sub-required")
    async def sub_required(info: SubscriptionInfo = Depends(require_active_subscription)):
        return {
            "user_id": info.user_id,
            "plan_key": info.plan_key,
            "is_active": info.is_active,
            "onboarding_completed": info.onboarding_completed,
        }

    @test_app.get("/sci/{sci_id}/member")
    async def sci_member(membership: AssocieMembership = Depends(require_sci_membership)):
        return {
            "user_id": membership.user_id,
            "sci_id": membership.sci_id,
            "role": membership.role,
            "associe_id": membership.associe_id,
        }

    @test_app.get("/sci/{sci_id}/gerant")
    async def sci_gerant(membership: AssocieMembership = Depends(require_gerant_role)):
        return {
            "user_id": membership.user_id,
            "sci_id": membership.sci_id,
            "role": membership.role,
        }

    return test_app


def _auth_headers(user_id: str = "user-123") -> dict[str, str]:
    token = jwt.encode(
        {"sub": user_id, "role": "authenticated"},
        settings.supabase_jwt_secret,
        algorithm="HS256",
    )
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def paywall_supabase(fake_supabase):
    """Fake supabase with UUID-based SCI/associes data for paywall tests."""
    fake_supabase.store["associes"] = [
        {
            "id": "associe-1",
            "id_sci": SCI_1_UUID,
            "user_id": "user-123",
            "nom": "Test User",
            "email": "test@sci.local",
            "part": 60,
            "role": "gerant",
        },
        {
            "id": "associe-1b",
            "id_sci": SCI_1_UUID,
            "user_id": "user-456",
            "nom": "Camille Bernard",
            "email": "camille@sci.local",
            "part": 40,
            "role": "associe",
        },
    ]
    return fake_supabase


@pytest.fixture
def paywall_client(monkeypatch, paywall_supabase):
    """TestClient wired to a minimal app with paywall dependencies patched."""
    from app.core import paywall as paywall_mod, supabase_client as supabase_client_mod
    from app.services import subscription_service

    def fake_service():
        return paywall_supabase
    fake_service.cache_clear = lambda: None

    monkeypatch.setattr(paywall_mod, "get_supabase_service_client", fake_service)
    monkeypatch.setattr(supabase_client_mod, "get_supabase_service_client", fake_service)
    monkeypatch.setattr(subscription_service, "get_supabase_service_client", fake_service)

    app = _build_app()
    with TestClient(app, base_url="http://testserver") as tc:
        yield tc


# ---------------------------------------------------------------------------
# require_active_subscription tests
# ---------------------------------------------------------------------------

class TestRequireActiveSubscription:
    """Tests for the require_active_subscription dependency."""

    def test_free_plan_is_active_by_default(self, paywall_client, paywall_supabase):
        """Users with no subscription row default to free plan and are active."""
        paywall_supabase.store["subscriptions"] = []

        resp = paywall_client.get("/sub-required", headers=_auth_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan_key"] == "free"
        assert data["is_active"] is True

    def test_active_subscription_returns_plan(self, paywall_client, paywall_supabase):
        """Active paid subscription returns plan info."""
        paywall_supabase.store["subscriptions"] = [
            {
                "user_id": "user-123",
                "plan_key": "pro",
                "status": "active",
                "is_active": True,
                "max_scis": 10,
                "max_biens": 20,
                "onboarding_completed": True,
                "features": {"multi_sci_enabled": True},
            }
        ]

        resp = paywall_client.get("/sub-required", headers=_auth_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan_key"] == "pro"
        assert data["is_active"] is True
        assert data["onboarding_completed"] is True

    def test_inactive_subscription_returns_402(self, paywall_client, paywall_supabase, monkeypatch):
        """Expired/cancelled subscription returns 402."""
        monkeypatch.setattr(settings, "feature_plan_entitlements_enforcement", "strict")

        paywall_supabase.store["subscriptions"] = [
            {
                "user_id": "user-123",
                "plan_key": "pro",
                "status": "cancelled",
                "is_active": False,
                "max_scis": 10,
                "max_biens": 20,
                "features": {"multi_sci_enabled": True},
            }
        ]

        resp = paywall_client.get("/sub-required", headers=_auth_headers())
        assert resp.status_code == 402
        data = resp.json()
        assert data["detail"]["code"] == "subscription_required"
        assert data["detail"]["redirect"] == "/pricing"

    def test_no_auth_returns_401(self, paywall_client):
        """Missing auth token returns 401."""
        resp = paywall_client.get("/sub-required")
        assert resp.status_code in (401, 403)

    def test_onboarding_not_completed_defaults_false(self, paywall_client, paywall_supabase):
        """When onboarding_completed is missing, defaults to False."""
        paywall_supabase.store["subscriptions"] = [
            {
                "user_id": "user-123",
                "plan_key": "starter",
                "status": "active",
                "is_active": True,
                "max_scis": 3,
                "max_biens": 5,
                "features": {},
            }
        ]

        resp = paywall_client.get("/sub-required", headers=_auth_headers())
        assert resp.status_code == 200
        assert resp.json()["onboarding_completed"] is False


# ---------------------------------------------------------------------------
# require_sci_membership tests
# ---------------------------------------------------------------------------

class TestRequireSciMembership:
    """Tests for the require_sci_membership dependency."""

    def test_member_gets_membership(self, paywall_client, paywall_supabase):
        """User who is associe of the SCI gets membership info."""
        resp = paywall_client.get(f"/sci/{SCI_1_UUID}/member", headers=_auth_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "user-123"
        assert data["sci_id"] == SCI_1_UUID
        assert data["role"] == "gerant"

    def test_non_member_gets_404(self, paywall_client, paywall_supabase):
        """User not associated with SCI gets 404."""
        resp = paywall_client.get(f"/sci/{SCI_UNKNOWN_UUID}/member", headers=_auth_headers())
        assert resp.status_code == 404

    def test_different_user_gets_404(self, paywall_client, paywall_supabase):
        """User not associated with a specific SCI gets 404."""
        resp = paywall_client.get(f"/sci/{SCI_1_UUID}/member", headers=_auth_headers("user-999"))
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# require_gerant_role tests
# ---------------------------------------------------------------------------

class TestRequireGerantRole:
    """Tests for the require_gerant_role dependency."""

    def test_gerant_allowed(self, paywall_client, paywall_supabase):
        """Gerant role passes the check."""
        resp = paywall_client.get(f"/sci/{SCI_1_UUID}/gerant", headers=_auth_headers())
        assert resp.status_code == 200
        data = resp.json()
        assert data["role"] == "gerant"

    def test_associe_blocked_with_403(self, paywall_client, paywall_supabase):
        """Non-gerant associe gets 403."""
        resp = paywall_client.get(f"/sci/{SCI_1_UUID}/gerant", headers=_auth_headers("user-456"))
        assert resp.status_code == 403

    def test_non_member_blocked_with_404(self, paywall_client, paywall_supabase):
        """Non-member of SCI gets 404 (membership check fails first)."""
        resp = paywall_client.get(f"/sci/{SCI_UNKNOWN_UUID}/gerant", headers=_auth_headers())
        assert resp.status_code == 404
