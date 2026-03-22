from __future__ import annotations

from typing import Any

import structlog

from app.core.config import settings
from app.core.entitlements import (
    PlanKey,
    build_plan_snapshot,
    compute_remaining_quota,
    get_plan,
    get_trial_expired_plan,
    is_trial_active,
    resolve_plan_key_from_price_id,
)
from app.core.exceptions import PlanLimitError, SubscriptionInactiveError, UpgradeRequiredError
from app.core.supabase_client import get_supabase_service_client

logger = structlog.get_logger(__name__)

ACTIVE_SUBSCRIPTION_STATUSES = {"active", "trialing", "paid", "free"}


class SubscriptionService:
    @staticmethod
    def _enforcement_mode() -> str:
        return settings.feature_plan_entitlements_enforcement

    @classmethod
    def _guardrail_allows(cls) -> bool:
        return cls._enforcement_mode() in {"observe", "warn"}

    @classmethod
    def _log_guardrail_bypass(
        cls,
        *,
        reason: str,
        user_id: str,
        plan_key: str,
        details: dict[str, Any],
    ) -> None:
        logger.warning(
            "subscription_guardrail_bypassed",
            enforcement_mode=cls._enforcement_mode(),
            reason=reason,
            user_id=user_id,
            plan_key=plan_key,
            **details,
        )

    @staticmethod
    def _count_query(query: Any) -> int:
        result = query.execute()
        count = getattr(result, "count", None)
        if isinstance(count, int):
            return count
        rows = getattr(result, "data", None) or []
        return len(rows)

    @staticmethod
    def _create_trial_subscription(user_id: str) -> dict[str, Any] | None:
        """Create a 14-day trial subscription for a new user."""
        from datetime import datetime, timedelta, timezone

        try:
            trial_end = datetime.now(timezone.utc) + timedelta(days=14)
            trial_end_iso = trial_end.isoformat()

            payload = {
                "user_id": user_id,
                "stripe_price_id": "trial",
                "status": "trialing",
                "mode": "subscription",
                "is_active": True,
                "current_period_end": trial_end_iso,
                "plan_key": "free",
                "entitlements_version": 1,
                "max_scis": None,
                "max_biens": None,
                "features": get_plan(PlanKey.PRO).features_payload(),
            }

            client = get_supabase_service_client()
            result = client.table("subscriptions").upsert(
                payload, on_conflict="user_id"
            ).execute()

            if result.data:
                return result.data[0]
            return payload
        except Exception:
            logger.warning("trial_subscription_creation_failed", user_id=user_id, exc_info=True)
            return None

    @staticmethod
    def _load_subscription_row(user_id: str) -> dict[str, Any] | None:
        client = get_supabase_service_client()
        result = client.table("subscriptions").select("*").eq("user_id", user_id).execute()
        rows = result.data or []
        if not rows:
            return None
        return rows[0]

    @classmethod
    def get_usage_counts(cls, user_id: str) -> dict[str, int]:
        client = get_supabase_service_client()
        sci_count = cls._count_query(client.table("associes").select("id", count="exact").eq("user_id", user_id))

        memberships = client.table("associes").select("id_sci").eq("user_id", user_id).execute().data or []
        sci_ids = [str(row.get("id_sci")) for row in memberships if row.get("id_sci")]

        if not sci_ids:
            return {"current_scis": sci_count, "current_biens": 0}

        biens_query = client.table("biens").select("id", count="exact")
        if hasattr(biens_query, "in_"):
            bien_count = cls._count_query(biens_query.in_("id_sci", sci_ids))
        else:
            bien_count = 0
            for sci_id in sci_ids:
                bien_count += cls._count_query(
                    client.table("biens").select("id", count="exact").eq("id_sci", sci_id)
                )

        return {"current_scis": sci_count, "current_biens": bien_count}

    @classmethod
    def get_subscription_summary(cls, user_id: str) -> dict[str, Any]:
        row = cls._load_subscription_row(user_id)
        if not row:
            # No subscription row at all: create a trial record for the user
            trial_row = cls._create_trial_subscription(user_id)
            if trial_row:
                row = trial_row
            else:
                # Fallback if trial creation fails
                row = build_plan_snapshot(PlanKey.FREE)
                row.update(
                    {
                        "status": "trialing",
                        "mode": "subscription",
                        "is_active": True,
                        "stripe_price_id": "trial",
                    }
                )

        # Handle trialing status with expiry check
        row_status = str(row.get("status") or "").lower()
        if row_status == "trialing":
            current_period_end = row.get("current_period_end")
            if is_trial_active(row_status, current_period_end):
                # Active trial: grant Pilotage-level access
                snapshot = build_plan_snapshot(PlanKey.PRO)
                row = {**snapshot, **row}
                row["is_active"] = True
                row["plan_name"] = "Essai Pilotage"
            else:
                # Expired trial: read-only access
                # Expired values MUST override DB row values
                expired_plan = get_trial_expired_plan()
                snapshot = build_plan_snapshot(PlanKey.FREE)
                row = {**snapshot, **row}
                row["features"] = expired_plan.features_payload()
                row["max_scis"] = expired_plan.max_scis
                row["max_biens"] = expired_plan.max_biens
                row["is_active"] = False
                row["plan_name"] = "Essai expiré"
        else:
            plan_key = row.get("plan_key") or resolve_plan_key_from_price_id(row.get("stripe_price_id")) or PlanKey.FREE.value
            snapshot = build_plan_snapshot(plan_key)
            row = {**snapshot, **row}
            row["is_active"] = row_status in ACTIVE_SUBSCRIPTION_STATUSES

        usage = cls.get_usage_counts(user_id)
        max_scis = row.get("max_scis")
        max_biens = row.get("max_biens")
        current_scis = usage["current_scis"]
        current_biens = usage["current_biens"]
        remaining_scis = compute_remaining_quota(max_scis, current_scis)
        remaining_biens = compute_remaining_quota(max_biens, current_biens)

        over_limit = bool(
            (max_scis is not None and current_scis > max_scis)
            or (max_biens is not None and current_biens > max_biens)
        )

        return {
            "plan_key": row.get("plan_key", PlanKey.FREE.value),
            "plan_name": row.get("plan_name") or get_plan(row.get("plan_key", PlanKey.FREE.value)).display_name,
            "status": row.get("status", "free"),
            "mode": row.get("mode", "subscription"),
            "is_active": bool(row.get("is_active", False)),
            "stripe_price_id": row.get("stripe_price_id"),
            "entitlements_version": row.get("entitlements_version", 1),
            "max_scis": max_scis,
            "max_biens": max_biens,
            "features": row.get("features") or get_plan(row.get("plan_key", PlanKey.FREE.value)).features_payload(),
            "current_scis": current_scis,
            "current_biens": current_biens,
            "remaining_scis": remaining_scis,
            "remaining_biens": remaining_biens,
            "over_limit": over_limit,
            "current_period_end": row.get("current_period_end"),
            "trial_expired": (
                row_status == "trialing"
                and not is_trial_active(row_status, row.get("current_period_end"))
            ),
        }

    @classmethod
    def ensure_feature_enabled(cls, user_id: str, feature_name: str) -> dict[str, Any]:
        summary = cls.get_subscription_summary(user_id)
        plan_key = str(summary["plan_key"])
        features = summary.get("features") or {}
        if plan_key != PlanKey.FREE.value and not summary.get("is_active", False):
            if cls._guardrail_allows():
                cls._log_guardrail_bypass(
                    reason="inactive_subscription",
                    user_id=user_id,
                    plan_key=plan_key,
                    details={"status": str(summary.get("status")), "feature_name": feature_name},
                )
                return summary
            raise SubscriptionInactiveError(plan_key=plan_key, status=str(summary.get("status")))
        if not features.get(feature_name, False):
            if cls._guardrail_allows():
                cls._log_guardrail_bypass(
                    reason="feature_disabled",
                    user_id=user_id,
                    plan_key=plan_key,
                    details={"feature_name": feature_name},
                )
                return summary
            raise UpgradeRequiredError(
                "Feature not available on your plan",
                plan_key=plan_key,
                feature=feature_name,
            )
        return summary

    @classmethod
    def enforce_limit(cls, user_id: str, resource: str) -> dict[str, Any]:
        summary = cls.get_subscription_summary(user_id)
        plan_key = str(summary["plan_key"])
        if plan_key != PlanKey.FREE.value and not summary.get("is_active", False):
            if cls._guardrail_allows():
                cls._log_guardrail_bypass(
                    reason="inactive_subscription",
                    user_id=user_id,
                    plan_key=plan_key,
                    details={"status": str(summary.get("status")), "resource": resource},
                )
                return summary
            raise SubscriptionInactiveError(plan_key=plan_key, status=str(summary.get("status")))

        limit_key = f"max_{resource}"
        current_key = f"current_{resource}"
        limit_value = summary.get(limit_key)
        current_value = int(summary.get(current_key) or 0)

        if limit_value is not None and current_value >= limit_value:
            logger.info(
                "plan_limit_reached",
                user_id=user_id,
                resource=resource,
                plan_key=plan_key,
                current=current_value,
                limit=limit_value,
            )
            if cls._guardrail_allows():
                cls._log_guardrail_bypass(
                    reason="limit_reached",
                    user_id=user_id,
                    plan_key=plan_key,
                    details={"resource": resource, "current": current_value, "limit": limit_value},
                )
                return summary
            raise PlanLimitError(resource=resource, limit=limit_value, current=current_value, plan_key=plan_key)

        return summary

    @staticmethod
    def build_subscription_payload(
        *,
        session_data: dict[str, Any],
        status_value: str,
        plan_key: str | None,
        current_period_end: Any = None,
    ) -> dict[str, Any]:
        resolved_plan_key = plan_key or resolve_plan_key_from_price_id(session_data.get("price_id")) or PlanKey.FREE.value
        snapshot = build_plan_snapshot(resolved_plan_key)
        return {
            "user_id": session_data.get("client_reference_id"),
            "stripe_customer_id": session_data.get("customer"),
            "stripe_subscription_id": session_data.get("subscription"),
            "stripe_price_id": session_data.get("price_id"),
            "mode": session_data.get("mode") or get_plan(resolved_plan_key).checkout_mode,
            "status": status_value,
            "current_period_end": current_period_end,
            "plan_key": snapshot["plan_key"],
            "entitlements_version": snapshot["entitlements_version"],
            "max_scis": snapshot["max_scis"],
            "max_biens": snapshot["max_biens"],
            "features": snapshot["features"],
            "is_active": status_value in ACTIVE_SUBSCRIPTION_STATUSES,
        }
