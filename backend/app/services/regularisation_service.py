"""Annual charge regularisation service.

Compares provisions (charges_locatives from bail * 12) against actual
charges recorded for a bien in a given year. Returns the balance:
positive = tenant overpaid, negative = tenant owes more.

Loi ALUR art. 23 — obligation de régularisation annuelle.
"""
from __future__ import annotations

from datetime import date

import structlog

logger = structlog.get_logger(__name__)


def calculate_regularisation(client, bail_id: str, annee: int) -> dict:
    """Calculate the annual charge regularization for a bail.

    Args:
        client: Supabase client (service role recommended).
        bail_id: UUID of the bail.
        annee: Calendar year for which to compute.

    Returns:
        Dict with provisions_annuelles, charges_reelles, solde, sens, saved.

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
    sens = "trop_percu" if solde > 0 else "complement_du" if solde < 0 else "equilibre"

    # Check if a confirmed regularisation already exists
    saved = _get_saved_regularisation(client, id_bien, bail_id, annee)

    result = {
        "bail_id": bail_id,
        "bien_id": id_bien,
        "annee": annee,
        "provisions_annuelles": provisions,
        "charges_reelles": charges_reelles,
        "solde": solde,
        "sens": sens,
        "saved": saved,
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


def _get_saved_regularisation(client, bien_id: str, bail_id: str, annee: int) -> dict | None:
    """Check if a regularisation has already been saved for this bien/bail/year."""
    result = (
        client.table("regularisations_charges")
        .select("*")
        .eq("id_bien", bien_id)
        .eq("id_bail", bail_id)
        .eq("annee", annee)
        .execute()
    )
    rows = result.data or []
    return rows[0] if rows else None


def confirm_regularisation(
    client,
    bien_id: str,
    bail_id: str,
    annee: int,
    notes: str | None = None,
) -> dict:
    """Confirm and persist a regularisation calculation.

    Recalculates from source data to prevent stale values, then upserts
    into regularisations_charges table.

    Args:
        client: Supabase service client (for writes).
        bien_id: UUID of the bien.
        bail_id: UUID of the bail.
        annee: Calendar year.
        notes: Optional user notes.

    Returns:
        The saved regularisation row.
    """
    # Recalculate from source to ensure consistency
    calc = calculate_regularisation(client, bail_id, annee)

    row = {
        "id_bien": bien_id,
        "id_bail": bail_id,
        "annee": annee,
        "total_provisions": calc["provisions_annuelles"],
        "total_charges_reelles": calc["charges_reelles"],
        "solde": calc["solde"],
        "sens": calc["sens"],
        "statut": "confirme",
        "date_regularisation": date.today().isoformat(),
        "notes": notes,
        "updated_at": "now()",
    }

    # Check if exists — upsert
    existing = _get_saved_regularisation(client, bien_id, bail_id, annee)
    if existing:
        result = (
            client.table("regularisations_charges")
            .update(row)
            .eq("id", existing["id"])
            .execute()
        )
    else:
        result = (
            client.table("regularisations_charges")
            .insert(row)
            .execute()
        )

    if getattr(result, "error", None):
        raise ValueError(f"Failed to save regularisation: {result.error}")

    data = result.data or []
    if not data:
        raise ValueError("Failed to save regularisation — no data returned")

    saved = data[0]

    logger.info(
        "regularisation_confirmed",
        bail_id=bail_id,
        bien_id=bien_id,
        annee=annee,
        solde=calc["solde"],
        regularisation_id=saved.get("id"),
    )

    return saved
