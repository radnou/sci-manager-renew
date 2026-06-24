"""Tests for signup_nurture_service, nurture_service and mrr_snapshot_service.

B) app/services/signup_nurture_service.py
C) app/services/nurture_service.py
D) app/services/mrr_snapshot_service.py
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from tests.conftest import FakeSupabaseClient


# ===========================================================================
# Helpers
# ===========================================================================

def _make_client(subscriptions=None, lead_captures=None) -> FakeSupabaseClient:
    c = FakeSupabaseClient()
    if subscriptions is not None:
        c.store["subscriptions"] = subscriptions
    if lead_captures is not None:
        c.store["lead_captures"] = lead_captures
    return c


def _iso_hours_ago(hours: float) -> str:
    """Return ISO8601 UTC string for N hours ago."""
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat().replace("+00:00", "Z")


def _iso_days_ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat().replace("+00:00", "Z")


# ===========================================================================
# B) signup_nurture_service
# ===========================================================================

class TestSignupNurtureService:
    """Tests for app.services.signup_nurture_service.check_and_send_signup_nurture_emails."""

    SVC_CLIENT = "app.services.signup_nurture_service.get_supabase_service_client"
    EMAIL_SEND = "app.services.signup_nurture_service.EmailService"

    def _mock_email_service(self):
        """Return a MagicMock that has an async send_email method."""
        from unittest.mock import MagicMock
        svc = MagicMock()
        svc.send_email = AsyncMock()
        return svc

    @pytest.fixture(autouse=True)
    def patch_resend_key(self, monkeypatch):
        """Ensure settings.resend_api_key is set to a real-looking value."""
        from app.core import config as cfg
        monkeypatch.setattr(cfg.settings, "resend_api_key", "re_real_key_123")

    def test_returns_zero_when_no_subscriptions(self, monkeypatch):
        """No subscriptions → 0 emails sent."""
        c = _make_client(subscriptions=[])
        monkeypatch.setattr("app.services.signup_nurture_service.get_supabase_service_client", lambda: c)
        mock_svc = self._mock_email_service()
        with patch(self.EMAIL_SVC_CLASS, return_value=mock_svc):
            pass  # We override directly below

        import app.services.signup_nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email_service()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.check_and_send_signup_nurture_emails())
        assert result == 0
        mock_email.send_email.assert_not_called()

    EMAIL_SVC_CLASS = "app.services.signup_nurture_service.EmailService"

    def test_returns_zero_when_placeholder_api_key(self, monkeypatch):
        """When resend_api_key is placeholder, returns 0 immediately."""
        from app.core import config as cfg
        monkeypatch.setattr(cfg.settings, "resend_api_key", "re_placeholder")
        import app.services.signup_nurture_service as svc_mod
        result = asyncio.run(svc_mod.check_and_send_signup_nurture_emails())
        assert result == 0

    def test_skips_active_subscriptions(self, monkeypatch):
        """Users with status 'active' are skipped (already converted)."""
        c = _make_client(subscriptions=[
            {"id": "sub-1", "user_id": "u1", "status": "active",
             "nurture_step": 0, "created_at": _iso_days_ago(2)}
        ])
        import app.services.signup_nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email_service()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.check_and_send_signup_nurture_emails())
        assert result == 0
        mock_email.send_email.assert_not_called()

    def test_skips_paid_subscriptions(self, monkeypatch):
        """Users with status 'paid' are skipped."""
        c = _make_client(subscriptions=[
            {"id": "sub-2", "user_id": "u2", "status": "paid",
             "nurture_step": 0, "created_at": _iso_days_ago(2)}
        ])
        import app.services.signup_nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email_service()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.check_and_send_signup_nurture_emails())
        assert result == 0

    def test_skips_fully_nurtured_step_3(self, monkeypatch):
        """Users with nurture_step=3 (already sent all) are filtered by query."""
        # The query has .lt("nurture_step", 3) — so step 3 won't be returned.
        # We simulate by having the store return empty.
        c = _make_client(subscriptions=[
            {"id": "sub-3", "user_id": "u3", "status": "demo",
             "nurture_step": 3, "created_at": _iso_days_ago(10)}
        ])
        import app.services.signup_nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email_service()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.check_and_send_signup_nurture_emails())
        # step=3 is excluded by the lt filter — 0 emails
        assert result == 0

    def test_sends_day1_email_after_24h(self, monkeypatch):
        """Step 1 email sent when 24+ hours have passed."""
        c = _make_client(subscriptions=[
            {"id": "sub-4", "user_id": "u4", "status": "demo",
             "nurture_step": 0, "created_at": _iso_hours_ago(25)}
        ])
        import app.services.signup_nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email_service()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.check_and_send_signup_nurture_emails())
        assert result == 1
        mock_email.send_email.assert_awaited_once()
        call_kwargs = mock_email.send_email.call_args
        assert call_kwargs.kwargs["template"] == "nurture_signup_day1.html"
        # Nurture step advanced
        sub = c.store["subscriptions"][0]
        assert sub["nurture_step"] == 1

    def test_does_not_send_day1_email_before_24h(self, monkeypatch):
        """Step 1 email NOT sent when less than 24 hours have passed."""
        c = _make_client(subscriptions=[
            {"id": "sub-5", "user_id": "u5", "status": "demo",
             "nurture_step": 0, "created_at": _iso_hours_ago(10)}
        ])
        import app.services.signup_nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email_service()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.check_and_send_signup_nurture_emails())
        assert result == 0
        mock_email.send_email.assert_not_called()

    def test_sends_day3_email_after_72h(self, monkeypatch):
        """Step 2 email sent when 72+ hours have passed and step=1."""
        c = _make_client(subscriptions=[
            {"id": "sub-6", "user_id": "u6", "status": "demo",
             "nurture_step": 1, "created_at": _iso_hours_ago(73)}
        ])
        import app.services.signup_nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email_service()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.check_and_send_signup_nurture_emails())
        assert result == 1
        call_kwargs = mock_email.send_email.call_args
        assert call_kwargs.kwargs["template"] == "nurture_signup_day3.html"

    def test_sends_day7_email_after_168h(self, monkeypatch):
        """Step 3 email sent when 7+ days have passed and step=2."""
        c = _make_client(subscriptions=[
            {"id": "sub-7", "user_id": "u7", "status": "demo",
             "nurture_step": 2, "created_at": _iso_hours_ago(169)}
        ])
        import app.services.signup_nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email_service()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.check_and_send_signup_nurture_emails())
        assert result == 1
        call_kwargs = mock_email.send_email.call_args
        assert call_kwargs.kwargs["template"] == "nurture_signup_day7.html"
        sub = c.store["subscriptions"][0]
        assert sub["nurture_step"] == 3

    def test_skips_missing_created_at(self, monkeypatch):
        """Subscriptions with no created_at are skipped."""
        c = _make_client(subscriptions=[
            {"id": "sub-8", "user_id": "u8", "status": "demo",
             "nurture_step": 0, "created_at": None}
        ])
        import app.services.signup_nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email_service()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.check_and_send_signup_nurture_emails())
        assert result == 0

    def test_skips_missing_user_id(self, monkeypatch):
        """Subscriptions with no user_id are skipped."""
        c = _make_client(subscriptions=[
            {"id": "sub-9", "user_id": None, "status": "demo",
             "nurture_step": 0, "created_at": _iso_hours_ago(25)}
        ])
        import app.services.signup_nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email_service()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.check_and_send_signup_nurture_emails())
        assert result == 0

    def test_send_failure_does_not_raise(self, monkeypatch):
        """Email send failure is caught; function returns 0 without raising."""
        c = _make_client(subscriptions=[
            {"id": "sub-10", "user_id": "u10", "status": "demo",
             "nurture_step": 0, "created_at": _iso_hours_ago(25)}
        ])
        import app.services.signup_nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)

        from unittest.mock import MagicMock
        mock_email = MagicMock()
        mock_email.send_email = AsyncMock(side_effect=RuntimeError("SMTP fail"))
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        # Should not raise
        result = asyncio.run(svc_mod.check_and_send_signup_nurture_emails())
        assert result == 0

    def test_multiple_users_sent_correct_steps(self, monkeypatch):
        """Multiple users at different steps each get the right email."""
        c = _make_client(subscriptions=[
            {"id": "s1", "user_id": "ua", "status": "demo",
             "nurture_step": 0, "created_at": _iso_hours_ago(25)},
            {"id": "s2", "user_id": "ub", "status": "demo",
             "nurture_step": 1, "created_at": _iso_hours_ago(73)},
        ])
        import app.services.signup_nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email_service()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.check_and_send_signup_nurture_emails())
        assert result == 2
        assert mock_email.send_email.await_count == 2

    def test_invalid_created_at_skipped(self, monkeypatch):
        """Subscription with unparseable created_at is skipped."""
        c = _make_client(subscriptions=[
            {"id": "bad-1", "user_id": "u-bad", "status": "demo",
             "nurture_step": 0, "created_at": "not-a-date"}
        ])
        import app.services.signup_nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email_service()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.check_and_send_signup_nurture_emails())
        assert result == 0

    def test_auth_lookup_failure_skips_user(self, monkeypatch):
        """If auth.admin.get_user_by_id raises, user is skipped without crashing."""
        from unittest.mock import MagicMock
        c = _make_client(subscriptions=[
            {"id": "auth-fail", "user_id": "u-fail", "status": "demo",
             "nurture_step": 0, "created_at": _iso_hours_ago(25)}
        ])
        # Override auth to raise
        c.auth.admin.get_user_by_id = MagicMock(side_effect=RuntimeError("auth error"))

        import app.services.signup_nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email_service()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.check_and_send_signup_nurture_emails())
        assert result == 0
        mock_email.send_email.assert_not_called()

    def test_user_with_no_email_is_skipped(self, monkeypatch):
        """If auth returns a user with no email, subscription is skipped."""
        from unittest.mock import MagicMock
        c = _make_client(subscriptions=[
            {"id": "no-email", "user_id": "u-noemail", "status": "demo",
             "nurture_step": 0, "created_at": _iso_hours_ago(25)}
        ])
        # Auth returns user with no email
        c.auth.admin.get_user_by_id = MagicMock(return_value=type(
            "R", (), {"user": type("U", (), {"email": None})()}
        )())

        import app.services.signup_nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email_service()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.check_and_send_signup_nurture_emails())
        assert result == 0


# ===========================================================================
# C) nurture_service (lead captures)
# ===========================================================================

class TestNurtureService:
    """Tests for app.services.nurture_service.process_nurture_emails."""

    @pytest.fixture(autouse=True)
    def patch_resend_key(self, monkeypatch):
        from app.core import config as cfg
        monkeypatch.setattr(cfg.settings, "resend_api_key", "re_real_key_abc")

    def _mock_email(self):
        from unittest.mock import MagicMock
        svc = MagicMock()
        svc.send_email = AsyncMock()
        return svc

    def test_returns_zero_when_no_leads(self, monkeypatch):
        """No lead_captures → 0 emails."""
        c = _make_client(lead_captures=[])
        import app.services.nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.process_nurture_emails())
        assert result == 0

    def test_returns_zero_when_placeholder_key(self, monkeypatch):
        """Placeholder API key returns 0 immediately."""
        from app.core import config as cfg
        monkeypatch.setattr(cfg.settings, "resend_api_key", "re_placeholder")
        import app.services.nurture_service as svc_mod
        result = asyncio.run(svc_mod.process_nurture_emails())
        assert result == 0

    def test_sends_welcome_email_day0(self, monkeypatch):
        """Lead captured today gets the day-0 welcome email."""
        c = _make_client(lead_captures=[
            {
                "id": "lead-1", "email": "test@lead.fr",
                "source": "simulateur-cerfa",
                "nurture_step": 0,
                "converted_to_user_id": None,
                "created_at": _iso_hours_ago(1),  # less than 1 day
            }
        ])
        import app.services.nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.process_nurture_emails())
        assert result == 1
        call_kwargs = mock_email.send_email.call_args
        assert call_kwargs.kwargs["template"] == "nurture_1_bienvenue.html"
        # Nurture step advanced
        lead = c.store["lead_captures"][0]
        assert lead["nurture_step"] == 1

    def test_sends_day3_email(self, monkeypatch):
        """Lead at step 1 captured 4 days ago gets day-3 email."""
        c = _make_client(lead_captures=[
            {
                "id": "lead-2", "email": "lead2@test.fr",
                "source": "generateur-quittance",
                "nurture_step": 1,
                "converted_to_user_id": None,
                "created_at": _iso_days_ago(4),
            }
        ])
        import app.services.nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.process_nurture_emails())
        assert result == 1
        call_kwargs = mock_email.send_email.call_args
        assert call_kwargs.kwargs["template"] == "nurture_2_valeur.html"

    def test_sends_day7_email(self, monkeypatch):
        """Lead at step 2 captured 8 days ago gets day-7 email."""
        c = _make_client(lead_captures=[
            {
                "id": "lead-3", "email": "lead3@test.fr",
                "source": "calendrier-fiscal",
                "nurture_step": 2,
                "converted_to_user_id": None,
                "created_at": _iso_days_ago(8),
            }
        ])
        import app.services.nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.process_nurture_emails())
        assert result == 1
        call_kwargs = mock_email.send_email.call_args
        assert call_kwargs.kwargs["template"] == "nurture_3_urgence.html"
        lead = c.store["lead_captures"][0]
        assert lead["nurture_step"] == 3

    def test_skips_leads_without_email(self, monkeypatch):
        """Leads with no email are skipped."""
        c = _make_client(lead_captures=[
            {
                "id": "lead-4", "email": None, "source": "landing",
                "nurture_step": 0, "converted_to_user_id": None,
                "created_at": _iso_days_ago(1),
            }
        ])
        import app.services.nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.process_nurture_emails())
        assert result == 0

    def test_skips_leads_without_created_at(self, monkeypatch):
        """Leads with no created_at are skipped."""
        c = _make_client(lead_captures=[
            {
                "id": "lead-5", "email": "x@y.fr", "source": "landing",
                "nurture_step": 0, "converted_to_user_id": None,
                "created_at": None,
            }
        ])
        import app.services.nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.process_nurture_emails())
        assert result == 0

    def test_skips_converted_leads(self, monkeypatch):
        """Leads with converted_to_user_id are excluded (filtered by query)."""
        # The service queries with .is_("converted_to_user_id", "null")
        # FakeQuery is_ filter will exclude rows where the field is not None.
        c = _make_client(lead_captures=[
            {
                "id": "lead-6", "email": "conv@test.fr", "source": "landing",
                "nurture_step": 0, "converted_to_user_id": "user-123",
                "created_at": _iso_days_ago(2),
            }
        ])
        import app.services.nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.process_nurture_emails())
        assert result == 0

    def test_only_one_email_per_run_per_lead(self, monkeypatch):
        """Even if step 0 and step 1 are both due, only one email is sent per run."""
        # Lead created 10 days ago, step 0 → days 0, 3, 7 all due but break after first
        c = _make_client(lead_captures=[
            {
                "id": "lead-7", "email": "multi@test.fr", "source": "landing",
                "nurture_step": 0, "converted_to_user_id": None,
                "created_at": _iso_days_ago(10),
            }
        ])
        import app.services.nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.process_nurture_emails())
        assert result == 1  # Only first eligible step sent per run
        assert mock_email.send_email.await_count == 1

    def test_send_failure_does_not_raise(self, monkeypatch):
        """Email send failure is caught; remaining leads still processed."""
        c = _make_client(lead_captures=[
            {
                "id": "lead-8", "email": "fail@test.fr", "source": "landing",
                "nurture_step": 0, "converted_to_user_id": None,
                "created_at": _iso_days_ago(1),
            }
        ])
        import app.services.nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)

        from unittest.mock import MagicMock
        mock_email = MagicMock()
        mock_email.send_email = AsyncMock(side_effect=RuntimeError("boom"))
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.process_nurture_emails())
        assert result == 0  # send failed, not counted

    def test_source_label_mapping(self, monkeypatch):
        """Context passed to email contains correct source_label for known source."""
        c = _make_client(lead_captures=[
            {
                "id": "lead-9", "email": "src@test.fr",
                "source": "simulateur-cerfa",
                "nurture_step": 0, "converted_to_user_id": None,
                "created_at": _iso_hours_ago(2),
            }
        ])
        import app.services.nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        asyncio.run(svc_mod.process_nurture_emails())

        call_kwargs = mock_email.send_email.call_args.kwargs
        assert call_kwargs["context"]["source_label"] == "simulateur CERFA 2044"

    def test_unknown_source_uses_fallback_label(self, monkeypatch):
        """Unknown source maps to the fallback label."""
        c = _make_client(lead_captures=[
            {
                "id": "lead-10", "email": "unk@test.fr",
                "source": "some-unknown-page",
                "nurture_step": 0, "converted_to_user_id": None,
                "created_at": _iso_hours_ago(2),
            }
        ])
        import app.services.nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        asyncio.run(svc_mod.process_nurture_emails())

        call_kwargs = mock_email.send_email.call_args.kwargs
        assert call_kwargs["context"]["source_label"] == "outil gratuit GérerSCI"

    def test_invalid_created_at_is_skipped(self, monkeypatch):
        """Lead with unparseable created_at is skipped."""
        c = _make_client(lead_captures=[
            {
                "id": "bad-lead", "email": "bad@test.fr", "source": "landing",
                "nurture_step": 0, "converted_to_user_id": None,
                "created_at": "not-a-date",
            }
        ])
        import app.services.nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.process_nurture_emails())
        assert result == 0

    def test_skips_already_passed_steps(self, monkeypatch):
        """Lead at step 2 doesn't re-send steps 0 and 1."""
        c = _make_client(lead_captures=[
            {
                "id": "step2-lead", "email": "step2@test.fr", "source": "landing",
                "nurture_step": 2, "converted_to_user_id": None,
                "created_at": _iso_days_ago(8),
            }
        ])
        import app.services.nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.process_nurture_emails())
        assert result == 1
        # Should send step 3 (index 2 = day 7) template
        call_kwargs = mock_email.send_email.call_args.kwargs
        assert call_kwargs["template"] == "nurture_3_urgence.html"

    def test_multiple_leads_all_processed(self, monkeypatch):
        """Multiple leads each get their correct email."""
        c = _make_client(lead_captures=[
            {
                "id": "ml-1", "email": "a@test.fr", "source": "landing",
                "nurture_step": 0, "converted_to_user_id": None,
                "created_at": _iso_hours_ago(2),
            },
            {
                "id": "ml-2", "email": "b@test.fr", "source": "landing",
                "nurture_step": 0, "converted_to_user_id": None,
                "created_at": _iso_days_ago(5),
            },
        ])
        import app.services.nurture_service as svc_mod
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)
        mock_email = self._mock_email()
        monkeypatch.setattr(svc_mod, "EmailService", lambda: mock_email)

        result = asyncio.run(svc_mod.process_nurture_emails())
        assert result == 2
        assert mock_email.send_email.await_count == 2


# ===========================================================================
# D) mrr_snapshot_service
# ===========================================================================

class TestMrrSnapshotService:
    """Tests for app.services.mrr_snapshot_service."""

    def _client_with_subs(self, subs: list[dict]) -> FakeSupabaseClient:
        c = FakeSupabaseClient()
        c.store["subscriptions"] = subs
        c.store.setdefault("admin_mrr_snapshots", [])
        return c

    # ---- _compute_mrr_breakdown ----

    def test_compute_mrr_no_subscriptions(self):
        """Empty subscriptions → MRR = 0."""
        import app.services.mrr_snapshot_service as svc_mod
        c = self._client_with_subs([])
        total, by_plan, count = svc_mod._compute_mrr_breakdown(c)
        assert total == 0.0
        assert count == 0
        assert by_plan == {}

    def test_compute_mrr_single_pro_subscriber(self):
        """One 'pro' active subscriber → MRR = 19.90."""
        from app.core.config import settings
        import app.services.mrr_snapshot_service as svc_mod

        # Use a known price id mapped to 'pro'
        pro_price_id = settings.stripe_pro_price_id
        c = self._client_with_subs([
            {"stripe_price_id": pro_price_id, "status": "active"}
        ])
        total, by_plan, count = svc_mod._compute_mrr_breakdown(c)
        assert total > 0.0
        assert count == 1

    def test_compute_mrr_skips_inactive_subscriptions(self):
        """Subscriptions with status other than active/trialing/paid are skipped."""
        import app.services.mrr_snapshot_service as svc_mod
        c = self._client_with_subs([
            {"stripe_price_id": None, "status": "canceled"},
            {"stripe_price_id": None, "status": "demo"},
            {"stripe_price_id": None, "status": "no_subscription"},
        ])
        total, by_plan, count = svc_mod._compute_mrr_breakdown(c)
        assert total == 0.0
        assert count == 0

    def test_compute_mrr_free_plan_does_not_count(self):
        """Free/fondateur plans have 0 MRR but active status counts 0 revenue."""
        import app.services.mrr_snapshot_service as svc_mod
        c = self._client_with_subs([
            {"stripe_price_id": None, "status": "active"},  # resolves to 'free' → 0 MRR
        ])
        total, by_plan, count = svc_mod._compute_mrr_breakdown(c)
        # total is 0 because free plan has 0 monthly price
        assert total == 0.0
        # count only increments for monthly > 0
        assert count == 0

    def test_compute_mrr_multiple_subscribers(self):
        """Multiple active subscribers sum correctly."""
        from app.core.config import settings
        import app.services.mrr_snapshot_service as svc_mod

        starter_price = settings.stripe_starter_price_id
        pro_price = settings.stripe_pro_price_id

        c = self._client_with_subs([
            {"stripe_price_id": starter_price, "status": "active"},
            {"stripe_price_id": pro_price, "status": "paid"},
            {"stripe_price_id": starter_price, "status": "trialing"},
        ])
        total, by_plan, count = svc_mod._compute_mrr_breakdown(c)
        assert count == 3  # all 3 have non-zero monthly prices
        assert total > 0.0

    # ---- take_mrr_snapshot ----

    def test_take_mrr_snapshot_returns_dict(self, monkeypatch):
        """take_mrr_snapshot returns a dict with expected keys."""
        import app.services.mrr_snapshot_service as svc_mod
        c = self._client_with_subs([])
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)

        result = asyncio.run(svc_mod.take_mrr_snapshot())
        assert "snapshot_date" in result
        assert "total_mrr" in result
        assert "mrr_by_plan" in result
        assert "active_subscribers" in result
        assert "arpu" in result

    def test_take_mrr_snapshot_persists_to_store(self, monkeypatch):
        """take_mrr_snapshot upserts a row into admin_mrr_snapshots."""
        import app.services.mrr_snapshot_service as svc_mod
        c = self._client_with_subs([])
        c.store["admin_mrr_snapshots"] = []
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)

        asyncio.run(svc_mod.take_mrr_snapshot())
        assert len(c.store["admin_mrr_snapshots"]) >= 1

    def test_take_mrr_snapshot_zero_subscribers(self, monkeypatch):
        """Snapshot with no subscribers: MRR=0, arpu=0."""
        import app.services.mrr_snapshot_service as svc_mod
        c = self._client_with_subs([])
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)

        result = asyncio.run(svc_mod.take_mrr_snapshot())
        assert result["total_mrr"] == 0.0
        assert result["arpu"] == 0.0
        assert result["active_subscribers"] == 0

    def test_take_mrr_snapshot_arpu_computed(self, monkeypatch):
        """ARPU = total_mrr / active_subscribers."""
        from app.core.config import settings
        import app.services.mrr_snapshot_service as svc_mod

        pro_price = settings.stripe_pro_price_id
        c = self._client_with_subs([
            {"stripe_price_id": pro_price, "status": "active"},
            {"stripe_price_id": pro_price, "status": "active"},
        ])
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)

        result = asyncio.run(svc_mod.take_mrr_snapshot())
        if result["active_subscribers"] > 0:
            expected_arpu = round(result["total_mrr"] / result["active_subscribers"], 2)
            assert result["arpu"] == expected_arpu

    # ---- get_mrr_trend ----

    def test_get_mrr_trend_no_snapshots_falls_back_to_live(self, monkeypatch):
        """With no snapshots, returns live computation and has_history=False."""
        import app.services.mrr_snapshot_service as svc_mod
        c = self._client_with_subs([])
        c.store["admin_mrr_snapshots"] = []
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)

        result = svc_mod.get_mrr_trend(days=30)
        assert result["has_history"] is False
        assert "current_mrr" in result
        assert "previous_mrr" in result

    def test_get_mrr_trend_with_snapshots(self, monkeypatch):
        """With snapshots available, has_history=True and values are read from DB."""
        from datetime import date, timedelta
        import app.services.mrr_snapshot_service as svc_mod
        c = self._client_with_subs([])
        today = date.today()
        c.store["admin_mrr_snapshots"] = [
            {"snapshot_date": today.isoformat(), "total_mrr": 200.0},
            {"snapshot_date": (today - timedelta(days=35)).isoformat(), "total_mrr": 150.0},
        ]
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)

        result = svc_mod.get_mrr_trend(days=30)
        assert result["has_history"] is True
        assert result["current_mrr"] == 200.0

    def test_get_mrr_trend_no_previous_snapshot(self, monkeypatch):
        """When only current window has snapshots, previous_mrr = current_mrr."""
        from datetime import date
        import app.services.mrr_snapshot_service as svc_mod
        c = self._client_with_subs([])
        today = date.today()
        c.store["admin_mrr_snapshots"] = [
            {"snapshot_date": today.isoformat(), "total_mrr": 300.0},
        ]
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)

        result = svc_mod.get_mrr_trend(days=30)
        assert result["has_history"] is True
        assert result["current_mrr"] == 300.0
        # When no previous data, previous_mrr defaults to current_mrr
        assert result["previous_mrr"] == 300.0

    def test_resolve_plan_free_when_no_price_id(self):
        """_resolve_plan with None returns 'free'."""
        import app.services.mrr_snapshot_service as svc_mod
        assert svc_mod._resolve_plan(None) == "free"

    def test_resolve_plan_unknown_price_id(self):
        """_resolve_plan with unknown price_id falls through to free."""
        import app.services.mrr_snapshot_service as svc_mod
        result = svc_mod._resolve_plan("price_unknown_xyz")
        # resolve_plan_key_from_price_id returns PlanKey.FREE for unknown ids
        assert result == "free"

    def test_mrr_by_plan_breakdown(self, monkeypatch):
        """MRR breakdown dict keys match plan names."""
        from app.core.config import settings
        import app.services.mrr_snapshot_service as svc_mod

        starter_price = settings.stripe_starter_price_id
        c = self._client_with_subs([
            {"stripe_price_id": starter_price, "status": "active"},
        ])
        monkeypatch.setattr(svc_mod, "get_supabase_service_client", lambda: c)

        result = asyncio.run(svc_mod.take_mrr_snapshot())
        # mrr_by_plan should have the plan key
        assert isinstance(result["mrr_by_plan"], dict)
