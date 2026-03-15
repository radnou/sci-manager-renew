# Admin Dashboard v2 Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the basic admin panel with a business cockpit featuring 5 hero KPIs (North Star, MRR, activation, churn, conversion), business alerts, activation funnel, and enriched user list with educational tooltips.

**Architecture:** Backend service layer (`admin_metrics_service.py`) computes all metrics from existing DB tables via service client (bypass RLS). New Pydantic schemas enforce response contracts. Frontend replaces current pages with 4 new Svelte components following existing sci-page-shell / DashboardKpis patterns.

**Tech Stack:** FastAPI + Pydantic (backend), SvelteKit 5 + Tailwind CSS 4 + lucide-svelte (frontend), pytest (backend tests), Vitest (frontend tests)

**Spec:** `docs/superpowers/specs/2026-03-15-admin-dashboard-v2-design.md`

---

## File Structure

### New files
| File | Responsibility |
|------|---------------|
| `backend/app/schemas/admin.py` | Pydantic models: MetricValue, HeroMetrics, BusinessAlert, FunnelStep, EnrichedUser, etc. |
| `backend/app/services/admin_metrics_service.py` | All metric calculations: hero KPIs, alerts, funnel, enriched users |
| `backend/tests/test_admin_metrics.py` | Unit tests for admin_metrics_service |
| `backend/tests/test_admin_api.py` | API integration tests for admin endpoints |
| `frontend/src/lib/components/admin/AdminHeroKpis.svelte` | 5 KPI cards with subtitles + tooltips + trends |
| `frontend/src/lib/components/admin/AdminAlerts.svelte` | Business alerts with severity colors + helper tooltips |
| `frontend/src/lib/components/admin/AdminFunnel.svelte` | Horizontal activation funnel bars with bottleneck highlight |
| `frontend/src/lib/components/admin/AdminUserStatusBadge.svelte` | Colored badge for user status (power_user/prospect/at_risk/new/active) |

### Modified files
| File | Changes |
|------|---------|
| `backend/app/api/v1/admin.py` | Replace 4 endpoints → metrics, alerts, funnel, enhanced users |
| `frontend/src/routes/(app)/admin/+layout.svelte` | Auth check → `/admin/metrics` instead of `/admin/stats` |
| `frontend/src/routes/(app)/admin/+page.svelte` | Full rewrite: KPIs + alerts + funnel sections |
| `frontend/src/routes/(app)/admin/users/+page.svelte` | Enriched table + filters + status badges |
| `frontend/src/lib/api.ts` | Add 4 typed admin API functions |

---

## Chunk 1: Backend Schemas + Service Layer

### Task 1: Pydantic admin schemas

**Files:**
- Create: `backend/app/schemas/admin.py`

- [ ] **Step 1: Create admin schemas file**

```python
"""Pydantic schemas for admin dashboard endpoints."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel


class TrendDirection(str, Enum):
    up = "up"
    down = "down"
    stable = "stable"


class MetricValue(BaseModel):
    value: float
    previous: float
    trend: TrendDirection
    change_pct: float | None = None  # None when previous == 0


class HeroMetrics(BaseModel):
    north_star: MetricValue
    mrr: MetricValue
    activation_rate: MetricValue
    churn_30d: MetricValue
    conversion_rate: MetricValue


class BusinessAlert(BaseModel):
    type: str
    severity: Literal["high", "medium", "info"]
    message: str
    detail: str
    tooltip: str


class BusinessAlerts(BaseModel):
    alerts: list[BusinessAlert]


class FunnelStep(BaseModel):
    label: str
    count: int
    rate: float


class ActivationFunnel(BaseModel):
    steps: list[FunnelStep]
    bottleneck_index: int


class UserStatus(str, Enum):
    power_user = "power_user"
    prospect = "prospect"
    at_risk = "at_risk"
    new = "new"
    active = "active"


class EnrichedUser(BaseModel):
    id: str
    email: str
    created_at: str
    plan_key: str
    is_active: bool
    sci_count: int
    biens_count: int
    loyers_30d: int
    last_activity: str | None = None
    status: UserStatus
    stripe_customer_id: str | None = None


class EnrichedUserList(BaseModel):
    users: list[EnrichedUser]
    total: int
    page: int
    per_page: int
```

- [ ] **Step 2: Verify schemas import cleanly**

Run: `cd backend && python -c "from app.schemas.admin import HeroMetrics, EnrichedUserList; print('OK')"`
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/schemas/admin.py
git commit -m "feat(admin): add Pydantic schemas for admin dashboard v2"
```

---

### Task 2: Admin metrics service — hero KPIs

**Files:**
- Create: `backend/app/services/admin_metrics_service.py`
- Create: `backend/tests/test_admin_metrics.py`

- [ ] **Step 1: Write failing tests for `compute_hero_metrics`**

```python
"""Tests for admin metrics service."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.services.admin_metrics_service import (
    compute_hero_metrics,
    compute_business_alerts,
    compute_activation_funnel,
    compute_enriched_users,
    _compute_trend,
)


class TestComputeTrend:
    def test_trend_up(self):
        result = _compute_trend(current=30, previous=20, higher_is_better=True)
        assert result.value == 30
        assert result.previous == 20
        assert result.trend.value == "up"
        assert result.change_pct == pytest.approx(50.0)

    def test_trend_down(self):
        result = _compute_trend(current=10, previous=20, higher_is_better=True)
        assert result.trend.value == "down"
        assert result.change_pct == pytest.approx(-50.0)

    def test_trend_stable(self):
        result = _compute_trend(current=20, previous=20, higher_is_better=True)
        assert result.trend.value == "stable"
        assert result.change_pct == pytest.approx(0.0)

    def test_previous_zero_returns_none_change_pct(self):
        result = _compute_trend(current=5, previous=0, higher_is_better=True)
        assert result.change_pct is None
        assert result.trend.value == "up"

    def test_both_zero(self):
        result = _compute_trend(current=0, previous=0, higher_is_better=True)
        assert result.trend.value == "stable"
        assert result.change_pct is None

    def test_churn_lower_is_better(self):
        """For churn, a decrease is 'up' (good)."""
        result = _compute_trend(current=3, previous=5, higher_is_better=False)
        assert result.trend.value == "up"  # good direction

    def test_churn_increase_is_down(self):
        result = _compute_trend(current=7, previous=5, higher_is_better=False)
        assert result.trend.value == "down"  # bad direction


class TestComputeHeroMetrics:
    @patch("app.services.admin_metrics_service.get_supabase_service_client")
    def test_returns_hero_metrics_structure(self, mock_get_client):
        client = MagicMock()
        mock_get_client.return_value = client
        now = datetime.now(timezone.utc)
        d30 = (now - timedelta(days=30)).isoformat()
        d60 = (now - timedelta(days=60)).isoformat()

        # Mock: 2 distinct SCIs with loyers in last 30d
        client.table.return_value.select.return_value.gte.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[
                {"id_bien": "b1", "biens": {"id_sci": "s1"}},
                {"id_bien": "b2", "biens": {"id_sci": "s2"}},
            ]
        )
        # Mock associes
        client.table.return_value.select.return_value.execute.return_value = MagicMock(
            data=[{"user_id": "u1"}, {"user_id": "u2"}, {"user_id": "u3"}],
            count=3,
        )

        result = compute_hero_metrics()
        assert "north_star" in result
        assert "mrr" in result
        assert "activation_rate" in result
        assert "churn_30d" in result
        assert "conversion_rate" in result

    @patch("app.services.admin_metrics_service.get_supabase_service_client")
    def test_zero_users_no_crash(self, mock_get_client):
        client = MagicMock()
        mock_get_client.return_value = client
        client.table.return_value.select.return_value.execute.return_value = MagicMock(data=[], count=0)
        client.table.return_value.select.return_value.gte.return_value.eq.return_value.execute.return_value = MagicMock(data=[])
        client.table.return_value.select.return_value.in_.return_value.execute.return_value = MagicMock(data=[])
        client.auth.admin.list_users.return_value = []

        result = compute_hero_metrics()
        assert result["north_star"]["value"] == 0
        assert result["activation_rate"]["value"] == 0
        assert result["churn_30d"]["value"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && PYTHONPATH=. pytest tests/test_admin_metrics.py -v --no-header 2>&1 | head -30`
Expected: FAIL (module not found)

- [ ] **Step 3: Implement `admin_metrics_service.py`**

```python
"""Admin metrics service — computes business KPIs from existing DB tables."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import structlog

from app.core.supabase_client import get_supabase_service_client
from app.schemas.admin import (
    BusinessAlert,
    EnrichedUser,
    FunnelStep,
    MetricValue,
    TrendDirection,
    UserStatus,
)

logger = structlog.get_logger(__name__)

# Monthly prices for MRR (EUR). Annual subs normalized to monthly equivalent.
MRR_MONTHLY_PRICES: dict[str, float] = {
    "free": 0.0,
    "starter": 9.90,
    "pro": 19.90,
    "lifetime": 0.0,  # one-time, excluded from MRR
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
    from app.core.entitlements import resolve_plan_key_from_price_id

    subs = client.table("subscriptions").select("plan_key, stripe_price_id, status").execute()
    total = 0.0
    for s in subs.data or []:
        if s.get("status") in ACTIVE_STATUSES:
            # Prefer plan_key column, fallback to resolving from stripe_price_id
            plan = s.get("plan_key")
            if not plan:
                resolved = resolve_plan_key_from_price_id(s.get("stripe_price_id"))
                plan = resolved.value if resolved else "free"
            total += MRR_MONTHLY_PRICES.get(plan, 0.0)
    return round(total, 2)


def compute_hero_metrics() -> dict:
    """Compute the 5 hero KPIs with trend comparison."""
    client = get_supabase_service_client()
    now = datetime.now(timezone.utc)
    d30 = (now - timedelta(days=30)).date().isoformat()
    d60 = (now - timedelta(days=60)).date().isoformat()
    d90 = (now - timedelta(days=90)).date().isoformat()

    # North Star: active SCIs in last 30d vs previous 30d
    ns_current = _count_active_scis(client, d30)
    ns_previous = _count_active_scis(client, d60, d30)

    # MRR: current snapshot only — no historical snapshots stored yet.
    # Previous = current, so trend will always be "stable" and mrr_declining alert
    # will never fire. This is a known limitation for early stage.
    # TODO: Store weekly MRR snapshots in a new table to enable trend detection.
    mrr_current = _compute_mrr(client)
    mrr_previous = mrr_current

    # Activation rate
    total_users = _get_total_users(client)
    users_with_loyers = _count_users_with_loyers(client, "2000-01-01")
    activation_current = (len(users_with_loyers) / total_users * 100) if total_users > 0 else 0

    # Previous activation (approximate: users with loyers before 30d ago / total users 30d ago)
    activation_previous = activation_current  # simplified: no historical user count

    # Churn 30d
    active_m1 = _count_users_with_loyers(client, d60, d30)
    active_m0 = _count_users_with_loyers(client, d30)
    churned = active_m1 - active_m0  # users in M-1 not in M0
    churn_current = (len(churned) / len(active_m1) * 100) if active_m1 else 0

    active_m2 = _count_users_with_loyers(client, d90, d60)
    churned_prev = active_m2 - active_m1
    churn_previous = (len(churned_prev) / len(active_m2) * 100) if active_m2 else 0

    # Conversion free → paid
    subs = client.table("subscriptions").select("user_id, status, plan_key").execute()
    paid_users = {
        s["user_id"]
        for s in (subs.data or [])
        if s.get("status") in ACTIVE_STATUSES and s.get("plan_key") != "free"
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

    # MRR declining check (simplified: check if trend is down)
    mrr = metrics["mrr"]
    if mrr["trend"] == "down":
        alerts.append(
            BusinessAlert(
                type="mrr_declining",
                severity="high",
                message="MRR en baisse",
                detail=f"{mrr['previous']} EUR → {mrr['value']} EUR",
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
    subs = client.table("subscriptions").select("user_id, onboarding_completed, status, plan_key").execute()
    subs_data = subs.data or []
    onboarded = {s["user_id"] for s in subs_data if s.get("onboarding_completed")}

    # Step 3: Users with ≥1 bien
    biens = client.table("biens").select("id_sci").execute()
    sci_with_biens = {b["id_sci"] for b in (biens.data or [])}
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
        if s.get("status") in ACTIVE_STATUSES and s.get("plan_key") != "free"
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

    subs = client.table("subscriptions").select("user_id, plan_key, status, stripe_customer_id").execute()
    subs_data = subs.data or []
    subs_by_user = {s["user_id"]: s for s in subs_data}

    # Build lookup maps
    user_scis: dict[str, set[str]] = {}
    for a in assoc_data:
        user_scis.setdefault(a["user_id"], set()).add(a["id_sci"])

    sci_biens: dict[str, set[str]] = {}
    for b in biens_data:
        sci_biens.setdefault(b["id_sci"], set()).add(b["id"])

    # Loyers in 30d per user (via sci)
    bien_sci_map = {b["id"]: b["id_sci"] for b in biens_data}
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
        plan_key = sub.get("plan_key", "free")
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
```

- [ ] **Step 4: Run tests**

Run: `cd backend && PYTHONPATH=. pytest tests/test_admin_metrics.py -v --no-header 2>&1 | tail -20`
Expected: All tests PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/admin_metrics_service.py backend/tests/test_admin_metrics.py
git commit -m "feat(admin): add admin metrics service with hero KPIs, alerts, funnel, enriched users"
```

---

### Task 3: Replace backend admin API endpoints

**Files:**
- Modify: `backend/app/api/v1/admin.py` (full rewrite, lines 1-124)
- Create: `backend/tests/test_admin_api.py`

- [ ] **Step 1: Write API integration tests**

```python
"""API tests for admin endpoints."""

from unittest.mock import patch, MagicMock

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _mock_admin(user_id="admin-123"):
    """Override get_current_admin dependency."""
    from app.core.security import get_current_admin
    app.dependency_overrides[get_current_admin] = lambda: user_id
    return user_id


def _clear_overrides():
    app.dependency_overrides.clear()


class TestAdminMetrics:
    def setup_method(self):
        _mock_admin()

    def teardown_method(self):
        _clear_overrides()

    @patch("app.api.v1.admin.compute_hero_metrics")
    def test_get_metrics(self, mock_compute):
        mock_compute.return_value = {
            "north_star": {"value": 5, "previous": 3, "trend": "up", "change_pct": 66.7},
            "mrr": {"value": 99.0, "previous": 99.0, "trend": "stable", "change_pct": 0.0},
            "activation_rate": {"value": 25.0, "previous": 25.0, "trend": "stable", "change_pct": 0.0},
            "churn_30d": {"value": 2.0, "previous": 3.0, "trend": "up", "change_pct": -33.3},
            "conversion_rate": {"value": 10.0, "previous": 10.0, "trend": "stable", "change_pct": 0.0},
        }
        resp = client.get("/api/v1/admin/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "north_star" in data
        assert data["north_star"]["value"] == 5

    @patch("app.api.v1.admin.compute_business_alerts")
    def test_get_alerts(self, mock_compute):
        mock_compute.return_value = {"alerts": []}
        resp = client.get("/api/v1/admin/alerts")
        assert resp.status_code == 200
        assert resp.json()["alerts"] == []

    @patch("app.api.v1.admin.compute_activation_funnel")
    def test_get_funnel(self, mock_compute):
        mock_compute.return_value = {
            "steps": [{"label": "Inscrits", "count": 10, "rate": 100.0}],
            "bottleneck_index": 0,
        }
        resp = client.get("/api/v1/admin/funnel")
        assert resp.status_code == 200
        assert len(resp.json()["steps"]) == 1

    @patch("app.api.v1.admin.compute_enriched_users")
    def test_get_users(self, mock_compute):
        mock_compute.return_value = {"users": [], "total": 0, "page": 1, "per_page": 50}
        resp = client.get("/api/v1/admin/users?page=1&per_page=10")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0


class TestAdminAuth:
    def test_metrics_requires_admin(self):
        _clear_overrides()
        resp = client.get("/api/v1/admin/metrics")
        assert resp.status_code in (401, 403)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && PYTHONPATH=. pytest tests/test_admin_api.py -v --no-header 2>&1 | tail -20`
Expected: FAIL (endpoints don't exist yet)

- [ ] **Step 3: Rewrite admin.py**

Replace the entire file `backend/app/api/v1/admin.py`:

```python
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
```

- [ ] **Step 4: Run all admin tests**

Run: `cd backend && PYTHONPATH=. pytest tests/test_admin_api.py tests/test_admin_metrics.py -v --no-header 2>&1 | tail -20`
Expected: All PASS

- [ ] **Step 5: Run full backend test suite to check no regressions**

Run: `cd backend && PYTHONPATH=. pytest --tb=short -q 2>&1 | tail -5`
Expected: All pass, no regressions

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/v1/admin.py backend/tests/test_admin_api.py
git commit -m "feat(admin): replace admin endpoints with metrics, alerts, funnel, enriched users"
```

---

## Chunk 2: Frontend Components

### Task 4: Admin API client functions

**Files:**
- Modify: `frontend/src/lib/api.ts` (add functions at end of file)

- [ ] **Step 1: Add admin API functions to api.ts**

Add these functions at the end of `frontend/src/lib/api.ts`:

```typescript
// ── Admin ──────────────────────────────────────────
export function fetchAdminMetrics() {
	return apiFetch<{
		north_star: { value: number; previous: number; trend: string; change_pct: number | null };
		mrr: { value: number; previous: number; trend: string; change_pct: number | null };
		activation_rate: { value: number; previous: number; trend: string; change_pct: number | null };
		churn_30d: { value: number; previous: number; trend: string; change_pct: number | null };
		conversion_rate: { value: number; previous: number; trend: string; change_pct: number | null };
	}>('/api/v1/admin/metrics');
}

export function fetchAdminAlerts() {
	return apiFetch<{
		alerts: Array<{
			type: string;
			severity: 'high' | 'medium';
			message: string;
			detail: string;
			tooltip: string;
		}>;
	}>('/api/v1/admin/alerts');
}

export function fetchAdminFunnel() {
	return apiFetch<{
		steps: Array<{ label: string; count: number; rate: number }>;
		bottleneck_index: number;
	}>('/api/v1/admin/funnel');
}

export function fetchAdminUsers(params: {
	search?: string;
	status?: string;
	plan?: string;
	sort?: string;
	page?: number;
	per_page?: number;
} = {}) {
	const searchParams = new URLSearchParams();
	if (params.search) searchParams.set('search', params.search);
	if (params.status) searchParams.set('status', params.status);
	if (params.plan) searchParams.set('plan', params.plan);
	if (params.sort) searchParams.set('sort', params.sort);
	if (params.page) searchParams.set('page', String(params.page));
	if (params.per_page) searchParams.set('per_page', String(params.per_page));
	const qs = searchParams.toString();
	return apiFetch<{
		users: Array<{
			id: string;
			email: string;
			created_at: string;
			plan_key: string;
			is_active: boolean;
			sci_count: number;
			biens_count: number;
			loyers_30d: number;
			last_activity: string | null;
			status: string;
			stripe_customer_id: string | null;
		}>;
		total: number;
		page: number;
		per_page: number;
	}>(`/api/v1/admin/users${qs ? `?${qs}` : ''}`);
}
```

- [ ] **Step 2: Verify frontend compiles**

Run: `cd frontend && pnpm run check 2>&1 | tail -10`
Expected: 0 errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/api.ts
git commit -m "feat(admin): add typed admin API client functions"
```

---

### Task 5: AdminHeroKpis component

**Files:**
- Create: `frontend/src/lib/components/admin/AdminHeroKpis.svelte`

- [ ] **Step 1: Create the component**

```svelte
<script lang="ts">
	import { Target, Euro, Zap, UserMinus, ArrowUpRight, TrendingUp, TrendingDown, Minus, Info } from 'lucide-svelte';

	type MetricValue = {
		value: number;
		previous: number;
		trend: string;
		change_pct: number | null;
	};

	type Props = {
		metrics: {
			north_star: MetricValue;
			mrr: MetricValue;
			activation_rate: MetricValue;
			churn_30d: MetricValue;
			conversion_rate: MetricValue;
		};
	};

	let { metrics }: Props = $props();

	const kpis = $derived([
		{
			key: 'north_star',
			label: 'North Star',
			subtitle: 'SCIs actives sur 30j',
			tooltip:
				'Combien de SCI ont enregistre ≥1 loyer paye ces 30 derniers jours. C\'est ta metrique #1 — si elle monte, ton produit cree de la valeur. Si elle stagne, concentre-toi sur l\'activation.',
			icon: Target,
			color: 'indigo',
			format: 'integer',
			positiveUp: true,
			data: metrics.north_star,
		},
		{
			key: 'mrr',
			label: 'MRR',
			subtitle: 'Revenu mensuel recurrent',
			tooltip:
				'Somme des abonnements actifs ce mois (hors lifetime). C\'est ce qui paie tes serveurs. Surveille la tendance : 2 semaines de baisse = signal d\'alerte.',
			icon: Euro,
			color: 'emerald',
			format: 'currency',
			positiveUp: true,
			data: metrics.mrr,
		},
		{
			key: 'activation_rate',
			label: 'Activation',
			subtitle: 'Inscrits → 1er loyer',
			tooltip:
				'% d\'utilisateurs inscrits qui ont enregistre au moins 1 loyer. En dessous de 30%, ton onboarding a un probleme — simplifie le parcours.',
			icon: Zap,
			color: 'sky',
			format: 'percentage',
			positiveUp: true,
			data: metrics.activation_rate,
		},
		{
			key: 'churn_30d',
			label: 'Churn 30j',
			subtitle: 'Users perdus ce mois',
			tooltip:
				'% d\'utilisateurs actifs le mois dernier qui ne le sont plus ce mois-ci. Au-dessus de 5%/mois, il y a une fuite a colmater — contacte les users perdus.',
			icon: UserMinus,
			color: 'rose',
			format: 'percentage',
			positiveUp: false,
			data: metrics.churn_30d,
		},
		{
			key: 'conversion_rate',
			label: 'Conversion',
			subtitle: 'Free vers payant',
			tooltip:
				'% d\'utilisateurs gratuits passes a un plan payant. Bon indicateur de la valeur percue et du positionnement de ton paywall.',
			icon: ArrowUpRight,
			color: 'amber',
			format: 'percentage',
			positiveUp: true,
			data: metrics.conversion_rate,
		},
	]);

	function formatValue(value: number, format: string): string {
		if (format === 'currency') return `${value.toLocaleString('fr-FR')} €`;
		if (format === 'percentage') return `${value}%`;
		return String(Math.round(value));
	}

	const colorMap: Record<string, { bg: string; icon: string; darkBg: string }> = {
		indigo: { bg: 'bg-indigo-50', icon: 'text-indigo-500', darkBg: 'dark:bg-indigo-950/40' },
		emerald: { bg: 'bg-emerald-50', icon: 'text-emerald-500', darkBg: 'dark:bg-emerald-950/40' },
		sky: { bg: 'bg-sky-50', icon: 'text-sky-500', darkBg: 'dark:bg-sky-950/40' },
		rose: { bg: 'bg-rose-50', icon: 'text-rose-500', darkBg: 'dark:bg-rose-950/40' },
		amber: { bg: 'bg-amber-50', icon: 'text-amber-500', darkBg: 'dark:bg-amber-950/40' },
	};
</script>

<div class="grid gap-4 grid-cols-2 sm:grid-cols-3 lg:grid-cols-5">
	{#each kpis as kpi (kpi.key)}
		{@const c = colorMap[kpi.color]}
		{@const trendGood = kpi.data.trend === 'up'}
		{@const trendBad = kpi.data.trend === 'down'}
		<div
			class="rounded-2xl border border-slate-200 bg-white p-5 dark:border-slate-800 dark:bg-slate-950"
		>
			<div class="flex items-center justify-between">
				<div class="flex items-center gap-2">
					<div class="flex h-8 w-8 items-center justify-center rounded-lg {c.bg} {c.darkBg}">
						<kpi.icon class="h-4 w-4 {c.icon}" />
					</div>
					<p class="text-xs font-semibold tracking-wider text-slate-500 uppercase">{kpi.label}</p>
				</div>
				<button class="group relative ml-1 inline-flex cursor-help" aria-label="Info">
					<Info class="h-3.5 w-3.5 text-slate-400" />
					<div
						class="pointer-events-none absolute bottom-full right-0 z-50 mb-2 w-64 rounded-lg border border-slate-200 bg-white p-3 text-xs leading-relaxed text-slate-600 opacity-0 shadow-lg transition-opacity group-hover:opacity-100 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"
					>
						{kpi.tooltip}
					</div>
				</button>
			</div>

			<div class="mt-3 flex items-end justify-between">
				<p class="text-2xl font-bold text-slate-900 dark:text-slate-100">
					{formatValue(kpi.data.value, kpi.format)}
				</p>
				{#if kpi.data.change_pct != null}
					<div class="flex items-center gap-0.5 text-xs font-semibold {trendGood ? 'text-emerald-600' : trendBad ? 'text-rose-600' : 'text-slate-400'}">
						{#if trendGood}
							<TrendingUp class="h-3.5 w-3.5" />
						{:else if trendBad}
							<TrendingDown class="h-3.5 w-3.5" />
						{:else}
							<Minus class="h-3.5 w-3.5" />
						{/if}
						{Math.abs(kpi.data.change_pct)}%
					</div>
				{:else}
					<span class="text-xs text-slate-400">—</span>
				{/if}
			</div>

			<p class="mt-1 text-xs text-slate-500 dark:text-slate-400">{kpi.subtitle}</p>
		</div>
	{/each}
</div>
```

- [ ] **Step 2: Verify frontend compiles**

Run: `cd frontend && pnpm run check 2>&1 | tail -10`
Expected: 0 errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/components/admin/AdminHeroKpis.svelte
git commit -m "feat(admin): add AdminHeroKpis component with tooltips and trends"
```

---

### Task 6: AdminAlerts component

**Files:**
- Create: `frontend/src/lib/components/admin/AdminAlerts.svelte`

- [ ] **Step 1: Create the component**

```svelte
<script lang="ts">
	import { CircleAlert, TriangleAlert, CircleCheck } from 'lucide-svelte';

	type Alert = {
		type: string;
		severity: 'high' | 'medium';
		message: string;
		detail: string;
		tooltip: string;
	};

	type Props = { alerts: Alert[] };
	let { alerts }: Props = $props();

	const severityConfig: Record<string, { border: string; bg: string; icon: typeof CircleAlert; iconColor: string }> = {
		high: {
			border: 'border-rose-200 dark:border-rose-800',
			bg: 'bg-rose-50 dark:bg-rose-950/30',
			icon: CircleAlert,
			iconColor: 'text-rose-500',
		},
		medium: {
			border: 'border-amber-200 dark:border-amber-800',
			bg: 'bg-amber-50 dark:bg-amber-950/30',
			icon: TriangleAlert,
			iconColor: 'text-amber-500',
		},
	};
</script>

{#if alerts.length === 0}
	<div
		class="flex items-center gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-5 py-4 dark:border-emerald-800 dark:bg-emerald-950/30"
	>
		<CircleCheck class="h-5 w-5 flex-shrink-0 text-emerald-500" />
		<p class="text-sm font-medium text-emerald-700 dark:text-emerald-300">
			Tout va bien — aucune alerte business
		</p>
	</div>
{:else}
	<div class="space-y-3">
		{#each alerts as alert (alert.type)}
			{@const config = severityConfig[alert.severity] ?? severityConfig.medium}
			<div
				class="flex items-start gap-3 rounded-xl border px-5 py-4 {config.border} {config.bg}"
			>
				<config.icon class="mt-0.5 h-5 w-5 flex-shrink-0 {config.iconColor}" />
				<div class="min-w-0 flex-1">
					<p class="text-sm font-medium text-slate-900 dark:text-slate-100">{alert.message}</p>
					<p class="mt-0.5 text-xs text-slate-600 dark:text-slate-400">{alert.detail}</p>
					<p class="mt-1 text-xs italic text-slate-500 dark:text-slate-500">{alert.tooltip}</p>
				</div>
			</div>
		{/each}
	</div>
{/if}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/components/admin/AdminAlerts.svelte
git commit -m "feat(admin): add AdminAlerts component with severity colors and tips"
```

---

### Task 7: AdminFunnel component

**Files:**
- Create: `frontend/src/lib/components/admin/AdminFunnel.svelte`

- [ ] **Step 1: Create the component**

```svelte
<script lang="ts">
	type FunnelStep = { label: string; count: number; rate: number };
	type Props = { steps: FunnelStep[]; bottleneck_index: number };
	let { steps, bottleneck_index }: Props = $props();
</script>

<div class="rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-950">
	<h2 class="text-lg font-semibold text-slate-900 dark:text-slate-100">Funnel d'activation</h2>
	<p class="mt-1 text-xs text-slate-500">Parcours des utilisateurs de l'inscription au paiement</p>

	<div class="mt-5 space-y-3">
		{#each steps as step, i (step.label)}
			{@const isBottleneck = i === bottleneck_index && steps.length > 1}
			<div class="flex items-center gap-3">
				<div class="w-44 flex-shrink-0">
					<p class="text-sm font-medium text-slate-700 dark:text-slate-300">{step.label}</p>
				</div>
				<div class="flex flex-1 items-center gap-2">
					<div class="relative h-6 flex-1 rounded-full bg-slate-100 dark:bg-slate-800">
						<div
							class="absolute inset-y-0 left-0 rounded-full transition-all {isBottleneck
								? 'bg-amber-500'
								: 'bg-sky-500'}"
							style="width: {step.rate}%"
						></div>
					</div>
					<span class="w-10 text-right text-xs font-semibold text-slate-600 dark:text-slate-400">
						{step.count}
					</span>
					<span
						class="w-12 rounded-full px-2 py-0.5 text-center text-xs font-semibold {isBottleneck
							? 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
							: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400'}"
					>
						{step.rate}%
					</span>
				</div>
				{#if isBottleneck}
					<span class="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">
						Goulot
					</span>
				{/if}
			</div>
		{/each}
	</div>
</div>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/components/admin/AdminFunnel.svelte
git commit -m "feat(admin): add AdminFunnel component with bottleneck highlight"
```

---

### Task 8: AdminUserStatusBadge component

**Files:**
- Create: `frontend/src/lib/components/admin/AdminUserStatusBadge.svelte`

- [ ] **Step 1: Create the component**

```svelte
<script lang="ts">
	type Props = { status: string };
	let { status }: Props = $props();

	const config: Record<string, { label: string; classes: string }> = {
		power_user: {
			label: 'Power user',
			classes: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
		},
		prospect: {
			label: 'Prospect chaud',
			classes: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
		},
		at_risk: {
			label: 'A risque',
			classes: 'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400',
		},
		new: {
			label: 'Nouveau',
			classes: 'bg-sky-100 text-sky-700 dark:bg-sky-900/30 dark:text-sky-400',
		},
		active: {
			label: 'Actif',
			classes: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400',
		},
	};

	const c = $derived(config[status] ?? config.active);
</script>

<span class="inline-flex rounded-full px-2.5 py-0.5 text-xs font-semibold {c.classes}">
	{c.label}
</span>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/components/admin/AdminUserStatusBadge.svelte
git commit -m "feat(admin): add AdminUserStatusBadge component"
```

---

## Chunk 3: Frontend Pages (Wiring)

### Task 9: Update admin layout auth check

**Files:**
- Modify: `frontend/src/routes/(app)/admin/+layout.svelte` (line 25)

- [ ] **Step 1: Update auth check endpoint**

In `+layout.svelte`, change line 25 from:
```typescript
await apiFetch('/api/v1/admin/stats');
```
to:
```typescript
await apiFetch('/api/v1/admin/metrics');
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/routes/(app)/admin/+layout.svelte
git commit -m "fix(admin): update layout auth check to use /metrics endpoint"
```

---

### Task 10: Rewrite admin dashboard page

**Files:**
- Modify: `frontend/src/routes/(app)/admin/+page.svelte` (full rewrite)

- [ ] **Step 1: Rewrite the admin dashboard page**

Replace the entire file:

```svelte
<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchAdminMetrics, fetchAdminAlerts, fetchAdminFunnel } from '$lib/api';
	import AdminHeroKpis from '$lib/components/admin/AdminHeroKpis.svelte';
	import AdminAlerts from '$lib/components/admin/AdminAlerts.svelte';
	import AdminFunnel from '$lib/components/admin/AdminFunnel.svelte';

	let metrics = $state<Awaited<ReturnType<typeof fetchAdminMetrics>> | null>(null);
	let alerts = $state<Awaited<ReturnType<typeof fetchAdminAlerts>> | null>(null);
	let funnel = $state<Awaited<ReturnType<typeof fetchAdminFunnel>> | null>(null);
	let loading = $state(true);
	let error = $state('');

	onMount(async () => {
		try {
			const [m, a, f] = await Promise.all([
				fetchAdminMetrics(),
				fetchAdminAlerts(),
				fetchAdminFunnel(),
			]);
			metrics = m;
			alerts = a;
			funnel = f;
		} catch (e) {
			error = 'Erreur lors du chargement des metriques';
		} finally {
			loading = false;
		}
	});
</script>

<svelte:head>
	<title>Cockpit Business | Admin | GererSCI</title>
</svelte:head>

{#if loading}
	<div class="flex items-center justify-center py-20">
		<div class="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-slate-600"></div>
	</div>
{:else if error}
	<div class="rounded-xl border border-rose-200 bg-rose-50 px-5 py-4 dark:border-rose-800 dark:bg-rose-950/30">
		<p class="text-sm text-rose-700 dark:text-rose-300">{error}</p>
	</div>
{:else}
	<div class="space-y-6">
		{#if metrics}
			<AdminHeroKpis {metrics} />
		{/if}

		{#if alerts}
			<div>
				<h2 class="mb-3 text-lg font-semibold text-slate-900 dark:text-slate-100">Alertes business</h2>
				<AdminAlerts alerts={alerts.alerts} />
			</div>
		{/if}

		{#if funnel}
			<AdminFunnel steps={funnel.steps} bottleneck_index={funnel.bottleneck_index} />
		{/if}
	</div>
{/if}
```

- [ ] **Step 2: Verify frontend compiles**

Run: `cd frontend && pnpm run check 2>&1 | tail -10`
Expected: 0 errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/routes/(app)/admin/+page.svelte
git commit -m "feat(admin): rewrite dashboard page with KPIs, alerts, funnel"
```

---

### Task 11: Rewrite admin users page

**Files:**
- Modify: `frontend/src/routes/(app)/admin/users/+page.svelte` (full rewrite)

- [ ] **Step 1: Rewrite the users page**

Replace the entire file:

```svelte
<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchAdminUsers } from '$lib/api';
	import AdminUserStatusBadge from '$lib/components/admin/AdminUserStatusBadge.svelte';

	type EnrichedUser = Awaited<ReturnType<typeof fetchAdminUsers>>['users'][number];

	let users = $state<EnrichedUser[]>([]);
	let total = $state(0);
	let page = $state(1);
	let search = $state('');
	let statusFilter = $state('');
	let planFilter = $state('');
	let sortBy = $state('created_at');
	let loading = $state(true);

	const perPage = 50;
	const totalPages = $derived(Math.ceil(total / perPage));

	async function loadUsers() {
		loading = true;
		try {
			const data = await fetchAdminUsers({
				search: search || undefined,
				status: statusFilter || undefined,
				plan: planFilter || undefined,
				sort: sortBy,
				page,
				per_page: perPage,
			});
			users = data.users;
			total = data.total;
		} catch {
			// handled by layout guard
		} finally {
			loading = false;
		}
	}

	onMount(loadUsers);

	function applyFilters() {
		page = 1;
		loadUsers();
	}

	function relativeTime(dateStr: string | null): string {
		if (!dateStr) return 'Jamais';
		const diff = Date.now() - new Date(dateStr).getTime();
		const minutes = Math.floor(diff / 60000);
		if (minutes < 1) return "a l'instant";
		if (minutes < 60) return `il y a ${minutes} min`;
		const hours = Math.floor(minutes / 60);
		if (hours < 24) return `il y a ${hours}h`;
		const days = Math.floor(hours / 24);
		if (days === 1) return 'hier';
		if (days < 30) return `il y a ${days}j`;
		const months = Math.floor(days / 30);
		return `il y a ${months} mois`;
	}

	const planBadgeClass: Record<string, string> = {
		pro: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
		lifetime: 'bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400',
		starter: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
		cabinet: 'bg-indigo-100 text-indigo-700 dark:bg-indigo-900/30 dark:text-indigo-400',
		free: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-400',
	};
</script>

<svelte:head>
	<title>Utilisateurs | Admin | GererSCI</title>
</svelte:head>

<!-- Filters -->
<div class="mb-4 flex flex-wrap items-center gap-3">
	<input
		type="text"
		placeholder="Rechercher par email..."
		bind:value={search}
		oninput={() => applyFilters()}
		class="h-9 w-64 rounded-lg border border-slate-200 bg-white px-3 text-sm placeholder:text-slate-400 focus:border-sky-500 focus:outline-none dark:border-slate-700 dark:bg-slate-900 dark:text-slate-100"
	/>
	<select
		bind:value={statusFilter}
		onchange={() => applyFilters()}
		class="h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
	>
		<option value="">Tous les statuts</option>
		<option value="power_user">Power user</option>
		<option value="prospect">Prospect chaud</option>
		<option value="at_risk">A risque</option>
		<option value="new">Nouveau</option>
		<option value="active">Actif</option>
	</select>
	<select
		bind:value={planFilter}
		onchange={() => applyFilters()}
		class="h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
	>
		<option value="">Tous les plans</option>
		<option value="free">Free</option>
		<option value="starter">Starter</option>
		<option value="pro">Pro</option>
		<option value="lifetime">Lifetime</option>
	</select>
	<select
		bind:value={sortBy}
		onchange={() => applyFilters()}
		class="h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300"
	>
		<option value="created_at">Tri: inscription</option>
		<option value="last_activity">Tri: activite</option>
	</select>
</div>

<!-- Table -->
<div class="rounded-2xl border border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-950">
	<div class="overflow-x-auto">
		<table class="w-full text-left text-sm">
			<thead>
				<tr class="border-b border-slate-200 dark:border-slate-800">
					<th class="px-4 py-3 font-semibold text-slate-600 dark:text-slate-400">Email</th>
					<th class="px-4 py-3 font-semibold text-slate-600 dark:text-slate-400">Plan</th>
					<th class="px-4 py-3 font-semibold text-slate-600 dark:text-slate-400">SCIs</th>
					<th class="px-4 py-3 font-semibold text-slate-600 dark:text-slate-400">Biens</th>
					<th class="px-4 py-3 font-semibold text-slate-600 dark:text-slate-400">Activite</th>
					<th class="px-4 py-3 font-semibold text-slate-600 dark:text-slate-400">Statut</th>
				</tr>
			</thead>
			<tbody>
				{#each users as user (user.id)}
					<tr class="border-b border-slate-100 transition-colors hover:bg-slate-50 dark:border-slate-800/50 dark:hover:bg-slate-900">
						<td class="px-4 py-3 font-medium text-slate-900 dark:text-slate-100">{user.email}</td>
						<td class="px-4 py-3">
							<span class="rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize {planBadgeClass[user.plan_key] ?? planBadgeClass.free}">
								{user.plan_key}
							</span>
						</td>
						<td class="px-4 py-3 text-slate-600 dark:text-slate-400">{user.sci_count}</td>
						<td class="px-4 py-3 text-slate-600 dark:text-slate-400">{user.biens_count}</td>
						<td class="px-4 py-3 text-slate-500">{relativeTime(user.last_activity)}</td>
						<td class="px-4 py-3">
							<AdminUserStatusBadge status={user.status} />
						</td>
					</tr>
				{:else}
					<tr>
						<td colspan="6" class="px-4 py-8 text-center text-slate-500">Aucun utilisateur trouve</td>
					</tr>
				{/each}
			</tbody>
		</table>
	</div>
</div>

<!-- Pagination -->
<div class="mt-4 flex items-center gap-2">
	<button
		class="rounded-lg bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-700 disabled:opacity-50 dark:bg-slate-800 dark:text-slate-300"
		disabled={page === 1}
		onclick={() => { page--; loadUsers(); }}
	>
		Precedent
	</button>
	<span class="px-3 py-1.5 text-sm text-slate-500">
		Page {page} / {totalPages || 1} ({total} users)
	</span>
	<button
		class="rounded-lg bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-700 disabled:opacity-50 dark:bg-slate-800 dark:text-slate-300"
		disabled={page >= totalPages}
		onclick={() => { page++; loadUsers(); }}
	>
		Suivant
	</button>
</div>
```

- [ ] **Step 2: Verify frontend compiles**

Run: `cd frontend && pnpm run check 2>&1 | tail -10`
Expected: 0 errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/routes/(app)/admin/users/+page.svelte
git commit -m "feat(admin): rewrite users page with filters, enriched data, status badges"
```

---

### Task 12: Final verification

- [ ] **Step 1: Run full backend tests**

Run: `cd backend && PYTHONPATH=. pytest --tb=short -q 2>&1 | tail -5`
Expected: All pass

- [ ] **Step 2: Run frontend check**

Run: `cd frontend && pnpm run check 2>&1 | tail -10`
Expected: 0 errors, 0 warnings

- [ ] **Step 3: Run frontend lint**

Run: `cd frontend && pnpm run lint 2>&1 | tail -10`
Expected: 0 errors

- [ ] **Step 4: Start dev servers and verify manually**

Run: `cd backend && uvicorn app.main:app --port 8000` (in one terminal)
Run: `cd frontend && pnpm run dev` (in another terminal)
Navigate to `http://localhost:5173/admin` — verify dashboard loads with KPIs, alerts, funnel.
Navigate to `http://localhost:5173/admin/users` — verify filters and status badges work.

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "feat(admin): admin dashboard v2 — business cockpit with KPIs, alerts, funnel, enriched users"
```
