"""Tests for app.services.credit_service — targeting >80% coverage.

Covers:
- generate_amortissement: nominal case, taux=0, short duration, month-end rounding, _days_in_month helper
"""

from __future__ import annotations

import pytest

from app.services.credit_service import _days_in_month, generate_amortissement


# ---------------------------------------------------------------------------
# _days_in_month
# ---------------------------------------------------------------------------


class TestDaysInMonth:

    def test_january(self):
        assert _days_in_month(2025, 1) == 31

    def test_february_common_year(self):
        assert _days_in_month(2025, 2) == 28

    def test_february_leap_year(self):
        assert _days_in_month(2024, 2) == 29

    def test_april_30_days(self):
        assert _days_in_month(2025, 4) == 30

    def test_december(self):
        """December triggers the year+1 branch in _days_in_month."""
        assert _days_in_month(2025, 12) == 31

    def test_november(self):
        assert _days_in_month(2025, 11) == 30


# ---------------------------------------------------------------------------
# generate_amortissement — nominal case
# ---------------------------------------------------------------------------


class TestGenerateAmortissementNominal:

    def test_row_count_matches_duration(self):
        """Number of rows must equal duree_mois."""
        rows = generate_amortissement(
            montant=200_000.0,
            taux_nominal=2.5,
            taux_assurance=0.3,
            duree_mois=12,
            date_debut="2025-01-01",
            mensualite=1_693.09,
        )
        assert len(rows) == 12

    def test_first_row_fields(self):
        """First row has mois=1 and expected fields."""
        rows = generate_amortissement(
            montant=100_000.0,
            taux_nominal=3.0,
            taux_assurance=0.25,
            duree_mois=6,
            date_debut="2025-01-01",
            mensualite=16_889.16,
        )
        row = rows[0]
        assert row["mois"] == 1
        assert "date" in row
        assert "mensualite" in row
        assert "capital" in row
        assert "interets" in row
        assert "assurance" in row
        assert "capital_restant" in row

    def test_first_row_interest_calculation(self):
        """Interest for first month = capital * monthly_rate."""
        montant = 100_000.0
        taux_nominal = 3.0
        taux_mensuel = (taux_nominal / 100) / 12
        expected_interets = round(montant * taux_mensuel, 2)

        rows = generate_amortissement(
            montant=montant,
            taux_nominal=taux_nominal,
            taux_assurance=0.0,
            duree_mois=12,
            date_debut="2025-01-01",
            mensualite=8_513.21,
        )
        assert rows[0]["interets"] == expected_interets

    def test_insurance_calculation(self):
        """Insurance = montant * taux_assurance_mensuel (constant across all rows)."""
        montant = 120_000.0
        taux_assurance = 0.36
        taux_assurance_mensuel = (taux_assurance / 100) / 12
        expected_assurance = round(montant * taux_assurance_mensuel, 2)

        rows = generate_amortissement(
            montant=montant,
            taux_nominal=2.0,
            taux_assurance=taux_assurance,
            duree_mois=3,
            date_debut="2025-01-01",
            mensualite=40_200.0,
        )
        for row in rows:
            assert row["assurance"] == expected_assurance

    def test_last_row_capital_restant_is_zero(self):
        """After the final payment, capital_restant should be 0 (or very close)."""
        rows = generate_amortissement(
            montant=50_000.0,
            taux_nominal=2.0,
            taux_assurance=0.2,
            duree_mois=24,
            date_debut="2025-01-01",
            mensualite=2_127.71,
        )
        assert rows[-1]["capital_restant"] == 0.0

    def test_last_row_mois(self):
        """Last row mois must equal duree_mois."""
        duree = 6
        rows = generate_amortissement(
            montant=60_000.0,
            taux_nominal=1.5,
            taux_assurance=0.1,
            duree_mois=duree,
            date_debut="2025-06-01",
            mensualite=10_075.0,
        )
        assert rows[-1]["mois"] == duree

    def test_capital_restant_decreases_monotonically(self):
        """Capital restant should be non-increasing across rows."""
        rows = generate_amortissement(
            montant=80_000.0,
            taux_nominal=2.0,
            taux_assurance=0.3,
            duree_mois=12,
            date_debut="2025-01-01",
            mensualite=6_754.0,
        )
        for i in range(1, len(rows)):
            assert rows[i]["capital_restant"] <= rows[i - 1]["capital_restant"]

    def test_mensualite_includes_assurance(self):
        """Row mensualite = base mensualite + assurance."""
        montant = 100_000.0
        taux_nominal = 2.0
        taux_assurance = 0.24
        base_mensualite = 8_516.0

        taux_assurance_mensuel = (taux_assurance / 100) / 12
        expected_assurance = round(montant * taux_assurance_mensuel, 2)

        rows = generate_amortissement(
            montant=montant,
            taux_nominal=taux_nominal,
            taux_assurance=taux_assurance,
            duree_mois=12,
            date_debut="2025-01-01",
            mensualite=base_mensualite,
        )
        for row in rows:
            assert row["mensualite"] == round(base_mensualite + expected_assurance, 2)


# ---------------------------------------------------------------------------
# generate_amortissement — zero interest rate
# ---------------------------------------------------------------------------


class TestGenerateAmortissementZeroRate:

    def test_zero_rate_no_interest(self):
        """With taux_nominal=0, every row has interets=0."""
        montant = 60_000.0
        duree_mois = 12
        mensualite = montant / duree_mois  # 5000.0 per month

        rows = generate_amortissement(
            montant=montant,
            taux_nominal=0.0,
            taux_assurance=0.0,
            duree_mois=duree_mois,
            date_debut="2025-01-01",
            mensualite=mensualite,
        )
        for row in rows:
            assert row["interets"] == 0.0

    def test_zero_rate_capital_equals_mensualite(self):
        """With taux_nominal=0, capital repaid each month equals mensualite."""
        montant = 24_000.0
        duree_mois = 12
        mensualite = 2_000.0

        rows = generate_amortissement(
            montant=montant,
            taux_nominal=0.0,
            taux_assurance=0.0,
            duree_mois=duree_mois,
            date_debut="2025-01-01",
            mensualite=mensualite,
        )
        # All rows except last: capital = mensualite - interets = mensualite - 0 = mensualite
        for row in rows[:-1]:
            assert row["capital"] == mensualite

    def test_zero_rate_and_zero_insurance(self):
        """Both rates zero: mensualite_row == base mensualite."""
        montant = 12_000.0
        mensualite = 1_000.0
        rows = generate_amortissement(
            montant=montant,
            taux_nominal=0.0,
            taux_assurance=0.0,
            duree_mois=12,
            date_debut="2025-03-01",
            mensualite=mensualite,
        )
        for row in rows:
            assert row["mensualite"] == mensualite


# ---------------------------------------------------------------------------
# generate_amortissement — short duration edge cases
# ---------------------------------------------------------------------------


class TestGenerateAmortissementShortDuration:

    def test_single_month_loan(self):
        """A 1-month loan: only one row, last-month branch used."""
        montant = 10_000.0
        rows = generate_amortissement(
            montant=montant,
            taux_nominal=3.0,
            taux_assurance=0.0,
            duree_mois=1,
            date_debut="2025-05-01",
            mensualite=10_025.0,
        )
        assert len(rows) == 1
        assert rows[0]["mois"] == 1
        # Last month: capital = capital_restant (whole amount)
        assert rows[0]["capital"] == montant
        assert rows[0]["capital_restant"] == 0.0

    def test_two_month_loan(self):
        """A 2-month loan: first row normal, second row uses last-month branch."""
        montant = 20_000.0
        rows = generate_amortissement(
            montant=montant,
            taux_nominal=0.0,
            taux_assurance=0.0,
            duree_mois=2,
            date_debut="2025-11-01",
            mensualite=10_000.0,
        )
        assert len(rows) == 2
        assert rows[0]["mois"] == 1
        assert rows[1]["mois"] == 2
        assert rows[1]["capital_restant"] == 0.0


# ---------------------------------------------------------------------------
# generate_amortissement — negative capital guard (lines 51, 55)
# ---------------------------------------------------------------------------


class TestGenerateAmortissementNegativeGuard:

    def test_mensualite_less_than_interest_clamps_capital_to_zero(self):
        """When mensualite < interets, capital would be negative → clamped to 0."""
        # Use a very high interest rate and low mensualite to trigger negative capital guard.
        # montant=100_000, taux_nominal=120% → monthly rate = 10%
        # interets month 1 = 100_000 * 0.10 = 10_000
        # mensualite = 5_000 < interets → capital = 5_000 - 10_000 = -5_000 → clamped to 0
        montant = 100_000.0
        rows = generate_amortissement(
            montant=montant,
            taux_nominal=120.0,  # 10% per month
            taux_assurance=0.0,
            duree_mois=3,
            date_debut="2025-01-01",
            mensualite=5_000.0,  # less than monthly interest
        )
        # capital for non-last months should be clamped to 0 or non-negative
        for row in rows[:-1]:
            assert row["capital"] >= 0.0
        # capital_restant should never be negative
        for row in rows:
            assert row["capital_restant"] >= 0.0

    def test_capital_restant_never_goes_negative(self):
        """Even with an overshooting mensualite, capital_restant is clamped to 0.

        This triggers line 55: capital_restant = 0.0.
        A 2-month loan where mensualite is slightly larger than the full balance:
        month 1: capital = mensualite - interets may exceed capital_restant.
        """
        montant = 1_000.0
        # taux_nominal=0 → interets=0, capital = mensualite = 600 in month 1
        # capital_restant = 1000 - 600 = 400 (fine)
        # month 2 = last month: capital = 400, capital_restant = 0
        # To trigger line 55 we need capital > capital_restant in a non-last month.
        # Use mensualite = 1_200 (bigger than montant) and duree_mois = 2:
        # month 1: interets=0, capital = 1200 - 0 = 1200 > 1000 → capital_restant = -200 → 0.0
        rows = generate_amortissement(
            montant=montant,
            taux_nominal=0.0,
            taux_assurance=0.0,
            duree_mois=2,
            date_debut="2025-06-01",
            mensualite=1_200.0,  # larger than total principal
        )
        for row in rows:
            assert row["capital_restant"] >= 0.0


# ---------------------------------------------------------------------------
# generate_amortissement — date calculation
# ---------------------------------------------------------------------------


class TestGenerateAmortissementDates:

    def test_dates_increase_monthly(self):
        """Each row date should be one month after the previous."""
        rows = generate_amortissement(
            montant=100_000.0,
            taux_nominal=2.0,
            taux_assurance=0.0,
            duree_mois=3,
            date_debut="2025-01-15",
            mensualite=33_550.0,
        )
        dates = [row["date"] for row in rows]
        assert dates[0] == "2025-02-15"
        assert dates[1] == "2025-03-15"
        assert dates[2] == "2025-04-15"

    def test_month_end_clamping(self):
        """Starting on Jan 31, subsequent months clamp to shortest month."""
        rows = generate_amortissement(
            montant=50_000.0,
            taux_nominal=1.0,
            taux_assurance=0.0,
            duree_mois=3,
            date_debut="2025-01-31",
            mensualite=16_680.0,
        )
        # Feb has only 28 days in 2025
        assert rows[0]["date"] == "2025-02-28"
        # March has 31 days so 31 is valid
        assert rows[1]["date"] == "2025-03-31"
        # April has 30 days
        assert rows[2]["date"] == "2025-04-30"

    def test_year_rollover_december(self):
        """Starting in Dec, month 1 should land in January of next year."""
        rows = generate_amortissement(
            montant=10_000.0,
            taux_nominal=0.0,
            taux_assurance=0.0,
            duree_mois=2,
            date_debut="2025-12-01",
            mensualite=5_000.0,
        )
        assert rows[0]["date"] == "2026-01-01"
        assert rows[1]["date"] == "2026-02-01"
