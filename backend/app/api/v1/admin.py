"""Admin panel API routes — protected by ADMIN_SECRET_KEY query param."""

import structlog

from fastapi import APIRouter, Query, HTTPException

from app.core.security import verify_admin_secret
from app.services.admin_metrics_service import (
    compute_hero_metrics,
    compute_business_alerts,
    compute_activation_funnel,
    compute_enriched_users,
)

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
)


@router.get("/metrics")
async def admin_metrics(key: str | None = Query(None)):
    """Hero KPIs with trend comparison."""
    verify_admin_secret(key)
    return compute_hero_metrics()


@router.get("/alerts")
async def admin_alerts(key: str | None = Query(None)):
    """Business alerts based on metric thresholds."""
    verify_admin_secret(key)
    return compute_business_alerts()


@router.get("/funnel")
async def admin_funnel(key: str | None = Query(None)):
    """Activation funnel counts."""
    verify_admin_secret(key)
    return compute_activation_funnel()


@router.get("/users")
async def admin_list_users(
    key: str | None = Query(None),
    search: str | None = Query(None),
    status: str | None = Query(None),
    plan: str | None = Query(None),
    sort: str = Query("created_at"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
):
    """Enriched user list with filters and status classification."""
    verify_admin_secret(key)
    return compute_enriched_users(
        search=search,
        status_filter=status,
        plan_filter=plan,
        sort=sort,
        page=page,
        per_page=per_page,
    )


@router.get("/users/{user_id}")
async def admin_get_user(
    user_id: str,
    key: str | None = Query(None),
):
    """Detailed info for a specific user."""
    verify_admin_secret(key)
    from app.core.supabase_client import get_supabase_service_client

    client = get_supabase_service_client()
    user = client.auth.admin.get_user_by_id(user_id)
    associes = client.table("associes").select("*, sci(*)").eq("user_id", user_id).execute()
    sub = client.table("subscriptions").select("*").eq("user_id", user_id).maybe_single().execute()

    user_data = user.user if hasattr(user, "user") else user
    return {
        "user": {
            "id": user_data.id if hasattr(user_data, "id") else user_id,
            "email": user_data.email if hasattr(user_data, "email") else "",
            "created_at": str(user_data.created_at if hasattr(user_data, "created_at") else ""),
        },
        "scis": associes.data or [],
        "subscription": sub.data if sub.data else None,
    }
