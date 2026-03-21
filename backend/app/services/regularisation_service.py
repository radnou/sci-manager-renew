"""Annual charge regularisation service.

Compares provisions (charges_locatives from bail * 12) against actual
charges recorded for a bien in a given year. Returns the balance:
positive = tenant overpaid, negative = tenant owes more.
"""
from __future__ import annotations

import structlog

logger = structlog.get_logger(__name__)


def calculate_regularisation(client, bail_id: str, annee: int) -> dict:
    """Calculate the annual charge regularization for a bail.

    Args:
        client: Supabase client (service role recommended).
        bail_id: UUID of the bail.
        annee: Calendar year for which to compute.

    Returns:
        Dict with provisions_annuelles, charges_reelles, solde, sens.

    Raises:
        ValueError: If bail not found.
    """
    # Fetch bail
    bail_result = (
        client.table("baux")
        .select("id, id_bien, charges_locatives")
        .eq("id", bail_id)
        .execute()
    )
    bail_rows = bail_result.data or []
    if not bail_rows:
        raise ValueError(f"Bail {bail_id} not found")

    bail = bail_rows[0]
    charges_locatives = float(bail.get("charges_locatives") or 0)
    provisions = round(charges_locatives * 12, 2)

    id_bien = bail.get("id_bien")

    # Fetch actual charges for the bien in the given year
    year_start = f"{annee}-01-01"
    year_end = f"{annee}-12-31"

    charges_result = (
        client.table("charges")
        .select("montant, date_paiement")
        .eq("id_bien", id_bien)
        .gte("date_paiement", year_start)
        .lte("date_paiement", year_end)
        .execute()
    )

    charges_reelles = round(
        sum(float(c.get("montant") or 0) for c in (charges_result.data or [])),
        2,
    )

    solde = round(provisions - charges_reelles, 2)

    result = {
        "bail_id": bail_id,
        "annee": annee,
        "provisions_annuelles": provisions,
        "charges_reelles": charges_reelles,
        "solde": solde,
        "sens": "trop_percu" if solde > 0 else "complement_du" if solde < 0 else "equilibre",
    }

    logger.info(
        "regularisation_calculated",
        bail_id=bail_id,
        annee=annee,
        provisions=provisions,
        charges_reelles=charges_reelles,
        solde=solde,
    )

    return result
