from __future__ import annotations

from typing import Any

import stripe
import structlog
from fastapi import APIRouter, Depends, Request

from app.core.entitlements import PlanKey, get_plan, resolve_price_id_for_plan
from app.core.config import settings
from app.core.exceptions import ExternalServiceError, FeatureDisabledError, ValidationError
from app.core.rate_limit import limiter
from app.core.security import get_current_user
from app.core.supabase_client import get_supabase_service_client
from app.models.stripe import (
    CheckoutSessionCreateRequest,
    CheckoutSessionCreateResponse,
    SubscriptionEntitlementsResponse,
    StripeWebhookResponse,
)
from app.services.subscription_service import SubscriptionService

router = APIRouter(prefix="/stripe", tags=["stripe"])
logger = structlog.get_logger(__name__)


def _to_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _sync_subscription(
    session_data: dict[str, Any],
    status_value: str,
    *,
    plan_key: str | None = None,
    current_period_end: Any = None,
) -> None:
    user_id = _to_str(session_data.get("client_reference_id"))
    if not user_id:
        return

    payload = SubscriptionService.build_subscription_payload(
        session_data={
            "client_reference_id": user_id,
            "customer": _to_str(session_data.get("customer")),
            "subscription": _to_str(session_data.get("subscription")),
            "price_id": _to_str(session_data.get("price_id")),
            "mode": _to_str(session_data.get("mode")),
        },
        status_value=status_value,
        plan_key=plan_key,
        current_period_end=current_period_end,
    )

    try:
        client = get_supabase_service_client()
        client.table("subscriptions").upsert(payload, on_conflict="user_id").execute()
    except Exception:
        logger.warning("Unable to persist Stripe subscription state", exc_info=True)


def _sync_subscription_deleted(subscription_data: dict[str, Any]) -> None:
    customer_id = _to_str(subscription_data.get("customer"))
    subscription_id = _to_str(subscription_data.get("id"))
    if not customer_id and not subscription_id:
        return

    try:
        client = get_supabase_service_client()
        query = client.table("subscriptions").update({"status": "canceled", "is_active": False})
        if subscription_id:
            query = query.eq("stripe_subscription_id", subscription_id)
        elif customer_id:
            query = query.eq("stripe_customer_id", customer_id)
        query.execute()
    except Exception:
        logger.warning("Unable to persist Stripe cancellation state", exc_info=True)


def _handle_event(event: Any) -> None:
    event_type = _to_str(event.get("type")) if hasattr(event, "get") else None
    event_data = event.get("data", {}) if hasattr(event, "get") else {}
    obj = event_data.get("object", {}) if isinstance(event_data, dict) else {}

    if not isinstance(obj, dict):
        obj = dict(obj)

    if event_type == "checkout.session.completed":
        status_value = "active" if obj.get("payment_status") == "paid" else "pending"
        _sync_subscription(
            obj,
            status_value,
            plan_key=_to_str(obj.get("metadata", {}).get("plan_key")) if isinstance(obj.get("metadata"), dict) else None,
        )
        return

    if event_type == "customer.subscription.deleted":
        _sync_subscription_deleted(obj)
        return

    if event_type == "customer.subscription.updated":
        subscription_status = _to_str(obj.get("status")) or "active"
        session_like = {
            "client_reference_id": obj.get("metadata", {}).get("user_id")
            if isinstance(obj.get("metadata"), dict)
            else None,
            "customer": obj.get("customer"),
            "subscription": obj.get("id"),
            "price_id": obj.get("items", {})
            .get("data", [{}])[0]
            .get("price", {})
            .get("id")
            if isinstance(obj.get("items"), dict)
            else None,
            "mode": "subscription",
        }
        _sync_subscription(
            session_like,
            subscription_status,
            plan_key=_to_str(obj.get("metadata", {}).get("plan_key")) if isinstance(obj.get("metadata"), dict) else None,
            current_period_end=obj.get("current_period_end"),
        )


@router.get("/subscription", response_model=SubscriptionEntitlementsResponse)
async def get_subscription(user_id: str = Depends(get_current_user)) -> SubscriptionEntitlementsResponse:
    logger.info("fetching_subscription_entitlements", user_id=user_id)
    summary = SubscriptionService.get_subscription_summary(user_id)

    # Load onboarding_completed from subscriptions table
    client = get_supabase_service_client()
    result = (
        client.table("subscriptions")
        .select("onboarding_completed")
        .eq("user_id", user_id)
        .execute()
    )
    onboarding_completed = False
    if result.data:
        onboarding_completed = bool(result.data[0].get("onboarding_completed", False))

    summary["onboarding_completed"] = onboarding_completed
    return SubscriptionEntitlementsResponse(**summary)


@router.post(
    "/create-checkout-session",
    response_model=CheckoutSessionCreateResponse,
)
@limiter.limit("10/minute")
async def create_checkout_session(
    request: Request,
    payload: CheckoutSessionCreateRequest,
    user_id: str = Depends(get_current_user),
) -> CheckoutSessionCreateResponse:
    del request
    if not settings.feature_stripe_payments:
        raise FeatureDisabledError(
            "Les paiements Stripe sont désactivés.",
            flag_name="feature_stripe_payments",
        )
    if not settings.feature_new_checkout_catalog:
        raise FeatureDisabledError(
            "Le catalogue Stripe est désactivé.",
            flag_name="feature_new_checkout_catalog",
        )
    resolved_plan = get_plan(payload.plan_key)
    if payload.plan_key == PlanKey.FREE:
        raise ValidationError("Le plan gratuit ne passe pas par Stripe.")

    price_id = resolve_price_id_for_plan(payload.plan_key)
    if not price_id:
        raise ExternalServiceError("Stripe", "Price ID unavailable for requested plan")

    checkout_mode = payload.mode or resolved_plan.checkout_mode
    if checkout_mode != resolved_plan.checkout_mode:
        raise ValidationError("Checkout mode does not match the selected plan")

    logger.info(
        "creating_checkout_session",
        user_id=user_id,
        plan_key=payload.plan_key.value,
        price_id=price_id,
        mode=checkout_mode,
    )

    stripe.api_key = settings.stripe_secret_key

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            mode=checkout_mode,
            success_url=f"{settings.frontend_url}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.frontend_url}/pricing",
            client_reference_id=user_id,
            metadata={"user_id": user_id, "plan_key": payload.plan_key.value},
        )
    except stripe.error.StripeError as exc:
        logger.error(
            "stripe_checkout_session_failed",
            user_id=user_id,
            plan_key=payload.plan_key.value,
            error=str(exc),
            exc_info=True,
        )
        raise ExternalServiceError("Stripe", f"Checkout session creation failed: {str(exc)}")

    session_url = _to_str(getattr(session, "url", None))
    if not session_url and hasattr(session, "get"):
        session_url = _to_str(session.get("url"))

    if not session_url:
        logger.error("stripe_session_url_missing", user_id=user_id)
        raise ExternalServiceError("Stripe", "Checkout session URL unavailable")

    logger.info(
        "checkout_session_created",
        user_id=user_id,
        plan_key=payload.plan_key.value,
        session_url=session_url,
    )
    return CheckoutSessionCreateResponse(url=session_url)


@router.post("/webhook", response_model=StripeWebhookResponse)
@limiter.limit("10/minute")
async def stripe_webhook(request: Request) -> StripeWebhookResponse:
    logger.info("stripe_webhook_received")

    if not settings.feature_stripe_payments:
        logger.warning("stripe_webhook_ignored", reason="feature_disabled")
        return StripeWebhookResponse(status="ignored")

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        logger.warning("stripe_webhook_missing_signature")
        raise ValidationError("Missing Stripe signature header")

    stripe.api_key = settings.stripe_secret_key

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.stripe_webhook_secret,
        )
    except ValueError as exc:
        logger.error("stripe_webhook_invalid_payload", error=str(exc))
        raise ValidationError(f"Invalid Stripe payload: {str(exc)}")
    except stripe.error.SignatureVerificationError as exc:
        logger.error("stripe_webhook_invalid_signature", error=str(exc))
        raise ValidationError("Invalid Stripe signature") from exc

    logger.info("stripe_webhook_processing", event_type=event.get("type") if hasattr(event, "get") else None)
    _handle_event(event)
    logger.info("stripe_webhook_processed_successfully")
    return StripeWebhookResponse(status="success")
