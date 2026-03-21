"""PDF generator for the résumé fiscal — multi-page, CERFA 2044 structure."""

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
    KeepTogether,
)

from app.services.resume_fiscal_service import ResumeFiscalResult, BienFiscalDetail, AssocieQuotePart

# ── Font registration (same strategy as quitus_service) ──────────────────

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
_CADRE_BORDER = colors.HexColor("#93c5fd")

_DISCLAIMER_TEXT = (
    "Document de travail — Ne constitue pas le formulaire CERFA officiel"
)


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


class ResumeFiscalPdfService:
    """Generates a multi-page résumé fiscal PDF matching CERFA 2044 structure."""

    def __init__(self):
        styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            "RFTitle", parent=styles["Heading1"],
            fontName=_FONT_BOLD, fontSize=16, spaceAfter=4 * mm, textColor=_DARK,
        )
        self.cadre_title_style = ParagraphStyle(
            "RFCadre", parent=styles["Heading2"],
            fontName=_FONT_BOLD, fontSize=14, spaceBefore=4 * mm, spaceAfter=3 * mm,
            textColor=_ACCENT,
        )
        self.section_style = ParagraphStyle(
            "RFSection", parent=styles["Heading2"],
            fontName=_FONT_BOLD, fontSize=12, spaceBefore=4 * mm, spaceAfter=2 * mm,
            textColor=_ACCENT,
        )
        self.normal_style = ParagraphStyle(
            "RFNormal", parent=styles["Normal"],
            fontName=_FONT_NAME, fontSize=10, leading=14, textColor=_DARK,
        )
        self.small_style = ParagraphStyle(
            "RFSmall", parent=styles["Normal"],
            fontName=_FONT_NAME, fontSize=9, leading=12, textColor=_GRAY,
        )
        self.disclaimer_style = ParagraphStyle(
            "RFDisclaimer", parent=styles["Normal"],
            fontName=_FONT_NAME, fontSize=7, textColor=_GRAY, leading=10,
        )
        self.footer_style = ParagraphStyle(
            "RFFooter", parent=styles["Normal"],
            fontName=_FONT_NAME, fontSize=7, textColor=colors.HexColor("#94a3b8"),
        )
        self.instruction_style = ParagraphStyle(
            "RFInstruction", parent=styles["Normal"],
            fontName=_FONT_BOLD, fontSize=10, textColor=_ACCENT, leading=14,
        )

    def _page_footer(self) -> list:
        """Common page footer with disclaimer."""
        return [
            Spacer(1, 4 * mm),
            Paragraph(f"<i>{_DISCLAIMER_TEXT}</i>", self.disclaimer_style),
        ]

    def _make_cerfa_table(self, data: list, col_widths: list, highlight_last: bool = True) -> Table:
        """Create a consistently styled CERFA-like table."""
        table = Table(data, colWidths=col_widths)
        style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), _DARK),
            ("FONTNAME", (0, 0), (-1, 0), _FONT_BOLD),
            ("FONTNAME", (0, 1), (-1, -1), _FONT_NAME),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
        ]
        if highlight_last and len(data) > 1:
            style_cmds.extend([
                ("BACKGROUND", (0, -1), (-1, -1), _LIGHT_BG),
                ("FONTNAME", (0, -1), (-1, -1), _FONT_BOLD),
            ])
        table.setStyle(TableStyle(style_cmds))
        return table

    # ── Page 1: Identification ──────────────────────────────────────────

    def _build_page1_identification(self, result: ResumeFiscalResult) -> list:
        """Page 1: SCI identification and fiscal year overview."""
        elements: list = []

        elements.append(Paragraph(
            f"Résumé fiscal CERFA 2044 — Exercice {result.annee}",
            self.title_style,
        ))
        elements.append(Paragraph(
            "Déclaration des revenus fonciers — Document de travail",
            self.small_style,
        ))
        elements.append(Spacer(1, 6 * mm))

        # SCI identification table
        elements.append(Paragraph("Identification de la SCI", self.cadre_title_style))

        id_data = [
            ["Champ", "Valeur"],
            ["Dénomination", result.sci_nom],
            ["SIREN", result.sci_siren or "Non renseigné"],
            ["Siège social", result.sci_adresse_siege or "Non renseigné"],
            ["Capital social", _fmt_eur(result.sci_capital_social) if result.sci_capital_social else "Non renseigné"],
            ["Gérant", result.sci_nom_gerant or "Non renseigné"],
            ["Régime fiscal", f"{result.regime_fiscal} — Revenus fonciers" if result.regime_fiscal == "IR" else result.regime_fiscal],
            ["Année fiscale", str(result.annee)],
            ["Nombre de biens", str(result.nb_biens)],
            ["Nombre d'associés", str(result.nb_associes)],
        ]

        id_table = Table(id_data, colWidths=[60 * mm, 105 * mm])
        id_table.setStyle(TableStyle([
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
        ]))
        elements.append(id_table)

        elements.extend(self._page_footer())
        return elements

    # ── Page 2: Cadre 1 — Revenus ────────────────────────────────────

    def _build_page2_revenus(self, result: ResumeFiscalResult) -> list:
        """Page 2: Cadre 1 — Revenus fonciers per bien + total."""
        elements: list = [PageBreak()]

        elements.append(Paragraph(
            "Cadre 1 — Revenus fonciers bruts",
            self.cadre_title_style,
        ))

        col_w_ligne = 18 * mm
        col_w_poste = 80 * mm
        col_w_montant = 42 * mm

        # Per-bien breakdown
        for i, bien in enumerate(result.biens):
            bien_label = f"{bien.adresse}"
            if bien.ville:
                bien_label += f", {bien.ville}"

            elements.append(Paragraph(
                f"Bien {i + 1} : {bien_label}",
                self.section_style,
            ))

            data = [
                ["Ligne", "Poste", "Montant"],
                ["211", "Loyers bruts encaissés", _fmt_eur(bien.ligne_211_loyers_bruts)],
                ["215", "Total recettes", _fmt_eur(bien.ligne_211_loyers_bruts)],
            ]

            elements.append(self._make_cerfa_table(data, [col_w_ligne, col_w_poste, col_w_montant]))
            elements.append(Spacer(1, 3 * mm))

        # Total revenus
        elements.append(Spacer(1, 3 * mm))
        total_data = [
            ["Ligne", "Poste", "Montant"],
            ["211", "TOTAL — Loyers bruts encaissés", _fmt_eur(result.total_revenus)],
            ["215", "TOTAL — Recettes", _fmt_eur(result.total_revenus)],
        ]
        total_table = self._make_cerfa_table(total_data, [col_w_ligne, col_w_poste, col_w_montant])
        total_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), _DARK),
            ("FONTNAME", (0, 0), (-1, -1), _FONT_BOLD),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
            ("BACKGROUND", (0, 1), (-1, -1), _CADRE_BG),
        ]))
        elements.append(total_table)

        elements.extend(self._page_footer())
        return elements

    # ── Page 3: Cadre 2 — Charges déductibles ────────────────────────

    def _build_page3_charges(self, result: ResumeFiscalResult) -> list:
        """Page 3: Cadre 2 — Charges déductibles per bien + total."""
        elements: list = [PageBreak()]

        elements.append(Paragraph(
            "Cadre 2 — Charges déductibles",
            self.cadre_title_style,
        ))

        col_w_ligne = 18 * mm
        col_w_poste = 80 * mm
        col_w_montant = 42 * mm

        for i, bien in enumerate(result.biens):
            bien_label = f"{bien.adresse}"
            if bien.ville:
                bien_label += f", {bien.ville}"

            elements.append(Paragraph(
                f"Bien {i + 1} : {bien_label}",
                self.section_style,
            ))

            data = [
                ["Ligne", "Poste", "Montant"],
                ["221", "Frais d'administration + forfait 20 EUR", _fmt_eur(bien.ligne_215_frais_gestion)],
                ["223", "Assurances (PNO)", _fmt_eur(bien.ligne_220_assurance)],
                ["224", "Travaux / entretien", _fmt_eur(bien.ligne_221_travaux)],
                ["227", "Taxe foncière", _fmt_eur(bien.ligne_224_taxe_fonciere)],
                ["229", "Copropriété", _fmt_eur(bien.ligne_227_copropriete)],
                ["230", "Total charges (hors intérêts)", _fmt_eur(bien.ligne_229_total_charges)],
                ["250", "Intérêts d'emprunt", _fmt_eur(bien.ligne_230_interets_emprunt)],
            ]

            table = self._make_cerfa_table(data, [col_w_ligne, col_w_poste, col_w_montant])
            # Highlight the subtotal row (230)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), _DARK),
                ("FONTNAME", (0, 0), (-1, 0), _FONT_BOLD),
                ("FONTNAME", (0, 1), (-1, -1), _FONT_NAME),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
                # Subtotal (line 230)
                ("BACKGROUND", (0, -2), (-1, -2), _LIGHT_BG),
                ("FONTNAME", (0, -2), (-1, -2), _FONT_BOLD),
                # Intérêts emprunt (separated)
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#fef3c7")),
                ("FONTNAME", (0, -1), (-1, -1), _FONT_BOLD),
            ]))
            elements.append(table)
            elements.append(Spacer(1, 3 * mm))

        # Totals
        elements.append(Spacer(1, 2 * mm))
        total_data = [
            ["Ligne", "Poste", "Montant"],
            ["230", "TOTAL — Charges déductibles", _fmt_eur(result.total_charges)],
            ["250", "TOTAL — Intérêts d'emprunt", _fmt_eur(result.total_interets)],
        ]
        total_table = Table(total_data, colWidths=[col_w_ligne, col_w_poste, col_w_montant])
        total_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), _DARK),
            ("FONTNAME", (0, 0), (-1, -1), _FONT_BOLD),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (0, 0), (0, -1), "CENTER"),
            ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
            ("BACKGROUND", (0, 1), (-1, -1), _CADRE_BG),
        ]))
        elements.append(total_table)

        elements.extend(self._page_footer())
        return elements

    # ── Page 4: Cadre 3 — Résultat + Déficit ─────────────────────────

    def _build_page4_resultat(self, result: ResumeFiscalResult) -> list:
        """Page 4: Cadre 3 — Résultat foncier, déficit decomposition, micro-foncier comparison."""
        elements: list = [PageBreak()]

        elements.append(Paragraph(
            "Cadre 3 — Résultat foncier",
            self.cadre_title_style,
        ))

        col_w_label = 110 * mm
        col_w_amount = 55 * mm

        # Résultat
        res_data = [
            ["Poste", "Montant"],
            ["Ligne 211 — Revenus fonciers bruts", _fmt_eur(result.total_revenus)],
            ["Ligne 230 — Total charges déductibles", f"- {_fmt_eur(result.total_charges)}"],
            ["Ligne 250 — Intérêts d'emprunt", f"- {_fmt_eur(result.total_interets)}"],
            ["Ligne 261 — Résultat foncier", _fmt_eur(result.resultat_global)],
        ]

        res_table = Table(res_data, colWidths=[col_w_label, col_w_amount])
        result_color = _result_color(result.resultat_global)
        res_table.setStyle(TableStyle([
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
        ]))
        elements.append(res_table)

        # Déficit decomposition
        if result.is_deficit:
            elements.append(Spacer(1, 6 * mm))
            elements.append(Paragraph("Décomposition du déficit foncier", self.section_style))
            elements.append(Paragraph(
                "<i>Art. 156-I-3° CGI — Les intérêts d'emprunt ne s'imputent que sur les revenus fonciers.</i>",
                self.disclaimer_style,
            ))
            elements.append(Spacer(1, 2 * mm))

            deficit_data = [
                ["Poste", "Montant"],
                ["Déficit total", _fmt_eur(result.deficit_total)],
                [
                    "Dont intérêts d'emprunt (reportable revenus fonciers, 10 ans)",
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

            deficit_table = Table(deficit_data, colWidths=[col_w_label, col_w_amount])
            deficit_table.setStyle(TableStyle([
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
            ]))
            elements.append(deficit_table)

        # Déficits antérieurs tracker
        if result.deficits_anterieurs:
            elements.append(Spacer(1, 6 * mm))
            elements.append(Paragraph(
                "Suivi des déficits antérieurs reportables (10 ans)",
                self.section_style,
            ))

            da_data = [["Année", "Montant initial", "Imputé", "Solde restant", "Prescription"]]
            for da in result.deficits_anterieurs:
                da_data.append([
                    str(da.annee),
                    _fmt_eur(da.montant_initial),
                    _fmt_eur(da.total_impute),
                    _fmt_eur(da.solde_restant),
                    str(da.annee_prescription),
                ])

            da_col_widths = [25 * mm, 38 * mm, 30 * mm, 38 * mm, 30 * mm]
            da_table = Table(da_data, colWidths=da_col_widths)
            da_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), _DARK),
                ("FONTNAME", (0, 0), (-1, 0), _FONT_BOLD),
                ("FONTNAME", (0, 1), (-1, -1), _FONT_NAME),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
            ]))
            elements.append(da_table)

            if result.total_deficits_anterieurs_imputes > 0:
                elements.append(Spacer(1, 2 * mm))
                elements.append(Paragraph(
                    f"<b>Total déficits antérieurs imputés cette année :</b> {_fmt_eur(result.total_deficits_anterieurs_imputes)}",
                    self.normal_style,
                ))

        # Micro-foncier comparison
        if result.micro_foncier_eligible:
            elements.append(Spacer(1, 6 * mm))
            elements.append(Paragraph("Comparaison Micro-foncier / Réel", self.section_style))

            regime_label = (
                "Régime réel recommandé"
                if result.regime_recommande == "reel"
                else "Micro-foncier recommandé"
            )
            elements.append(Paragraph(
                f"<b>{regime_label}</b> — économie de {_fmt_eur(result.economie_regime_recommande)}",
                self.normal_style,
            ))
            elements.append(Spacer(1, 2 * mm))

            col_w_label_m = 60 * mm
            col_w_val_m = 52.5 * mm

            micro_data = [
                ["", "Micro-foncier", "Régime réel"],
                ["Revenus bruts", _fmt_eur(result.total_revenus), _fmt_eur(result.total_revenus)],
                [
                    "Abattement / Charges",
                    f"- {_fmt_eur(result.micro_foncier_abattement)} (30 %)",
                    f"- {_fmt_eur(result.total_charges + result.total_interets)}",
                ],
                [
                    "Résultat net imposable",
                    _fmt_eur(result.micro_foncier_resultat),
                    _fmt_eur(result.resultat_global),
                ],
            ]

            micro_table = Table(micro_data, colWidths=[col_w_label_m, col_w_val_m, col_w_val_m])
            rec_col = 2 if result.regime_recommande == "reel" else 1
            micro_table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
                ("TEXTCOLOR", (0, 0), (-1, 0), _DARK),
                ("FONTNAME", (0, 0), (-1, 0), _FONT_BOLD),
                ("FONTNAME", (0, 1), (-1, -1), _FONT_NAME),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
                ("FONTNAME", (0, -1), (-1, -1), _FONT_BOLD),
                ("BACKGROUND", (0, -1), (-1, -1), _LIGHT_BG),
                ("BACKGROUND", (rec_col, 0), (rec_col, 0), colors.HexColor("#dbeafe")),
                ("TEXTCOLOR", (rec_col, -1), (rec_col, -1), _GREEN),
            ]))
            elements.append(micro_table)

            elements.append(Spacer(1, 2 * mm))
            elements.append(Paragraph(
                "<i>L'option pour le régime réel est irrévocable pour 3 ans (art. 32-4 CGI).</i>",
                self.disclaimer_style,
            ))

        elements.extend(self._page_footer())
        return elements

    # ── Page 5: Cadre 4 — Répartition par associé ────────────────────

    def _build_page5_associes(self, result: ResumeFiscalResult) -> list:
        """Page 5: Cadre 4 — Quote-parts and cases 2042."""
        elements: list = [PageBreak()]

        elements.append(Paragraph(
            "Cadre 4 — Répartition par associé",
            self.cadre_title_style,
        ))

        if not result.associes:
            elements.append(Paragraph(
                "Aucun associé enregistré — répartition non calculable.",
                self.normal_style,
            ))
            elements.extend(self._page_footer())
            return elements

        # Quote-part table
        qp_data = [["Associé", "Parts (%)", "Quote-part résultat"]]
        for a in result.associes:
            qp_data.append([
                a.nom,
                f"{a.part_pct:.1f} %",
                _fmt_eur(a.quote_part_resultat),
            ])

        qp_table = Table(qp_data, colWidths=[70 * mm, 40 * mm, 55 * mm])
        qp_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), _DARK),
            ("FONTNAME", (0, 0), (-1, 0), _FONT_BOLD),
            ("FONTNAME", (0, 1), (-1, -1), _FONT_NAME),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
        ]))
        elements.append(qp_table)

        # Cases 2042 per associé
        elements.append(Spacer(1, 6 * mm))
        elements.append(Paragraph(
            "Cases à reporter sur la déclaration 2042",
            self.section_style,
        ))

        cases_data = [["Associé", "Case 4BA", "Case 4BB", "Case 4BC", "Case 4BD"]]
        for a in result.associes:
            cases_data.append([
                a.nom,
                _fmt_eur(a.case_4ba) if a.case_4ba > 0 else "—",
                _fmt_eur(a.case_4bb) if a.case_4bb > 0 else "—",
                _fmt_eur(a.case_4bc) if a.case_4bc > 0 else "—",
                _fmt_eur(a.case_4bd) if a.case_4bd > 0 else "—",
            ])

        cases_col_w = [50 * mm, 28 * mm, 28 * mm, 28 * mm, 28 * mm]
        cases_table = Table(cases_data, colWidths=cases_col_w)
        cases_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), _DARK),
            ("FONTNAME", (0, 0), (-1, 0), _FONT_BOLD),
            ("FONTNAME", (0, 1), (-1, -1), _FONT_NAME),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
        ]))
        elements.append(cases_table)

        # Case legend
        elements.append(Spacer(1, 4 * mm))
        legends = [
            "<b>Case 4BA</b> : Bénéfice foncier imposable",
            "<b>Case 4BB</b> : Déficit imputable sur le revenu global (max 10 700 EUR)",
            "<b>Case 4BC</b> : Déficit reportable sur les revenus fonciers (10 ans)",
            "<b>Case 4BD</b> : Déficits antérieurs non encore imputés",
        ]
        for legend in legends:
            elements.append(Paragraph(legend, self.small_style))

        # Instruction per associé
        elements.append(Spacer(1, 6 * mm))
        for a in result.associes:
            if a.case_4ba > 0:
                elements.append(Paragraph(
                    f"<b>{a.nom}</b> : Reportez {_fmt_eur(a.case_4ba)} en case 4BA de votre déclaration 2042",
                    self.instruction_style,
                ))
            elif a.case_4bb > 0 or a.case_4bc > 0:
                parts = []
                if a.case_4bb > 0:
                    parts.append(f"{_fmt_eur(a.case_4bb)} en case 4BB")
                if a.case_4bc > 0:
                    parts.append(f"{_fmt_eur(a.case_4bc)} en case 4BC")
                elements.append(Paragraph(
                    f"<b>{a.nom}</b> : Reportez {' et '.join(parts)} de votre déclaration 2042",
                    self.instruction_style,
                ))

        elements.extend(self._page_footer())
        return elements

    # ── Alertes page ─────────────────────────────────────────────────

    def _build_alertes(self, result: ResumeFiscalResult) -> list:
        """Alertes, disclaimers, and generation metadata."""
        elements: list = []

        if result.alertes:
            elements.append(Spacer(1, 6 * mm))
            elements.append(Paragraph("Alertes et données manquantes", self.section_style))
            for alerte in result.alertes:
                elements.append(Paragraph(f"  - {alerte}", self.normal_style))
            elements.append(Spacer(1, 4 * mm))

        elements.append(Spacer(1, 8 * mm))
        elements.append(Paragraph(
            "<i>Ce document est un résumé simplifié du calcul foncier structuré selon le formulaire "
            "CERFA 2044, généré par GérerSCI. Il ne constitue pas le formulaire officiel CERFA 2044 "
            "et ne se substitue pas aux obligations déclaratives auprès de l'administration "
            "fiscale. Les numéros de lignes sont fournis à titre indicatif pour faciliter "
            "le report sur votre déclaration. Consultez votre comptable pour la déclaration "
            "définitive.</i>",
            self.disclaimer_style,
        ))

        elements.append(Spacer(1, 4 * mm))
        elements.append(Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} via GérerSCI (gerersci.fr)",
            self.footer_style,
        ))

        return elements

    # ── Main generate method ─────────────────────────────────────────

    def generate(self, result: ResumeFiscalResult) -> bytes:
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

        # Page 2: Cadre 1 — Revenus
        if result.biens:
            elements.extend(self._build_page2_revenus(result))

        # Page 3: Cadre 2 — Charges
        if result.biens:
            elements.extend(self._build_page3_charges(result))

        # Page 4: Cadre 3 — Résultat + Déficit
        elements.extend(self._build_page4_resultat(result))

        # Page 5: Cadre 4 — Répartition par associé
        elements.extend(self._build_page5_associes(result))

        # Final: Alertes
        elements.extend(self._build_alertes(result))

        doc.build(elements)
        buffer.seek(0)
        return buffer.read()


class Report2042PdfService:
    """Generates a 1-page PDF report for a specific associé showing their cases 2042."""

    def generate(
        self,
        result: ResumeFiscalResult,
        associe: AssocieQuotePart,
    ) -> bytes:
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=18 * mm,
            rightMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "R2042Title", parent=styles["Heading1"],
            fontName=_FONT_BOLD, fontSize=16, spaceAfter=4 * mm, textColor=_DARK,
        )
        section_style = ParagraphStyle(
            "R2042Section", parent=styles["Heading2"],
            fontName=_FONT_BOLD, fontSize=13, spaceBefore=4 * mm, spaceAfter=3 * mm,
            textColor=_ACCENT,
        )
        normal_style = ParagraphStyle(
            "R2042Normal", parent=styles["Normal"],
            fontName=_FONT_NAME, fontSize=10, leading=14, textColor=_DARK,
        )
        instruction_style = ParagraphStyle(
            "R2042Instruction", parent=styles["Normal"],
            fontName=_FONT_BOLD, fontSize=11, textColor=_ACCENT, leading=16,
            spaceBefore=3 * mm,
        )
        disclaimer_style = ParagraphStyle(
            "R2042Disclaimer", parent=styles["Normal"],
            fontName=_FONT_NAME, fontSize=7, textColor=_GRAY, leading=10,
        )
        footer_style = ParagraphStyle(
            "R2042Footer", parent=styles["Normal"],
            fontName=_FONT_NAME, fontSize=7, textColor=colors.HexColor("#94a3b8"),
        )

        elements: list = []

        # Header
        elements.append(Paragraph(
            f"Report individuel 2042 — Exercice {result.annee}",
            title_style,
        ))
        elements.append(Paragraph(
            "Quote-part des revenus fonciers à reporter sur la déclaration 2042",
            ParagraphStyle("R2042Sub", parent=styles["Normal"],
                          fontName=_FONT_NAME, fontSize=10, textColor=_GRAY, spaceAfter=6 * mm),
        ))

        # SCI info
        elements.append(Paragraph("SCI", section_style))
        sci_data = [
            ["Champ", "Valeur"],
            ["Dénomination", result.sci_nom],
            ["SIREN", result.sci_siren or "Non renseigné"],
        ]
        sci_table = Table(sci_data, colWidths=[50 * mm, 115 * mm])
        sci_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
            ("FONTNAME", (0, 0), (-1, 0), _FONT_BOLD),
            ("FONTNAME", (0, 1), (0, -1), _FONT_BOLD),
            ("FONTNAME", (1, 1), (1, -1), _FONT_NAME),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
            ("BACKGROUND", (0, 1), (0, -1), _LIGHT_BG),
        ]))
        elements.append(sci_table)

        # Associé info
        elements.append(Paragraph("Associé", section_style))
        assoc_data = [
            ["Champ", "Valeur"],
            ["Nom", associe.nom],
            ["Email", associe.email or "Non renseigné"],
            ["Parts", f"{associe.part_pct:.1f} %"],
            ["Quote-part résultat", _fmt_eur(associe.quote_part_resultat)],
        ]
        assoc_table = Table(assoc_data, colWidths=[50 * mm, 115 * mm])
        assoc_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
            ("FONTNAME", (0, 0), (-1, 0), _FONT_BOLD),
            ("FONTNAME", (0, 1), (0, -1), _FONT_BOLD),
            ("FONTNAME", (1, 1), (1, -1), _FONT_NAME),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
            ("BACKGROUND", (0, 1), (0, -1), _LIGHT_BG),
        ]))
        elements.append(assoc_table)

        # Cases 2042
        elements.append(Paragraph("Cases à reporter sur la déclaration 2042", section_style))

        cases = [
            ("Case 4BA", "Bénéfice foncier", associe.case_4ba),
            ("Case 4BB", "Déficit imputable sur le revenu global", associe.case_4bb),
            ("Case 4BC", "Déficit reportable sur les revenus fonciers", associe.case_4bc),
            ("Case 4BD", "Déficits antérieurs non encore imputés", associe.case_4bd),
        ]

        cases_data = [["Case", "Description", "Montant"]]
        for case_name, desc, amount in cases:
            cases_data.append([
                case_name,
                desc,
                _fmt_eur(amount) if amount > 0 else "—",
            ])

        cases_table = Table(cases_data, colWidths=[30 * mm, 95 * mm, 40 * mm])
        cases_style_cmds = [
            ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), _DARK),
            ("FONTNAME", (0, 0), (-1, 0), _FONT_BOLD),
            ("FONTNAME", (0, 1), (0, -1), _FONT_BOLD),
            ("FONTNAME", (1, 1), (-1, -1), _FONT_NAME),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (-1, 0), (-1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
        ]
        # Highlight active cases
        for i, (_, _, amount) in enumerate(cases, start=1):
            if amount > 0:
                cases_style_cmds.extend([
                    ("BACKGROUND", (0, i), (-1, i), _CADRE_BG),
                    ("FONTNAME", (0, i), (-1, i), _FONT_BOLD),
                ])
        cases_table.setStyle(TableStyle(cases_style_cmds))
        elements.append(cases_table)

        # Instructions
        elements.append(Spacer(1, 6 * mm))
        elements.append(Paragraph("Instructions", section_style))

        if associe.case_4ba > 0:
            elements.append(Paragraph(
                f"Reportez <b>{_fmt_eur(associe.case_4ba)}</b> en case <b>4BA</b> de votre déclaration 2042.",
                instruction_style,
            ))
        if associe.case_4bb > 0:
            elements.append(Paragraph(
                f"Reportez <b>{_fmt_eur(associe.case_4bb)}</b> en case <b>4BB</b> de votre déclaration 2042.",
                instruction_style,
            ))
        if associe.case_4bc > 0:
            elements.append(Paragraph(
                f"Reportez <b>{_fmt_eur(associe.case_4bc)}</b> en case <b>4BC</b> de votre déclaration 2042.",
                instruction_style,
            ))
        if associe.case_4bd > 0:
            elements.append(Paragraph(
                f"Reportez <b>{_fmt_eur(associe.case_4bd)}</b> en case <b>4BD</b> de votre déclaration 2042.",
                instruction_style,
            ))

        if all(getattr(associe, f"case_{c}") == 0 for c in ["4ba", "4bb", "4bc", "4bd"]):
            elements.append(Paragraph(
                "Aucun montant à reporter — résultat foncier nul.",
                normal_style,
            ))

        # Disclaimers
        elements.append(Spacer(1, 10 * mm))
        elements.append(Paragraph(
            f"<i>{_DISCLAIMER_TEXT}</i>",
            disclaimer_style,
        ))
        elements.append(Spacer(1, 2 * mm))
        elements.append(Paragraph(
            "<i>Ce document est un aide-mémoire pour faciliter le report des revenus fonciers "
            "sur votre déclaration 2042. Il ne se substitue pas aux obligations déclaratives. "
            "Consultez votre comptable pour la déclaration définitive.</i>",
            disclaimer_style,
        ))

        elements.append(Spacer(1, 4 * mm))
        elements.append(Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} via GérerSCI (gerersci.fr)",
            footer_style,
        ))

        doc.build(elements)
        buffer.seek(0)
        return buffer.read()
