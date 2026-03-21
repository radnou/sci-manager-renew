"""Echeances API — upcoming deadlines for a user's SCIs."""

from __future__ import annotations

from typing import Optional

import structlog
from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel

from app.core.exceptions import DatabaseError, SCIManagerException
from app.core.security import get_current_user
from app.core.supabase_client import get_supabase_user_client
from app.services.echeances_service import EcheancesService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/echeances", tags=["echeances"])

_service = EcheancesService()


def _get_client(request: Request):
    return get_supabase_user_client(request)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class EcheanceItem(BaseModel):
    type: str
    entite: str
    titre: str
    description: str
    date_echeance: str
    urgence: str
    reference_legale: str = ""
    consequence: str = ""
    action_url: str = ""


class EcheanceResume(BaseModel):
    depassee: int = 0
    critique: int = 0
    urgente: int = 0
    normale: int = 0
    lointaine: int = 0


class EcheancesResponse(BaseModel):
    echeances: list[EcheanceItem] = []
    resume: EcheanceResume = EcheanceResume()


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get("", response_model=EcheancesResponse)
@router.get("/", response_model=EcheancesResponse)
async def get_echeances(
    request: Request,
    user_id: str = Depends(get_current_user),
    sci_id: Optional[str] = Query(None, description="Filter by SCI id"),
    urgence: Optional[str] = Query(None, description="Filter by urgency levels (comma-separated: critique,urgente)"),
):
    """
    Return all upcoming deadlines for the authenticated user's SCIs.

    Optional filters:
    - sci_id: restrict to a single SCI
    - urgence: comma-separated urgency levels to include
    """
    logger.info("fetching_echeances", user_id=user_id, sci_id=sci_id, urgence=urgence)

    try:
        client = _get_client(request)
        result = _service.get_echeances(client, user_id, sci_id=sci_id)

        # Filter by urgency if requested
        if urgence:
            levels = {u.strip() for u in urgence.split(",")}
            result["echeances"] = [
                e for e in result["echeances"] if e["urgence"] in levels
            ]

        return EcheancesResponse(**result)
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("echeances_fetch_failed", user_id=user_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to fetch echeances data")
