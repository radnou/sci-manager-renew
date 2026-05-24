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


@router.get("/{bien_id}/frais-agence", response_model=list[FraisAgenceResponse])
async def list_bien_frais_agence(
    sci_id: UUID,
    bien_id: str,
    request: Request,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Liste les frais d'agence d'un bien."""
    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = (
        client.table("frais_agence")
        .select("*")
        .eq("id_bien", bien_id)
        .order("created_at", desc=True)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    return result.data or []


# ──────────────────────────────────────────────────────────────
# CREATE frais agence
# ──────────────────────────────────────────────────────────────

@router.post("/{bien_id}/frais-agence", response_model=FraisAgenceResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_bien_frais_agence(
    sci_id: UUID,
    bien_id: str,
    payload: FraisAgenceCreate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Crée un frais d'agence pour un bien (gérant uniquement)."""
    logger.info("creating_frais_agence", bien_id=bien_id, sci_id=str(sci_id))

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    row = payload.model_dump(mode="json")
    row["id_bien"] = bien_id

    write_client = _get_client(request)
    result = write_client.table("frais_agence").insert(row).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise DatabaseError("Unable to create frais agence")

    created = data[0]
    logger.info("frais_agence_created", frais_id=created.get("id"), bien_id=bien_id)
    return created


# ──────────────────────────────────────────────────────────────
# DELETE frais agence
# ──────────────────────────────────────────────────────────────

@router.delete("/{bien_id}/frais-agence/{frais_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def delete_bien_frais_agence(
    sci_id: UUID,
    bien_id: str,
    frais_id: int,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Supprime un frais d'agence (gérant uniquement)."""
    logger.info("deleting_frais_agence", frais_id=frais_id, bien_id=bien_id)

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    result = client.table("frais_agence").delete().eq("id", frais_id).eq("id_bien", bien_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    logger.info("frais_agence_deleted", frais_id=frais_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ──────────────────────────────────────────────────────────────
# LIST documents for a bien
# ──────────────────────────────────────────────────────────────
