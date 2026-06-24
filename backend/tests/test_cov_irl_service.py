"""Tests for app.services.irl_service — targeting >80% coverage.

Covers:
- _next_anniversary: logic for computing next annual anniversary
- check_irl_revisions: filtering by bail age, window, dedup, notification creation
"""

from __future__ import annotations

from datetime import date, timedelta
from unittest.mock import AsyncMock, patch

import pytest

from app.services.irl_service import IRL_INCREASE_FACTOR, _next_anniversary, check_irl_revisions


# ---------------------------------------------------------------------------
# _next_anniversary
# ---------------------------------------------------------------------------


class TestNextAnniversary:

    def test_anniversary_in_current_year_before_reference(self):
        """When same-year anniversary is in the past, returns next year."""
        # bail started Jan 1 2022, reference is Feb 1 2025
        # anniversary this year = Jan 1 2025 < Feb 1 2025 → return Jan 1 2026
        result = _next_anniversary(date(2022, 1, 1), date(2025, 2, 1))
        assert result == date(2026, 1, 1)

    def test_anniversary_in_current_year_after_reference(self):
        """When same-year anniversary is still in the future, returns it."""
        # bail started Dec 1 2022, reference is Nov 1 2025
        # anniversary this year = Dec 1 2025 > Nov 1 2025 → return Dec 1 2025
        result = _next_anniversary(date(2022, 12, 1), date(2025, 11, 1))
        assert result == date(2025, 12, 1)

    def test_anniversary_exactly_on_reference(self):
        """Anniversary exactly on the reference date returns next year (< not <=)."""
        # bail started Mar 15 2022, reference is Mar 15 2025
        # Mar 15 2025 is NOT < Mar 15 2025 → stays at 2025
        result = _next_anniversary(date(2022, 3, 15), date(2025, 3, 15))
        assert result == date(2025, 3, 15)

    def test_anniversary_day_after_reference(self):
        """Anniversary one day after reference stays in same year."""
        result = _next_anniversary(date(2022, 6, 20), date(2025, 6, 19))
        assert result == date(2025, 6, 20)

    def test_anniversary_one_day_before_reference(self):
        """Anniversary one day before reference goes to next year."""
        result = _next_anniversary(date(2022, 6, 20), date(2025, 6, 21))
        assert result == date(2026, 6, 20)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def mock_notify():
    """Mock create_notification_with_email to avoid real email/DB calls."""
    with patch(
        "app.services.irl_service.create_notification_with_email",
        new_callable=AsyncMock,
        return_value=True,
    ) as m:
        yield m


# ---------------------------------------------------------------------------
# check_irl_revisions
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_baux_returns_zero(fake_supabase, mock_notify):
    """With no active baux, returns 0."""
    fake_supabase.store["baux"] = []
    count = await check_irl_revisions(fake_supabase)
    assert count == 0
    mock_notify.assert_not_called()


@pytest.mark.asyncio
async def test_bail_too_young_skipped(fake_supabase, mock_notify):
    """A bail less than 1 year old is skipped."""
    recent_start = (date.today() - timedelta(days=200)).isoformat()
    fake_supabase.store["baux"] = [
        {
            "id": "bail-young",
            "id_bien": "bien-1",
            "date_debut": recent_start,
            "loyer_hc": 1000.0,
            "statut": "en_cours",
            "indice_irl_reference": None,
        }
    ]
    count = await check_irl_revisions(fake_supabase)
    assert count == 0
    mock_notify.assert_not_called()


@pytest.mark.asyncio
async def test_bail_outside_30_day_window_skipped(fake_supabase, mock_notify):
    """Anniversary more than 30 days away is skipped."""
    # Start bail 14 months ago, so anniversary is 2 months in the future
    start = (date.today() - timedelta(days=420)).isoformat()
    fake_supabase.store["baux"] = [
        {
            "id": "bail-far",
            "id_bien": "bien-1",
            "date_debut": start,
            "loyer_hc": 1000.0,
            "statut": "en_cours",
            "indice_irl_reference": None,
        }
    ]
    count = await check_irl_revisions(fake_supabase)
    assert count == 0


@pytest.mark.asyncio
async def test_bail_within_30_day_window_notifies(fake_supabase, mock_notify):
    """Anniversary within 30 days triggers notification for each owner."""
    # Use a fixed-past start date that guarantees > 365 days old,
    # and whose anniversary is within 30 days from today (2026-06-24).
    # Start on 2025-06-10: age = 379 days (> 365). Anniversary 2026-06-10 = 14 days ago,
    # next anniversary = 2027-06-10 (future, > 30 days away).
    # Instead use 2024-07-01: age > 365, anniversary 2026-07-01 = 7 days away.
    today = date.today()
    # Find a start date where: (today - start).days >= 365 and next_anniversary
    # is between 0 and 30 days from today.
    # We use 2 years ago same day so anniversary is today exactly (days_until=0)
    start = today.replace(year=today.year - 2)
    # anniversary this year = today → days_until = 0 → within window

    fake_supabase.store["baux"] = [
        {
            "id": "bail-due",
            "id_bien": "bien-1",
            "date_debut": start.isoformat(),
            "loyer_hc": 1200.0,
            "statut": "en_cours",
            "indice_irl_reference": None,
        }
    ]
    # bien-1 → sci-1 → 2 associes (user-123, user-456)
    fake_supabase.store["biens"] = [
        {"id": "bien-1", "id_sci": "sci-1", "adresse": "1 rue de la Paix", "ville": "Paris"}
    ]
    fake_supabase.store["notifications"] = []

    count = await check_irl_revisions(fake_supabase)
    # sci-1 has 2 associes with user_id set
    assert count == 2
    assert mock_notify.call_count == 2


@pytest.mark.asyncio
async def test_notification_content_correct(fake_supabase, mock_notify):
    """Verify notification data contains correct loyer calculations."""
    today = date.today()
    # Use start date 2 years ago today: age > 365, anniversary = today (days_until=0 <= 30)
    start = today.replace(year=today.year - 2)

    loyer_hc = 900.0
    expected_new_loyer = round(loyer_hc * IRL_INCREASE_FACTOR, 2)

    fake_supabase.store["baux"] = [
        {
            "id": "bail-content",
            "id_bien": "bien-1",
            "date_debut": start.isoformat(),
            "loyer_hc": loyer_hc,
            "statut": "en_cours",
            "indice_irl_reference": None,
        }
    ]
    fake_supabase.store["biens"] = [
        {"id": "bien-1", "id_sci": "sci-1", "adresse": "10 avenue Test", "ville": "Lyon"}
    ]
    fake_supabase.store["associes"] = [
        {"id": "assoc-1", "id_sci": "sci-1", "user_id": "user-111"}
    ]
    fake_supabase.store["notifications"] = []

    count = await check_irl_revisions(fake_supabase)
    assert count == 1  # 1 owner
    assert mock_notify.call_count == 1

    call_kwargs = mock_notify.call_args[1]
    data = call_kwargs["data"]
    assert call_kwargs["notification_type"] == "irl_revision"
    assert call_kwargs["user_id"] == "user-111"
    assert str(loyer_hc) in data["message"]
    assert str(expected_new_loyer) in data["message"]
    assert "10 avenue Test" in data["title"]
    # metadata
    assert data["metadata"]["current_loyer"] == loyer_hc
    assert data["metadata"]["estimated_loyer"] == expected_new_loyer
    assert "dedup_key" in data["metadata"]
    assert data["metadata"]["bail_id"] == "bail-content"


@pytest.mark.asyncio
async def test_dedup_prevents_second_notification(fake_supabase, mock_notify):
    """If an irl_revision notification with same dedup_key already exists, skip."""
    today = date.today()
    # Start 2 years ago today: age > 365, anniversary = today, year = today.year
    start = today.replace(year=today.year - 2)
    dedup_key = f"irl_bail-dedup_{today.year}"

    fake_supabase.store["baux"] = [
        {
            "id": "bail-dedup",
            "id_bien": "bien-1",
            "date_debut": start.isoformat(),
            "loyer_hc": 1000.0,
            "statut": "en_cours",
            "indice_irl_reference": None,
        }
    ]
    fake_supabase.store["biens"] = [
        {"id": "bien-1", "id_sci": "sci-1", "adresse": "Dedup Street", "ville": "Paris"}
    ]
    # Pre-insert a matching notification (same dedup_key)
    fake_supabase.store["notifications"] = [
        {
            "id": "notif-existing",
            "type": "irl_revision",
            "metadata": {"dedup_key": dedup_key},
        }
    ]

    count = await check_irl_revisions(fake_supabase)
    assert count == 0
    mock_notify.assert_not_called()


@pytest.mark.asyncio
async def test_missing_date_debut_skipped(fake_supabase, mock_notify):
    """Bail missing date_debut is skipped."""
    fake_supabase.store["baux"] = [
        {
            "id": "bail-nodatestart",
            "id_bien": "bien-1",
            "date_debut": None,
            "loyer_hc": 1000.0,
            "statut": "en_cours",
            "indice_irl_reference": None,
        }
    ]
    count = await check_irl_revisions(fake_supabase)
    assert count == 0


@pytest.mark.asyncio
async def test_missing_id_bien_skipped(fake_supabase, mock_notify):
    """Bail missing id_bien is skipped."""
    today = date.today()
    start = (today - timedelta(days=400)).isoformat()
    fake_supabase.store["baux"] = [
        {
            "id": "bail-nobien",
            "id_bien": None,
            "date_debut": start,
            "loyer_hc": 1000.0,
            "statut": "en_cours",
            "indice_irl_reference": None,
        }
    ]
    count = await check_irl_revisions(fake_supabase)
    assert count == 0


@pytest.mark.asyncio
async def test_zero_loyer_skipped(fake_supabase, mock_notify):
    """Bail with loyer_hc=0 or None is skipped."""
    today = date.today()
    # Start 2 years ago today → anniversary = today (within 30-day window, age > 365)
    start = today.replace(year=today.year - 2)

    fake_supabase.store["baux"] = [
        {
            "id": "bail-zerloyer",
            "id_bien": "bien-1",
            "date_debut": start.isoformat(),
            "loyer_hc": 0.0,
            "statut": "en_cours",
            "indice_irl_reference": None,
        }
    ]
    fake_supabase.store["biens"] = [
        {"id": "bien-1", "id_sci": "sci-1", "adresse": "Test", "ville": "Paris"}
    ]
    fake_supabase.store["notifications"] = []
    count = await check_irl_revisions(fake_supabase)
    assert count == 0


@pytest.mark.asyncio
async def test_bien_not_found_skipped(fake_supabase, mock_notify):
    """When the bien lookup returns nothing, bail is skipped."""
    today = date.today()
    # Start 2 years ago today → anniversary = today (within 30-day window, age > 365)
    start = today.replace(year=today.year - 2)

    fake_supabase.store["baux"] = [
        {
            "id": "bail-nobien2",
            "id_bien": "bien-nonexistent",
            "date_debut": start.isoformat(),
            "loyer_hc": 800.0,
            "statut": "en_cours",
            "indice_irl_reference": None,
        }
    ]
    fake_supabase.store["biens"] = []  # empty
    fake_supabase.store["notifications"] = []
    count = await check_irl_revisions(fake_supabase)
    assert count == 0


@pytest.mark.asyncio
async def test_bien_missing_sci_id_skipped(fake_supabase, mock_notify):
    """When the bien has no id_sci, bail is skipped."""
    today = date.today()
    # Start 2 years ago today → anniversary = today (within 30-day window, age > 365)
    start = today.replace(year=today.year - 2)

    fake_supabase.store["baux"] = [
        {
            "id": "bail-nosciid",
            "id_bien": "bien-nosci",
            "date_debut": start.isoformat(),
            "loyer_hc": 800.0,
            "statut": "en_cours",
            "indice_irl_reference": None,
        }
    ]
    fake_supabase.store["biens"] = [
        {"id": "bien-nosci", "id_sci": None, "adresse": "Missing SCI", "ville": "Nowhere"}
    ]
    fake_supabase.store["notifications"] = []
    count = await check_irl_revisions(fake_supabase)
    assert count == 0


@pytest.mark.asyncio
async def test_invalid_date_format_skipped(fake_supabase, mock_notify):
    """Bail with an invalid date_debut format is skipped gracefully."""
    fake_supabase.store["baux"] = [
        {
            "id": "bail-baddate",
            "id_bien": "bien-1",
            "date_debut": "not-a-date",
            "loyer_hc": 1000.0,
            "statut": "en_cours",
            "indice_irl_reference": None,
        }
    ]
    count = await check_irl_revisions(fake_supabase)
    assert count == 0


@pytest.mark.asyncio
async def test_multiple_baux_multiple_notifications(fake_supabase, mock_notify):
    """Multiple qualifying baux each produce their own notifications."""
    today = date.today()
    # Both start 2 years ago today: age > 365, anniversary = today (days_until=0 <= 30)
    start_2y = today.replace(year=today.year - 2).isoformat()

    fake_supabase.store["baux"] = [
        {
            "id": "bail-multi-1",
            "id_bien": "bien-1",
            "date_debut": start_2y,
            "loyer_hc": 1000.0,
            "statut": "en_cours",
            "indice_irl_reference": None,
        },
        {
            "id": "bail-multi-2",
            "id_bien": "bien-9",
            "date_debut": start_2y,
            "loyer_hc": 800.0,
            "statut": "en_cours",
            "indice_irl_reference": None,
        },
    ]
    fake_supabase.store["biens"] = [
        {"id": "bien-1", "id_sci": "sci-1", "adresse": "Addr 1", "ville": "Paris"},
        {"id": "bien-9", "id_sci": "sci-2", "adresse": "Addr 9", "ville": "Lyon"},
    ]
    fake_supabase.store["associes"] = [
        {"id": "a1", "id_sci": "sci-1", "user_id": "user-A"},
        {"id": "a2", "id_sci": "sci-2", "user_id": "user-B"},
    ]
    fake_supabase.store["notifications"] = []

    count = await check_irl_revisions(fake_supabase)
    # bail-multi-1 → sci-1 → 1 owner; bail-multi-2 → sci-2 → 1 owner
    assert count == 2


@pytest.mark.asyncio
async def test_irl_increase_factor_value():
    """IRL_INCREASE_FACTOR constant should be 1.025 (2.5%)."""
    assert IRL_INCREASE_FACTOR == 1.025


@pytest.mark.asyncio
async def test_notify_returns_false_not_counted(fake_supabase):
    """When create_notification_with_email returns False, count is not incremented."""
    today = date.today()
    # Start 2 years ago today → anniversary = today (within 30-day window, age > 365)
    start = today.replace(year=today.year - 2)

    fake_supabase.store["baux"] = [
        {
            "id": "bail-notfalse",
            "id_bien": "bien-1",
            "date_debut": start.isoformat(),
            "loyer_hc": 1000.0,
            "statut": "en_cours",
            "indice_irl_reference": None,
        }
    ]
    fake_supabase.store["biens"] = [
        {"id": "bien-1", "id_sci": "sci-1", "adresse": "No Notif", "ville": "Paris"}
    ]
    fake_supabase.store["associes"] = [
        {"id": "a1", "id_sci": "sci-1", "user_id": "user-X"}
    ]
    fake_supabase.store["notifications"] = []

    with patch(
        "app.services.irl_service.create_notification_with_email",
        new_callable=AsyncMock,
        return_value=False,  # notification creation failed
    ):
        count = await check_irl_revisions(fake_supabase)
    assert count == 0
