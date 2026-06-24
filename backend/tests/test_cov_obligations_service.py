"""Tests for app/services/obligations_service.py.

Covers get_obligations() for all 7 check categories:
- pno: valid, expired, missing
- dpe: valid, expired, no date, no class
- bail: active, none
- locataire: linked, missing, no bail
- depot_garantie: present, zero, no bail
- edl_entree: present, missing, no bail
- diagnostics: each of amiante/electricite/gaz/plomb (valid, expired, missing date)

Also covers _parse_date edge cases.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from tests.conftest import FakeSupabaseClient
from app.services.obligations_service import get_obligations, _parse_date


# ── Helpers ─────────────────────────────────────────────────────────────────

BIEN_ID = "bien-1"
BAIL_ID = "bail-1"
LOC_ID = "loc-1"

TODAY = date.today()
FUTURE = (TODAY + timedelta(days=180)).isoformat()
PAST_SOON = (TODAY - timedelta(days=30)).isoformat()
FAR_PAST_10Y = (TODAY - timedelta(days=365 * 11)).isoformat()
FAR_PAST_3Y = (TODAY - timedelta(days=365 * 4)).isoformat()
FAR_PAST_6Y = (TODAY - timedelta(days=365 * 7)).isoformat()
VALID_6Y = (TODAY - timedelta(days=365 * 2)).isoformat()
VALID_10Y = (TODAY - timedelta(days=365 * 5)).isoformat()
VALID_3Y = (TODAY - timedelta(days=365 * 1)).isoformat()


def _make_client(
    biens=None,
    pno=None,
    baux=None,
    bail_locataires=None,
) -> FakeSupabaseClient:
    c = FakeSupabaseClient()
    c.store["biens"] = biens if biens is not None else [{"id": BIEN_ID}]
    c.store["assurances_pno"] = pno if pno is not None else []
    c.store["baux"] = baux if baux is not None else []
    c.store["bail_locataires"] = bail_locataires if bail_locataires is not None else []
    return c


def _default_bien(**kwargs):
    base = {"id": BIEN_ID}
    base.update(kwargs)
    return base


def _default_bail(depot_garantie=1000, etat_lieux_entree=None):
    return {
        "id": BAIL_ID,
        "id_bien": BIEN_ID,
        "date_debut": "2024-01-01",
        "date_fin": "2026-12-31",
        "depot_garantie": depot_garantie,
        "statut": "en_cours",
        "etat_lieux_entree": etat_lieux_entree,
    }


# ── Tests: PNO ───────────────────────────────────────────────────────────────


class TestPno:
    def test_pno_valid_when_future_echeance(self):
        c = _make_client(
            pno=[{"id": "pno-1", "id_bien": BIEN_ID, "date_echeance": FUTURE, "compagnie": "MAIF"}],
        )
        result = get_obligations(c, BIEN_ID)
        assert result["pno"]["valid"] is True
        assert "MAIF" in result["pno"]["detail"]

    def test_pno_invalid_when_past_echeance(self):
        c = _make_client(
            pno=[{"id": "pno-1", "id_bien": BIEN_ID, "date_echeance": PAST_SOON, "compagnie": "AXA"}],
        )
        result = get_obligations(c, BIEN_ID)
        assert result["pno"]["valid"] is False
        assert "Expirée" in result["pno"]["detail"]

    def test_pno_invalid_when_no_insurance(self):
        c = _make_client(pno=[])
        result = get_obligations(c, BIEN_ID)
        assert result["pno"]["valid"] is False
        assert "Aucune" in result["pno"]["detail"]


# ── Tests: DPE ───────────────────────────────────────────────────────────────


class TestDpe:
    def test_dpe_valid_when_class_and_recent_date(self):
        c = _make_client(biens=[_default_bien(dpe_classe="B", dpe_date=VALID_10Y)])
        result = get_obligations(c, BIEN_ID)
        assert result["dpe"]["valid"] is True
        assert "Classe B" in result["dpe"]["detail"]

    def test_dpe_invalid_when_date_too_old(self):
        c = _make_client(biens=[_default_bien(dpe_classe="C", dpe_date=FAR_PAST_10Y)])
        result = get_obligations(c, BIEN_ID)
        assert result["dpe"]["valid"] is False
        assert "expiré" in result["dpe"]["detail"]

    def test_dpe_invalid_when_no_class(self):
        c = _make_client(biens=[_default_bien()])
        result = get_obligations(c, BIEN_ID)
        assert result["dpe"]["valid"] is False
        assert "Aucun DPE" in result["dpe"]["detail"]

    def test_dpe_invalid_when_class_but_no_date(self):
        c = _make_client(biens=[_default_bien(dpe_classe="D")])
        result = get_obligations(c, BIEN_ID)
        assert result["dpe"]["valid"] is False
        assert "date du diagnostic manquante" in result["dpe"]["detail"]


# ── Tests: Bail ───────────────────────────────────────────────────────────────


class TestBail:
    def test_bail_valid_when_en_cours(self):
        c = _make_client(baux=[_default_bail()])
        result = get_obligations(c, BIEN_ID)
        assert result["bail"]["valid"] is True
        assert "actif" in result["bail"]["detail"]

    def test_bail_invalid_when_no_bail(self):
        c = _make_client(baux=[])
        result = get_obligations(c, BIEN_ID)
        assert result["bail"]["valid"] is False
        assert "Aucun bail" in result["bail"]["detail"]

    def test_bail_invalid_when_not_en_cours(self):
        non_active_bail = {
            "id": BAIL_ID,
            "id_bien": BIEN_ID,
            "date_debut": "2020-01-01",
            "date_fin": "2022-12-31",
            "depot_garantie": 0,
            "statut": "termine",
            "etat_lieux_entree": None,
        }
        # Only "en_cours" is selected by the service filter
        c = _make_client(baux=[non_active_bail])
        result = get_obligations(c, BIEN_ID)
        # The service queries .eq("statut", "en_cours"), so termine bail won't match
        assert result["bail"]["valid"] is False


# ── Tests: Locataire ─────────────────────────────────────────────────────────


class TestLocataire:
    def test_locataire_valid_when_linked(self):
        c = _make_client(
            baux=[_default_bail()],
            bail_locataires=[{"id": "bl-1", "id_bail": BAIL_ID, "id_locataire": LOC_ID}],
        )
        result = get_obligations(c, BIEN_ID)
        assert result["locataire"]["valid"] is True
        assert "1 locataire" in result["locataire"]["detail"]

    def test_locataire_invalid_when_none_linked(self):
        c = _make_client(
            baux=[_default_bail()],
            bail_locataires=[],
        )
        result = get_obligations(c, BIEN_ID)
        assert result["locataire"]["valid"] is False
        assert "sans locataire" in result["locataire"]["detail"]

    def test_locataire_invalid_when_no_bail(self):
        c = _make_client(baux=[], bail_locataires=[])
        result = get_obligations(c, BIEN_ID)
        assert result["locataire"]["valid"] is False
        assert "Aucun locataire" in result["locataire"]["detail"]

    def test_locataire_counts_multiple(self):
        c = _make_client(
            baux=[_default_bail()],
            bail_locataires=[
                {"id": "bl-1", "id_bail": BAIL_ID, "id_locataire": "loc-1"},
                {"id": "bl-2", "id_bail": BAIL_ID, "id_locataire": "loc-2"},
            ],
        )
        result = get_obligations(c, BIEN_ID)
        assert result["locataire"]["valid"] is True
        assert "2 locataire" in result["locataire"]["detail"]


# ── Tests: Dépôt de garantie ─────────────────────────────────────────────────


class TestDepotGarantie:
    def test_depot_valid_when_positive(self):
        c = _make_client(
            baux=[_default_bail(depot_garantie=1500)],
            bail_locataires=[{"id": "bl-1", "id_bail": BAIL_ID, "id_locataire": LOC_ID}],
        )
        result = get_obligations(c, BIEN_ID)
        assert result["depot_garantie"]["valid"] is True
        assert "1500.00" in result["depot_garantie"]["detail"]

    def test_depot_invalid_when_zero(self):
        c = _make_client(
            baux=[_default_bail(depot_garantie=0)],
            bail_locataires=[],
        )
        result = get_obligations(c, BIEN_ID)
        assert result["depot_garantie"]["valid"] is False
        assert "sans dépôt" in result["depot_garantie"]["detail"]

    def test_depot_invalid_when_no_bail(self):
        c = _make_client(baux=[])
        result = get_obligations(c, BIEN_ID)
        assert result["depot_garantie"]["valid"] is False
        assert "Aucun dépôt" in result["depot_garantie"]["detail"]


# ── Tests: État des lieux d'entrée ───────────────────────────────────────────


class TestEdlEntree:
    def test_edl_valid_when_date_present(self):
        c = _make_client(baux=[_default_bail(etat_lieux_entree="2024-01-15")])
        result = get_obligations(c, BIEN_ID)
        assert result["edl_entree"]["valid"] is True
        assert "2024-01-15" in result["edl_entree"]["detail"]

    def test_edl_invalid_when_no_date(self):
        c = _make_client(baux=[_default_bail(etat_lieux_entree=None)])
        result = get_obligations(c, BIEN_ID)
        assert result["edl_entree"]["valid"] is False
        assert "Non renseigné" in result["edl_entree"]["detail"]

    def test_edl_invalid_when_no_bail(self):
        c = _make_client(baux=[])
        result = get_obligations(c, BIEN_ID)
        assert result["edl_entree"]["valid"] is False
        assert "Aucun bail actif" in result["edl_entree"]["detail"]


# ── Tests: Diagnostics ───────────────────────────────────────────────────────


class TestDiagnosticsAmiante:
    def test_amiante_valid_within_3_years(self):
        c = _make_client(biens=[_default_bien(diagnostic_amiante_date=VALID_3Y)])
        result = get_obligations(c, BIEN_ID)
        assert result["diagnostics"]["amiante"]["valid"] is True
        assert "3 ans" in result["diagnostics"]["amiante"]["detail"]

    def test_amiante_invalid_older_than_3_years(self):
        c = _make_client(biens=[_default_bien(diagnostic_amiante_date=FAR_PAST_3Y)])
        result = get_obligations(c, BIEN_ID)
        assert result["diagnostics"]["amiante"]["valid"] is False
        assert "expiré" in result["diagnostics"]["amiante"]["detail"]

    def test_amiante_invalid_no_date(self):
        c = _make_client(biens=[_default_bien()])
        result = get_obligations(c, BIEN_ID)
        assert result["diagnostics"]["amiante"]["valid"] is False
        assert "aucune date" in result["diagnostics"]["amiante"]["detail"]


class TestDiagnosticsElectricite:
    def test_electricite_valid_within_6_years(self):
        c = _make_client(biens=[_default_bien(diagnostic_electricite_date=VALID_6Y)])
        result = get_obligations(c, BIEN_ID)
        assert result["diagnostics"]["electricite"]["valid"] is True

    def test_electricite_invalid_older_than_6_years(self):
        c = _make_client(biens=[_default_bien(diagnostic_electricite_date=FAR_PAST_6Y)])
        result = get_obligations(c, BIEN_ID)
        assert result["diagnostics"]["electricite"]["valid"] is False
        assert "expiré" in result["diagnostics"]["electricite"]["detail"]

    def test_electricite_invalid_no_date(self):
        c = _make_client(biens=[_default_bien()])
        result = get_obligations(c, BIEN_ID)
        assert result["diagnostics"]["electricite"]["valid"] is False


class TestDiagnosticsGaz:
    def test_gaz_valid_within_6_years(self):
        c = _make_client(biens=[_default_bien(diagnostic_gaz_date=VALID_6Y)])
        result = get_obligations(c, BIEN_ID)
        assert result["diagnostics"]["gaz"]["valid"] is True

    def test_gaz_invalid_older_than_6_years(self):
        c = _make_client(biens=[_default_bien(diagnostic_gaz_date=FAR_PAST_6Y)])
        result = get_obligations(c, BIEN_ID)
        assert result["diagnostics"]["gaz"]["valid"] is False

    def test_gaz_invalid_no_date(self):
        c = _make_client(biens=[_default_bien()])
        result = get_obligations(c, BIEN_ID)
        assert result["diagnostics"]["gaz"]["valid"] is False


class TestDiagnosticsPlomb:
    def test_plomb_valid_within_6_years(self):
        c = _make_client(biens=[_default_bien(diagnostic_plomb_date=VALID_6Y)])
        result = get_obligations(c, BIEN_ID)
        assert result["diagnostics"]["plomb"]["valid"] is True

    def test_plomb_invalid_older_than_6_years(self):
        c = _make_client(biens=[_default_bien(diagnostic_plomb_date=FAR_PAST_6Y)])
        result = get_obligations(c, BIEN_ID)
        assert result["diagnostics"]["plomb"]["valid"] is False

    def test_plomb_invalid_no_date(self):
        c = _make_client(biens=[_default_bien()])
        result = get_obligations(c, BIEN_ID)
        assert result["diagnostics"]["plomb"]["valid"] is False


# ── Tests: _parse_date ────────────────────────────────────────────────────────


class TestParseDate:
    def test_valid_date(self):
        d = _parse_date("2025-06-15")
        assert d == date(2025, 6, 15)

    def test_invalid_string_returns_none(self):
        assert _parse_date("not-a-date") is None

    def test_none_returns_none(self):
        assert _parse_date(None) is None

    def test_datetime_string_uses_first_10_chars(self):
        d = _parse_date("2025-06-15T12:00:00")
        assert d == date(2025, 6, 15)

    def test_empty_string_returns_none(self):
        assert _parse_date("") is None


# ── Tests: complete bien with all diagnostics ─────────────────────────────────


class TestCompleteObligations:
    def test_all_valid_scenario(self):
        """A bien with all obligations fulfilled returns all valid=True."""
        c = _make_client(
            biens=[_default_bien(
                dpe_classe="A",
                dpe_date=VALID_10Y,
                diagnostic_amiante_date=VALID_3Y,
                diagnostic_electricite_date=VALID_6Y,
                diagnostic_gaz_date=VALID_6Y,
                diagnostic_plomb_date=VALID_6Y,
            )],
            pno=[{"id": "pno-1", "id_bien": BIEN_ID, "date_echeance": FUTURE, "compagnie": "MACIF"}],
            baux=[_default_bail(depot_garantie=1200, etat_lieux_entree="2024-01-10")],
            bail_locataires=[{"id": "bl-1", "id_bail": BAIL_ID, "id_locataire": LOC_ID}],
        )
        result = get_obligations(c, BIEN_ID)

        assert result["pno"]["valid"] is True
        assert result["dpe"]["valid"] is True
        assert result["bail"]["valid"] is True
        assert result["locataire"]["valid"] is True
        assert result["depot_garantie"]["valid"] is True
        assert result["edl_entree"]["valid"] is True
        for diag_key in ("amiante", "electricite", "gaz", "plomb"):
            assert result["diagnostics"][diag_key]["valid"] is True, f"{diag_key} should be valid"

    def test_all_invalid_scenario(self):
        """A bien with no data returns all valid=False."""
        c = _make_client(
            biens=[{"id": BIEN_ID}],
            pno=[],
            baux=[],
            bail_locataires=[],
        )
        result = get_obligations(c, BIEN_ID)

        assert result["pno"]["valid"] is False
        assert result["dpe"]["valid"] is False
        assert result["bail"]["valid"] is False
        assert result["locataire"]["valid"] is False
        assert result["depot_garantie"]["valid"] is False
        assert result["edl_entree"]["valid"] is False
        for diag_key in ("amiante", "electricite", "gaz", "plomb"):
            assert result["diagnostics"][diag_key]["valid"] is False

    def test_result_has_all_expected_keys(self):
        c = _make_client()
        result = get_obligations(c, BIEN_ID)
        assert "pno" in result
        assert "dpe" in result
        assert "bail" in result
        assert "locataire" in result
        assert "depot_garantie" in result
        assert "edl_entree" in result
        assert "diagnostics" in result
        for diag_key in ("amiante", "electricite", "gaz", "plomb"):
            assert diag_key in result["diagnostics"]
