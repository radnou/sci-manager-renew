from __future__ import annotations

from datetime import datetime, timedelta, timezone

import structlog

from app.services.notification_service import create_notification_with_email

logger = structlog.get_logger(__name__)


async def check_late_payments(supabase_client) -> int:
    """Find loyers more than 5 days unpaid and notify the owner."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=5)).strftime("%Y-%m-%d")

    result = (
        supabase_client.table("loyers")
        .select("id, id_bien, id_sci, date_loyer, montant, biens(id_sci, adresse, ville)")
        .in_("statut", ["en_attente", "en_retard"])
        .lt("date_loyer", cutoff)
        .execute()
    )

    notified = 0
    for loyer in result.data or []:
        # Resolve the owner via the SCI associes
        sci_id = loyer.get("id_sci") or (loyer.get("biens") or {}).get("id_sci")
        if not sci_id:
            continue

        owners = (
            supabase_client.table("associes")
            .select("user_id")
            .eq("id_sci", sci_id)
            .not_.is_("user_id", "null")
            .execute()
        )

        bien = loyer.get("biens") or {}
        for owner in owners.data or []:
            await create_notification_with_email(
                supabase_client,
                user_id=owner["user_id"],
                notification_type="late_payment",
                data={
                    "title": "Loyer en retard",
                    "message": f"Le loyer du {loyer['date_loyer']} ({loyer['montant']} EUR) pour {bien.get('adresse', 'un bien')} est impaye.",
                    "metadata": {"loyer_id": loyer["id"], "bien_adresse": bien.get("adresse")},
                },
            )
            notified += 1

    logger.info("check_late_payments_complete", notified=notified)
    return notified


async def check_expiring_bails(supabase_client) -> int:
    """Find baux expiring within 90 days and notify the owner."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    horizon = (datetime.now(timezone.utc) + timedelta(days=90)).strftime("%Y-%m-%d")

    result = (
        supabase_client.table("baux")
        .select("id, id_bien, date_fin, biens(id_sci, adresse, ville)")
        .gte("date_fin", now)
        .lte("date_fin", horizon)
        .execute()
    )

    notified = 0
    for bail in result.data or []:
        bien = bail.get("biens") or {}
        sci_id = bien.get("id_sci")
        if not sci_id:
            continue

        owners = (
            supabase_client.table("associes")
            .select("user_id")
            .eq("id_sci", sci_id)
            .not_.is_("user_id", "null")
            .execute()
        )

        for owner in owners.data or []:
            await create_notification_with_email(
                supabase_client,
                user_id=owner["user_id"],
                notification_type="bail_expiring",
                data={
                    "title": "Bail expirant",
                    "message": f"Le bail pour {bien.get('adresse', 'un bien')} expire le {bail['date_fin']}.",
                    "metadata": {"bail_id": bail["id"], "bien_adresse": bien.get("adresse")},
                },
            )
            notified += 1

    logger.info("check_expiring_bails_complete", notified=notified)
    return notified


async def check_pending_quittances(supabase_client) -> int:
    """Find loyers marked as paid but without a generated quittance."""
    result = (
        supabase_client.table("loyers")
        .select("id, id_bien, id_sci, date_loyer, montant, biens(id_sci, adresse, ville)")
        .eq("statut", "paye")
        .eq("quitus_genere", False)
        .execute()
    )

    notified = 0
    for loyer in result.data or []:
        sci_id = loyer.get("id_sci") or (loyer.get("biens") or {}).get("id_sci")
        if not sci_id:
            continue

        owners = (
            supabase_client.table("associes")
            .select("user_id")
            .eq("id_sci", sci_id)
            .not_.is_("user_id", "null")
            .execute()
        )

        bien = loyer.get("biens") or {}
        for owner in owners.data or []:
            await create_notification_with_email(
                supabase_client,
                user_id=owner["user_id"],
                notification_type="quittance_pending",
                data={
                    "title": "Quittance en attente",
                    "message": f"Le loyer du {loyer['date_loyer']} pour {bien.get('adresse', 'un bien')} est paye mais la quittance n'a pas ete generee.",
                    "metadata": {"loyer_id": loyer["id"], "bien_adresse": bien.get("adresse")},
                },
            )
            notified += 1

    logger.info("check_pending_quittances_complete", notified=notified)
    return notified


async def check_expiring_pno(supabase_client) -> int:
    """Find PNO insurance policies expiring within 30 days."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    horizon = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")

    result = (
        supabase_client.table("assurance_pno")
        .select("id, id_bien, assureur, date_fin, biens(id_sci, adresse, ville)")
        .gte("date_fin", now)
        .lte("date_fin", horizon)
        .execute()
    )

    notified = 0
    for pno in result.data or []:
        bien = pno.get("biens") or {}
        sci_id = bien.get("id_sci")
        if not sci_id:
            continue

        owners = (
            supabase_client.table("associes")
            .select("user_id")
            .eq("id_sci", sci_id)
            .not_.is_("user_id", "null")
            .execute()
        )

        for owner in owners.data or []:
            await create_notification_with_email(
                supabase_client,
                user_id=owner["user_id"],
                notification_type="pno_expiring",
                data={
                    "title": "PNO expirant",
                    "message": f"L'assurance PNO ({pno.get('assureur', 'N/A')}) pour {bien.get('adresse', 'un bien')} expire le {pno['date_fin']}.",
                    "metadata": {"pno_id": pno["id"], "bien_adresse": bien.get("adresse")},
                },
            )
            notified += 1

    logger.info("check_expiring_pno_complete", notified=notified)
    return notified
