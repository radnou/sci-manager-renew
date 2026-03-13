"""Tests for notification_service and notification_cron modules."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from tests.conftest import FakeSupabaseClient


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_client(prefs: list[dict] | None = None) -> FakeSupabaseClient:
    """Return a FakeSupabaseClient pre-seeded with optional prefs."""
    client = FakeSupabaseClient()
    client.store.setdefault("notifications", [])
    client.store["notification_preferences"] = prefs if prefs is not None else []
    return client


# send_notification_email is imported lazily inside notification_service and
# does not yet exist as a module-level symbol in email_service.  We patch it
# with create=True so unittest.mock will insert it into the module dict for
# the duration of each test.
EMAIL_PATCH = "app.services.email_service.send_notification_email"
EMAIL_PATCH_KWARGS: dict = {"create": True}


# ---------------------------------------------------------------------------
# notification_service tests
# ---------------------------------------------------------------------------

class TestCreateNotificationWithEmail:

    @pytest.mark.asyncio
    async def test_defaults_both_enabled_when_no_prefs(self):
        """When no preference row exists, both in_app and email are enabled."""
        client = make_client([])

        with patch(EMAIL_PATCH, new_callable=AsyncMock, create=True) as mock_email:
            from app.services.notification_service import create_notification_with_email

            await create_notification_with_email(
                client,
                user_id="user-123",
                notification_type="late_payment",
                data={"title": "Test", "message": "msg", "metadata": {}},
            )

        # In-app notification inserted
        notifs = client.store["notifications"]
        assert len(notifs) == 1
        assert notifs[0]["user_id"] == "user-123"
        assert notifs[0]["type"] == "late_payment"
        assert notifs[0]["title"] == "Test"
        assert notifs[0]["message"] == "msg"

        # Email was attempted
        mock_email.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_in_app_disabled_by_preference(self):
        """When in_app_enabled=False, no notification row is inserted."""
        prefs = [
            {"user_id": "user-123", "type": "late_payment",
             "in_app_enabled": False, "email_enabled": True}
        ]
        client = make_client(prefs)

        with patch(EMAIL_PATCH, new_callable=AsyncMock, create=True) as mock_email:
            from app.services.notification_service import create_notification_with_email

            await create_notification_with_email(
                client,
                user_id="user-123",
                notification_type="late_payment",
                data={"title": "T", "message": "M", "metadata": {}},
            )

        assert len(client.store.get("notifications", [])) == 0
        mock_email.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_email_disabled_by_preference(self):
        """When email_enabled=False, email is not sent but in-app is created."""
        prefs = [
            {"user_id": "user-123", "type": "late_payment",
             "in_app_enabled": True, "email_enabled": False}
        ]
        client = make_client(prefs)

        with patch(EMAIL_PATCH, new_callable=AsyncMock, create=True) as mock_email:
            from app.services.notification_service import create_notification_with_email

            await create_notification_with_email(
                client,
                user_id="user-123",
                notification_type="late_payment",
                data={"title": "T", "message": "M", "metadata": {}},
            )

        assert len(client.store["notifications"]) == 1
        mock_email.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_both_disabled_by_preference(self):
        """When both are disabled, nothing happens."""
        prefs = [
            {"user_id": "user-123", "type": "late_payment",
             "in_app_enabled": False, "email_enabled": False}
        ]
        client = make_client(prefs)

        with patch(EMAIL_PATCH, new_callable=AsyncMock, create=True) as mock_email:
            from app.services.notification_service import create_notification_with_email

            await create_notification_with_email(
                client,
                user_id="user-123",
                notification_type="late_payment",
                data={"title": "T", "message": "M", "metadata": {}},
            )

        assert len(client.store.get("notifications", [])) == 0
        mock_email.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_notification_uses_default_title_if_missing(self):
        """Notification title defaults to 'Notification' when not in data."""
        client = make_client([])

        with patch(EMAIL_PATCH, new_callable=AsyncMock, create=True):
            from app.services.notification_service import create_notification_with_email

            await create_notification_with_email(
                client,
                user_id="user-999",
                notification_type="bail_expiring",
                data={},  # no title / message / metadata
            )

        notifs = client.store["notifications"]
        assert len(notifs) == 1
        assert notifs[0]["title"] == "Notification"
        assert notifs[0]["message"] == ""
        assert notifs[0]["metadata"] == {}

    @pytest.mark.asyncio
    async def test_email_failure_does_not_raise(self):
        """Email errors are caught; the function should not propagate them."""
        client = make_client([])

        async def boom(*_args, **_kwargs):
            raise RuntimeError("SMTP failure")

        with patch(EMAIL_PATCH, side_effect=boom, create=True):
            from app.services.notification_service import create_notification_with_email

            # Should NOT raise
            await create_notification_with_email(
                client,
                user_id="user-123",
                notification_type="late_payment",
                data={"title": "T", "message": "M", "metadata": {}},
            )

        # In-app notification was still created before the email attempt
        assert len(client.store["notifications"]) == 1

    @pytest.mark.asyncio
    async def test_notification_metadata_stored_correctly(self):
        """Custom metadata dict is persisted verbatim."""
        client = make_client([])
        meta = {"loyer_id": "loyer-42", "bien_adresse": "12 rue de la Paix"}

        with patch(EMAIL_PATCH, new_callable=AsyncMock, create=True):
            from app.services.notification_service import create_notification_with_email

            await create_notification_with_email(
                client,
                user_id="user-123",
                notification_type="quittance_pending",
                data={"title": "Quittance", "message": "msg", "metadata": meta},
            )

        assert client.store["notifications"][0]["metadata"] == meta


# ---------------------------------------------------------------------------
# notification_cron tests
# ---------------------------------------------------------------------------

class TestCheckLatePayments:

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_late_loyers(self):
        """No late loyers → 0 notifications sent."""
        client = make_client([])

        with patch(EMAIL_PATCH, new_callable=AsyncMock, create=True):
            from app.services.notification_cron import check_late_payments

            result = await check_late_payments(client)

        assert result == 0

    @pytest.mark.asyncio
    async def test_notifies_owner_for_late_loyer(self):
        """One late loyer with matching owners → 1 notification per owner."""
        client = make_client([])
        # Seed a late loyer (date_loyer well in the past)
        client.store["loyers"] = [
            {
                "id": "loyer-late-1",
                "id_bien": "bien-1",
                "id_sci": "sci-1",
                "date_loyer": "2020-01-01",   # far in the past
                "montant": 800,
                "statut": "en_attente",
                "quitus_genere": False,
                "biens": {"id_sci": "sci-1", "adresse": "10 rue Test", "ville": "Paris"},
            }
        ]

        with patch(EMAIL_PATCH, new_callable=AsyncMock, create=True):
            from app.services.notification_cron import check_late_payments

            result = await check_late_payments(client)

        # sci-1 has 2 owners (user-123 and user-456) in the fake store
        assert result == 2
        notifs = client.store.get("notifications", [])
        assert len(notifs) == 2
        types = {n["type"] for n in notifs}
        assert types == {"late_payment"}

    @pytest.mark.asyncio
    async def test_skips_loyer_without_sci_id(self):
        """Loyers with no resolvable sci_id are skipped."""
        client = make_client([])
        client.store["loyers"] = [
            {
                "id": "loyer-orphan",
                "id_bien": None,
                "id_sci": None,
                "date_loyer": "2020-01-01",
                "montant": 500,
                "statut": "en_retard",
                "quitus_genere": False,
                "biens": None,
            }
        ]

        with patch(EMAIL_PATCH, new_callable=AsyncMock, create=True):
            from app.services.notification_cron import check_late_payments

            result = await check_late_payments(client)

        assert result == 0


class TestCheckExpiringBails:

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_expiring_baux(self):
        """No baux in the window → 0 notifications."""
        client = make_client([])
        client.store.setdefault("baux", [])

        with patch(EMAIL_PATCH, new_callable=AsyncMock, create=True):
            from app.services.notification_cron import check_expiring_bails

            result = await check_expiring_bails(client)

        assert result == 0

    @pytest.mark.asyncio
    async def test_notifies_owner_for_expiring_bail(self):
        """A bail expiring within 90 days triggers owner notifications."""
        from datetime import datetime, timedelta, timezone

        client = make_client([])
        soon = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
        client.store["baux"] = [
            {
                "id": "bail-1",
                "id_bien": "bien-1",
                "date_fin": soon,
                "biens": {"id_sci": "sci-1", "adresse": "10 rue Test", "ville": "Paris"},
            }
        ]

        with patch(EMAIL_PATCH, new_callable=AsyncMock, create=True):
            from app.services.notification_cron import check_expiring_bails

            result = await check_expiring_bails(client)

        assert result == 2  # 2 owners of sci-1
        notifs = client.store.get("notifications", [])
        assert all(n["type"] == "bail_expiring" for n in notifs)

    @pytest.mark.asyncio
    async def test_skips_bail_without_sci_id(self):
        """Baux whose bien has no sci_id are skipped."""
        from datetime import datetime, timedelta, timezone

        client = make_client([])
        soon = (datetime.now(timezone.utc) + timedelta(days=10)).strftime("%Y-%m-%d")
        client.store["baux"] = [
            {
                "id": "bail-orphan",
                "id_bien": "bien-x",
                "date_fin": soon,
                "biens": {"id_sci": None, "adresse": "Orphan", "ville": "Somewhere"},
            }
        ]

        with patch(EMAIL_PATCH, new_callable=AsyncMock, create=True):
            from app.services.notification_cron import check_expiring_bails

            result = await check_expiring_bails(client)

        assert result == 0


class TestCheckPendingQuittances:

    @pytest.mark.asyncio
    async def test_returns_zero_when_all_quittances_generated(self):
        """No loyers with quitus_genere=False → 0 notifications."""
        client = make_client([])
        client.store["loyers"] = [
            {
                "id": "loyer-done",
                "id_sci": "sci-1",
                "id_bien": "bien-1",
                "date_loyer": "2025-01-01",
                "montant": 700,
                "statut": "paye",
                "quitus_genere": True,
                "biens": {"id_sci": "sci-1", "adresse": "done", "ville": "Paris"},
            }
        ]

        with patch(EMAIL_PATCH, new_callable=AsyncMock, create=True):
            from app.services.notification_cron import check_pending_quittances

            result = await check_pending_quittances(client)

        assert result == 0

    @pytest.mark.asyncio
    async def test_notifies_owner_for_pending_quittance(self):
        """Paid loyer without quittance triggers a notification per owner."""
        client = make_client([])
        client.store["loyers"] = [
            {
                "id": "loyer-pending",
                "id_sci": "sci-1",
                "id_bien": "bien-1",
                "date_loyer": "2025-03-01",
                "montant": 900,
                "statut": "paye",
                "quitus_genere": False,
                "biens": {"id_sci": "sci-1", "adresse": "9 bd Voltaire", "ville": "Paris"},
            }
        ]

        with patch(EMAIL_PATCH, new_callable=AsyncMock, create=True):
            from app.services.notification_cron import check_pending_quittances

            result = await check_pending_quittances(client)

        assert result == 2
        notifs = client.store.get("notifications", [])
        assert all(n["type"] == "quittance_pending" for n in notifs)


class TestCheckExpiringPno:

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_expiring_pno(self):
        """No PNO policies expiring within 30 days → 0 notifications."""
        client = make_client([])
        client.store.setdefault("assurances_pno", [])

        with patch(EMAIL_PATCH, new_callable=AsyncMock, create=True):
            from app.services.notification_cron import check_expiring_pno

            result = await check_expiring_pno(client)

        assert result == 0

    @pytest.mark.asyncio
    async def test_notifies_owner_for_expiring_pno(self):
        """PNO policy expiring within 30 days triggers owner notifications."""
        from datetime import datetime, timedelta, timezone

        client = make_client([])
        soon = (datetime.now(timezone.utc) + timedelta(days=15)).strftime("%Y-%m-%d")
        client.store["assurances_pno"] = [
            {
                "id": "pno-1",
                "id_bien": "bien-1",
                "assureur": "AXA",
                "date_fin": soon,
                "biens": {"id_sci": "sci-1", "adresse": "10 rue Test", "ville": "Paris"},
            }
        ]

        with patch(EMAIL_PATCH, new_callable=AsyncMock, create=True):
            from app.services.notification_cron import check_expiring_pno

            result = await check_expiring_pno(client)

        assert result == 2  # 2 owners of sci-1
        notifs = client.store.get("notifications", [])
        assert all(n["type"] == "pno_expiring" for n in notifs)
        # Message should include the assureur name
        assert all("AXA" in n["message"] for n in notifs)

    @pytest.mark.asyncio
    async def test_skips_pno_without_sci_id(self):
        """PNO records whose bien has no sci_id are skipped."""
        from datetime import datetime, timedelta, timezone

        client = make_client([])
        soon = (datetime.now(timezone.utc) + timedelta(days=5)).strftime("%Y-%m-%d")
        client.store["assurances_pno"] = [
            {
                "id": "pno-orphan",
                "id_bien": "bien-x",
                "assureur": "Orphan",
                "date_fin": soon,
                "biens": {"id_sci": None, "adresse": "Nowhere", "ville": "N/A"},
            }
        ]

        with patch(EMAIL_PATCH, new_callable=AsyncMock, create=True):
            from app.services.notification_cron import check_expiring_pno

            result = await check_expiring_pno(client)

        assert result == 0
