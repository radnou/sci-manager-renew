"""IRL (Indice de Reference des Loyers) revision service.

Detects baux approaching their annual revision anniversary and notifies
owners with estimated new rent based on IRL increase.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import structlog

from app.services.notification_service import create_notification_with_email

logger = structlog.get_logger(__name__)

# Typical annual IRL increase factor (2.5% as of recent quarters).
# In a future iteration this could be fetched from INSEE API.
IRL_INCREASE_FACTOR = 1.025


def _next_anniversary(date_debut: date, reference: date) -> date:
    """Calculate the next bail anniversary date relative to a reference date.

    The anniversary is the same month/day as date_debut, in the year
    that is >= reference date.
    """
    anniversary_this_year = date_debut.replace(year=reference.year)
    if anniversary_this_year < reference:
        anniversary_this_year = date_debut.replace(year=reference.year + 1)
    return anniversary_this_year


async def check_irl_revisions(supabase_client) -> int:
    """Find baux where the revision anniversary is within 30 days.

    For each matching bail, creates a notification with the estimated
    revised rent based on IRL increase.
    """
    today = date.today()
    notified = 0

    # Fetch all active baux
    result = (
        supabase_client.table("baux")
        .select("id, id_bien, date_debut, loyer_hc, statut, indice_irl_reference")
        .eq("statut", "en_cours")
        .execute()
    )

    for bail in result.data or []:
        if not bail.get("date_debut") or not bail.get("id_bien"):
            continue

        try:
            bail_date_debut = datetime.strptime(bail["date_debut"], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue

        # Skip baux less than 1 year old (no revision yet)
        if (today - bail_date_debut).days < 365:
            continue

        anniversary = _next_anniversary(bail_date_debut, today)
        days_until = (anniversary - today).days

        # Only notify if anniversary is within 30 days
        if days_until < 0 or days_until > 30:
            continue

        loyer_hc = float(bail.get("loyer_hc") or 0)
        if loyer_hc <= 0:
            continue

        new_loyer = round(loyer_hc * IRL_INCREASE_FACTOR, 2)

        # Resolve bien info
        bien_result = (
            supabase_client.table("biens")
            .select("id_sci, adresse, ville")
            .eq("id", bail["id_bien"])
            .execute()
        )
        bien_rows = bien_result.data or []
        if not bien_rows:
            continue

        bien = bien_rows[0]
        sci_id = bien.get("id_sci")
        if not sci_id:
            continue

        adresse = bien.get("adresse", "un bien")

        # Fetch owners
        owners = (
            supabase_client.table("associes")
            .select("user_id")
            .eq("id_sci", sci_id)
            .not_.is_("user_id", "null")
            .execute()
        )

        for owner in owners.data or []:
            created = await create_notification_with_email(
                supabase_client,
                user_id=owner["user_id"],
                notification_type="system",
                data={
                    "title": f"Revision IRL \u2014 {adresse}",
                    "message": (
                        f"Le bail est revisable le {anniversary.strftime('%d/%m/%Y')}. "
                        f"Loyer actuel: {loyer_hc}\u20ac, loyer revise estime: {new_loyer}\u20ac (+2.5% IRL)."
                    ),
                    "metadata": {
                        "bail_id": bail["id"],
                        "bien_adresse": adresse,
                        "current_loyer": loyer_hc,
                        "estimated_loyer": new_loyer,
                        "anniversary": anniversary.isoformat(),
                        "dedup_key": f"irl_{bail['id']}_{anniversary.year}",
                    },
                },
            )
            if created:
                notified += 1

    logger.info("check_irl_revisions_complete", notified=notified)
    return notified
