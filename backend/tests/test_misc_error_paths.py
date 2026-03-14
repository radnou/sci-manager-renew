"""Targeted error path tests for small uncovered blocks across multiple modules."""
from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest
from app.core.exceptions import DatabaseError
from app.core.paywall import AssocieMembership
from tests.conftest import FakeResult


class ErrorQuery:
    def select(self, *a, **k): return self
    def eq(self, *a, **k): return self
    def in_(self, *a, **k): return self
    def insert(self, *a, **k): return self
    def update(self, *a, **k): return self
    def delete(self, *a, **k): return self
    def order(self, *a, **k): return self
    def gte(self, *a, **k): return self
    def lte(self, *a, **k): return self
    def limit(self, *a, **k): return self
    def execute(self):
        return FakeResult(data=[], error="db_error")


class ErrorClient:
    def table(self, name):
        return ErrorQuery()


MEMBERSHIP = AssocieMembership(user_id="u1", sci_id="s1", role="gerant", associe_id="a1")


def _mock_request():
    r = MagicMock()
    r.state = MagicMock()
    return r


# ---------------------------------------------------------------------------
# charges.py error paths (lines 49-52, 77-80)
# ---------------------------------------------------------------------------

class TestChargesEndpointErrors:
    @pytest.mark.asyncio
    async def test_list_charges_db_error(self):
        from app.api.v1 import charges as charges_mod
        with patch.object(charges_mod, "get_supabase_user_client", return_value=ErrorClient()):
            with pytest.raises(DatabaseError):
                await charges_mod.list_charges(_mock_request(), id_sci="sci-1", user_id="user-123")

    @pytest.mark.asyncio
    async def test_create_charge_db_error(self):
        from app.api.v1 import charges as charges_mod
        from app.models.charges import ChargeCreate
        payload = ChargeCreate(id_bien="b1", type_charge="copro", montant=200, date_paiement="2026-01-01")
        with patch.object(charges_mod, "get_supabase_user_client", return_value=ErrorClient()), \
             patch.object(charges_mod, "SubscriptionService") as mock_sub:
            mock_sub.ensure_feature_enabled.return_value = None
            with pytest.raises(DatabaseError):
                await charges_mod.create_charge(payload, _mock_request(), user_id="user-123")


# ---------------------------------------------------------------------------
# dashboard.py error paths (lines 113-117)
# ---------------------------------------------------------------------------

class TestDashboardEndpointErrors:
    @pytest.mark.asyncio
    async def test_dashboard_unexpected_error(self):
        from app.api.v1.dashboard import get_dashboard

        class CrashClient:
            def table(self, name):
                raise RuntimeError("unexpected db crash")

        with patch("app.api.v1.dashboard._get_client", return_value=CrashClient()):
            with pytest.raises(DatabaseError, match="Unable to fetch dashboard"):
                await get_dashboard(_mock_request(), "user-123")


# ---------------------------------------------------------------------------
# notifications.py error paths (lines 63, 82, 105, 127)
# ---------------------------------------------------------------------------

class TestNotificationsEndpointErrors:
    @pytest.mark.asyncio
    async def test_list_notifications_error(self):
        from app.api.v1.notifications import list_notifications
        with patch("app.api.v1.notifications._get_client", return_value=ErrorClient()):
            with pytest.raises(DatabaseError):
                await list_notifications(request=_mock_request(), user_id="user-123")

    @pytest.mark.asyncio
    async def test_mark_as_read_error(self):
        from app.api.v1 import notifications as notif_mod
        with patch.object(notif_mod, "get_supabase_user_client", return_value=ErrorClient()):
            with pytest.raises(DatabaseError):
                await notif_mod.mark_as_read(notification_id="notif-1", request=_mock_request(), user_id="user-123")

    # mark_all_as_read and unread_count use _get_client which delegates
    # to get_supabase_user_client — already covered via HTTP integration tests


# ---------------------------------------------------------------------------
# notification_preferences.py error paths (lines 34, 56, 105)
# ---------------------------------------------------------------------------

class TestNotificationPrefsEndpointErrors:
    @pytest.mark.asyncio
    async def test_list_preferences_error(self):
        from app.api.v1 import notification_preferences as np_mod
        with patch.object(np_mod, "_get_client", return_value=ErrorClient()):
            with pytest.raises(DatabaseError):
                await np_mod.get_notification_preferences(request=_mock_request(), user_id="user-123")

    # update_notification_preference error path covered via HTTP integration tests


# ---------------------------------------------------------------------------
# onboarding.py error path (line 148)
# ---------------------------------------------------------------------------

    # onboarding error paths covered via HTTP integration tests


# ---------------------------------------------------------------------------
# external_services.py error path (lines 65-67)
# ---------------------------------------------------------------------------

class TestExternalServicesErrors:
    def test_coerce_timeout_none_returns_default(self):
        from app.core.external_services import coerce_timeout
        assert coerce_timeout(None, 5.0) == 5.0

    def test_coerce_timeout_value_returns_max(self):
        from app.core.external_services import coerce_timeout
        assert coerce_timeout(0.05, 5.0) == 0.1  # clamped to 0.1
        assert coerce_timeout(10.0, 5.0) == 10.0

    @pytest.mark.asyncio
    async def test_run_with_retry_non_retryable(self):
        from app.core.external_services import run_with_retry

        def always_fail():
            raise RuntimeError("permanent error")

        with pytest.raises(RuntimeError, match="permanent"):
            await run_with_retry(
                operation="test_op",
                func=always_fail,
                context={},
            )
