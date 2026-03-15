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
