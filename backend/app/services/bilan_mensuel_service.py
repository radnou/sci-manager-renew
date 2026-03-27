"""Service for generating monthly accounting bilans (snapshots).

Aggregates loyers + charges per bien, per SCI, and at portfolio level
for a given YYYY-MM period.  Results are cached in the bilans_mensuels
table so subsequent requests return the pre-computed snapshot.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import structlog

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------


async def generate_bilan_mensuel(client, user_id: str, periode: str) -> dict:
    """Build the full bilan data structure for a given month.

    Args:
        client: Supabase service-role client (bypasses RLS).
        user_id: UUID of the user.
        periode: "YYYY-MM" string.

    Returns:
        Complete bilan dict with portefeuille / scis / biens breakdown.
    """
    # 1. Get all SCIs for user via associes
    assoc_res = (
        client.table("associes")
        .select("id_sci")
        .eq("user_id", user_id)
        .execute()
    )
    sci_ids = list({row["id_sci"] for row in (assoc_res.data or [])})

    if not sci_ids:
        return _empty_bilan(periode)

    # SCI details
    scis_res = (
        client.table("sci")
        .select("id, nom")
        .in_("id", sci_ids)
        .execute()
    )
    sci_map = {str(s["id"]): s["nom"] for s in (scis_res.data or [])}

    # 2. Get all biens for those SCIs
    biens_res = (
        client.table("biens")
        .select("id, id_sci, adresse, ville")
        .in_("id_sci", sci_ids)
        .execute()
    )
    biens = biens_res.data or []
    bien_ids = [str(b["id"]) for b in biens]
    # Map bien_id -> sci_id
    bien_sci_map = {str(b["id"]): str(b["id_sci"]) for b in biens}
    # Map bien_id -> bien row
    bien_detail_map = {str(b["id"]): b for b in biens}

    if not bien_ids:
        return _empty_bilan(periode)

    # Date range for the month
    date_start = f"{periode}-01"
    # Compute last day: use next month
    year, month = int(periode[:4]), int(periode[5:7])
    if month == 12:
        date_end = f"{year + 1}-01-01"
    else:
        date_end = f"{year}-{month + 1:02d}-01"

    # 3. Get loyers for the period
    loyers_res = (
        client.table("loyers")
        .select("id, id_bien, montant, statut, date_loyer, id_locataire")
        .in_("id_bien", bien_ids)
        .gte("date_loyer", date_start)
        .lt("date_loyer", date_end)
        .execute()
    )
    loyers = loyers_res.data or []

    # 4. Get charges for the period (date_paiement in month)
    charges_res = (
        client.table("charges")
        .select("id, id_bien, montant, type_charge, date_paiement")
        .in_("id_bien", bien_ids)
        .gte("date_paiement", date_start)
        .lt("date_paiement", date_end)
        .execute()
    )
    charges = charges_res.data or []

    # Collect locataire IDs for name resolution
    locataire_ids = list({
        str(l["id_locataire"])
        for l in loyers
        if l.get("id_locataire")
    })
    locataire_map: dict[str, str] = {}
    if locataire_ids:
        loc_res = (
            client.table("locataires")
            .select("id, nom, prenom")
            .in_("id", locataire_ids)
            .execute()
        )
        for loc in (loc_res.data or []):
            full = f"{loc.get('prenom', '')} {loc.get('nom', '')}".strip()
            locataire_map[str(loc["id"])] = full or loc.get("nom", "?")

    # --------------- Aggregate per bien ---------------
    # Group loyers by bien
    bien_loyers: dict[str, list] = {bid: [] for bid in bien_ids}
    for l in loyers:
        bid = str(l.get("id_bien", ""))
        if bid in bien_loyers:
            bien_loyers[bid].append(l)

    # Group charges by bien
    bien_charges: dict[str, list] = {bid: [] for bid in bien_ids}
    for c in charges:
        bid = str(c.get("id_bien", ""))
        if bid in bien_charges:
            bien_charges[bid].append(c)

    # Build per-bien data
    biens_data: dict[str, dict] = {}
    for bid in bien_ids:
        b_loyers = bien_loyers[bid]
        b_charges = bien_charges[bid]
        detail = bien_detail_map[bid]

        rev_attendus = sum(l.get("montant") or 0 for l in b_loyers)
        rev_encaisses = sum(
            l.get("montant") or 0
            for l in b_loyers
            if l.get("statut") in ("paye", "paid")
        )
        impayes = sum(
            l.get("montant") or 0
            for l in b_loyers
            if l.get("statut") in ("en_retard", "en_attente", "late", "pending")
        )
        charges_total = sum(c.get("montant") or 0 for c in b_charges)

        total_entrees = round(rev_encaisses, 2)
        total_sorties = round(charges_total, 2)
        solde = round(rev_encaisses - charges_total, 2)

        # Build BilanLigne[] from loyers and charges
        lignes: list[dict] = []
        for l in b_loyers:
            loc_name = locataire_map.get(str(l.get("id_locataire", "")), "")
            label = f"Loyer {loc_name}".strip() if loc_name else "Loyer"
            montant = l.get("montant") or 0
            statut = l.get("statut", "")
            is_paid = statut in ("paye", "paid")
            lignes.append({
                "date": l.get("date_loyer", ""),
                "libelle": label,
                "entrees": round(montant, 2) if is_paid else 0,
                "sorties": 0,
                "solde": 0,  # computed after sorting
                "type": "loyer",
                "statut": statut,
            })
        for c in b_charges:
            type_charge = c.get("type_charge", "Charge")
            montant = c.get("montant") or 0
            lignes.append({
                "date": c.get("date_paiement", ""),
                "libelle": f"Charge {type_charge}",
                "entrees": 0,
                "sorties": round(montant, 2),
                "solde": 0,  # computed after sorting
                "type": "charge",
                "statut": None,
            })

        # Sort by date and compute running solde
        lignes.sort(key=lambda x: x.get("date", ""))
        running = 0.0
        for ligne in lignes:
            running += ligne["entrees"] - ligne["sorties"]
            ligne["solde"] = round(running, 2)

        # Keep legacy fields for PDF service compatibility
        loyers_detail = [
            {
                "date": l.get("date_loyer", ""),
                "montant": l.get("montant") or 0,
                "statut": l.get("statut", ""),
                "locataire": locataire_map.get(str(l.get("id_locataire", "")), ""),
            }
            for l in b_loyers
        ]
        charges_detail = [
            {
                "type": c.get("type_charge", ""),
                "montant": c.get("montant") or 0,
                "date": c.get("date_paiement", ""),
            }
            for c in b_charges
        ]

        biens_data[bid] = {
            "bien_id": bid,
            "adresse": detail.get("adresse") or "",
            "ville": detail.get("ville") or "",
            "lignes": lignes,
            "total_entrees": total_entrees,
            "total_sorties": total_sorties,
            "solde": solde,
            # Legacy fields kept for PDF service
            "revenus_attendus": round(rev_attendus, 2),
            "revenus_encaisses": total_entrees,
            "impayes": round(impayes, 2),
            "charges": total_sorties,
            "cashflow_net": solde,
            "loyers": loyers_detail,
            "charges_detail": charges_detail,
        }

    # --------------- Aggregate per SCI ---------------
    scis_data = []
    for sci_id in sci_ids:
        sci_id_str = str(sci_id)
        sci_biens = [
            biens_data[bid]
            for bid in bien_ids
            if bien_sci_map.get(bid) == sci_id_str and bid in biens_data
        ]
        rev_attendus = sum(b["revenus_attendus"] for b in sci_biens)
        rev_encaisses = sum(b["revenus_encaisses"] for b in sci_biens)
        impayes = sum(b["impayes"] for b in sci_biens)
        charges_total = sum(b["charges"] for b in sci_biens)
        cashflow = rev_encaisses - charges_total
        taux = (rev_encaisses / rev_attendus * 100) if rev_attendus > 0 else 0

        sci_total_entrees = round(rev_encaisses, 2)
        sci_total_sorties = round(charges_total, 2)
        sci_solde = round(cashflow, 2)

        scis_data.append({
            "sci_id": sci_id_str,
            "sci_nom": sci_map.get(sci_id_str, "?"),
            "biens": sci_biens,
            "total_entrees": sci_total_entrees,
            "total_sorties": sci_total_sorties,
            "solde": sci_solde,
            # Legacy fields kept for PDF service
            "revenus_attendus": round(rev_attendus, 2),
            "revenus_encaisses": sci_total_entrees,
            "impayes": round(impayes, 2),
            "charges": sci_total_sorties,
            "cashflow_net": sci_solde,
            "taux_recouvrement": round(taux, 1),
        })

    # --------------- Portfolio aggregate ---------------
    p_rev_attendus = sum(s["revenus_attendus"] for s in scis_data)
    p_rev_encaisses = sum(s["revenus_encaisses"] for s in scis_data)
    p_impayes = sum(s["impayes"] for s in scis_data)
    p_charges = sum(s["charges"] for s in scis_data)
    p_cashflow = p_rev_encaisses - p_charges
    p_taux = (p_rev_encaisses / p_rev_attendus * 100) if p_rev_attendus > 0 else 0

    p_total_entrees = round(p_rev_encaisses, 2)
    p_total_sorties = round(p_charges, 2)
    p_solde = round(p_cashflow, 2)

    return {
        "periode": periode,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scis": scis_data,
        "total_entrees": p_total_entrees,
        "total_sorties": p_total_sorties,
        "solde": p_solde,
        "kpis": {
            "revenus_attendus": round(p_rev_attendus, 2),
            "revenus_encaisses": p_total_entrees,
            "charges_totales": p_total_sorties,
            "cashflow_net": p_solde,
            "taux_recouvrement": round(p_taux, 1),
            "nb_biens": len(bien_ids),
            "nb_scis": len(sci_ids),
        },
        # Legacy field kept for PDF service
        "portefeuille": {
            "revenus_attendus": round(p_rev_attendus, 2),
            "revenus_encaisses": p_total_entrees,
            "impayes": round(p_impayes, 2),
            "charges": p_total_sorties,
            "cashflow_net": p_solde,
            "taux_recouvrement": round(p_taux, 1),
            "nb_biens": len(bien_ids),
            "nb_scis": len(sci_ids),
        },
    }


# ---------------------------------------------------------------------------
# Get or generate (with cache in DB)
# ---------------------------------------------------------------------------


async def get_or_generate_bilan(
    client,
    user_id: str,
    periode: str,
    scope: str = "portefeuille",
    scope_id: str | None = None,
    force_refresh: bool = False,
) -> dict:
    """Return a bilan from cache or generate + store it.

    Args:
        client: Supabase service-role client.
        user_id: UUID of the user.
        periode: "YYYY-MM".
        scope: "portefeuille" | "sci" | "bien".
        scope_id: UUID of the SCI or bien (None for portefeuille).
        force_refresh: If True, regenerate even if cached.
    """
    if not force_refresh:
        # Check cache
        query = (
            client.table("bilans_mensuels")
            .select("data, scope_nom")
            .eq("user_id", user_id)
            .eq("periode", periode)
            .eq("scope", scope)
        )
        if scope_id:
            query = query.eq("scope_id", scope_id)
        else:
            query = query.is_("scope_id", "null")

        result = query.execute()
        if result.data:
            return result.data[0]["data"]

    # Generate full bilan
    bilan = await generate_bilan_mensuel(client, user_id, periode)

    # Extract the right scope slice
    if scope == "portefeuille":
        scoped_data = bilan
        scope_nom = "Portefeuille"
    elif scope == "sci" and scope_id:
        scoped_data = bilan
        # Also extract sci-specific view
        sci_match = next(
            (s for s in bilan.get("scis", []) if s["sci_id"] == scope_id),
            None,
        )
        if sci_match:
            scoped_data = {
                "periode": bilan["periode"],
                "generated_at": bilan["generated_at"],
                "sci": sci_match,
            }
            scope_nom = sci_match.get("sci_nom", "SCI")
        else:
            scope_nom = "SCI"
    elif scope == "bien" and scope_id:
        scoped_data = bilan
        # Find bien across all SCIs
        bien_match = None
        for sci in bilan.get("scis", []):
            for b in sci.get("biens", []):
                if b["bien_id"] == scope_id:
                    bien_match = b
                    break
            if bien_match:
                break
        if bien_match:
            scoped_data = {
                "periode": bilan["periode"],
                "generated_at": bilan["generated_at"],
                "bien": bien_match,
            }
            scope_nom = f"{bien_match.get('adresse', '')} {bien_match.get('ville', '')}".strip()
        else:
            scope_nom = "Bien"
    else:
        scoped_data = bilan
        scope_nom = "Portefeuille"

    # Upsert into cache (portefeuille-level always stored)
    _upsert_bilan(client, user_id, periode, scope, scope_id, scope_nom, scoped_data)

    return scoped_data


def _upsert_bilan(
    client, user_id: str, periode: str, scope: str,
    scope_id: str | None, scope_nom: str, data: dict,
) -> None:
    """Insert or update a bilan snapshot in the DB."""
    try:
        row = {
            "user_id": user_id,
            "periode": periode,
            "scope": scope,
            "scope_id": scope_id,
            "scope_nom": scope_nom,
            "data": data,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        client.table("bilans_mensuels").upsert(
            row,
            on_conflict="user_id,periode,scope,scope_id",
        ).execute()
    except Exception:
        logger.warning("bilan_upsert_failed", user_id=user_id, periode=periode, exc_info=True)


# ---------------------------------------------------------------------------
# List available periods
# ---------------------------------------------------------------------------


async def list_periodes(client, user_id: str) -> list[str]:
    """Return sorted list of YYYY-MM strings where loyers exist for the user."""
    assoc_res = (
        client.table("associes")
        .select("id_sci")
        .eq("user_id", user_id)
        .execute()
    )
    sci_ids = list({row["id_sci"] for row in (assoc_res.data or [])})
    if not sci_ids:
        return []

    biens_res = (
        client.table("biens")
        .select("id")
        .in_("id_sci", sci_ids)
        .execute()
    )
    bien_ids = [str(b["id"]) for b in (biens_res.data or [])]
    if not bien_ids:
        return []

    loyers_res = (
        client.table("loyers")
        .select("date_loyer")
        .in_("id_bien", bien_ids)
        .execute()
    )
    months = set()
    for l in (loyers_res.data or []):
        dl = l.get("date_loyer", "")
        if dl and len(dl) >= 7:
            months.add(dl[:7])

    return sorted(months, reverse=True)


# ---------------------------------------------------------------------------
# Auto-generate (cron)
# ---------------------------------------------------------------------------


async def auto_generate_bilans(client) -> int:
    """Auto-generate bilans for all active users on the 2nd of each month.

    Called from the notification cron loop. Only runs on day 2.
    Returns count of bilans generated.
    """
    now = datetime.now(timezone.utc)
    if now.day != 2:
        return 0

    # Previous month
    if now.month == 1:
        prev_year, prev_month = now.year - 1, 12
    else:
        prev_year, prev_month = now.year, now.month - 1
    periode = f"{prev_year}-{prev_month:02d}"

    logger.info("auto_generate_bilans_start", periode=periode)

    # Get all users with active subscriptions
    subs_res = (
        client.table("subscriptions")
        .select("user_id")
        .in_("status", ["active", "paid"])
        .execute()
    )
    user_ids = list({row["user_id"] for row in (subs_res.data or [])})

    count = 0
    for uid in user_ids:
        try:
            await get_or_generate_bilan(
                client, uid, periode,
                scope="portefeuille", scope_id=None, force_refresh=False,
            )
            count += 1

            # Send email notification
            await _send_bilan_email(client, uid, periode)
        except Exception:
            logger.warning("auto_bilan_user_failed", user_id=uid, exc_info=True)

    logger.info("auto_generate_bilans_done", periode=periode, count=count)
    return count


async def _send_bilan_email(client, user_id: str, periode: str) -> None:
    """Send bilan notification email to user."""
    try:
        # Get user email
        user_res = (
            client.table("auth.users")
            .select("email")
            .eq("id", user_id)
            .execute()
        )
        if not user_res.data:
            # Fallback: try associes table for email
            assoc_res = (
                client.table("associes")
                .select("email")
                .eq("user_id", user_id)
                .limit(1)
                .execute()
            )
            if not assoc_res.data:
                return
            email = assoc_res.data[0].get("email")
        else:
            email = user_res.data[0].get("email")

        if not email:
            return

        # Check notification preferences
        pref_res = (
            client.table("notification_preferences")
            .select("email_enabled")
            .eq("user_id", user_id)
            .eq("notification_type", "bilan_mensuel")
            .execute()
        )
        if pref_res.data and not pref_res.data[0].get("email_enabled", True):
            return

        from app.services.email_service import email_service

        # Format month name in French
        month_names = [
            "", "janvier", "f\u00e9vrier", "mars", "avril", "mai", "juin",
            "juillet", "ao\u00fbt", "septembre", "octobre", "novembre", "d\u00e9cembre",
        ]
        year, month = int(periode[:4]), int(periode[5:7])
        mois_label = f"{month_names[month]} {year}"

        await email_service.send_email(
            to=email,
            subject=f"Votre bilan mensuel {mois_label} \u2014 G\u00e9rerSCI",
            template="bilan_mensuel.html",
            context={
                "mois_label": mois_label,
                "cta_url": f"{email_service.frontend_url}/finances",
                "cta_text": "Consulter mon bilan",
                "unsubscribe_url": f"{email_service.frontend_url}/settings",
            },
        )
    except Exception:
        logger.warning("bilan_email_failed", user_id=user_id, exc_info=True)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _empty_bilan(periode: str) -> dict:
    return {
        "periode": periode,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scis": [],
        "total_entrees": 0,
        "total_sorties": 0,
        "solde": 0,
        "kpis": {
            "revenus_attendus": 0,
            "revenus_encaisses": 0,
            "charges_totales": 0,
            "cashflow_net": 0,
            "taux_recouvrement": 0,
            "nb_biens": 0,
            "nb_scis": 0,
        },
        # Legacy field kept for PDF service
        "portefeuille": {
            "revenus_attendus": 0,
            "revenus_encaisses": 0,
            "impayes": 0,
            "charges": 0,
            "cashflow_net": 0,
            "taux_recouvrement": 0,
            "nb_biens": 0,
            "nb_scis": 0,
        },
    }
