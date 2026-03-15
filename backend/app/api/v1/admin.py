"""Admin panel API routes — restricted to users in the admins table."""

import structlog

from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_admin
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
    dependencies=[Depends(get_current_admin)],
)


@router.get("/metrics")
async def admin_metrics(admin_id: str = Depends(get_current_admin)):
    """Hero KPIs with trend comparison."""
    return compute_hero_metrics()


@router.get("/alerts")
async def admin_alerts(admin_id: str = Depends(get_current_admin)):
    """Business alerts based on metric thresholds."""
    return compute_business_alerts()


@router.get("/funnel")
async def admin_funnel(admin_id: str = Depends(get_current_admin)):
    """Activation funnel counts."""
    return compute_activation_funnel()


@router.get("/users")
async def admin_list_users(
    search: str | None = Query(None),
    status: str | None = Query(None),
    plan: str | None = Query(None),
    sort: str = Query("created_at"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    admin_id: str = Depends(get_current_admin),
):
    """Enriched user list with filters and status classification."""
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
    admin_id: str = Depends(get_current_admin),
):
    """Detailed info for a specific user (kept for future use)."""
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
