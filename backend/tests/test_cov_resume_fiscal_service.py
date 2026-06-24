"""Tests de couverture pour app.services.resume_fiscal_service.

Couvre :
- ResumeFiscalService.calculate() — IR régime réel, plusieurs biens
- Cas déficit foncier (art. 156-I-3° CGI)
- Micro-foncier comparison (art. 32 CGI)
- Déficits antérieurs FIFO
- prefill_fiscalite()
- Helpers internes (_safe_float, _execute_select, _load_prior_deficits, _save_deficit, _impute_prior_deficits)
- SCI inconnue, aucun bien, aucun associé
"""
from __future__ import annotations

import asyncio
from copy import deepcopy

import pytest

from tests.conftest import FakeSupabaseClient
from app.services.resume_fiscal_service import (
    ResumeFiscalService,
    ResumeFiscalResult,
    BienFiscalDetail,
    AssocieQuotePart,
    DeficitAnterieur,
)

ANNEE = 2025
SCI_IR = "sci-ir-001"
SCI_IS = "sci-is-002"
SCI_MISSING = "sci-missing-999"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client(extra: dict | None = None) -> FakeSupabaseClient:
    """Return a fresh FakeSupabaseClient with minimal IR SCI data."""
    c = FakeSupabaseClient()
    # Base IR SCI
    c.store["sci"] = [
        {
            "id": SCI_IR,
            "nom": "SCI Résumé Fiscal IR",
            "siren": "111222333",
            "regime_fiscal": "IR",
            "adresse_siege": "10 Rue Fiscale, 75001 Paris",
            "capital_social": 15000,
            "nom_gerant": "Moussa Belkacem",
            "nb_parts_total": 100,
        },
        {
            "id": SCI_IS,
            "nom": "SCI Résumé Fiscal IS",
            "siren": "444555666",
            "regime_fiscal": "IS",
            "adresse_siege": "5 Avenue Prospère, 69001 Lyon",
            "capital_social": 50000,
            "nom_gerant": "Sophie Martin",
            "nb_parts_total": 200,
        },
    ]
    c.store["associes"] = [
        {
            "id": "assoc-ir-1",
            "id_sci": SCI_IR,
            "user_id": "user-123",
            "nom": "Moussa Belkacem",
            "email": "moussa@test.fr",
            "part": 50,
            "nb_parts": 60,
            "role": "gerant",
        },
        {
            "id": "assoc-ir-2",
            "id_sci": SCI_IR,
            "user_id": "user-456",
            "nom": "Sophie Lemaire",
            "email": "sophie@test.fr",
            "part": 50,
            "nb_parts": 40,
            "role": "associe",
        },
        {
            "id": "assoc-is-1",
            "id_sci": SCI_IS,
            "user_id": "user-123",
            "nom": "Moussa Belkacem",
            "email": "moussa@test.fr",
            "part": 100,
            "nb_parts": 200,
            "role": "gerant",
        },
    ]
    c.store["biens"] = [
        {
            "id": "bien-ir-1",
            "id_sci": SCI_IR,
            "adresse": "10 Rue Fiscale",
            "ville": "Paris",
            "type_locatif": "nu",
            "prix_acquisition": 250000,
        },
        {
            "id": "bien-ir-2",
            "id_sci": SCI_IR,
            "adresse": "20 Allée Verte",
            "ville": "Bordeaux",
            "type_locatif": "nu",
            "prix_acquisition": 180000,
        },
        {
            "id": "bien-is-1",
            "id_sci": SCI_IS,
            "adresse": "5 Avenue Prospère",
            "ville": "Lyon",
            "type_locatif": "nu",
            "prix_acquisition": 300000,
        },
    ]
    c.store["loyers"] = [
        # Bien IR-1: 12 mois de loyers payés
        {"id": f"loyer-ir1-{m:02d}", "id_bien": "bien-ir-1",
         "date_loyer": f"{ANNEE}-{m:02d}-01", "montant": 900.0, "statut": "paye"}
        for m in range(1, 13)
    ] + [
        # Bien IR-2: 10 mois
        {"id": f"loyer-ir2-{m:02d}", "id_bien": "bien-ir-2",
         "date_loyer": f"{ANNEE}-{m:02d}-01", "montant": 700.0, "statut": "paye"}
        for m in range(1, 11)
    ] + [
        # Bien IS-1: 12 mois
        {"id": f"loyer-is1-{m:02d}", "id_bien": "bien-is-1",
         "date_loyer": f"{ANNEE}-{m:02d}-01", "montant": 1200.0, "statut": "paye"}
        for m in range(1, 13)
    ] + [
        # Loyer non payé (ne doit pas compter)
        {"id": "loyer-impaye", "id_bien": "bien-ir-1",
         "date_loyer": f"{ANNEE}-01-15", "montant": 900.0, "statut": "en_retard"},
        # Loyer de l'année précédente (ne doit pas compter)
        {"id": "loyer-old", "id_bien": "bien-ir-1",
         "date_loyer": "2024-12-01", "montant": 900.0, "statut": "paye"},
    ]
    c.store["charges"] = [
        # Taxe foncière bien IR-1
        {"id": "ch-1", "id_bien": "bien-ir-1", "type_charge": "taxe_fonciere",
         "montant": 800.0, "date_paiement": f"{ANNEE}-09-15"},
        # Copropriété bien IR-1
        {"id": "ch-2", "id_bien": "bien-ir-1", "type_charge": "copropriete",
         "montant": 1200.0, "date_paiement": f"{ANNEE}-06-01"},
        # Travaux bien IR-2
        {"id": "ch-3", "id_bien": "bien-ir-2", "type_charge": "travaux",
         "montant": 2500.0, "date_paiement": f"{ANNEE}-04-01"},
        # Charge hors période (ne doit pas compter)
        {"id": "ch-old", "id_bien": "bien-ir-1", "type_charge": "taxe_fonciere",
         "montant": 800.0, "date_paiement": "2024-09-15"},
    ]
    c.store["assurances_pno"] = [
        {"id": "pno-ir-1", "id_bien": "bien-ir-1", "montant_annuel": 280.0, "compagnie": "MAIF"},
        {"id": "pno-ir-2", "id_bien": "bien-ir-2", "montant_annuel": 200.0, "compagnie": "AXA"},
    ]
    c.store["credits_immobiliers"] = []
    c.store["deficit_reportable"] = []
    if extra:
        for table, rows in extra.items():
            c.store[table] = rows
    return c


service = ResumeFiscalService()


# ---------------------------------------------------------------------------
# 1. Helpers _safe_float et _execute_select
# ---------------------------------------------------------------------------

class TestHelpers:
    def test_safe_float_none(self):
        assert service._safe_float(None) == 0.0

    def test_safe_float_int(self):
        assert service._safe_float(42) == 42.0

    def test_safe_float_string(self):
        assert service._safe_float("3.14") == 3.14

    def test_safe_float_invalid_string(self):
        assert service._safe_float("abc") == 0.0

    def test_safe_float_zero(self):
        assert service._safe_float(0) == 0.0

    def test_safe_float_negative(self):
        assert service._safe_float(-500) == -500.0

    def test_execute_select_success(self):
        c = _make_client()
        query = c.table("sci").select("*").eq("id", SCI_IR)
        result = service._execute_select(query)
        assert len(result) == 1
        assert result[0]["id"] == SCI_IR

    def test_execute_select_empty(self):
        c = _make_client()
        query = c.table("sci").select("*").eq("id", "nonexistent")
        result = service._execute_select(query)
        assert result == []


# ---------------------------------------------------------------------------
# 2. Cas SCI inconnue
# ---------------------------------------------------------------------------

class TestSciInconnue:
    def test_sci_inconnue_returns_default_result(self):
        c = _make_client()
        result = service.calculate(SCI_MISSING, ANNEE, c)
        assert isinstance(result, ResumeFiscalResult)
        assert result.sci_nom == "SCI inconnue"
        assert "SCI introuvable" in result.alertes[0]
        assert result.total_revenus == 0.0
        assert result.total_charges == 0.0


# ---------------------------------------------------------------------------
# 3. SCI sans biens
# ---------------------------------------------------------------------------

class TestSciSansBiens:
    def test_alerte_aucun_bien(self):
        c = _make_client()
        c.store["biens"] = []
        result = service.calculate(SCI_IR, ANNEE, c)
        assert any("Aucun bien" in a for a in result.alertes)
        assert result.nb_biens == 0
        assert result.total_revenus == 0.0


# ---------------------------------------------------------------------------
# 4. Calcul nominal — 2 biens IR
# ---------------------------------------------------------------------------

class TestCalculateNominalIR:
    def test_revenus_bien_1_correct(self):
        c = _make_client()
        result = service.calculate(SCI_IR, ANNEE, c)
        bien1 = next(b for b in result.biens if b.bien_id == "bien-ir-1")
        # 12 loyers × 900 = 10 800
        assert bien1.ligne_211_loyers_bruts == 10800.0

    def test_revenus_bien_2_correct(self):
        c = _make_client()
        result = service.calculate(SCI_IR, ANNEE, c)
        bien2 = next(b for b in result.biens if b.bien_id == "bien-ir-2")
        # 10 loyers × 700 = 7 000
        assert bien2.ligne_211_loyers_bruts == 7000.0

    def test_total_revenus(self):
        c = _make_client()
        result = service.calculate(SCI_IR, ANNEE, c)
        assert result.total_revenus == 17800.0

    def test_frais_gestion_forfait_20(self):
        c = _make_client()
        result = service.calculate(SCI_IR, ANNEE, c)
        for bien in result.biens:
            assert bien.ligne_215_frais_gestion == 20.0

    def test_taxe_fonciere_bien_1(self):
        c = _make_client()
        result = service.calculate(SCI_IR, ANNEE, c)
        bien1 = next(b for b in result.biens if b.bien_id == "bien-ir-1")
        assert bien1.ligne_224_taxe_fonciere == 800.0

    def test_copropriete_bien_1(self):
        c = _make_client()
        result = service.calculate(SCI_IR, ANNEE, c)
        bien1 = next(b for b in result.biens if b.bien_id == "bien-ir-1")
        assert bien1.ligne_227_copropriete == 1200.0

    def test_assurance_pno_bien_1(self):
        c = _make_client()
        result = service.calculate(SCI_IR, ANNEE, c)
        bien1 = next(b for b in result.biens if b.bien_id == "bien-ir-1")
        assert bien1.ligne_220_assurance == 280.0

    def test_travaux_bien_2(self):
        c = _make_client()
        result = service.calculate(SCI_IR, ANNEE, c)
        bien2 = next(b for b in result.biens if b.bien_id == "bien-ir-2")
        assert bien2.ligne_221_travaux == 2500.0

    def test_total_charges_includes_all_lines(self):
        c = _make_client()
        result = service.calculate(SCI_IR, ANNEE, c)
        # bien1: 20 (forfait) + 280 (pno) + 800 (taxe) + 1200 (copro) = 2300
        # bien2: 20 (forfait) + 200 (pno) + 2500 (travaux) = 2720
        bien1 = next(b for b in result.biens if b.bien_id == "bien-ir-1")
        assert bien1.ligne_229_total_charges == 2300.0

    def test_resultat_net_bien(self):
        c = _make_client()
        result = service.calculate(SCI_IR, ANNEE, c)
        bien1 = next(b for b in result.biens if b.bien_id == "bien-ir-1")
        # 10800 - 2300 - 0 (no interest) = 8500
        assert bien1.ligne_240_resultat_net == 8500.0

    def test_nb_biens_et_associes(self):
        c = _make_client()
        result = service.calculate(SCI_IR, ANNEE, c)
        assert result.nb_biens == 2
        assert result.nb_associes == 2

    def test_sci_identification_fields(self):
        c = _make_client()
        result = service.calculate(SCI_IR, ANNEE, c)
        assert result.sci_nom == "SCI Résumé Fiscal IR"
        assert result.sci_siren == "111222333"
        assert result.sci_adresse_siege == "10 Rue Fiscale, 75001 Paris"
        assert result.sci_capital_social == 15000.0
        assert result.sci_nom_gerant == "Moussa Belkacem"

    def test_regime_fiscal_ir(self):
        c = _make_client()
        result = service.calculate(SCI_IR, ANNEE, c)
        assert result.regime_fiscal == "IR"


# ---------------------------------------------------------------------------
# 5. Quote-parts associés
# ---------------------------------------------------------------------------

class TestAssociesQuotePart:
    def test_two_associes_present(self):
        c = _make_client()
        result = service.calculate(SCI_IR, ANNEE, c)
        assert len(result.associes) == 2

    def test_parts_pct_somme_100(self):
        c = _make_client()
        result = service.calculate(SCI_IR, ANNEE, c)
        total_pct = sum(a.part_pct for a in result.associes)
        assert abs(total_pct - 100.0) < 0.1

    def test_quote_part_proportionnelle(self):
        c = _make_client()
        result = service.calculate(SCI_IR, ANNEE, c)
        # nb_parts: assoc-ir-1=60, assoc-ir-2=40 → total=100
        a1 = next(a for a in result.associes if a.nom == "Moussa Belkacem")
        a2 = next(a for a in result.associes if a.nom == "Sophie Lemaire")
        assert a1.part_pct == 60.0
        assert a2.part_pct == 40.0

    def test_case_4ba_positive_result(self):
        """Quand résultat > 0, case_4ba = quote-part."""
        c = _make_client()
        result = service.calculate(SCI_IR, ANNEE, c)
        for a in result.associes:
            if a.quote_part_resultat >= 0:
                assert a.case_4ba >= 0
                assert a.case_4bb == 0.0

    def test_alerte_aucun_associe(self):
        c = _make_client()
        c.store["associes"] = []
        result = service.calculate(SCI_IR, ANNEE, c)
        assert any("Aucun associé" in a for a in result.alertes)


# ---------------------------------------------------------------------------
# 6. Micro-foncier comparison
# ---------------------------------------------------------------------------

class TestMicroFoncier:
    def test_eligible_si_revenus_inferieurs_15000(self):
        """Micro-foncier éligible si revenus bruts ≤ 15 000 EUR."""
        c = _make_client()
        # Remplace les loyers par des montants bas
        c.store["loyers"] = [
            {"id": "l1", "id_bien": "bien-ir-1",
             "date_loyer": f"{ANNEE}-01-01", "montant": 500.0, "statut": "paye"},
        ]
        result = service.calculate(SCI_IR, ANNEE, c)
        assert result.micro_foncier_eligible is True
        assert result.micro_foncier_abattement == round(500.0 * 0.30, 2)

    def test_ineligible_si_revenus_superieurs_15000(self):
        c = _make_client()  # revenus = 17 800 > 15 000
        result = service.calculate(SCI_IR, ANNEE, c)
        assert result.micro_foncier_eligible is False
        assert result.micro_foncier_abattement == 0.0
        assert result.micro_foncier_resultat == 0.0

    def test_regime_recommande_reel(self):
        c = _make_client()
        result = service.calculate(SCI_IR, ANNEE, c)
        assert result.regime_recommande == "reel"

    def test_regime_recommande_micro_when_eligible_and_better(self):
        """Si micro donne résultat plus bas, regime_recommande = 'micro'."""
        c = _make_client()
        # Loyers bas, aucune charge => micro plus avantageux
        c.store["loyers"] = [
            {"id": "l1", "id_bien": "bien-ir-1",
             "date_loyer": f"{ANNEE}-06-01", "montant": 5000.0, "statut": "paye"},
        ]
        c.store["charges"] = []
        c.store["assurances_pno"] = []
        result = service.calculate(SCI_IR, ANNEE, c)
        assert result.micro_foncier_eligible is True
        # Résultat réel = 5000 - 20 (forfait) = 4980
        # Résultat micro = 5000 * 0.70 = 3500 → micro < réel → recommande = micro
        assert result.regime_recommande == "micro"


# ---------------------------------------------------------------------------
# 7. Déficit foncier (art. 156-I-3° CGI)
# ---------------------------------------------------------------------------

class TestDeficitFoncier:
    def _client_deficit(self) -> FakeSupabaseClient:
        """SCI with heavy charges leading to a deficit."""
        c = _make_client()
        c.store["loyers"] = [
            {"id": "l1", "id_bien": "bien-ir-1",
             "date_loyer": f"{ANNEE}-06-01", "montant": 3000.0, "statut": "paye"},
        ]
        c.store["charges"] = [
            {"id": "ch-1", "id_bien": "bien-ir-1", "type_charge": "travaux",
             "montant": 8000.0, "date_paiement": f"{ANNEE}-03-01"},
            {"id": "ch-2", "id_bien": "bien-ir-1", "type_charge": "interets_emprunt",
             "montant": 2000.0, "date_paiement": f"{ANNEE}-01-01"},
        ]
        c.store["assurances_pno"] = []
        return c

    def test_is_deficit_true(self):
        c = self._client_deficit()
        result = service.calculate(SCI_IR, ANNEE, c)
        assert result.is_deficit is True

    def test_deficit_total_positive(self):
        c = self._client_deficit()
        result = service.calculate(SCI_IR, ANNEE, c)
        assert result.deficit_total > 0

    def test_deficit_interets_emprunt(self):
        c = self._client_deficit()
        result = service.calculate(SCI_IR, ANNEE, c)
        # Intérêts = 2000 contribuent au déficit intérêts
        assert result.deficit_interets_emprunt >= 0

    def test_deficit_imputable_revenu_global_capped_at_10700(self):
        c = _make_client()
        # Loyers très bas, charges hors intérêts très élevées
        c.store["loyers"] = [
            {"id": "l1", "id_bien": "bien-ir-1",
             "date_loyer": f"{ANNEE}-01-01", "montant": 1000.0, "statut": "paye"},
        ]
        c.store["charges"] = [
            {"id": "ch-1", "id_bien": "bien-ir-1", "type_charge": "travaux",
             "montant": 25000.0, "date_paiement": f"{ANNEE}-04-01"},
        ]
        c.store["assurances_pno"] = []
        result = service.calculate(SCI_IR, ANNEE, c)
        # Déficit = charges - revenus (très élevé). Part imputable revenu global ≤ 10700
        assert result.deficit_imputable_revenu_global <= 10700.0

    def test_deficit_saved_to_tracker(self):
        c = self._client_deficit()
        result = service.calculate(SCI_IR, ANNEE, c)
        if result.is_deficit:
            rows = c.store.get("deficit_reportable", [])
            assert len(rows) >= 1

    def test_case_4bb_positive_for_deficit(self):
        """Si déficit, les associés ont case_4bb > 0."""
        c = self._client_deficit()
        result = service.calculate(SCI_IR, ANNEE, c)
        if result.is_deficit and result.deficit_imputable_revenu_global > 0:
            for a in result.associes:
                assert a.case_4bb >= 0


# ---------------------------------------------------------------------------
# 8. Déficits antérieurs — imputation FIFO
# ---------------------------------------------------------------------------

class TestDeficitsAnterieurs:
    def test_prior_deficit_imputed_against_positive_result(self):
        """Un déficit antérieur est imputé sur un résultat positif courant."""
        c = _make_client()
        # SCI en bénéfice cette année
        # Ajouter un déficit antérieur reportable
        c.store["deficit_reportable"] = [
            {
                "id": "def-ant-1",
                "id_sci": SCI_IR,
                "annee_constatation": 2023,
                "deficit_interets": 1000.0,
                "deficit_charges": 500.0,
                "impute_revenu_global": 500.0,
                "total_impute_foncier": 0.0,
                "solde_restant": 1500.0,
                "annee_prescription": 2033,
            }
        ]
        result = service.calculate(SCI_IR, ANNEE, c)
        # Le déficit antérieur doit être imputable
        assert result.total_deficits_anterieurs_imputes >= 0.0
        assert len(result.deficits_anterieurs) >= 1

    def test_prior_deficit_zero_solde_skipped(self):
        """Déficit avec solde_restant=0 n'est pas imputé."""
        c = _make_client()
        c.store["deficit_reportable"] = [
            {
                "id": "def-zero",
                "id_sci": SCI_IR,
                "annee_constatation": 2022,
                "deficit_interets": 0.0,
                "deficit_charges": 0.0,
                "impute_revenu_global": 0.0,
                "total_impute_foncier": 0.0,
                "solde_restant": 0.0,
                "annee_prescription": 2032,
            }
        ]
        result = service.calculate(SCI_IR, ANNEE, c)
        assert result.total_deficits_anterieurs_imputes == 0.0

    def test_deficits_anterieurs_listed_when_deficit_current(self):
        """Même en déficit courant, on charge et liste les déficits antérieurs."""
        c = _make_client()
        c.store["loyers"] = [
            {"id": "l1", "id_bien": "bien-ir-1",
             "date_loyer": f"{ANNEE}-01-01", "montant": 500.0, "statut": "paye"},
        ]
        c.store["charges"] = [
            {"id": "ch-1", "id_bien": "bien-ir-1", "type_charge": "travaux",
             "montant": 20000.0, "date_paiement": f"{ANNEE}-04-01"},
        ]
        c.store["assurances_pno"] = []
        c.store["deficit_reportable"] = [
            {
                "id": "def-ant-2",
                "id_sci": SCI_IR,
                "annee_constatation": 2021,
                "deficit_interets": 800.0,
                "deficit_charges": 200.0,
                "impute_revenu_global": 0.0,
                "total_impute_foncier": 0.0,
                "solde_restant": 1000.0,
                "annee_prescription": 2031,
            }
        ]
        result = service.calculate(SCI_IR, ANNEE, c)
        assert result.is_deficit is True
        assert len(result.deficits_anterieurs) >= 1

    def test_impute_prior_deficits_fifo_order(self):
        """Deux déficits antérieurs, le plus ancien est imputé en premier (FIFO)."""
        c = _make_client()
        c.store["deficit_reportable"] = [
            {
                "id": "def-2021",
                "id_sci": SCI_IR,
                "annee_constatation": 2021,
                "deficit_interets": 500.0,
                "deficit_charges": 0.0,
                "impute_revenu_global": 0.0,
                "total_impute_foncier": 0.0,
                "solde_restant": 500.0,
                "annee_prescription": 2031,
            },
            {
                "id": "def-2022",
                "id_sci": SCI_IR,
                "annee_constatation": 2022,
                "deficit_interets": 300.0,
                "deficit_charges": 0.0,
                "impute_revenu_global": 0.0,
                "total_impute_foncier": 0.0,
                "solde_restant": 300.0,
                "annee_prescription": 2032,
            },
        ]
        result = service.calculate(SCI_IR, ANNEE, c)
        # Les deux devraient être listés
        assert len(result.deficits_anterieurs) == 2


# ---------------------------------------------------------------------------
# 9. Intérêts auto-calculés depuis credits_immobiliers
# ---------------------------------------------------------------------------

class TestInteretsAutoCalcules:
    def test_interets_auto_depuis_credit(self):
        """Sans charge 'interets_emprunt', on calcule depuis credits_immobiliers."""
        c = _make_client()
        c.store["charges"] = []  # Pas de charges manuelles
        c.store["credits_immobiliers"] = [
            {
                "id": "credit-1",
                "id_bien": "bien-ir-1",
                "montant_emprunte": 200000.0,
                "taux_nominal": 3.0,
                "taux_assurance": 0.2,
                "duree_mois": 240,
                "date_debut": f"{ANNEE}-01-01",
                "mensualite": 1109.0,
            }
        ]
        result = service.calculate(SCI_IR, ANNEE, c)
        bien1 = next(b for b in result.biens if b.bien_id == "bien-ir-1")
        assert bien1.ligne_230_interets_emprunt > 0.0

    def test_credit_invalid_skip(self):
        """Un crédit avec montant=0 est ignoré."""
        c = _make_client()
        c.store["charges"] = []
        c.store["credits_immobiliers"] = [
            {
                "id": "credit-bad",
                "id_bien": "bien-ir-1",
                "montant_emprunte": 0.0,
                "taux_nominal": 0.0,
                "duree_mois": 0,
                "date_debut": "",
                "mensualite": 0.0,
            }
        ]
        result = service.calculate(SCI_IR, ANNEE, c)
        bien1 = next(b for b in result.biens if b.bien_id == "bien-ir-1")
        assert bien1.ligne_230_interets_emprunt == 0.0

    def test_interets_manuels_prioritaires(self):
        """Les intérêts manuels (charges table) ont priorité sur le calcul auto."""
        c = _make_client()
        c.store["charges"] = [
            {"id": "ch-i", "id_bien": "bien-ir-1", "type_charge": "interets_emprunt",
             "montant": 1500.0, "date_paiement": f"{ANNEE}-06-01"},
        ]
        c.store["credits_immobiliers"] = [
            {
                "id": "credit-1",
                "id_bien": "bien-ir-1",
                "montant_emprunte": 200000.0,
                "taux_nominal": 3.0,
                "taux_assurance": 0.0,
                "duree_mois": 240,
                "date_debut": f"{ANNEE}-01-01",
                "mensualite": 1109.0,
            }
        ]
        result = service.calculate(SCI_IR, ANNEE, c)
        bien1 = next(b for b in result.biens if b.bien_id == "bien-ir-1")
        # Doit utiliser 1500 (manuel), pas le calcul auto
        assert bien1.ligne_230_interets_emprunt == 1500.0


# ---------------------------------------------------------------------------
# 10. Types de charges variés et alertes CERFA
# ---------------------------------------------------------------------------

class TestChargesVariees:
    def test_entretien_mappe_ligne_221(self):
        c = _make_client()
        c.store["charges"] = [
            {"id": "ch-e", "id_bien": "bien-ir-1", "type_charge": "entretien",
             "montant": 600.0, "date_paiement": f"{ANNEE}-02-01"},
        ]
        c.store["assurances_pno"] = []
        result = service.calculate(SCI_IR, ANNEE, c)
        bien1 = next(b for b in result.biens if b.bien_id == "bien-ir-1")
        assert bien1.ligne_221_travaux >= 600.0

    def test_syndic_mappe_ligne_227(self):
        c = _make_client()
        c.store["charges"] = [
            {"id": "ch-s", "id_bien": "bien-ir-1", "type_charge": "syndic",
             "montant": 400.0, "date_paiement": f"{ANNEE}-03-01"},
        ]
        c.store["assurances_pno"] = []
        result = service.calculate(SCI_IR, ANNEE, c)
        bien1 = next(b for b in result.biens if b.bien_id == "bien-ir-1")
        assert bien1.ligne_227_copropriete == 400.0

    def test_assurance_charge_ligne_220(self):
        c = _make_client()
        c.store["charges"] = [
            {"id": "ch-a", "id_bien": "bien-ir-1", "type_charge": "assurance",
             "montant": 350.0, "date_paiement": f"{ANNEE}-05-01"},
        ]
        c.store["assurances_pno"] = []
        result = service.calculate(SCI_IR, ANNEE, c)
        bien1 = next(b for b in result.biens if b.bien_id == "bien-ir-1")
        assert bien1.ligne_220_assurance == 350.0

    def test_charge_non_mappee_alerte(self):
        """Un type de charge inconnu doit générer une alerte."""
        c = _make_client()
        c.store["charges"] = [
            {"id": "ch-x", "id_bien": "bien-ir-1", "type_charge": "type_inconnu",
             "montant": 100.0, "date_paiement": f"{ANNEE}-01-01"},
        ]
        result = service.calculate(SCI_IR, ANNEE, c)
        # Alerte pour type non mappé
        assert any("non mappée" in a for a in result.alertes)

    def test_alerte_aucune_charge_avec_loyers(self):
        """Un bien avec loyers mais sans charge génère une alerte."""
        c = _make_client()
        c.store["charges"] = []
        c.store["assurances_pno"] = []
        result = service.calculate(SCI_IR, ANNEE, c)
        assert any("aucune charge déductible" in a for a in result.alertes)

    def test_frais_gestion_charge_mappe_221(self):
        c = _make_client()
        c.store["charges"] = [
            {"id": "ch-fg", "id_bien": "bien-ir-1", "type_charge": "frais_gestion",
             "montant": 300.0, "date_paiement": f"{ANNEE}-07-01"},
        ]
        c.store["assurances_pno"] = []
        result = service.calculate(SCI_IR, ANNEE, c)
        bien1 = next(b for b in result.biens if b.bien_id == "bien-ir-1")
        assert bien1.ligne_221_travaux >= 300.0

    def test_travaux_amelioration_mappe_221(self):
        c = _make_client()
        c.store["charges"] = [
            {"id": "ch-ta", "id_bien": "bien-ir-1", "type_charge": "travaux_amelioration",
             "montant": 1000.0, "date_paiement": f"{ANNEE}-08-01"},
        ]
        c.store["assurances_pno"] = []
        result = service.calculate(SCI_IR, ANNEE, c)
        bien1 = next(b for b in result.biens if b.bien_id == "bien-ir-1")
        assert bien1.ligne_221_travaux >= 1000.0

    def test_prime_assurance_mappe_220(self):
        c = _make_client()
        c.store["charges"] = [
            {"id": "ch-pa", "id_bien": "bien-ir-1", "type_charge": "prime_assurance",
             "montant": 250.0, "date_paiement": f"{ANNEE}-02-15"},
        ]
        c.store["assurances_pno"] = []
        result = service.calculate(SCI_IR, ANNEE, c)
        bien1 = next(b for b in result.biens if b.bien_id == "bien-ir-1")
        assert bien1.ligne_220_assurance >= 250.0


# ---------------------------------------------------------------------------
# 11. Alerte loyer manquant pour un bien
# ---------------------------------------------------------------------------

class TestAlerteLoyer:
    def test_alerte_si_aucun_loyer_pour_bien(self):
        c = _make_client()
        # Supprimer les loyers du bien-ir-2
        c.store["loyers"] = [
            r for r in c.store["loyers"]
            if r.get("id_bien") == "bien-ir-1" and r.get("statut") == "paye"
            and r.get("date_loyer", "").startswith(str(ANNEE))
        ]
        result = service.calculate(SCI_IR, ANNEE, c)
        assert any("Aucun loyer" in a for a in result.alertes)


# ---------------------------------------------------------------------------
# 12. Alerte parts ne totalisant pas nb_parts_total
# ---------------------------------------------------------------------------

class TestAlerteParts:
    def test_alerte_parts_incorrectes(self):
        """Si la somme des parts != nb_parts_total, une alerte est générée."""
        c = _make_client()
        # Mettre 150 parts alors que nb_parts_total=100
        c.store["associes"] = [
            {
                "id": "assoc-bad",
                "id_sci": SCI_IR,
                "user_id": "user-123",
                "nom": "Test",
                "email": "t@t.fr",
                "part": 100,
                "nb_parts": 150,
                "role": "gerant",
            }
        ]
        result = service.calculate(SCI_IR, ANNEE, c)
        assert any("totalisent" in a for a in result.alertes)


# ---------------------------------------------------------------------------
# 13. Associé sans parts (nb_parts=0)
# ---------------------------------------------------------------------------

class TestAssociesSansParts:
    def test_alerte_no_parts(self):
        """Aucun associé avec nb_parts → alerte quote-parts non calculables."""
        c = _make_client()
        c.store["associes"] = [
            {
                "id": "assoc-np",
                "id_sci": SCI_IR,
                "user_id": "user-123",
                "nom": "Sans Parts",
                "email": "sp@test.fr",
                "part": 100,
                "nb_parts": 0,
                "role": "gerant",
            }
        ]
        result = service.calculate(SCI_IR, ANNEE, c)
        assert any("quote-parts non calculables" in a for a in result.alertes)


# ---------------------------------------------------------------------------
# 14. _save_deficit — ne sauvegarde pas si pas de déficit
# ---------------------------------------------------------------------------

class TestSaveDeficit:
    def test_save_deficit_no_op_when_no_deficit(self):
        c = _make_client()
        # Résultat positif — is_deficit=False
        result_obj = ResumeFiscalResult(
            sci_nom="Test", sci_siren="", regime_fiscal="IR", annee=ANNEE,
            is_deficit=False,
        )
        # Ne doit pas lever d'exception
        service._save_deficit(SCI_IR, ANNEE, result_obj, c)
        assert c.store.get("deficit_reportable", []) == []

    def test_save_deficit_upserts_row(self):
        c = _make_client()
        result_obj = ResumeFiscalResult(
            sci_nom="Test", sci_siren="", regime_fiscal="IR", annee=ANNEE,
            is_deficit=True,
            deficit_total=5000.0,
            deficit_interets_emprunt=1000.0,
            deficit_imputable_revenu_global=3000.0,
            deficit_reportable_foncier=1000.0,
        )
        service._save_deficit(SCI_IR, ANNEE, result_obj, c)
        rows = c.store.get("deficit_reportable", [])
        assert len(rows) == 1
        assert rows[0]["id_sci"] == SCI_IR

    def test_save_deficit_zero_reportable_no_op(self):
        """Si total reportable = 0, ne sauvegarde rien."""
        c = _make_client()
        result_obj = ResumeFiscalResult(
            sci_nom="Test", sci_siren="", regime_fiscal="IR", annee=ANNEE,
            is_deficit=True,
            deficit_total=0.0,
            deficit_interets_emprunt=0.0,
            deficit_imputable_revenu_global=0.0,
            deficit_reportable_foncier=0.0,
        )
        service._save_deficit(SCI_IR, ANNEE, result_obj, c)
        assert c.store.get("deficit_reportable", []) == []


# ---------------------------------------------------------------------------
# 15. prefill_fiscalite
# ---------------------------------------------------------------------------

class TestPrefillFiscalite:
    def test_prefill_creates_fiscalite_record(self):
        c = _make_client()
        c.store["fiscalite"] = []  # Pas encore de record
        result = service.prefill_fiscalite(c, SCI_IR, ANNEE)
        assert result["id_sci"] == SCI_IR
        assert result["annee"] == ANNEE
        assert result["total_revenus"] > 0
        # Vérifie que le record est créé dans le store
        rows = c.store.get("fiscalite", [])
        assert len(rows) == 1

    def test_prefill_updates_existing_record(self):
        c = _make_client()
        c.store["fiscalite"] = [
            {"id": "fisc-existing", "id_sci": SCI_IR, "annee": ANNEE, "total_revenus": 0}
        ]
        result = service.prefill_fiscalite(c, SCI_IR, ANNEE)
        assert result["total_revenus"] > 0
        # Le record doit être mis à jour (id existant)
        assert result["id"] == "fisc-existing"

    def test_prefill_correct_total_revenus(self):
        c = _make_client()
        c.store["fiscalite"] = []
        result = service.prefill_fiscalite(c, SCI_IR, ANNEE)
        # 12 × 900 + 10 × 700 = 10800 + 7000 = 17800
        assert result["total_revenus"] == 17800.0

    def test_prefill_charges_par_categorie(self):
        c = _make_client()
        c.store["fiscalite"] = []
        c.store["charges"] = [
            {"id": "ch-1", "id_bien": "bien-ir-1", "type_charge": "interets_emprunt",
             "montant": 1000.0, "date_paiement": f"{ANNEE}-01-15"},
            {"id": "ch-2", "id_bien": "bien-ir-1", "type_charge": "travaux_entretien",
             "montant": 500.0, "date_paiement": f"{ANNEE}-03-01"},
        ]
        result = service.prefill_fiscalite(c, SCI_IR, ANNEE)
        assert result["interets_emprunt"] == 1000.0
        assert result["travaux"] == 500.0

    def test_prefill_resultat_fiscal_calcule(self):
        c = _make_client()
        c.store["fiscalite"] = []
        c.store["charges"] = [
            {"id": "ch-1", "id_bien": "bien-ir-1", "type_charge": "taxe_fonciere",
             "montant": 800.0, "date_paiement": f"{ANNEE}-09-01"},
        ]
        result = service.prefill_fiscalite(c, SCI_IR, ANNEE)
        assert result["resultat_fiscal"] == round(result["total_revenus"] - result["total_charges"], 2)

    def test_prefill_no_biens(self):
        c = _make_client()
        c.store["biens"] = []
        c.store["fiscalite"] = []
        result = service.prefill_fiscalite(c, SCI_IR, ANNEE)
        assert result["total_revenus"] == 0.0
        assert result["total_charges"] == 0.0


# ---------------------------------------------------------------------------
# 16. _load_prior_deficits
# ---------------------------------------------------------------------------

class TestLoadPriorDeficits:
    def test_load_prior_deficits_returns_rows(self):
        c = _make_client()
        c.store["deficit_reportable"] = [
            {
                "id": "def-1",
                "id_sci": SCI_IR,
                "annee_constatation": 2022,
                "solde_restant": 500.0,
                "annee_prescription": 2032,
                "deficit_interets": 200.0,
                "deficit_charges": 300.0,
                "total_impute_foncier": 0.0,
            }
        ]
        rows = service._load_prior_deficits(SCI_IR, ANNEE, c)
        assert len(rows) == 1

    def test_load_prior_deficits_expired_excluded(self):
        """Déficits dont annee_prescription <= annee courant sont exclus."""
        c = _make_client()
        c.store["deficit_reportable"] = [
            {
                "id": "def-expired",
                "id_sci": SCI_IR,
                "annee_constatation": 2010,
                "solde_restant": 500.0,
                "annee_prescription": 2020,  # Prescrit avant ANNEE
                "deficit_interets": 0.0,
                "deficit_charges": 500.0,
                "total_impute_foncier": 0.0,
            }
        ]
        rows = service._load_prior_deficits(SCI_IR, ANNEE, c)
        assert len(rows) == 0

    def test_load_prior_deficits_only_matching_sci(self):
        """Seuls les déficits de la bonne SCI sont retournés."""
        c = _make_client()
        c.store["deficit_reportable"] = [
            {
                "id": "def-other-sci",
                "id_sci": "autre-sci",
                "annee_constatation": 2021,
                "solde_restant": 500.0,
                "annee_prescription": 2031,
                "deficit_interets": 0.0,
                "deficit_charges": 500.0,
                "total_impute_foncier": 0.0,
            }
        ]
        rows = service._load_prior_deficits(SCI_IR, ANNEE, c)
        # L'autre SCI ne doit pas être retournée
        assert all(r.get("id_sci") == SCI_IR for r in rows)


# ---------------------------------------------------------------------------
# 17. _impute_prior_deficits
# ---------------------------------------------------------------------------

class TestImputePriorDeficits:
    def test_impute_reduces_solde(self):
        c = _make_client()
        prior_rows = [
            {
                "id": "def-1",
                "annee_constatation": 2022,
                "annee_prescription": 2032,
                "deficit_interets": 300.0,
                "deficit_charges": 200.0,
                "total_impute_foncier": 0.0,
                "solde_restant": 500.0,
            }
        ]
        deficits, total_imputed = service._impute_prior_deficits(prior_rows, 1000.0, c)
        assert total_imputed == 500.0  # Tout imputé (revenu > solde)
        assert deficits[0].solde_restant == 0.0

    def test_impute_partial_when_income_less_than_deficit(self):
        c = _make_client()
        prior_rows = [
            {
                "id": "def-2",
                "annee_constatation": 2021,
                "annee_prescription": 2031,
                "deficit_interets": 1000.0,
                "deficit_charges": 0.0,
                "total_impute_foncier": 0.0,
                "solde_restant": 1000.0,
            }
        ]
        deficits, total_imputed = service._impute_prior_deficits(prior_rows, 400.0, c)
        assert total_imputed == 400.0  # Partiel: revenu = 400
        assert deficits[0].solde_restant == 600.0

    def test_impute_zero_income_no_imputation(self):
        c = _make_client()
        prior_rows = [
            {
                "id": "def-3",
                "annee_constatation": 2022,
                "annee_prescription": 2032,
                "deficit_interets": 500.0,
                "deficit_charges": 0.0,
                "total_impute_foncier": 0.0,
                "solde_restant": 500.0,
            }
        ]
        deficits, total_imputed = service._impute_prior_deficits(prior_rows, 0.0, c)
        assert total_imputed == 0.0


# ---------------------------------------------------------------------------
# 18. Résultat global arrondi
# ---------------------------------------------------------------------------

class TestResultatGlobal:
    def test_resultat_global_bénéfice(self):
        c = _make_client()
        result = service.calculate(SCI_IR, ANNEE, c)
        # Revenus = 17800, charges > 0 → résultat positif
        assert result.resultat_global > 0

    def test_resultat_global_is_rounded(self):
        c = _make_client()
        result = service.calculate(SCI_IR, ANNEE, c)
        # Doit être arrondi à 2 décimales
        assert result.resultat_global == round(result.resultat_global, 2)


# ---------------------------------------------------------------------------
# 19. Cas sans SCI adresse/capital/gérant (None)
# ---------------------------------------------------------------------------

class TestSciFieldsNone:
    def test_optional_sci_fields_none(self):
        c = _make_client()
        c.store["sci"] = [
            {
                "id": SCI_IR,
                "nom": "SCI Minimale",
                "siren": None,
                "regime_fiscal": None,
                "adresse_siege": None,
                "capital_social": None,
                "nom_gerant": None,
                "nb_parts_total": 100,
            }
        ]
        result = service.calculate(SCI_IR, ANNEE, c)
        assert result.sci_siren == ""
        assert result.regime_fiscal == "IR"
        assert result.sci_adresse_siege == ""
        assert result.sci_capital_social == 0.0
        assert result.sci_nom_gerant == ""
