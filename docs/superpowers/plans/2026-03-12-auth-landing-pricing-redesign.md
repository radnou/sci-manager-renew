# Auth + Landing + Pricing Redesign — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refonte auth (pay-first + email/mdp), landing one-page avec pricing intégré, restructuration plans (Essentiel/Gestion/Fiscal), email templates Jinja2, SEO technique.

**Architecture:** Backend-first approach — entitlements + config → Stripe endpoints → auth endpoints → email templates → frontend pages → landing + SEO. Chaque task produit du code testable indépendamment.

**Tech Stack:** FastAPI, Supabase Auth Admin API, Stripe Checkout, Jinja2, SvelteKit, Tailwind CSS 4

**Spec:** `docs/superpowers/specs/2026-03-11-auth-landing-pricing-redesign.md`

---

## Chunk 1: Backend Foundation (Entitlements + Config + Migration)

### Task 1: Restructure PlanEntitlements dataclass

**Files:**
- Modify: `backend/app/core/entitlements.py`
- Test: `backend/tests/test_entitlements.py`

- [ ] **Step 1: Write failing tests for new entitlements structure**

```python
# In tests/test_entitlements.py — add these tests

def test_free_plan_is_public():
    plan = get_plan(PlanKey.FREE)
    assert plan.is_public is True
    assert plan.display_name == "Essentiel"
    assert plan.max_scis == 1
    assert plan.max_biens == 2


def test_starter_plan_renamed_gestion():
    plan = get_plan(PlanKey.STARTER)
    assert plan.display_name == "Gestion"
    assert plan.max_scis == 3
    assert plan.max_biens == 10
    assert plan.multi_sci_enabled is True
    assert plan.documents_enabled is True
    assert plan.notifications_enabled is True
    assert plan.dashboard_complet is True
    assert plan.cerfa_enabled is False
    assert plan.fiscalite_enabled is False


def test_pro_plan_renamed_fiscal():
    plan = get_plan(PlanKey.PRO)
    assert plan.display_name == "Fiscal"
    assert plan.max_scis is None
    assert plan.max_biens is None
    assert plan.cerfa_enabled is True
    assert plan.fiscalite_enabled is True
    assert plan.associes_enabled is True
    assert plan.pno_frais_enabled is True
    assert plan.rentabilite_enabled is True
    assert plan.dashboard_complet is True


def test_lifetime_grandfathered_to_pro():
    plan = get_plan(PlanKey.LIFETIME)
    assert plan.plan_key == PlanKey.PRO
    assert plan.display_name == "Fiscal"


def test_features_payload_includes_new_fields():
    plan = get_plan(PlanKey.PRO)
    payload = plan.features_payload()
    assert "documents_enabled" in payload
    assert "notifications_enabled" in payload
    assert "associes_enabled" in payload
    assert "pno_frais_enabled" in payload
    assert "rentabilite_enabled" in payload
    assert "dashboard_complet" in payload
    assert payload["documents_enabled"] is True


def test_list_public_plans_includes_all_three():
    from app.core.entitlements import list_public_plans
    plans = list_public_plans()
    keys = {p.plan_key for p in plans}
    assert keys == {PlanKey.FREE, PlanKey.STARTER, PlanKey.PRO}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && PYTHONPATH=. pytest tests/test_entitlements.py -v -k "test_free_plan_is_public or test_starter_plan_renamed or test_pro_plan_renamed or test_lifetime_grandfathered or test_features_payload_includes or test_list_public_plans_includes" 2>&1 | tail -20`

Expected: Multiple FAIL (display_name mismatch, missing fields, etc.)

- [ ] **Step 3: Add new fields to PlanEntitlements dataclass**

In `backend/app/core/entitlements.py`, add after `is_public: bool = True`:

```python
    documents_enabled: bool = False
    notifications_enabled: bool = False
    associes_enabled: bool = False
    pno_frais_enabled: bool = False
    rentabilite_enabled: bool = False
    dashboard_complet: bool = False
```

- [ ] **Step 4: Update features_payload() to include new fields**

Replace the `features_payload` method body:

```python
    def features_payload(self) -> dict[str, bool]:
        return {
            "multi_sci_enabled": self.multi_sci_enabled,
            "charges_enabled": self.charges_enabled,
            "fiscalite_enabled": self.fiscalite_enabled,
            "quitus_enabled": self.quitus_enabled,
            "cerfa_enabled": self.cerfa_enabled,
            "priority_support": self.priority_support,
            "documents_enabled": self.documents_enabled,
            "notifications_enabled": self.notifications_enabled,
            "associes_enabled": self.associes_enabled,
            "pno_frais_enabled": self.pno_frais_enabled,
            "rentabilite_enabled": self.rentabilite_enabled,
            "dashboard_complet": self.dashboard_complet,
        }
```

- [ ] **Step 5: Rewrite PLAN_CATALOG with new plan structure**

Replace the entire `PLAN_CATALOG` dict with the spec's version (section 6.2.2). Key changes:
- FREE: `display_name="Essentiel"`, `is_public=True`, `max_biens=2`
- STARTER: `display_name="Gestion"`, `max_scis=3`, `max_biens=10`, `multi_sci_enabled=True`, `documents_enabled=True`, `notifications_enabled=True`, `dashboard_complet=True`
- PRO: `display_name="Fiscal"`, `max_scis=None`, `max_biens=None`, all features enabled
- Remove LIFETIME entry from PLAN_CATALOG (keep enum value)

**⚠️ Note**: Also update any existing tests in `test_entitlements.py` that assert `max_biens=1` or `display_name="Free"` for the FREE plan — these will break with the new values (`max_biens=2`, `display_name="Essentiel"`).

- [ ] **Step 6: Add lifetime→pro mapping in get_plan()**

```python
def get_plan(plan_key: PlanKey | str) -> PlanEntitlements:
    normalized = plan_key if isinstance(plan_key, PlanKey) else PlanKey(str(plan_key))
    if normalized == PlanKey.LIFETIME:
        normalized = PlanKey.PRO
    return PLAN_CATALOG[normalized]
```

- [ ] **Step 7: Run tests to verify they pass**

Run: `cd backend && PYTHONPATH=. pytest tests/test_entitlements.py -v 2>&1 | tail -20`

Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add backend/app/core/entitlements.py backend/tests/test_entitlements.py
git commit -m "feat: restructure entitlements — Essentiel/Gestion/Fiscal plans, new feature gates"
```

---

### Task 2: Update config.py + resolve functions for annual billing

**Files:**
- Modify: `backend/app/core/config.py`
- Modify: `backend/app/core/entitlements.py`
- Test: `backend/tests/test_entitlements.py`

- [ ] **Step 1: Write failing tests for annual price resolution**

```python
# In tests/test_entitlements.py

def test_resolve_price_id_annual_starter(monkeypatch):
    monkeypatch.setattr(settings, "stripe_starter_annual_price_id", "price_starter_annual")
    result = resolve_price_id_for_plan(PlanKey.STARTER, billing_period="year")
    assert result == "price_starter_annual"


def test_resolve_price_id_monthly_default(monkeypatch):
    monkeypatch.setattr(settings, "stripe_starter_price_id", "price_starter_monthly")
    result = resolve_price_id_for_plan(PlanKey.STARTER)
    assert result == "price_starter_monthly"


def test_resolve_plan_key_from_annual_price(monkeypatch):
    monkeypatch.setattr(settings, "stripe_pro_annual_price_id", "price_pro_annual")
    result = resolve_plan_key_from_price_id("price_pro_annual")
    assert result == PlanKey.PRO


def test_resolve_price_id_lifetime_returns_none():
    result = resolve_price_id_for_plan(PlanKey.LIFETIME)
    assert result is None
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && PYTHONPATH=. pytest tests/test_entitlements.py -v -k "annual" 2>&1 | tail -10`

Expected: FAIL (no `stripe_starter_annual_price_id` attribute, wrong signature)

- [ ] **Step 3: Add annual price ID fields to config.py**

In `backend/app/core/config.py`, after `stripe_lifetime_price_id`:

```python
    stripe_starter_annual_price_id: str = "price_starter_annual_placeholder"
    stripe_pro_annual_price_id: str = "price_pro_annual_placeholder"
```

Add comment on `stripe_lifetime_price_id`:

```python
    stripe_lifetime_price_id: str = "price_lifetime_placeholder"  # DEPRECATED: kept for grandfathered users
```

- [ ] **Step 4: Update resolve_price_id_for_plan with billing_period param**

```python
def resolve_price_id_for_plan(plan_key: PlanKey | str, billing_period: str = "month") -> str | None:
    normalized = plan_key if isinstance(plan_key, PlanKey) else PlanKey(str(plan_key))
    if normalized == PlanKey.STARTER:
        if billing_period == "year":
            return settings.stripe_starter_annual_price_id
        return settings.stripe_starter_price_id
    if normalized == PlanKey.PRO:
        if billing_period == "year":
            return settings.stripe_pro_annual_price_id
        return settings.stripe_pro_price_id
    return None
```

- [ ] **Step 5: Update resolve_plan_key_from_price_id for annual prices**

```python
def resolve_plan_key_from_price_id(price_id: str | None) -> PlanKey | None:
    if not price_id:
        return None
    price_mapping = {
        settings.stripe_starter_price_id: PlanKey.STARTER,
        settings.stripe_starter_annual_price_id: PlanKey.STARTER,
        settings.stripe_pro_price_id: PlanKey.PRO,
        settings.stripe_pro_annual_price_id: PlanKey.PRO,
    }
    return price_mapping.get(price_id)
```

- [ ] **Step 6: Run all entitlements tests**

Run: `cd backend && PYTHONPATH=. pytest tests/test_entitlements.py -v 2>&1 | tail -20`

Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/core/config.py backend/app/core/entitlements.py backend/tests/test_entitlements.py
git commit -m "feat: annual billing support + deprecate lifetime price"
```

---

### Task 3: Database migration — activated_sessions table

**Files:**
- Create: `supabase/migrations/009_auth_activated_sessions.sql`

- [ ] **Step 1: Create migration file**

```sql
-- 009_auth_activated_sessions.sql
-- Table anti-replay pour /activate endpoint (pay-first auth flow)

CREATE TABLE IF NOT EXISTS activated_sessions (
    session_id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES auth.users(id),
    activated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_activated_sessions_activated_at ON activated_sessions(activated_at);

ALTER TABLE activated_sessions ENABLE ROW LEVEL SECURITY;
-- No user policies — only accessible via service_role
```

- [ ] **Step 2: Verify migration syntax**

Run: `cd /Users/radnoumanemossabely/Code/sci-manager-renew && cat supabase/migrations/009_auth_activated_sessions.sql`

Expected: File contents displayed without syntax errors

- [ ] **Step 3: Commit**

```bash
git add supabase/migrations/009_auth_activated_sessions.sql
git commit -m "feat: add activated_sessions table for anti-replay protection"
```

---

## Chunk 2: Backend Stripe + Auth Endpoints

### Task 4: Guest checkout endpoint

**Files:**
- Modify: `backend/app/api/v1/stripe.py`
- Modify: `backend/app/models/stripe.py`
- Test: `backend/tests/test_stripe.py`

- [ ] **Step 1: Write failing tests for guest checkout**

```python
# In tests/test_stripe.py — add

def test_guest_checkout_rejects_free_plan(client):
    response = client.post(
        "/api/v1/stripe/create-guest-checkout",
        json={"plan_key": "free", "billing_period": "month"},
    )
    assert response.status_code == 400


def test_guest_checkout_rejects_invalid_plan(client):
    response = client.post(
        "/api/v1/stripe/create-guest-checkout",
        json={"plan_key": "invalid", "billing_period": "month"},
    )
    assert response.status_code in (400, 422)


def test_guest_checkout_rejects_invalid_billing_period(client):
    response = client.post(
        "/api/v1/stripe/create-guest-checkout",
        json={"plan_key": "starter", "billing_period": "weekly"},
    )
    assert response.status_code in (400, 422)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd backend && PYTHONPATH=. pytest tests/test_stripe.py -v -k "guest_checkout" 2>&1 | tail -10`

Expected: FAIL (404, endpoint doesn't exist)

- [ ] **Step 3: Create GuestCheckoutRequest model + update CheckoutSessionCreateResponse**

In `backend/app/models/stripe.py`, add:

```python
class GuestCheckoutRequest(BaseModel):
    plan_key: str
    billing_period: str = "month"
```

Also add `session_id` to `CheckoutSessionCreateResponse` (the guest checkout returns it for `/welcome` redirect):

```python
class CheckoutSessionCreateResponse(BaseModel):
    url: str
    session_id: str = ""
```

- [ ] **Step 4: Implement guest checkout endpoint**

In `backend/app/api/v1/stripe.py`, add after imports:

```python
from app.models.stripe import GuestCheckoutRequest
```

Add the endpoint (no `Depends(get_current_user)`):

```python
@router.post("/create-guest-checkout", response_model=CheckoutSessionCreateResponse)
@limiter.limit("5/minute")
async def create_guest_checkout(
    request: Request,
    payload: GuestCheckoutRequest,
) -> CheckoutSessionCreateResponse:
    del request
    if not settings.feature_stripe_payments:
        raise FeatureDisabledError("Les paiements Stripe sont désactivés.", flag_name="feature_stripe_payments")

    if payload.plan_key not in ("starter", "pro"):
        raise ValidationError("plan_key must be 'starter' or 'pro'")
    if payload.billing_period not in ("month", "year"):
        raise ValidationError("billing_period must be 'month' or 'year'")

    price_id = resolve_price_id_for_plan(payload.plan_key, billing_period=payload.billing_period)
    if not price_id:
        raise ExternalServiceError("Stripe", "Price ID unavailable for requested plan")

    logger.info("creating_guest_checkout", plan_key=payload.plan_key, billing_period=payload.billing_period)
    stripe.api_key = settings.stripe_secret_key

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=f"{settings.frontend_url}/welcome?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.frontend_url}/#pricing",
            metadata={"plan_key": payload.plan_key, "billing_period": payload.billing_period},
        )
    except stripe.error.StripeError as exc:
        logger.error("guest_checkout_failed", error=str(exc), exc_info=True)
        raise ExternalServiceError("Stripe", f"Checkout session creation failed: {str(exc)}")

    session_url = _to_str(getattr(session, "url", None))
    if not session_url and hasattr(session, "get"):
        session_url = _to_str(session.get("url"))
    session_id = _to_str(getattr(session, "id", None))
    if not session_id and hasattr(session, "get"):
        session_id = _to_str(session.get("id"))

    return CheckoutSessionCreateResponse(url=session_url or "", session_id=session_id or "")
```

- [ ] **Step 5: Update existing checkout success_url and cancel_url**

In the existing `create_checkout_session`, change:
- `success_url` from `/success?session_id=` to `/dashboard?upgraded=true`
- `cancel_url` from `/pricing` to `/#pricing`

- [ ] **Step 6: Run tests**

Run: `cd backend && PYTHONPATH=. pytest tests/test_stripe.py -v 2>&1 | tail -20`

Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/api/v1/stripe.py backend/app/models/stripe.py backend/tests/test_stripe.py
git commit -m "feat: add guest checkout endpoint for pay-first flow"
```

---

### Task 5: Webhook modification — guest flow user creation

**Files:**
- Modify: `backend/app/api/v1/stripe.py`
- Test: `backend/tests/test_stripe.py`

- [ ] **Step 1: Write failing tests for webhook user creation**

```python
# In tests/test_stripe.py

def test_webhook_guest_checkout_creates_user(monkeypatch):
    """When client_reference_id is None, webhook should create user via Supabase Admin"""
    created_users = []

    class FakeAdminAuth:
        def create_user(self, params):
            created_users.append(params)
            return type("User", (), {"user": type("U", (), {"id": "new-user-id"})()})()
        def list_users(self):
            return type("R", (), {"users": []})()

    # Mock Supabase client
    # ... (depends on test harness — use existing fixture pattern from test_stripe.py)

    # Simulate checkout.session.completed with no client_reference_id
    event_data = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "client_reference_id": None,
                "customer": "cus_test",
                "subscription": "sub_test",
                "payment_status": "paid",
                "customer_details": {"email": "new@test.com"},
                "metadata": {"plan_key": "starter", "billing_period": "month"},
            }
        },
    }
    _handle_event(event_data)
    # Assert user was created
    assert len(created_users) == 1
```

- [ ] **Step 2: Implement guest flow in _handle_event**

In `_handle_event`, modify the `checkout.session.completed` handler:

```python
    if event_type == "checkout.session.completed":
        user_id = _to_str(obj.get("client_reference_id"))
        status_value = "active" if obj.get("payment_status") == "paid" else "pending"
        plan_key = _to_str(obj.get("metadata", {}).get("plan_key")) if isinstance(obj.get("metadata"), dict) else None

        # Guest checkout flow: no client_reference_id
        if not user_id:
            customer_details = obj.get("customer_details", {})
            email = customer_details.get("email") if isinstance(customer_details, dict) else None
            if email:
                user_id = _create_or_get_user(email)
                if user_id:
                    # Write user_id to Stripe Subscription metadata for future webhooks
                    sub_id = _to_str(obj.get("subscription"))
                    if sub_id:
                        _update_subscription_metadata(sub_id, user_id, plan_key)
                    # Send welcome email
                    _send_welcome_email_async(email, plan_key)

        if not user_id:
            return

        _sync_subscription(
            {**obj, "client_reference_id": user_id},
            status_value,
            plan_key=plan_key,
        )
        return
```

Add helper functions:

```python
import secrets

def _find_user_by_email(email: str) -> str | None:
    """Look up user by email via direct auth.users query (avoids list_users pagination)."""
    try:
        client = get_supabase_service_client()
        result = client.table("auth.users").select("id").eq("email", email).limit(1).execute()
        if result.data:
            return str(result.data[0]["id"])
    except Exception:
        # Fallback: some Supabase configurations don't allow direct auth.users query
        pass
    return None


def _create_or_get_user(email: str) -> str | None:
    """Create Supabase user if not exists, return user_id"""
    try:
        # Try direct lookup first (O(1) vs O(n) list_users)
        existing_id = _find_user_by_email(email)
        if existing_id:
            return existing_id

        client = get_supabase_service_client()
        # Create new user
        random_password = secrets.token_urlsafe(32)
        result = client.auth.admin.create_user({
            "email": email,
            "password": random_password,
            "email_confirm": True,
        })
        if hasattr(result, "user") and result.user:
            return str(result.user.id)
    except Exception:
        logger.error("guest_user_creation_failed", email=email, exc_info=True)
    return None


def _update_subscription_metadata(sub_id: str, user_id: str, plan_key: str | None) -> None:
    """Write user_id into Stripe Subscription metadata for future webhooks"""
    try:
        stripe.api_key = settings.stripe_secret_key
        metadata = {"user_id": user_id}
        if plan_key:
            metadata["plan_key"] = plan_key
        stripe.Subscription.modify(sub_id, metadata=metadata)
    except Exception:
        logger.error("stripe_subscription_metadata_update_failed", sub_id=sub_id, user_id=user_id, exc_info=True)


def _send_welcome_email_async(email: str, plan_key: str | None) -> None:
    """Fire-and-forget welcome email via background task"""
    try:
        from app.services.email_service import email_service
        import asyncio
        loop = asyncio.get_running_loop()
        # Note: send_welcome signature will be updated in Task 8 to accept plan_name.
        # Until then, pass plan_key as user_name — functionally harmless for email delivery.
        loop.create_task(email_service.send_welcome(email, plan_key or "Gestion"))
    except Exception:
        logger.warning("welcome_email_fire_and_forget_failed", email=email, exc_info=True)
```

- [ ] **Step 3: Add fallback in _sync_subscription for customer.subscription.updated**

In the `customer.subscription.updated` handler, add fallback after building `session_like`:

```python
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
```

- [ ] **Step 4: Run tests**

Run: `cd backend && PYTHONPATH=. pytest tests/test_stripe.py -v 2>&1 | tail -20`

Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/v1/stripe.py backend/tests/test_stripe.py
git commit -m "feat: webhook guest flow — auto-create user + metadata fallback"
```

---

### Task 6: /activate endpoint (anti-replay)

**Files:**
- Modify: `backend/app/api/v1/auth.py`
- Test: `backend/tests/test_auth.py`

- [ ] **Step 1: Write failing tests**

```python
# In tests/test_auth.py — add

def test_activate_missing_session_id(client):
    response = client.get("/api/v1/auth/activate")
    assert response.status_code == 400


def test_activate_invalid_session_id(client):
    response = client.get("/api/v1/auth/activate?session_id=invalid")
    assert response.status_code == 400
```

- [ ] **Step 2: Implement /activate endpoint**

In `backend/app/api/v1/auth.py`, add:

```python
import stripe
from app.core.config import settings
from app.core.supabase_client import get_supabase_service_client


class ActivateResponse(BaseModel):
    token_hash: str
    type: str = "magiclink"
    plan_key: str | None = None


@router.get("/activate", response_model=ActivateResponse)
@limiter.limit("5/minute")
async def activate_session(request: Request, session_id: str | None = None) -> ActivateResponse:
    """Auto-login after Stripe checkout — returns OTP token for frontend verifyOtp"""
    del request
    if not session_id:
        raise ValidationError("session_id is required")

    # 1. Validate with Stripe
    stripe.api_key = settings.stripe_secret_key
    try:
        session = stripe.checkout.Session.retrieve(session_id)
    except stripe.error.StripeError:
        raise ValidationError("Invalid or expired session")

    if session.payment_status != "paid":
        raise ValidationError("Payment not completed")

    # 2. Extract email + plan_key
    email = session.customer_details.email if session.customer_details else None
    if not email:
        raise ValidationError("No email found in session")
    plan_key = session.metadata.get("plan_key") if session.metadata else None

    # 3. Anti-replay: atomic INSERT ... ON CONFLICT
    client = get_supabase_service_client()

    # Check user exists (webhook may be delayed — retry up to 3 times)
    user_id = None
    for attempt in range(3):
        user_id = _find_user_by_email(email)
        if user_id:
            break
        import asyncio
        await asyncio.sleep(2)

    if not user_id:
        raise ExternalServiceError("Supabase", "Account not yet created — please retry")

    # Atomic anti-replay: upsert with on_conflict, then check if row was freshly inserted
    # Use ignoreDuplicates to avoid overwriting existing rows (Supabase PostgREST)
    result = client.table("activated_sessions").upsert(
        {"session_id": session_id, "user_id": user_id},
        on_conflict="session_id",
        ignore_duplicates=True,
    ).execute()
    # If the row already existed, upsert returns empty data (ignore_duplicates=True)
    if not result.data:
        raise AuthenticationError("This activation link has already been used")

    # 4. Generate magic link for auto-login
    link_result = client.auth.admin.generate_link({
        "type": "magiclink",
        "email": email,
    })

    token_hash = ""
    if hasattr(link_result, "properties"):
        token_hash = getattr(link_result.properties, "hashed_token", "")

    logger.info("session_activated", session_id=session_id, user_id=user_id)
    return ActivateResponse(token_hash=token_hash, plan_key=plan_key)
```

- [ ] **Step 3: Run tests**

Run: `cd backend && PYTHONPATH=. pytest tests/test_auth.py -v 2>&1 | tail -20`

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/auth.py backend/tests/test_auth.py
git commit -m "feat: /activate endpoint with anti-replay for pay-first flow"
```

---

### Task 7: /forgot-password endpoint

**Files:**
- Modify: `backend/app/api/v1/auth.py`
- Test: `backend/tests/test_auth.py`

- [ ] **Step 1: Write failing test**

```python
def test_forgot_password_requires_email(client):
    response = client.post("/api/v1/auth/forgot-password", json={})
    assert response.status_code == 422
```

- [ ] **Step 2: Implement endpoint**

In `backend/app/api/v1/auth.py`:

```python
class ForgotPasswordRequest(BaseModel):
    email: EmailStr


@router.post("/forgot-password", response_model=MagicLinkResponse)
@limiter.limit("3/minute")
async def forgot_password(request: Request, payload: ForgotPasswordRequest) -> MagicLinkResponse:
    """Send password reset email via Supabase Auth"""
    del request
    logger.info("forgot_password_requested", email=payload.email)
    try:
        client = get_supabase_service_client()
        client.auth.reset_password_email(payload.email, {
            "redirect_to": f"{settings.frontend_url}/reset-password",
        })
        return MagicLinkResponse(success=True, message="If this email exists, a reset link has been sent.")
    except Exception as e:
        logger.error("forgot_password_error", email=payload.email, error=str(e))
        # Always return success to avoid email enumeration
        return MagicLinkResponse(success=True, message="If this email exists, a reset link has been sent.")
```

- [ ] **Step 3: Run tests + commit**

Run: `cd backend && PYTHONPATH=. pytest tests/test_auth.py -v 2>&1 | tail -20`

```bash
git add backend/app/api/v1/auth.py backend/tests/test_auth.py
git commit -m "feat: /forgot-password endpoint"
```

---

## Chunk 3: Backend Email Templates

### Task 8: Jinja2 email templates

**Files:**
- Create: `backend/templates/emails/base.html`
- Create: `backend/templates/emails/welcome.html`
- Create: `backend/templates/emails/magic_link.html`
- Create: `backend/templates/emails/reset_password.html`
- Create: `backend/templates/emails/quittance.html`
- Create: `backend/templates/emails/subscription.html`
- Modify: `backend/app/services/email_service.py`
- Test: `backend/tests/test_email_service.py`

- [ ] **Step 1: Create templates directory**

Run: `mkdir -p /Users/radnoumanemossabely/Code/sci-manager-renew/backend/templates/emails`

- [ ] **Step 2: Create base.html template**

```html
<!DOCTYPE html>
<html lang="fr">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f4f4f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:40px 0;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:#fff;border-radius:8px;overflow:hidden;">
        <tr><td style="background:#2563eb;padding:24px;text-align:center;">
          <span style="color:#fff;font-size:24px;font-weight:700;">GererSCI</span>
        </td></tr>
        <tr><td style="padding:32px;">
          <p style="color:#374151;font-size:16px;line-height:1.6;">Bonjour,</p>
          {% block content %}{% endblock %}
          {% if cta_url and cta_text %}
          <table width="100%" cellpadding="0" cellspacing="0" style="margin:24px 0;">
            <tr><td align="center">
              <a href="{{ cta_url }}" style="display:inline-block;background:#2563eb;color:#fff;padding:12px 32px;border-radius:6px;text-decoration:none;font-weight:600;font-size:16px;">{{ cta_text }}</a>
            </td></tr>
          </table>
          <p style="color:#9ca3af;font-size:13px;">Si le bouton ne fonctionne pas, copiez ce lien&nbsp;: <a href="{{ cta_url }}" style="color:#2563eb;">{{ cta_url }}</a></p>
          {% endif %}
        </td></tr>
        <tr><td style="background:#f9fafb;padding:16px;text-align:center;border-top:1px solid #e5e7eb;">
          <p style="color:#9ca3af;font-size:12px;margin:0;">GererSCI &middot; gerersci.fr</p>
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>
```

- [ ] **Step 3: Create welcome.html**

```html
{% extends "base.html" %}
{% block content %}
<p style="color:#374151;font-size:16px;line-height:1.6;">Bienvenue sur <strong>GererSCI</strong>&nbsp;!</p>
<p style="color:#374151;font-size:16px;line-height:1.6;">Votre abonnement <strong>{{ plan_name }}</strong> est actif. Vous pouvez dès maintenant gérer vos SCI, suivre vos loyers et générer vos quittances.</p>
{% endblock %}
```

Set `cta_url` to app URL, `cta_text` to "Accéder à mon espace".

- [ ] **Step 4: Create magic_link.html, reset_password.html, quittance.html, subscription.html**

Each extends `base.html`. Template variables for each:

- **magic_link.html**: `{% extends "base.html" %}` — variables: `cta_url` (the magic link URL), `cta_text` = "Se connecter". Content: "Cliquez sur le bouton pour vous connecter à votre espace GererSCI."
- **reset_password.html**: `{% extends "base.html" %}` — variables: `cta_url` (reset link), `cta_text` = "Réinitialiser mon mot de passe". Content: "Vous avez demandé à réinitialiser votre mot de passe. Ce lien expire dans 1 heure."
- **quittance.html**: `{% extends "base.html" %}` — variables: `locataire_name`, `bien_adresse`, `mois`, `cta_url` (download link), `cta_text` = "Télécharger la quittance". Content: "La quittance de loyer de {{ locataire_name }} pour {{ mois }} est disponible."
- **subscription.html**: `{% extends "base.html" %}` — variables: `plan_name`, `cta_url` (dashboard link), `cta_text` = "Accéder à mon espace". Content: "Votre abonnement {{ plan_name }} est confirmé."

- [ ] **Step 5: Refactor email_service.py to use file templates**

Replace inline `Template(...)` calls with `jinja2.Environment(loader=FileSystemLoader("templates/emails"))`:

```python
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "emails"
_jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=True)


def _render_template(template_name: str, **kwargs) -> str:
    template = _jinja_env.get_template(template_name)
    return template.render(**kwargs)
```

Then replace each method's inline template with `_render_template("welcome.html", plan_name=plan, ...)`.

**⚠️ Signature change**: Update `send_welcome(self, email: str, user_name: str)` to `send_welcome(self, email: str, plan_name: str)`. This aligns with the `welcome.html` template variable and with the call in Task 5's `_send_welcome_email_async`. Update all callers of `send_welcome` accordingly.

- [ ] **Step 6: Write test for template rendering**

```python
# In tests/test_email_service.py
def test_render_welcome_template():
    from app.services.email_service import _render_template
    html = _render_template("welcome.html", plan_name="Gestion", cta_url="https://app.gerersci.fr", cta_text="Accéder")
    assert "Gestion" in html
    assert "GererSCI" in html
```

- [ ] **Step 7: Run tests + commit**

Run: `cd backend && PYTHONPATH=. pytest tests/test_email_service.py -v 2>&1 | tail -10`

```bash
git add backend/templates/ backend/app/services/email_service.py backend/tests/test_email_service.py
git commit -m "feat: branded Jinja2 email templates replacing inline HTML"
```

---

## Chunk 4: Frontend Auth Pages

### Task 9: Route guard updates

**Files:**
- Modify: `frontend/src/lib/auth/route-guard.ts`

- [ ] **Step 1: Update route guard**

```typescript
const PROTECTED_ROUTE_PREFIXES = [
	'/account',
	'/settings',
	'/admin',
	'/onboarding'
];
// Removed: '/success' (deleted page)

const GUEST_ONLY_ROUTE_PREFIXES = ['/login', '/register'];

const PUBLIC_ROUTE_PREFIXES = ['/forgot-password', '/reset-password', '/welcome'];
// /welcome is "semi-protected" — page validates session_id itself

export function isPublicRoute(pathname: string) {
	return PUBLIC_ROUTE_PREFIXES.some((routePrefix) => matchesRoutePrefix(pathname, routePrefix));
}
```

- [ ] **Step 2: Wire `isPublicRoute` into layout auth logic**

In the consumer of route-guard (likely `frontend/src/routes/+layout.svelte` or `(app)/+layout.ts`), import `isPublicRoute` and skip auth redirects for public routes. The existing logic checks `isProtectedRoute()` and `isGuestOnlyRoute()` — add a check: if `isPublicRoute(pathname)`, allow through without auth.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/auth/route-guard.ts
git commit -m "feat: update route guard — add auth pages, remove /success"
```

---

### Task 10: Login page redesign

**Files:**
- Modify: `frontend/src/routes/login/+page.svelte`

- [ ] **Step 1: Rewrite login page**

Replace magic-link-only UI with:
- Email + password form (primary)
- "Connexion sans mot de passe" collapsible (magic link fallback)
- "Mot de passe oublié ?" link → `/forgot-password`
- "Pas encore de compte ? Voir les tarifs →" link → `/#pricing`

Use `supabase.auth.signInWithPassword({email, password})` as primary.
Keep `supabase.auth.signInWithOtp({email})` as fallback.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/routes/login/+page.svelte
git commit -m "feat: login page — email/password primary + magic link fallback"
```

---

### Task 11: Register page (free tier)

**Files:**
- Create: `frontend/src/routes/register/+page.svelte`

- [ ] **Step 1: Create register page**

Create `+page.ts` with `export const prerender = false; export const ssr = false;`.

Simple form: email + password + confirm password.
Call `supabase.auth.signUp({email, password})`.
On success → redirect `/onboarding`.
Link to `/#pricing` for paid plans.
Add `<svelte:head>` with title "Créer un compte | GererSCI".

- [ ] **Step 2: Commit**

```bash
git add frontend/src/routes/register/+page.svelte
git commit -m "feat: register page for free tier signup"
```

---

### Task 12: Welcome page (post-payment)

**Files:**
- Create: `frontend/src/routes/welcome/+page.svelte`
- Create: `frontend/src/routes/welcome/+page.ts`

- [ ] **Step 1: Create +page.ts to extract session_id**

```typescript
import type { PageLoad } from './$types';
import { redirect } from '@sveltejs/kit';

export const prerender = false;
export const ssr = false;

export const load: PageLoad = ({ url }) => {
	const sessionId = url.searchParams.get('session_id');
	if (!sessionId) {
		throw redirect(302, '/#pricing');
	}
	return { sessionId };
};
```

- [ ] **Step 2: Create +page.svelte**

States (check in this order):
0. **First**: Check if user already has an active Supabase session (`supabase.auth.getSession()`). If yes → redirect `/dashboard` immediately. Do NOT call `/activate`.
1. Loading: call `/api/v1/auth/activate?session_id=XXX`
3. On success: call `supabase.auth.verifyOtp({token_hash, type: "magiclink"})` → show password creation form
4. On 409: "Ce lien a déjà été utilisé" + link to `/login`
5. On 503: "Compte en cours de création..." + auto-retry
6. On error: "Lien invalide" + link to `/#pricing`

Password form: calls `supabase.auth.updateUser({password})`, then redirects to `/onboarding`.

- [ ] **Step 3: Add activateSession to api.ts**

```typescript
export async function activateSession(sessionId: string) {
	return apiFetch<{ token_hash: string; type: string; plan_key: string | null }>(
		`/api/v1/auth/activate?session_id=${encodeURIComponent(sessionId)}`,
		{ method: 'GET' }
	);
}

export async function createGuestCheckout(planKey: string, billingPeriod: string = 'month') {
	return apiFetch<{ url: string; session_id: string }>(
		'/api/v1/stripe/create-guest-checkout',
		{ method: 'POST', body: JSON.stringify({ plan_key: planKey, billing_period: billingPeriod }) }
	);
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/routes/welcome/ frontend/src/lib/api.ts
git commit -m "feat: welcome page — post-payment auto-login + password creation"
```

---

### Task 13: Forgot-password + Reset-password pages

**Files:**
- Create: `frontend/src/routes/forgot-password/+page.svelte`
- Create: `frontend/src/routes/reset-password/+page.svelte`
- Create: `frontend/src/routes/reset-password/+page.ts`

- [ ] **Step 1: Create forgot-password page**

Create `+page.ts` with `export const prerender = false;`.

Simple form: email input.
Call `supabase.auth.resetPasswordForEmail(email, {redirectTo: origin + '/reset-password'})`.
Show "Si cet email existe, un lien a été envoyé."

- [ ] **Step 2: Create reset-password page**

```typescript
// +page.ts
export const prerender = false;
export const ssr = false;
```

Page: password + confirm inputs.
Call `supabase.auth.updateUser({password})`.
On success → redirect `/login` with toast.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/routes/forgot-password/ frontend/src/routes/reset-password/
git commit -m "feat: forgot-password + reset-password pages"
```

---

### Task 14: Account page — security section

**Files:**
- Modify: `frontend/src/routes/(app)/account/+page.svelte`

- [ ] **Step 1: Add password change section**

Add a "Sécurité" section with:
- Current password (optional — for users who set one)
- New password + confirm
- Call `supabase.auth.updateUser({password})`
- Success toast

- [ ] **Step 2: Commit**

```bash
git add frontend/src/routes/\(app\)/account/+page.svelte
git commit -m "feat: account page — change password section"
```

---

## Chunk 5: Frontend Landing + Pricing + SEO

### Task 15: Landing page refonte with integrated pricing

**Files:**
- Modify: `frontend/src/routes/+page.svelte`

- [ ] **Step 1: Rewrite landing page**

9 sections per spec §5.1:
1. Hero: H1 + CTA with price + trust bar
2. Problem (before/after)
3. Demo placeholder
4. Features (4 cards)
5. Audiences (3 tabs)
6. Pricing (section id="pricing") with 3 tiers + annual toggle
7. Testimonials
8. FAQ (accordion)
9. CTA final

Pricing section pulls from static plan data (not API — prerendered page).
CTA buttons: paid plans → call `createGuestCheckout(planKey, billingPeriod)` from `$lib/api.ts` (added in Task 12 Step 3), free tier → link to `/register`.

**Note**: Since the landing page is prerendered, the CTA click handlers must be client-side JS that calls the API at runtime (not at build time). Use `onclick` handlers that call `createGuestCheckout` and redirect to `data.url`.

- [ ] **Step 2: Add prerender + SEO meta**

```typescript
// +page.ts
export const prerender = true;
```

Add `<svelte:head>` with title, description, OG tags, canonical URL.
Add Schema.org JSON-LD (SoftwareApplication + FAQPage).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/routes/+page.svelte frontend/src/routes/+page.ts
git commit -m "feat: landing page refonte — one-page with integrated pricing + SEO"
```

---

### Task 16: /pricing redirect + /success cleanup

**Files:**
- Modify: `frontend/src/routes/pricing/+page.svelte` → redirect
- Delete: `frontend/src/routes/success/` (if exists)
- Modify: `frontend/src/routes/(app)/+layout.ts` → change redirect target

- [ ] **Step 1: Replace /pricing with redirect**

Create `frontend/src/routes/pricing/+page.server.ts`:

```typescript
import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = () => {
	throw redirect(301, '/#pricing');
};
```

Remove or empty `+page.svelte` (keep minimal to avoid build error).

- [ ] **Step 2: Update (app)/+layout.ts redirect**

Change paywall redirect from `'/pricing'` to `'/#pricing'`.

**Note**: `redirect(302, '/#pricing')` works on client-side (SvelteKit CSR navigation). Verify that free tier users (`plan_key: "free"`) have `is_active: true` from `fetchSubscriptionEntitlements()` so they are NOT redirected. If the backend returns `is_active: false` for users with no Stripe subscription, this must be fixed in `subscription_service.py` to treat `free` as active.

- [ ] **Step 3: Delete /success route if exists**

- [ ] **Step 4: Commit**

```bash
git add frontend/src/routes/pricing/ frontend/src/routes/\(app\)/+layout.ts
git commit -m "feat: /pricing → /#pricing redirect, update paywall redirect"
```

---

### Task 17: SEO files

**Files:**
- Create: `frontend/static/robots.txt`
- Create: `frontend/src/routes/sitemap.xml/+server.ts`
- Modify: `frontend/src/app.html`
- Modify: `frontend/src/routes/+layout.svelte` (guest nav)

- [ ] **Step 1: Create robots.txt**

```
User-agent: *
Allow: /
Disallow: /dashboard
Disallow: /scis
Disallow: /onboarding
Disallow: /admin
Disallow: /settings
Disallow: /account
Disallow: /welcome
Disallow: /register
Disallow: /forgot-password
Disallow: /reset-password
Disallow: /auth
Sitemap: https://gerersci.fr/sitemap.xml
```

- [ ] **Step 2: Create sitemap.xml server route**

```typescript
// frontend/src/routes/sitemap.xml/+server.ts
import type { RequestHandler } from './$types';

const PAGES = ['/', '/login', '/cgu', '/mentions-legales', '/confidentialite'];

export const GET: RequestHandler = () => {
	const body = `<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
${PAGES.map(
	(page) => `  <url>
    <loc>https://gerersci.fr${page}</loc>
    <changefreq>monthly</changefreq>
  </url>`
).join('\n')}
</urlset>`;

	return new Response(body, {
		headers: { 'Content-Type': 'application/xml' }
	});
};

export const prerender = true;
```

- [ ] **Step 3: Verify Paraglide lang default is fr-FR**

**⚠️ DO NOT hardcode `lang="fr-FR"` in `app.html`** — it uses `%paraglide.lang%` and `%paraglide.dir%` for i18n. Instead, verify that Paraglide's default locale is `fr` or `fr-FR` in the Paraglide config (likely `project.inlang/settings.json` or `vite.config.ts` paraglide plugin options). If the default locale is already `fr`, no change needed.

- [ ] **Step 4: Simplify guest navigation in +layout.svelte**

For non-authenticated users, show minimal nav: Logo + "Tarifs" (anchor to `/#pricing`) + "Connexion" (`/login`).

- [ ] **Step 5: Commit**

```bash
git add frontend/static/robots.txt frontend/src/routes/sitemap.xml/ frontend/src/app.html frontend/src/routes/+layout.svelte
git commit -m "feat: SEO — robots.txt, sitemap, lang attr, guest nav"
```

---

## Chunk 6: Verification

### Task 18: Run full test suites

- [ ] **Step 1: Backend tests**

Run: `cd backend && PYTHONPATH=. pytest --cov=app --cov-report=term-missing -q 2>&1 | tail -20`

Expected: ≥82% coverage, no failures

- [ ] **Step 2: Frontend type check**

Run: `cd frontend && pnpm run check 2>&1 | tail -10`

Expected: No errors

- [ ] **Step 3: Frontend high-value tests**

Run: `cd frontend && pnpm run test:high-value 2>&1 | tail -10`

Expected: ≥98% coverage on high-value modules

- [ ] **Step 4: Address any failures**

Fix any test failures or type errors introduced by the changes.

- [ ] **Step 5: Final commit if fixes needed**

```bash
git add <specific changed files>
git commit -m "fix: address test failures from auth+landing redesign"
```

**⚠️ Do NOT use `git add -A`** — stage only the specific files that were fixed to avoid committing unintended changes.
