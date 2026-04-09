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
from app.core.exceptions import FeatureDisabledError, ResourceNotFoundError, ValidationError
from app.core.rate_limit import limiter
from app.core.security import get_current_user
from app.core.supabase_client import get_supabase_user_client
from app.services.declaration_2072_service import Declaration2072PdfService
from app.services.resume_fiscal_pdf_service import ResumeFiscalPdfService, Report2042PdfService
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


def _ensure_sci_access(client, sci_id: str, user_id: str) -> None:
    """Verify user has access to the SCI via associes membership."""
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


def _ensure_feature_enabled(user_id: str) -> None:
    """Verify CERFA feature is enabled for the user."""
    SubscriptionService.ensure_feature_enabled(user_id, "cerfa_enabled")
    if not settings.feature_cerfa_generation:
        raise FeatureDisabledError(
            "La génération du résumé fiscal est désactivée.",
            flag_name="feature_cerfa_generation",
        )


def _calculate_and_validate(sci_id: str, annee: int, client):
    """Calculate fiscal summary and validate regime."""
    service = ResumeFiscalService()
    result = service.calculate(sci_id, annee, client)

    if result.regime_fiscal and result.regime_fiscal.upper() == "IS":
        raise ValidationError(
            "Le résumé fiscal foncier ne s'applique pas aux SCI à l'IS. "
            "Utilisez la liasse fiscale 2065."
        )

    return result


@router.post("/2044")
@limiter.limit("30/minute")
async def generate_cerfa_2044(
    request: Request,
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
@limiter.limit("30/minute")
async def generate_cerfa_2044_pdf(
    request: Request,
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


@router.get("/scis/{sci_id}/resume-fiscal/{annee}")
async def get_resume_fiscal_json(
    sci_id: str,
    annee: int,
    request: Request,
    user_id: str = Depends(get_current_user),
):
    """Résumé fiscal JSON — micro-foncier, déficit foncier, régime recommandé."""
    _ensure_feature_enabled(user_id)
    client = get_supabase_user_client(request)
    _ensure_sci_access(client, sci_id, user_id)

    result = _calculate_and_validate(sci_id, annee, client)

    from dataclasses import asdict
    return asdict(result)


@router.get("/scis/{sci_id}/resume-fiscal/{annee}/pdf")
async def generate_resume_fiscal_pdf(
    sci_id: str,
    annee: int,
    request: Request,
    user_id: str = Depends(get_current_user),
):
    """Résumé fiscal détaillé par bien avec correspondance lignes CERFA 2044.

    Generates a 5-page PDF:
    - Page 1: Identification (SCI info, fiscal year)
    - Page 2: Cadre 1 — Revenus (per bien + total)
    - Page 3: Cadre 2 — Charges déductibles (per bien + total)
    - Page 4: Cadre 3 — Résultat + Déficit + Micro-foncier
    - Page 5: Cadre 4 — Répartition par associé + Cases 2042
    """
    _ensure_feature_enabled(user_id)
    client = get_supabase_user_client(request)
    _ensure_sci_access(client, sci_id, user_id)

    result = _calculate_and_validate(sci_id, annee, client)

    # Generate PDF
    pdf_service = ResumeFiscalPdfService()
    pdf_bytes = pdf_service.generate(result)

    filename = f"resume_fiscal_{annee}_{result.sci_nom or 'sci'}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/scis/{sci_id}/report-2042/{annee}/{associe_id}/pdf")
async def generate_report_2042_pdf(
    sci_id: str,
    annee: int,
    associe_id: str,
    request: Request,
    user_id: str = Depends(get_current_user),
):
    """Report individuel 2042 pour un associé spécifique.

    Generates a 1-page PDF showing:
    - Associé name, email, parts %
    - SCI name, SIREN
    - Quote-part résultat
    - Cases 2042 (4BA, 4BB, 4BC, 4BD)
    - Instructions de report
    """
    _ensure_feature_enabled(user_id)
    client = get_supabase_user_client(request)
    _ensure_sci_access(client, sci_id, user_id)

    result = _calculate_and_validate(sci_id, annee, client)

    # Find the specific associé in the result
    target_associe = None
    for a in result.associes:
        if a.associe_id == associe_id:
            target_associe = a
            break

    if not target_associe:
        raise ResourceNotFoundError("Associé", associe_id)

    # Generate PDF
    pdf_service = Report2042PdfService()
    pdf_bytes = pdf_service.generate(result, target_associe)

    safe_nom = target_associe.nom.replace(" ", "_")
    filename = f"report_2042_{annee}_{safe_nom}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/scis/{sci_id}/declaration-2072/{annee}/pdf")
@limiter.limit("5/minute")
async def generate_declaration_2072_pdf(
    sci_id: str,
    annee: int,
    request: Request,
    user_id: str = Depends(get_current_user),
):
    """Declaration 2072-S — Declaration de resultats des SCI non soumises a l'IS.

    Generates a multi-page PDF:
    - Cadre I: Identification de la SCI
    - Cadre II: Revenus fonciers bruts par immeuble
    - Cadre III: Charges deductibles par immeuble
    - Cadre IV: Determination du resultat fiscal
    - Cadre V: Repartition du resultat entre les associes
    """
    _ensure_feature_enabled(user_id)
    client = get_supabase_user_client(request)
    _ensure_sci_access(client, sci_id, user_id)

    result = _calculate_and_validate(sci_id, annee, client)

    # Generate PDF
    pdf_service = Declaration2072PdfService()
    pdf_bytes = pdf_service.generate(result)

    safe_nom = (result.sci_nom or "sci").replace(" ", "_")
    filename = f"declaration_2072_{annee}_{safe_nom}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
