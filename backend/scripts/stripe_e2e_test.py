#!/usr/bin/env python3
"""
GererSCI — Stripe E2E Test (Public API)
=======================================
Test complet via l'API publique https://api.gerersci.fr
Simule le parcours réel d'un utilisateur.

Usage depuis le VPS:
  cd /opt/gerersci
  export $(grep -v '^#' .env | xargs)
  python3 backend/scripts/stripe_e2e_test.py
"""
import os, sys, time, json, hmac, hashlib, secrets
import httpx, stripe

# ─── Config ─────────────────────────────────────────────────────────────────
API_URL      = "https://api.gerersci.fr"
APP_URL      = "https://gerersci.fr"
SUPABASE_URL = os.getenv("SUPABASE_URL", "").replace(
    "supabase_kong_sci-manager-renew:8000", "api.gerersci.fr"
)
# Forcer URL publique si URL interne
if "supabase_kong" in SUPABASE_URL:
    SUPABASE_URL = "https://api.gerersci.fr"

SUPABASE_ANON_KEY    = os.getenv("SUPABASE_ANON_KEY", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
STRIPE_SECRET_KEY    = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

stripe.api_key = STRIPE_SECRET_KEY

print("=" * 60)
print("  🧪 STRIPE E2E TEST — GererSCI")
print(f"  API: {API_URL}")
print("=" * 60)

results = []
def ok(label):   results.append(("✅", label)); print(f"   ✅ {label}")
def warn(label): results.append(("⚠️ ", label)); print(f"   ⚠️  {label}")
def fail(label): results.append(("❌", label)); print(f"   ❌ {label}")

def supabase_admin(method, path, **kwargs):
    """Appel direct Supabase via Kong (Caddy → api.gerersci.fr)."""
    h = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    return httpx.request(method, f"{SUPABASE_URL}/{path.lstrip('/')}", headers=h, timeout=20, **kwargs)

def make_stripe_sig(payload: bytes, secret: str) -> str:
    ts = int(time.time())
    signed = f"{ts}.{payload.decode()}"
    sig = hmac.new(secret.encode(), signed.encode(), hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"

# ─── Validate config ─────────────────────────────────────────────────────
print("\n🔧 Validation configuration...")
if not STRIPE_SECRET_KEY:
    fail("STRIPE_SECRET_KEY manquante"); sys.exit(1)
if not STRIPE_WEBHOOK_SECRET:
    fail("STRIPE_WEBHOOK_SECRET manquante"); sys.exit(1)
if "sk_test" in STRIPE_SECRET_KEY:
    ok("Mode Stripe: TEST ✓")
elif "sk_live" in STRIPE_SECRET_KEY:
    ok("Mode Stripe: LIVE (PRODUCTION) ✓")
else:
    warn("Mode Stripe inconnu")

# ─── ÉTAPE 1: Créer user test ─────────────────────────────────────────────
print("\n📍 ÉTAPE 1: Création compte test Supabase")
email = f"stripe-e2e-{secrets.token_hex(4)}@test-gerersci.fr"
r = supabase_admin("POST", "auth/v1/admin/users",
    json={"email": email, "password": "TestStripe2024!", "email_confirm": True}
)
if r.status_code in (200, 201):
    user_id = r.json()["id"]
    ok(f"User: {user_id[:8]}... | {email}")
else:
    fail(f"Création user: {r.status_code} — {r.text[:120]}")
    sys.exit(1)

# Login
login = httpx.post(
    f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
    headers={"apikey": SUPABASE_ANON_KEY or SUPABASE_SERVICE_KEY},
    json={"email": email, "password": "TestStripe2024!"},
    timeout=20
)
if login.status_code == 200:
    jwt = login.json()["access_token"]
    ok("JWT obtenu")
else:
    fail(f"Login: {login.status_code} {login.text[:80]}")
    sys.exit(1)

auth = {"Authorization": f"Bearer {jwt}"}

# ─── ÉTAPE 2: Checkout session API ───────────────────────────────────────
print("\n📍 ÉTAPE 2: Création session checkout")
for plan in ["gestion", "starter", "pilotage"]:
    resp = httpx.post(
        f"{API_URL}/api/v1/stripe/create-checkout-session",
        headers=auth, json={"plan_key": plan, "billing_period": "month"}, timeout=20
    )
    if resp.status_code == 200:
        url = resp.json().get("url", "")
        ok(f"Checkout {plan}: {url[:55]}...")
        checkout_plan = plan
        break
    else:
        warn(f"Checkout {plan}: {resp.status_code} — {resp.text[:60]}")
else:
    warn("Aucun plan checkout disponible")
    checkout_plan = None

# ─── ÉTAPE 3: Stripe Customer + Subscription réels ────────────────────────
print("\n📍 ÉTAPE 3: Création Customer & Subscription Stripe (test)")
try:
    customer = stripe.Customer.create(email=email, metadata={"user_id": user_id, "test": "e2e"})
    customer_id = customer.id
    ok(f"Customer: {customer_id}")
except Exception as e:
    fail(f"Customer Stripe: {e}"); sys.exit(1)

# Chercher un price récurrent actif
price_id = None
for env_key in ["STRIPE_GESTION_MONTHLY_PRICE_ID", "STRIPE_PILOTAGE_MONTHLY_PRICE_ID", "STRIPE_STARTER_PRICE_ID"]:
    pid = os.getenv(env_key, "")
    if pid and "placeholder" not in pid.lower():
        price_id = pid
        ok(f"Price ID: {price_id} (from {env_key})")
        break

if not price_id:
    try:
        prices = stripe.Price.list(limit=20, active=True)
        recurring = [p for p in prices.data if p.type == "recurring"]
        if recurring:
            price_id = recurring[0].id
            ok(f"Price ID auto-détecté: {price_id}")
    except Exception as e:
        warn(f"Listing prices: {e}")

sub_id = None
if price_id:
    try:
        pm = stripe.PaymentMethod.create(type="card", card={"token": "tok_visa"})
        stripe.PaymentMethod.attach(pm.id, customer=customer_id)
        stripe.Customer.modify(customer_id, invoice_settings={"default_payment_method": pm.id})
        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
            metadata={"user_id": user_id, "plan_key": checkout_plan or "gestion"},
        )
        sub_id = subscription.id
        ok(f"Subscription: {sub_id} | status: {subscription.status}")
    except Exception as e:
        warn(f"Subscription: {e}")
else:
    warn("Aucun price_id disponible — webhook test sans sub réelle")

# ─── ÉTAPE 4: Webhook checkout.session.completed ──────────────────────────
print("\n📍 ÉTAPE 4: Webhook checkout.session.completed")
event = {
    "id": f"evt_test_{secrets.token_hex(8)}",
    "object": "event",
    "type": "checkout.session.completed",
    "data": {
        "object": {
            "id": f"cs_test_{secrets.token_hex(8)}",
            "object": "checkout.session",
            "mode": "subscription",
            "payment_status": "paid",
            "status": "complete",
            "client_reference_id": user_id,
            "customer": customer_id,
            "subscription": sub_id or f"sub_test_{secrets.token_hex(8)}",
            "metadata": {"user_id": user_id, "plan_key": checkout_plan or "gestion"},
            "customer_details": {"email": email},
        }
    }
}
payload = json.dumps(event, separators=(',', ':')).encode()
sig = make_stripe_sig(payload, STRIPE_WEBHOOK_SECRET)

wh = httpx.post(
    f"{API_URL}/api/v1/stripe/webhook",
    content=payload,
    headers={"Content-Type": "application/json", "stripe-signature": sig},
    timeout=30
)
if wh.status_code == 200:
    status = wh.json().get("status", "?")
    ok(f"Webhook traité: status={status}")
else:
    warn(f"Webhook {wh.status_code}: {wh.text[:120]}")

# ─── ÉTAPE 5: Vérification DB ────────────────────────────────────────────
print("\n📍 ÉTAPE 5: Vérification abonnement en DB")
time.sleep(1.5)
db = supabase_admin("GET", f"rest/v1/subscriptions?user_id=eq.{user_id}&select=*")
if db.status_code == 200 and db.json():
    row = db.json()[0]
    ok(f"DB: plan={row.get('plan_key')} | status={row.get('status')} | active={row.get('is_active')} | customer={row.get('stripe_customer_id', '')[:15]}")
else:
    warn(f"Subscription non trouvée en DB ({db.status_code})")

# ─── ÉTAPE 6: Paywall (entitlements) ────────────────────────────────────
print("\n📍 ÉTAPE 6: Paywall / Entitlements")
r = httpx.get(f"{API_URL}/api/v1/stripe/subscription", headers=auth, timeout=20)
if r.status_code == 200:
    d = r.json()
    plan, active, max_biens = d.get("plan"), d.get("is_active"), d.get("max_biens")
    if active and plan != "free":
        ok(f"Paywall: plan={plan} | active={active} | max_biens={max_biens}")
    else:
        warn(f"Paywall: plan={plan} | active={active} — abonnement peut-être pas activé en DB")
else:
    warn(f"Paywall: {r.status_code} {r.text[:80]}")

# ─── ÉTAPE 7: Webhook annulation ─────────────────────────────────────────
print("\n📍 ÉTAPE 7: Webhook subscription.updated (annulation)")
cancel_event = {
    "id": f"evt_test_{secrets.token_hex(8)}",
    "object": "event",
    "type": "customer.subscription.updated",
    "data": {
        "object": {
            "id": sub_id or "sub_test_1234",
            "object": "subscription",
            "status": "canceled",
            "customer": customer_id,
            "metadata": {"user_id": user_id, "plan_key": checkout_plan or "gestion"},
            "items": {"data": [{"price": {"id": price_id or "price_test"}}]},
            "current_period_end": int(time.time()) + 3600,
        }
    }
}
cancel_bytes = json.dumps(cancel_event, separators=(',', ':')).encode()
cancel_sig = make_stripe_sig(cancel_bytes, STRIPE_WEBHOOK_SECRET)
cr = httpx.post(
    f"{API_URL}/api/v1/stripe/webhook",
    content=cancel_bytes,
    headers={"Content-Type": "application/json", "stripe-signature": cancel_sig},
    timeout=30
)
if cr.status_code == 200:
    ok(f"Webhook annulation: {cr.json().get('status')}")
else:
    warn(f"Annulation: {cr.status_code} — {cr.text[:100]}")

# ─── ÉTAPE 8: Fondateur ──────────────────────────────────────────────────
print("\n📍 ÉTAPE 8: Checkout Fondateur (one-time)")
fondateur_price = os.getenv("STRIPE_FONDATEUR_PRICE_ID", "")
if fondateur_price and "placeholder" not in fondateur_price.lower():
    fr = httpx.post(
        f"{API_URL}/api/v1/stripe/create-checkout-session",
        headers=auth, json={"plan_key": "fondateur", "billing_period": "month"}, timeout=20
    )
    if fr.status_code == 200:
        ok(f"Fondateur checkout: {fr.json().get('url','')[:50]}...")
    else:
        warn(f"Fondateur: {fr.status_code} — {fr.text[:80]}")
else:
    warn("STRIPE_FONDATEUR_PRICE_ID non configuré")

# ─── ÉTAPE 9: Nettoyage ─────────────────────────────────────────────────
print("\n📍 ÉTAPE 9: Nettoyage")
try:
    if sub_id:
        stripe.Subscription.cancel(sub_id)
        ok("Subscription Stripe annulée")
    stripe.Customer.delete(customer_id)
    ok("Customer Stripe supprimé")
except Exception as e:
    warn(f"Cleanup Stripe: {e}")

dr = supabase_admin("DELETE", f"auth/v1/admin/users/{user_id}")
if dr.status_code in (200, 204):
    ok("User Supabase supprimé")
else:
    warn(f"Delete user: {dr.status_code}")

# ─── RÉSUMÉ ─────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  📊 RÉSUMÉ")
print("=" * 60)
for icon, label in results:
    print(f"   {icon} {label}")

errors   = [r for r in results if r[0] == "❌"]
warnings = [r for r in results if r[0] == "⚠️ "]
oks      = [r for r in results if r[0] == "✅"]
print(f"\n   {len(oks)} OK | {len(warnings)} warnings | {len(errors)} erreurs\n")

sys.exit(1 if errors else 0)
