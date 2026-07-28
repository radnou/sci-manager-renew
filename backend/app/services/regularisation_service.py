"""Annual charge regularisation service.

Compares provisions (charges_locatives * mois_occupation) against actual
recoverable charges recorded for a bien in a given year. Returns the balance:
positive = tenant overpaid, negative = tenant owes more.

Loi ALUR art. 23 — obligation de régularisation annuelle.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date

import structlog

logger = structlog.get_logger(__name__)

# Décret n° 87-713 : la liste des charges récupérables auprès du locataire est
# LIMITATIVE. Sur le référentiel `CHARGE_TYPES` de ce projet, seules les charges
# de copropriété comportent une quote-part récupérable ; tout le reste est à la
# charge exclusive du bailleur.
CHARGES_RECUPERABLES: frozenset[str] = frozenset({"copropriete"})


def _parse_date(value) -> date | None:
    """Convertit une valeur en date : accepte un objet date, une chaîne ISO ou None.

    Lève ValueError sur une chaîne malformée — une date illisible ne doit jamais
    être silencieusement traitée comme une absence de bail.
    """
    if value is None:
        return None
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value)[:10])


def _mois_occupation(date_debut, date_fin, annee: int) -> int:
    """Nombre de mois d'occupation du bien pendant l'année civile `annee`.

    Un mois entamé compte pour un mois entier (convention usuelle dans les
    régularisations locatives françaises et favorable à la lisibilité).

    Paramètres acceptés pour `date_debut` et `date_fin` : objets `date`,
    chaînes ISO (AAAA-MM-JJ), ou None.

    Retourne 0 si `date_debut` est None ou postérieur au 31/12 de l'année,
    ou si le bail s'est terminé avant le 01/01 de l'année.
    """
    year_start = date(annee, 1, 1)
    year_end = date(annee, 12, 31)

    debut = _parse_date(date_debut)
    fin = _parse_date(date_fin)

    if debut is None or debut > year_end:
        return 0

    # date_fin nulle ou postérieure au 31/12 → occupation jusqu'à la fin de l'année
    effective_fin = min(fin, year_end) if fin is not None else year_end

    if effective_fin < year_start:
        return 0

    effective_debut = max(debut, year_start)

    # Un mois entamé = un mois entier : on compte du mois de début au mois de fin inclus
    mois = (
        (effective_fin.year - effective_debut.year) * 12
        + effective_fin.month
        - effective_debut.month
        + 1
    )
    return min(max(mois, 0), 12)


def calculate_regularisation(client, bail_id: str, annee: int) -> dict:
    """Calculate the annual charge regularization for a bail.

    Args:
        client: Supabase client (service role recommended).
        bail_id: UUID of the bail.
        annee: Calendar year for which to compute.

    Returns:
        Dict avec provisions_annuelles, charges_reelles, solde, sens, saved,
        mois_occupation, charges_non_recuperables, detail_exclusions.

    Raises:
        ValueError: If bail not found.
    """
    # Fetch bail — date_debut et date_fin nécessaires pour le prorata d'occupation
    bail_result = (
        client.table("baux")
        .select("id, id_bien, charges_locatives, date_debut, date_fin")
        .eq("id", bail_id)
        .execute()
    )
    bail_rows = bail_result.data or []
    if not bail_rows:
        raise ValueError(f"Bail {bail_id} not found")

    bail = bail_rows[0]
    charges_locatives = float(bail.get("charges_locatives") or 0)

    # Prorata sur les mois d'occupation réels de l'année civile
    mois = _mois_occupation(bail.get("date_debut"), bail.get("date_fin"), annee)
    provisions = round(charges_locatives * mois, 2)

    id_bien = bail.get("id_bien")

    # Fetch actual charges for the bien in the given year (avec type_charge)
    year_start = f"{annee}-01-01"
    year_end = f"{annee}-12-31"

    charges_result = (
        client.table("charges")
        .select("montant, date_paiement, type_charge")
        .eq("id_bien", id_bien)
        .gte("date_paiement", year_start)
        .lte("date_paiement", year_end)
        .execute()
    )

    charges_data = charges_result.data or []

    # Sépare les charges récupérables des charges à la charge du seul bailleur
    recuperables_total = 0.0
    exclusions_by_type: dict[str, float] = defaultdict(float)

    for c in charges_data:
        montant = float(c.get("montant") or 0)
        # Un type_charge absent ou None est traité comme non récupérable : on ne
        # réclame jamais au locataire sur la foi d'un type indéterminé.
        type_charge = c.get("type_charge") or "non_renseigne"
        if type_charge in CHARGES_RECUPERABLES:
            recuperables_total += montant
        else:
            exclusions_by_type[type_charge] += montant

    charges_reelles = round(recuperables_total, 2)
    charges_non_recuperables = round(sum(exclusions_by_type.values()), 2)

    # Trié par montant décroissant, puis par type pour stabilité en cas d'égalité
    detail_exclusions = sorted(
        [
            {"type_charge": k, "montant": round(v, 2)}
            for k, v in exclusions_by_type.items()
        ],
        key=lambda e: (-e["montant"], e["type_charge"]),
    )

    solde = round(provisions - charges_reelles, 2)
    sens = "trop_percu" if solde > 0 else "complement_du" if solde < 0 else "equilibre"

    # Check if a confirmed regularisation already exists
    saved = _get_saved_regularisation(client, id_bien, bail_id, annee)

    result = {
        "bail_id": bail_id,
        "bien_id": id_bien,
        "annee": annee,
        "mois_occupation": mois,
        "provisions_annuelles": provisions,
        "charges_reelles": charges_reelles,
        "charges_non_recuperables": charges_non_recuperables,
        "detail_exclusions": detail_exclusions,
        "solde": solde,
        "sens": sens,
        "saved": saved,
    }

    logger.info(
        "regularisation_calculated",
        bail_id=bail_id,
        annee=annee,
        mois_occupation=mois,
        provisions=provisions,
        charges_reelles=charges_reelles,
        charges_non_recuperables=charges_non_recuperables,
        solde=solde,
    )

    return result


def _get_saved_regularisation(
    client, bien_id: str, bail_id: str, annee: int
) -> dict | None:
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

    # Seuls les champs présents en DB sont persistés : les champs de diagnostic
    # (charges_non_recuperables, detail_exclusions) sont calculés à la volée et
    # ne correspondent pas à des colonnes de regularisations_charges.
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
        result = client.table("regularisations_charges").insert(row).execute()

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
