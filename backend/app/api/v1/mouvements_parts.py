"""CRUD API for mouvements de parts (share transfers registry) under /scis/{sci_id}/mouvements-parts."""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Request, Response, status
from pydantic import BaseModel, Field

from app.core.exceptions import DatabaseError, GererSCIException, ResourceNotFoundError
from app.core.paywall import AssocieMembership, require_gerant_role, require_sci_membership
from app.core.supabase_client import get_supabase_user_client, get_supabase_service_client

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/scis/{sci_id}/mouvements-parts", tags=["mouvements-parts"])


# ──────────────────────────────────────────────────────────────
# Pydantic models
# ──────────────────────────────────────────────────────────────


class MouvementPartsCreate(BaseModel):
    date_mouvement: date
    type_mouvement: str = Field(..., min_length=1, max_length=50)
    cedant_nom: str = Field(..., min_length=1, max_length=200)
    cessionnaire_nom: str = Field(..., min_length=1, max_length=200)
    nb_parts: int = Field(..., gt=0)
    prix_unitaire: float = Field(..., ge=0)
    prix_total: float = Field(..., ge=0)
    document_url: Optional[str] = None
    notes: Optional[str] = None


class MouvementPartsResponse(BaseModel):
    id: str
    id_sci: str
    date_mouvement: date
    type_mouvement: str
    cedant_nom: str
    cessionnaire_nom: str
    nb_parts: int
    prix_unitaire: float
    prix_total: float
    document_url: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────


def _get_client(request: Request):
    return get_supabase_user_client(request)


def _get_write_client():
    """Service client for INSERT operations — RLS blocks inserts before membership exists."""
    return get_supabase_service_client()


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────


@router.get("", response_model=list[MouvementPartsResponse])
@router.get("/", response_model=list[MouvementPartsResponse])
async def list_mouvements_parts(
    sci_id: UUID,
    request: Request,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """List all share transfer movements for a given SCI."""
    logger.info("listing_mouvements_parts", sci_id=str(sci_id), user_id=membership.user_id)

    try:
        client = _get_client(request)
        result = client.table("mouvements_parts").select("*").eq("id_sci", str(sci_id)).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        rows = result.data or []
        rows.sort(key=lambda r: str(r.get("date_mouvement", "")), reverse=True)
        return rows
    except GererSCIException:
        raise
    except Exception as exc:
        logger.error("list_mouvements_parts_failed", sci_id=str(sci_id), error=str(exc), exc_info=True)
        raise DatabaseError("Unable to list mouvements de parts")


@router.post("", response_model=MouvementPartsResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=MouvementPartsResponse, status_code=status.HTTP_201_CREATED)
async def create_mouvement_parts(
    sci_id: UUID,
    payload: MouvementPartsCreate,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Create a new share transfer movement. Requires gerant role."""
    logger.info(
        "creating_mouvement_parts",
        sci_id=str(sci_id),
        user_id=membership.user_id,
        type_mouvement=payload.type_mouvement,
    )

    try:
        client = _get_client(request)
        insert_data = payload.model_dump(mode="json")
        insert_data["id_sci"] = str(sci_id)

        write_client = _get_write_client()
        result = write_client.table("mouvements_parts").insert(insert_data).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        rows = result.data or []
        if not rows:
            raise DatabaseError("Unable to create mouvement de parts")

        return rows[0]
    except GererSCIException:
        raise
    except Exception as exc:
        logger.error("create_mouvement_parts_failed", sci_id=str(sci_id), error=str(exc), exc_info=True)
        raise DatabaseError("Unable to create mouvement de parts")


@router.delete("/{mouvement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_mouvement_parts(
    sci_id: UUID,
    mouvement_id: UUID,
    request: Request,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Delete a share transfer movement. Requires gerant role."""
    logger.info(
        "deleting_mouvement_parts",
        sci_id=str(sci_id),
        mouvement_id=str(mouvement_id),
        user_id=membership.user_id,
    )

    try:
        client = _get_client(request)

        # Verify the mouvement exists and belongs to this SCI
        check = client.table("mouvements_parts").select("id").eq("id", str(mouvement_id)).eq("id_sci", str(sci_id)).execute()
        if getattr(check, "error", None):
            raise DatabaseError(str(check.error))
        if not (check.data or []):
            raise ResourceNotFoundError("MouvementParts", str(mouvement_id))

        result = client.table("mouvements_parts").delete().eq("id", str(mouvement_id)).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except GererSCIException:
        raise
    except Exception as exc:
        logger.error("delete_mouvement_parts_failed", mouvement_id=str(mouvement_id), error=str(exc), exc_info=True)
        raise DatabaseError("Unable to delete mouvement de parts")
