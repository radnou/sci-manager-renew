from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from app.core.config import settings


class PlanKey(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    LIFETIME = "lifetime"


@dataclass(frozen=True)
class PlanEntitlements:
    plan_key: PlanKey
    display_name: str
    billing_period: str
    max_scis: int | None
    max_biens: int | None
    multi_sci_enabled: bool
    charges_enabled: bool
    fiscalite_enabled: bool
    quitus_enabled: bool
    cerfa_enabled: bool
    priority_support: bool
    checkout_mode: str
    entitlements_version: int = 1
    is_public: bool = True

    def features_payload(self) -> dict[str, bool]:
        return {
            "multi_sci_enabled": self.multi_sci_enabled,
            "charges_enabled": self.charges_enabled,
            "fiscalite_enabled": self.fiscalite_enabled,
            "quitus_enabled": self.quitus_enabled,
            "cerfa_enabled": self.cerfa_enabled,
            "priority_support": self.priority_support,
        }

    def metadata_payload(self) -> dict[str, str]:
        return {
            "plan_key": self.plan_key.value,
            "billing_period": self.billing_period,
            "max_scis": "" if self.max_scis is None else str(self.max_scis),
            "max_biens": "" if self.max_biens is None else str(self.max_biens),
            "entitlements_version": str(self.entitlements_version),
            **{key: str(value).lower() for key, value in self.features_payload().items()},
        }

    def supports_multiple_scis(self) -> bool:
        return self.max_scis is None or self.max_scis > 1 or self.multi_sci_enabled


PLAN_CATALOG: dict[PlanKey, PlanEntitlements] = {
    PlanKey.FREE: PlanEntitlements(
        plan_key=PlanKey.FREE,
        display_name="Free",
        billing_period="none",
        max_scis=1,
        max_biens=1,
        multi_sci_enabled=False,
        charges_enabled=False,
        fiscalite_enabled=False,
        quitus_enabled=True,
        cerfa_enabled=False,
        priority_support=False,
        checkout_mode="subscription",
        is_public=False,
    ),
    PlanKey.STARTER: PlanEntitlements(
        plan_key=PlanKey.STARTER,
        display_name="Starter",
        billing_period="month",
        max_scis=1,
        max_biens=5,
        multi_sci_enabled=False,
        charges_enabled=True,
        fiscalite_enabled=False,
        quitus_enabled=True,
        cerfa_enabled=False,
        priority_support=False,
        checkout_mode="subscription",
    ),
    PlanKey.PRO: PlanEntitlements(
        plan_key=PlanKey.PRO,
        display_name="Pro",
        billing_period="month",
        max_scis=10,
        max_biens=20,
        multi_sci_enabled=True,
        charges_enabled=True,
        fiscalite_enabled=True,
        quitus_enabled=True,
        cerfa_enabled=True,
        priority_support=True,
        checkout_mode="subscription",
    ),
    PlanKey.LIFETIME: PlanEntitlements(
        plan_key=PlanKey.LIFETIME,
        display_name="Lifetime",
        billing_period="once",
        max_scis=None,
        max_biens=None,
        multi_sci_enabled=True,
        charges_enabled=True,
        fiscalite_enabled=True,
        quitus_enabled=True,
        cerfa_enabled=True,
        priority_support=True,
        checkout_mode="payment",
    ),
}


def get_plan(plan_key: PlanKey | str) -> PlanEntitlements:
    normalized = plan_key if isinstance(plan_key, PlanKey) else PlanKey(str(plan_key))
    return PLAN_CATALOG[normalized]


def list_public_plans() -> list[PlanEntitlements]:
    return [plan for plan in PLAN_CATALOG.values() if plan.is_public]


def resolve_price_id_for_plan(plan_key: PlanKey | str) -> str | None:
    normalized = plan_key if isinstance(plan_key, PlanKey) else PlanKey(str(plan_key))
    if normalized == PlanKey.STARTER:
        return settings.stripe_starter_price_id
    if normalized == PlanKey.PRO:
        return settings.stripe_pro_price_id
    if normalized == PlanKey.LIFETIME:
        return settings.stripe_lifetime_price_id
    return None


def resolve_plan_key_from_price_id(price_id: str | None) -> PlanKey | None:
    if not price_id:
        return None

    price_mapping = {
        settings.stripe_starter_price_id: PlanKey.STARTER,
        settings.stripe_pro_price_id: PlanKey.PRO,
        settings.stripe_lifetime_price_id: PlanKey.LIFETIME,
    }
    return price_mapping.get(price_id)


def build_plan_snapshot(plan_key: PlanKey | str) -> dict[str, Any]:
    plan = get_plan(plan_key)
    return {
        "plan_key": plan.plan_key.value,
        "plan_name": plan.display_name,
        "billing_period": plan.billing_period,
        "max_scis": plan.max_scis,
        "max_biens": plan.max_biens,
        "entitlements_version": plan.entitlements_version,
        "features": plan.features_payload(),
    }


def compute_remaining_quota(limit_value: int | None, current_value: int) -> int | None:
    if limit_value is None:
        return None
    return max(limit_value - current_value, 0)
