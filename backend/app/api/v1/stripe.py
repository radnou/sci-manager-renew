from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
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
    GuestCheckoutRequest,
    RefundResponse,
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


def _find_user_by_email(email: str) -> str | None:
    """Look up user by email via direct auth.users query."""
    try:
        client = get_supabase_service_client()
        existing = client.auth.admin.list_users()
        for user in getattr(existing, "users", []):
            if getattr(user, "email", None) == email:
                return str(user.id)
    except Exception:
        logger.warning("find_user_by_email_failed", email=email)
    return None


def _create_or_get_user(email: str) -> str | None:
    """Create Supabase user if not exists, return user_id."""
    try:
        existing_id = _find_user_by_email(email)
        if existing_id:
            return existing_id

        client = get_supabase_service_client()
        random_password = secrets.token_urlsafe(32)
        result = client.auth.admin.create_user({
            "email": email,
            "password": random_password,
            "email_confirm": True,
        })
        if hasattr(result, "user") and result.user:
            return str(result.user.id)
    except Exception as exc:
        # Handle race condition: user was created between find and create
        if "already been registered" in str(exc):
            logger.info("guest_user_already_exists_retrying_find", email=email)
            return _find_user_by_email(email)
        logger.error("guest_user_creation_failed", email=email, exc_info=True)
    return None


def _update_subscription_metadata(sub_id: str, user_id: str, plan_key: str | None) -> None:
    """Write user_id into Stripe Subscription metadata for future webhooks."""
    try:
        stripe.api_key = settings.stripe_secret_key
        metadata: dict[str, str] = {"user_id": user_id}
        if plan_key:
            metadata["plan_key"] = plan_key
        stripe.Subscription.modify(sub_id, metadata=metadata)
    except Exception:
        logger.error("stripe_subscription_metadata_update_failed", sub_id=sub_id, user_id=user_id, exc_info=True)


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

    client = get_supabase_service_client()
    client.table("subscriptions").upsert(payload, on_conflict="user_id").execute()


def _sync_subscription_deleted(subscription_data: dict[str, Any]) -> None:
    customer_id = _to_str(subscription_data.get("customer"))
    subscription_id = _to_str(subscription_data.get("id"))
    if not customer_id and not subscription_id:
        return

    client = get_supabase_service_client()
    query = client.table("subscriptions").update({"status": "canceled", "is_active": False})
    if subscription_id:
        query = query.eq("stripe_subscription_id", subscription_id)
    elif customer_id:
        query = query.eq("stripe_customer_id", customer_id)
    query.execute()


def _is_event_already_processed(event_id: str) -> bool:
    """Check if a Stripe webhook event was already processed (idempotency guard).

    Uses the stripe_webhook_events table as a lightweight dedup store.
    Returns True if the event was already processed, False otherwise.
    On check failure (table missing, etc.), returns False to allow processing.
    """
    try:
        client = get_supabase_service_client()
        result = (
            client.table("stripe_webhook_events")
            .select("id")
            .eq("event_id", event_id)
            .limit(1)
            .execute()
        )
        return bool(result.data)
    except Exception:
        # Table may not exist yet; allow processing and log warning
        logger.warning("idempotency_check_failed", event_id=event_id, exc_info=True)
        return False


def _mark_event_processed(event_id: str, event_type: str) -> None:
    """Record a Stripe event as processed for idempotency."""
    try:
        client = get_supabase_service_client()
        client.table("stripe_webhook_events").insert({
            "event_id": event_id,
            "event_type": event_type,
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception:
        logger.warning("idempotency_mark_failed", event_id=event_id, exc_info=True)


async def _handle_event(event: Any) -> None:
    event_type = _to_str(event.get("type")) if hasattr(event, "get") else None
    event_data = event.get("data", {}) if hasattr(event, "get") else {}
    obj = event_data.get("object", {}) if isinstance(event_data, dict) else {}

    if not isinstance(obj, dict):
        obj = dict(obj)

    if event_type == "checkout.session.completed":
        user_id = _to_str(obj.get("client_reference_id"))
        status_value = "active" if obj.get("payment_status") == "paid" else "pending"
        plan_key = _to_str(obj.get("metadata", {}).get("plan_key")) if isinstance(obj.get("metadata"), dict) else None
        checkout_mode = _to_str(obj.get("mode"))

        # Guest checkout flow: no client_reference_id
        if not user_id:
            customer_details = obj.get("customer_details", {})
            email = customer_details.get("email") if isinstance(customer_details, dict) else None
            if email:
                user_id = _create_or_get_user(email)
                if user_id:
                    sub_id = _to_str(obj.get("subscription"))
                    if sub_id:
                        _update_subscription_metadata(sub_id, user_id, plan_key)

        if not user_id:
            return

        # Fondateur: one-time payment, no subscription object from Stripe
        if checkout_mode == "payment" and plan_key == "fondateur":
            _sync_subscription(
                {**obj, "client_reference_id": user_id, "mode": "payment"},
                "active",
                plan_key="fondateur",
            )
        else:
            _sync_subscription(
                {**obj, "client_reference_id": user_id},
                status_value,
                plan_key=plan_key,
            )

        # Clean up demo data now that user has paid
        try:
            from app.services.demo_service import cleanup_demo_data
            service_client = get_supabase_service_client()
            await cleanup_demo_data(service_client, user_id)
            logger.info("demo_cleanup_after_checkout", user_id=user_id)
        except Exception:
            logger.warning("demo_cleanup_failed_after_checkout", user_id=user_id, exc_info=True)

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

        # Fallback: resolve user_id via stripe_customer_id if metadata is missing
        if not session_like.get("client_reference_id"):
            customer_id = _to_str(obj.get("customer"))
            if customer_id:
                try:
                    client = get_supabase_service_client()
                    result = client.table("subscriptions").select("user_id").eq("stripe_customer_id", customer_id).limit(1).execute()
                    if result.data:
                        session_like["client_reference_id"] = result.data[0].get("user_id")
                except Exception:
                    logger.warning("fallback_user_resolution_failed", customer_id=customer_id, exc_info=True)

        _sync_subscription(
            session_like,
            subscription_status,
            plan_key=_to_str(obj.get("metadata", {}).get("plan_key")) if isinstance(obj.get("metadata"), dict) else None,
            current_period_end=obj.get("current_period_end"),
        )

    if event_type == "invoice.payment_failed":
        customer_id = _to_str(obj.get("customer"))
        if customer_id:
            try:
                client = get_supabase_service_client()
                result = client.table("subscriptions").select("user_id").eq("stripe_customer_id", customer_id).limit(1).execute()
                if result.data:
                    user_id = result.data[0].get("user_id")
                    if user_id:
                        client.table("notifications").insert({
                            "user_id": user_id,
                            "type": "payment_failed",
                            "title": "Paiement échoué",
                            "message": "Votre paiement a échoué. Mettez à jour votre moyen de paiement pour maintenir votre accès.",
                            "read": False,
                        }).execute()
                        logger.info("payment_failed_notification_created", user_id=user_id)
            except Exception:
                logger.warning("payment_failed_notification_error", exc_info=True)
        return


@router.get("/subscription", response_model=SubscriptionEntitlementsResponse)
async def get_subscription(user_id: str = Depends(get_current_user)) -> SubscriptionEntitlementsResponse:
    logger.info("fetching_subscription_entitlements", user_id=user_id)
    summary = SubscriptionService.get_subscription_summary(user_id)

    # Load onboarding_completed and demo_seeded from subscriptions table
    client = get_supabase_service_client()
    result = (
        client.table("subscriptions")
        .select("onboarding_completed, demo_seeded")
        .eq("user_id", user_id)
        .execute()
    )
    onboarding_completed = False
    demo_seeded = False
    if result.data:
        onboarding_completed = bool(result.data[0].get("onboarding_completed", False))
        demo_seeded = bool(result.data[0].get("demo_seeded", False))

    summary["onboarding_completed"] = onboarding_completed
    summary["demo_seeded"] = demo_seeded
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

    price_id = resolve_price_id_for_plan(payload.plan_key, billing_period=payload.billing_period)
    if not price_id:
        raise ExternalServiceError("Stripe", "Price ID unavailable for requested plan")

    checkout_mode = payload.mode or resolved_plan.checkout_mode
    # Allow fondateur to use 'payment' mode
    if checkout_mode != resolved_plan.checkout_mode and payload.plan_key != PlanKey.FONDATEUR:
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
        session = await stripe.checkout.Session.create_async(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            mode=checkout_mode,
            success_url=f"{settings.frontend_url}/dashboard?upgraded=true",
            cancel_url=f"{settings.frontend_url}/#pricing",
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


@router.post(
    "/create-guest-checkout",
    response_model=CheckoutSessionCreateResponse,
)
@limiter.limit("5/minute")
async def create_guest_checkout(
    request: Request,
    payload: GuestCheckoutRequest,
) -> CheckoutSessionCreateResponse:
    del request
    if not settings.feature_stripe_payments:
        raise FeatureDisabledError(
            "Les paiements Stripe sont désactivés.",
            flag_name="feature_stripe_payments",
        )

    if payload.plan_key not in ("starter", "pro", "fondateur"):
        raise ValidationError("plan_key must be 'starter', 'pro', or 'fondateur'.")

    is_fondateur = payload.plan_key == "fondateur"

    if not is_fondateur and payload.billing_period not in ("month", "year"):
        raise ValidationError("billing_period must be 'month' or 'year'.")

    price_id = resolve_price_id_for_plan(payload.plan_key, billing_period=payload.billing_period)
    if not price_id:
        raise ExternalServiceError("Stripe", "Price ID unavailable for requested plan")

    checkout_mode = "payment" if is_fondateur else "subscription"

    logger.info(
        "creating_guest_checkout_session",
        plan_key=payload.plan_key,
        billing_period=payload.billing_period,
        price_id=price_id,
        mode=checkout_mode,
    )

    stripe.api_key = settings.stripe_secret_key

    try:
        session = await stripe.checkout.Session.create_async(
            payment_method_types=["card"],
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                }
            ],
            mode=checkout_mode,
            success_url=f"{settings.frontend_url}/welcome?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.frontend_url}/#pricing",
            metadata={"plan_key": payload.plan_key, "billing_period": payload.billing_period},
        )
    except stripe.error.StripeError as exc:
        logger.error(
            "stripe_guest_checkout_session_failed",
            plan_key=payload.plan_key,
            error=str(exc),
            exc_info=True,
        )
        raise ExternalServiceError("Stripe", f"Checkout session creation failed: {str(exc)}")

    session_url = _to_str(getattr(session, "url", None))
    if not session_url and hasattr(session, "get"):
        session_url = _to_str(session.get("url"))

    if not session_url:
        logger.error("stripe_guest_session_url_missing")
        raise ExternalServiceError("Stripe", "Checkout session URL unavailable")

    session_id = _to_str(getattr(session, "id", None))
    if not session_id and hasattr(session, "get"):
        session_id = _to_str(session.get("id"))

    logger.info(
        "guest_checkout_session_created",
        plan_key=payload.plan_key,
        session_url=session_url,
    )
    return CheckoutSessionCreateResponse(url=session_url, session_id=session_id or "")


@router.post("/cancel-subscription")
@limiter.limit("3/minute")
async def cancel_subscription(
    request: Request,
    user_id: str = Depends(get_current_user),
):
    """Cancel subscription at end of current period (loi résiliation 3 clics)."""
    if not settings.feature_stripe_payments:
        raise FeatureDisabledError("Les paiements Stripe sont désactivés.", flag_name="feature_stripe_payments")

    client = get_supabase_service_client()
    result = client.table("subscriptions").select("stripe_subscription_id").eq("user_id", user_id).limit(1).execute()

    if not result.data or not result.data[0].get("stripe_subscription_id"):
        raise ValidationError("Aucun abonnement actif à résilier.")

    sub_id = result.data[0]["stripe_subscription_id"]
    stripe.api_key = settings.stripe_secret_key

    try:
        # Cancel at period end (user keeps access until end of billing cycle)
        stripe.Subscription.modify(sub_id, cancel_at_period_end=True)
    except stripe.error.StripeError as exc:
        raise ExternalServiceError("Stripe", f"Résiliation échouée: {str(exc)}")

    logger.info("subscription_cancelled", user_id=user_id, subscription_id=sub_id)
    return {"status": "cancelled", "message": "Votre abonnement sera résilié à la fin de la période en cours."}


@router.post("/customer-portal")
@limiter.limit("5/minute")
async def create_customer_portal(
    request: Request,
    user_id: str = Depends(get_current_user),
):
    """Create a Stripe Billing Portal session for self-service subscription management."""
    del request
    if not settings.feature_stripe_payments:
        raise FeatureDisabledError("Les paiements Stripe sont désactivés.", flag_name="feature_stripe_payments")

    client = get_supabase_service_client()
    result = client.table("subscriptions").select("stripe_customer_id").eq("user_id", user_id).limit(1).execute()

    if not result.data or not result.data[0].get("stripe_customer_id"):
        raise ValidationError("Aucun abonnement Stripe trouvé pour cet utilisateur.")

    stripe_customer_id = result.data[0]["stripe_customer_id"]
    stripe.api_key = settings.stripe_secret_key

    try:
        portal_session = await stripe.billing_portal.Session.create_async(
            customer=stripe_customer_id,
            return_url=f"{settings.frontend_url}/settings",
        )
    except stripe.error.StripeError as exc:
        raise ExternalServiceError("Stripe", f"Portal session creation failed: {str(exc)}")

    return {"url": portal_session.url}


@router.post("/webhook", response_model=StripeWebhookResponse)
@limiter.limit("30/minute")
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

    event_id = _to_str(event.get("id")) if hasattr(event, "get") else None
    event_type = _to_str(event.get("type")) if hasattr(event, "get") else None
    logger.info("stripe_webhook_processing", event_type=event_type, event_id=event_id)

    # Idempotency guard: skip already-processed events (Stripe delivers at-least-once)
    if event_id and _is_event_already_processed(event_id):
        logger.info("stripe_webhook_duplicate_skipped", event_id=event_id, event_type=event_type)
        return StripeWebhookResponse(status="already_processed")

    await _handle_event(event)

    # Mark event as processed after successful handling
    if event_id:
        _mark_event_processed(event_id, event_type or "unknown")

    logger.info("stripe_webhook_processed_successfully", event_id=event_id)
    return StripeWebhookResponse(status="success")


@router.post("/refund", response_model=RefundResponse)
@limiter.limit("2/day")
async def request_refund(
    request: Request,
    user_id: str = Depends(get_current_user),
) -> RefundResponse:
    """Request a refund within the 30-day money-back guarantee period.

    Per CGV art. L221-28, users can request a full refund within 30 days
    of their first payment. The subscription is immediately cancelled
    and access revoked.
    """
    del request
    if not settings.feature_stripe_payments:
        raise FeatureDisabledError(
            "Les paiements Stripe sont désactivés.",
            flag_name="feature_stripe_payments",
        )

    client = get_supabase_service_client()
    result = (
        client.table("subscriptions")
        .select("stripe_subscription_id, stripe_customer_id, guarantee_expires_at, created_at, status, mode")
        .eq("user_id", user_id)
        .limit(1)
        .execute()
    )

    if not result.data:
        raise ValidationError("Aucun abonnement trouvé.")

    sub_row = result.data[0]
    sub_status = (sub_row.get("status") or "").lower()

    if sub_status not in {"active", "paid"}:
        raise ValidationError("Votre abonnement n'est pas actif. Remboursement impossible.")

    # Check 30-day guarantee window
    guarantee_expires_at = sub_row.get("guarantee_expires_at")
    if guarantee_expires_at:
        expiry = datetime.fromisoformat(str(guarantee_expires_at).replace("Z", "+00:00"))
    else:
        # Fallback: 30 days from subscription creation
        created_at = sub_row.get("created_at")
        if not created_at:
            raise ValidationError("Impossible de déterminer la date de souscription.")
        created = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
        expiry = created + timedelta(days=30)

    now = datetime.now(timezone.utc)
    if now > expiry:
        days_ago = (now - expiry).days
        raise ValidationError(
            f"La période de garantie de 30 jours est expirée depuis {days_ago} jour(s). "
            "Remboursement non disponible."
        )

    stripe.api_key = settings.stripe_secret_key
    stripe_sub_id = sub_row.get("stripe_subscription_id")
    stripe_customer_id = sub_row.get("stripe_customer_id")
    checkout_mode = sub_row.get("mode")

    # Find the latest invoice to refund
    refund_id = None
    try:
        if checkout_mode == "payment":
            # Fondateur (one-time payment): find payment intent via customer
            if stripe_customer_id:
                charges = stripe.Charge.list(customer=stripe_customer_id, limit=1)
                if charges.data:
                    refund = stripe.Refund.create(charge=charges.data[0].id)
                    refund_id = refund.id
                else:
                    raise ExternalServiceError("Stripe", "Aucun paiement trouvé pour ce client.")
            else:
                raise ExternalServiceError("Stripe", "Identifiant client Stripe manquant.")
        else:
            # Subscription: refund latest invoice then cancel
            if not stripe_sub_id:
                raise ExternalServiceError("Stripe", "Identifiant abonnement Stripe manquant.")

            invoices = stripe.Invoice.list(subscription=stripe_sub_id, limit=1, status="paid")
            if invoices.data:
                latest_invoice = invoices.data[0]
                if latest_invoice.payment_intent:
                    refund = stripe.Refund.create(payment_intent=latest_invoice.payment_intent)
                    refund_id = refund.id
                else:
                    raise ExternalServiceError("Stripe", "Aucun paiement associé à la dernière facture.")
            else:
                raise ExternalServiceError("Stripe", "Aucune facture payée trouvée.")

            # Cancel subscription immediately (not at period end)
            stripe.Subscription.cancel(stripe_sub_id)

    except stripe.error.StripeError as exc:
        logger.error(
            "stripe_refund_failed",
            user_id=user_id,
            stripe_sub_id=stripe_sub_id,
            error=str(exc),
            exc_info=True,
        )
        raise ExternalServiceError("Stripe", f"Remboursement échoué: {str(exc)}")

    # Update subscription status in DB
    client.table("subscriptions").update({
        "status": "refunded",
        "is_active": False,
    }).eq("user_id", user_id).execute()

    logger.info(
        "refund_processed",
        user_id=user_id,
        refund_id=refund_id,
        stripe_sub_id=stripe_sub_id,
    )

    return RefundResponse(
        status="refunded",
        message="Votre remboursement a été effectué. Votre abonnement est résilié.",
        refund_id=refund_id,
    )
