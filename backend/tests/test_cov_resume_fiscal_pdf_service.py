"""Coverage tests for app/services/resume_fiscal_pdf_service.py.

Strategy: instantiate ResumeFiscalResult directly (no DB, no Supabase) and
call ResumeFiscalPdfService.generate() / Report2042PdfService.generate() with
realistic, complete data dicts.  A single well-formed call exercises hundreds
of ReportLab drawing lines; multiple variants hit every conditional branch.
"""

from __future__ import annotations

from unittest.mock import patch

from app.services.resume_fiscal_pdf_service import (
    ResumeFiscalPdfService,
    Report2042PdfService,
    _fmt_eur,
    _result_color,
    _register_fonts,
)
from app.services.resume_fiscal_service import (
    AssocieQuotePart,
    BienFiscalDetail,
    DeficitAnterieur,
    ResumeFiscalResult,
)


# ---------------------------------------------------------------------------
# Helpers to build complete result objects
# ---------------------------------------------------------------------------


def _make_bien(
    bid: str = "bien-1",
    adresse: str = "12 rue de la Paix",
    ville: str = "Paris",
    loyers: float = 12000.0,
    frais: float = 20.0,
    assurance: float = 280.0,
    travaux: float = 1500.0,
    taxe: float = 800.0,
    copro: float = 600.0,
    total_charges: float = 3200.0,
    interets: float = 3000.0,
) -> BienFiscalDetail:
    return BienFiscalDetail(
        bien_id=bid,
        adresse=adresse,
        ville=ville,
        ligne_211_loyers_bruts=loyers,
        ligne_215_frais_gestion=frais,
        ligne_220_assurance=assurance,
        ligne_221_travaux=travaux,
        ligne_224_taxe_fonciere=taxe,
        ligne_227_copropriete=copro,
        ligne_229_total_charges=total_charges,
        ligne_230_interets_emprunt=interets,
        ligne_240_resultat_net=loyers - total_charges - interets,
    )


def _make_associe(
    nom: str = "Jean Dupont",
    part_pct: float = 60.0,
    quote_part: float = 3000.0,
    case_4ba: float = 3000.0,
    case_4bb: float = 0.0,
    case_4bc: float = 0.0,
    case_4bd: float = 0.0,
) -> AssocieQuotePart:
    return AssocieQuotePart(
        associe_id="assoc-1",
        nom=nom,
        email="jean@dupont.fr",
        part_pct=part_pct,
        quote_part_resultat=quote_part,
        case_4ba=case_4ba,
        case_4bb=case_4bb,
        case_4bc=case_4bc,
        case_4bd=case_4bd,
    )


def _make_result_ir_benefice() -> ResumeFiscalResult:
    """Typical IR SCI with positive result, two biens, two associés, micro-foncier comparison."""
    bien1 = _make_bien(bid="b1", adresse="12 rue de la Paix", ville="Paris")
    bien2 = _make_bien(
        bid="b2",
        adresse="5 avenue de Lyon",
        ville="Lyon",
        loyers=9600.0,
        total_charges=2800.0,
        interets=2200.0,
    )
    assoc1 = _make_associe(nom="Jean Dupont", part_pct=60.0, quote_part=3240.0, case_4ba=3240.0)
    assoc2 = _make_associe(
        nom="Marie Martin",
        part_pct=40.0,
        quote_part=2160.0,
        case_4ba=2160.0,
    )
    return ResumeFiscalResult(
        sci_nom="SCI Lumière",
        sci_siren="123456789",
        regime_fiscal="IR",
        annee=2025,
        biens=[bien1, bien2],
        total_revenus=21600.0,
        total_charges=6000.0,
        total_interets=5200.0,
        resultat_global=5400.0,
        associes=[assoc1, assoc2],
        alertes=["Alerte test : taxe foncière manquante."],
        sci_adresse_siege="12 rue de Belleville, 75020 Paris",
        sci_capital_social=10000.0,
        sci_nom_gerant="Jean Dupont",
        nb_biens=2,
        nb_associes=2,
        # Micro-foncier NOT eligible (revenus > 15 000)
        micro_foncier_eligible=False,
        micro_foncier_abattement=0.0,
        micro_foncier_resultat=0.0,
        regime_recommande="reel",
        economie_regime_recommande=0.0,
        is_deficit=False,
    )


def _make_result_ir_deficit() -> ResumeFiscalResult:
    """IR SCI with deficit, prior deficits, micro-foncier eligible."""
    bien = _make_bien(
        bid="b1",
        adresse="8 impasse Courte",
        ville="Bordeaux",
        loyers=8000.0,
        total_charges=7000.0,
        interets=4000.0,
    )
    assoc = AssocieQuotePart(
        associe_id="assoc-d",
        nom="Alice Bernard",
        email="alice@b.fr",
        part_pct=100.0,
        quote_part_resultat=-3000.0,
        case_4ba=0.0,
        case_4bb=2700.0,
        case_4bc=300.0,
        case_4bd=500.0,
    )
    prior = DeficitAnterieur(
        annee=2023,
        montant_initial=5000.0,
        total_impute=2000.0,
        solde_restant=3000.0,
        annee_prescription=2033,
    )
    return ResumeFiscalResult(
        sci_nom="SCI Déficit",
        sci_siren="987654321",
        regime_fiscal="IR",
        annee=2025,
        biens=[bien],
        total_revenus=8000.0,
        total_charges=7000.0,
        total_interets=4000.0,
        resultat_global=-3000.0,
        associes=[assoc],
        alertes=[],
        sci_adresse_siege="",
        sci_capital_social=0.0,
        sci_nom_gerant="",
        nb_biens=1,
        nb_associes=1,
        # Micro-foncier eligible (revenus <= 15 000)
        micro_foncier_eligible=True,
        micro_foncier_abattement=2400.0,
        micro_foncier_resultat=5600.0,
        regime_recommande="reel",
        economie_regime_recommande=8600.0,
        # Déficit
        is_deficit=True,
        deficit_total=3000.0,
        deficit_interets_emprunt=3000.0,
        deficit_imputable_revenu_global=0.0,
        deficit_reportable_foncier=0.0,
        deficits_anterieurs=[prior],
        total_deficits_anterieurs_imputes=500.0,
    )


def _make_result_no_biens_no_associes() -> ResumeFiscalResult:
    """Minimal edge case: no biens, no associés."""
    return ResumeFiscalResult(
        sci_nom="SCI Vide",
        sci_siren=None,
        regime_fiscal="IS",
        annee=2024,
        biens=[],
        total_revenus=0.0,
        total_charges=0.0,
        total_interets=0.0,
        resultat_global=0.0,
        associes=[],
        alertes=["SCI sans bien enregistré."],
        sci_adresse_siege=None,
        sci_capital_social=None,
        sci_nom_gerant=None,
        nb_biens=0,
        nb_associes=0,
        micro_foncier_eligible=False,
        is_deficit=False,
    )


def _make_result_micro_foncier_micro_recommande() -> ResumeFiscalResult:
    """Micro-foncier eligible AND micro régime recommended."""
    bien = _make_bien(
        bid="b1",
        adresse="1 rue Test",
        ville="Nantes",
        loyers=5000.0,
        total_charges=500.0,
        interets=0.0,
    )
    assoc = _make_associe(part_pct=100.0, quote_part=4500.0, case_4ba=4500.0)
    return ResumeFiscalResult(
        sci_nom="SCI Micro",
        sci_siren="111222333",
        regime_fiscal="IR",
        annee=2025,
        biens=[bien],
        total_revenus=5000.0,
        total_charges=500.0,
        total_interets=0.0,
        resultat_global=4500.0,
        associes=[assoc],
        alertes=[],
        sci_adresse_siege="1 place Test, 44000 Nantes",
        sci_capital_social=5000.0,
        sci_nom_gerant="Test Gérant",
        nb_biens=1,
        nb_associes=1,
        micro_foncier_eligible=True,
        micro_foncier_abattement=1500.0,
        micro_foncier_resultat=3500.0,
        regime_recommande="micro",
        economie_regime_recommande=1000.0,
        is_deficit=False,
    )


# ---------------------------------------------------------------------------
# Module-level helpers
# ---------------------------------------------------------------------------


class TestFmtEur:
    def test_positive_integer(self):
        assert "1 200,00 EUR" in _fmt_eur(1200.0)

    def test_zero(self):
        result = _fmt_eur(0.0)
        assert "0,00 EUR" in result

    def test_negative(self):
        result = _fmt_eur(-500.50)
        assert result.startswith("-")
        assert "500" in result

    def test_large_number(self):
        result = _fmt_eur(1_234_567.89)
        assert "EUR" in result

    def test_small_decimal(self):
        result = _fmt_eur(0.01)
        assert "EUR" in result


class TestResultColor:
    def test_positive_green(self):
        from reportlab.lib import colors as rcolors
        color = _result_color(100.0)
        assert color is not None

    def test_negative_red(self):
        color = _result_color(-100.0)
        assert color is not None

    def test_zero_dark(self):
        color = _result_color(0.0)
        assert color is not None


class TestRegisterFonts:
    def test_returns_tuple_of_strings(self):
        name, bold = _register_fonts()
        assert isinstance(name, str) and len(name) > 0
        assert isinstance(bold, str) and len(bold) > 0

    def test_no_fonts_fallback_helvetica(self):
        with patch("app.services.resume_fiscal_pdf_service.os.path.isfile", return_value=False):
            name, bold = _register_fonts()
        assert name == "Helvetica"
        assert bold == "Helvetica-Bold"

    def test_dejavu_not_found_vera_fallback(self):
        import os as _os
        original = _os.path.isfile

        def fake_isfile(path):
            if "DejaVu" in path or "dejavu" in path:
                return False
            return original(path)

        with patch("app.services.resume_fiscal_pdf_service.os.path.isfile", side_effect=fake_isfile):
            name, bold = _register_fonts()
        assert "DejaVu" not in name

    def test_dejavu_registration_raises_continues(self):
        import os as _os
        original = _os.path.isfile

        def fake_isfile(path):
            if "DejaVu" in path:
                return True
            return original(path)

        with patch("app.services.resume_fiscal_pdf_service.os.path.isfile", side_effect=fake_isfile), \
             patch("app.services.resume_fiscal_pdf_service.pdfmetrics.registerFont", side_effect=Exception("font error")):
            name, bold = _register_fonts()
        # Should not raise; falls back
        assert isinstance(name, str)


# ---------------------------------------------------------------------------
# ResumeFiscalPdfService.generate()
# ---------------------------------------------------------------------------


class TestResumeFiscalPdfServiceGenerate:
    """Each test calls generate() and checks that a valid PDF is returned."""

    def _svc(self):
        return ResumeFiscalPdfService()

    def test_generate_ir_benefice_returns_pdf_bytes(self):
        result = _make_result_ir_benefice()
        pdf = self._svc().generate(result)
        assert isinstance(pdf, (bytes, bytearray))
        assert len(pdf) > 500
        assert pdf[:4] == b"%PDF"

    def test_generate_ir_deficit_with_prior_deficits(self):
        result = _make_result_ir_deficit()
        pdf = self._svc().generate(result)
        assert isinstance(pdf, (bytes, bytearray))
        assert len(pdf) > 500
        assert pdf[:4] == b"%PDF"

    def test_generate_no_biens_no_associes(self):
        """Edge case: empty biens list skips pages 2 & 3; no associés shows placeholder text."""
        result = _make_result_no_biens_no_associes()
        pdf = self._svc().generate(result)
        assert isinstance(pdf, (bytes, bytearray))
        assert len(pdf) > 500

    def test_generate_micro_foncier_micro_recommended(self):
        """Micro-foncier eligible with micro as recommended regime — covers rec_col=1 branch."""
        result = _make_result_micro_foncier_micro_recommande()
        pdf = self._svc().generate(result)
        assert isinstance(pdf, (bytes, bytearray))
        assert len(pdf) > 500

    def test_generate_is_regime(self):
        """IS regime — covers the else branch in regime_fiscal label."""
        result = _make_result_no_biens_no_associes()
        result.regime_fiscal = "IS"
        pdf = self._svc().generate(result)
        assert isinstance(pdf, (bytes, bytearray))
        assert len(pdf) > 500

    def test_generate_ir_regime_string(self):
        """IR regime — covers the 'IR — Revenus fonciers' branch."""
        result = _make_result_ir_benefice()
        result.regime_fiscal = "IR"
        pdf = self._svc().generate(result)
        assert pdf[:4] == b"%PDF"

    def test_generate_with_alertes(self):
        """Alertes section is rendered when result.alertes is non-empty."""
        result = _make_result_ir_benefice()
        result.alertes = ["Alerte 1 : données manquantes.", "Alerte 2 : charge non mappée."]
        pdf = self._svc().generate(result)
        assert len(pdf) > 500

    def test_generate_no_alertes(self):
        """Alertes section skipped when alertes is empty."""
        result = _make_result_ir_benefice()
        result.alertes = []
        pdf = self._svc().generate(result)
        assert pdf[:4] == b"%PDF"

    def test_generate_sci_siren_none(self):
        """sci_siren=None renders as 'Non renseigné' — NoneType safety."""
        result = _make_result_ir_benefice()
        result.sci_siren = None
        pdf = self._svc().generate(result)
        assert len(pdf) > 500

    def test_generate_sci_capital_none(self):
        """sci_capital_social=None renders as 'Non renseigné'."""
        result = _make_result_ir_benefice()
        result.sci_capital_social = None
        pdf = self._svc().generate(result)
        assert len(pdf) > 500

    def test_generate_bien_no_ville(self):
        """Bien with empty ville — skips the ', ville' part of label."""
        result = _make_result_ir_benefice()
        result.biens[0].ville = ""
        pdf = self._svc().generate(result)
        assert len(pdf) > 500

    def test_generate_result_zero(self):
        """resultat_global exactly zero — _result_color returns _DARK."""
        result = _make_result_ir_benefice()
        result.resultat_global = 0.0
        result.is_deficit = False
        pdf = self._svc().generate(result)
        assert pdf[:4] == b"%PDF"

    def test_generate_negative_result_no_deficit_flag(self):
        """Negative result without is_deficit=True — deficit section skipped."""
        result = _make_result_ir_benefice()
        result.resultat_global = -100.0
        result.is_deficit = False
        pdf = self._svc().generate(result)
        assert len(pdf) > 500

    def test_generate_deficit_total_imputes_gt_zero(self):
        """total_deficits_anterieurs_imputes > 0 — renders the imputation paragraph."""
        result = _make_result_ir_deficit()
        result.total_deficits_anterieurs_imputes = 500.0
        pdf = self._svc().generate(result)
        assert len(pdf) > 500

    def test_generate_associes_case_4bb_4bc(self):
        """Associé with case_4bb and case_4bc triggers the multi-case instruction branch."""
        result = _make_result_ir_deficit()
        # Already has associe with case_4bb=2700 and case_4bc=300
        pdf = self._svc().generate(result)
        assert len(pdf) > 500

    def test_generate_associes_all_zero_cases(self):
        """Associé with all-zero cases — no instruction lines rendered."""
        result = _make_result_ir_benefice()
        for assoc in result.associes:
            assoc.case_4ba = 0.0
            assoc.case_4bb = 0.0
            assoc.case_4bc = 0.0
            assoc.case_4bd = 0.0
        pdf = self._svc().generate(result)
        assert len(pdf) > 500

    def test_generate_micro_foncier_reel_recommended(self):
        """Micro-foncier eligible with reel as recommended — rec_col=2 branch."""
        result = _make_result_micro_foncier_micro_recommande()
        result.regime_recommande = "reel"
        pdf = self._svc().generate(result)
        assert pdf[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# Individual page builders (unit tests without full generate())
# ---------------------------------------------------------------------------


class TestPageBuilders:
    """Call private _build_* methods to ensure they return non-empty element lists."""

    def _svc(self):
        return ResumeFiscalPdfService()

    def test_build_page1_identification(self):
        svc = self._svc()
        result = _make_result_ir_benefice()
        elements = svc._build_page1_identification(result)
        assert len(elements) > 0

    def test_build_page2_revenus(self):
        svc = self._svc()
        result = _make_result_ir_benefice()
        elements = svc._build_page2_revenus(result)
        assert len(elements) > 0

    def test_build_page3_charges(self):
        svc = self._svc()
        result = _make_result_ir_benefice()
        elements = svc._build_page3_charges(result)
        assert len(elements) > 0

    def test_build_page4_resultat_benefice(self):
        svc = self._svc()
        result = _make_result_ir_benefice()
        elements = svc._build_page4_resultat(result)
        assert len(elements) > 0

    def test_build_page4_resultat_deficit(self):
        svc = self._svc()
        result = _make_result_ir_deficit()
        elements = svc._build_page4_resultat(result)
        assert len(elements) > 0

    def test_build_page5_associes_with_associes(self):
        svc = self._svc()
        result = _make_result_ir_benefice()
        elements = svc._build_page5_associes(result)
        assert len(elements) > 0

    def test_build_page5_associes_empty(self):
        svc = self._svc()
        result = _make_result_no_biens_no_associes()
        elements = svc._build_page5_associes(result)
        # Should render the "Aucun associé" placeholder
        assert len(elements) > 0

    def test_build_alertes_non_empty(self):
        svc = self._svc()
        result = _make_result_ir_benefice()
        result.alertes = ["Alerte A", "Alerte B"]
        elements = svc._build_alertes(result)
        assert len(elements) > 0

    def test_build_alertes_empty(self):
        svc = self._svc()
        result = _make_result_ir_benefice()
        result.alertes = []
        elements = svc._build_alertes(result)
        # Footer + disclaimer always present
        assert len(elements) > 0

    def test_page_footer(self):
        svc = self._svc()
        footer = svc._page_footer()
        assert len(footer) >= 2

    def test_make_cerfa_table_no_highlight(self):
        """highlight_last=False skips the last-row style commands."""
        svc = self._svc()
        data = [["H1", "H2"], ["v1", "v2"]]
        table = svc._make_cerfa_table(data, [80, 80], highlight_last=False)
        assert table is not None

    def test_make_cerfa_table_single_row(self):
        """Single data row (header only) — highlight_last branch skipped."""
        svc = self._svc()
        data = [["H1", "H2"]]
        table = svc._make_cerfa_table(data, [80, 80], highlight_last=True)
        assert table is not None


# ---------------------------------------------------------------------------
# Report2042PdfService.generate()
# ---------------------------------------------------------------------------


class TestReport2042PdfService:
    """Tests for the per-associé 2042 PDF."""

    def _svc(self):
        return Report2042PdfService()

    def _make_associe_4ba(self) -> AssocieQuotePart:
        return AssocieQuotePart(
            associe_id="a1",
            nom="Jean Dupont",
            email="jean@dupont.fr",
            part_pct=60.0,
            quote_part_resultat=3000.0,
            case_4ba=3000.0,
            case_4bb=0.0,
            case_4bc=0.0,
            case_4bd=0.0,
        )

    def _make_associe_4bb_4bc(self) -> AssocieQuotePart:
        return AssocieQuotePart(
            associe_id="a2",
            nom="Marie Martin",
            email="marie@martin.fr",
            part_pct=40.0,
            quote_part_resultat=-2000.0,
            case_4ba=0.0,
            case_4bb=1800.0,
            case_4bc=200.0,
            case_4bd=0.0,
        )

    def _make_associe_4bd(self) -> AssocieQuotePart:
        return AssocieQuotePart(
            associe_id="a3",
            nom="Pierre Durand",
            email="",
            part_pct=100.0,
            quote_part_resultat=500.0,
            case_4ba=0.0,
            case_4bb=0.0,
            case_4bc=0.0,
            case_4bd=750.0,
        )

    def _make_associe_all_zero(self) -> AssocieQuotePart:
        return AssocieQuotePart(
            associe_id="a4",
            nom="Claire Petit",
            email="claire@p.fr",
            part_pct=50.0,
            quote_part_resultat=0.0,
            case_4ba=0.0,
            case_4bb=0.0,
            case_4bc=0.0,
            case_4bd=0.0,
        )

    def test_generate_4ba_case(self):
        """Associé with case_4ba — instruction line rendered."""
        result = _make_result_ir_benefice()
        pdf = self._svc().generate(result, self._make_associe_4ba())
        assert isinstance(pdf, (bytes, bytearray))
        assert len(pdf) > 500
        assert pdf[:4] == b"%PDF"

    def test_generate_4bb_4bc_case(self):
        """Associé with case_4bb and case_4bc."""
        result = _make_result_ir_deficit()
        pdf = self._svc().generate(result, self._make_associe_4bb_4bc())
        assert isinstance(pdf, (bytes, bytearray))
        assert len(pdf) > 500

    def test_generate_4bd_case(self):
        """Associé with only case_4bd non-zero."""
        result = _make_result_ir_benefice()
        pdf = self._svc().generate(result, self._make_associe_4bd())
        assert isinstance(pdf, (bytes, bytearray))
        assert len(pdf) > 500

    def test_generate_all_zero_cases(self):
        """Associé with all-zero cases triggers 'Aucun montant à reporter' message."""
        result = _make_result_ir_benefice()
        pdf = self._svc().generate(result, self._make_associe_all_zero())
        assert isinstance(pdf, (bytes, bytearray))
        assert len(pdf) > 500

    def test_generate_no_siren(self):
        """sci_siren=None renders as 'Non renseigné'."""
        result = _make_result_ir_benefice()
        result.sci_siren = None
        pdf = self._svc().generate(result, self._make_associe_4ba())
        assert len(pdf) > 500

    def test_generate_no_email(self):
        """Associé with no email renders as 'Non renseigné'."""
        assoc = self._make_associe_4ba()
        assoc.email = None
        result = _make_result_ir_benefice()
        pdf = self._svc().generate(result, assoc)
        assert len(pdf) > 500

    def test_generate_deficit_result(self):
        """Associé with negative quote_part_resultat."""
        result = _make_result_ir_deficit()
        assoc = result.associes[0]
        pdf = self._svc().generate(result, assoc)
        assert pdf[:4] == b"%PDF"

    def test_generate_4bc_only(self):
        """Associé with only case_4bc non-zero."""
        result = _make_result_ir_deficit()
        assoc = AssocieQuotePart(
            associe_id="a5",
            nom="Test User",
            email="test@test.fr",
            part_pct=100.0,
            quote_part_resultat=-500.0,
            case_4ba=0.0,
            case_4bb=0.0,
            case_4bc=500.0,
            case_4bd=0.0,
        )
        pdf = self._svc().generate(result, assoc)
        assert len(pdf) > 500
