"""Demo data API — seed and cleanup demo data for new users."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Request

from app.core.security import get_current_user
from app.core.supabase_client import get_supabase_service_client
from app.core.rate_limit import limiter
from app.services.demo_service import seed_demo_data, cleanup_demo_data

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/seed", status_code=201)
@limiter.limit("10/hour")
async def seed_demo(request: Request, user=Depends(get_current_user)):
    """Seed demo data for a new user. Only works once (idempotent)."""
    client = get_supabase_service_client()

    # Check if already seeded
    sub_res = (
        client.table("subscriptions")
        .select("demo_seeded, status")
        .eq("user_id", user)
        .execute()
    )
    if sub_res.data:
        sub = sub_res.data[0]
        if sub.get("demo_seeded"):
            return {"message": "Données de démonstration déjà chargées.", "already_seeded": True}
        if sub.get("status") in ("active", "paid"):
            return {"message": "Abonnement actif — pas de données demo nécessaires.", "already_seeded": False}

    result = await seed_demo_data(client, user)
    return {"message": "Données de démonstration chargées avec succès.", "sci_id": result["sci_id"]}


@router.delete("/cleanup", status_code=200)
@limiter.limit("1/minute")
async def cleanup_demo(request: Request, user=Depends(get_current_user)):
    """Remove all demo data for the current user."""
    client = get_supabase_service_client()
    deleted = await cleanup_demo_data(client, user)
    return {"message": f"{deleted} enregistrements de démonstration supprimés.", "deleted": deleted}
