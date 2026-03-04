from __future__ import annotations

import logging
from typing import Any

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.security import get_current_user
from app.core.supabase_client import get_supabase_service_client
from app.models.stripe import (
    CheckoutSessionCreateRequest,
    CheckoutSessionCreateResponse,
    StripeWebhookResponse,
)

router = APIRouter(prefix="/stripe", tags=["stripe"])
logger = logging.getLogger(__name__)


def _to_str(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _sync_subscription(session_data: dict[str, Any], status_value: str) -> None:
    user_id = _to_str(session_data.get("client_reference_id"))
    if not user_id:
        return

    payload: dict[str, Any] = {
        "user_id": user_id,
        "stripe_customer_id": _to_str(session_data.get("customer")),
        "stripe_subscription_id": _to_str(session_data.get("subscription")),
        "stripe_price_id": _to_str(session_data.get("price_id")),
        "mode": _to_str(session_data.get("mode")),
        "status": status_value,
    }

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
        query = client.table("subscriptions").update({"status": "canceled"})
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
        _sync_subscription(obj, status_value)
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
        _sync_subscription(session_like, subscription_status)


@router.post(
    "/create-checkout-session",
    response_model=CheckoutSessionCreateResponse,
)
async def create_checkout_session(
    payload: CheckoutSessionCreateRequest,
    user_id: str = Depends(get_current_user),
) -> CheckoutSessionCreateResponse:
    stripe.api_key = settings.stripe_secret_key

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": payload.price_id,
                    "quantity": 1,
                }
            ],
            mode=payload.mode,
            success_url=f"{settings.frontend_url}/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.frontend_url}/pricing",
            client_reference_id=user_id,
        )
    except stripe.error.StripeError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    session_url = _to_str(getattr(session, "url", None))
    if not session_url and hasattr(session, "get"):
        session_url = _to_str(session.get("url"))

    if not session_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe checkout session URL unavailable",
        )

    return CheckoutSessionCreateResponse(url=session_url)


@router.post("/webhook", response_model=StripeWebhookResponse)
@limiter.limit("10/minute")
async def stripe_webhook(request: Request) -> StripeWebhookResponse:
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe signature",
        )

    stripe.api_key = settings.stripe_secret_key

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=settings.stripe_webhook_secret,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Stripe payload",
        ) from exc
    except stripe.error.SignatureVerificationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Stripe signature",
        ) from exc

    _handle_event(event)
    return StripeWebhookResponse(status="success")

