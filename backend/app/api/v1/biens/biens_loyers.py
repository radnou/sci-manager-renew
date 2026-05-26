from __future__ import annotations

from datetime import date, timedelta
from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, Response, UploadFile, status
from pydantic import BaseModel

from app.core.supabase_client import get_supabase_user_client, get_supabase_service_client
from app.core.exceptions import BusinessLogicError, DatabaseError, ResourceNotFoundError, ValidationError
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


@router.get("/{bien_id}/loyers", response_model=list[LoyerResponse])
async def list_bien_loyers(
    sci_id: UUID,
    bien_id: str,
    request: Request,
    membership: AssocieMembership = Depends(require_sci_membership),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(50, ge=1, le=100, description="Items per page"),
):
    """Liste les loyers d'un bien."""
    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    start = (page - 1) * page_size
    end = start + page_size - 1
    result = (
        client.table("loyers")
        .select("*")
        .eq("id_bien", bien_id)
        .order("date_loyer", desc=True)
        .range(start, end)
        .execute()
    )
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    return result.data or []


# ──────────────────────────────────────────────────────────────
# CREATE loyer for a bien
# ──────────────────────────────────────────────────────────────

@router.post("/{bien_id}/loyers", response_model=LoyerResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_bien_loyer(
    sci_id: UUID,
    bien_id: str,
    payload: LoyerCreate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Crée un loyer pour un bien (gérant uniquement)."""
    SubscriptionService.enforce_limit(membership.user_id, "biens")

    logger.info("creating_loyer_nested", bien_id=bien_id, sci_id=str(sci_id))

    client = _get_client(request)
    _verify_bien_belongs_to_sci(client, bien_id, str(sci_id))

    row = payload.model_dump(mode="json")
    row["id_bien"] = bien_id
    row["id_sci"] = str(sci_id)

    month_prefix = row["date_loyer"][:7]  # YYYY-MM
    existing = (
        client.table("loyers")
        .select("id, date_loyer")
        .eq("id_bien", bien_id)
        .gte("date_loyer", f"{month_prefix}-01")
        .lte("date_loyer", f"{month_prefix}-31")
        .limit(1)
        .execute()
    )
    if existing.data:
        existing_id = existing.data[0].get("id")
        raise BusinessLogicError(
            "Un loyer existe déjà pour ce mois sur ce bien. Voulez-vous le modifier ?",
            details={"existing_loyer_id": existing_id} if existing_id else None,
        )

    write_client = _get_client(request)
    result = write_client.table("loyers").insert(row).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    data = result.data or []
    if not data:
        raise DatabaseError("Unable to create loyer")

    created = data[0]
    logger.info("loyer_created_nested", loyer_id=created.get("id"), bien_id=bien_id)
    return created


# ──────────────────────────────────────────────────────────────
# LIST baux for a bien (history)
# ──────────────────────────────────────────────────────────────
