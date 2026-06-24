"""Tests for app/services/comptabilite_service.py.

Covers:
- ComptabiliteService.get_recap_annuel: no biens, single bien, multiple biens,
  pct change N vs N-1, evenements deductibles, only 'paye'/'paid' loyers count
- ComptabiliteService.get_evolution_mensuelle: no biens, monthly aggregation
- _fetch_loyers, _fetch_charges, _fetch_evenements_deductibles helpers
- _pct_change: zero old, positive growth, negative change
- _empty_recap structure
"""
from __future__ import annotations

from copy import deepcopy

import pytest

from tests.conftest import FakeSupabaseClient
from app.services.comptabilite_service import (
    ComptabiliteService,
    _pct_change,
    _empty_recap,
    _fetch_loyers,
    _fetch_charges,
    _fetch_evenements_deductibles,
)


# ── Constants ─────────────────────────────────────────────────────────────────

SCI_ID = "sci-1"
BIEN_1 = "bien-1"
BIEN_2 = "bien-2"
ANNEE = 2025


# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_client(
    biens=None,
    loyers=None,
    charges=None,
    evenements=None,
) -> FakeSupabaseClient:
    c = FakeSupabaseClient()
    c.store["biens"] = biens if biens is not None else []
    c.store["loyers"] = loyers if loyers is not None else []
    c.store["charges"] = charges if charges is not None else []
    c.store["evenements_bien"] = evenements if evenements is not None else []
    return c


def _bien(id_=BIEN_1, sci_id=SCI_ID, adresse="1 rue Test", ville="Paris"):
    return {"id": id_, "id_sci": sci_id, "adresse": adresse, "ville": ville}


def _loyer(bien_id, montant, statut="paye", date_str=None):
    return {
        "id": f"loyer-{bien_id}-{montant}",
        "id_bien": bien_id,
        "montant": montant,
        "statut": statut,
        "date_loyer": date_str or f"{ANNEE}-06-01",
    }


def _charge(bien_id, montant, date_str=None):
    return {
        "id": f"charge-{bien_id}-{montant}",
        "id_bien": bien_id,
        "montant": montant,
        "date_paiement": date_str or f"{ANNEE}-06-01",
    }


def _evenement(bien_id, montant, deductible=True, date_str=None):
    return {
        "id": f"evt-{bien_id}-{montant}",
        "id_bien": bien_id,
        "montant": montant,
        "deductible_fiscalement": deductible,
        "date_evenement": date_str or f"{ANNEE}-06-01",
    }


# ── Tests: get_recap_annuel — no biens ────────────────────────────────────────


class TestGetRecapAnnuelNoBiens:
    def test_returns_empty_recap_when_no_biens(self):
        c = _make_client(biens=[])
        result = ComptabiliteService.get_recap_annuel(c, SCI_ID, ANNEE)

        assert result["annee"] == ANNEE
        assert result["biens"] == []
        assert result["totaux"]["revenus"] == 0
        assert result["totaux"]["charges"] == 0
        assert result["totaux"]["resultat"] == 0
        assert result["totaux"]["evenements_deductibles"] == 0
        assert result["variation_n1"]["revenus_pct"] is None
        assert result["variation_n1"]["charges_pct"] is None
        assert result["variation_n1"]["resultat_pct"] is None


# ── Tests: get_recap_annuel — single bien ─────────────────────────────────────


class TestGetRecapAnnuelSingleBien:
    def test_basic_recap_single_bien(self):
        """Simple case: 1200 revenus, 300 charges → resultat 900."""
        c = _make_client(
            biens=[_bien()],
            loyers=[
                _loyer(BIEN_1, 600, "paye", f"{ANNEE}-01-01"),
                _loyer(BIEN_1, 600, "paye", f"{ANNEE}-07-01"),
            ],
            charges=[_charge(BIEN_1, 300, f"{ANNEE}-03-01")],
        )
        result = ComptabiliteService.get_recap_annuel(c, SCI_ID, ANNEE)

        bien_data = result["biens"][0]
        assert bien_data["bien_id"] == BIEN_1
        assert bien_data["revenus"] == 1200.0
        assert bien_data["charges"] == 300.0
        assert bien_data["resultat"] == 900.0
        assert result["totaux"]["revenus"] == 1200.0
        assert result["totaux"]["charges"] == 300.0
        assert result["totaux"]["resultat"] == 900.0

    def test_only_paye_loyers_count(self):
        """Loyers with statut en_attente or en_retard must not count as revenus."""
        c = _make_client(
            biens=[_bien()],
            loyers=[
                _loyer(BIEN_1, 1000, "paye"),
                _loyer(BIEN_1, 500, "en_attente"),
                _loyer(BIEN_1, 500, "en_retard"),
            ],
        )
        result = ComptabiliteService.get_recap_annuel(c, SCI_ID, ANNEE)
        assert result["totaux"]["revenus"] == 1000.0

    def test_paid_status_also_counted(self):
        """Loyers with statut 'paid' (English variant) also count."""
        c = _make_client(
            biens=[_bien()],
            loyers=[_loyer(BIEN_1, 800, "paid")],
        )
        result = ComptabiliteService.get_recap_annuel(c, SCI_ID, ANNEE)
        assert result["totaux"]["revenus"] == 800.0

    def test_evenements_deductibles_reduce_resultat(self):
        """Deductible evenements reduce resultat like charges."""
        c = _make_client(
            biens=[_bien()],
            loyers=[_loyer(BIEN_1, 1200, "paye")],
            charges=[_charge(BIEN_1, 200)],
            evenements=[_evenement(BIEN_1, 300)],
        )
        result = ComptabiliteService.get_recap_annuel(c, SCI_ID, ANNEE)
        bien_data = result["biens"][0]
        # resultat = 1200 - 200 - 300 = 700
        assert bien_data["evenements_deductibles"] == 300.0
        assert bien_data["resultat"] == 700.0

    def test_non_deductible_evenements_not_counted(self):
        """Evenements with deductible_fiscalement=False should not reduce resultat."""
        c = _make_client(
            biens=[_bien()],
            loyers=[_loyer(BIEN_1, 1200, "paye")],
            evenements=[_evenement(BIEN_1, 500, deductible=False)],
        )
        result = ComptabiliteService.get_recap_annuel(c, SCI_ID, ANNEE)
        # Non-deductible event: resultat = 1200 - 0 - 0 = 1200
        assert result["totaux"]["resultat"] == 1200.0

    def test_loyers_out_of_year_not_counted(self):
        """Loyers from a different year must not be included."""
        c = _make_client(
            biens=[_bien()],
            loyers=[
                _loyer(BIEN_1, 800, "paye", f"{ANNEE}-06-01"),        # in year → count
                _loyer(BIEN_1, 9999, "paye", f"{ANNEE + 1}-01-01"),   # out of year
                _loyer(BIEN_1, 9999, "paye", f"{ANNEE - 1}-12-31"),   # out of year
            ],
        )
        result = ComptabiliteService.get_recap_annuel(c, SCI_ID, ANNEE)
        assert result["totaux"]["revenus"] == 800.0

    def test_bien_info_fields_present(self):
        """Each bien in result should have adresse and ville."""
        c = _make_client(biens=[_bien(adresse="42 rue Victor Hugo", ville="Lyon")])
        result = ComptabiliteService.get_recap_annuel(c, SCI_ID, ANNEE)
        bien_data = result["biens"][0]
        assert bien_data["adresse"] == "42 rue Victor Hugo"
        assert bien_data["ville"] == "Lyon"


# ── Tests: get_recap_annuel — multiple biens ──────────────────────────────────


class TestGetRecapAnnuelMultipleBiens:
    def test_totaux_aggregated_across_biens(self):
        """Totaux should sum revenus and charges from all biens."""
        c = _make_client(
            biens=[_bien(BIEN_1, SCI_ID), _bien(BIEN_2, SCI_ID, "2 rue Exemple", "Lyon")],
            loyers=[
                _loyer(BIEN_1, 1000, "paye"),
                _loyer(BIEN_2, 800, "paye"),
            ],
            charges=[
                _charge(BIEN_1, 200),
                _charge(BIEN_2, 150),
            ],
        )
        result = ComptabiliteService.get_recap_annuel(c, SCI_ID, ANNEE)
        assert result["totaux"]["revenus"] == 1800.0
        assert result["totaux"]["charges"] == 350.0
        assert result["totaux"]["resultat"] == 1450.0
        assert len(result["biens"]) == 2

    def test_charges_per_bien_isolated(self):
        """Charges for bien-2 should not appear in bien-1's recap."""
        c = _make_client(
            biens=[_bien(BIEN_1, SCI_ID), _bien(BIEN_2, SCI_ID, "x", "x")],
            loyers=[_loyer(BIEN_1, 1000, "paye")],
            charges=[
                _charge(BIEN_1, 100),
                _charge(BIEN_2, 999),
            ],
        )
        result = ComptabiliteService.get_recap_annuel(c, SCI_ID, ANNEE)
        b1 = next(b for b in result["biens"] if b["bien_id"] == BIEN_1)
        assert b1["charges"] == 100.0


# ── Tests: N-1 comparison / variation_n1 ─────────────────────────────────────


class TestGetRecapAnnuelN1Comparison:
    def test_variation_n1_none_when_n1_has_no_data(self):
        """When N-1 revenus/charges are 0, variation_pct should be None."""
        c = _make_client(
            biens=[_bien()],
            loyers=[_loyer(BIEN_1, 1200, "paye", f"{ANNEE}-06-01")],
        )
        result = ComptabiliteService.get_recap_annuel(c, SCI_ID, ANNEE)
        # No N-1 data → all None
        assert result["variation_n1"]["revenus_pct"] is None
        assert result["variation_n1"]["charges_pct"] is None

    def test_variation_n1_computed_when_n1_has_data(self):
        """Growth from 1000 to 1200 = +20%."""
        n1 = ANNEE - 1
        c = _make_client(
            biens=[_bien()],
            loyers=[
                _loyer(BIEN_1, 1000, "paye", f"{n1}-06-01"),   # N-1
                _loyer(BIEN_1, 1200, "paye", f"{ANNEE}-06-01"), # N
            ],
        )
        result = ComptabiliteService.get_recap_annuel(c, SCI_ID, ANNEE)
        assert result["variation_n1"]["revenus_pct"] == 20.0

    def test_variation_n1_negative_change(self):
        """Drop from 1000 to 800 = -20%."""
        n1 = ANNEE - 1
        c = _make_client(
            biens=[_bien()],
            loyers=[
                _loyer(BIEN_1, 1000, "paye", f"{n1}-06-01"),  # N-1
                _loyer(BIEN_1, 800, "paye", f"{ANNEE}-06-01"), # N
            ],
        )
        result = ComptabiliteService.get_recap_annuel(c, SCI_ID, ANNEE)
        assert result["variation_n1"]["revenus_pct"] == -20.0


# ── Tests: get_evolution_mensuelle ───────────────────────────────────────────


class TestGetEvolutionMensuellaNoBiens:
    def test_returns_12_empty_months_when_no_biens(self):
        c = _make_client(biens=[])
        result = ComptabiliteService.get_evolution_mensuelle(c, SCI_ID, ANNEE)

        assert len(result) == 12
        for item in result:
            assert item["revenus"] == 0.0
            assert item["charges"] == 0.0
        # Check months span full year
        months = [item["mois"] for item in result]
        assert months[0] == f"{ANNEE}-01"
        assert months[-1] == f"{ANNEE}-12"


class TestGetEvolutionMensuelle:
    def test_monthly_revenus_aggregated_correctly(self):
        """Two loyers in the same month should be summed."""
        c = _make_client(
            biens=[_bien()],
            loyers=[
                _loyer(BIEN_1, 600, "paye", f"{ANNEE}-03-01"),
                _loyer(BIEN_1, 400, "paye", f"{ANNEE}-03-15"),
                _loyer(BIEN_1, 800, "paye", f"{ANNEE}-09-01"),
            ],
        )
        result = ComptabiliteService.get_evolution_mensuelle(c, SCI_ID, ANNEE)
        by_month = {r["mois"]: r for r in result}

        assert by_month[f"{ANNEE}-03"]["revenus"] == 1000.0
        assert by_month[f"{ANNEE}-09"]["revenus"] == 800.0
        assert by_month[f"{ANNEE}-01"]["revenus"] == 0.0

    def test_monthly_charges_aggregated_correctly(self):
        c = _make_client(
            biens=[_bien()],
            charges=[
                _charge(BIEN_1, 300, f"{ANNEE}-02-01"),
                _charge(BIEN_1, 100, f"{ANNEE}-02-28"),
            ],
        )
        result = ComptabiliteService.get_evolution_mensuelle(c, SCI_ID, ANNEE)
        by_month = {r["mois"]: r for r in result}

        assert by_month[f"{ANNEE}-02"]["charges"] == 400.0

    def test_only_paye_loyers_count_in_monthly(self):
        """Unpaid loyers should not count as revenus in monthly evolution."""
        c = _make_client(
            biens=[_bien()],
            loyers=[
                _loyer(BIEN_1, 1000, "paye", f"{ANNEE}-05-01"),
                _loyer(BIEN_1, 999, "en_attente", f"{ANNEE}-05-15"),
            ],
        )
        result = ComptabiliteService.get_evolution_mensuelle(c, SCI_ID, ANNEE)
        by_month = {r["mois"]: r for r in result}
        assert by_month[f"{ANNEE}-05"]["revenus"] == 1000.0

    def test_loyers_from_other_year_excluded(self):
        """Loyers outside the target year must not appear in monthly data."""
        c = _make_client(
            biens=[_bien()],
            loyers=[
                _loyer(BIEN_1, 1000, "paye", f"{ANNEE}-06-01"),
                _loyer(BIEN_1, 9999, "paye", f"{ANNEE + 1}-01-01"),
            ],
        )
        result = ComptabiliteService.get_evolution_mensuelle(c, SCI_ID, ANNEE)
        total_revenus = sum(r["revenus"] for r in result)
        assert total_revenus == 1000.0

    def test_returns_12_sorted_months(self):
        c = _make_client(biens=[_bien()])
        result = ComptabiliteService.get_evolution_mensuelle(c, SCI_ID, ANNEE)
        assert len(result) == 12
        months = [r["mois"] for r in result]
        assert months == sorted(months)

    def test_each_entry_has_required_keys(self):
        c = _make_client(biens=[_bien()])
        result = ComptabiliteService.get_evolution_mensuelle(c, SCI_ID, ANNEE)
        for entry in result:
            assert "mois" in entry
            assert "revenus" in entry
            assert "charges" in entry


# ── Tests: _pct_change helper ─────────────────────────────────────────────────


class TestPctChange:
    def test_positive_growth(self):
        assert _pct_change(1000.0, 1200.0) == 20.0

    def test_negative_growth(self):
        assert _pct_change(1000.0, 800.0) == -20.0

    def test_no_change(self):
        assert _pct_change(500.0, 500.0) == 0.0

    def test_old_is_zero_returns_none(self):
        assert _pct_change(0.0, 1000.0) is None

    def test_both_zero_returns_none(self):
        assert _pct_change(0.0, 0.0) is None

    def test_result_rounded_to_one_decimal(self):
        # 100 → 133.33... = 33.3%
        result = _pct_change(100.0, 133.333)
        assert result == 33.3

    def test_old_negative_uses_abs(self):
        """When old is negative (e.g. loss), abs(old) is used as denominator."""
        # old=-100, new=-50 → change = (-50 - -100) / 100 * 100 = 50.0
        result = _pct_change(-100.0, -50.0)
        assert result == 50.0


# ── Tests: _empty_recap ───────────────────────────────────────────────────────


class TestEmptyRecap:
    def test_empty_recap_structure(self):
        result = _empty_recap(2025)
        assert result["annee"] == 2025
        assert result["biens"] == []
        assert result["totaux"]["revenus"] == 0
        assert result["totaux"]["charges"] == 0
        assert result["totaux"]["evenements_deductibles"] == 0
        assert result["totaux"]["resultat"] == 0
        assert result["variation_n1"]["revenus_pct"] is None
        assert result["variation_n1"]["charges_pct"] is None
        assert result["variation_n1"]["resultat_pct"] is None


# ── Tests: _fetch_evenements_deductibles exception handling ───────────────────


class TestFetchEvenementsDeductiblesException:
    def test_exception_returns_empty_list(self):
        """If the DB query raises, the function returns [] silently."""

        class BrokenClient:
            def table(self, name):
                raise RuntimeError("DB unavailable")

        result = _fetch_evenements_deductibles(BrokenClient(), [BIEN_1], f"{ANNEE}-01-01", f"{ANNEE}-12-31")
        assert result == []


# ── Tests: _fetch_loyers and _fetch_charges ───────────────────────────────────


class TestFetchHelpers:
    def test_fetch_loyers_returns_matching(self):
        c = _make_client(
            loyers=[
                {"id": "l1", "id_bien": BIEN_1, "montant": 500, "statut": "paye", "date_loyer": f"{ANNEE}-03-01"},
                {"id": "l2", "id_bien": "other", "montant": 999, "statut": "paye", "date_loyer": f"{ANNEE}-03-01"},
            ]
        )
        rows = _fetch_loyers(c, [BIEN_1], f"{ANNEE}-01-01", f"{ANNEE}-12-31")
        assert len(rows) == 1
        assert rows[0]["id"] == "l1"

    def test_fetch_charges_returns_matching(self):
        c = _make_client(
            charges=[
                {"id": "c1", "id_bien": BIEN_1, "montant": 200, "date_paiement": f"{ANNEE}-04-01"},
                {"id": "c2", "id_bien": "other", "montant": 999, "date_paiement": f"{ANNEE}-04-01"},
            ]
        )
        rows = _fetch_charges(c, [BIEN_1], f"{ANNEE}-01-01", f"{ANNEE}-12-31")
        assert len(rows) == 1
        assert rows[0]["id"] == "c1"

    def test_fetch_loyers_empty_bien_ids(self):
        c = _make_client(loyers=[{"id": "l1", "id_bien": BIEN_1, "montant": 500, "statut": "paye", "date_loyer": f"{ANNEE}-03-01"}])
        rows = _fetch_loyers(c, [], f"{ANNEE}-01-01", f"{ANNEE}-12-31")
        # in_() with empty list → FakeQuery returns no rows
        assert isinstance(rows, list)
