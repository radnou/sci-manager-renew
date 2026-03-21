"""Service for annual accounting recap per SCI."""

from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)


class ComptabiliteService:
    """Calculates annual financial recap for a SCI, aggregating per-bien data."""

    @staticmethod
    def get_recap_annuel(client, sci_id: str, annee: int) -> dict:
        """Build annual accounting summary for a SCI.

        For each bien in the SCI:
          - revenus = SUM(loyers WHERE statut='paye' AND year=annee)
          - charges = SUM(charges WHERE year=annee)
          - evenements_deductibles = SUM(evenements WHERE deductible AND year=annee)
          - resultat = revenus - charges - evenements_deductibles

        Also calculates N-1 totals for year-over-year comparison.

        Returns:
            {
                annee, biens: [...], totaux: {...},
                variation_n1: {revenus_pct, charges_pct, resultat_pct}
            }
        """
        # Fetch all biens for SCI
        biens_result = (
            client.table("biens")
            .select("id, adresse, ville")
            .eq("id_sci", sci_id)
            .execute()
        )
        biens = biens_result.data or []
        if not biens:
            return _empty_recap(annee)

        bien_ids = [b["id"] for b in biens]
        bien_map = {b["id"]: b for b in biens}

        # Fetch loyers for year N
        date_start = f"{annee}-01-01"
        date_end = f"{annee}-12-31"

        loyers_n = _fetch_loyers(client, bien_ids, date_start, date_end)

        # Fetch charges for year N
        charges_n = _fetch_charges(client, bien_ids, date_start, date_end)

        # Fetch deductible evenements for year N
        evenements_n = _fetch_evenements_deductibles(client, bien_ids, date_start, date_end)

        # Build per-bien data for year N
        biens_recap = []
        totaux_revenus = 0.0
        totaux_charges = 0.0
        totaux_evenements = 0.0

        for bien_id in bien_ids:
            bien_info = bien_map[bien_id]
            revenus = sum(
                l.get("montant", 0) or 0
                for l in loyers_n
                if l.get("id_bien") == bien_id and l.get("statut") in ("paye", "paid")
            )
            charges = sum(
                c.get("montant", 0) or 0
                for c in charges_n
                if c.get("id_bien") == bien_id
            )
            evt_deductibles = sum(
                float(e.get("montant", 0) or 0)
                for e in evenements_n
                if e.get("id_bien") == bien_id
            )
            resultat = revenus - charges - evt_deductibles

            biens_recap.append({
                "bien_id": bien_id,
                "adresse": bien_info.get("adresse", ""),
                "ville": bien_info.get("ville", ""),
                "revenus": round(revenus, 2),
                "charges": round(charges, 2),
                "evenements_deductibles": round(evt_deductibles, 2),
                "resultat": round(resultat, 2),
            })

            totaux_revenus += revenus
            totaux_charges += charges
            totaux_evenements += evt_deductibles

        totaux_resultat = totaux_revenus - totaux_charges - totaux_evenements

        # Year N-1 totals for comparison
        annee_n1 = annee - 1
        date_start_n1 = f"{annee_n1}-01-01"
        date_end_n1 = f"{annee_n1}-12-31"

        loyers_n1 = _fetch_loyers(client, bien_ids, date_start_n1, date_end_n1)
        charges_n1 = _fetch_charges(client, bien_ids, date_start_n1, date_end_n1)
        evenements_n1 = _fetch_evenements_deductibles(client, bien_ids, date_start_n1, date_end_n1)

        revenus_n1 = sum(
            l.get("montant", 0) or 0
            for l in loyers_n1
            if l.get("statut") in ("paye", "paid")
        )
        charges_n1_total = sum(c.get("montant", 0) or 0 for c in charges_n1)
        evt_n1_total = sum(float(e.get("montant", 0) or 0) for e in evenements_n1)
        resultat_n1 = revenus_n1 - charges_n1_total - evt_n1_total

        variation_n1 = {
            "revenus_pct": _pct_change(revenus_n1, totaux_revenus),
            "charges_pct": _pct_change(charges_n1_total, totaux_charges),
            "resultat_pct": _pct_change(resultat_n1, totaux_resultat),
        }

        return {
            "annee": annee,
            "biens": biens_recap,
            "totaux": {
                "revenus": round(totaux_revenus, 2),
                "charges": round(totaux_charges, 2),
                "evenements_deductibles": round(totaux_evenements, 2),
                "resultat": round(totaux_resultat, 2),
            },
            "variation_n1": variation_n1,
        }


def _fetch_loyers(client, bien_ids: list[str], date_start: str, date_end: str) -> list[dict]:
    result = (
        client.table("loyers")
        .select("id_bien, montant, statut")
        .in_("id_bien", bien_ids)
        .gte("date_loyer", date_start)
        .lte("date_loyer", date_end)
        .execute()
    )
    return result.data or []


def _fetch_charges(client, bien_ids: list[str], date_start: str, date_end: str) -> list[dict]:
    result = (
        client.table("charges")
        .select("id_bien, montant")
        .in_("id_bien", bien_ids)
        .gte("date_paiement", date_start)
        .lte("date_paiement", date_end)
        .execute()
    )
    return result.data or []


def _fetch_evenements_deductibles(client, bien_ids: list[str], date_start: str, date_end: str) -> list[dict]:
    result = (
        client.table("evenements_bien")
        .select("id_bien, montant")
        .in_("id_bien", bien_ids)
        .eq("deductible_fiscalement", True)
        .gte("date_evenement", date_start)
        .lte("date_evenement", date_end)
        .execute()
    )
    return result.data or []


def _pct_change(old: float, new: float) -> float | None:
    """Calculate percentage change from old to new. Returns None if old is 0."""
    if old == 0:
        return None
    return round((new - old) / abs(old) * 100, 1)


def _empty_recap(annee: int) -> dict:
    return {
        "annee": annee,
        "biens": [],
        "totaux": {
            "revenus": 0,
            "charges": 0,
            "evenements_deductibles": 0,
            "resultat": 0,
        },
        "variation_n1": {
            "revenus_pct": None,
            "charges_pct": None,
            "resultat_pct": None,
        },
    }
