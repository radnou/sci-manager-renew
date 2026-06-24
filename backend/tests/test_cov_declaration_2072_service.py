"""Tests de couverture pour app.services.declaration_2072_service.

Couvre :
- Declaration2072PdfService.generate() — SCI à l'IR, plusieurs biens
- _build_page1_identification (Cadre I — Identification)
- _build_page2_revenus (Cadre II — Revenus)
- _build_page3_charges (Cadre III — Charges)
- _build_page4_resultat (Cadre IV — Résultat fiscal)
- _build_page5_repartition (Cadre V — Répartition associés)
- _build_alertes (alertes + disclaimers)
- _fmt_eur (formattage EUR)
- _result_color (couleur résultat)
- _make_table (helper table)
- _page_footer (pied de page)
- Cas sans biens, sans associés, avec déficit
"""
from __future__ import annotations

import pytest

from app.services.declaration_2072_service import (
    Declaration2072PdfService,
    _fmt_eur,
    _result_color,
    _DARK,
    _GREEN,
    _RED,
)
from app.services.resume_fiscal_service import (
    ResumeFiscalResult,
    BienFiscalDetail,
    AssocieQuotePart,
)


# ---------------------------------------------------------------------------
# Helpers — build ResumeFiscalResult fixtures
# ---------------------------------------------------------------------------

def _make_bien(
    bien_id: str = "b1",
    adresse: str = "10 Rue du Test",
    ville: str = "Paris",
    loyers_bruts: float = 10800.0,
    taxe_fonciere: float = 800.0,
    copropriete: float = 1200.0,
    assurance: float = 280.0,
    travaux: float = 0.0,
    interets: float = 0.0,
) -> BienFiscalDetail:
    total_charges = 20.0 + assurance + travaux + taxe_fonciere + copropriete
    return BienFiscalDetail(
        bien_id=bien_id,
        adresse=adresse,
        ville=ville,
        ligne_211_loyers_bruts=loyers_bruts,
        ligne_215_frais_gestion=20.0,
        ligne_220_assurance=assurance,
        ligne_221_travaux=travaux,
        ligne_224_taxe_fonciere=taxe_fonciere,
        ligne_227_copropriete=copropriete,
        ligne_229_total_charges=total_charges,
        ligne_230_interets_emprunt=interets,
        ligne_240_resultat_net=loyers_bruts - total_charges - interets,
    )


def _make_associe(
    nom: str = "Moussa Belkacem",
    part_pct: float = 60.0,
    quote_part_resultat: float = 4000.0,
    case_4ba: float = 4000.0,
    case_4bb: float = 0.0,
    case_4bc: float = 0.0,
    case_4bd: float = 0.0,
) -> AssocieQuotePart:
    return AssocieQuotePart(
        associe_id="assoc-1",
        nom=nom,
        email=f"{nom.replace(' ', '').lower()}@test.fr",
        part_pct=part_pct,
        quote_part_resultat=quote_part_resultat,
        case_4ba=case_4ba,
        case_4bb=case_4bb,
        case_4bc=case_4bc,
        case_4bd=case_4bd,
    )


def _make_result(
    biens: list[BienFiscalDetail] | None = None,
    associes: list[AssocieQuotePart] | None = None,
    is_deficit: bool = False,
    alertes: list[str] | None = None,
    total_revenus: float = 10800.0,
    total_charges: float = 2300.0,
    total_interets: float = 0.0,
) -> ResumeFiscalResult:
    if biens is None:
        biens = [_make_bien()]
    if associes is None:
        associes = [_make_associe()]
    if alertes is None:
        alertes = []

    resultat_global = total_revenus - total_charges - total_interets
    deficit_total = abs(resultat_global) if is_deficit else 0.0

    return ResumeFiscalResult(
        sci_nom="SCI Déclaration 2072 Test",
        sci_siren="123456789",
        regime_fiscal="IR",
        annee=2025,
        biens=biens,
        total_revenus=total_revenus,
        total_charges=total_charges,
        total_interets=total_interets,
        resultat_global=resultat_global,
        associes=associes,
        alertes=alertes,
        sci_adresse_siege="10 Rue Fiscale, 75001 Paris",
        sci_capital_social=15000.0,
        sci_nom_gerant="Moussa Belkacem",
        nb_biens=len(biens),
        nb_associes=len(associes),
        is_deficit=is_deficit,
        deficit_total=deficit_total,
        deficit_interets_emprunt=total_interets if is_deficit else 0.0,
        deficit_imputable_revenu_global=min(deficit_total, 10700.0) if is_deficit else 0.0,
        deficit_reportable_foncier=max(deficit_total - 10700.0, 0.0) if is_deficit else 0.0,
    )


pdf_service = Declaration2072PdfService()


# ---------------------------------------------------------------------------
# 1. _fmt_eur — formattage monétaire
# ---------------------------------------------------------------------------

class TestFmtEur:
    def test_positive_value(self):
        result = _fmt_eur(1234.56)
        assert "EUR" in result
        assert "1" in result
        assert "234" in result

    def test_zero(self):
        result = _fmt_eur(0.0)
        assert "EUR" in result
        assert result.startswith("0")

    def test_negative_value(self):
        result = _fmt_eur(-500.0)
        assert result.startswith("-")
        assert "EUR" in result

    def test_large_value(self):
        result = _fmt_eur(100000.0)
        assert "EUR" in result
        assert "100" in result

    def test_decimal_comma_separator(self):
        """French format uses comma as decimal separator."""
        result = _fmt_eur(1234.5)
        assert "," in result


# ---------------------------------------------------------------------------
# 2. _result_color — couleur selon le signe du résultat
# ---------------------------------------------------------------------------

class TestResultColor:
    def test_positive_returns_green(self):
        assert _result_color(100.0) == _GREEN

    def test_negative_returns_red(self):
        assert _result_color(-100.0) == _RED

    def test_zero_returns_dark(self):
        assert _result_color(0.0) == _DARK


# ---------------------------------------------------------------------------
# 3. generate() — cas nominal avec un bien et un associé
# ---------------------------------------------------------------------------

class TestGenerateNominal:
    def test_generate_returns_bytes(self):
        result = _make_result()
        pdf = pdf_service.generate(result)
        assert isinstance(pdf, bytes)

    def test_generate_is_pdf(self):
        """Le PDF doit commencer par la signature %PDF."""
        result = _make_result()
        pdf = pdf_service.generate(result)
        assert pdf[:4] == b"%PDF"

    def test_generate_non_empty(self):
        result = _make_result()
        pdf = pdf_service.generate(result)
        assert len(pdf) > 1000  # PDF has meaningful content

    def test_generate_with_two_biens(self):
        biens = [
            _make_bien("b1", "10 Rue du Test", "Paris", 10800.0),
            _make_bien("b2", "20 Avenue Verte", "Lyon", 8400.0, interets=1000.0),
        ]
        result = _make_result(biens=biens, total_revenus=19200.0, total_interets=1000.0)
        pdf = pdf_service.generate(result)
        assert pdf[:4] == b"%PDF"
        assert len(pdf) > 2000


# ---------------------------------------------------------------------------
# 4. generate() — SCI sans biens
# ---------------------------------------------------------------------------

class TestGenerateSansBiens:
    def test_generate_no_biens(self):
        """Sans biens, les pages 2 et 3 ne sont pas générées."""
        result = _make_result(biens=[], total_revenus=0.0, total_charges=0.0)
        pdf = pdf_service.generate(result)
        assert isinstance(pdf, bytes)
        assert pdf[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# 5. generate() — SCI sans associés
# ---------------------------------------------------------------------------

class TestGenerateSansAssocies:
    def test_generate_no_associes(self):
        """La page 5 affiche un message si aucun associé."""
        result = _make_result(associes=[])
        pdf = pdf_service.generate(result)
        assert isinstance(pdf, bytes)
        assert pdf[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# 6. generate() — avec alertes
# ---------------------------------------------------------------------------

class TestGenerateAvecAlertes:
    def test_generate_with_alertes(self):
        alertes = [
            "Aucun loyer encaissé pour 10 Rue du Test (Paris) en 2025.",
            "Charge de type 'autre' non mappée.",
        ]
        result = _make_result(alertes=alertes)
        pdf = pdf_service.generate(result)
        assert isinstance(pdf, bytes)
        assert pdf[:4] == b"%PDF"

    def test_generate_without_alertes(self):
        result = _make_result(alertes=[])
        pdf = pdf_service.generate(result)
        assert pdf[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# 7. generate() — avec déficit foncier
# ---------------------------------------------------------------------------

class TestGenerateAvecDeficit:
    def test_generate_deficit_foncier(self):
        """Avec déficit, la page 4 inclut la décomposition du déficit."""
        biens = [
            _make_bien("b1", "10 Rue du Test", "Paris",
                       loyers_bruts=3000.0,
                       taxe_fonciere=5000.0,
                       copropriete=4000.0,
                       interets=2000.0),
        ]
        total_charges = 20.0 + 5000.0 + 4000.0  # 9020
        total_interets = 2000.0
        total_revenus = 3000.0
        result = _make_result(
            biens=biens,
            is_deficit=True,
            total_revenus=total_revenus,
            total_charges=total_charges,
            total_interets=total_interets,
        )
        pdf = pdf_service.generate(result)
        assert isinstance(pdf, bytes)
        assert pdf[:4] == b"%PDF"

    def test_generate_large_deficit_capped_imputable(self):
        """Déficit > 10 700 € → résultat fiscal très négatif."""
        biens = [
            _make_bien("b1", "Bien Déficit", "Marseille",
                       loyers_bruts=1000.0,
                       travaux=25000.0,
                       interets=3000.0),
        ]
        result = _make_result(
            biens=biens,
            is_deficit=True,
            total_revenus=1000.0,
            total_charges=25020.0,
            total_interets=3000.0,
        )
        pdf = pdf_service.generate(result)
        assert pdf[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# 8. generate() — associé avec déficit (cases 4BB/4BC)
# ---------------------------------------------------------------------------

class TestGenerateAssocieDeficit:
    def test_associe_cases_4bb_4bc(self):
        """Associé avec résultat négatif → case 4BB et 4BC."""
        associes = [
            _make_associe(
                nom="Jean Associé",
                part_pct=100.0,
                quote_part_resultat=-5000.0,
                case_4ba=0.0,
                case_4bb=3000.0,  # Imputable revenu global
                case_4bc=2000.0,  # Reportable
            )
        ]
        biens = [
            _make_bien("b1", "Rue Déficit", "Nice",
                       loyers_bruts=2000.0, travaux=8000.0)
        ]
        result = _make_result(
            biens=biens,
            associes=associes,
            is_deficit=True,
            total_revenus=2000.0,
            total_charges=8020.0,
        )
        pdf = pdf_service.generate(result)
        assert isinstance(pdf, bytes)
        assert pdf[:4] == b"%PDF"

    def test_associe_case_4bd_anterieurs(self):
        """Associé avec case_4bd > 0 (déficits antérieurs imputés)."""
        associes = [
            _make_associe(
                nom="Marie Dupont",
                part_pct=50.0,
                quote_part_resultat=2000.0,
                case_4ba=2000.0,
                case_4bd=500.0,  # Déficits antérieurs
            )
        ]
        result = _make_result(associes=associes)
        pdf = pdf_service.generate(result)
        assert pdf[:4] == b"%PDF"

    def test_deux_associes_deficit(self):
        """Deux associés en déficit."""
        associes = [
            _make_associe(
                nom="Assoc A",
                part_pct=60.0,
                quote_part_resultat=-3000.0,
                case_4ba=0.0,
                case_4bb=2000.0,
                case_4bc=1000.0,
            ),
            _make_associe(
                nom="Assoc B",
                part_pct=40.0,
                quote_part_resultat=-2000.0,
                case_4ba=0.0,
                case_4bb=1500.0,
                case_4bc=500.0,
            ),
        ]
        result = _make_result(
            associes=associes,
            is_deficit=True,
            total_revenus=3000.0,
            total_charges=9020.0,
        )
        pdf = pdf_service.generate(result)
        assert pdf[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# 9. Méthodes internes — _build_page* retournent des listes non vides
# ---------------------------------------------------------------------------

class TestBuildPages:
    def test_build_page1_returns_list(self):
        result = _make_result()
        elements = pdf_service._build_page1_identification(result)
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_build_page2_returns_list(self):
        result = _make_result()
        elements = pdf_service._build_page2_revenus(result)
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_build_page3_returns_list_with_biens(self):
        result = _make_result()
        elements = pdf_service._build_page3_charges(result)
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_build_page4_returns_list(self):
        result = _make_result()
        elements = pdf_service._build_page4_resultat(result)
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_build_page4_with_deficit(self):
        """Page 4 avec déficit inclut la décomposition."""
        result = _make_result(is_deficit=True, total_revenus=2000.0, total_charges=12000.0)
        elements = pdf_service._build_page4_resultat(result)
        assert len(elements) > 3  # More elements when deficit present

    def test_build_page5_returns_list(self):
        result = _make_result()
        elements = pdf_service._build_page5_repartition(result)
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_build_page5_no_associes(self):
        """Page 5 sans associés retourne quand même une liste valide."""
        result = _make_result(associes=[])
        elements = pdf_service._build_page5_repartition(result)
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_build_alertes_with_alertes(self):
        result = _make_result(alertes=["Alerte test 1", "Alerte test 2"])
        elements = pdf_service._build_alertes(result)
        assert isinstance(elements, list)
        assert len(elements) > 0

    def test_build_alertes_empty(self):
        result = _make_result(alertes=[])
        elements = pdf_service._build_alertes(result)
        assert isinstance(elements, list)
        # Toujours le disclaimer + footer
        assert len(elements) > 0

    def test_page_footer_returns_list(self):
        elements = pdf_service._page_footer()
        assert isinstance(elements, list)
        assert len(elements) > 0


# ---------------------------------------------------------------------------
# 10. _make_table — helper interne
# ---------------------------------------------------------------------------

class TestMakeTable:
    def test_make_table_basic(self):
        from reportlab.platypus import Table
        data = [
            ["Col A", "Col B"],
            ["Val 1", "100 EUR"],
        ]
        table = pdf_service._make_table(data, [80, 60])
        assert isinstance(table, Table)

    def test_make_table_no_highlight_last(self):
        from reportlab.platypus import Table
        data = [
            ["Col A", "Col B"],
            ["Val 1", "100 EUR"],
        ]
        table = pdf_service._make_table(data, [80, 60], highlight_last=False)
        assert isinstance(table, Table)

    def test_make_table_single_row(self):
        from reportlab.platypus import Table
        data = [["Header", "Val"]]
        table = pdf_service._make_table(data, [80, 60], highlight_last=True)
        assert isinstance(table, Table)


# ---------------------------------------------------------------------------
# 11. Adresse / champs SCI non renseignés (None)
# ---------------------------------------------------------------------------

class TestSciFieldsNone:
    def test_generate_sci_siren_none(self):
        result = _make_result()
        result.sci_siren = None
        pdf = pdf_service.generate(result)
        assert pdf[:4] == b"%PDF"

    def test_generate_sci_adresse_none(self):
        result = _make_result()
        result.sci_adresse_siege = None
        pdf = pdf_service.generate(result)
        assert pdf[:4] == b"%PDF"

    def test_generate_sci_capital_none(self):
        result = _make_result()
        result.sci_capital_social = None
        pdf = pdf_service.generate(result)
        assert pdf[:4] == b"%PDF"

    def test_generate_sci_gerant_none(self):
        result = _make_result()
        result.sci_nom_gerant = None
        pdf = pdf_service.generate(result)
        assert pdf[:4] == b"%PDF"


# ---------------------------------------------------------------------------
# 12. Bien sans ville
# ---------------------------------------------------------------------------

class TestBienSansVille:
    def test_generate_bien_ville_vide(self):
        biens = [_make_bien("b1", "10 Rue du Test", "")]  # ville vide
        result = _make_result(biens=biens)
        pdf = pdf_service.generate(result)
        assert pdf[:4] == b"%PDF"

    def test_build_page3_bien_sans_ville(self):
        """Page 3 — bien sans ville ne doit pas lever d'exception."""
        biens = [_make_bien("b1", "10 Rue du Test", "")]
        result = _make_result(biens=biens)
        elements = pdf_service._build_page3_charges(result)
        assert len(elements) > 0


# ---------------------------------------------------------------------------
# 13. Associé avec case_4bb > 0 mais case_4bc == 0 (rapport 2042)
# ---------------------------------------------------------------------------

class TestAssocieReport2042:
    def test_associe_report_only_4bb(self):
        """4BC = 0, seul 4BB est reporté."""
        associes = [
            _make_associe(
                nom="Prenom Nom",
                part_pct=100.0,
                quote_part_resultat=-2000.0,
                case_4ba=0.0,
                case_4bb=2000.0,
                case_4bc=0.0,
            )
        ]
        result = _make_result(associes=associes, is_deficit=True,
                              total_revenus=1000.0, total_charges=4000.0)
        pdf = pdf_service.generate(result)
        assert pdf[:4] == b"%PDF"

    def test_associe_report_only_4bc(self):
        """4BB = 0, seul 4BC est reporté."""
        associes = [
            _make_associe(
                nom="Prenom Nom",
                part_pct=100.0,
                quote_part_resultat=-15000.0,
                case_4ba=0.0,
                case_4bb=0.0,
                case_4bc=15000.0,
            )
        ]
        result = _make_result(associes=associes, is_deficit=True,
                              total_revenus=1000.0, total_charges=17000.0)
        pdf = pdf_service.generate(result)
        assert pdf[:4] == b"%PDF"

    def test_associe_report_no_parts(self):
        """Ni 4BB ni 4BC : affiche '—'."""
        associes = [
            _make_associe(
                nom="Prenom Nom",
                part_pct=100.0,
                quote_part_resultat=-1000.0,
                case_4ba=0.0,
                case_4bb=0.0,
                case_4bc=0.0,
            )
        ]
        result = _make_result(associes=associes, is_deficit=True,
                              total_revenus=500.0, total_charges=2000.0)
        # Should not raise
        elements = pdf_service._build_page5_repartition(result)
        assert len(elements) > 0


# ---------------------------------------------------------------------------
# 14. Plusieurs biens avec ville présente (page 3 label)
# ---------------------------------------------------------------------------

class TestPage3MultipleBiens:
    def test_build_page3_two_biens_avec_ville(self):
        biens = [
            _make_bien("b1", "10 Rue Paris", "Paris"),
            _make_bien("b2", "20 Rue Lyon", "Lyon", loyers_bruts=7000.0),
        ]
        result = _make_result(biens=biens, total_revenus=17800.0)
        elements = pdf_service._build_page3_charges(result)
        assert len(elements) > 0

    def test_generate_three_biens(self):
        biens = [
            _make_bien("b1", "10 Rue Paris", "Paris", 12000.0),
            _make_bien("b2", "20 Rue Lyon", "Lyon", 8400.0, travaux=2000.0),
            _make_bien("b3", "30 Rue Nantes", "Nantes", 6000.0, interets=1500.0),
        ]
        result = _make_result(
            biens=biens,
            total_revenus=26400.0,
            total_charges=60.0 + 280.0 * 3,  # Approx
            total_interets=1500.0,
        )
        pdf = pdf_service.generate(result)
        assert pdf[:4] == b"%PDF"
