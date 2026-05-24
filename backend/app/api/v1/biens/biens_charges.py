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


@router.get("/{bien_id}/charges", response_model=list[ChargeResponse])
async def list_bien_charges(
    sci_id: UUID,
    bien_id: str,
    request: Request,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Liste les charges d'un bien."""
    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = (
        client.table("charges")
        .select("*")
        .eq("id_bien", bien_id)
        .order("date_paiement", desc=True)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    return result.data or []


# ──────────────────────────────────────────────────────────────
# CREATE charge for a bien
# ──────────────────────────────────────────────────────────────

@router.post("/{bien_id}/charges", response_model=ChargeResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_bien_charge(
    sci_id: UUID,
    bien_id: str,
    payload: ChargeCreate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Crée une charge pour un bien (gérant uniquement)."""
    logger.info("creating_charge", bien_id=bien_id, sci_id=str(sci_id))

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    row = payload.model_dump(mode="json")
    row["id_bien"] = bien_id
    # Note: charges table has no id_sci column — scoping is via id_bien → biens.id_sci

    write_client = _get_client(request)
    result = write_client.table("charges").insert(row).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise DatabaseError("Unable to create charge")

    created = data[0]
    logger.info("charge_created", charge_id=created.get("id"), bien_id=bien_id)
    return created


# ──────────────────────────────────────────────────────────────
# UPDATE charge
# ──────────────────────────────────────────────────────────────

@router.patch("/{bien_id}/charges/{charge_id}", response_model=ChargeResponse)
@limiter.limit("30/minute")
async def update_bien_charge(
    sci_id: UUID,
    bien_id: str,
    charge_id: str,
    payload: ChargeUpdate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Met à jour une charge (gérant uniquement)."""
    update_payload = payload.model_dump(exclude_unset=True, mode="json")
    logger.info("updating_charge", charge_id=charge_id, bien_id=bien_id, fields=list(update_payload.keys()))

    if not update_payload:
        raise DatabaseError("No update fields provided")

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = (
        client.table("charges")
        .update(update_payload)
        .eq("id", charge_id)
        .eq("id_bien", bien_id)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise ResourceNotFoundError("Charge", charge_id)

    logger.info("charge_updated", charge_id=charge_id)
    return data[0]


# ──────────────────────────────────────────────────────────────
# DELETE charge
# ──────────────────────────────────────────────────────────────

@router.delete("/{bien_id}/charges/{charge_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def delete_bien_charge(
    sci_id: UUID,
    bien_id: str,
    charge_id: str,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Supprime une charge (gérant uniquement)."""
    logger.info("deleting_charge", charge_id=charge_id, bien_id=bien_id)

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = client.table("charges").delete().eq("id", charge_id).eq("id_bien", bien_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    logger.info("charge_deleted", charge_id=charge_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────
# GET assurance PNO for a bien
# ──────────────────────────────────────────────────────────────
