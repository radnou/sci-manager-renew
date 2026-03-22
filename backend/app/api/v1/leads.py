"""Lead capture endpoints for SEO funnel tools."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Request, BackgroundTasks
from pydantic import BaseModel, EmailStr

from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.supabase_client import get_supabase_service_client

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/leads", tags=["leads"])


class LeadCaptureRequest(BaseModel):
    email: EmailStr
    source: str = "unknown"
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None


class LeadCaptureWithContextRequest(LeadCaptureRequest):
    """Extended capture with context data for email confirmation."""
    context: dict | None = None  # e.g. {"periode": "Mars 2026", "nom_proprietaire": "SCI X", ...}


class LeadCaptureResponse(BaseModel):
    status: str = "captured"


async def _send_lead_confirmation_email(email: str, source: str, context: dict | None) -> None:
    """Send confirmation email in background based on source."""
    if not settings.resend_api_key or settings.resend_api_key == "re_placeholder":
        logger.info("lead_email_skipped_no_api_key", email=email)
        return

    try:
        from app.services.email_service import EmailService
        svc = EmailService()

        template_map = {
            "generateur-quittance": {
                "template": "lead_quittance.html",
                "subject": "Votre quittance de loyer — GérerSCI",
            },
            "simulateur-cerfa": {
                "template": "nurture_1_bienvenue.html",
                "subject": "Votre simulation CERFA 2044 — GérerSCI",
            },
            "calendrier-fiscal": {
                "template": "nurture_1_bienvenue.html",
                "subject": "Calendrier fiscal SCI 2026 — GérerSCI",
            },
        }

        config = template_map.get(source, {
            "template": "nurture_1_bienvenue.html",
            "subject": "Bienvenue — GérerSCI",
        })

        template_context = {
            "frontend_url": settings.frontend_url,
            "source_label": source.replace("-", " ").title(),
            "unsubscribe_url": f"{settings.frontend_url}/settings",
            **(context or {}),
        }

        # For quittance, add CTA to download
        if source == "generateur-quittance":
            template_context["cta_url"] = f"{settings.frontend_url}/generateur-quittance"
            template_context["cta_text"] = "Télécharger ma quittance"

        await svc.send_email(
            to=email,
            subject=config["subject"],
            template=config["template"],
            context=template_context,
        )
        logger.info("lead_confirmation_sent", email=email, source=source)
    except Exception:
        logger.warning("lead_confirmation_failed", email=email, source=source, exc_info=True)


@router.post("/capture", response_model=LeadCaptureResponse)
@limiter.limit("10/minute")
async def capture_lead(
    request: Request,
    payload: LeadCaptureWithContextRequest,
    background_tasks: BackgroundTasks,
) -> LeadCaptureResponse:
    """Capture an email lead and send confirmation email in background."""
    client = get_supabase_service_client()
    client.table("lead_captures").insert(
        {
            "email": payload.email,
            "source": payload.source,
            "utm_source": payload.utm_source,
            "utm_medium": payload.utm_medium,
            "utm_campaign": payload.utm_campaign,
        }
    ).execute()

    # Send confirmation email in background (non-blocking)
    background_tasks.add_task(
        _send_lead_confirmation_email,
        payload.email,
        payload.source,
        payload.context,
    )

    return LeadCaptureResponse()
