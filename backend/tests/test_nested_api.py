"""
Integration tests for nested/aggregated API endpoints.

Tests use dependency overrides to bypass auth and paywall,
and monkeypatch Supabase clients to avoid real DB calls.
Each test verifies that routes resolve correctly and return
the expected response shapes.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.core.paywall import (
    AssocieMembership,
    SubscriptionInfo,
    require_active_subscription,
    require_gerant_role,
    require_sci_membership,
)
from app.core.security import get_current_user
from app.main import app

# ---------------------------------------------------------------------------
# Fake dependencies
# ---------------------------------------------------------------------------

TEST_USER_ID = "test-user-id"


async def fake_user():
    return TEST_USER_ID


async def fake_subscription():
    return SubscriptionInfo(
        user_id=TEST_USER_ID,
        plan_key="pro",
        is_active=True,
        onboarding_completed=True,
    )


async def fake_membership():
    return AssocieMembership(
        user_id=TEST_USER_ID,
        sci_id="sci-1",
        role="gerant",
        associe_id="1",
    )


async def fake_gerant():
    return await fake_membership()


# ---------------------------------------------------------------------------
# Fake Supabase helpers (minimal, just enough for the routes under test)
# ---------------------------------------------------------------------------


class _FakeResult:
    def __init__(self, data: list[dict] | None = None, error=None):
        self.data = data or []
        self.error = error
        self.count = len(self.data)


class _FakeQuery:
    """Chainable query builder that always returns empty results."""

    def __init__(self, data: list[dict] | None = None):
        self._data = data or []

    def select(self, *_a, **_kw):
        return self

    def insert(self, *_a, **_kw):
        return self

    def update(self, *_a, **_kw):
        return self

    def upsert(self, *_a, **_kw):
        return self

    def delete(self):
        return self

    def eq(self, *_a, **_kw):
        return self

    def in_(self, *_a, **_kw):
        return self

    def gte(self, *_a, **_kw):
        return self

    def lte(self, *_a, **_kw):
        return self

    def is_(self, *_a, **_kw):
        return self

    def order(self, *_a, **_kw):
        return self

    def limit(self, *_a, **_kw):
        return self

    def execute(self):
        return _FakeResult(data=self._data)


class _FakeSupabaseClient:
    """Minimal fake Supabase client that returns empty results for any table."""

    def __init__(self, store: dict[str, list[dict]] | None = None):
        self._store = store or {}

    def table(self, name: str):
        return _FakeQuery(data=self._store.get(name, []))


def _make_fake_client(**table_data: list[dict]) -> _FakeSupabaseClient:
    return _FakeSupabaseClient(store=table_data)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _override_dependencies():
    """Apply dependency overrides for all tests in this module."""
    app.dependency_overrides[get_current_user] = fake_user
    app.dependency_overrides[require_active_subscription] = fake_subscription
    app.dependency_overrides[require_sci_membership] = fake_membership
    app.dependency_overrides[require_gerant_role] = fake_gerant
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _allow_test_host():
    """Ensure the TrustedHostMiddleware accepts our test host."""
    original = settings.allowed_hosts
    settings.allowed_hosts = ["test", "testserver", "localhost", "*.gerersci.fr"]
    yield
    settings.allowed_hosts = original


@pytest.fixture()
def empty_supabase():
    """A fake Supabase client that returns empty results for all tables."""
    return _make_fake_client()


# ---------------------------------------------------------------------------
# Dashboard tests
# ---------------------------------------------------------------------------


class TestDashboard:
    """Tests for GET /api/v1/dashboard"""

    @pytest.mark.asyncio
    async def test_dashboard_returns_200(self):
        """Dashboard endpoint resolves and returns expected top-level keys."""
        fake_client = _make_fake_client(
            associes=[
                {"id": "a1", "id_sci": "sci-1", "user_id": TEST_USER_ID, "role": "gerant"},
            ],
            sci=[
                {"id": "sci-1", "nom": "Test SCI", "statut": "active"},
            ],
            biens=[],
            loyers=[],
            charges=[],
            locataires=[],
        )
        with (
            patch("app.api.v1.dashboard._get_client", return_value=fake_client),
            patch("app.services.dashboard_service.get_supabase_service_client", return_value=fake_client),
        ):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/dashboard")
                assert response.status_code == 200
                data = response.json()
                assert "alertes" in data
                assert "kpis" in data
                assert "scis" in data
                assert "activite" in data

    @pytest.mark.asyncio
    async def test_dashboard_kpis_structure(self):
        """KPIs block has expected numeric fields."""
        fake_client = _make_fake_client(
            associes=[],
            sci=[],
            biens=[],
            loyers=[],
            charges=[],
        )
        with patch("app.api.v1.dashboard._get_client", return_value=fake_client):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/dashboard")
                assert response.status_code == 200
                kpis = response.json()["kpis"]
                for key in ("sci_count", "biens_count", "taux_recouvrement", "cashflow_net"):
                    assert key in kpis

    @pytest.mark.asyncio
    async def test_dashboard_empty_user(self):
        """Dashboard for a user with no SCIs returns empty lists and zero KPIs."""
        fake_client = _make_fake_client(associes=[], sci=[], biens=[], loyers=[], charges=[])
        with patch("app.api.v1.dashboard._get_client", return_value=fake_client):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/dashboard")
                assert response.status_code == 200
                data = response.json()
                assert data["alertes"] == []
                assert data["scis"] == []
                assert data["activite"] == []
                assert data["kpis"]["sci_count"] == 0


# ---------------------------------------------------------------------------
# Onboarding tests
# ---------------------------------------------------------------------------


class TestOnboarding:
    """Tests for /api/v1/onboarding endpoints."""

    @pytest.mark.asyncio
    async def test_get_onboarding_status_returns_200(self):
        """GET /api/v1/onboarding returns onboarding progress fields."""
        fake_client = _make_fake_client(
            subscriptions=[],
            associes=[],
            biens=[],
            baux=[],
            notification_preferences=[],
        )
        with patch("app.api.v1.onboarding.get_supabase_service_client", return_value=fake_client):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/onboarding")
                assert response.status_code == 200
                data = response.json()
                for key in ("completed", "sci_created", "bien_created", "bail_created", "notifications_set"):
                    assert key in data

    @pytest.mark.asyncio
    async def test_onboarding_status_all_false_for_new_user(self):
        """A new user with no data should have all onboarding steps as False."""
        fake_client = _make_fake_client(
            subscriptions=[],
            associes=[],
            biens=[],
            baux=[],
            notification_preferences=[],
        )
        with patch("app.api.v1.onboarding.get_supabase_service_client", return_value=fake_client):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/onboarding")
                assert response.status_code == 200
                data = response.json()
                assert data["completed"] is False
                assert data["sci_created"] is False
                assert data["bien_created"] is False
                assert data["bail_created"] is False
                assert data["notifications_set"] is False

    @pytest.mark.asyncio
    async def test_complete_onboarding_returns_200(self):
        """POST /api/v1/onboarding/complete marks onboarding as done."""
        fake_client = _make_fake_client(subscriptions=[{"user_id": TEST_USER_ID, "onboarding_completed": False}])
        with patch("app.api.v1.onboarding.get_supabase_service_client", return_value=fake_client):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.post("/api/v1/onboarding/complete")
                assert response.status_code == 200
                data = response.json()
                assert "completed" in data
                assert data["completed"] is True


# ---------------------------------------------------------------------------
# Finances tests
# ---------------------------------------------------------------------------


class TestFinances:
    """Tests for GET /api/v1/finances"""

    @pytest.mark.asyncio
    async def test_finances_returns_200(self):
        """Finances endpoint returns expected financial overview structure."""
        fake_client = _make_fake_client(
            associes=[{"id_sci": "sci-1", "user_id": TEST_USER_ID}],
            sci=[{"id": "sci-1", "nom": "Test SCI"}],
            biens=[],
            loyers=[],
            charges=[],
        )
        with patch("app.api.v1.finances.get_supabase_service_client", return_value=fake_client):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/finances")
                assert response.status_code == 200
                data = response.json()
                for key in (
                    "revenus_total",
                    "charges_total",
                    "cashflow_net",
                    "taux_recouvrement",
                    "patrimoine_total",
                    "rentabilite_moyenne",
                    "evolution_mensuelle",
                    "repartition_sci",
                ):
                    assert key in data

    @pytest.mark.asyncio
    async def test_finances_empty_user_returns_zeros(self):
        """A user with no SCIs gets zeroed-out financial data."""
        fake_client = _make_fake_client(associes=[], sci=[], biens=[], loyers=[], charges=[])
        with patch("app.api.v1.finances.get_supabase_service_client", return_value=fake_client):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/finances")
                assert response.status_code == 200
                data = response.json()
                assert data["revenus_total"] == 0
                assert data["charges_total"] == 0
                assert data["cashflow_net"] == 0

    @pytest.mark.asyncio
    async def test_finances_accepts_period_param(self):
        """The period query parameter is accepted without error."""
        fake_client = _make_fake_client(associes=[], sci=[], biens=[], loyers=[], charges=[])
        with patch("app.api.v1.finances.get_supabase_service_client", return_value=fake_client):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                for period in ("6m", "12m", "24m"):
                    response = await client.get(f"/api/v1/finances?period={period}")
                    assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_finances_lists_are_lists(self):
        """evolution_mensuelle and repartition_sci are always lists."""
        fake_client = _make_fake_client(associes=[], sci=[], biens=[], loyers=[], charges=[])
        with patch("app.api.v1.finances.get_supabase_service_client", return_value=fake_client):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/finances")
                data = response.json()
                assert isinstance(data["evolution_mensuelle"], list)
                assert isinstance(data["repartition_sci"], list)


# ---------------------------------------------------------------------------
# Notification preferences tests
# ---------------------------------------------------------------------------


class TestNotificationPreferences:
    """Tests for GET /api/v1/user/notification-preferences"""

    @pytest.mark.asyncio
    async def test_get_notification_preferences_returns_200(self):
        """Endpoint returns default notification preferences."""
        fake_client = _make_fake_client(notification_preferences=[])
        with patch("app.api.v1.notification_preferences._get_client", return_value=fake_client):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/user/notification-preferences")
                assert response.status_code == 200
                data = response.json()
                assert "preferences" in data
                assert isinstance(data["preferences"], list)

    @pytest.mark.asyncio
    async def test_notification_preferences_have_defaults(self):
        """When no preferences exist, all default types are returned."""
        fake_client = _make_fake_client(notification_preferences=[])
        with patch("app.api.v1.notification_preferences._get_client", return_value=fake_client):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/user/notification-preferences")
                data = response.json()
                prefs = data["preferences"]
                # There are 7 default notification types
                assert len(prefs) == 7
                types = {p["type"] for p in prefs}
                assert "late_payment" in types
                assert "bail_expiring" in types
                assert "quittance_pending" in types

    @pytest.mark.asyncio
    async def test_notification_preference_item_structure(self):
        """Each preference item has type, email_enabled, and in_app_enabled."""
        fake_client = _make_fake_client(notification_preferences=[])
        with patch("app.api.v1.notification_preferences._get_client", return_value=fake_client):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                response = await client.get("/api/v1/user/notification-preferences")
                prefs = response.json()["preferences"]
                for pref in prefs:
                    assert "type" in pref
                    assert "email_enabled" in pref
                    assert "in_app_enabled" in pref


# ---------------------------------------------------------------------------
# Paywall / Auth enforcement tests
# ---------------------------------------------------------------------------


class TestPaywallEnforcement:
    """
    Without dependency overrides, protected endpoints should return
    401 (no auth) or 402 (no subscription).
    """

    @pytest.fixture(autouse=True)
    def _clear_overrides(self):
        """Remove dependency overrides so real auth/paywall logic runs."""
        saved = dict(app.dependency_overrides)
        app.dependency_overrides.clear()
        yield
        app.dependency_overrides.update(saved)

    @pytest.mark.asyncio
    async def test_dashboard_requires_auth(self):
        """GET /api/v1/dashboard without token returns 401."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/dashboard")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_onboarding_requires_auth(self):
        """GET /api/v1/onboarding without token returns 401."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/onboarding")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_finances_requires_auth(self):
        """GET /api/v1/finances without token returns 401."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/finances")
            # finances uses require_active_subscription which depends on get_current_user
            # Without a token, the first dependency (get_current_user) fails with 401
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_notification_preferences_requires_auth(self):
        """GET /api/v1/user/notification-preferences without token returns 401."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/user/notification-preferences")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_complete_onboarding_requires_auth(self):
        """POST /api/v1/onboarding/complete without token returns 401."""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/api/v1/onboarding/complete")
            assert response.status_code == 401


# ---------------------------------------------------------------------------
# Health check (sanity — no auth required)
# ---------------------------------------------------------------------------


class TestHealthSanity:
    """Quick sanity check that unauthenticated health endpoint works."""

    @pytest.fixture(autouse=True)
    def _clear_overrides(self):
        """Remove overrides to prove health needs no auth."""
        saved = dict(app.dependency_overrides)
        app.dependency_overrides.clear()
        yield
        app.dependency_overrides.update(saved)

    @pytest.mark.asyncio
    async def test_health_live_returns_200(self):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/health/live")
            assert response.status_code == 200
