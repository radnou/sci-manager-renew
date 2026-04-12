from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta, timezone

import structlog

from app.services.notification_service import create_notification_with_email
from app.services.jour_loyer_service import resolve_jour_loyer_for_bien

logger = structlog.get_logger(__name__)


# ── TASK 1: Appel de loyer automatique ──────────────────────────────────


async def check_monthly_loyer_generation(supabase_client) -> int:
    """Generate loyer records for all active baux on their configured jour_loyer.

    For each bail with statut='en_cours', creates a loyer when today matches the
    resolved jour_loyer for the bien (bien.jour_loyer ?? sci.jour_loyer ?? 1).

    Creates a loyer with:
    - date_loyer = jour_loyer of current month (or 1st if jour_loyer > days in month)
    - montant = bail.loyer_hc + bail.charges_locatives
    - statut = 'en_attente'
    - id_bien = bail.id_bien

    Skips if a loyer already exists for this bien + month (dedup).
    """
    today = date.today()

    # Fetch all active baux
    result = (
        supabase_client.table("baux")
        .select("id, id_bien, loyer_hc, charges_locatives, statut")
        .eq("statut", "en_cours")
        .execute()
    )

    created_count = 0
    for bail in result.data or []:
        id_bien = bail.get("id_bien")
        if not id_bien:
            continue

        loyer_hc = float(bail.get("loyer_hc") or 0)
        charges_locatives = float(bail.get("charges_locatives") or 0)
        montant = round(loyer_hc + charges_locatives, 2)
        if montant <= 0:
            continue

        # Resolve id_sci and jour_loyer from the bien + sci
        bien_result = (
            supabase_client.table("biens")
            .select("id_sci, jour_loyer")
            .eq("id", id_bien)
            .execute()
        )
        bien_rows = bien_result.data or []
        if not bien_rows:
            continue
        bien_row = bien_rows[0]
        id_sci = bien_row.get("id_sci")

        # Fetch sci-level jour_loyer
        sci_row = None
        if id_sci:
            sci_result = (
                supabase_client.table("sci")
                .select("jour_loyer")
                .eq("id", id_sci)
                .execute()
            )
            sci_rows = sci_result.data or []
            sci_row = sci_rows[0] if sci_rows else None

        effective_jour = resolve_jour_loyer_for_bien(bien_row, sci_row)

        # Only generate on the configured day
        if today.day != effective_jour:
            continue

        # Build the loyer date for this month using the effective day
        # (safe because effective_jour is clamped to 1-28)
        loyer_date = today.replace(day=effective_jour).isoformat()

        # Dedup: check if loyer already exists for this bien + month
        month_start = today.replace(day=1).isoformat()
        last_day = calendar.monthrange(today.year, today.month)[1]
        month_end = today.replace(day=last_day).isoformat()
        existing = (
            supabase_client.table("loyers")
            .select("id")
            .eq("id_bien", id_bien)
            .gte("date_loyer", month_start)
            .lte("date_loyer", month_end)
            .execute()
        )
        if existing.data:
            continue

        # Create loyer record
        supabase_client.table("loyers").insert({
            "id_bien": id_bien,
            "id_sci": id_sci,
            "date_loyer": loyer_date,
            "montant": montant,
            "statut": "en_attente",
            "quitus_genere": False,
        }).execute()
        created_count += 1

    logger.info("check_monthly_loyer_generation_complete", created=created_count)
    return created_count


# ── TASK 2: Relance impaye graduee ──────────────────────────────────────


_LATE_PAYMENT_LEVELS = [
    {"days": 5, "title_prefix": "Relance amiable", "severity": "info"},
    {"days": 15, "title_prefix": "Relance formelle", "severity": "warning"},
    {"days": 30, "title_prefix": "Mise en demeure recommandee", "severity": "critical"},
]


async def check_late_payments(supabase_client) -> int:
    """Find unpaid loyers and send graduated reminders at J+5, J+15, J+30."""
    now = datetime.now(timezone.utc)
    # Fetch all unpaid loyers older than 5 days
    cutoff = (now - timedelta(days=5)).strftime("%Y-%m-%d")

    result = (
        supabase_client.table("loyers")
        .select("id, id_bien, id_sci, date_loyer, montant, biens(id_sci, adresse, ville)")
        .in_("statut", ["en_attente", "en_retard"])
        .lt("date_loyer", cutoff)
        .execute()
    )

    notified = 0
    for loyer in result.data or []:
        sci_id = loyer.get("id_sci") or (loyer.get("biens") or {}).get("id_sci")
        if not sci_id:
            continue

        bien = loyer.get("biens") or {}
        adresse = bien.get("adresse", "un bien")

        # Calculate days late
        try:
            loyer_date = datetime.strptime(loyer["date_loyer"], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            continue
        days_late = (now - loyer_date).days

        owners = (
            supabase_client.table("associes")
            .select("user_id")
            .eq("id_sci", sci_id)
            .not_.is_("user_id", "null")
            .execute()
        )

        for level in _LATE_PAYMENT_LEVELS:
            if days_late < level["days"]:
                continue

            dedup_key = f"late_{loyer['id']}_j{level['days']}"
            metadata = {
                "loyer_id": loyer["id"],
                "bien_adresse": adresse,
                "days_late": days_late,
                "dedup_key": dedup_key,
            }
            if level["severity"] == "critical":
                metadata["severity"] = "critical"

            for owner in owners.data or []:
                created = await create_notification_with_email(
                    supabase_client,
                    user_id=owner["user_id"],
                    notification_type="late_payment",
                    data={
                        "title": f"{level['title_prefix']} \u2014 {adresse}",
                        "message": (
                            f"Le loyer du {loyer['date_loyer']} ({loyer['montant']} EUR) "
                            f"pour {adresse} est impayé depuis {days_late} jours."
                        ),
                        "metadata": metadata,
                    },
                )
                if created:
                    notified += 1

    logger.info("check_late_payments_complete", notified=notified)
    return notified


# ── TASK 4: Renouvellement bail tacite ──────────────────────────────────


async def check_bail_renewal(supabase_client) -> int:
    """Handle tacit bail renewals and upcoming conge deadlines.

    1. Find baux where date_fin is passed AND statut='en_cours'
       → Tacitly renew: +3 years (nu) or +1 year (meuble)
       → Notify owner of tacit renewal

    2. Find baux expiring in 6+ months with no conge
       → Notify about conge bailleur deadline
    """
    today = date.today()
    today_str = today.isoformat()
    notified = 0

    # --- Part 1: Tacit renewals (date_fin passed, still en_cours) ---
    expired_result = (
        supabase_client.table("baux")
        .select("id, id_bien, date_debut, date_fin, statut, biens(id_sci, adresse, ville, type_locatif)")
        .eq("statut", "en_cours")
        .lt("date_fin", today_str)
        .execute()
    )

    for bail in (expired_result.data or []):
        if not bail.get("date_fin"):
            continue

        bien = bail.get("biens") or {}
        sci_id = bien.get("id_sci")
        if not sci_id:
            continue

        type_locatif = bien.get("type_locatif", "nu")

        # Calculate new end date: +3 years (nu/mixte) or +1 year (meuble)
        try:
            old_date_fin = datetime.strptime(bail["date_fin"], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue

        if type_locatif == "meuble":
            new_date_fin = old_date_fin.replace(year=old_date_fin.year + 1)
        else:
            new_date_fin = old_date_fin.replace(year=old_date_fin.year + 3)

        # Update the bail with new date_fin
        supabase_client.table("baux").update({
            "date_fin": new_date_fin.isoformat(),
        }).eq("id", bail["id"]).execute()

        # Resolve locataire names for the notification
        bl_result = (
            supabase_client.table("bail_locataires")
            .select("id_locataire")
            .eq("id_bail", bail["id"])
            .execute()
        )
        locataire_names = []
        for bl in (bl_result.data or []):
            loc_result = (
                supabase_client.table("locataires")
                .select("nom")
                .eq("id", bl["id_locataire"])
                .execute()
            )
            for loc in (loc_result.data or []):
                locataire_names.append(loc.get("nom", "").strip())

        locataire_label = ", ".join(locataire_names) if locataire_names else "le locataire"
        adresse = bien.get("adresse", "un bien")

        owners = (
            supabase_client.table("associes")
            .select("user_id")
            .eq("id_sci", sci_id)
            .not_.is_("user_id", "null")
            .execute()
        )

        for owner in (owners.data or []):
            created = await create_notification_with_email(
                supabase_client,
                user_id=owner["user_id"],
                notification_type="bail_renewal",
                data={
                    "title": f"Renouvellement tacite \u2014 {adresse}",
                    "message": (
                        f"Le bail de {locataire_label} a ete tacitement "
                        f"reconduit jusqu'au {new_date_fin.strftime('%d/%m/%Y')}."
                    ),
                    "metadata": {
                        "bail_id": bail["id"],
                        "bien_adresse": adresse,
                        "new_date_fin": new_date_fin.isoformat(),
                        "dedup_key": f"renewal_{bail['id']}_{new_date_fin.isoformat()}",
                    },
                },
            )
            if created:
                notified += 1

    # --- Part 2: Upcoming conge bailleur deadlines (6+ months before expiry) ---
    six_months_later = today.replace(
        year=today.year + (1 if today.month > 6 else 0),
        month=((today.month + 5) % 12) + 1,
        day=1,
    )
    horizon_str = six_months_later.isoformat()

    upcoming_result = (
        supabase_client.table("baux")
        .select("id, id_bien, date_fin, biens(id_sci, adresse, ville)")
        .eq("statut", "en_cours")
        .gte("date_fin", horizon_str)
        .execute()
    )

    for bail in (upcoming_result.data or []):
        if not bail.get("date_fin"):
            continue

        bien = bail.get("biens") or {}
        sci_id = bien.get("id_sci")
        if not sci_id:
            continue

        try:
            bail_date_fin = datetime.strptime(bail["date_fin"], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue

        months_until = (bail_date_fin.year - today.year) * 12 + (bail_date_fin.month - today.month)
        # Conge must be sent 6 months before expiry
        if months_until > 12:
            continue

        owners = (
            supabase_client.table("associes")
            .select("user_id")
            .eq("id_sci", sci_id)
            .not_.is_("user_id", "null")
            .execute()
        )

        adresse = bien.get("adresse", "un bien")
        for owner in (owners.data or []):
            created = await create_notification_with_email(
                supabase_client,
                user_id=owner["user_id"],
                notification_type="bail_conge_deadline",
                data={
                    "title": f"Deadline congé bailleur \u2014 {adresse}",
                    "message": (
                        f"Le bail pour {adresse} expire le {bail['date_fin']}. "
                        f"Deadline conge bailleur dans {months_until} mois."
                    ),
                    "metadata": {
                        "bail_id": bail["id"],
                        "bien_adresse": adresse,
                        "date_fin": bail["date_fin"],
                        "months_until": months_until,
                        "dedup_key": f"conge_{bail['id']}_{bail['date_fin']}",
                    },
                },
            )
            if created:
                notified += 1

    logger.info("check_bail_renewal_complete", notified=notified)
    return notified


# ── TASK: Charges recurrentes auto-generees ───────────────────────────


_RECURRING_CHARGE_TYPES = {"copropriete", "taxe_fonciere"}

# Quarter start months (Jan=1, Apr=4, Jul=7, Oct=10)
_QUARTER_MONTHS = {1, 4, 7, 10}


async def check_recurring_charges(supabase_client) -> int:
    """On the 1st of each quarter, auto-create charge records for all biens.

    Looks at existing charges of type copropriete / taxe_fonciere,
    and reproduces them for the current quarter using the last known amount.
    Skips if a charge already exists for this bien + type + quarter.
    """
    today = date.today()

    # Only run on the 1st of a quarter month
    if today.day != 1 or today.month not in _QUARTER_MONTHS:
        return 0

    quarter_start = today.replace(day=1).isoformat()
    # Quarter end: last day of the quarter
    quarter_end_month = today.month + 2
    if quarter_end_month == 3:
        quarter_end = date(today.year, 3, 31).isoformat()
    elif quarter_end_month == 6:
        quarter_end = date(today.year, 6, 30).isoformat()
    elif quarter_end_month == 9:
        quarter_end = date(today.year, 9, 30).isoformat()
    else:
        quarter_end = date(today.year, 12, 31).isoformat()

    created_count = 0

    # Fetch all biens
    biens_result = supabase_client.table("biens").select("id, id_sci").execute()
    biens = biens_result.data or []

    for bien in biens:
        bien_id = bien.get("id")
        id_sci = bien.get("id_sci")
        if not bien_id or not id_sci:
            continue

        for charge_type in _RECURRING_CHARGE_TYPES:
            # Check if a charge already exists for this bien + type in the current quarter
            existing = (
                supabase_client.table("charges")
                .select("id")
                .eq("id_bien", bien_id)
                .eq("type_charge", charge_type)
                .gte("date_paiement", quarter_start)
                .lte("date_paiement", quarter_end)
                .execute()
            )
            if existing.data:
                continue

            # Find the most recent charge of this type for this bien (template)
            last_charge = (
                supabase_client.table("charges")
                .select("montant")
                .eq("id_bien", bien_id)
                .eq("type_charge", charge_type)
                .order("date_paiement", desc=True)
                .limit(1)
                .execute()
            )
            if not last_charge.data:
                continue

            montant = last_charge.data[0].get("montant")
            if not montant or float(montant) <= 0:
                continue

            # Create the new charge record
            supabase_client.table("charges").insert({
                "id_bien": bien_id,
                "id_sci": id_sci,
                "type_charge": charge_type,
                "montant": float(montant),
                "date_paiement": quarter_start,
            }).execute()
            created_count += 1

    logger.info("check_recurring_charges_complete", created=created_count)
    return created_count


async def check_regularisation_charges_reminder(supabase_client) -> int:
    """In January, remind landlords to regularize charges for the previous year.

    Loi ALUR art. 23 — obligation de régularisation annuelle.
    Checks all active baux and notifies if no confirmed regularisation
    exists for the previous calendar year.
    """
    today = date.today()

    # Only run in January
    if today.month != 1:
        return 0

    previous_year = today.year - 1
    notified = 0

    # Fetch all active baux
    result = (
        supabase_client.table("baux")
        .select("id, id_bien, charges_locatives, biens(id_sci, adresse, ville)")
        .eq("statut", "en_cours")
        .execute()
    )

    for bail in result.data or []:
        charges_locatives = float(bail.get("charges_locatives") or 0)
        if charges_locatives <= 0:
            continue

        bien = bail.get("biens") or {}
        sci_id = bien.get("id_sci")
        if not sci_id:
            continue

        id_bien = bail.get("id_bien")
        bail_id = bail.get("id")

        # Check if a confirmed regularisation already exists for previous year
        existing = (
            supabase_client.table("regularisations_charges")
            .select("id")
            .eq("id_bien", id_bien)
            .eq("id_bail", bail_id)
            .eq("annee", previous_year)
            .eq("statut", "confirme")
            .execute()
        )
        if existing.data:
            continue

        adresse = bien.get("adresse", "un bien")

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
                notification_type="regularisation_charges",
                data={
                    "title": f"Régularisation des charges {previous_year} — {adresse}",
                    "message": (
                        f"La régularisation annuelle des charges pour {adresse} "
                        f"(année {previous_year}) n'a pas encore été effectuée. "
                        f"Obligation légale (loi ALUR art. 23)."
                    ),
                    "metadata": {
                        "bail_id": bail_id,
                        "bien_id": id_bien,
                        "bien_adresse": adresse,
                        "annee": previous_year,
                        "dedup_key": f"regularisation_{bail_id}_{previous_year}",
                    },
                },
            )
            if created:
                notified += 1

    logger.info("check_regularisation_charges_reminder_complete", notified=notified)
    return notified


async def check_depot_garantie_restitution(supabase_client) -> int:
    """Alert landlords when a terminated bail has an unrestituted depot de garantie.

    Legal deadlines (loi du 6 juillet 1989, art. 22) :
    - 1 month  if état des lieux de sortie is conforme (= etat_lieux_sortie IS NOT NULL)
    - 2 months if no état des lieux de sortie recorded

    Checks baux where:
    - statut = 'termine'
    - depot_garantie > 0
    - depot_restitue = FALSE
    - date_fin + deadline has passed
    """
    today = date.today()
    notified = 0

    # Fetch all terminated baux with unrestituted depot
    result = (
        supabase_client.table("baux")
        .select("id, id_bien, depot_garantie, date_fin, etat_lieux_sortie, biens(id_sci, adresse, ville)")
        .eq("statut", "termine")
        .eq("depot_restitue", False)
        .gt("depot_garantie", 0)
        .not_.is_("date_fin", "null")
        .execute()
    )

    for bail in result.data or []:
        try:
            date_fin = datetime.strptime(bail["date_fin"], "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue

        # Deadline: 1 month (30 days) if conforme EDL sortie, else 2 months (60 days)
        # Use timedelta to avoid ValueError on month-end dates (e.g. Jan 31 + 1 month ≠ Feb 31)
        has_edl_sortie = bool(bail.get("etat_lieux_sortie"))
        deadline_days = 30 if has_edl_sortie else 60
        deadline_date = date_fin + timedelta(days=deadline_days)

        if today < deadline_date:
            continue

        bien = bail.get("biens") or {}
        sci_id = bien.get("id_sci")
        if not sci_id:
            continue

        adresse = bien.get("adresse", "un bien")
        depot = float(bail.get("depot_garantie") or 0)
        days_overdue = (today - deadline_date).days

        owners = (
            supabase_client.table("associes")
            .select("user_id")
            .eq("id_sci", sci_id)
            .not_.is_("user_id", "null")
            .execute()
        )

        dedup_key = f"depot_{bail['id']}_{deadline_date.isoformat()}"

        for owner in owners.data or []:
            created = await create_notification_with_email(
                supabase_client,
                user_id=owner["user_id"],
                notification_type="depot_garantie_restitution",
                data={
                    "title": f"Dépôt de garantie à restituer — {adresse}",
                    "message": (
                        f"Le bail pour {adresse} est terminé depuis le {bail['date_fin']}. "
                        f"Le dépôt de garantie ({depot:.2f} EUR) doit être restitué "
                        f"sous {deadline_days // 30} mois (EDL {'conforme' if has_edl_sortie else 'absent'}). "
                        f"Délai dépassé de {days_overdue} jour(s)."
                    ),
                    "metadata": {
                        "bail_id": bail["id"],
                        "bien_adresse": adresse,
                        "depot_garantie": depot,
                        "date_fin": bail["date_fin"],
                        "deadline_days": deadline_days,
                        "days_overdue": days_overdue,
                        "dedup_key": dedup_key,
                    },
                },
            )
            if created:
                notified += 1

    logger.info("check_depot_garantie_restitution_complete", notified=notified)
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
            created = await create_notification_with_email(
                supabase_client,
                user_id=owner["user_id"],
                notification_type="bail_expiring",
                data={
                    "title": "Bail expirant",
                    "message": f"Le bail pour {bien.get('adresse', 'un bien')} expire le {bail['date_fin']}.",
                    "metadata": {"bail_id": bail["id"], "bien_adresse": bien.get("adresse"), "dedup_key": f"bail_{bail['id']}"},
                },
            )
            if created:
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
            created = await create_notification_with_email(
                supabase_client,
                user_id=owner["user_id"],
                notification_type="quittance_pending",
                data={
                    "title": "Quittance en attente",
                    "message": f"Le loyer du {loyer['date_loyer']} pour {bien.get('adresse', 'un bien')} est payé mais la quittance n'a pas été générée.",
                    "metadata": {"loyer_id": loyer["id"], "bien_adresse": bien.get("adresse"), "dedup_key": f"quittance_{loyer['id']}"},
                },
            )
            if created:
                notified += 1

    logger.info("check_pending_quittances_complete", notified=notified)
    return notified


async def check_expiring_pno(supabase_client) -> int:
    """Find PNO insurance policies expiring within 30 days."""
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    horizon = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")

    result = (
        supabase_client.table("assurances_pno")
        .select("id, id_bien, compagnie, date_echeance, biens(id_sci, adresse, ville)")
        .gte("date_echeance", now)
        .lte("date_echeance", horizon)
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
            created = await create_notification_with_email(
                supabase_client,
                user_id=owner["user_id"],
                notification_type="pno_expiring",
                data={
                    "title": "PNO expirant",
                    "message": f"L'assurance PNO ({pno.get('compagnie', 'N/A')}) pour {bien.get('adresse', 'un bien')} expire le {pno['date_echeance']}.",
                    "metadata": {"pno_id": pno["id"], "bien_adresse": bien.get("adresse"), "dedup_key": f"pno_{pno['id']}"},
                },
            )
            if created:
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
    # TODO: La date du 31/03 est valable pour les exercices clos au 31/12 uniquement.
    # Pour un exercice non-standard, le délai légal est de 3 mois après la clôture.
    # Le modèle SCI ne stocke pas encore la date de clôture d'exercice — à implémenter.
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
    result = supabase_client.table("sci").select("id, nom, regime_fiscal, date_cloture_exercice").execute()
    scis = result.data or []
    if not scis:
        return 0

    notified = 0
    for sci in scis:
        sci_regime = (sci.get("regime_fiscal") or "").upper()

        # Resolve fiscal year-end from date_cloture_exercice (NULL → Dec 31)
        cloture_raw: str | None = sci.get("date_cloture_exercice")
        if cloture_raw:
            try:
                from datetime import date as _date
                _cloture = _date.fromisoformat(cloture_raw)
                cloture_month = _cloture.month
                cloture_day = _cloture.day
            except (ValueError, TypeError):
                cloture_month, cloture_day = 12, 31
        else:
            cloture_month, cloture_day = 12, 31

        # Build the closing date in the current (or previous) year that
        # produces a sensible deadline reference.
        try:
            cloture_ref = datetime(year, cloture_month, cloture_day, tzinfo=timezone.utc)
        except ValueError:
            # Edge case: Feb 29 in non-leap year → use Feb 28
            cloture_ref = datetime(year, cloture_month, 28, tzinfo=timezone.utc)

        for deadline in FISCAL_DEADLINES:
            # Skip regime-specific deadlines that don't apply
            if deadline["regime"] and deadline["regime"] != sci_regime:
                continue

            # Compute deadline date:
            # - liasse_fiscale_is  → 3 months after closing
            # - ag_annuelle        → 6 months after closing
            # - all others         → fixed calendar date (unchanged by custom closing)
            if deadline["key"] in ("liasse_fiscale_is", "ag_annuelle"):
                # Compute deadline = N months after fiscal year closing.
                # We try two reference years (current and previous) and pick
                # the one that is upcoming (days_until >= 0) and within the
                # advance window. This handles closings in Dec (e.g. Dec 31:
                # liasse = Mar 31, AG = Jun 30) correctly regardless of which
                # part of the year we're in.
                _offset_months = 3 if deadline["key"] == "liasse_fiscale_is" else 6
                _advance = deadline["advance_days"]

                def _compute_relative(base_year: int) -> datetime:
                    _rm = cloture_month + _offset_months
                    _yo = (_rm - 1) // 12
                    _ty = base_year + _yo
                    _tm = ((_rm - 1) % 12) + 1
                    _md = calendar.monthrange(_ty, _tm)[1]
                    return datetime(_ty, _tm, min(cloture_day, _md), tzinfo=timezone.utc)

                _d_curr = _compute_relative(year)
                _d_prev = _compute_relative(year - 1)
                _days_curr = (_d_curr - now).days
                _days_prev = (_d_prev - now).days

                # Prefer current-year base if within window; else try prev-year base
                if 0 <= _days_curr <= _advance:
                    deadline_date = _d_curr
                elif 0 <= _days_prev <= _advance:
                    deadline_date = _d_prev
                else:
                    deadline_date = _d_curr
            else:
                deadline_date = datetime(year, deadline["month"], deadline["day"], tzinfo=timezone.utc)

            days_until = (deadline_date - now).days

            # Only notify within the advance window and if not past
            if days_until < 0 or days_until > deadline["advance_days"]:
                continue

            # Human-readable closing date label for messages
            cloture_label = f"{cloture_day:02d}/{cloture_month:02d}"

            # Fetch SCI owners
            owners = (
                supabase_client.table("associes")
                .select("user_id")
                .eq("id_sci", sci["id"])
                .not_.is_("user_id", "null")
                .execute()
            )

            for owner in owners.data or []:
                base_message = f"Échéance le {deadline_date.strftime('%d/%m/%Y')} ({days_until} jours restants)."
                if deadline["key"] in ("liasse_fiscale_is", "ag_annuelle"):
                    base_message += f" (basé sur la clôture de l'exercice au {cloture_label})"

                created = await create_notification_with_email(
                    supabase_client,
                    user_id=owner["user_id"],
                    notification_type="fiscal_deadline",
                    data={
                        "title": f"{deadline['label']} — {sci['nom']}",
                        "message": base_message,
                        "metadata": {
                            "sci_id": sci["id"],
                            "deadline_key": deadline["key"],
                            "deadline_date": deadline_date.strftime("%Y-%m-%d"),
                            "days_until": days_until,
                            "dedup_key": f"fiscal_{sci['id']}_{deadline['key']}_{year}",
                        },
                    },
                )
                if created:
                    notified += 1

    logger.info("check_fiscal_deadlines_complete", notified=notified)
    return notified
