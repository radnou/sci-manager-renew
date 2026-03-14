"""CRUD API for assemblees generales (general assembly registry) under /scis/{sci_id}/assemblees-generales."""

from __future__ import annotations

from datetime import date
from typing import Optional
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, Field

from app.core.exceptions import DatabaseError, GererSCIException, ResourceNotFoundError
from app.core.paywall import AssocieMembership, require_gerant_role, require_sci_membership
from app.core.supabase_client import get_supabase_service_client

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/scis/{sci_id}/assemblees-generales", tags=["assemblees-generales"])


# ──────────────────────────────────────────────────────────────
# Pydantic models
# ──────────────────────────────────────────────────────────────


class AGCreate(BaseModel):
    date_ag: date
    type_ag: str = Field(..., min_length=1, max_length=50)
    exercice_annee: int = Field(..., ge=2000, le=2100)
    ordre_du_jour: Optional[str] = None
    pv_url: Optional[str] = None
    quorum_atteint: bool = False
    resolutions: Optional[str] = None
    notes: Optional[str] = None


class AGResponse(BaseModel):
    id: str
    id_sci: str
    date_ag: date
    type_ag: str
    exercice_annee: int
    ordre_du_jour: Optional[str] = None
    pv_url: Optional[str] = None
    quorum_atteint: bool
    resolutions: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[str] = None


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────


def _get_client():
    return get_supabase_service_client()


# ──────────────────────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────────────────────


@router.get("", response_model=list[AGResponse])
@router.get("/", response_model=list[AGResponse])
async def list_assemblees_generales(
    sci_id: UUID,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """List all general assemblies for a given SCI."""
    logger.info("listing_assemblees_generales", sci_id=str(sci_id), user_id=membership.user_id)

    try:
        client = _get_client()
        result = client.table("assemblees_generales").select("*").eq("id_sci", str(sci_id)).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        rows = result.data or []
        rows.sort(key=lambda r: str(r.get("date_ag", "")), reverse=True)
        return rows
    except GererSCIException:
        raise
    except Exception as exc:
        logger.error("list_assemblees_generales_failed", sci_id=str(sci_id), error=str(exc), exc_info=True)
        raise DatabaseError("Unable to list assemblees generales")


@router.post("", response_model=AGResponse, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=AGResponse, status_code=status.HTTP_201_CREATED)
async def create_assemblee_generale(
    sci_id: UUID,
    payload: AGCreate,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Create a new general assembly record. Requires gerant role."""
    logger.info(
        "creating_assemblee_generale",
        sci_id=str(sci_id),
        user_id=membership.user_id,
        type_ag=payload.type_ag,
        exercice_annee=payload.exercice_annee,
    )

    try:
        client = _get_client()
        insert_data = payload.model_dump(mode="json")
        insert_data["id_sci"] = str(sci_id)

        result = client.table("assemblees_generales").insert(insert_data).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        rows = result.data or []
        if not rows:
            raise DatabaseError("Unable to create assemblee generale")

        return rows[0]
    except GererSCIException:
        raise
    except Exception as exc:
        logger.error("create_assemblee_generale_failed", sci_id=str(sci_id), error=str(exc), exc_info=True)
        raise DatabaseError("Unable to create assemblee generale")


@router.patch("/{ag_id}", response_model=AGResponse)
async def update_assemblee_generale(
    sci_id: UUID,
    ag_id: UUID,
    payload: AGCreate,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Update an existing general assembly record. Requires gerant role."""
    logger.info(
        "updating_assemblee_generale",
        sci_id=str(sci_id),
        ag_id=str(ag_id),
        user_id=membership.user_id,
    )

    try:
        client = _get_client()

        # Verify the AG exists and belongs to this SCI
        check = client.table("assemblees_generales").select("id").eq("id", str(ag_id)).eq("id_sci", str(sci_id)).execute()
        if getattr(check, "error", None):
            raise DatabaseError(str(check.error))
        if not (check.data or []):
            raise ResourceNotFoundError("AssembleeGenerale", str(ag_id))

        update_data = payload.model_dump(mode="json")
        result = client.table("assemblees_generales").update(update_data).eq("id", str(ag_id)).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        rows = result.data or []
        if not rows:
            raise ResourceNotFoundError("AssembleeGenerale", str(ag_id))

        return rows[0]
    except GererSCIException:
        raise
    except Exception as exc:
        logger.error("update_assemblee_generale_failed", ag_id=str(ag_id), error=str(exc), exc_info=True)
        raise DatabaseError("Unable to update assemblee generale")


@router.delete("/{ag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_assemblee_generale(
    sci_id: UUID,
    ag_id: UUID,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Delete a general assembly record. Requires gerant role."""
    logger.info(
        "deleting_assemblee_generale",
        sci_id=str(sci_id),
        ag_id=str(ag_id),
        user_id=membership.user_id,
    )

    try:
        client = _get_client()

        # Verify the AG exists and belongs to this SCI
        check = client.table("assemblees_generales").select("id").eq("id", str(ag_id)).eq("id_sci", str(sci_id)).execute()
        if getattr(check, "error", None):
            raise DatabaseError(str(check.error))
        if not (check.data or []):
            raise ResourceNotFoundError("AssembleeGenerale", str(ag_id))

        result = client.table("assemblees_generales").delete().eq("id", str(ag_id)).execute()
        if getattr(result, "error", None):
            raise DatabaseError(str(result.error))

        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except GererSCIException:
        raise
    except Exception as exc:
        logger.error("delete_assemblee_generale_failed", ag_id=str(ag_id), error=str(exc), exc_info=True)
        raise DatabaseError("Unable to delete assemblee generale")
