"""Service de generation PDF de la Declaration 2072 pour SCI a l'IR.

Le CERFA 2072-S est la declaration annuelle de resultats des SCI non soumises a l'IS.
Ce service genere un document de travail structure selon les cadres du formulaire officiel.
"""

from __future__ import annotations

import os
from datetime import datetime
from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from app.services.resume_fiscal_service import (
    ResumeFiscalResult,
    BienFiscalDetail,
    AssocieQuotePart,
)

# ── Font registration (same strategy as quitus_service / resume_fiscal_pdf_service) ──

_DEJAVU_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/TTF/DejaVuSans.ttf",
]
_DEJAVU_BOLD_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
]


def _register_fonts() -> tuple[str, str]:
    """Register a TTF font that supports accented characters."""
    font_name = "Helvetica"
    font_bold = "Helvetica-Bold"

    for path in _DEJAVU_PATHS:
        if os.path.isfile(path):
            try:
                pdfmetrics.registerFont(TTFont("DejaVuSans", path))
                font_name = "DejaVuSans"
            except Exception:
                pass
            break

    for path in _DEJAVU_BOLD_PATHS:
        if os.path.isfile(path):
            try:
                pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", path))
                font_bold = "DejaVuSans-Bold"
            except Exception:
                pass
            break

    if font_name == "Helvetica":
        import reportlab

        rl_fonts_dir = os.path.join(os.path.dirname(reportlab.__file__), "fonts")
        vera_path = os.path.join(rl_fonts_dir, "Vera.ttf")
        vera_bold_path = os.path.join(rl_fonts_dir, "VeraBd.ttf")

        if os.path.isfile(vera_path):
            try:
                pdfmetrics.registerFont(TTFont("Vera", vera_path))
                font_name = "Vera"
            except Exception:
                pass

        if os.path.isfile(vera_bold_path):
            try:
                pdfmetrics.registerFont(TTFont("VeraBd", vera_bold_path))
                font_bold = "VeraBd"
            except Exception:
                pass

    return font_name, font_bold


_FONT_NAME, _FONT_BOLD = _register_fonts()

# ── Color palette ────────────────────────────────────────────────────────

_DARK = colors.HexColor("#1e293b")
_GRAY = colors.HexColor("#64748b")
_LIGHT_BG = colors.HexColor("#f8fafc")
_HEADER_BG = colors.HexColor("#f1f5f9")
_BORDER = colors.HexColor("#e2e8f0")
_ACCENT = colors.HexColor("#1e40af")
_GREEN = colors.HexColor("#166534")
_RED = colors.HexColor("#991b1b")
_CADRE_BG = colors.HexColor("#eff6ff")


def _fmt_eur(amount: float) -> str:
    """Format as French currency: 1 234,56 EUR."""
    sign = "-" if amount < 0 else ""
    abs_val = abs(amount)
    formatted = f"{abs_val:,.2f}".replace(",", " ").replace(".", ",")
    return f"{sign}{formatted} EUR"


def _result_color(value: float) -> colors.Color:
    if value > 0:
        return _GREEN
    if value < 0:
        return _RED
    return _DARK


class Declaration2072PdfService:
    """Generates a multi-page Declaration 2072-S PDF for SCI a l'IR."""

    def __init__(self):
        styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            "D2072Title",
            parent=styles["Heading1"],
            fontName=_FONT_BOLD,
            fontSize=16,
            spaceAfter=4 * mm,
            textColor=_DARK,
        )
        self.cadre_title_style = ParagraphStyle(
            "D2072Cadre",
            parent=styles["Heading2"],
            fontName=_FONT_BOLD,
            fontSize=14,
            spaceBefore=4 * mm,
            spaceAfter=3 * mm,
            textColor=_ACCENT,
        )
        self.section_style = ParagraphStyle(
            "D2072Section",
            parent=styles["Heading2"],
            fontName=_FONT_BOLD,
            fontSize=12,
            spaceBefore=4 * mm,
            spaceAfter=2 * mm,
            textColor=_ACCENT,
        )
        self.normal_style = ParagraphStyle(
            "D2072Normal",
            parent=styles["Normal"],
            fontName=_FONT_NAME,
            fontSize=10,
            leading=14,
            textColor=_DARK,
        )
        self.small_style = ParagraphStyle(
            "D2072Small",
            parent=styles["Normal"],
            fontName=_FONT_NAME,
            fontSize=9,
            leading=12,
            textColor=_GRAY,
        )
        self.disclaimer_style = ParagraphStyle(
            "D2072Disclaimer",
            parent=styles["Normal"],
            fontName=_FONT_NAME,
            fontSize=7,
            textColor=_GRAY,
            leading=10,
        )
        self.footer_style = ParagraphStyle(
            "D2072Footer",
            parent=styles["Normal"],
            fontName=_FONT_NAME,
            fontSize=7,
            textColor=colors.HexColor("#94a3b8"),
        )

    def _make_table(
        self,
        data: list,
        col_widths: list,
        highlight_last: bool = True,
    ) -> Table:
        """Create a consistently styled table."""
        table = Table(data, colWidths=col_widths)
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), _DARK),
            ("FONTNAME", (0, 0), (-1, 0), _FONT_BOLD),
            ("FONTNAME", (0, 1), (-1, -1), _FONT_NAME),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
        ]
        if highlight_last and len(data) > 1:
            style_cmds.extend(
                [
                    ("BACKGROUND", (0, -1), (-1, -1), _LIGHT_BG),
                    ("FONTNAME", (0, -1), (-1, -1), _FONT_BOLD),
                ]
            )
        table.setStyle(TableStyle(style_cmds))
        return table

    def _page_footer(self) -> list:
        return [
            Spacer(1, 4 * mm),
            Paragraph(
                "<i>Document de travail — Ne constitue pas le formulaire CERFA 2072-S officiel</i>",
                self.disclaimer_style,
            ),
        ]

    # ── Page 1: Identification SCI ───────────────────────────────────

    def _build_page1_identification(self, result: ResumeFiscalResult) -> list:
        elements: list = []

        elements.append(
            Paragraph(
                f"Déclaration 2072-S — Exercice {result.annee}",
                self.title_style,
            )
        )
        elements.append(
            Paragraph(
                "Déclaration de résultats des sociétés immobilières non soumises à l'IS",
                self.small_style,
            )
        )
        elements.append(Spacer(1, 6 * mm))

        # Cadre I: Identification
        elements.append(
            Paragraph("Cadre I — Identification de la SCI", self.cadre_title_style)
        )

        id_data = [
            ["Champ", "Valeur"],
            ["Raison sociale", result.sci_nom],
            ["SIREN", result.sci_siren or "Non renseigne"],
            [
                "Adresse du siege social",
                result.sci_adresse_siege or "Non renseigne",
            ],
            [
                "Capital social",
                _fmt_eur(result.sci_capital_social)
                if result.sci_capital_social
                else "Non renseigne",
            ],
            ["Gerant", result.sci_nom_gerant or "Non renseigne"],
            ["Régime fiscal", "IR — Revenus fonciers (art. 8 CGI)"],
            ["Exercice", f"01/01/{result.annee} au 31/12/{result.annee}"],
            ["Nombre d'immeubles", str(result.nb_biens)],
            ["Nombre d'associes", str(result.nb_associes)],
        ]

        id_table = Table(id_data, colWidths=[60 * mm, 105 * mm])
        id_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
                    ("TEXTCOLOR", (0, 0), (-1, 0), _DARK),
                    ("FONTNAME", (0, 0), (-1, 0), _FONT_BOLD),
                    ("FONTNAME", (0, 1), (0, -1), _FONT_BOLD),
                    ("FONTNAME", (1, 1), (1, -1), _FONT_NAME),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
                    ("BACKGROUND", (0, 1), (0, -1), _LIGHT_BG),
                ]
            )
        )
        elements.append(id_table)

        elements.extend(self._page_footer())
        return elements

    # ── Page 2: Cadre II — Revenus fonciers bruts par immeuble ───────

    def _build_page2_revenus(self, result: ResumeFiscalResult) -> list:
        elements: list = [PageBreak()]

        elements.append(
            Paragraph(
                "Cadre II — Revenus fonciers bruts par immeuble",
                self.cadre_title_style,
            )
        )

        col_w = [10 * mm, 70 * mm, 35 * mm, 45 * mm]

        data = [["N.", "Immeuble", "Ville", "Loyers bruts"]]
        for i, bien in enumerate(result.biens):
            data.append(
                [
                    str(i + 1),
                    bien.adresse,
                    bien.ville or "",
                    _fmt_eur(bien.ligne_211_loyers_bruts),
                ]
            )

        # Total row
        data.append(
            ["", "TOTAL REVENUS FONCIERS BRUTS", "", _fmt_eur(result.total_revenus)]
        )

        elements.append(self._make_table(data, col_w, highlight_last=True))
        elements.extend(self._page_footer())
        return elements

    # ── Page 3: Cadre III — Charges deductibles par immeuble ─────────

    def _build_page3_charges(self, result: ResumeFiscalResult) -> list:
        elements: list = [PageBreak()]

        elements.append(
            Paragraph(
                "Cadre III — Charges déductibles par immeuble",
                self.cadre_title_style,
            )
        )

        for i, bien in enumerate(result.biens):
            bien_label = bien.adresse
            if bien.ville:
                bien_label += f", {bien.ville}"

            elements.append(
                Paragraph(f"Immeuble {i + 1} : {bien_label}", self.section_style)
            )

            col_w = [80 * mm, 45 * mm]
            charges_total = (
                bien.ligne_229_total_charges + bien.ligne_230_interets_emprunt
            )

            data = [
                ["Poste", "Montant"],
                ["Frais d'administration (forfait 20 EUR)", _fmt_eur(bien.ligne_215_frais_gestion)],
                ["Assurances (PNO)", _fmt_eur(bien.ligne_220_assurance)],
                ["Travaux d'entretien et réparation", _fmt_eur(bien.ligne_221_travaux)],
                ["Taxe foncière", _fmt_eur(bien.ligne_224_taxe_fonciere)],
                ["Charges de copropriété", _fmt_eur(bien.ligne_227_copropriete)],
                ["Intérêts d'emprunt", _fmt_eur(bien.ligne_230_interets_emprunt)],
                ["Total charges déductibles", _fmt_eur(charges_total)],
            ]

            table = self._make_table(data, col_w, highlight_last=True)
            elements.append(table)
            elements.append(Spacer(1, 3 * mm))

        # Aggregate totals
        elements.append(Spacer(1, 2 * mm))
        total_all_charges = result.total_charges + result.total_interets
        agg_data = [
            ["Poste", "Montant"],
            ["TOTAL charges hors intérêts", _fmt_eur(result.total_charges)],
            ["TOTAL intérêts d'emprunt", _fmt_eur(result.total_interets)],
            ["TOTAL CHARGES DÉDUCTIBLES", _fmt_eur(total_all_charges)],
        ]
        agg_table = Table(agg_data, colWidths=[80 * mm, 45 * mm])
        agg_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
                    ("TEXTCOLOR", (0, 0), (-1, 0), _DARK),
                    ("FONTNAME", (0, 0), (-1, -1), _FONT_BOLD),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
                    ("BACKGROUND", (0, 1), (-1, -1), _CADRE_BG),
                ]
            )
        )
        elements.append(agg_table)
        elements.extend(self._page_footer())
        return elements

    # ── Page 4: Cadre IV — Resultat fiscal de la SCI ─────────────────

    def _build_page4_resultat(self, result: ResumeFiscalResult) -> list:
        elements: list = [PageBreak()]

        elements.append(
            Paragraph(
                "Cadre IV — Détermination du résultat fiscal",
                self.cadre_title_style,
            )
        )

        col_w = [100 * mm, 60 * mm]
        total_all_charges = result.total_charges + result.total_interets

        res_data = [
            ["Poste", "Montant"],
            ["Revenus fonciers bruts (Cadre II)", _fmt_eur(result.total_revenus)],
            ["Charges déductibles (Cadre III)", f"- {_fmt_eur(total_all_charges)}"],
            ["RÉSULTAT FISCAL DE LA SCI", _fmt_eur(result.resultat_global)],
        ]

        res_table = Table(res_data, colWidths=col_w)
        result_color = _result_color(result.resultat_global)
        res_table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
                    ("TEXTCOLOR", (0, 0), (-1, 0), _DARK),
                    ("FONTNAME", (0, 0), (-1, 0), _FONT_BOLD),
                    ("FONTNAME", (0, 1), (-1, -1), _FONT_NAME),
                    ("FONTSIZE", (0, 0), (-1, -1), 10),
                    ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
                    ("BACKGROUND", (0, -1), (-1, -1), _LIGHT_BG),
                    ("FONTNAME", (0, -1), (-1, -1), _FONT_BOLD),
                    ("TEXTCOLOR", (1, -1), (1, -1), result_color),
                ]
            )
        )
        elements.append(res_table)

        # Deficit decomposition
        if result.is_deficit:
            elements.append(Spacer(1, 6 * mm))
            elements.append(
                Paragraph("Décomposition du déficit foncier", self.section_style)
            )
            elements.append(
                Paragraph(
                    "<i>Art. 156-I-3. CGI — Les intérêts d'emprunt ne s'imputent que sur les revenus fonciers.</i>",
                    self.disclaimer_style,
                )
            )
            elements.append(Spacer(1, 2 * mm))

            deficit_data = [
                ["Poste", "Montant"],
                ["Déficit total", _fmt_eur(result.deficit_total)],
                [
                    "Dont intérêts d'emprunt (reportable revenus fonciers)",
                    _fmt_eur(result.deficit_interets_emprunt),
                ],
                [
                    "Dont charges hors intérêts — imputable revenu global (max 10 700 EUR)",
                    _fmt_eur(result.deficit_imputable_revenu_global),
                ],
                [
                    "Excédent reportable sur revenus fonciers (10 ans)",
                    _fmt_eur(result.deficit_reportable_foncier),
                ],
            ]

            deficit_table = self._make_table(deficit_data, col_w, highlight_last=False)
            deficit_table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
                        ("TEXTCOLOR", (0, 0), (-1, 0), _DARK),
                        ("FONTNAME", (0, 0), (-1, 0), _FONT_BOLD),
                        ("FONTNAME", (0, 1), (-1, -1), _FONT_NAME),
                        ("FONTSIZE", (0, 0), (-1, -1), 9),
                        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
                        ("FONTNAME", (0, 1), (-1, 1), _FONT_BOLD),
                        ("BACKGROUND", (0, 1), (-1, 1), _LIGHT_BG),
                        ("TEXTCOLOR", (1, 1), (1, 1), _RED),
                    ]
                )
            )
            elements.append(deficit_table)

        elements.extend(self._page_footer())
        return elements

    # ── Page 5: Cadre V — Repartition entre associes ─────────────────

    def _build_page5_repartition(self, result: ResumeFiscalResult) -> list:
        elements: list = [PageBreak()]

        elements.append(
            Paragraph(
                "Cadre V — Répartition du résultat entre les associés",
                self.cadre_title_style,
            )
        )

        if not result.associes:
            elements.append(
                Paragraph(
                    "Aucun associé enregistré — répartition non calculable.",
                    self.normal_style,
                )
            )
            elements.extend(self._page_footer())
            return elements

        # Repartition table
        col_w = [55 * mm, 25 * mm, 40 * mm, 40 * mm]
        rp_data = [["Associe", "Parts (%)", "Quote-part resultat", "A reporter sur 2042"]]
        for a in result.associes:
            if a.quote_part_resultat >= 0:
                report_2042 = f"4BA: {_fmt_eur(a.case_4ba)}"
            else:
                parts = []
                if a.case_4bb > 0:
                    parts.append(f"4BB: {_fmt_eur(a.case_4bb)}")
                if a.case_4bc > 0:
                    parts.append(f"4BC: {_fmt_eur(a.case_4bc)}")
                report_2042 = " / ".join(parts) if parts else "—"

            rp_data.append(
                [
                    a.nom,
                    f"{a.part_pct:.1f} %",
                    _fmt_eur(a.quote_part_resultat),
                    report_2042,
                ]
            )

        rp_table = self._make_table(rp_data, col_w, highlight_last=False)
        elements.append(rp_table)

        # Detail per associe
        elements.append(Spacer(1, 6 * mm))
        elements.append(
            Paragraph(
                "Detail des cases 2042 par associe",
                self.section_style,
            )
        )

        cases_data = [["Associe", "Case 4BA", "Case 4BB", "Case 4BC", "Case 4BD"]]
        for a in result.associes:
            cases_data.append(
                [
                    a.nom,
                    _fmt_eur(a.case_4ba) if a.case_4ba > 0 else "—",
                    _fmt_eur(a.case_4bb) if a.case_4bb > 0 else "—",
                    _fmt_eur(a.case_4bc) if a.case_4bc > 0 else "—",
                    _fmt_eur(a.case_4bd) if a.case_4bd > 0 else "—",
                ]
            )

        cases_col_w = [50 * mm, 28 * mm, 28 * mm, 28 * mm, 28 * mm]
        cases_table = self._make_table(cases_data, cases_col_w, highlight_last=False)
        elements.append(cases_table)

        # Legend
        elements.append(Spacer(1, 4 * mm))
        legends = [
            "<b>Case 4BA</b> : Bénéfice foncier imposable",
            "<b>Case 4BB</b> : Déficit imputable sur le revenu global (max 10 700 EUR)",
            "<b>Case 4BC</b> : Déficit reportable sur les revenus fonciers (10 ans)",
            "<b>Case 4BD</b> : Déficits antérieurs non encore imputés",
        ]
        for legend in legends:
            elements.append(Paragraph(legend, self.small_style))

        elements.extend(self._page_footer())
        return elements

    # ── Final: Alertes + disclaimers ─────────────────────────────────

    def _build_alertes(self, result: ResumeFiscalResult) -> list:
        elements: list = []

        if result.alertes:
            elements.append(Spacer(1, 6 * mm))
            elements.append(
                Paragraph("Alertes et données manquantes", self.section_style)
            )
            for alerte in result.alertes:
                elements.append(Paragraph(f"  - {alerte}", self.normal_style))
            elements.append(Spacer(1, 4 * mm))

        elements.append(Spacer(1, 8 * mm))
        elements.append(
            Paragraph(
                "<i>Ce document est un resume simplifie structure selon le formulaire "
                "CERFA 2072-S (déclaration de résultats des sociétés immobilières non soumises "
                "a l'IS), genere par GererSCI. Il ne constitue pas le formulaire officiel "
                "et ne se substitue pas aux obligations declaratives aupres de l'administration "
                "fiscale. Consultez votre comptable pour la declaration definitive.</i>",
                self.disclaimer_style,
            )
        )

        elements.append(Spacer(1, 4 * mm))
        elements.append(
            Paragraph(
                f"Genere le {datetime.now().strftime('%d/%m/%Y a %H:%M')} via GererSCI (gerersci.fr)",
                self.footer_style,
            )
        )

        return elements

    # ── Main generate method ─────────────────────────────────────────

    def generate(self, result: ResumeFiscalResult) -> bytes:
        """Generate the full Declaration 2072-S PDF.

        Args:
            result: A fully populated ResumeFiscalResult from ResumeFiscalService.

        Returns:
            PDF bytes ready to stream.
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
        )

        elements: list = []

        # Page 1: Identification
        elements.extend(self._build_page1_identification(result))

        # Page 2: Revenus fonciers bruts
        if result.biens:
            elements.extend(self._build_page2_revenus(result))

        # Page 3: Charges deductibles
        if result.biens:
            elements.extend(self._build_page3_charges(result))

        # Page 4: Resultat fiscal
        elements.extend(self._build_page4_resultat(result))

        # Page 5: Repartition entre associes
        elements.extend(self._build_page5_repartition(result))

        # Alertes + disclaimers
        elements.extend(self._build_alertes(result))

        doc.build(elements)
        buffer.seek(0)
        return buffer.read()
