"""MRR Snapshot service — computes and persists daily MRR snapshots."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from collections import defaultdict

import structlog

from app.core.entitlements import resolve_plan_key_from_price_id
from app.core.supabase_client import get_supabase_service_client

logger = structlog.get_logger(__name__)

ACTIVE_STATUSES = {"active", "trialing", "paid"}

# Monthly prices for MRR computation (EUR).
MRR_MONTHLY_PRICES: dict[str, float] = {
    "free": 0.0,
    "starter": 9.90,
    "gestion": 9.90,
    "pro": 19.90,
    "pilotage": 19.90,
    "fondateur": 0.0,   # one-time lifetime, excluded from recurring MRR
    "cabinet": 49.90,
    "lifetime": 0.0,
}


def _resolve_plan(stripe_price_id: str | None) -> str:
    """Resolve stripe_price_id to plan key string."""
    if not stripe_price_id:
        return "free"
    resolved = resolve_plan_key_from_price_id(stripe_price_id)
    return resolved.value if resolved else "free"


def _compute_mrr_breakdown(client) -> tuple[float, dict[str, float], int]:
    """
    Returns (total_mrr, mrr_by_plan, active_subscribers).
    mrr_by_plan maps plan_key → monthly revenue contribution.
    """
    subs = client.table("subscriptions").select("stripe_price_id, status").execute()
    mrr_by_plan: dict[str, float] = defaultdict(float)
    active_count = 0

    for s in subs.data or []:
        if s.get("status") in ACTIVE_STATUSES:
            plan = _resolve_plan(s.get("stripe_price_id"))
            monthly = MRR_MONTHLY_PRICES.get(plan, 0.0)
            mrr_by_plan[plan] += monthly
            if monthly > 0:
                active_count += 1

    total_mrr = round(sum(mrr_by_plan.values()), 2)
    return total_mrr, {k: round(v, 2) for k, v in mrr_by_plan.items()}, active_count


async def take_mrr_snapshot() -> dict:
    """
    Compute current MRR, breakdown by plan, ARPU and persist to admin_mrr_snapshots.
    Safe to call multiple times on the same day (UNIQUE on snapshot_date → upsert).
    """
    client = get_supabase_service_client()
    today = date.today().isoformat()

    total_mrr, mrr_by_plan, active_subscribers = _compute_mrr_breakdown(client)
    arpu = round(total_mrr / active_subscribers, 2) if active_subscribers > 0 else 0.0

    row = {
        "snapshot_date": today,
        "total_mrr": total_mrr,
        "mrr_by_plan": mrr_by_plan,
        "active_subscribers": active_subscribers,
        "arpu": arpu,
    }

    result = (
        client.table("admin_mrr_snapshots")
        .upsert(row, on_conflict="snapshot_date")
        .execute()
    )

    logger.info(
        "mrr_snapshot_taken",
        date=today,
        total_mrr=total_mrr,
        active_subscribers=active_subscribers,
        arpu=arpu,
    )
    return {
        "snapshot_date": today,
        "total_mrr": total_mrr,
        "mrr_by_plan": mrr_by_plan,
        "active_subscribers": active_subscribers,
        "arpu": arpu,
    }


def get_mrr_trend(days: int = 30) -> dict:
    """
    Return MRR trend: current period vs previous period using stored snapshots.
    Falls back to live computation when no snapshots exist yet.
    """
    client = get_supabase_service_client()
    today = date.today()
    cutoff_current = (today - timedelta(days=days)).isoformat()
    cutoff_previous = (today - timedelta(days=days * 2)).isoformat()

    # Latest snapshot in current window
    current_rows = (
        client.table("admin_mrr_snapshots")
        .select("total_mrr, snapshot_date")
        .gte("snapshot_date", cutoff_current)
        .order("snapshot_date", desc=True)
        .limit(1)
        .execute()
    )

    # Latest snapshot in previous window
    previous_rows = (
        client.table("admin_mrr_snapshots")
        .select("total_mrr, snapshot_date")
        .gte("snapshot_date", cutoff_previous)
        .lt("snapshot_date", cutoff_current)
        .order("snapshot_date", desc=True)
        .limit(1)
        .execute()
    )

    # Fall back to live computation if no snapshots available
    if not (current_rows.data or []):
        total_mrr, _, _ = _compute_mrr_breakdown(client)
        return {
            "current_mrr": total_mrr,
            "previous_mrr": total_mrr,
            "has_history": False,
        }

    current_mrr = float((current_rows.data or [{}])[0].get("total_mrr", 0))
    previous_mrr = float((previous_rows.data or [{}])[0].get("total_mrr", 0)) if previous_rows.data else current_mrr

    return {
        "current_mrr": current_mrr,
        "previous_mrr": previous_mrr,
        "has_history": True,
    }
