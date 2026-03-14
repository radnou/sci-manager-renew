"""Dashboard API — unified endpoint for the main dashboard view."""

from __future__ import annotations

from typing import Any

import structlog
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from app.core.supabase_client import get_supabase_user_client
from app.core.exceptions import DatabaseError, SCIManagerException
from app.core.security import get_current_user
from app.services.dashboard_service import (
    get_alertes,
    get_portfolio_kpis,
    get_recent_activity,
    get_sci_cards,
)

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def _get_client(request: Request):
    return get_supabase_user_client(request)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class AlerteItem(BaseModel):
    type: str
    severity: str
    message: str
    entity_id: str | None = None
    entity_type: str | None = None
    id_sci: str | None = None
    montant: float | None = None
    date: str | None = None
    sci_nom: str | None = None
    bien_adresse: str | None = None
    link: str | None = None


class PortfolioKPIs(BaseModel):
    sci_count: int = 0
    biens_count: int = 0
    taux_recouvrement: float = 0.0
    cashflow_net: float = 0.0
    loyers_total: float = 0.0
    loyers_payes: float = 0.0
    charges_total: float = 0.0


class SCICard(BaseModel):
    id: str
    nom: str
    statut: str = "active"
    biens_count: int = 0
    loyer_total: float = 0.0
    loyer_payes: float = 0.0
    recouvrement: float = 0.0


class ActivityItem(BaseModel):
    type: str
    id: str | None = None
    id_sci: str | None = None
    description: str = ""
    date: str | None = None
    created_at: str | None = None


class DashboardResponse(BaseModel):
    alertes: list[AlerteItem] = []
    kpis: PortfolioKPIs = PortfolioKPIs()
    scis: list[SCICard] = []
    activite: list[ActivityItem] = []


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.get("", response_model=DashboardResponse)
@router.get("/", response_model=DashboardResponse)
async def get_dashboard(
    request: Request,
    user_id: str = Depends(get_current_user),
):
    """
    Return the full dashboard payload in a single call:
    alertes, KPIs, SCI cards and recent activity.
    """
    logger.info("fetching_dashboard", user_id=user_id)

    try:
        client = _get_client(request)

        alertes = await get_alertes(client, user_id)
        kpis = await get_portfolio_kpis(client, user_id)
        scis = await get_sci_cards(client, user_id)
        activite = await get_recent_activity(client, user_id, limit=10)

        return DashboardResponse(
            alertes=alertes,
            kpis=kpis,
            scis=scis,
            activite=activite,
        )
    except SCIManagerException:
        raise
    except Exception as exc:
        logger.error("dashboard_fetch_failed", user_id=user_id, error=str(exc), exc_info=True)
        raise DatabaseError("Unable to fetch dashboard data")
