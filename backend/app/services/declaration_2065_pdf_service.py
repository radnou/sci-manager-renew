"""Service de génération PDF de la déclaration 2065 (CERFA)."""

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.declaration_2065_service import Declaration2065


class Declaration2065PdfService:
    """Génère un PDF CERFA 2065 (bilan simplifié SCI à l'IS)."""

    def generate(self, declaration: Declaration2065, sci_nom: str = "") -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=20 * mm,
            rightMargin=20 * mm,
            topMargin=20 * mm,
            bottomMargin=20 * mm,
        )

        styles = getSampleStyleSheet()

        # Styles personnalisés
        title_style = ParagraphStyle(
            "CerfaTitle",
            parent=styles["Heading1"],
            fontSize=16,
            spaceAfter=6 * mm,
            textColor=colors.HexColor("#1e293b"),
        )
        subtitle_style = ParagraphStyle(
            "CerfaSubtitle",
            parent=styles["Normal"],
            fontSize=10,
            spaceAfter=4 * mm,
            textColor=colors.HexColor("#64748b"),
        )
        heading2_style = ParagraphStyle(
            "CerfaHeading2",
            parent=styles["Heading2"],
            fontSize=12,
            spaceAfter=4 * mm,
            spaceBefore=6 * mm,
            textColor=colors.HexColor("#1e293b"),
        )
        normal_style = ParagraphStyle(
            "CerfaNormal",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#334155"),
        )
        label_style = ParagraphStyle(
            "CerfaLabel",
            parent=normal_style,
            fontSize=9,
            textColor=colors.HexColor("#64748b"),
        )
        value_style = ParagraphStyle(
            "CerfaValue",
            parent=normal_style,
            fontSize=10,
            alignment=2,  # Right align
        )

        elements = []

        # ═══════════════════════════════════════════════════════════════
        # PAGE 1 — IDENTIFICATION + BILAN ACTIF
        # ═══════════════════════════════════════════════════════════════

        # En-tête CERFA
        elements.append(Paragraph("Déclaration n° 2065", title_style))
        elements.append(Paragraph(
            f"Liasse fiscale des sociétés civiles immobilières à l'impôt sur les sociétés — Exercice {declaration.exercice}",
            subtitle_style,
        ))

        if sci_nom:
            elements.append(Paragraph(f"<b>SCI :</b> {sci_nom}", normal_style))

        elements.append(Paragraph(
            f"<b>Date de clôture :</b> {declaration.date_cloture.strftime('%d/%m/%Y')}",
            normal_style,
        ))
        elements.append(Spacer(1, 4 * mm))

        # ── BILAN ACTIF ──────────────────────────────────────────────
        elements.append(Paragraph("BILAN — ACTIF", heading2_style))

        actif_data = [
            ["Poste", "Montant (€)"],
            ["Immobilisations corporelles", f"{float(declaration.actif.immobilisations_corporelles):,.2f}"],
            ["Travaux en cours", f"{float(declaration.actif.travaux_en_cours or 0):,.2f}"],
            ["Créances clients (loyers impayés)", f"{float(declaration.actif.créances_clients):,.2f}"],
            ["Autres créances", f"{float(declaration.actif.autres_créances or 0):,.2f}"],
            ["Trésorerie active", f"{float(declaration.actif.trésorerie_actif):,.2f}"],
            ["<b>TOTAL ACTIF</b>", f"<b>{float(declaration.actif.total_actif):,.2f}</b>"],
        ]

        actif_table = Table(actif_data, colWidths=[110 * mm, 50 * mm])
        actif_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f8fafc")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ]))
        elements.append(actif_table)

        elements.append(Spacer(1, 8 * mm))

        # ── BILAN PASSIF ─────────────────────────────────────────────
        elements.append(Paragraph("BILAN — PASSIF", heading2_style))

        passif_data = [
            ["Poste", "Montant (€)"],
            ["Capital social", f"{float(declaration.passif.capital_social):,.2f}"],
            ["Réserves", f"{float(declaration.passif.réserves or 0):,.2f}"],
            ["Report à nouveau", f"{float(declaration.passif.report_à_nouveau or 0):,.2f}"],
            ["Résultat de l'exercice", f"{float(declaration.passif.résultat_exercice):,.2f}"],
            ["Emprunts", f"{float(declaration.passif.emprunts):,.2f}"],
            ["Dettes fournisseurs", f"{float(declaration.passif.dettes_fournisseurs or 0):,.2f}"],
            ["Autres dettes", f"{float(declaration.passif.autres_dettes or 0):,.2f}"],
            ["<b>TOTAL PASSIF</b>", f"<b>{float(declaration.passif.total_passif):,.2f}</b>"],
        ]

        passif_table = Table(passif_data, colWidths=[110 * mm, 50 * mm])
        passif_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f8fafc")),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ]))
        elements.append(passif_table)

        elements.append(Spacer(1, 8 * mm))

        # ── CONTRÔLE ÉQUILIBRE ──────────────────────────────────────
        ecart = float(declaration.écart)
        ecart_color = "#22c55e" if abs(ecart) < 0.01 else "#ef4444"
        elements.append(Paragraph(
            f"<b>Contrôle d'équilibre :</b> Écart actif/passif = <font color='{ecart_color}'>{ecart:,.2f} €</font>",
            ParagraphStyle("Ecart", parent=normal_style, fontSize=11),
        ))

        if abs(ecart) >= 0.01:
            elements.append(Paragraph(
                f"<font color='#ef4444'><b>⚠ Bilan déséquilibré</b> — Vérifiez les montants saisis.</font>",
                normal_style,
            ))
        else:
            elements.append(Paragraph(
                f"<font color='#22c55e'>✓ Bilan équilibré</font>",
                normal_style,
            ))

        # ── DISCLAIMER ──────────────────────────────────────────────
        elements.append(Spacer(1, 10 * mm))
        elements.append(Paragraph(
            "<i>Ce document est un résumé simplifié de la liasse fiscale 2065, généré par GererSCI. "
            "Il ne constitue pas le formulaire officiel CERFA et ne se substitue pas aux "
            "obligations déclaratives auprès de l'administration fiscale. "
            "Vérifiez les montants et consultez un expert-comptable avant dépôt.</i>",
            ParagraphStyle(
                "Disclaimer",
                parent=styles["Normal"],
                fontSize=8,
                textColor=colors.HexColor("#94a3b8"),
                leading=12,
            ),
        ))

        elements.append(Spacer(1, 4 * mm))
        elements.append(Paragraph(
            f"Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')} via GererSCI",
            ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#94a3b8")),
        ))

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
