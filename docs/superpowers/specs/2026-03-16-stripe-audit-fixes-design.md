# Stripe Audit Fixes — Design Spec

**Date**: 2026-03-16
**Status**: Draft
**Source**: Stripe integration audit (pre-launch)

## Context

Pre-launch Stripe audit found 2 critical bugs, 4 important issues, and 2 minor issues. This spec covers all fixes.

## Fix 1: Annual subscriptions broken for authenticated users (CRITICAL)

**Bug**: `CheckoutSessionCreateRequest` in `backend/app/models/stripe.py:8-10` has no `billing_period` field. The authenticated `create_checkout_session` endpoint always uses the monthly price via `resolve_price_id_for_plan(payload.plan_key)` without passing `billing_period`. Guest checkout (`GuestCheckoutRequest`) correctly accepts `billing_period`.

**Fix**:
- Add `billing_period: str = "month"` to `CheckoutSessionCreateRequest`
- Pass `billing_period=payload.billing_period` to `resolve_price_id_for_plan()` in the authenticated checkout endpoint
- Frontend already sends `billing_period` — backend just ignores it

**Files**: `backend/app/models/stripe.py`, `backend/app/api/v1/stripe.py`

## Fix 2: Silent subscription state loss on webhook DB failure (CRITICAL)

**Bug**: In `_sync_subscription` (`stripe.py:105-109`), if the Supabase upsert fails, the exception is caught, logged as warning, and the webhook returns 200. Stripe won't retry. Subscription state is silently lost.

**Fix**:
- Let the exception propagate (don't catch it in `_sync_subscription`)
- The webhook endpoint's outer try/catch will return 500, and Stripe will retry with exponential backoff (up to 72h)
- Add explicit error handling: if upsert fails, return 500 so Stripe retries

**Files**: `backend/app/api/v1/stripe.py`

## Fix 3: No customer portal for self-service (IMPORTANT)

**Bug**: No `stripe.billing_portal.Session.create()` anywhere. Users can't cancel, update payment method, or view invoices. Required by French consumer law (droit de résiliation en ligne).

**Fix**:
- Add `POST /api/v1/stripe/customer-portal` endpoint
- Creates a Stripe Billing Portal session with return URL
- Add a "Gérer mon abonnement" button in the frontend settings/account page
- Requires `stripe_customer_id` from the user's subscription

**Files**: `backend/app/api/v1/stripe.py`, `frontend/src/routes/(app)/settings/+page.svelte` or `account/+page.svelte`

## Fix 4: Pricing page ≠ entitlements mismatch (IMPORTANT)

**Bug**: Multiple discrepancies between `/pricing` UI and `entitlements.py`:
- Free plan: UI says "2 biens maximum", backend enforces 5
- Free plan: UI says "Suivi des charges" included, backend has `charges_enabled=False`
- Starter plan: UI says "Gestion des associés", backend has `associes_enabled=False`

**Fix**:
- Update pricing page to match actual entitlements:
  - Free: "5 biens maximum" (not 2)
  - Free: remove "Suivi des charges" from feature list
  - Starter: remove "Gestion des associés" or enable it in entitlements
- Decision: align UI to backend (backend is the source of truth)

**Files**: `frontend/src/routes/pricing/+page.svelte`, potentially `frontend/src/routes/+page.svelte` (homepage pricing section)

## Fix 5: No `invoice.payment_failed` handling (IMPORTANT)

**Bug**: Failed renewals result in silent access loss. No notification to user.

**Fix**:
- Add `invoice.payment_failed` event handling in the webhook
- When payment fails, create a notification for the user (via existing notification system)
- The `customer.subscription.updated` handler already handles the status change to `past_due`
- Just add a user-facing notification: "Votre paiement a échoué. Mettez à jour votre moyen de paiement."

**Files**: `backend/app/api/v1/stripe.py`

## Fix 6: Missing env vars in `.env.production.example` (IMPORTANT)

**Bug**: `STRIPE_STARTER_ANNUAL_PRICE_ID`, `STRIPE_PRO_ANNUAL_PRICE_ID`, `STRIPE_CABINET_PRICE_ID`, `STRIPE_CABINET_ANNUAL_PRICE_ID` are used in code but absent from `.env.production.example`.

**Fix**: Add the missing vars to `.env.production.example`.

**Files**: `.env.production.example`

## Fix 7: Minor cleanup

- Remove dead code `frontend/src/lib/stripe.ts` (never imported)
- Handle `?upgraded=true` in dashboard with a success toast
- Increase webhook rate limit from 10/min to 30/min

**Files**: `frontend/src/lib/stripe.ts`, `frontend/src/routes/(app)/dashboard/+page.svelte`, `backend/app/api/v1/stripe.py`

## Out of Scope

- Downgrade resource cleanup (read access to over-limit resources is acceptable)
- Lifetime deal re-enablement (grandfathered users are safe)
- `_find_user_by_email` O(N) scan (acceptable at current scale)
