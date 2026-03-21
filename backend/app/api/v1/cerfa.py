from __future__ import annotations

import io
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.core.config import settings
from app.core.exceptions import FeatureDisabledError, ValidationError
from app.core.security import get_current_user
from app.core.supabase_client import get_supabase_user_client
from app.services.resume_fiscal_pdf_service import ResumeFiscalPdfService
from app.services.resume_fiscal_service import ResumeFiscalService
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/cerfa", tags=["cerfa"])


class Cerfa2044Request(BaseModel):
    annee: int = Field(ge=2000, le=2100)
    total_revenus: float = Field(ge=0)
    total_charges: float = Field(ge=0)
    sci_nom: str = ""
    siren: str = ""
    regime_fiscal: str | None = None
    # Charge decomposition (optional, included in PDF if provided)
    interets_emprunt: float | None = None
    travaux: float | None = None
    frais_gestion: float | None = None
    assurance: float | None = None
    taxe_fonciere: float | None = None
    copropriete: float | None = None


def _ensure_cerfa_2044_allowed(payload: Cerfa2044Request) -> None:
    if not settings.feature_cerfa_generation:
        raise FeatureDisabledError(
            "La génération du résumé fiscal est désactivée.",
            flag_name="feature_cerfa_generation",
        )

    if (payload.regime_fiscal or "").upper() == "IS":
        raise ValidationError(
            "Le résumé fiscal foncier ne s'applique pas aux SCI à l'IS. Utilisez la liasse fiscale 2065."
        )


@router.post("/2044")
async def generate_cerfa_2044(
    payload: Cerfa2044Request,
    user_id: str = Depends(get_current_user),
) -> dict[str, float | int | str]:
    """Bilan foncier simplifié — calcul revenus - charges (JSON). Route kept as /cerfa/2044 for backward compat."""
    SubscriptionService.ensure_feature_enabled(user_id, "cerfa_enabled")
    _ensure_cerfa_2044_allowed(payload)
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
    """Résumé fiscal foncier au format PDF. Route kept as /cerfa/2044/pdf for backward compat."""
    SubscriptionService.ensure_feature_enabled(user_id, "cerfa_enabled")
    _ensure_cerfa_2044_allowed(payload)

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
    elements.append(Paragraph("Bilan foncier", title_style))
    elements.append(Paragraph(
        f"Résumé fiscal — Exercice {payload.annee} — Calcul simplifié",
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

    # Charge decomposition (if any detail fields provided)
    charge_details = [
        ("Intérêts d'emprunt", payload.interets_emprunt),
        ("Travaux", payload.travaux),
        ("Frais de gestion", payload.frais_gestion),
        ("Assurance", payload.assurance),
        ("Taxe foncière", payload.taxe_fonciere),
        ("Copropriété", payload.copropriete),
    ]
    filled_details = [(label, val) for label, val in charge_details if val is not None and val > 0]

    if filled_details:
        elements.append(Spacer(1, 6 * mm))
        elements.append(Paragraph("<b>Détail des charges déductibles</b>", normal_style))
        elements.append(Spacer(1, 3 * mm))

        detail_data = [["Poste", "Montant (€)"]]
        for label, val in filled_details:
            detail_data.append([label, f"{val:,.2f}"])

        detail_table = Table(detail_data, colWidths=[120 * mm, 50 * mm])
        detail_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ]))
        elements.append(detail_table)

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

    filename = f"resume_fiscal_{payload.annee}_{payload.sci_nom or 'sci'}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/scis/{sci_id}/resume-fiscal/{annee}/pdf")
async def generate_resume_fiscal_pdf(
    sci_id: str,
    annee: int,
    request: Request,
    user_id: str = Depends(get_current_user),
):
    """Résumé fiscal détaillé par bien avec correspondance lignes CERFA 2044.

    Generates a multi-page PDF:
    - Page 1: Synthèse (SCI info, totals, quote-parts associés)
    - Page 2+: Détail par bien (lignes CERFA 211-240)
    - Alertes + mentions légales
    """
    SubscriptionService.ensure_feature_enabled(user_id, "cerfa_enabled")

    if not settings.feature_cerfa_generation:
        raise FeatureDisabledError(
            "La génération du résumé fiscal est désactivée.",
            flag_name="feature_cerfa_generation",
        )

    client = get_supabase_user_client(request)

    # Verify SCI access
    assoc_rows = (
        client.table("associes")
        .select("id")
        .eq("id_sci", sci_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not (assoc_rows.data or []):
        from app.core.exceptions import AuthorizationError
        raise AuthorizationError("SCI", sci_id)

    # Calculate fiscal summary
    service = ResumeFiscalService()
    result = service.calculate(sci_id, annee, client)

    if result.regime_fiscal and result.regime_fiscal.upper() == "IS":
        raise ValidationError(
            "Le résumé fiscal foncier ne s'applique pas aux SCI à l'IS. "
            "Utilisez la liasse fiscale 2065."
        )

    # Generate PDF
    pdf_service = ResumeFiscalPdfService()
    pdf_bytes = pdf_service.generate(result)

    filename = f"resume_fiscal_{annee}_{result.sci_nom or 'sci'}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
