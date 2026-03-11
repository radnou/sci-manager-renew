"""Finances API — aggregated cross-SCI financial overview."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.core.paywall import SubscriptionInfo, require_active_subscription
from app.core.supabase_client import get_supabase_service_client
from app.services.finances_service import get_finances_overview

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/finances", tags=["finances"])


class FinancesResponse(BaseModel):
    revenus_total: float = 0
    charges_total: float = 0
    cashflow_net: float = 0
    taux_recouvrement: float = 0
    patrimoine_total: float = 0
    rentabilite_moyenne: float = 0
    evolution_mensuelle: list[dict] = []
    repartition_sci: list[dict] = []


@router.get("", response_model=FinancesResponse)
@router.get("/", response_model=FinancesResponse)
async def get_finances(
    period: str = Query("12m", description="Period: 6m, 12m, 24m"),
    subscription: SubscriptionInfo = Depends(require_active_subscription),
):
    """Return aggregated cross-SCI financial data."""
    # Parse period
    period_months = 12
    if period == "6m":
        period_months = 6
    elif period == "24m":
        period_months = 24

    client = get_supabase_service_client()
    data = await get_finances_overview(client, subscription.user_id, period_months)

    return FinancesResponse(**data)
