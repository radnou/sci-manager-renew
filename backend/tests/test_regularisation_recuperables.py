"""Tests CRITICAL-6 : charges récupérables et prorata d'occupation.

Vérifie que :
1. Seules les charges de copropriété (décret n° 87-713) entrent dans
   `charges_reelles` ; les autres alimentent `charges_non_recuperables`
   et `detail_exclusions`.
2. `_mois_occupation` calcule correctement le chevauchement entre la période
   du bail et l'année civile, pour les cinq cas typiques.
3. Le prorata d'occupation produit les bonnes provisions et `mois_occupation`.
"""

from __future__ import annotations

from datetime import date

import pytest

from tests.conftest import FakeSupabaseClient
from app.services.regularisation_service import (
    CHARGES_RECUPERABLES,
    _mois_occupation,
    calculate_regularisation,
)

# ── Constantes partagées ─────────────────────────────────────────────────────

BAIL_ID = "bail-recuperables-1"
BIEN_ID = "bien-recuperables-1"
ANNEE = 2025


def _make_client(baux=None, charges=None) -> FakeSupabaseClient:
    c = FakeSupabaseClient()
    c.store["baux"] = baux or []
    c.store["charges"] = charges or []
    c.store["regularisations_charges"] = []
    return c


def _bail(charges_locatives=100.0, date_debut=None, date_fin=None):
    return {
        "id": BAIL_ID,
        "id_bien": BIEN_ID,
        "charges_locatives": charges_locatives,
        "statut": "en_cours",
        "date_debut": date_debut or f"{ANNEE}-01-01",
        "date_fin": date_fin,
    }


# ── 1. Filtrage par type de charge ───────────────────────────────────────────


class TestChargesRecuperables:
    def test_seule_copropriete_compte_dans_charges_reelles(self):
        """Taxe foncière (1200) et travaux (800) sont exclus ; seule la copropriété
        (600) entre dans charges_reelles. charges_non_recuperables = 2000."""
        charges = [
            {
                "id": "c1",
                "id_bien": BIEN_ID,
                "montant": 600.0,
                "date_paiement": f"{ANNEE}-03-01",
                "type_charge": "copropriete",
            },
            {
                "id": "c2",
                "id_bien": BIEN_ID,
                "montant": 1200.0,
                "date_paiement": f"{ANNEE}-06-01",
                "type_charge": "taxe_fonciere",
            },
            {
                "id": "c3",
                "id_bien": BIEN_ID,
                "montant": 800.0,
                "date_paiement": f"{ANNEE}-09-01",
                "type_charge": "travaux_entretien",
            },
        ]
        c = _make_client(baux=[_bail()], charges=charges)
        result = calculate_regularisation(c, BAIL_ID, ANNEE)

        assert result["charges_reelles"] == 600.0
        assert result["charges_non_recuperables"] == 2000.0

    def test_detail_exclusions_contient_les_types_exclus(self):
        """detail_exclusions liste les types exclus agrégés par type, décroissant."""
        charges = [
            {
                "id": "c1",
                "id_bien": BIEN_ID,
                "montant": 600.0,
                "date_paiement": f"{ANNEE}-03-01",
                "type_charge": "copropriete",
            },
            {
                "id": "c2",
                "id_bien": BIEN_ID,
                "montant": 1200.0,
                "date_paiement": f"{ANNEE}-06-01",
                "type_charge": "taxe_fonciere",
            },
            {
                "id": "c3",
                "id_bien": BIEN_ID,
                "montant": 800.0,
                "date_paiement": f"{ANNEE}-09-01",
                "type_charge": "travaux_entretien",
            },
        ]
        c = _make_client(baux=[_bail()], charges=charges)
        result = calculate_regularisation(c, BAIL_ID, ANNEE)

        exclusions = result["detail_exclusions"]
        assert len(exclusions) == 2
        # Trié par montant décroissant
        assert exclusions[0]["type_charge"] == "taxe_fonciere"
        assert exclusions[0]["montant"] == 1200.0
        assert exclusions[1]["type_charge"] == "travaux_entretien"
        assert exclusions[1]["montant"] == 800.0

    def test_aucune_charge_recuperable_donne_zero(self):
        """Si seules des charges non récupérables existent, charges_reelles = 0."""
        charges = [
            {
                "id": "c1",
                "id_bien": BIEN_ID,
                "montant": 500.0,
                "date_paiement": f"{ANNEE}-01-15",
                "type_charge": "taxe_fonciere",
            },
            {
                "id": "c2",
                "id_bien": BIEN_ID,
                "montant": 300.0,
                "date_paiement": f"{ANNEE}-04-01",
                "type_charge": "assurance_pno",
            },
        ]
        c = _make_client(baux=[_bail()], charges=charges)
        result = calculate_regularisation(c, BAIL_ID, ANNEE)

        assert result["charges_reelles"] == 0.0
        assert result["charges_non_recuperables"] == 800.0
        assert result["sens"] == "trop_percu"  # provisions > 0, charges_reelles = 0

    def test_charges_sans_type_charge_sont_exclues(self):
        """Une charge sans type_charge (type indéterminé) est classée non récupérable."""
        charges = [
            {
                "id": "c1",
                "id_bien": BIEN_ID,
                "montant": 400.0,
                "date_paiement": f"{ANNEE}-02-01",
            },
        ]
        c = _make_client(baux=[_bail()], charges=charges)
        result = calculate_regularisation(c, BAIL_ID, ANNEE)

        assert result["charges_reelles"] == 0.0
        assert result["charges_non_recuperables"] == 400.0

    def test_charges_recuperables_est_un_frozenset(self):
        """La constante CHARGES_RECUPERABLES doit être un frozenset immuable."""
        assert isinstance(CHARGES_RECUPERABLES, frozenset)
        assert "copropriete" in CHARGES_RECUPERABLES


# ── 2. _mois_occupation — cinq cas paramétrés ───────────────────────────────


@pytest.mark.parametrize(
    "date_debut,date_fin,annee,expected",
    [
        # Cas 1 : bail commencé avant l'année, date_fin nulle → 12 mois pleins
        ("2024-06-01", None, 2025, 12),
        # Cas 2 : bail commencé mi-année, se terminant après l'année (chaînes ISO)
        ("2025-07-01", "2026-03-01", 2025, 6),
        # Cas 3 : bail entièrement hors de l'année (futur) → 0
        ("2026-01-01", None, 2025, 0),
        # Cas 4 : date_debut nulle → 0 (impossibilité de déterminer l'occupation)
        (None, None, 2025, 0),
        # Cas 5 : dates passées comme objets date (pas des chaînes ISO)
        (date(2024, 1, 1), date(2025, 8, 20), 2025, 8),
    ],
    ids=[
        "bail_avant_annee_sans_fin",
        "bail_termine_apres_annee",
        "bail_entierement_hors_annee",
        "date_debut_nulle",
        "dates_comme_objets_date",
    ],
)
def test_mois_occupation(date_debut, date_fin, annee, expected):
    assert _mois_occupation(date_debut, date_fin, annee) == expected


def test_mois_occupation_bail_termine_avant_annee():
    """Bail terminé le 31/12 de l'année précédente → 0 mois."""
    assert _mois_occupation("2024-01-01", "2024-12-31", 2025) == 0


# ── 3. Prorata d'occupation sur les provisions ───────────────────────────────


class TestProrataOccupation:
    def test_bail_6_mois_provisions_proratas(self):
        """Un bail de juillet à décembre (6 mois) avec charges_locatives=100
        doit produire provisions=600 et mois_occupation=6."""
        charges = [
            {
                "id": "c1",
                "id_bien": BIEN_ID,
                "montant": 200.0,
                "date_paiement": f"{ANNEE}-09-01",
                "type_charge": "copropriete",
            },
        ]
        c = _make_client(
            baux=[_bail(charges_locatives=100.0, date_debut=f"{ANNEE}-07-01")],
            charges=charges,
        )
        result = calculate_regularisation(c, BAIL_ID, ANNEE)

        assert result["mois_occupation"] == 6
        assert result["provisions_annuelles"] == 600.0

    def test_bail_pleine_annee_12_mois(self):
        """Un bail qui couvre toute l'année produit mois_occupation=12."""
        c = _make_client(
            baux=[_bail(charges_locatives=50.0, date_debut=f"{ANNEE}-01-01")],
            charges=[],
        )
        result = calculate_regularisation(c, BAIL_ID, ANNEE)

        assert result["mois_occupation"] == 12
        assert result["provisions_annuelles"] == 600.0

    def test_bail_hors_annee_provisions_zero(self):
        """Un bail qui n'a pas encore commencé donne provisions=0."""
        c = _make_client(
            baux=[_bail(charges_locatives=200.0, date_debut=f"{ANNEE + 1}-01-01")],
            charges=[],
        )
        result = calculate_regularisation(c, BAIL_ID, ANNEE)

        assert result["mois_occupation"] == 0
        assert result["provisions_annuelles"] == 0.0
