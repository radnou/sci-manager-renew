from __future__ import annotations

import io
from datetime import datetime

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.config import settings
from app.core.exceptions import FeatureDisabledError
from app.core.security import get_current_user
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/cerfa", tags=["cerfa"])


class Cerfa2044Request(BaseModel):
    annee: int = Field(ge=2000, le=2100)
    total_revenus: float = Field(ge=0)
    total_charges: float = Field(ge=0)
    sci_nom: str = ""
    siren: str = ""


@router.post("/2044")
async def generate_cerfa_2044(
    payload: Cerfa2044Request,
    user_id: str = Depends(get_current_user),
) -> dict[str, float | int | str]:
    """Simplified CERFA 2044 fiscal calculation (JSON)."""
    SubscriptionService.ensure_feature_enabled(user_id, "cerfa_enabled")
    if not settings.feature_cerfa_generation:
        raise FeatureDisabledError(
            "La génération Cerfa est désactivée.",
            flag_name="feature_cerfa_generation",
        )
    resultat_fiscal = round(payload.total_revenus - payload.total_charges, 2)
    return {
        "status": "generated",
        "annee": payload.annee,
        "total_revenus": payload.total_revenus,
        "total_charges": payload.total_charges,
        "resultat_fiscal": resultat_fiscal,
        "formulaire": "cerfa_2044",
    }


@router.post("/2044/pdf")
async def generate_cerfa_2044_pdf(
    payload: Cerfa2044Request,
    user_id: str = Depends(get_current_user),
):
    """Generate a simplified CERFA 2044 summary as PDF."""
    SubscriptionService.ensure_feature_enabled(user_id, "cerfa_enabled")

    resultat_fiscal = round(payload.total_revenus - payload.total_charges, 2)

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
    normal_style = ParagraphStyle(
        "CerfaNormal",
        parent=styles["Normal"],
        fontSize=11,
        leading=16,
        textColor=colors.HexColor("#334155"),
    )

    elements = []

    # Header
    elements.append(Paragraph("Déclaration des revenus fonciers", title_style))
    elements.append(Paragraph(
        f"CERFA 2044 — Exercice {payload.annee} — Calcul simplifié",
        subtitle_style,
    ))

    if payload.sci_nom:
        elements.append(Paragraph(f"<b>SCI :</b> {payload.sci_nom}", normal_style))
    if payload.siren:
        elements.append(Paragraph(f"<b>SIREN :</b> {payload.siren}", normal_style))

    elements.append(Spacer(1, 8 * mm))

    # Summary table
    data = [
        ["Poste", "Montant (€)"],
        ["Revenus fonciers bruts", f"{payload.total_revenus:,.2f}"],
        ["Charges déductibles", f"- {payload.total_charges:,.2f}"],
        ["Résultat fiscal net", f"{resultat_fiscal:,.2f}"],
    ]

    table = Table(data, colWidths=[120 * mm, 50 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 11),
        ("ALIGN", (1, 0), (1, -1), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f8fafc")),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
    ]))
    elements.append(table)

    elements.append(Spacer(1, 10 * mm))

    # Disclaimer
    elements.append(Paragraph(
        "<i>Ce document est un résumé simplifié du calcul foncier, généré par GererSCI. "
        "Il ne constitue pas le formulaire officiel CERFA 2044 et ne se substitue pas aux "
        "obligations déclaratives auprès de l'administration fiscale.</i>",
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

    filename = f"cerfa_2044_{payload.annee}_{payload.sci_nom or 'sci'}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
