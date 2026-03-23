"""Admin panel API routes — protected by X-Admin-Key header or query param."""

import structlog

from fastapi import APIRouter, Query, HTTPException, Body, Request

from app.core.security import verify_admin_secret
from app.services.admin_metrics_service import (
    compute_hero_metrics,
    compute_business_alerts,
    compute_activation_funnel,
    compute_enriched_users,
    compute_revenue_breakdown,
    compute_arpu,
    compute_cohort_retention,
)
from app.services.mrr_snapshot_service import take_mrr_snapshot
from app.services.admin_audit_service import log_admin_action, get_audit_log

logger = structlog.get_logger(__name__)

# Plan price IDs for manual plan changes
PLAN_PRICE_MAP = {
    "free": None,
    "gestion": "price_gestion",
    "pilotage": "price_pilotage",
    "fondateur": "price_fondateur",
    "cabinet": "price_cabinet",
    # Legacy
    "starter": "price_starter",
    "pro": "price_pro",
    "lifetime": "price_lifetime",
}

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
)


@router.get("/metrics")
async def admin_metrics(request: Request):
    """Hero KPIs with trend comparison."""
    verify_admin_secret(request)
    return compute_hero_metrics()


@router.get("/alerts")
async def admin_alerts(request: Request):
    """Business alerts based on metric thresholds."""
    verify_admin_secret(request)
    return compute_business_alerts()


@router.get("/funnel")
async def admin_funnel(request: Request):
    """Activation funnel counts."""
    verify_admin_secret(request)
    return compute_activation_funnel()


@router.get("/users")
async def admin_list_users(
    request: Request,
    search: str | None = Query(None),
    status: str | None = Query(None),
    plan: str | None = Query(None),
    sort: str = Query("created_at"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
):
    """Enriched user list with filters and status classification."""
    verify_admin_secret(request)
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
    request: Request,
    user_id: str,
):
    """Detailed info for a specific user."""
    verify_admin_secret(request)
    from app.core.supabase_client import get_supabase_service_client

    client = get_supabase_service_client()
    user = client.auth.admin.get_user_by_id(user_id)
    associes = client.table("associes").select("*, sci(*)").eq("user_id", user_id).execute()
    sub = client.table("subscriptions").select("*").eq("user_id", user_id).maybe_single().execute()

    user_data = user.user if hasattr(user, "user") else user

    # Fetch biens and loyers for each SCI
    sci_ids = [a["id_sci"] for a in (associes.data or []) if a.get("id_sci")]
    biens_data = []
    loyers_count = 0
    if sci_ids:
        biens = client.table("biens").select("id, adresse, ville, id_sci").in_("id_sci", sci_ids).execute()
        biens_data = biens.data or []
        bien_ids = [b["id"] for b in biens_data]
        if bien_ids:
            loyers = client.table("loyers").select("id", count="exact").in_("id_bien", bien_ids).execute()
            loyers_count = loyers.count or 0

    return {
        "user": {
            "id": user_data.id if hasattr(user_data, "id") else user_id,
            "email": user_data.email if hasattr(user_data, "email") else "",
            "created_at": str(user_data.created_at if hasattr(user_data, "created_at") else ""),
        },
        "scis": associes.data or [],
        "biens": biens_data,
        "loyers_count": loyers_count,
        "subscription": sub.data if sub and sub.data else None,
    }


@router.put("/users/{user_id}/plan")
async def admin_change_plan(
    request: Request,
    user_id: str,
    plan: str = Body(..., embed=True),
):
    """Change a user's subscription plan."""
    verify_admin_secret(request)
    from app.core.supabase_client import get_supabase_service_client

    if plan not in PLAN_PRICE_MAP:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {plan}. Valid: {list(PLAN_PRICE_MAP.keys())}")

    client = get_supabase_service_client()
    price_id = PLAN_PRICE_MAP[plan]
    ip = request.client.host if request.client else "unknown"

    if plan == "free":
        # Delete subscription row (revert to free)
        client.table("subscriptions").delete().eq("user_id", user_id).execute()
        logger.info("admin_plan_changed", user_id=user_id, plan=plan)
        await log_admin_action(
            action="plan_change",
            target_user_id=user_id,
            details={"plan": plan},
            ip=ip,
        )
        return {"status": "ok", "plan": plan}

    # Upsert subscription
    sub_data = {
        "user_id": user_id,
        "stripe_price_id": price_id,
        "status": "active",
        "mode": "subscription",
        "onboarding_completed": True,
    }
    client.table("subscriptions").upsert(sub_data, on_conflict="user_id").execute()
    logger.info("admin_plan_changed", user_id=user_id, plan=plan)
    await log_admin_action(
        action="plan_change",
        target_user_id=user_id,
        details={"plan": plan, "price_id": price_id},
        ip=ip,
    )
    return {"status": "ok", "plan": plan}


@router.post("/users/{user_id}/email")
async def admin_send_email(
    request: Request,
    user_id: str,
    subject: str = Body(...),
    message: str = Body(...),
):
    """Send a custom email to a user using the branded email template."""
    verify_admin_secret(request)
    from app.core.supabase_client import get_supabase_service_client
    from app.services.email_service import EmailService, _render_template

    client = get_supabase_service_client()
    user = client.auth.admin.get_user_by_id(user_id)
    user_data = user.user if hasattr(user, "user") else user
    email = user_data.email if hasattr(user_data, "email") else ""
    ip = request.client.host if request.client else "unknown"

    if not email:
        raise HTTPException(status_code=400, detail="User has no email")

    html = _render_template("admin_message.html", subject=subject, message=message)

    import resend
    from app.core.config import settings
    resend.api_key = settings.resend_api_key

    resend.Emails.send({
        "from": settings.resend_from_email,
        "to": email,
        "subject": subject,
        "html": html,
    })

    logger.info("admin_email_sent", user_id=user_id, email=email, subject=subject)
    await log_admin_action(
        action="send_email",
        target_user_id=user_id,
        details={"subject": subject, "email": email},
        ip=ip,
    )
    return {"status": "ok", "email": email}


@router.delete("/users/{user_id}")
async def admin_disable_user(
    request: Request,
    user_id: str,
):
    """Disable a user account (ban from Supabase Auth)."""
    verify_admin_secret(request)
    from app.core.supabase_client import get_supabase_service_client

    client = get_supabase_service_client()
    ip = request.client.host if request.client else "unknown"
    client.auth.admin.update_user_by_id(user_id, {"ban_duration": "876000h"})  # ~100 years
    logger.info("admin_user_disabled", user_id=user_id)
    await log_admin_action(
        action="disable_user",
        target_user_id=user_id,
        details={"ban_duration": "876000h"},
        ip=ip,
    )
    return {"status": "ok", "user_id": user_id}


# ── New KPI endpoints ────────────────────────────────────────────────


@router.get("/revenue")
async def admin_revenue(request: Request):
    """MRR breakdown per plan."""
    verify_admin_secret(request)
    return compute_revenue_breakdown()


@router.get("/cohorts")
async def admin_cohorts(
    request: Request,
    months: int = Query(6, ge=1, le=24),
):
    """Monthly cohort retention table."""
    verify_admin_secret(request)
    return compute_cohort_retention(months=months)


@router.post("/snapshots/mrr")
async def admin_take_mrr_snapshot(request: Request):
    """Manually trigger an MRR snapshot for today."""
    verify_admin_secret(request)
    return await take_mrr_snapshot()


# ── Audit log endpoint ───────────────────────────────────────────────


@router.get("/audit-log")
async def admin_audit_log(
    request: Request,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
):
    """Paginated admin audit log."""
    verify_admin_secret(request)
    return get_audit_log(page=page, per_page=per_page)
