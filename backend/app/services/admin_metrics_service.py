"""Admin metrics service — computes business KPIs from existing DB tables."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone

import structlog

from app.core.entitlements import resolve_plan_key_from_price_id
from app.core.supabase_client import get_supabase_service_client
from app.schemas.admin import (
    BusinessAlert,
    EnrichedUser,
    FunnelStep,
    MetricValue,
    TrendDirection,
    UserStatus,
)


def _resolve_plan(stripe_price_id: str | None) -> str:
    """Resolve stripe_price_id to plan key string."""
    if not stripe_price_id:
        return "free"
    resolved = resolve_plan_key_from_price_id(stripe_price_id)
    return resolved.value if resolved else "free"

logger = structlog.get_logger(__name__)

# Monthly prices for MRR (EUR). Annual subs normalized to monthly equivalent.
MRR_MONTHLY_PRICES: dict[str, float] = {
    "free": 0.0,
    "starter": 9.90,
    "gestion": 9.90,
    "pro": 19.90,
    "pilotage": 19.90,
    "fondateur": 0.0,   # one-time lifetime, excluded from recurring MRR
    "lifetime": 0.0,    # one-time, excluded from MRR
    "cabinet": 49.90,
}

ACTIVE_STATUSES = {"active", "trialing", "paid"}


def _compute_trend(
    current: float, previous: float, higher_is_better: bool = True
) -> MetricValue:
    """Compute trend direction and change percentage."""
    if previous == 0 and current == 0:
        return MetricValue(
            value=current, previous=previous, trend=TrendDirection.stable, change_pct=None
        )
    if previous == 0:
        trend = TrendDirection.up if (current > 0) == higher_is_better else TrendDirection.down
        return MetricValue(
            value=current, previous=previous, trend=trend, change_pct=None
        )

    change_pct = ((current - previous) / previous) * 100
    if current == previous:
        trend = TrendDirection.stable
    elif higher_is_better:
        trend = TrendDirection.up if current > previous else TrendDirection.down
    else:
        trend = TrendDirection.up if current < previous else TrendDirection.down

    return MetricValue(
        value=round(current, 1),
        previous=round(previous, 1),
        trend=trend,
        change_pct=round(change_pct, 1),
    )


def _count_active_scis(client, start_date: str, end_date: str | None = None) -> int:
    """Count distinct SCIs with ≥1 paid loyer in the date range."""
    query = (
        client.table("loyers")
        .select("id_bien, biens!inner(id_sci)")
        .gte("date_loyer", start_date)
        .eq("statut", "paye")
    )
    if end_date:
        query = query.lt("date_loyer", end_date)
    result = query.execute()
    sci_ids = {row.get("biens", {}).get("id_sci") for row in (result.data or []) if row.get("biens")}
    return len(sci_ids)


def _count_users_with_loyers(client, start_date: str, end_date: str | None = None) -> set[str]:
    """Return set of user_ids who have at least 1 loyer in the date range."""
    query = (
        client.table("loyers")
        .select("id_bien, biens!inner(id_sci)")
        .gte("date_loyer", start_date)
    )
    if end_date:
        query = query.lt("date_loyer", end_date)
    result = query.execute()
    sci_ids = {row.get("biens", {}).get("id_sci") for row in (result.data or []) if row.get("biens")}
    if not sci_ids:
        return set()
    associes = (
        client.table("associes")
        .select("user_id")
        .in_("id_sci", list(sci_ids))
        .execute()
    )
    return {a["user_id"] for a in (associes.data or [])}


def _get_total_users(client) -> int:
    """Count distinct users from associes table."""
    result = client.table("associes").select("user_id").execute()
    return len({a["user_id"] for a in (result.data or [])})


def _compute_mrr(client) -> float:
    """Sum monthly revenue from active subscriptions."""
    subs = client.table("subscriptions").select("stripe_price_id, status").execute()
    total = 0.0
    for s in subs.data or []:
        if s.get("status") in ACTIVE_STATUSES:
            plan = _resolve_plan(s.get("stripe_price_id"))
            total += MRR_MONTHLY_PRICES.get(plan, 0.0)
    return round(total, 2)


def compute_hero_metrics() -> dict:
    """Compute the 5 hero KPIs with trend comparison."""
    from app.services.mrr_snapshot_service import get_mrr_trend

    client = get_supabase_service_client()
    now = datetime.now(timezone.utc)
    d30 = (now - timedelta(days=30)).date().isoformat()
    d60 = (now - timedelta(days=60)).date().isoformat()
    d90 = (now - timedelta(days=90)).date().isoformat()

    # North Star: active SCIs in last 30d vs previous 30d
    ns_current = _count_active_scis(client, d30)
    ns_previous = _count_active_scis(client, d60, d30)

    # MRR: use snapshot-based trend for real historical comparison
    mrr_trend = get_mrr_trend(days=30)
    mrr_current = mrr_trend["current_mrr"]
    mrr_previous = mrr_trend["previous_mrr"]

    # Activation rate
    total_users = _get_total_users(client)
    users_with_loyers = _count_users_with_loyers(client, "2000-01-01")
    activation_current = (len(users_with_loyers) / total_users * 100) if total_users > 0 else 0

    # Previous activation (approximate: no historical user count)
    activation_previous = activation_current

    # Churn 30d
    active_m1 = _count_users_with_loyers(client, d60, d30)
    active_m0 = _count_users_with_loyers(client, d30)
    churned = active_m1 - active_m0  # users in M-1 not in M0
    churn_current = (len(churned) / len(active_m1) * 100) if active_m1 else 0

    active_m2 = _count_users_with_loyers(client, d90, d60)
    churned_prev = active_m2 - active_m1
    churn_previous = (len(churned_prev) / len(active_m2) * 100) if active_m2 else 0

    # Conversion free → paid
    subs = client.table("subscriptions").select("user_id, status, stripe_price_id").execute()
    paid_users = {
        s["user_id"]
        for s in (subs.data or [])
        if s.get("status") in ACTIVE_STATUSES and _resolve_plan(s.get("stripe_price_id")) != "free"
    }
    conversion_current = (len(paid_users) / total_users * 100) if total_users > 0 else 0
    conversion_previous = conversion_current  # simplified

    return {
        "north_star": _compute_trend(ns_current, ns_previous, higher_is_better=True).model_dump(),
        "mrr": _compute_trend(mrr_current, mrr_previous, higher_is_better=True).model_dump(),
        "activation_rate": _compute_trend(activation_current, activation_previous, higher_is_better=True).model_dump(),
        "churn_30d": _compute_trend(churn_current, churn_previous, higher_is_better=False).model_dump(),
        "conversion_rate": _compute_trend(conversion_current, conversion_previous, higher_is_better=True).model_dump(),
    }


def compute_business_alerts() -> dict:
    """Generate business alerts based on metric thresholds."""
    metrics = compute_hero_metrics()
    alerts: list[dict] = []

    # MRR declining check
    mrr = metrics["mrr"]
    if mrr["trend"] == "down":
        alerts.append(
            BusinessAlert(
                type="mrr_declining",
                severity="high",
                message="MRR en baisse",
                detail=f"{mrr['previous']} EUR \u2192 {mrr['value']} EUR",
                tooltip="Verifie si des utilisateurs ont downgrade ou churne recemment.",
            ).model_dump()
        )

    # Low activation
    activation = metrics["activation_rate"]
    if activation["value"] < 30:
        alerts.append(
            BusinessAlert(
                type="low_activation",
                severity="medium",
                message=f"Taux d'activation faible : {activation['value']}%",
                detail="Moins de 30% des inscrits ont enregistre un loyer",
                tooltip="Simplifie le parcours d'onboarding ou ajoute des guides in-app.",
            ).model_dump()
        )

    # High churn
    churn = metrics["churn_30d"]
    if churn["value"] > 5:
        alerts.append(
            BusinessAlert(
                type="high_churn",
                severity="medium",
                message=f"Churn eleve : {churn['value']}%",
                detail="Plus de 5% des utilisateurs actifs perdus ce mois",
                tooltip="Contacte les utilisateurs perdus pour comprendre pourquoi ils partent.",
            ).model_dump()
        )

    # No signups in 7 days
    client = get_supabase_service_client()
    d7 = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    try:
        recent_users = client.auth.admin.list_users()
        recent_users_list = recent_users if isinstance(recent_users, list) else []
        new_in_7d = [
            u
            for u in recent_users_list
            if str(getattr(u, "created_at", "")) >= d7
        ]
        if len(new_in_7d) == 0:
            alerts.append(
                BusinessAlert(
                    type="no_signups",
                    severity="medium",
                    message="Aucune inscription depuis 7 jours",
                    detail="0 nouvel utilisateur cette semaine",
                    tooltip="Verifie tes canaux d'acquisition et ta landing page.",
                ).model_dump()
            )
    except Exception:
        logger.warning("admin_alerts_signup_check_failed")

    return {"alerts": alerts}


def compute_activation_funnel() -> dict:
    """Compute the 5-step activation funnel."""
    client = get_supabase_service_client()

    # Step 1: Total registered users
    associes = client.table("associes").select("user_id").execute()
    all_users = {a["user_id"] for a in (associes.data or [])}
    total = len(all_users)

    # Step 2: Onboarding completed (users with subscription row + onboarding_completed)
    subs = client.table("subscriptions").select("user_id, onboarding_completed, status, stripe_price_id").execute()
    subs_data = subs.data or []
    onboarded = {s["user_id"] for s in subs_data if s.get("onboarding_completed")}

    # Step 3: Users with ≥1 bien
    biens = client.table("biens").select("id, id_sci").execute()
    biens_data = biens.data or []
    sci_with_biens = {b["id_sci"] for b in biens_data}
    users_with_biens: set[str] = set()
    if sci_with_biens:
        assoc_with_biens = client.table("associes").select("user_id").in_("id_sci", list(sci_with_biens)).execute()
        users_with_biens = {a["user_id"] for a in (assoc_with_biens.data or [])} & all_users

    # Step 4: Users with ≥1 loyer
    users_with_loyers = _count_users_with_loyers(client, "2000-01-01") & all_users

    # Step 5: Paid users
    paid = {
        s["user_id"]
        for s in subs_data
        if s.get("status") in ACTIVE_STATUSES and _resolve_plan(s.get("stripe_price_id")) != "free"
    } & all_users

    counts = [total, len(onboarded), len(users_with_biens), len(users_with_loyers), len(paid)]
    labels = ["Inscrits", "Onboarding complete", "1er bien cree", "1er loyer enregistre", "Passe en paid"]

    steps = []
    for i, (label, count) in enumerate(zip(labels, counts)):
        rate = (count / total * 100) if total > 0 else 0
        steps.append(FunnelStep(label=label, count=count, rate=round(rate, 1)).model_dump())

    # Bottleneck: largest absolute drop-off (0-based, first wins on tie)
    bottleneck_index = 0
    max_drop = 0.0
    for i in range(len(steps) - 1):
        drop = steps[i]["rate"] - steps[i + 1]["rate"]
        if drop > max_drop:
            max_drop = drop
            bottleneck_index = i

    return {"steps": steps, "bottleneck_index": bottleneck_index}


def compute_enriched_users(
    search: str | None = None,
    status_filter: str | None = None,
    plan_filter: str | None = None,
    sort: str = "created_at",
    page: int = 1,
    per_page: int = 50,
) -> dict:
    """Compute enriched user list with status classification."""
    client = get_supabase_service_client()
    now = datetime.now(timezone.utc)
    d30 = (now - timedelta(days=30)).date().isoformat()
    d7 = (now - timedelta(days=7)).date().isoformat()

    # 1. Fetch all auth users
    auth_users = client.auth.admin.list_users()
    auth_list = auth_users if isinstance(auth_users, list) else []

    # 2. Fetch all associes, biens, loyers (30d), subscriptions
    associes = client.table("associes").select("user_id, id_sci").execute()
    assoc_data = associes.data or []

    biens = client.table("biens").select("id, id_sci").execute()
    biens_data = biens.data or []

    loyers = client.table("loyers").select("id_bien, date_loyer, created_at, biens!inner(id_sci)").gte("date_loyer", d30).execute()
    loyers_data = loyers.data or []

    # All loyers for last_activity
    all_loyers = client.table("loyers").select("created_at, biens!inner(id_sci)").order("created_at", desc=True).execute()
    all_loyers_data = all_loyers.data or []

    subs = client.table("subscriptions").select("user_id, stripe_price_id, status, stripe_customer_id").execute()
    subs_data = subs.data or []
    subs_by_user = {s["user_id"]: s for s in subs_data}

    # Build lookup maps
    user_scis: dict[str, set[str]] = {}
    for a in assoc_data:
        user_scis.setdefault(a["user_id"], set()).add(a["id_sci"])

    sci_biens: dict[str, set[str]] = {}
    for b in biens_data:
        sci_biens.setdefault(b["id_sci"], set()).add(b["id"])

    # Loyers in 30d per SCI
    sci_loyers_30d: dict[str, int] = {}
    for l in loyers_data:
        sci_id = l.get("biens", {}).get("id_sci")
        if sci_id:
            sci_loyers_30d[sci_id] = sci_loyers_30d.get(sci_id, 0) + 1

    # Last activity per sci
    sci_last_activity: dict[str, str] = {}
    for l in all_loyers_data:
        sci_id = l.get("biens", {}).get("id_sci")
        if sci_id and sci_id not in sci_last_activity:
            sci_last_activity[sci_id] = l.get("created_at", "")

    # 3. Enrich each user
    enriched = []
    for u in auth_list:
        uid = u.id if hasattr(u, "id") else u.get("id", "")
        email = u.email if hasattr(u, "email") else u.get("email", "")
        created = str(u.created_at if hasattr(u, "created_at") else u.get("created_at", ""))

        scis = user_scis.get(uid, set())
        sci_count = len(scis)
        biens_count = sum(len(sci_biens.get(s, set())) for s in scis)
        loyers_30d = sum(sci_loyers_30d.get(s, 0) for s in scis)

        # Last activity
        last_acts = [sci_last_activity[s] for s in scis if s in sci_last_activity]
        last_activity = max(last_acts) if last_acts else None

        sub = subs_by_user.get(uid, {})
        plan_key = _resolve_plan(sub.get("stripe_price_id"))
        is_active = sub.get("status", "") in ACTIVE_STATUSES

        # Status classification (priority order)
        # Normalize created_at to date-only string for safe comparison
        created_date = created[:10]  # "YYYY-MM-DD" from ISO datetime
        if loyers_30d >= 3:
            status = UserStatus.power_user
        elif plan_key == "free" and biens_count >= 4:
            status = UserStatus.prospect
        elif loyers_30d == 0 and created_date < d7:
            status = UserStatus.at_risk
        elif created_date >= d7:
            status = UserStatus.new
        else:
            status = UserStatus.active

        enriched.append(EnrichedUser(
            id=uid,
            email=email,
            created_at=created,
            plan_key=plan_key,
            is_active=is_active,
            sci_count=sci_count,
            biens_count=biens_count,
            loyers_30d=loyers_30d,
            last_activity=last_activity,
            status=status,
            stripe_customer_id=sub.get("stripe_customer_id"),
        ))

    # 4. Filter
    if search:
        search_lower = search.lower()
        enriched = [u for u in enriched if search_lower in u.email.lower()]
    if status_filter:
        enriched = [u for u in enriched if u.status.value == status_filter]
    if plan_filter:
        enriched = [u for u in enriched if u.plan_key == plan_filter]

    # 5. Sort
    if sort == "last_activity":
        enriched.sort(key=lambda u: u.last_activity or "", reverse=True)
    else:
        enriched.sort(key=lambda u: u.created_at, reverse=True)

    # 6. Paginate
    total = len(enriched)
    start = (page - 1) * per_page
    end = start + per_page
    page_users = enriched[start:end]

    return {
        "users": [u.model_dump() for u in page_users],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def compute_revenue_breakdown() -> dict:
    """Return MRR broken down per plan (free, gestion, pilotage, fondateur, cabinet)."""
    client = get_supabase_service_client()
    subs = client.table("subscriptions").select("stripe_price_id, status").execute()

    mrr_by_plan: dict[str, float] = defaultdict(float)
    count_by_plan: dict[str, int] = defaultdict(int)

    for s in subs.data or []:
        if s.get("status") in ACTIVE_STATUSES:
            plan = _resolve_plan(s.get("stripe_price_id"))
            monthly = MRR_MONTHLY_PRICES.get(plan, 0.0)
            mrr_by_plan[plan] += monthly
            count_by_plan[plan] += 1

    total_mrr = round(sum(mrr_by_plan.values()), 2)

    plans = [
        "free", "gestion", "pilotage", "fondateur", "cabinet",
        "starter", "pro", "lifetime",  # legacy
    ]
    breakdown = []
    for plan in plans:
        mrr_val = round(mrr_by_plan.get(plan, 0.0), 2)
        count = count_by_plan.get(plan, 0)
        pct = round(mrr_val / total_mrr * 100, 1) if total_mrr > 0 else 0.0
        breakdown.append({
            "plan": plan,
            "mrr": mrr_val,
            "subscribers": count,
            "pct_of_total": pct,
        })

    return {
        "total_mrr": total_mrr,
        "breakdown": breakdown,
    }


def compute_arpu() -> dict:
    """Average Revenue Per User across all active paying subscribers."""
    client = get_supabase_service_client()
    subs = client.table("subscriptions").select("stripe_price_id, status").execute()

    total_mrr = 0.0
    paying_count = 0

    for s in subs.data or []:
        if s.get("status") in ACTIVE_STATUSES:
            plan = _resolve_plan(s.get("stripe_price_id"))
            monthly = MRR_MONTHLY_PRICES.get(plan, 0.0)
            if monthly > 0:
                total_mrr += monthly
                paying_count += 1

    arpu = round(total_mrr / paying_count, 2) if paying_count > 0 else 0.0

    return {
        "arpu": arpu,
        "total_mrr": round(total_mrr, 2),
        "paying_subscribers": paying_count,
    }


def compute_cohort_retention(months: int = 6) -> dict:
    """
    Monthly cohort retention table.
    For each cohort month (signup month), computes what % of users were
    still active (had ≥1 loyer) in month+1, month+2, … up to `months` intervals.
    """
    client = get_supabase_service_client()
    now = datetime.now(timezone.utc)

    # Fetch all auth users with their creation dates
    auth_users = client.auth.admin.list_users()
    auth_list = auth_users if isinstance(auth_users, list) else []

    # Group users by cohort month (YYYY-MM)
    cohort_users: dict[str, list[str]] = defaultdict(list)
    for u in auth_list:
        uid = u.id if hasattr(u, "id") else u.get("id", "")
        created = str(u.created_at if hasattr(u, "created_at") else u.get("created_at", ""))
        if len(created) >= 7:
            cohort_month = created[:7]  # "YYYY-MM"
            cohort_users[cohort_month].append(uid)

    # Fetch associes to map user_id → set of sci_ids
    associes = client.table("associes").select("user_id, id_sci").execute()
    user_scis: dict[str, set[str]] = defaultdict(set)
    for a in associes.data or []:
        user_scis[a["user_id"]].add(a["id_sci"])

    # Fetch all loyers with dates to determine user activity per month
    all_loyers = (
        client.table("loyers")
        .select("date_loyer, biens!inner(id_sci)")
        .execute()
    )

    # Build: sci_id → set of active months ("YYYY-MM")
    sci_active_months: dict[str, set[str]] = defaultdict(set)
    for l in all_loyers.data or []:
        sci_id = l.get("biens", {}).get("id_sci")
        date_loyer = l.get("date_loyer", "")
        if sci_id and len(date_loyer) >= 7:
            sci_active_months[sci_id].add(date_loyer[:7])

    # Build: user_id → set of active months
    def user_active_months(uid: str) -> set[str]:
        scis = user_scis.get(uid, set())
        active: set[str] = set()
        for sci in scis:
            active |= sci_active_months.get(sci, set())
        return active

    # Build cohort table
    # Only include cohort months within the last `months` months
    cohort_table = []
    sorted_cohorts = sorted(cohort_users.keys(), reverse=True)[:months]

    for cohort_month in sorted(sorted_cohorts):
        users = cohort_users[cohort_month]
        cohort_size = len(users)
        if cohort_size == 0:
            continue

        retention_row: dict = {
            "cohort": cohort_month,
            "size": cohort_size,
            "retention": {},
        }

        # Compute year/month from cohort_month
        try:
            cy, cm = int(cohort_month[:4]), int(cohort_month[5:7])
        except ValueError:
            continue

        for interval in range(0, months + 1):
            # Target month = cohort_month + interval months
            tm = cm + interval
            ty = cy + (tm - 1) // 12
            tm = ((tm - 1) % 12) + 1
            target_month = f"{ty:04d}-{tm:02d}"

            # Don't compute retention for future months
            target_dt = datetime(ty, tm, 1, tzinfo=timezone.utc)
            if target_dt > now:
                break

            active_in_month = sum(
                1 for uid in users if target_month in user_active_months(uid)
            )
            rate = round(active_in_month / cohort_size * 100, 1)
            retention_row["retention"][f"month_{interval}"] = {
                "active": active_in_month,
                "rate": rate,
            }

        cohort_table.append(retention_row)

    return {
        "cohorts": cohort_table,
        "months_tracked": months,
    }
