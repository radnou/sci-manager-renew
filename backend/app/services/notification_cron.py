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
        supabase_client.table("assurances_pno")
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


# ── SCI fiscal-calendar deadlines (relative to current year) ──────────
# IR → 2072 déclaration ~20 mai, 2044 individuelle ~fin mai
# IS → liasse fiscale ~3 mois après clôture (31 mars pour exercice 31/12)
# Taxe foncière → ~15 octobre
# CFE → ~15 décembre
# AG annuelle → obligatoire dans les 6 mois post-clôture (~30 juin)

FISCAL_DEADLINES = [
    {"key": "declaration_2072", "label": "Déclaration 2072", "month": 5, "day": 20, "regime": "IR", "advance_days": 30},
    {"key": "declaration_2044", "label": "Déclaration 2044 (associés)", "month": 5, "day": 31, "regime": "IR", "advance_days": 30},
    {"key": "liasse_fiscale_is", "label": "Liasse fiscale IS", "month": 3, "day": 31, "regime": "IS", "advance_days": 30},
    {"key": "taxe_fonciere", "label": "Taxe foncière", "month": 10, "day": 15, "regime": None, "advance_days": 30},
    {"key": "cfe", "label": "CFE (Cotisation Foncière)", "month": 12, "day": 15, "regime": None, "advance_days": 30},
    {"key": "ag_annuelle", "label": "AG annuelle obligatoire", "month": 6, "day": 30, "regime": None, "advance_days": 45},
]


async def check_fiscal_deadlines(supabase_client) -> int:
    """Notify SCI owners about upcoming fiscal deadlines."""
    now = datetime.now(timezone.utc)
    year = now.year

    # Fetch all SCIs with their regime fiscal
    result = supabase_client.table("sci").select("id, nom, regime_fiscal").execute()
    scis = result.data or []
    if not scis:
        return 0

    notified = 0
    for sci in scis:
        sci_regime = (sci.get("regime_fiscal") or "").upper()

        for deadline in FISCAL_DEADLINES:
            # Skip regime-specific deadlines that don't apply
            if deadline["regime"] and deadline["regime"] != sci_regime:
                continue

            deadline_date = datetime(year, deadline["month"], deadline["day"], tzinfo=timezone.utc)
            days_until = (deadline_date - now).days

            # Only notify within the advance window and if not past
            if days_until < 0 or days_until > deadline["advance_days"]:
                continue

            # Fetch SCI owners
            owners = (
                supabase_client.table("associes")
                .select("user_id")
                .eq("id_sci", sci["id"])
                .not_.is_("user_id", "null")
                .execute()
            )

            for owner in owners.data or []:
                await create_notification_with_email(
                    supabase_client,
                    user_id=owner["user_id"],
                    notification_type="fiscal_deadline",
                    data={
                        "title": f"{deadline['label']} — {sci['nom']}",
                        "message": f"Échéance le {deadline_date.strftime('%d/%m/%Y')} ({days_until} jours restants).",
                        "metadata": {
                            "sci_id": sci["id"],
                            "deadline_key": deadline["key"],
                            "deadline_date": deadline_date.strftime("%Y-%m-%d"),
                            "days_until": days_until,
                        },
                    },
                )
                notified += 1

    logger.info("check_fiscal_deadlines_complete", notified=notified)
    return notified
