from __future__ import annotations

from datetime import date, timedelta
from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, Response, UploadFile, status
from pydantic import BaseModel

from app.core.supabase_client import get_supabase_user_client, get_supabase_service_client
from app.core.exceptions import DatabaseError, ResourceNotFoundError, ValidationError
from app.core.paywall import AssocieMembership, require_gerant_role, require_sci_membership
from app.core.rate_limit import limiter
from app.services.subscription_service import SubscriptionService
from app.models.biens import BienCreate, BienResponse, BienUpdate
from app.models.charges import ChargeCreate, ChargeResponse, ChargeUpdate
from app.models.evenements import EvenementCreate, EvenementResponse, EvenementUpdate
from app.models.loyers import LoyerCreate, LoyerResponse
from app.schemas.assurance_pno import AssurancePnoCreate, AssurancePnoResponse, AssurancePnoUpdate
from app.schemas.baux import BailCreate, BailResponse, BailUpdate
from app.schemas.documents import DocumentBienResponse
from app.schemas.fiche_bien import FicheBienResponse, RentabiliteCalculee
from app.schemas.frais_agence import FraisAgenceCreate, FraisAgenceResponse
from app.services.document_links import create_document_signed_url, extract_document_storage_path
from app.services.rentabilite_service import calculate_rentabilite
from app.services.notification_service import create_notification_with_email

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["scis-biens"])


def _get_client(request: Request):
    return get_supabase_user_client(request)


def _verify_bien_belongs_to_sci(client, bien_id: str, sci_id: str) -> dict:
    result = client.table("biens").select("*").eq("id", bien_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))
    rows = result.data or []
    if not rows:
        raise ResourceNotFoundError("Bien", bien_id)
    bien = rows[0]
    if str(bien.get("id_sci", "")) != sci_id:
        raise ResourceNotFoundError("Bien", bien_id)
    return bien


@router.get("/{bien_id}/evenements", response_model=list[EvenementResponse])
async def list_bien_evenements(
    sci_id: UUID,
    bien_id: str,
    request: Request,
    annee: int | None = Query(default=None, description="Filtrer par année"),
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Liste les événements d'un bien, avec filtre optionnel par année."""
    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    try:
        query = (
            client.table("evenements_bien")
            .select("*")
            .eq("id_bien", bien_id)
        )

        if annee is not None:
            query = query.gte("date_evenement", f"{annee}-01-01").lte("date_evenement", f"{annee}-12-31")

        result = query.order("date_evenement", desc=True).execute()
    except Exception:
        return []

    return result.data or []


# ──────────────────────────────────────────────────────────────
# CREATE evenement for a bien
# ──────────────────────────────────────────────────────────────

@router.post("/{bien_id}/evenements", response_model=EvenementResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_bien_evenement(
    sci_id: UUID,
    bien_id: str,
    payload: EvenementCreate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Crée un événement pour un bien (gérant uniquement)."""
    logger.info("creating_evenement", bien_id=bien_id, sci_id=str(sci_id), type=payload.type)

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    row = payload.model_dump(mode="json")
    row["id_bien"] = bien_id

    write_client = _get_client(request)
    result = write_client.table("evenements_bien").insert(row).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise DatabaseError("Unable to create evenement")

    created = data[0]
    logger.info("evenement_created", event_id=created.get("id"), bien_id=bien_id)
    return created


# ──────────────────────────────────────────────────────────────
# UPDATE evenement
# ──────────────────────────────────────────────────────────────

@router.patch("/{bien_id}/evenements/{event_id}", response_model=EvenementResponse)
@limiter.limit("30/minute")
async def update_bien_evenement(
    sci_id: UUID,
    bien_id: str,
    event_id: str,
    payload: EvenementUpdate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Met à jour un événement (gérant uniquement)."""
    update_payload = payload.model_dump(exclude_unset=True, mode="json")
    logger.info("updating_evenement", event_id=event_id, bien_id=bien_id, fields=list(update_payload.keys()))

    if not update_payload:
        raise DatabaseError("No update fields provided")

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = (
        client.table("evenements_bien")
        .update(update_payload)
        .eq("id", event_id)
        .eq("id_bien", bien_id)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise ResourceNotFoundError("Evenement", event_id)

    logger.info("evenement_updated", event_id=event_id)
    return data[0]


# ──────────────────────────────────────────────────────────────
# DELETE evenement
# ──────────────────────────────────────────────────────────────

@router.delete("/{bien_id}/evenements/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def delete_bien_evenement(
    sci_id: UUID,
    bien_id: str,
    event_id: str,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Supprime un événement (gérant uniquement)."""
    logger.info("deleting_evenement", event_id=event_id, bien_id=bien_id)

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = client.table("evenements_bien").delete().eq("id", event_id).eq("id_bien", bien_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    logger.info("evenement_deleted", event_id=event_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────
# GET obligations for a bien
# ──────────────────────────────────────────────────────────────

@router.get("/{bien_id}/obligations")
async def get_bien_obligations(
    sci_id: UUID,
    bien_id: str,
    request: Request,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Retourne le statut des obligations réglementaires d'un bien."""
    from app.services.obligations_service import get_obligations

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    return get_obligations(client, bien_id)


# ──────────────────────────────────────────────────────────────
# AVENANT BAIL — POST /scis/{sci_id}/biens/{bien_id}/baux/{bail_id}/avenant
# ──────────────────────────────────────────────────────────────

AVENANT_TYPES = {"revision_loyer", "modification_charges", "ajout_locataire", "changement_destination"}


class AvenantCreate(BaseModel):
    type_avenant: str
    nouveau_loyer_hc: Optional[float] = None
    nouvelles_charges: Optional[float] = None
    date_effet: date
    motif: str


class AvenantResponse(BaseModel):
    avenant: dict
    bail_updated: dict


@router.post("/{bien_id}/baux/{bail_id}/avenant", response_model=AvenantResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_avenant(
    sci_id: UUID,
    bien_id: str,
    bail_id: str,
    payload: AvenantCreate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Create an avenant (amendment) to an existing bail."""
    if payload.type_avenant not in AVENANT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"type_avenant invalide. Valeurs acceptées : {', '.join(sorted(AVENANT_TYPES))}",
        )

    logger.info(
        "creating_avenant",
        bail_id=bail_id,
        bien_id=bien_id,
        sci_id=str(sci_id),
        type_avenant=payload.type_avenant,
    )

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    # Verify the bail exists
    bail_result = client.table("baux").select("*").eq("id", bail_id).eq("id_bien", bien_id).execute()
    if getattr(bail_result, "error", None) or not bail_result.data:
        raise ResourceNotFoundError("Bail", bail_id)

    bail = bail_result.data[0]

    # Build update payload for the bail based on avenant type
    bail_update: dict = {}
    if payload.type_avenant == "revision_loyer" and payload.nouveau_loyer_hc is not None:
        bail_update["loyer_hc"] = payload.nouveau_loyer_hc
    elif payload.type_avenant == "modification_charges" and payload.nouvelles_charges is not None:
        bail_update["charges_locatives"] = payload.nouvelles_charges

    write_client = _get_client(request)

    # Update the bail if there are changes (must use write_client — RLS read-only on baux)
    if bail_update:
        update_result = (
            write_client.table("baux")
            .update(bail_update)
            .eq("id", bail_id)
            .execute()
        )
        if getattr(update_result, "error", None):
            raise DatabaseError(str(update_result.error))
        bail.update(bail_update)

    # Store avenant as an evenement_bien
    avenant_metadata = payload.model_dump(mode="json")
    avenant_metadata["ancien_loyer_hc"] = bail_result.data[0].get("loyer_hc")
    avenant_metadata["anciennes_charges"] = bail_result.data[0].get("charges_locatives")

    evenement_row = {
        "id_bien": bien_id,
        "type": "avenant",
        "titre": f"Avenant : {payload.type_avenant.replace('_', ' ')}",
        "description": payload.motif,
        "date_evenement": payload.date_effet.isoformat(),
        "montant": payload.nouveau_loyer_hc,
        "deductible_fiscalement": False,
    }

    try:
        evt_result = write_client.table("evenements_bien").insert(evenement_row).execute()
        created_event = (evt_result.data or [{}])[0]
    except Exception as exc:
        logger.warning("evenements_bien_insert_skip", reason=str(exc))
        created_event = {"id": None, "type": "avenant", "titre": evenement_row["titre"]}

    # Create notification for SCI owners

    owners = (
        client.table("associes")
        .select("user_id")
        .eq("id_sci", str(sci_id))
        .not_.is_("user_id", "null")
        .execute()
    )
    for owner in (owners.data or []):
        try:
            await create_notification_with_email(
                write_client,
                user_id=owner["user_id"],
                notification_type="avenant_bail",
                data={
                    "title": f"Avenant bail — {payload.type_avenant.replace('_', ' ')}",
                    "message": f"{payload.motif} (effet au {payload.date_effet.isoformat()})",
                    "metadata": {
                        "bail_id": bail_id,
                        "bien_id": bien_id,
                        "type_avenant": payload.type_avenant,
                        "dedup_key": f"avenant_{bail_id}_{payload.date_effet.isoformat()}",
                    },
                },
            )
        except Exception as notif_exc:
            logger.warning("avenant_notification_skip", reason=str(notif_exc), user_id=owner["user_id"])

    logger.info("avenant_created", bail_id=bail_id, event_id=created_event.get("id"))
    return AvenantResponse(avenant=created_event, bail_updated=bail)


# ──────────────────────────────────────────────────────────────
# SINISTRE PNO — POST /scis/{sci_id}/biens/{bien_id}/sinistre
# ──────────────────────────────────────────────────────────────


class SinistreCreate(BaseModel):
    date_sinistre: date
    description: str
    montant_estime: Optional[float] = None
    numero_dossier: Optional[str] = None


class SinistreResponse(BaseModel):
    evenement: dict
    assurance_pno: Optional[dict] = None


@router.post("/{bien_id}/sinistre", response_model=SinistreResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def declare_sinistre(
    sci_id: UUID,
    bien_id: str,
    payload: SinistreCreate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Declare a sinistre (insurance claim) linked to PNO insurance."""
    logger.info("declaring_sinistre", bien_id=bien_id, sci_id=str(sci_id))

    client = _get_client(request)
    bien = _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    # Fetch PNO insurance for the bien
    pno_result = (
        client.table("assurances_pno")
        .select("*")
        .eq("id_bien", bien_id)
        .execute()
    )
    pno_info = (pno_result.data or [None])[0] if pno_result.data else None

    # Build the titre with numero_dossier if provided
    titre = "Sinistre"
    if payload.numero_dossier:
        titre = f"Sinistre {payload.numero_dossier}"

    # Create evenement for the sinistre
    evenement_row = {
        "id_bien": bien_id,
        "type": "sinistre",
        "titre": titre,
        "description": payload.description,
        "date_evenement": payload.date_sinistre.isoformat(),
        "montant": payload.montant_estime,
        "deductible_fiscalement": False,
    }

    write_client = _get_client(request)
    try:
        evt_result = write_client.table("evenements_bien").insert(evenement_row).execute()
        created_event = (evt_result.data or [{}])[0]
    except Exception as exc:
        logger.warning("evenements_bien_insert_skip", reason=str(exc))
        created_event = {"id": None, "type": "sinistre", "titre": evenement_row["titre"]}

    # Create notification with PNO assureur details

    adresse = bien.get("adresse", "un bien")
    assureur = pno_info.get("compagnie", "N/A") if pno_info else "Aucune PNO"

    owners = (
        client.table("associes")
        .select("user_id")
        .eq("id_sci", str(sci_id))
        .not_.is_("user_id", "null")
        .execute()
    )
    for owner in (owners.data or []):
        try:
            await create_notification_with_email(
                write_client,
                user_id=owner["user_id"],
                notification_type="sinistre",
                data={
                    "title": f"Sinistre declare — {adresse}",
                    "message": (
                        f"{payload.description}. "
                        f"Montant estime : {payload.montant_estime or 'N/A'} EUR. "
                        f"Assureur PNO : {assureur}."
                    ),
                    "metadata": {
                        "bien_id": bien_id,
                        "event_id": created_event.get("id"),
                        "numero_dossier": payload.numero_dossier,
                        "dedup_key": f"sinistre_{bien_id}_{payload.date_sinistre.isoformat()}",
                    },
                },
            )
        except Exception as notif_exc:
            logger.warning("sinistre_notification_skip", reason=str(notif_exc), user_id=owner["user_id"])

    logger.info("sinistre_declared", event_id=created_event.get("id"), bien_id=bien_id)
    return SinistreResponse(evenement=created_event, assurance_pno=pno_info)