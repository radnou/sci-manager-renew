"""SCI & Bien lifecycle endpoints: dissolution, gérant change, capital modification, bien cession."""

from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Request, status
from pydantic import BaseModel, Field

from app.core.exceptions import BusinessLogicError, DatabaseError, ResourceNotFoundError, ValidationError
from app.core.paywall import AssocieMembership, require_gerant_role, require_sci_membership
from app.core.rate_limit import limiter
from app.core.supabase_client import get_supabase_user_client, get_supabase_service_client
from app.services.notification_service import create_notification_with_email

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/scis", tags=["sci-lifecycle"])


def _get_client(request: Request):
    return get_supabase_user_client(request)


def _get_write_client():
    return get_supabase_service_client()


def _execute_select(query):
    result = query.execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))
    return result.data or []


async def _notify_all_associes(client, sci_id: str, notification_type: str, title: str, message: str):
    """Send notification to all associes of a SCI."""
    associes = _execute_select(
        client.table("associes").select("user_id").eq("id_sci", sci_id)
    )
    for associe in associes:
        user_id = associe.get("user_id")
        if user_id:
            try:
                await create_notification_with_email(
                    client, user_id, notification_type,
                    {"title": title, "message": message, "metadata": {"sci_id": sci_id}},
                )
            except Exception:
                logger.warning("notification_failed", user_id=user_id, type=notification_type)


# ──────────────────────────────────────────────────────────────
# TASK 1: Dissolution SCI
# ──────────────────────────────────────────────────────────────


class DissolutionPayload(BaseModel):
    date_dissolution: date
    motif: str = Field(min_length=1, max_length=500)
    liquidateur: str = Field(min_length=1, max_length=100)


class DissolutionResponse(BaseModel):
    id: str
    nom: str
    statut: str
    date_dissolution: date
    motif_dissolution: str
    liquidateur: str


@router.post("/{sci_id}/dissoudre", response_model=DissolutionResponse, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def dissoudre_sci(
    sci_id: UUID,
    payload: DissolutionPayload,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Dissolve a SCI. Requires all baux to be terminated."""
    logger.info("dissolving_sci", sci_id=str(sci_id), motif=payload.motif)

    client = _get_client(request)
    write_client = _get_write_client()

    # Verify SCI exists
    sci_rows = _execute_select(client.table("sci").select("*").eq("id", str(sci_id)))
    if not sci_rows:
        raise ResourceNotFoundError("SCI", str(sci_id))

    sci = sci_rows[0]

    # Check SCI is not already dissolved
    if sci.get("statut") == "dissoute":
        raise BusinessLogicError("Cette SCI est déjà dissoute.")

    # Verify all baux are terminated (no active bail)
    biens_rows = _execute_select(client.table("biens").select("id").eq("id_sci", str(sci_id)))
    bien_ids = [str(b["id"]) for b in biens_rows if b.get("id")]

    if bien_ids:
        for bid in bien_ids:
            active_baux = _execute_select(
                client.table("baux").select("id").eq("id_bien", bid).eq("statut", "en_cours")
            )
            if active_baux:
                raise BusinessLogicError(
                    "Impossible de dissoudre la SCI : des baux sont encore en cours. "
                    "Veuillez résilier tous les baux avant la dissolution."
                )

    # Update SCI with dissolution fields
    update_data = {
        "statut": "dissoute",
        "date_dissolution": payload.date_dissolution.isoformat(),
        "motif_dissolution": payload.motif,
        "liquidateur": payload.liquidateur,
    }
    result = write_client.table("sci").update(update_data).eq("id", str(sci_id)).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    updated_rows = result.data or []
    if not updated_rows:
        raise DatabaseError("Unable to update SCI for dissolution")

    updated = updated_rows[0]

    # Notify all associes
    await _notify_all_associes(
        write_client, str(sci_id), "dissolution",
        f"Dissolution de {sci.get('nom', 'la SCI')}",
        f"La SCI {sci.get('nom', '')} a été dissoute le {payload.date_dissolution.isoformat()}. "
        f"Motif : {payload.motif}. Liquidateur désigné : {payload.liquidateur}.",
    )

    logger.info("sci_dissolved", sci_id=str(sci_id))
    return DissolutionResponse(
        id=str(updated.get("id", sci_id)),
        nom=str(updated.get("nom", "")),
        statut="dissoute",
        date_dissolution=payload.date_dissolution,
        motif_dissolution=payload.motif,
        liquidateur=payload.liquidateur,
    )


# ──────────────────────────────────────────────────────────────
# TASK 2: Changement de gérant
# ──────────────────────────────────────────────────────────────


class ChangerGerantPayload(BaseModel):
    nouveau_gerant_associe_id: str
    date_effet: date
    ag_id: Optional[str] = None


class ChangerGerantResponse(BaseModel):
    sci_id: str
    ancien_gerant: str
    nouveau_gerant: str
    date_effet: date
    ag_id: Optional[str] = None


@router.post("/{sci_id}/changer-gerant", response_model=ChangerGerantResponse, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def changer_gerant(
    sci_id: UUID,
    payload: ChangerGerantPayload,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Change the gérant of a SCI. Current gérant becomes associé."""
    logger.info("changing_gerant", sci_id=str(sci_id), new_gerant_id=payload.nouveau_gerant_associe_id)

    client = _get_client(request)
    write_client = _get_write_client()

    # Verify the new gérant is an associé of this SCI
    new_gerant_rows = _execute_select(
        client.table("associes").select("*")
        .eq("id", payload.nouveau_gerant_associe_id)
        .eq("id_sci", str(sci_id))
    )
    if not new_gerant_rows:
        raise ResourceNotFoundError("Associé", payload.nouveau_gerant_associe_id)

    new_gerant = new_gerant_rows[0]
    new_gerant_nom = str(new_gerant.get("nom", ""))

    if new_gerant.get("role") == "gerant":
        raise BusinessLogicError("Cet associé est déjà gérant de la SCI.")

    # Get old gérant info
    old_gerant_rows = _execute_select(
        client.table("associes").select("*")
        .eq("id_sci", str(sci_id))
        .eq("role", "gerant")
    )
    old_gerant_nom = str(old_gerant_rows[0].get("nom", "")) if old_gerant_rows else "Ancien gérant"

    # Update old gérant → associe
    for old_gerant in old_gerant_rows:
        write_client.table("associes").update({"role": "associe"}).eq("id", str(old_gerant["id"])).execute()

    # Update new gérant → gerant
    write_client.table("associes").update({"role": "gerant"}).eq("id", payload.nouveau_gerant_associe_id).execute()

    # Update sci.nom_gerant
    write_client.table("sci").update({"nom_gerant": new_gerant_nom}).eq("id", str(sci_id)).execute()

    # Notify all associes
    sci_rows = _execute_select(client.table("sci").select("nom").eq("id", str(sci_id)))
    sci_nom = sci_rows[0].get("nom", "la SCI") if sci_rows else "la SCI"

    await _notify_all_associes(
        write_client, str(sci_id), "changement_gerant",
        f"Changement de gérant — {sci_nom}",
        f"{new_gerant_nom} est désigné(e) nouveau gérant de {sci_nom} "
        f"à compter du {payload.date_effet.isoformat()}, en remplacement de {old_gerant_nom}.",
    )

    logger.info("gerant_changed", sci_id=str(sci_id), new_gerant=new_gerant_nom)
    return ChangerGerantResponse(
        sci_id=str(sci_id),
        ancien_gerant=old_gerant_nom,
        nouveau_gerant=new_gerant_nom,
        date_effet=payload.date_effet,
        ag_id=payload.ag_id,
    )


# ──────────────────────────────────────────────────────────────
# TASK 3: Modification du capital social
# ──────────────────────────────────────────────────────────────


class ModifierCapitalPayload(BaseModel):
    nouveau_capital: float = Field(gt=0)
    nouveau_nb_parts: int = Field(gt=0)
    nouvelle_valeur_nominale: float = Field(gt=0)
    type: str = Field(pattern=r"^(augmentation|reduction)$")
    ag_id: Optional[str] = None


class ModifierCapitalResponse(BaseModel):
    sci_id: str
    ancien_capital: Optional[float] = None
    nouveau_capital: float
    nouveau_nb_parts: int
    nouvelle_valeur_nominale: float
    type: str
    mouvement_parts_id: Optional[str] = None


@router.post("/{sci_id}/modifier-capital", response_model=ModifierCapitalResponse, status_code=status.HTTP_200_OK)
@limiter.limit("30/minute")
async def modifier_capital(
    sci_id: UUID,
    payload: ModifierCapitalPayload,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Modify capital social of a SCI (augmentation or reduction)."""
    logger.info("modifying_capital", sci_id=str(sci_id), type=payload.type, nouveau_capital=payload.nouveau_capital)

    client = _get_client(request)
    write_client = _get_write_client()

    # Get current SCI
    sci_rows = _execute_select(client.table("sci").select("*").eq("id", str(sci_id)))
    if not sci_rows:
        raise ResourceNotFoundError("SCI", str(sci_id))

    sci = sci_rows[0]
    ancien_capital = sci.get("capital_social")

    # Validate: reduction cannot go below 0
    if payload.type == "reduction" and ancien_capital is not None and payload.nouveau_capital >= ancien_capital:
        raise BusinessLogicError(
            "Pour une réduction de capital, le nouveau montant doit être inférieur au capital actuel."
        )

    if payload.type == "augmentation" and ancien_capital is not None and payload.nouveau_capital <= ancien_capital:
        raise BusinessLogicError(
            "Pour une augmentation de capital, le nouveau montant doit être supérieur au capital actuel."
        )

    # Update SCI capital fields
    update_data = {
        "capital_social": payload.nouveau_capital,
        "nb_parts_total": payload.nouveau_nb_parts,
        "valeur_nominale_part": payload.nouvelle_valeur_nominale,
    }
    result = write_client.table("sci").update(update_data).eq("id", str(sci_id)).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    # Create mouvement_parts record
    mouvement_id = None
    mouvement_data = {
        "id_sci": str(sci_id),
        "date_mouvement": date.today().isoformat(),
        "type_mouvement": payload.type,
        "cedant_nom": sci.get("nom", "SCI"),
        "cessionnaire_nom": sci.get("nom", "SCI"),
        "nb_parts": abs(payload.nouveau_nb_parts - (sci.get("nb_parts_total") or 0)),
        "prix_unitaire": payload.nouvelle_valeur_nominale,
        "prix_total": payload.nouveau_capital - (ancien_capital or 0),
        "notes": f"{payload.type.capitalize()} de capital : {ancien_capital or 0} → {payload.nouveau_capital}",
    }
    mp_result = write_client.table("mouvements_parts").insert(mouvement_data).execute()
    if mp_result.data:
        mouvement_id = str(mp_result.data[0].get("id", ""))

    # Notify all associes
    sci_nom = sci.get("nom", "la SCI")
    label = "Augmentation" if payload.type == "augmentation" else "Réduction"
    await _notify_all_associes(
        write_client, str(sci_id), "modification_capital",
        f"{label} de capital — {sci_nom}",
        f"{label} du capital social de {sci_nom} : {ancien_capital or 0} € → {payload.nouveau_capital} €. "
        f"Nombre de parts : {payload.nouveau_nb_parts}, valeur nominale : {payload.nouvelle_valeur_nominale} €.",
    )

    logger.info("capital_modified", sci_id=str(sci_id), type=payload.type)
    return ModifierCapitalResponse(
        sci_id=str(sci_id),
        ancien_capital=ancien_capital,
        nouveau_capital=payload.nouveau_capital,
        nouveau_nb_parts=payload.nouveau_nb_parts,
        nouvelle_valeur_nominale=payload.nouvelle_valeur_nominale,
        type=payload.type,
        mouvement_parts_id=mouvement_id,
    )


# ──────────────────────────────────────────────────────────────
# TASK 5: Cession / vente bien
# ──────────────────────────────────────────────────────────────


class CessionBienPayload(BaseModel):
    prix_cession: float = Field(gt=0)
    date_cession: date
    acquereur: str = Field(min_length=1, max_length=200)
    frais_cession: float = Field(default=0, ge=0)


class CessionBienResponse(BaseModel):
    bien_id: str
    sci_id: str
    prix_cession: float
    date_cession: date
    acquereur: str
    frais_cession: float
    plus_value_brute: Optional[float] = None
    statut: str


@router.post(
    "/{sci_id}/biens/{bien_id}/ceder",
    response_model=CessionBienResponse,
    status_code=status.HTTP_200_OK,
)
@limiter.limit("30/minute")
async def ceder_bien(
    sci_id: UUID,
    bien_id: str,
    payload: CessionBienPayload,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Sell/transfer a property. Requires all baux to be terminated."""
    logger.info("ceding_bien", bien_id=bien_id, sci_id=str(sci_id), prix=payload.prix_cession)

    client = _get_client(request)
    write_client = _get_write_client()

    # Verify bien exists and belongs to SCI
    bien_rows = _execute_select(
        client.table("biens").select("*").eq("id", bien_id).eq("id_sci", str(sci_id))
    )
    if not bien_rows:
        raise ResourceNotFoundError("Bien", bien_id)

    bien = bien_rows[0]

    # Check bien is not already sold
    if bien.get("statut") == "cede":
        raise BusinessLogicError("Ce bien a déjà été cédé.")

    # Verify all baux are terminated
    active_baux = _execute_select(
        client.table("baux").select("id").eq("id_bien", bien_id).eq("statut", "en_cours")
    )
    if active_baux:
        raise BusinessLogicError(
            "Impossible de céder le bien : des baux sont encore en cours. "
            "Veuillez résilier tous les baux avant la cession."
        )

    # Calculate plus-value brute
    prix_acquisition = bien.get("prix_acquisition")
    plus_value_brute = None
    if prix_acquisition is not None:
        plus_value_brute = round(payload.prix_cession - float(prix_acquisition), 2)

    # Update bien with cession fields and mark as cédé
    update_data = {
        "statut": "cede",
        "prix_cession": payload.prix_cession,
        "date_cession": payload.date_cession.isoformat(),
        "acquereur": payload.acquereur,
        "frais_cession": payload.frais_cession,
    }
    result = write_client.table("biens").update(update_data).eq("id", bien_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    # Create événement "Cession"
    total_cession = payload.prix_cession - payload.frais_cession
    desc_parts = [f"Cession à {payload.acquereur} pour {payload.prix_cession} €."]
    if plus_value_brute is not None:
        desc_parts.append(f"Plus-value brute estimée : {plus_value_brute} €.")
    if payload.frais_cession > 0:
        desc_parts.append(f"Frais de cession : {payload.frais_cession} €.")

    evenement_data = {
        "id_bien": bien_id,
        "type": "cession",
        "titre": f"Cession — {payload.acquereur}",
        "description": " ".join(desc_parts),
        "date_evenement": payload.date_cession.isoformat(),
        "montant": payload.prix_cession,
        "deductible_fiscalement": False,
    }
    try:
        write_client.table("evenements_bien").insert(evenement_data).execute()
    except Exception:
        logger.warning("evenements_bien_insert_skip", reason="table not found")

    # Notify all associes
    sci_rows = _execute_select(client.table("sci").select("nom").eq("id", str(sci_id)))
    sci_nom = sci_rows[0].get("nom", "la SCI") if sci_rows else "la SCI"
    bien_adresse = bien.get("adresse", "le bien")

    pv_msg = f" Plus-value brute estimée : {plus_value_brute} €." if plus_value_brute is not None else ""
    await _notify_all_associes(
        write_client, str(sci_id), "cession_bien",
        f"Cession de bien — {sci_nom}",
        f"Le bien {bien_adresse} a été cédé à {payload.acquereur} "
        f"pour {payload.prix_cession} € le {payload.date_cession.isoformat()}.{pv_msg}",
    )

    logger.info("bien_ceded", bien_id=bien_id, sci_id=str(sci_id), plus_value=plus_value_brute)
    return CessionBienResponse(
        bien_id=bien_id,
        sci_id=str(sci_id),
        prix_cession=payload.prix_cession,
        date_cession=payload.date_cession,
        acquereur=payload.acquereur,
        frais_cession=payload.frais_cession,
        plus_value_brute=plus_value_brute,
        statut="cede",
    )
