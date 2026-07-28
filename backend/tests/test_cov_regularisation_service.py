"""Tests for app/services/regularisation_service.py.

Covers:
- calculate_regularisation: bail not found, trop_percu, complement_du, equilibre
- _get_saved_regularisation: row found, none found
- confirm_regularisation: insert path, update path, error path

Fixtures mis à jour (CRITICAL-6) : les charges portent désormais
`type_charge="copropriete"` (seule catégorie récupérable selon le décret n° 87-713),
et les baux portent `date_debut` / `date_fin` pour le prorata d'occupation.
Les anciens tests conservent leurs assertions numériques car le bail couvre
l'année complète (12 mois), ce qui maintient `provisions = charges_locatives * 12`.
"""

from __future__ import annotations

from copy import deepcopy

import pytest

from tests.conftest import FakeSupabaseClient
from app.services.regularisation_service import (
    calculate_regularisation,
    confirm_regularisation,
    _get_saved_regularisation,
)


# ── Helpers ─────────────────────────────────────────────────────────────────

BAIL_ID = "bail-1"
BIEN_ID = "bien-1"
ANNEE = 2025


def _make_client(
    baux=None,
    charges=None,
    regularisations=None,
) -> FakeSupabaseClient:
    c = FakeSupabaseClient()
    if baux is not None:
        c.store["baux"] = baux
    if charges is not None:
        c.store["charges"] = charges
    else:
        c.store["charges"] = []
    c.store["regularisations_charges"] = regularisations or []
    return c


def _default_bail(
    bail_id=BAIL_ID,
    bien_id=BIEN_ID,
    charges_locatives=200.0,
    date_debut=None,
    date_fin=None,
):
    # date_debut par défaut au 1er janvier de l'année de test → prorata = 12 mois,
    # ce qui préserve les assertions numériques existantes (provisions = CL * 12).
    return {
        "id": bail_id,
        "id_bien": bien_id,
        "charges_locatives": charges_locatives,
        "statut": "en_cours",
        "date_debut": date_debut or f"{ANNEE}-01-01",
        "date_fin": date_fin,
    }


# ── Tests: calculate_regularisation ─────────────────────────────────────────


class TestCalculateRegularisationBailNotFound:
    def test_raises_value_error_when_bail_missing(self):
        c = _make_client(baux=[])
        with pytest.raises(ValueError, match="not found"):
            calculate_regularisation(c, "nonexistent-bail", ANNEE)


class TestCalculateRegularisationTropPercu:
    def test_provisions_exceed_real_charges(self):
        """provisions = 200*12 = 2400, charges_reelles = 1000 → solde = 1400 (trop_percu)."""
        c = _make_client(
            baux=[_default_bail(charges_locatives=200.0)],
            charges=[
                {
                    "id": "c1",
                    "id_bien": BIEN_ID,
                    "montant": 500.0,
                    "date_paiement": f"{ANNEE}-03-15",
                    "type_charge": "copropriete",
                },
                {
                    "id": "c2",
                    "id_bien": BIEN_ID,
                    "montant": 500.0,
                    "date_paiement": f"{ANNEE}-09-01",
                    "type_charge": "copropriete",
                },
            ],
        )
        result = calculate_regularisation(c, BAIL_ID, ANNEE)

        assert result["provisions_annuelles"] == 2400.0
        assert result["charges_reelles"] == 1000.0
        assert result["solde"] == 1400.0
        assert result["sens"] == "trop_percu"
        assert result["bail_id"] == BAIL_ID
        assert result["bien_id"] == BIEN_ID
        assert result["annee"] == ANNEE

    def test_returns_saved_none_when_no_regularisation_exists(self):
        c = _make_client(
            baux=[_default_bail(charges_locatives=100.0)],
            charges=[],
        )
        result = calculate_regularisation(c, BAIL_ID, ANNEE)
        assert result["saved"] is None


class TestCalculateRegularisationComplementDu:
    def test_real_charges_exceed_provisions(self):
        """provisions = 100*12 = 1200, charges = 2000 → solde = -800 (complement_du)."""
        c = _make_client(
            baux=[_default_bail(charges_locatives=100.0)],
            charges=[
                {
                    "id": "c1",
                    "id_bien": BIEN_ID,
                    "montant": 2000.0,
                    "date_paiement": f"{ANNEE}-06-01",
                    "type_charge": "copropriete",
                },
            ],
        )
        result = calculate_regularisation(c, BAIL_ID, ANNEE)
        assert result["solde"] == -800.0
        assert result["sens"] == "complement_du"


class TestCalculateRegularisationEquilibre:
    def test_provisions_equal_charges(self):
        """provisions = 100*12 = 1200, charges = 1200 → solde = 0 (equilibre)."""
        c = _make_client(
            baux=[_default_bail(charges_locatives=100.0)],
            charges=[
                {
                    "id": "c1",
                    "id_bien": BIEN_ID,
                    "montant": 1200.0,
                    "date_paiement": f"{ANNEE}-01-01",
                    "type_charge": "copropriete",
                },
            ],
        )
        result = calculate_regularisation(c, BAIL_ID, ANNEE)
        assert result["solde"] == 0.0
        assert result["sens"] == "equilibre"


class TestCalculateRegularisationNoCharges:
    def test_zero_charges_reelles(self):
        """No charges recorded → charges_reelles=0, solde=provisions, trop_percu."""
        c = _make_client(
            baux=[_default_bail(charges_locatives=150.0)],
            charges=[],
        )
        result = calculate_regularisation(c, BAIL_ID, ANNEE)
        assert result["charges_reelles"] == 0.0
        assert result["provisions_annuelles"] == 1800.0
        assert result["solde"] == 1800.0
        assert result["sens"] == "trop_percu"


class TestCalculateRegularisationNullChargesLocatives:
    def test_none_charges_locatives_treated_as_zero(self):
        """charges_locatives=None → provisions=0, charges_reelles=real → complement_du."""
        c = _make_client(
            baux=[_default_bail(charges_locatives=None)],
            charges=[
                {
                    "id": "c1",
                    "id_bien": BIEN_ID,
                    "montant": 500.0,
                    "date_paiement": f"{ANNEE}-05-01",
                    "type_charge": "copropriete",
                },
            ],
        )
        result = calculate_regularisation(c, BAIL_ID, ANNEE)
        assert result["provisions_annuelles"] == 0.0
        assert result["charges_reelles"] == 500.0
        assert result["solde"] == -500.0
        assert result["sens"] == "complement_du"


class TestCalculateRegularisationChargesOutOfYear:
    def test_charges_outside_year_are_excluded(self):
        """Charges from a different year must not count."""
        c = _make_client(
            baux=[_default_bail(charges_locatives=100.0)],
            charges=[
                # In year → should count
                {
                    "id": "c1",
                    "id_bien": BIEN_ID,
                    "montant": 600.0,
                    "date_paiement": f"{ANNEE}-06-01",
                    "type_charge": "copropriete",
                },
                # Out of year → should NOT count
                {
                    "id": "c2",
                    "id_bien": BIEN_ID,
                    "montant": 9999.0,
                    "date_paiement": f"{ANNEE + 1}-01-01",
                    "type_charge": "copropriete",
                },
                {
                    "id": "c3",
                    "id_bien": BIEN_ID,
                    "montant": 9999.0,
                    "date_paiement": f"{ANNEE - 1}-12-31",
                    "type_charge": "copropriete",
                },
            ],
        )
        result = calculate_regularisation(c, BAIL_ID, ANNEE)
        assert result["charges_reelles"] == 600.0


class TestCalculateRegularisationSavedExists:
    def test_saved_is_returned_when_regularisation_exists(self):
        saved_row = {
            "id": "reg-1",
            "id_bien": BIEN_ID,
            "id_bail": BAIL_ID,
            "annee": ANNEE,
            "statut": "confirme",
        }
        c = _make_client(
            baux=[_default_bail()],
            charges=[],
            regularisations=[saved_row],
        )
        result = calculate_regularisation(c, BAIL_ID, ANNEE)
        assert result["saved"] is not None
        assert result["saved"]["id"] == "reg-1"


class TestCalculateRegularisationMultipleBiens:
    def test_only_charges_for_the_bail_bien_are_summed(self):
        """Charges for a different bien must not be included."""
        OTHER_BIEN = "bien-other"
        c = _make_client(
            baux=[_default_bail(charges_locatives=100.0)],
            charges=[
                {
                    "id": "c1",
                    "id_bien": BIEN_ID,
                    "montant": 300.0,
                    "date_paiement": f"{ANNEE}-03-01",
                    "type_charge": "copropriete",
                },
                {
                    "id": "c2",
                    "id_bien": OTHER_BIEN,
                    "montant": 9999.0,
                    "date_paiement": f"{ANNEE}-04-01",
                    "type_charge": "copropriete",
                },
            ],
        )
        result = calculate_regularisation(c, BAIL_ID, ANNEE)
        assert result["charges_reelles"] == 300.0


# ── Tests: _get_saved_regularisation ────────────────────────────────────────


class TestGetSavedRegularisation:
    def test_returns_none_when_no_matching_row(self):
        c = _make_client(regularisations=[])
        saved = _get_saved_regularisation(c, BIEN_ID, BAIL_ID, ANNEE)
        assert saved is None

    def test_returns_row_when_found(self):
        row = {
            "id": "reg-99",
            "id_bien": BIEN_ID,
            "id_bail": BAIL_ID,
            "annee": ANNEE,
            "statut": "confirme",
        }
        c = _make_client(regularisations=[row])
        saved = _get_saved_regularisation(c, BIEN_ID, BAIL_ID, ANNEE)
        assert saved is not None
        assert saved["id"] == "reg-99"

    def test_does_not_return_row_for_different_annee(self):
        row = {
            "id": "reg-X",
            "id_bien": BIEN_ID,
            "id_bail": BAIL_ID,
            "annee": ANNEE - 1,
            "statut": "confirme",
        }
        c = _make_client(regularisations=[row])
        saved = _get_saved_regularisation(c, BIEN_ID, BAIL_ID, ANNEE)
        assert saved is None


# ── Tests: confirm_regularisation ───────────────────────────────────────────


class TestConfirmRegularisationInsert:
    def test_creates_new_row_when_none_exists(self):
        """confirm_regularisation should insert a new row and return it."""
        c = _make_client(
            baux=[_default_bail(charges_locatives=100.0)],
            charges=[
                {
                    "id": "c1",
                    "id_bien": BIEN_ID,
                    "montant": 600.0,
                    "date_paiement": f"{ANNEE}-06-01",
                    "type_charge": "copropriete",
                },
            ],
            regularisations=[],
        )
        saved = confirm_regularisation(c, BIEN_ID, BAIL_ID, ANNEE)
        assert saved is not None
        assert saved["statut"] == "confirme"
        assert saved["annee"] == ANNEE
        assert saved["id_bien"] == BIEN_ID
        assert saved["id_bail"] == BAIL_ID

    def test_insert_includes_solde_and_sens(self):
        c = _make_client(
            baux=[_default_bail(charges_locatives=200.0)],
            charges=[],  # no charges → trop_percu
            regularisations=[],
        )
        saved = confirm_regularisation(c, BIEN_ID, BAIL_ID, ANNEE)
        assert saved["solde"] == 2400.0
        assert saved["sens"] == "trop_percu"

    def test_insert_with_notes(self):
        c = _make_client(
            baux=[_default_bail(charges_locatives=100.0)],
            charges=[],
            regularisations=[],
        )
        saved = confirm_regularisation(c, BIEN_ID, BAIL_ID, ANNEE, notes="Custom note")
        assert saved["notes"] == "Custom note"


class TestConfirmRegularisationUpdate:
    def test_updates_existing_row_instead_of_inserting(self):
        """When a regularisation already exists, it should be updated (not duplicated)."""
        existing_row = {
            "id": "reg-existing",
            "id_bien": BIEN_ID,
            "id_bail": BAIL_ID,
            "annee": ANNEE,
            "statut": "confirme",
            "solde": 0.0,
        }
        c = _make_client(
            baux=[_default_bail(charges_locatives=200.0)],
            charges=[],
            regularisations=[existing_row],
        )
        saved = confirm_regularisation(c, BIEN_ID, BAIL_ID, ANNEE)
        # Should not create a duplicate — store still has one row
        regs = c.store["regularisations_charges"]
        assert len(regs) == 1
        # The row should now reflect updated values
        assert saved is not None


class TestConfirmRegularisationComplementDu:
    def test_complement_du_scenario(self):
        """When charges > provisions, confirm should record complement_du."""
        c = _make_client(
            baux=[_default_bail(charges_locatives=50.0)],  # provisions = 600
            charges=[
                {
                    "id": "c1",
                    "id_bien": BIEN_ID,
                    "montant": 1000.0,
                    "date_paiement": f"{ANNEE}-07-01",
                    "type_charge": "copropriete",
                },
            ],
            regularisations=[],
        )
        saved = confirm_regularisation(c, BIEN_ID, BAIL_ID, ANNEE)
        assert saved["sens"] == "complement_du"
        assert saved["solde"] == -400.0
