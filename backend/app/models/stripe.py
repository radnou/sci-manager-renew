from typing import Any, Literal

from pydantic import BaseModel, Field

from app.core.entitlements import PlanKey


class CheckoutSessionCreateRequest(BaseModel):
    plan_key: PlanKey
    mode: Literal["subscription", "payment"] | None = None


class CheckoutSessionCreateResponse(BaseModel):
    url: str


class StripeWebhookResponse(BaseModel):
    status: Literal["success", "ignored"]


class SubscriptionEntitlementsResponse(BaseModel):
    plan_key: str
    plan_name: str
    status: str
    mode: Literal["subscription", "payment"]
    is_active: bool
    stripe_price_id: str | None = None
    entitlements_version: int
    max_scis: int | None = None
    max_biens: int | None = None
    current_scis: int = 0
    current_biens: int = 0
    remaining_scis: int | None = None
    remaining_biens: int | None = None
    over_limit: bool = False
    features: dict[str, Any] = Field(default_factory=dict)
    onboarding_completed: bool = False
