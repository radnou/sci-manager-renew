"""Service for aggregated cross-SCI financial data."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

import structlog

logger = structlog.get_logger(__name__)


async def get_finances_overview(supabase_client, user_id: str, period_months: int = 12) -> dict:
    """
    Aggregate financial data across all SCIs the user belongs to.

    1. Get all SCIs for user via associes
    2. Get all biens for those SCIs
    3. Calculate: revenus (sum loyers payés), charges, cashflow
    4. Calculate taux_recouvrement (payés/total)
    5. Calculate patrimoine (sum prix_acquisition)
    6. Calculate evolution_mensuelle (group loyers by month)
    7. Calculate repartition_sci (group by SCI)
    """
    # 1. Get all SCIs for user
    associes_result = (
        supabase_client.table("associes")
        .select("id_sci")
        .eq("user_id", user_id)
        .execute()
    )
    sci_ids = [row["id_sci"] for row in (associes_result.data or [])]

    if not sci_ids:
        return _empty_response()

    # Get SCI details for names
    scis_result = (
        supabase_client.table("sci")
        .select("id, nom")
        .in_("id", sci_ids)
        .execute()
    )
    sci_map = {str(s["id"]): s["nom"] for s in (scis_result.data or [])}

    # 2. Get all biens for those SCIs
    biens_result = (
        supabase_client.table("biens")
        .select("id, id_sci, prix_acquisition, loyer_cc, charges")
        .in_("id_sci", sci_ids)
        .execute()
    )
    biens = biens_result.data or []
    bien_ids = [str(b["id"]) for b in biens]
    bien_sci_map = {str(b["id"]): str(b["id_sci"]) for b in biens}

    # Calculate patrimoine
    patrimoine_total = sum((b.get("prix_acquisition") or 0) for b in biens)

    if not bien_ids:
        return {
            **_empty_response(),
            "patrimoine_total": patrimoine_total,
            "repartition_sci": [
                {"sci_nom": sci_map.get(sid, "?"), "revenus": 0, "charges": 0}
                for sid in sci_ids
            ],
        }

    # 3. Get loyers within period
    cutoff_date = (datetime.utcnow() - timedelta(days=period_months * 30)).strftime("%Y-%m-%d")

    loyers_result = (
        supabase_client.table("loyers")
        .select("id, id_bien, montant, statut, date_loyer")
        .in_("id_bien", bien_ids)
        .gte("date_loyer", cutoff_date)
        .execute()
    )
    loyers = loyers_result.data or []

    # 4. Get charges within period
    charges_result = (
        supabase_client.table("charges")
        .select("id, id_bien, montant, date_paiement")
        .in_("id_bien", bien_ids)
        .gte("date_paiement", cutoff_date)
        .execute()
    )
    charges = charges_result.data or []

    # Calculate revenus (loyers payés)
    revenus_total = sum(
        (l.get("montant") or 0)
        for l in loyers
        if l.get("statut") in ("paye", "paid")
    )

    # Calculate total loyers (all statuses) for taux_recouvrement
    total_loyers = sum((l.get("montant") or 0) for l in loyers)

    # Calculate charges total
    charges_total = sum((c.get("montant") or 0) for c in charges)

    # Cashflow
    cashflow_net = revenus_total - charges_total

    # Taux de recouvrement
    taux_recouvrement = (revenus_total / total_loyers * 100) if total_loyers > 0 else 0

    # Rentabilité moyenne
    if patrimoine_total > 0:
        rentabilite_moyenne = (revenus_total / patrimoine_total * 100) * (12 / max(period_months, 1))
    else:
        rentabilite_moyenne = 0

    # 6. Evolution mensuelle
    monthly_revenus: dict[str, float] = defaultdict(float)
    monthly_charges: dict[str, float] = defaultdict(float)

    for l in loyers:
        if l.get("statut") in ("paye", "paid"):
            mois = (l.get("date_loyer") or "")[:7]  # "YYYY-MM"
            if mois:
                monthly_revenus[mois] += l.get("montant") or 0

    for c in charges:
        mois = (c.get("date_paiement") or "")[:7]
        if mois:
            monthly_charges[mois] += c.get("montant") or 0

    all_months = sorted(set(list(monthly_revenus.keys()) + list(monthly_charges.keys())))
    evolution_mensuelle = [
        {
            "mois": m,
            "revenus": round(monthly_revenus.get(m, 0), 2),
            "charges": round(monthly_charges.get(m, 0), 2),
        }
        for m in all_months
    ]

    # 7. Répartition par SCI
    sci_revenus: dict[str, float] = defaultdict(float)
    sci_charges: dict[str, float] = defaultdict(float)

    for l in loyers:
        if l.get("statut") in ("paye", "paid"):
            sci_id = bien_sci_map.get(str(l.get("id_bien", "")), "")
            sci_revenus[sci_id] += l.get("montant") or 0

    for c in charges:
        sci_id = bien_sci_map.get(str(c.get("id_bien", "")), "")
        sci_charges[sci_id] += c.get("montant") or 0

    repartition_sci = [
        {
            "sci_nom": sci_map.get(str(sid), "?"),
            "revenus": round(sci_revenus.get(str(sid), 0), 2),
            "charges": round(sci_charges.get(str(sid), 0), 2),
        }
        for sid in sci_ids
    ]

    return {
        "revenus_total": round(revenus_total, 2),
        "charges_total": round(charges_total, 2),
        "cashflow_net": round(cashflow_net, 2),
        "taux_recouvrement": round(taux_recouvrement, 1),
        "patrimoine_total": round(patrimoine_total, 2),
        "rentabilite_moyenne": round(rentabilite_moyenne, 1),
        "evolution_mensuelle": evolution_mensuelle,
        "repartition_sci": repartition_sci,
    }


def _empty_response() -> dict:
    return {
        "revenus_total": 0,
        "charges_total": 0,
        "cashflow_net": 0,
        "taux_recouvrement": 0,
        "patrimoine_total": 0,
        "rentabilite_moyenne": 0,
        "evolution_mensuelle": [],
        "repartition_sci": [],
    }
