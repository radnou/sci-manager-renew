"""Tests for app.services.notification_cron — targeting >= 95% coverage.

Covers:
- check_late_payments
- check_expiring_bails
- check_pending_quittances
- check_expiring_pno
- check_fiscal_deadlines (all 6 deadline types, IR vs IS filtering)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest

from app.services.notification_cron import (
    FISCAL_DEADLINES,
    check_expiring_bails,
    check_expiring_pno,
    check_fiscal_deadlines,
    check_late_payments,
    check_pending_quittances,
)


# ---------------------------------------------------------------------------
# Helper: mock create_notification_with_email so we don't trigger real emails
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def mock_notify():
    with patch(
        "app.services.notification_cron.create_notification_with_email",
        new_callable=AsyncMock,
    ) as m:
        yield m


# ── check_late_payments ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_late_payments_no_results(fake_supabase, mock_notify):
    """All seed loyers are 'paye' — nothing should be flagged."""
    count = await check_late_payments(fake_supabase)
    assert count == 0
    mock_notify.assert_not_called()


@pytest.mark.asyncio
async def test_late_payments_flags_overdue(fake_supabase, mock_notify):
    """A loyer 10 days overdue with status 'en_attente' triggers notification."""
    overdue_date = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%d")
    fake_supabase.store["loyers"].append(
        {
            "id": "loyer-late",
            "id_bien": "bien-1",
            "id_sci": "sci-1",
            "date_loyer": overdue_date,
            "montant": 1200.0,
            "statut": "en_attente",
        }
    )

    count = await check_late_payments(fake_supabase)
    # sci-1 has 2 associes with user_id set
    assert count == 2
    assert mock_notify.call_count == 2


@pytest.mark.asyncio
async def test_late_payments_en_retard_status(fake_supabase, mock_notify):
    """A loyer with status 'en_retard' should also be flagged."""
    overdue_date = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%d")
    fake_supabase.store["loyers"].append(
        {
            "id": "loyer-retard",
            "id_bien": "bien-9",
            "id_sci": "sci-2",
            "date_loyer": overdue_date,
            "montant": 980.0,
            "statut": "en_retard",
        }
    )

    count = await check_late_payments(fake_supabase)
    # sci-2 has 1 associe with user_id set
    assert count == 1


@pytest.mark.asyncio
async def test_late_payments_sci_id_from_biens_fallback(fake_supabase, mock_notify):
    """When loyer has no id_sci, it falls back to biens.id_sci."""
    overdue_date = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%d")
    fake_supabase.store["loyers"].append(
        {
            "id": "loyer-no-sci",
            "id_bien": "bien-1",
            # no id_sci — should fall back to biens sub-object
            "date_loyer": overdue_date,
            "montant": 500.0,
            "statut": "en_attente",
            "biens": {"id_sci": "sci-1", "adresse": "1 rue de la Paix", "ville": "Paris"},
        }
    )

    count = await check_late_payments(fake_supabase)
    assert count == 2  # sci-1 has 2 owners


@pytest.mark.asyncio
async def test_late_payments_no_sci_id_skip(fake_supabase, mock_notify):
    """When loyer has neither id_sci nor biens.id_sci, it is skipped."""
    overdue_date = (datetime.now(timezone.utc) - timedelta(days=10)).strftime("%Y-%m-%d")
    fake_supabase.store["loyers"].append(
        {
            "id": "loyer-orphan",
            "id_bien": "bien-1",
            "date_loyer": overdue_date,
            "montant": 500.0,
            "statut": "en_attente",
            # no id_sci, no biens sub-object
        }
    )

    count = await check_late_payments(fake_supabase)
    assert count == 0
    mock_notify.assert_not_called()


@pytest.mark.asyncio
async def test_late_payments_not_overdue_enough(fake_supabase, mock_notify):
    """A loyer only 2 days old (within 5-day grace period) is not flagged."""
    recent_date = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%d")
    fake_supabase.store["loyers"].append(
        {
            "id": "loyer-recent",
            "id_bien": "bien-1",
            "id_sci": "sci-1",
            "date_loyer": recent_date,
            "montant": 1200.0,
            "statut": "en_attente",
        }
    )

    count = await check_late_payments(fake_supabase)
    assert count == 0


# ── check_expiring_bails ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_expiring_bails_no_results(fake_supabase, mock_notify):
    """No baux in seed data — returns 0."""
    count = await check_expiring_bails(fake_supabase)
    assert count == 0
    mock_notify.assert_not_called()


@pytest.mark.asyncio
async def test_expiring_bails_within_90_days(fake_supabase, mock_notify):
    """A bail expiring in 30 days triggers notifications for SCI owners."""
    expiry = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
    fake_supabase.store.setdefault("baux", []).append(
        {
            "id": "bail-exp",
            "id_bien": "bien-1",
            "date_fin": expiry,
            "biens": {"id_sci": "sci-1", "adresse": "1 rue de la Paix", "ville": "Paris"},
        }
    )

    count = await check_expiring_bails(fake_supabase)
    assert count == 2  # sci-1 has 2 owners


@pytest.mark.asyncio
async def test_expiring_bails_no_sci_id_skipped(fake_supabase, mock_notify):
    """A bail without biens.id_sci is skipped."""
    expiry = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
    fake_supabase.store.setdefault("baux", []).append(
        {
            "id": "bail-no-sci",
            "id_bien": "bien-1",
            "date_fin": expiry,
            "biens": {"adresse": "somewhere"},  # no id_sci
        }
    )

    count = await check_expiring_bails(fake_supabase)
    assert count == 0


@pytest.mark.asyncio
async def test_expiring_bails_too_far(fake_supabase, mock_notify):
    """A bail expiring in 120 days is outside the 90-day window."""
    expiry = (datetime.now(timezone.utc) + timedelta(days=120)).strftime("%Y-%m-%d")
    fake_supabase.store.setdefault("baux", []).append(
        {
            "id": "bail-far",
            "id_bien": "bien-1",
            "date_fin": expiry,
            "biens": {"id_sci": "sci-1", "adresse": "1 rue de la Paix", "ville": "Paris"},
        }
    )

    count = await check_expiring_bails(fake_supabase)
    assert count == 0


@pytest.mark.asyncio
async def test_expiring_bails_already_expired(fake_supabase, mock_notify):
    """A bail that already expired is not included (date_fin < now)."""
    past = (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%d")
    fake_supabase.store.setdefault("baux", []).append(
        {
            "id": "bail-past",
            "id_bien": "bien-1",
            "date_fin": past,
            "biens": {"id_sci": "sci-1", "adresse": "1 rue de la Paix", "ville": "Paris"},
        }
    )

    count = await check_expiring_bails(fake_supabase)
    assert count == 0


# ── check_pending_quittances ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_pending_quittances_no_results(fake_supabase, mock_notify):
    """Seed loyers don't have quitus_genere=False — no match (no field = no eq match)."""
    count = await check_pending_quittances(fake_supabase)
    assert count == 0


@pytest.mark.asyncio
async def test_pending_quittances_flags_ungenerated(fake_supabase, mock_notify):
    """A paid loyer without quittance triggers notifications."""
    fake_supabase.store["loyers"].append(
        {
            "id": "loyer-noq",
            "id_bien": "bien-1",
            "id_sci": "sci-1",
            "date_loyer": "2026-02-01",
            "montant": 1200.0,
            "statut": "paye",
            "quitus_genere": False,
        }
    )

    count = await check_pending_quittances(fake_supabase)
    assert count == 2  # sci-1 has 2 owners


@pytest.mark.asyncio
async def test_pending_quittances_sci_id_from_biens(fake_supabase, mock_notify):
    """Fallback to biens.id_sci when loyer has no id_sci."""
    fake_supabase.store["loyers"].append(
        {
            "id": "loyer-noq-fb",
            "id_bien": "bien-9",
            # no id_sci
            "date_loyer": "2026-02-01",
            "montant": 980.0,
            "statut": "paye",
            "quitus_genere": False,
            "biens": {"id_sci": "sci-2", "adresse": "42 avenue QA", "ville": "Lyon"},
        }
    )

    count = await check_pending_quittances(fake_supabase)
    assert count == 1  # sci-2 has 1 owner


@pytest.mark.asyncio
async def test_pending_quittances_no_sci_id_skip(fake_supabase, mock_notify):
    """Line 115-116: loyer with no sci_id at all is skipped (continue branch)."""
    fake_supabase.store["loyers"].append(
        {
            "id": "loyer-noq-orphan",
            "id_bien": "bien-1",
            # no id_sci, no biens sub-object
            "date_loyer": "2026-02-01",
            "montant": 500.0,
            "statut": "paye",
            "quitus_genere": False,
        }
    )

    count = await check_pending_quittances(fake_supabase)
    assert count == 0
    mock_notify.assert_not_called()


# ── check_expiring_pno ───────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_expiring_pno_no_results(fake_supabase, mock_notify):
    """No PNO in seed data — returns 0."""
    count = await check_expiring_pno(fake_supabase)
    assert count == 0


@pytest.mark.asyncio
async def test_expiring_pno_within_30_days(fake_supabase, mock_notify):
    """A PNO expiring in 15 days triggers notifications."""
    expiry = (datetime.now(timezone.utc) + timedelta(days=15)).strftime("%Y-%m-%d")
    fake_supabase.store.setdefault("assurances_pno", []).append(
        {
            "id": "pno-exp",
            "id_bien": "bien-1",
            "assureur": "AXA",
            "date_fin": expiry,
            "biens": {"id_sci": "sci-1", "adresse": "1 rue de la Paix", "ville": "Paris"},
        }
    )

    count = await check_expiring_pno(fake_supabase)
    assert count == 2  # sci-1 has 2 owners


@pytest.mark.asyncio
async def test_expiring_pno_no_sci_id_skipped(fake_supabase, mock_notify):
    """A PNO without biens.id_sci is skipped."""
    expiry = (datetime.now(timezone.utc) + timedelta(days=15)).strftime("%Y-%m-%d")
    fake_supabase.store.setdefault("assurances_pno", []).append(
        {
            "id": "pno-no-sci",
            "id_bien": "bien-1",
            "assureur": "MAIF",
            "date_fin": expiry,
            "biens": {},  # no id_sci
        }
    )

    count = await check_expiring_pno(fake_supabase)
    assert count == 0


@pytest.mark.asyncio
async def test_expiring_pno_too_far(fake_supabase, mock_notify):
    """A PNO expiring in 60 days is outside the 30-day window."""
    expiry = (datetime.now(timezone.utc) + timedelta(days=60)).strftime("%Y-%m-%d")
    fake_supabase.store.setdefault("assurances_pno", []).append(
        {
            "id": "pno-far",
            "id_bien": "bien-1",
            "assureur": "AXA",
            "date_fin": expiry,
            "biens": {"id_sci": "sci-1", "adresse": "1 rue de la Paix", "ville": "Paris"},
        }
    )

    count = await check_expiring_pno(fake_supabase)
    assert count == 0


@pytest.mark.asyncio
async def test_expiring_pno_no_assureur(fake_supabase, mock_notify):
    """PNO without assureur field still works (uses 'N/A' fallback)."""
    expiry = (datetime.now(timezone.utc) + timedelta(days=10)).strftime("%Y-%m-%d")
    fake_supabase.store.setdefault("assurances_pno", []).append(
        {
            "id": "pno-noins",
            "id_bien": "bien-9",
            "date_fin": expiry,
            "biens": {"id_sci": "sci-2", "adresse": "42 avenue QA", "ville": "Lyon"},
        }
    )

    count = await check_expiring_pno(fake_supabase)
    assert count == 1
    call_data = mock_notify.call_args[1]["data"]
    assert "N/A" in call_data["message"]


# ── check_fiscal_deadlines ───────────────────────────────────────────────


@pytest.mark.asyncio
async def test_fiscal_deadlines_no_scis(fake_supabase, mock_notify):
    """When no SCIs exist, returns 0."""
    fake_supabase.store["sci"] = []
    count = await check_fiscal_deadlines(fake_supabase)
    assert count == 0
    mock_notify.assert_not_called()


@pytest.mark.asyncio
async def test_fiscal_deadlines_ir_declaration_2072(fake_supabase, mock_notify):
    """IR SCI gets notified about declaration 2072 (May 20)."""
    # Set "now" to 10 days before May 20
    fake_now = datetime(2026, 5, 10, 12, 0, 0, tzinfo=timezone.utc)
    with patch("app.services.notification_cron.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        count = await check_fiscal_deadlines(fake_supabase)

    # sci-1 is IR — should match 2072 (May 20, 10 days away) and 2044 (May 31, 21 days away)
    # Also universal deadlines: taxe_fonciere (Oct 15), CFE (Dec 15), AG (Jun 30)
    # May 10 → Oct 15 = 158 days (> 30 advance), Dec 15 = 219 (> 30), Jun 30 = 51 (> 45)
    # So for IR SCI: 2072 + 2044 = 2 deadlines, sci-1 has 2 owners = 4 notifications
    # sci-2 is IS — liasse_fiscale_is (Mar 31) is past, universal same as above
    # So total = 4 for sci-1 IR
    assert count >= 4
    # Verify at least one 2072 notification was sent
    calls = mock_notify.call_args_list
    deadline_keys = [
        c[1]["data"]["metadata"]["deadline_key"]
        for c in calls
        if "metadata" in c[1].get("data", {})
    ]
    assert "declaration_2072" in deadline_keys


@pytest.mark.asyncio
async def test_fiscal_deadlines_ir_declaration_2044(fake_supabase, mock_notify):
    """IR SCI gets notified about declaration 2044 (May 31)."""
    fake_now = datetime(2026, 5, 15, 12, 0, 0, tzinfo=timezone.utc)
    with patch("app.services.notification_cron.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        count = await check_fiscal_deadlines(fake_supabase)

    calls = mock_notify.call_args_list
    deadline_keys = [
        c[1]["data"]["metadata"]["deadline_key"]
        for c in calls
        if "metadata" in c[1].get("data", {})
    ]
    assert "declaration_2044" in deadline_keys


@pytest.mark.asyncio
async def test_fiscal_deadlines_is_liasse_fiscale(fake_supabase, mock_notify):
    """IS SCI gets notified about liasse fiscale (Mar 31)."""
    fake_now = datetime(2026, 3, 10, 12, 0, 0, tzinfo=timezone.utc)
    with patch("app.services.notification_cron.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        count = await check_fiscal_deadlines(fake_supabase)

    calls = mock_notify.call_args_list
    deadline_keys = [
        c[1]["data"]["metadata"]["deadline_key"]
        for c in calls
        if "metadata" in c[1].get("data", {})
    ]
    assert "liasse_fiscale_is" in deadline_keys
    # IR SCI (sci-1) should NOT get liasse_fiscale_is
    sci_ids_for_liasse = [
        c[1]["data"]["metadata"]["sci_id"]
        for c in calls
        if c[1]["data"]["metadata"].get("deadline_key") == "liasse_fiscale_is"
    ]
    assert "sci-1" not in sci_ids_for_liasse
    assert "sci-2" in sci_ids_for_liasse


@pytest.mark.asyncio
async def test_fiscal_deadlines_taxe_fonciere(fake_supabase, mock_notify):
    """Both IR and IS SCIs get taxe fonciere notification (Oct 15, regime=None)."""
    fake_now = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)
    with patch("app.services.notification_cron.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        count = await check_fiscal_deadlines(fake_supabase)

    calls = mock_notify.call_args_list
    deadline_keys = [
        c[1]["data"]["metadata"]["deadline_key"]
        for c in calls
        if "metadata" in c[1].get("data", {})
    ]
    assert "taxe_fonciere" in deadline_keys


@pytest.mark.asyncio
async def test_fiscal_deadlines_cfe(fake_supabase, mock_notify):
    """CFE deadline (Dec 15) notifies both SCIs."""
    fake_now = datetime(2026, 11, 20, 12, 0, 0, tzinfo=timezone.utc)
    with patch("app.services.notification_cron.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        count = await check_fiscal_deadlines(fake_supabase)

    calls = mock_notify.call_args_list
    deadline_keys = [
        c[1]["data"]["metadata"]["deadline_key"]
        for c in calls
        if "metadata" in c[1].get("data", {})
    ]
    assert "cfe" in deadline_keys


@pytest.mark.asyncio
async def test_fiscal_deadlines_ag_annuelle(fake_supabase, mock_notify):
    """AG annuelle (Jun 30, 45-day advance) notifies both SCIs."""
    fake_now = datetime(2026, 5, 20, 12, 0, 0, tzinfo=timezone.utc)
    with patch("app.services.notification_cron.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        count = await check_fiscal_deadlines(fake_supabase)

    calls = mock_notify.call_args_list
    deadline_keys = [
        c[1]["data"]["metadata"]["deadline_key"]
        for c in calls
        if "metadata" in c[1].get("data", {})
    ]
    assert "ag_annuelle" in deadline_keys


@pytest.mark.asyncio
async def test_fiscal_deadlines_past_deadline_skipped(fake_supabase, mock_notify):
    """Deadlines already past (days_until < 0) are skipped."""
    # June 1 — May deadlines (2072: May 20, 2044: May 31) are past
    fake_now = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    with patch("app.services.notification_cron.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        count = await check_fiscal_deadlines(fake_supabase)

    calls = mock_notify.call_args_list
    deadline_keys = [
        c[1]["data"]["metadata"]["deadline_key"]
        for c in calls
        if "metadata" in c[1].get("data", {})
    ]
    assert "declaration_2072" not in deadline_keys
    assert "declaration_2044" not in deadline_keys


@pytest.mark.asyncio
async def test_fiscal_deadlines_outside_advance_window(fake_supabase, mock_notify):
    """Deadlines too far in the future (> advance_days) are skipped."""
    # Jan 1 — all deadlines are > 30/45 days away
    fake_now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    with patch("app.services.notification_cron.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        count = await check_fiscal_deadlines(fake_supabase)

    # Liasse fiscale IS (Mar 31) is 89 days away — > 30 day advance
    # All others are even further
    assert count == 0


@pytest.mark.asyncio
async def test_fiscal_deadlines_ir_skips_is_deadlines(fake_supabase, mock_notify):
    """An IR-only SCI does not receive IS-specific notifications."""
    # Keep only the IR SCI
    fake_supabase.store["sci"] = [
        {"id": "sci-1", "nom": "SCI Mosa Belleville", "regime_fiscal": "IR"},
    ]

    fake_now = datetime(2026, 3, 10, 12, 0, 0, tzinfo=timezone.utc)
    with patch("app.services.notification_cron.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        count = await check_fiscal_deadlines(fake_supabase)

    calls = mock_notify.call_args_list
    deadline_keys = [
        c[1]["data"]["metadata"]["deadline_key"]
        for c in calls
        if "metadata" in c[1].get("data", {})
    ]
    assert "liasse_fiscale_is" not in deadline_keys


@pytest.mark.asyncio
async def test_fiscal_deadlines_is_skips_ir_deadlines(fake_supabase, mock_notify):
    """An IS-only SCI does not receive IR-specific notifications."""
    fake_supabase.store["sci"] = [
        {"id": "sci-2", "nom": "SCI Horizon Lyon", "regime_fiscal": "IS"},
    ]

    fake_now = datetime(2026, 5, 10, 12, 0, 0, tzinfo=timezone.utc)
    with patch("app.services.notification_cron.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        count = await check_fiscal_deadlines(fake_supabase)

    calls = mock_notify.call_args_list
    deadline_keys = [
        c[1]["data"]["metadata"]["deadline_key"]
        for c in calls
        if "metadata" in c[1].get("data", {})
    ]
    assert "declaration_2072" not in deadline_keys
    assert "declaration_2044" not in deadline_keys


@pytest.mark.asyncio
async def test_fiscal_deadlines_no_regime_gets_universal_only(fake_supabase, mock_notify):
    """A SCI with no regime_fiscal only gets universal deadlines."""
    fake_supabase.store["sci"] = [
        {"id": "sci-1", "nom": "SCI No Regime", "regime_fiscal": None},
    ]

    fake_now = datetime(2026, 9, 25, 12, 0, 0, tzinfo=timezone.utc)
    with patch("app.services.notification_cron.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        count = await check_fiscal_deadlines(fake_supabase)

    calls = mock_notify.call_args_list
    deadline_keys = [
        c[1]["data"]["metadata"]["deadline_key"]
        for c in calls
        if "metadata" in c[1].get("data", {})
    ]
    # Should not get IR or IS specific deadlines
    assert "declaration_2072" not in deadline_keys
    assert "declaration_2044" not in deadline_keys
    assert "liasse_fiscale_is" not in deadline_keys
    # Should get universal deadline (taxe_fonciere within window)
    assert "taxe_fonciere" in deadline_keys


@pytest.mark.asyncio
async def test_fiscal_deadlines_notification_content(fake_supabase, mock_notify):
    """Verify the notification content structure for fiscal deadlines."""
    fake_now = datetime(2026, 5, 10, 12, 0, 0, tzinfo=timezone.utc)
    with patch("app.services.notification_cron.datetime") as mock_dt:
        mock_dt.now.return_value = fake_now
        mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)

        await check_fiscal_deadlines(fake_supabase)

    # Find a 2072 notification call
    for call in mock_notify.call_args_list:
        data = call[1]["data"]
        if data["metadata"].get("deadline_key") == "declaration_2072":
            assert "Déclaration 2072" in data["title"]
            assert "SCI Mosa Belleville" in data["title"]
            assert "20/05/2026" in data["message"]
            assert "jours restants" in data["message"]
            assert data["metadata"]["sci_id"] == "sci-1"
            assert data["metadata"]["deadline_date"] == "2026-05-20"
            assert data["metadata"]["days_until"] in (9, 10)  # depends on time-of-day rounding
            break
    else:
        pytest.fail("No declaration_2072 notification found")


@pytest.mark.asyncio
async def test_fiscal_deadlines_constant_structure():
    """Verify FISCAL_DEADLINES constant has expected 6 entries."""
    assert len(FISCAL_DEADLINES) == 6
    keys = {d["key"] for d in FISCAL_DEADLINES}
    assert keys == {
        "declaration_2072",
        "declaration_2044",
        "liasse_fiscale_is",
        "taxe_fonciere",
        "cfe",
        "ag_annuelle",
    }
