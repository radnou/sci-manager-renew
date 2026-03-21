"""Comptabilite API — annual accounting recap per SCI."""

from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, Request

from app.core.paywall import AssocieMembership, require_sci_membership
from app.core.supabase_client import get_supabase_user_client
from app.services.comptabilite_service import ComptabiliteService

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/scis/{sci_id}/comptabilite", tags=["comptabilite"])


@router.get("/{annee}")
async def get_comptabilite_annuelle(
    sci_id: UUID,
    annee: int,
    request: Request,
    membership: AssocieMembership = Depends(require_sci_membership),
):
    """Retourne le récapitulatif comptable annuel d'une SCI."""
    logger.info("get_comptabilite", sci_id=str(sci_id), annee=annee)

    client = get_supabase_user_client(request)
    service = ComptabiliteService()
    return service.get_recap_annuel(client, str(sci_id), annee)
