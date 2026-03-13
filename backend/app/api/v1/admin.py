"""Admin panel API routes — restricted to users in the admins table."""

import logging

from fastapi import APIRouter, Depends, Query

from app.core.entitlements import PlanKey, resolve_plan_key_from_price_id
from app.core.security import get_current_admin
from app.core.supabase_client import get_supabase_service_client as get_service_client

ACTIVE_STATUSES = {"active", "trialing", "paid"}

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
    dependencies=[Depends(get_current_admin)],
)


@router.get("/stats")
async def admin_stats(admin_id: str = Depends(get_current_admin)):
    """Global platform statistics."""
    client = get_service_client()

    users_count = client.table("associes").select("user_id", count="exact").execute()
    scis_count = client.table("sci").select("id", count="exact").execute()
    biens_count = client.table("biens").select("id", count="exact").execute()
    subs = client.table("subscriptions").select("stripe_price_id, status").execute()

    active_subs = [s for s in (subs.data or []) if s.get("status") in ACTIVE_STATUSES]
    plan_breakdown = {}
    for s in active_subs:
        resolved = resolve_plan_key_from_price_id(s.get("stripe_price_id"))
        key = resolved.value if resolved else "free"
        plan_breakdown[key] = plan_breakdown.get(key, 0) + 1

    return {
        "total_users": users_count.count or 0,
        "total_scis": scis_count.count or 0,
        "total_biens": biens_count.count or 0,
        "active_subscriptions": len(active_subs),
        "plan_breakdown": plan_breakdown,
    }


@router.get("/users")
async def admin_list_users(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    admin_id: str = Depends(get_current_admin),
):
    """List all users with their subscription status."""
    client = get_service_client()
    offset = (page - 1) * per_page

    # Get users from auth.users via admin API
    auth_response = client.auth.admin.list_users(page=page, per_page=per_page)
    users = auth_response if isinstance(auth_response, list) else []

    # Get subscriptions for context
    subs = client.table("subscriptions").select("*").execute()
    subs_by_user = {s["user_id"]: s for s in (subs.data or [])}

    result = []
    for u in users:
        user_id = u.id if hasattr(u, "id") else u.get("id", "")
        email = u.email if hasattr(u, "email") else u.get("email", "")
        created = u.created_at if hasattr(u, "created_at") else u.get("created_at", "")
        sub = subs_by_user.get(user_id, {})
        resolved = resolve_plan_key_from_price_id(sub.get("stripe_price_id"))
        plan_key = resolved.value if resolved else "free"
        is_active = sub.get("status", "") in ACTIVE_STATUSES
        result.append({
            "id": user_id,
            "email": email,
            "created_at": str(created),
            "plan_key": plan_key,
            "is_active": is_active,
            "stripe_customer_id": sub.get("stripe_customer_id"),
        })

    return {"users": result, "page": page, "per_page": per_page}


@router.get("/users/{user_id}")
async def admin_get_user(
    user_id: str,
    admin_id: str = Depends(get_current_admin),
):
    """Get detailed info for a specific user."""
    client = get_service_client()

    # User auth info
    user = client.auth.admin.get_user_by_id(user_id)

    # User's SCIs (via associes)
    associes = client.table("associes").select("*, sci(*)").eq("user_id", user_id).execute()

    # User's subscription
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


@router.get("/subscriptions")
async def admin_list_subscriptions(
    admin_id: str = Depends(get_current_admin),
):
    """List all subscriptions."""
    client = get_service_client()
    result = client.table("subscriptions").select("*").order("created_at", desc=True).execute()
    return {"subscriptions": result.data or []}
