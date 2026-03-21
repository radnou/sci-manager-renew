"""PDF generator for the résumé fiscal — multi-page, CERFA 2044 line mapping."""

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

from app.services.resume_fiscal_service import ResumeFiscalResult, BienFiscalDetail

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
    """Generates a multi-page résumé fiscal PDF from a ResumeFiscalResult."""

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

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "RFTitle",
            parent=styles["Heading1"],
            fontName=_FONT_BOLD,
            fontSize=16,
            spaceAfter=4 * mm,
            textColor=_DARK,
        )
        subtitle_style = ParagraphStyle(
            "RFSubtitle",
            parent=styles["Normal"],
            fontName=_FONT_NAME,
            fontSize=10,
            spaceAfter=3 * mm,
            textColor=_GRAY,
        )
        section_style = ParagraphStyle(
            "RFSection",
            parent=styles["Heading2"],
            fontName=_FONT_BOLD,
            fontSize=13,
            spaceBefore=6 * mm,
            spaceAfter=3 * mm,
            textColor=_ACCENT,
        )
        normal_style = ParagraphStyle(
            "RFNormal",
            parent=styles["Normal"],
            fontName=_FONT_NAME,
            fontSize=10,
            leading=14,
            textColor=_DARK,
        )
        disclaimer_style = ParagraphStyle(
            "RFDisclaimer",
            parent=styles["Normal"],
            fontName=_FONT_NAME,
            fontSize=8,
            textColor=_GRAY,
            leading=11,
        )
        footer_style = ParagraphStyle(
            "RFFooter",
            parent=styles["Normal"],
            fontName=_FONT_NAME,
            fontSize=8,
            textColor=colors.HexColor("#94a3b8"),
        )

        elements: list = []

        # ── PAGE 1: Synthèse ──────────────────────────────────────────

        elements.append(Paragraph(
            f"Résumé fiscal — Exercice {result.annee}",
            title_style,
        ))
        elements.append(Paragraph(
            "Déclaration des revenus fonciers — CERFA 2044 (résumé simplifié)",
            subtitle_style,
        ))

        # SCI info
        sci_info_parts = [f"<b>SCI :</b> {result.sci_nom}"]
        if result.sci_siren:
            sci_info_parts.append(f"<b>SIREN :</b> {result.sci_siren}")
        sci_info_parts.append(f"<b>Régime :</b> {result.regime_fiscal}")
        elements.append(Paragraph(" — ".join(sci_info_parts), normal_style))
        elements.append(Spacer(1, 6 * mm))

        # Summary table
        elements.append(Paragraph("Synthèse globale", section_style))

        col_w_label = 110 * mm
        col_w_amount = 55 * mm

        summary_data = [
            ["Poste", "Montant"],
            ["Ligne 211 — Revenus fonciers bruts", _fmt_eur(result.total_revenus)],
            ["Ligne 229 — Total charges déductibles", f"- {_fmt_eur(result.total_charges)}"],
            ["Ligne 230 — Intérêts d'emprunt", f"- {_fmt_eur(result.total_interets)}"],
            ["Ligne 240 — Résultat fiscal net", _fmt_eur(result.resultat_global)],
        ]

        summary_table = Table(summary_data, colWidths=[col_w_label, col_w_amount])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), _DARK),
            ("FONTNAME", (0, 0), (-1, 0), _FONT_BOLD),
            ("FONTNAME", (0, 1), (0, -1), _FONT_NAME),
            ("FONTNAME", (1, 1), (1, -1), _FONT_NAME),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
            ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
            # Result row highlight
            ("BACKGROUND", (0, -1), (-1, -1), _LIGHT_BG),
            ("FONTNAME", (0, -1), (-1, -1), _FONT_BOLD),
            ("TEXTCOLOR", (1, -1), (1, -1), _result_color(result.resultat_global)),
        ]))
        elements.append(summary_table)

        # Nombre de biens
        elements.append(Spacer(1, 4 * mm))
        elements.append(Paragraph(
            f"<b>Nombre de biens :</b> {len(result.biens)}",
            normal_style,
        ))

        # Quote-parts des associés
        if result.associes:
            elements.append(Spacer(1, 4 * mm))
            elements.append(Paragraph("Quote-parts des associés", section_style))

            qp_data = [["Associé", "Parts (%)", "Quote-part résultat"]]
            for a in result.associes:
                qp_data.append([
                    a.nom,
                    f"{a.part_pct:.1f} %",
                    _fmt_eur(a.quote_part_resultat),
                ])

            qp_table = Table(qp_data, colWidths=[70 * mm, 45 * mm, 50 * mm])
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

        # ── PAGE 2+: Detail per bien ──────────────────────────────────

        if result.biens:
            elements.append(PageBreak())
            elements.append(Paragraph("Détail par bien — Lignes CERFA 2044", title_style))

            for i, bien in enumerate(result.biens):
                bien_label = f"{bien.adresse}"
                if bien.ville:
                    bien_label += f", {bien.ville}"

                bien_elements = []
                bien_elements.append(Paragraph(
                    f"Bien {i + 1} : {bien_label}",
                    section_style,
                ))

                detail_data = [
                    ["Ligne CERFA", "Poste", "Montant"],
                    ["211", "Loyers bruts encaissés", _fmt_eur(bien.ligne_211_loyers_bruts)],
                    ["215", "Frais de gestion forfaitaire", f"- {_fmt_eur(bien.ligne_215_frais_gestion)}"],
                    ["220", "Assurance PNO", f"- {_fmt_eur(bien.ligne_220_assurance)}"],
                    ["221", "Travaux / entretien", f"- {_fmt_eur(bien.ligne_221_travaux)}"],
                    ["224", "Taxe foncière", f"- {_fmt_eur(bien.ligne_224_taxe_fonciere)}"],
                    ["227", "Copropriété", f"- {_fmt_eur(bien.ligne_227_copropriete)}"],
                    ["229", "Total charges déductibles", f"- {_fmt_eur(bien.ligne_229_total_charges)}"],
                    ["230", "Intérêts d'emprunt", f"- {_fmt_eur(bien.ligne_230_interets_emprunt)}"],
                    ["240", "Résultat net", _fmt_eur(bien.ligne_240_resultat_net)],
                ]

                col_w_ligne = 22 * mm
                col_w_poste = 95 * mm
                col_w_montant = 48 * mm

                detail_table = Table(detail_data, colWidths=[col_w_ligne, col_w_poste, col_w_montant])
                detail_table.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
                    ("TEXTCOLOR", (0, 0), (-1, 0), _DARK),
                    ("FONTNAME", (0, 0), (-1, 0), _FONT_BOLD),
                    ("FONTNAME", (0, 1), (-1, -1), _FONT_NAME),
                    ("FONTSIZE", (0, 0), (-1, -1), 9),
                    ("ALIGN", (0, 0), (0, -1), "CENTER"),
                    ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("GRID", (0, 0), (-1, -1), 0.5, _BORDER),
                    # Subtotal row (229)
                    ("BACKGROUND", (0, -3), (-1, -3), _LIGHT_BG),
                    ("FONTNAME", (0, -3), (-1, -3), _FONT_BOLD),
                    # Result row (240)
                    ("BACKGROUND", (0, -1), (-1, -1), _LIGHT_BG),
                    ("FONTNAME", (0, -1), (-1, -1), _FONT_BOLD),
                    ("TEXTCOLOR", (2, -1), (2, -1), _result_color(bien.ligne_240_resultat_net)),
                ]))

                bien_elements.append(detail_table)
                bien_elements.append(Spacer(1, 4 * mm))

                elements.append(KeepTogether(bien_elements))

        # ── Last section: Alertes + Disclaimers ───────────────────────

        if result.alertes:
            elements.append(Spacer(1, 6 * mm))
            elements.append(Paragraph("Alertes et données manquantes", section_style))
            for alerte in result.alertes:
                elements.append(Paragraph(
                    f"  - {alerte}",
                    normal_style,
                ))
            elements.append(Spacer(1, 4 * mm))

        elements.append(Spacer(1, 8 * mm))
        elements.append(Paragraph(
            "<i>Ce document est un résumé simplifié du calcul foncier, "
            "généré par GérerSCI. Il ne constitue pas le formulaire officiel CERFA 2044 "
            "et ne se substitue pas aux obligations déclaratives auprès de l'administration "
            "fiscale. Les numéros de lignes sont fournis à titre indicatif pour faciliter "
            "le report sur votre déclaration. Consultez votre comptable pour la déclaration "
            "définitive.</i>",
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
