"""Post-signup nurture sequence for users who created an account but haven't paid.

Sends 3 emails over 7 days after signup:
  - Day 1 (24h):  Explore demo data + 3 key features
  - Day 3 (72h):  Pain point — impaye detection
  - Day 7:        Fondateur offer urgency + scarcity

Tracked via subscriptions.nurture_step (0→1→2→3).
Skipped if subscription status is 'active' or 'paid'.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import structlog

from app.core.config import settings
from app.core.supabase_client import get_supabase_service_client
from app.services.email_service import EmailService

logger = structlog.get_logger(__name__)

ACTIVE_STATUSES = {"active", "paid"}

NURTURE_SEQUENCE = [
    {
        "step": 1,
        "min_hours": 24,
        "template": "nurture_signup_day1.html",
        "subject": "Votre SCI mérite mieux qu\u2019un tableur",
        "cta_url_path": "/dashboard",
        "cta_text": "Explorer mon espace de démonstration",
    },
    {
        "step": 2,
        "min_hours": 72,
        "template": "nurture_signup_day3.html",
        "subject": "Un loyer impayé coûte 800\u202f\u20ac en moyenne",
        "cta_url_path": "/#comment-ca-marche",
        "cta_text": "Voir comment ça marche",
    },
    {
        "step": 3,
        "min_hours": 168,  # 7 days
        "template": "nurture_signup_day7.html",
        "subject": "Dernière chance : offre Fondateur à 349\u202f\u20ac (places limitées)",
        "cta_url_path": "/pricing",
        "cta_text": "Devenir Fondateur",
    },
]


async def check_and_send_signup_nurture_emails() -> int:
    """Check for users needing signup nurture emails and send them.

    Called from the notification cron loop. Returns number of emails sent.
    """
    if not settings.resend_api_key or settings.resend_api_key == "re_placeholder":
        return 0

    client = get_supabase_service_client()
    email_svc = EmailService()
    sent_count = 0
    now = datetime.now(timezone.utc)

    # Fetch subscriptions that are not yet active/paid and not fully nurtured
    result = (
        client.table("subscriptions")
        .select("id, user_id, status, nurture_step, created_at")
        .lt("nurture_step", 3)
        .execute()
    )

    for sub in result.data or []:
        status = sub.get("status", "")
        if status in ACTIVE_STATUSES:
            # User converted — skip nurture
            continue

        nurture_step = sub.get("nurture_step") or 0
        created_at = sub.get("created_at")
        user_id = sub.get("user_id")
        if not created_at or not user_id:
            continue

        try:
            sub_created = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            continue

        hours_since_signup = (now - sub_created).total_seconds() / 3600

        # Find the next email to send
        next_email = None
        for step_def in NURTURE_SEQUENCE:
            if step_def["step"] == nurture_step + 1:
                next_email = step_def
                break

        if not next_email:
            continue

        # Check timing: must have passed the minimum hours
        if hours_since_signup < next_email["min_hours"]:
            continue

        # Resolve user email via Supabase Auth admin
        try:
            user_resp = client.auth.admin.get_user_by_id(user_id)
            user_email = user_resp.user.email if user_resp and user_resp.user else None
        except Exception:
            logger.warning("signup_nurture_user_lookup_failed", user_id=user_id, exc_info=True)
            continue

        if not user_email:
            continue

        # Send the email
        try:
            cta_url = f"{settings.frontend_url}{next_email['cta_url_path']}"
            await email_svc.send_email(
                to=user_email,
                subject=next_email["subject"],
                template=next_email["template"],
                context={
                    "cta_url": cta_url,
                    "cta_text": next_email["cta_text"],
                    "unsubscribe_url": f"{settings.frontend_url}/settings",
                },
            )
            sent_count += 1

            # Advance nurture step
            client.table("subscriptions").update(
                {"nurture_step": next_email["step"]}
            ).eq("id", sub["id"]).execute()

            logger.info(
                "signup_nurture_email_sent",
                user_id=user_id,
                email=user_email,
                step=next_email["step"],
                template=next_email["template"],
                hours_since_signup=round(hours_since_signup, 1),
            )
        except Exception:
            logger.warning(
                "signup_nurture_email_failed",
                user_id=user_id,
                step=next_email["step"],
                exc_info=True,
            )

    return sent_count
