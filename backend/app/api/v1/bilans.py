"""Bilans mensuels API — monthly accounting snapshots."""

from __future__ import annotations

import re

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import StreamingResponse
from io import BytesIO

from app.core.paywall import SubscriptionInfo, require_active_subscription
from app.core.supabase_client import get_supabase_user_client
from app.services.bilan_mensuel_service import (
    get_or_generate_bilan,
    list_periodes,
)
from app.services.bilan_pdf_service import generate_bilan_pdf

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/bilans", tags=["bilans"])

_PERIODE_RE = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])$")
_VALID_SCOPES = {"portefeuille", "sci", "bien"}


def _validate_periode(periode: str) -> str:
    if not _PERIODE_RE.match(periode):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Format période invalide. Attendu : YYYY-MM",
        )
    return periode


def _validate_scope(scope: str, scope_id: str | None) -> None:
    if scope not in _VALID_SCOPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Scope invalide. Valeurs possibles: {', '.join(_VALID_SCOPES)}",
        )
    if scope in ("sci", "bien") and not scope_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"scope_id requis pour scope={scope}",
        )


@router.get("")
@router.get("/")
async def get_bilan(
    request: Request,
    periode: str = Query(..., description="Periode YYYY-MM"),
    scope: str = Query("portefeuille", description="portefeuille | sci | bien"),
    scope_id: str | None = Query(None, description="UUID SCI ou bien"),
    force_refresh: bool = Query(False, description="Forcer le recalcul"),
    subscription: SubscriptionInfo = Depends(require_active_subscription),
):
    """Return bilan data for a given period and scope."""
    _validate_periode(periode)
    _validate_scope(scope, scope_id)

    client = get_supabase_user_client(request)
    data = await get_or_generate_bilan(
        client,
        subscription.user_id,
        periode,
        scope=scope,
        scope_id=scope_id,
        force_refresh=force_refresh,
    )
    return data


@router.get("/pdf")
async def get_bilan_pdf(
    request: Request,
    periode: str = Query(..., description="Periode YYYY-MM"),
    scope: str = Query("portefeuille", description="portefeuille | sci | bien"),
    scope_id: str | None = Query(None, description="UUID SCI ou bien"),
    subscription: SubscriptionInfo = Depends(require_active_subscription),
):
    """Return bilan as a downloadable PDF."""
    _validate_periode(periode)
    _validate_scope(scope, scope_id)

    client = get_supabase_user_client(request)
    data = await get_or_generate_bilan(
        client,
        subscription.user_id,
        periode,
        scope=scope,
        scope_id=scope_id,
    )

    pdf_bytes = generate_bilan_pdf(data, scope=scope, scope_id=scope_id)

    filename = f"bilan_{periode}_{scope}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/periodes")
async def get_periodes(
    request: Request,
    subscription: SubscriptionInfo = Depends(require_active_subscription),
):
    """Return list of available YYYY-MM periods based on loyers data."""
    client = get_supabase_user_client(request)
    periodes = await list_periodes(client, subscription.user_id)
    return {"periodes": periodes}
