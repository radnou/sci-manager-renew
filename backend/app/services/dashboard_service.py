"""Dashboard service — aggregates KPIs, alertes, SCI cards and recent activity."""

from __future__ import annotations

from datetime import date, timedelta

import structlog

from app.core.exceptions import DatabaseError

logger = structlog.get_logger(__name__)


def _get_user_sci_ids(client, user_id: str) -> list[str]:
    """Return list of SCI ids the user has access to via associes."""
    result = client.table("associes").select("id_sci").eq("user_id", user_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))
    return [str(row["id_sci"]) for row in (result.data or []) if row.get("id_sci")]


def _query_in_sci_ids(client, table: str, select: str, sci_ids: list[str]):
    """Query a table scoped by a list of SCI ids."""
    query = client.table(table).select(select)
    if hasattr(query, "in_"):
        result = query.in_("id_sci", sci_ids).execute()
    else:
        # Fallback for clients without in_ (e.g. tests)
        all_data: list[dict] = []
        for sci_id in sci_ids:
            result = client.table(table).select(select).eq("id_sci", sci_id).execute()
            if getattr(result, "error", None):
                raise DatabaseError(str(result.error))
            all_data.extend(result.data or [])
        return all_data

    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))
    return result.data or []


def _format_date_fr(iso_date: str) -> str:
    """Convert ISO date (2025-07-01) to French format (1 juillet 2025)."""
    MOIS_FR = [
        "", "janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre",
    ]
    try:
        d = date.fromisoformat(iso_date)
        return f"{d.day} {MOIS_FR[d.month]} {d.year}"
    except (ValueError, IndexError):
        return iso_date


async def get_alertes(client, user_id: str) -> list[dict]:
    """
    Return a list of alert objects for the user:
    - Loyers en retard (statut='en_retard' or no paiement_date and date > 5 days ago)
    - Baux expiring within 90 days
    Enriched with sci_nom, bien_adresse and link for frontend display.
    """
    sci_ids = _get_user_sci_ids(client, user_id)
    if not sci_ids:
        return []

    alertes: list[dict] = []
    today = date.today()
    five_days_ago = (today - timedelta(days=5)).isoformat()
    ninety_days_from_now = (today + timedelta(days=90)).isoformat()

    # --- Build lookup maps for SCI names and biens ---
    sci_names: dict[str, str] = {}
    for sci_id in sci_ids:
        result = client.table("sci").select("id,nom").eq("id", sci_id).execute()
        if not getattr(result, "error", None) and result.data:
            for row in result.data:
                sci_names[str(row["id"])] = row.get("nom") or row.get("name", "")

    all_biens = _query_in_sci_ids(client, "biens", "id,id_sci,adresse", sci_ids)
    biens_by_id: dict[str, dict] = {str(b["id"]): b for b in all_biens}

    # --- Loyers en retard ---
    loyers = _query_in_sci_ids(client, "loyers", "*", sci_ids)
    for loyer in loyers:
        statut = loyer.get("statut", "")
        paiement_date = loyer.get("paiement_date") or loyer.get("date_paiement")
        date_loyer = loyer.get("date_loyer", "")

        is_late = statut == "en_retard"
        is_overdue = (
            not paiement_date
            and statut != "paye"
            and date_loyer
            and date_loyer < five_days_ago
        )

        if is_late or is_overdue:
            sci_id = str(loyer.get("id_sci", ""))
            bien_id = str(loyer.get("id_bien", ""))
            bien = biens_by_id.get(bien_id, {})
            date_label = _format_date_fr(date_loyer) if date_loyer else date_loyer

            alertes.append({
                "type": "loyer_en_retard",
                "severity": "high",
                "message": f"Loyer impayé — {date_label}",
                "entity_id": loyer.get("id"),
                "entity_type": "loyer",
                "id_sci": sci_id,
                "montant": loyer.get("montant"),
                "date": date_loyer,
                "sci_nom": sci_names.get(sci_id, ""),
                "bien_adresse": bien.get("adresse", ""),
                "link": f"/scis/{sci_id}/biens/{bien_id}" if bien_id else None,
            })

    # --- Baux expirant bientôt ---
    try:
        locataires = _query_in_sci_ids(client, "locataires", "*", sci_ids)
        for loc in locataires:
            date_fin = loc.get("date_fin_bail") or loc.get("date_fin")
            statut = loc.get("statut", "en_cours")
            if date_fin and statut == "en_cours" and date_fin <= ninety_days_from_now:
                sci_id = str(loc.get("id_sci", ""))
                date_label = _format_date_fr(date_fin) if date_fin else date_fin
                alertes.append({
                    "type": "bail_expire_bientot",
                    "severity": "medium",
                    "message": f"Bail expire le {date_label}",
                    "entity_id": loc.get("id"),
                    "entity_type": "locataire",
                    "id_sci": sci_id,
                    "date": date_fin,
                    "sci_nom": sci_names.get(sci_id, ""),
                })
    except Exception:
        # locataires table may not have id_sci; skip gracefully
        logger.warning("alertes_bail_check_failed", user_id=user_id, exc_info=True)

    return alertes


async def get_portfolio_kpis(client, user_id: str) -> dict:
    """
    Return high-level portfolio KPIs:
    - sci_count, biens_count
    - taux_recouvrement (% loyers payés / total)
    - cashflow_net (somme loyers payés - somme charges)
    """
    sci_ids = _get_user_sci_ids(client, user_id)
    if not sci_ids:
        return {
            "sci_count": 0,
            "biens_count": 0,
            "taux_recouvrement": 0.0,
            "cashflow_net": 0.0,
            "loyers_total": 0.0,
            "loyers_payes": 0.0,
            "charges_total": 0.0,
        }

    sci_count = len(sci_ids)

    # Biens count
    biens = _query_in_sci_ids(client, "biens", "id", sci_ids)
    biens_count = len(biens)

    # Loyers
    loyers = _query_in_sci_ids(client, "loyers", "montant,statut", sci_ids)
    loyers_total = sum(float(l.get("montant") or 0) for l in loyers)
    loyers_payes = sum(
        float(l.get("montant") or 0) for l in loyers if l.get("statut") == "paye"
    )
    taux_recouvrement = round((loyers_payes / loyers_total * 100) if loyers_total > 0 else 0.0, 1)

    # Charges
    try:
        charges = _query_in_sci_ids(client, "charges", "montant", sci_ids)
        charges_total = sum(float(c.get("montant") or 0) for c in charges)
    except Exception:
        charges_total = 0.0
        logger.warning("kpi_charges_fetch_failed", user_id=user_id, exc_info=True)

    cashflow_net = round(loyers_payes - charges_total, 2)

    return {
        "sci_count": sci_count,
        "biens_count": biens_count,
        "taux_recouvrement": taux_recouvrement,
        "cashflow_net": cashflow_net,
        "loyers_total": round(loyers_total, 2),
        "loyers_payes": round(loyers_payes, 2),
        "charges_total": round(charges_total, 2),
    }


async def get_sci_cards(client, user_id: str) -> list[dict]:
    """
    Return a list of SCI summary cards:
    - nom, statut, biens_count, loyer_total, recouvrement %
    """
    sci_ids = _get_user_sci_ids(client, user_id)
    if not sci_ids:
        return []

    # Fetch SCIs
    scis_data: list[dict] = []
    for sci_id in sci_ids:
        result = client.table("sci").select("*").eq("id", sci_id).execute()
        if not getattr(result, "error", None) and result.data:
            scis_data.extend(result.data)

    # Fetch biens and loyers for all SCIs at once
    all_biens = _query_in_sci_ids(client, "biens", "id,id_sci", sci_ids)
    all_loyers = _query_in_sci_ids(client, "loyers", "id_sci,montant,statut", sci_ids)

    # Index by SCI
    biens_by_sci: dict[str, int] = {}
    for b in all_biens:
        sid = str(b.get("id_sci", ""))
        biens_by_sci[sid] = biens_by_sci.get(sid, 0) + 1

    loyers_by_sci: dict[str, dict] = {}
    for l in all_loyers:
        sid = str(l.get("id_sci", ""))
        if sid not in loyers_by_sci:
            loyers_by_sci[sid] = {"total": 0.0, "payes": 0.0}
        montant = float(l.get("montant") or 0)
        loyers_by_sci[sid]["total"] += montant
        if l.get("statut") == "paye":
            loyers_by_sci[sid]["payes"] += montant

    cards: list[dict] = []
    for sci in scis_data:
        sid = str(sci.get("id", ""))
        loyer_data = loyers_by_sci.get(sid, {"total": 0.0, "payes": 0.0})
        total = loyer_data["total"]
        payes = loyer_data["payes"]
        recouvrement = round((payes / total * 100) if total > 0 else 0.0, 1)

        cards.append({
            "id": sid,
            "nom": sci.get("nom") or sci.get("name", ""),
            "statut": sci.get("statut", "active"),
            "biens_count": biens_by_sci.get(sid, 0),
            "loyer_total": round(total, 2),
            "loyer_payes": round(payes, 2),
            "recouvrement": recouvrement,
        })

    return cards


async def get_recent_activity(client, user_id: str, limit: int = 10) -> list[dict]:
    """
    Return recent activity across all user SCIs:
    - Recent loyers (created/updated)
    - Recent biens added
    Sorted by created_at desc.
    """
    sci_ids = _get_user_sci_ids(client, user_id)
    if not sci_ids:
        return []

    activities: list[dict] = []

    # Recent loyers
    try:
        loyers = _query_in_sci_ids(client, "loyers", "id,id_sci,montant,statut,date_loyer,created_at", sci_ids)
        for l in loyers:
            activities.append({
                "type": "loyer",
                "id": l.get("id"),
                "id_sci": l.get("id_sci"),
                "description": f"Loyer de {float(l.get('montant') or 0):,.0f} € — {l.get('statut', 'en_attente')}".replace(",", " "),
                "date": l.get("date_loyer"),
                "created_at": l.get("created_at", ""),
            })
    except Exception:
        logger.warning("recent_activity_loyers_failed", user_id=user_id, exc_info=True)

    # Recent biens
    try:
        biens = _query_in_sci_ids(client, "biens", "id,id_sci,adresse,created_at", sci_ids)
        for b in biens:
            nom = b.get("adresse") or "Bien"
            activities.append({
                "type": "bien",
                "id": b.get("id"),
                "id_sci": b.get("id_sci"),
                "description": f"Bien ajouté : {nom}",
                "date": None,
                "created_at": b.get("created_at", ""),
            })
    except Exception:
        logger.warning("recent_activity_biens_failed", user_id=user_id, exc_info=True)

    # Sort by created_at desc, take limit
    activities.sort(key=lambda a: a.get("created_at") or "", reverse=True)
    return activities[:limit]
