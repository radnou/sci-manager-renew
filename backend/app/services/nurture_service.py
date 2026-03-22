"""Email nurture sequence for captured leads.

Sends 3 emails over 7 days after lead capture:
  - Day 0: Welcome + simulation result
  - Day 3: Value proposition (3 erreurs)
  - Day 7: Urgency (saison fiscale)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import structlog

from app.core.config import settings
from app.core.supabase_client import get_supabase_service_client
from app.services.email_service import EmailService

logger = structlog.get_logger(__name__)

SOURCE_LABELS: dict[str, str] = {
    "simulateur-cerfa": "simulateur CERFA 2044",
    "generateur-quittance": "générateur de quittance",
    "calendrier-fiscal": "calendrier fiscal SCI",
    "landing": "page d'accueil",
}

NURTURE_SEQUENCE = [
    {"day": 0, "template": "nurture_1_bienvenue.html", "subject": "Votre simulation SCI est prête"},
    {"day": 3, "template": "nurture_2_valeur.html", "subject": "3 erreurs que font 80% des gérants de SCI"},
    {"day": 7, "template": "nurture_3_urgence.html", "subject": "La saison fiscale approche — êtes-vous prêt ?"},
]


async def process_nurture_emails() -> int:
    """Process pending nurture emails for all captured leads.

    Returns the number of emails sent.
    """
    if not settings.resend_api_key or settings.resend_api_key == "re_placeholder":
        return 0

    client = get_supabase_service_client()
    email_service = EmailService()
    sent_count = 0

    # Get all leads not yet converted to users
    result = client.table("lead_captures").select("*").is_("converted_to_user_id", "null").execute()
    leads = result.data or []

    now = datetime.now(timezone.utc)

    for lead in leads:
        email = lead.get("email")
        created_at = lead.get("created_at")
        if not email or not created_at:
            continue

        try:
            lead_date = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            continue

        days_since_capture = (now - lead_date).days
        nurture_step = lead.get("nurture_step", 0) or 0
        source = lead.get("source", "unknown")

        for i, step in enumerate(NURTURE_SEQUENCE):
            if i < nurture_step:
                continue
            if days_since_capture < step["day"]:
                break

            # Send this nurture email
            try:
                source_label = SOURCE_LABELS.get(source, "outil gratuit GérerSCI")
                await email_service.send_email(
                    to=email,
                    subject=step["subject"],
                    template=step["template"],
                    context={
                        "source_label": source_label,
                        "frontend_url": settings.frontend_url,
                    },
                )
                sent_count += 1

                # Update nurture step
                client.table("lead_captures").update(
                    {"nurture_step": i + 1}
                ).eq("id", lead["id"]).execute()

                logger.info(
                    "nurture_email_sent",
                    email=email,
                    step=i + 1,
                    template=step["template"],
                    days_since_capture=days_since_capture,
                )
            except Exception:
                logger.warning(
                    "nurture_email_failed",
                    email=email,
                    step=i + 1,
                    exc_info=True,
                )
            break  # Only send one email per lead per run

    return sent_count
