# Demo-First "Full Steak" Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let new users explore a fully-loaded dashboard with demo data before paying — Hormozi's "give them the full steak" — with credibility loading screens, a persistent demo banner, and locked write actions that prompt upgrade.

**Architecture:** Backend seeds realistic demo data (1 SCI, 2 biens, loyers, charges) on first login. Frontend bypasses the paywall for demo users, wraps all write actions with a lock overlay, and shows a persistent upgrade banner. Stripe webhook cleans up demo data on subscription activation. A credibility loading page (`/welcome`) with choreographed animation plays on first visit.

**Tech Stack:** FastAPI + Supabase (PostgreSQL migrations, RLS), SvelteKit 2 + Svelte 5 runes, Tailwind CSS 4, Stripe webhooks

**Spec:** `docs/superpowers/specs/2026-03-28-demo-first-full-steak-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `supabase/migrations/025_demo_data_support.sql` | Create | Add `is_demo` column to entity tables + `demo_seeded` to subscriptions |
| `backend/app/api/v1/demo.py` | Create | `POST /demo/seed` and `DELETE /demo/cleanup` endpoints |
| `backend/app/services/demo_service.py` | Create | Business logic: seed realistic data, cleanup demo rows |
| `backend/app/api/v1/stripe.py` | Modify | Call demo cleanup in `checkout.session.completed` handler |
| `backend/app/main.py` | Modify | Register demo router |
| `frontend/src/lib/api/demo.ts` | Create | `seedDemo()` and `cleanupDemo()` API functions |
| `frontend/src/lib/api/index.ts` | Modify | Re-export demo module |
| `frontend/src/lib/components/DemoBanner.svelte` | Create | Persistent amber banner for demo users |
| `frontend/src/lib/components/LockedAction.svelte` | Create | Wrapper that shows lock icon + intercepts click for demo users |
| `frontend/src/lib/components/UpgradePrompt.svelte` | Create | Modal shown when demo user clicks locked action |
| `frontend/src/routes/welcome/+page.svelte` | Create | Credibility loading screen (Kayak-style) |
| `frontend/src/routes/(app)/+layout.ts` | Modify | Bypass paywall for demo users, redirect to /welcome if not seeded |
| `frontend/src/routes/(app)/+layout.svelte` | Modify | Add DemoBanner when `!is_active` |
| Multiple `(app)` pages | Modify | Wrap write buttons with LockedAction |

---

## Task 1: Database Migration

**Files:**
- Create: `supabase/migrations/025_demo_data_support.sql`

- [ ] **Step 1: Create the migration file**

```sql
-- 025_demo_data_support.sql
-- Add is_demo flag to entity tables for demo data lifecycle management

ALTER TABLE sci ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
ALTER TABLE biens ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
ALTER TABLE baux ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
ALTER TABLE loyers ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
ALTER TABLE charges ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
ALTER TABLE locataires ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
ALTER TABLE assurance_pno ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;
ALTER TABLE associes ADD COLUMN IF NOT EXISTS is_demo BOOLEAN DEFAULT FALSE;

-- Flag on subscriptions to track if demo has been seeded
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS demo_seeded BOOLEAN DEFAULT FALSE;

-- Partial indexes for fast cleanup (only index demo=true rows)
CREATE INDEX IF NOT EXISTS idx_sci_is_demo ON sci(is_demo) WHERE is_demo = TRUE;
CREATE INDEX IF NOT EXISTS idx_biens_is_demo ON biens(is_demo) WHERE is_demo = TRUE;
CREATE INDEX IF NOT EXISTS idx_loyers_is_demo ON loyers(is_demo) WHERE is_demo = TRUE;
CREATE INDEX IF NOT EXISTS idx_charges_is_demo ON charges(is_demo) WHERE is_demo = TRUE;
```

- [ ] **Step 2: Apply migration locally**

Run: `cd /Users/radnoumanemossabely/Code/sci-manager-renew && npx supabase db push 2>&1 | tail -5`

If Supabase CLI is not set up locally, the migration will be applied on next deploy. Verify the file exists:
Run: `ls supabase/migrations/025_demo_data_support.sql`

- [ ] **Step 3: Commit**

```bash
git add supabase/migrations/025_demo_data_support.sql
git commit -m "feat(db): add is_demo columns + demo_seeded flag for demo data lifecycle"
```

---

## Task 2: Demo Seed Service (Backend)

**Files:**
- Create: `backend/app/services/demo_service.py`

- [ ] **Step 1: Create the demo service**

```python
"""Service for seeding and cleaning up demo data."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import structlog

logger = structlog.get_logger(__name__)


def _month_ago(months: int) -> str:
    """Return YYYY-MM-DD string for N months ago, day 05."""
    now = datetime.now(UTC)
    year = now.year
    month = now.month - months
    while month <= 0:
        month += 12
        year -= 1
    return f"{year}-{month:02d}-05"


def _next_month_first() -> str:
    """Return YYYY-MM-DD for the 1st of next month."""
    now = datetime.now(UTC)
    if now.month == 12:
        return f"{now.year + 1}-01-01"
    return f"{now.year}-{now.month + 1:02d}-01"


async def seed_demo_data(client, user_id: str) -> dict:
    """Seed a full set of realistic demo data for a new user.

    Creates: 1 SCI, 2 biens, baux, locataires, 6+ months of loyers, charges, PNO.
    All records marked with is_demo=True for easy cleanup.
    """
    logger.info("demo_seed_start", user_id=user_id)

    # --- SCI ---
    sci_id = str(uuid.uuid4())
    client.table("sci").insert({
        "id": sci_id,
        "nom": "SCI Résidence Belleville",
        "siren": "823456789",
        "regime_fiscal": "IR",
        "capital_social": 150000,
        "forme_juridique": "SCI",
        "nom_gerant": "Vous (démonstration)",
        "is_demo": True,
    }).execute()

    # --- Associé (user = gérant 100%) ---
    client.table("associes").insert({
        "id": str(uuid.uuid4()),
        "id_sci": sci_id,
        "user_id": user_id,
        "nom": "Gérant Démonstration",
        "email": "demo@gerersci.fr",
        "role": "gerant",
        "parts": 100,
        "is_demo": True,
    }).execute()

    # --- Bien 1: T3 Lyon 7e ---
    bien1_id = str(uuid.uuid4())
    client.table("biens").insert({
        "id": bien1_id,
        "id_sci": sci_id,
        "adresse": "45 avenue Jean Jaurès",
        "ville": "Lyon",
        "code_postal": "69007",
        "type_bien": "appartement",
        "type_locatif": "nu",
        "surface_m2": 65,
        "nb_pieces": 3,
        "dpe_classe": "C",
        "loyer_cc": 850,
        "charges": 50,
        "prix_acquisition": 185000,
        "is_demo": True,
    }).execute()

    # --- Bien 2: Studio Lyon 2e ---
    bien2_id = str(uuid.uuid4())
    client.table("biens").insert({
        "id": bien2_id,
        "id_sci": sci_id,
        "adresse": "12 rue Victor Hugo",
        "ville": "Lyon",
        "code_postal": "69002",
        "type_bien": "appartement",
        "type_locatif": "meuble",
        "surface_m2": 28,
        "nb_pieces": 1,
        "dpe_classe": "D",
        "loyer_cc": 620,
        "charges": 40,
        "prix_acquisition": 95000,
        "is_demo": True,
    }).execute()

    # --- Locataire 1 ---
    loc1_id = str(uuid.uuid4())
    client.table("locataires").insert({
        "id": loc1_id,
        "id_bien": bien1_id,
        "nom": "Lefèvre",
        "prenom": "Marie",
        "email": "marie.lefevre@demo.gerersci.fr",
        "telephone": "06 12 34 56 78",
        "date_debut": _month_ago(8),
        "is_demo": True,
    }).execute()

    # --- Locataire 2 ---
    loc2_id = str(uuid.uuid4())
    client.table("locataires").insert({
        "id": loc2_id,
        "id_bien": bien2_id,
        "nom": "Durand",
        "prenom": "Thomas",
        "email": "thomas.durand@demo.gerersci.fr",
        "telephone": "07 98 76 54 32",
        "date_debut": _month_ago(3),
        "is_demo": True,
    }).execute()

    # --- Bail 1 (Bien 1, 8 months ago) ---
    bail1_id = str(uuid.uuid4())
    client.table("baux").insert({
        "id": bail1_id,
        "id_bien": bien1_id,
        "date_debut": _month_ago(8),
        "loyer_hc": 800,
        "charges_locatives": 50,
        "statut": "en_cours",
        "is_demo": True,
    }).execute()
    # Link locataire to bail
    client.table("bail_locataires").insert({
        "id_bail": bail1_id,
        "id_locataire": loc1_id,
    }).execute()

    # --- Bail 2 (Bien 2, 3 months ago) ---
    bail2_id = str(uuid.uuid4())
    client.table("baux").insert({
        "id": bail2_id,
        "id_bien": bien2_id,
        "date_debut": _month_ago(3),
        "loyer_hc": 580,
        "charges_locatives": 40,
        "statut": "en_cours",
        "is_demo": True,
    }).execute()
    client.table("bail_locataires").insert({
        "id_bail": bail2_id,
        "id_locataire": loc2_id,
    }).execute()

    # --- Loyers Bien 1 (6 months: 4 payés, 1 en attente, 1 en retard) ---
    loyer_statuses_1 = [
        (_month_ago(6), "paye", _month_ago(6)),
        (_month_ago(5), "paye", _month_ago(5)),
        (_month_ago(4), "paye", _month_ago(4)),
        (_month_ago(3), "paye", _month_ago(3)),
        (_month_ago(2), "en_retard", None),
        (_month_ago(1), "en_attente", None),
    ]
    for date_loyer, statut, date_paiement in loyer_statuses_1:
        row = {
            "id": str(uuid.uuid4()),
            "id_bien": bien1_id,
            "montant": 850,
            "statut": statut,
            "date_loyer": date_loyer,
            "id_locataire": loc1_id,
            "is_demo": True,
        }
        if date_paiement:
            row["date_paiement"] = date_paiement
        client.table("loyers").insert(row).execute()

    # --- Loyers Bien 2 (3 months: 2 payés, 1 en attente) ---
    loyer_statuses_2 = [
        (_month_ago(3), "paye", _month_ago(3)),
        (_month_ago(2), "paye", _month_ago(2)),
        (_month_ago(1), "en_attente", None),
    ]
    for date_loyer, statut, date_paiement in loyer_statuses_2:
        row = {
            "id": str(uuid.uuid4()),
            "id_bien": bien2_id,
            "montant": 620,
            "statut": statut,
            "date_loyer": date_loyer,
            "id_locataire": loc2_id,
            "is_demo": True,
        }
        if date_paiement:
            row["date_paiement"] = date_paiement
        client.table("loyers").insert(row).execute()

    # --- Charges Bien 1 ---
    charges_data_1 = [
        ("copropriete", 150, _month_ago(3)),
        ("copropriete", 150, _month_ago(6)),
        ("taxe_fonciere", 800, _month_ago(4)),
    ]
    for type_charge, montant, date in charges_data_1:
        client.table("charges").insert({
            "id": str(uuid.uuid4()),
            "id_bien": bien1_id,
            "type_charge": type_charge,
            "montant": montant,
            "date_paiement": date,
            "is_demo": True,
        }).execute()

    # --- Charges Bien 2 ---
    client.table("charges").insert({
        "id": str(uuid.uuid4()),
        "id_bien": bien2_id,
        "type_charge": "copropriete",
        "montant": 90,
        "date_paiement": _month_ago(3),
        "is_demo": True,
    }).execute()

    # --- Assurance PNO (Bien 1) ---
    client.table("assurance_pno").insert({
        "id": str(uuid.uuid4()),
        "id_bien": bien1_id,
        "assureur": "AXA",
        "numero_contrat": "PNO-DEMO-2025-001",
        "prime_annuelle": 180,
        "date_debut": _month_ago(12),
        "date_fin": _next_month_first(),
        "is_demo": True,
    }).execute()

    # --- Mark demo as seeded in subscriptions ---
    # Upsert subscription row with demo_seeded=True
    sub_check = (
        client.table("subscriptions")
        .select("id")
        .eq("user_id", user_id)
        .execute()
    )
    if sub_check.data:
        client.table("subscriptions").update({
            "demo_seeded": True,
        }).eq("user_id", user_id).execute()
    else:
        client.table("subscriptions").insert({
            "user_id": user_id,
            "status": "demo",
            "demo_seeded": True,
            "onboarding_completed": False,
        }).execute()

    logger.info("demo_seed_complete", user_id=user_id, sci_id=sci_id)
    return {"sci_id": sci_id, "bien_ids": [bien1_id, bien2_id]}


async def cleanup_demo_data(client, user_id: str) -> int:
    """Remove all demo data for a user. Called after subscription activation."""
    logger.info("demo_cleanup_start", user_id=user_id)

    # Find demo SCIs for this user (via associes)
    assoc_res = (
        client.table("associes")
        .select("id_sci")
        .eq("user_id", user_id)
        .eq("is_demo", True)
        .execute()
    )
    sci_ids = [row["id_sci"] for row in (assoc_res.data or [])]

    if not sci_ids:
        logger.info("demo_cleanup_no_data", user_id=user_id)
        return 0

    # Find all demo biens
    biens_res = (
        client.table("biens")
        .select("id")
        .in_("id_sci", sci_ids)
        .eq("is_demo", True)
        .execute()
    )
    bien_ids = [row["id"] for row in (biens_res.data or [])]

    deleted = 0

    # Delete in dependency order (children first)
    if bien_ids:
        # Loyers
        r = client.table("loyers").delete().in_("id_bien", bien_ids).eq("is_demo", True).execute()
        deleted += len(r.data or [])

        # Charges
        r = client.table("charges").delete().in_("id_bien", bien_ids).eq("is_demo", True).execute()
        deleted += len(r.data or [])

        # Assurance PNO
        r = client.table("assurance_pno").delete().in_("id_bien", bien_ids).eq("is_demo", True).execute()
        deleted += len(r.data or [])

        # Bail_locataires (via baux)
        baux_res = client.table("baux").select("id").in_("id_bien", bien_ids).eq("is_demo", True).execute()
        bail_ids = [row["id"] for row in (baux_res.data or [])]
        if bail_ids:
            client.table("bail_locataires").delete().in_("id_bail", bail_ids).execute()

        # Locataires
        r = client.table("locataires").delete().in_("id_bien", bien_ids).eq("is_demo", True).execute()
        deleted += len(r.data or [])

        # Baux
        r = client.table("baux").delete().in_("id_bien", bien_ids).eq("is_demo", True).execute()
        deleted += len(r.data or [])

        # Biens
        r = client.table("biens").delete().in_("id_sci", sci_ids).eq("is_demo", True).execute()
        deleted += len(r.data or [])

    # Associes
    r = client.table("associes").delete().eq("user_id", user_id).eq("is_demo", True).execute()
    deleted += len(r.data or [])

    # SCIs
    for sci_id in sci_ids:
        r = client.table("sci").delete().eq("id", sci_id).eq("is_demo", True).execute()
        deleted += len(r.data or [])

    # Reset demo_seeded flag
    client.table("subscriptions").update({
        "demo_seeded": False,
    }).eq("user_id", user_id).execute()

    logger.info("demo_cleanup_complete", user_id=user_id, deleted_rows=deleted)
    return deleted
```

- [ ] **Step 2: Verify syntax**

Run: `cd /Users/radnoumanemossabely/Code/sci-manager-renew/backend && python -c "import app.services.demo_service; print('OK')"`
Expected: OK

- [ ] **Step 3: Commit**

```bash
git add backend/app/services/demo_service.py
git commit -m "feat(demo): add demo seed + cleanup service — realistic SCI data lifecycle"
```

---

## Task 3: Demo API Endpoints (Backend)

**Files:**
- Create: `backend/app/api/v1/demo.py`
- Modify: `backend/app/main.py` (add router registration)

- [ ] **Step 1: Create the demo router**

```python
"""Demo data API — seed and cleanup demo data for new users."""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Depends, Request

from app.core.security import get_current_user
from app.core.supabase_client import get_supabase_service_client
from app.core.rate_limit import limiter
from app.services.demo_service import seed_demo_data, cleanup_demo_data

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/demo", tags=["demo"])


@router.post("/seed", status_code=201)
@limiter.limit("1/hour")
async def seed_demo(request: Request, user=Depends(get_current_user)):
    """Seed demo data for a new user. Only works once (idempotent)."""
    client = get_supabase_service_client()

    # Check if already seeded
    sub_res = (
        client.table("subscriptions")
        .select("demo_seeded, status")
        .eq("user_id", user["sub"])
        .execute()
    )
    if sub_res.data:
        sub = sub_res.data[0]
        if sub.get("demo_seeded"):
            return {"message": "Données de démonstration déjà chargées.", "already_seeded": True}
        if sub.get("status") in ("active", "paid"):
            return {"message": "Abonnement actif — pas de données demo nécessaires.", "already_seeded": False}

    result = await seed_demo_data(client, user["sub"])
    return {"message": "Données de démonstration chargées avec succès.", "sci_id": result["sci_id"]}


@router.delete("/cleanup", status_code=200)
@limiter.limit("5/hour")
async def cleanup_demo(request: Request, user=Depends(get_current_user)):
    """Remove all demo data for the current user."""
    client = get_supabase_service_client()
    deleted = await cleanup_demo_data(client, user["sub"])
    return {"message": f"{deleted} enregistrements de démonstration supprimés.", "deleted": deleted}
```

- [ ] **Step 2: Register the router in main.py**

In `backend/app/main.py`, add import near the other router imports (around line 36-68):

```python
from app.api.v1 import demo
```

Add router registration near the other `include_router` calls (around line 580-614):

```python
app.include_router(demo.router, prefix="/api/v1")
```

- [ ] **Step 3: Verify server starts**

Run: `cd /Users/radnoumanemossabely/Code/sci-manager-renew/backend && python -c "from app.main import app; print('OK')"`
Expected: OK

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/demo.py backend/app/main.py
git commit -m "feat(api): add POST /demo/seed + DELETE /demo/cleanup endpoints"
```

---

## Task 4: Stripe Webhook — Demo Cleanup on Payment

**Files:**
- Modify: `backend/app/api/v1/stripe.py`

- [ ] **Step 1: Add demo cleanup to checkout.session.completed handler**

In `backend/app/api/v1/stripe.py`, find the `_handle_event` function. After the `checkout.session.completed` handling is complete (after the `_sync_subscription()` call), add demo cleanup:

```python
# After the existing _sync_subscription() call in checkout.session.completed handler:
# Clean up demo data now that user has paid
try:
    from app.services.demo_service import cleanup_demo_data
    service_client = get_supabase_service_client()
    await cleanup_demo_data(service_client, resolved_user_id)
    logger.info("demo_cleanup_after_checkout", user_id=resolved_user_id)
except Exception:
    logger.warning("demo_cleanup_failed_after_checkout", user_id=resolved_user_id, exc_info=True)
```

The `resolved_user_id` variable name may differ — use whatever variable holds the user_id at that point in the handler (could be `user_id`, `uid`, or extracted from session metadata). Read the actual code to find the correct variable name.

This must be placed INSIDE the `checkout.session.completed` case, AFTER subscription sync completes, BEFORE the function returns.

- [ ] **Step 2: Run backend tests**

Run: `cd /Users/radnoumanemossabely/Code/sci-manager-renew/backend && PYTHONPATH=. pytest -x -q 2>&1 | tail -5`
Expected: All tests pass

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/v1/stripe.py
git commit -m "feat(stripe): cleanup demo data on checkout.session.completed webhook"
```

---

## Task 5: Frontend API Module + Types

**Files:**
- Create: `frontend/src/lib/api/demo.ts`
- Modify: `frontend/src/lib/api/index.ts`
- Modify: `frontend/src/lib/api/types.ts`

- [ ] **Step 1: Add demo_seeded to SubscriptionEntitlements type**

In `frontend/src/lib/api/types.ts`, find the `SubscriptionEntitlements` type and add:

```typescript
demo_seeded?: boolean;
```

- [ ] **Step 2: Create the demo API module**

```typescript
import { apiFetch } from './client';

export async function seedDemo(): Promise<{ message: string; sci_id?: string; already_seeded?: boolean }> {
	return apiFetch('/api/v1/demo/seed', { method: 'POST' });
}

export async function cleanupDemo(): Promise<{ message: string; deleted: number }> {
	return apiFetch('/api/v1/demo/cleanup', { method: 'DELETE' });
}
```

- [ ] **Step 3: Add export to index.ts**

In `frontend/src/lib/api/index.ts`, add:

```typescript
export * from './demo';
```

- [ ] **Step 4: Verify compilation**

Run: `cd /Users/radnoumanemossabely/Code/sci-manager-renew/frontend && pnpm run check 2>&1 | tail -3`
Expected: 0 errors

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/api/demo.ts frontend/src/lib/api/index.ts frontend/src/lib/api/types.ts
git commit -m "feat(api): add seedDemo + cleanupDemo frontend API functions"
```

---

## Task 6: DemoBanner Component

**Files:**
- Create: `frontend/src/lib/components/DemoBanner.svelte`

- [ ] **Step 1: Create the component**

```svelte
<script lang="ts">
	import { Search } from 'lucide-svelte';
</script>

<div class="border-b border-amber-200 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/30">
	<div class="mx-auto flex max-w-7xl items-center justify-between px-4 py-2.5 sm:px-6 lg:px-8">
		<div class="flex items-center gap-2 text-sm text-amber-800 dark:text-amber-300">
			<Search class="h-4 w-4 flex-shrink-0" />
			<span>Vous explorez des données de démonstration. Souscrivez pour gérer vos vraies SCI.</span>
		</div>
		<a
			href="/pricing"
			class="flex-shrink-0 rounded-lg bg-amber-600 px-3 py-1.5 text-xs font-medium text-white transition-colors hover:bg-amber-700"
		>
			Souscrire →
		</a>
	</div>
</div>
```

- [ ] **Step 2: Verify compilation**

Run: `cd /Users/radnoumanemossabely/Code/sci-manager-renew/frontend && pnpm run check 2>&1 | tail -3`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/components/DemoBanner.svelte
git commit -m "feat: add DemoBanner — persistent amber banner for demo users"
```

---

## Task 7: UpgradePrompt + LockedAction Components

**Files:**
- Create: `frontend/src/lib/components/UpgradePrompt.svelte`
- Create: `frontend/src/lib/components/LockedAction.svelte`

- [ ] **Step 1: Create UpgradePrompt**

```svelte
<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Lock, Check, X } from 'lucide-svelte';

	interface Props {
		open: boolean;
		action: string;
		onClose: () => void;
	}

	let { open, action, onClose }: Props = $props();
</script>

{#if open}
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4">
		<button
			class="absolute inset-0 bg-black/50 backdrop-blur-sm"
			onclick={onClose}
			aria-label="Fermer"
		></button>
		<div class="relative z-10 w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-700 dark:bg-slate-900" style="animation: scaleIn 0.2s ease-out">
			<button
				class="absolute right-4 top-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
				onclick={onClose}
				aria-label="Fermer"
			>
				<X class="h-5 w-5" />
			</button>

			<div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-900/30">
				<Lock class="h-7 w-7 text-amber-600 dark:text-amber-400" />
			</div>

			<h3 class="text-center text-lg font-bold text-slate-900 dark:text-slate-100">
				Fonctionnalité réservée aux abonnés
			</h3>
			<p class="mt-2 text-center text-sm text-slate-600 dark:text-slate-400">
				Pour {action}, souscrivez un plan GérerSCI.
			</p>

			<ul class="mt-4 space-y-2">
				{#each [
					'Accès complet à toutes les fonctionnalités',
					'Vos données réelles, pas de la démo',
					'Support email dédié',
					'Garantie satisfait ou remboursé 30 jours'
				] as item}
					<li class="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-400">
						<Check class="h-4 w-4 flex-shrink-0 text-emerald-500" />
						{item}
					</li>
				{/each}
			</ul>

			<div class="mt-6 flex gap-3">
				<Button variant="outline" class="flex-1" onclick={onClose}>
					Plus tard
				</Button>
				<a href="/pricing" class="flex-1">
					<Button class="w-full bg-blue-600 text-white hover:bg-blue-700">
						Voir les plans →
					</Button>
				</a>
			</div>
		</div>
	</div>
{/if}

<style>
	@keyframes scaleIn {
		from { opacity: 0; transform: scale(0.95); }
		to { opacity: 1; transform: scale(1); }
	}
</style>
```

- [ ] **Step 2: Create LockedAction**

```svelte
<script lang="ts">
	import { Lock } from 'lucide-svelte';
	import UpgradePrompt from './UpgradePrompt.svelte';
	import type { Snippet } from 'svelte';

	interface Props {
		isDemo: boolean;
		action: string;
		children: Snippet;
	}

	let { isDemo, action, children }: Props = $props();
	let showPrompt = $state(false);
</script>

{#if isDemo}
	<div class="relative inline-flex">
		<button
			class="contents"
			onclick={(e) => { e.preventDefault(); e.stopPropagation(); showPrompt = true; }}
		>
			{@render children()}
		</button>
		<div class="pointer-events-none absolute -right-1 -top-1 flex h-5 w-5 items-center justify-center rounded-full bg-amber-500 text-white shadow-sm">
			<Lock class="h-3 w-3" />
		</div>
	</div>
	<UpgradePrompt open={showPrompt} {action} onClose={() => { showPrompt = false; }} />
{:else}
	{@render children()}
{/if}
```

- [ ] **Step 3: Verify compilation**

Run: `cd /Users/radnoumanemossabely/Code/sci-manager-renew/frontend && pnpm run check 2>&1 | tail -3`

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/components/UpgradePrompt.svelte frontend/src/lib/components/LockedAction.svelte
git commit -m "feat: add LockedAction wrapper + UpgradePrompt modal for demo paywall"
```

---

## Task 8: Credibility Loading Screen (`/welcome`)

**Files:**
- Create: `frontend/src/routes/welcome/+page.svelte`

- [ ] **Step 1: Create the welcome page**

```svelte
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { seedDemo } from '$lib/api';

	let currentStep = $state(0);
	let factIndex = $state(0);
	let progress = $state(0);
	let error = $state('');

	const steps = [
		{ text: 'Création de votre espace de gestion', duration: 1500 },
		{ text: 'Chargement des données de démonstration', duration: 2000 },
		{ text: 'Calcul de vos indicateurs financiers', duration: 2000 },
		{ text: 'Préparation de votre tableau de bord', duration: 1500 },
	];

	const facts = [
		'Un loyer impayé non détecté coûte en moyenne 800€ au propriétaire.',
		'Les gestionnaires digitalisés réduisent leurs impayés de 63%.',
		'GérerSCI pré-remplit votre CERFA 2044 automatiquement.',
		'72% des gestionnaires constatent une amélioration en 12 mois.',
	];

	const totalDuration = steps.reduce((s, step) => s + step.duration, 0);

	onMount(() => {
		// Launch API call immediately (runs in background)
		const seedPromise = seedDemo().catch((err) => {
			console.error('Demo seed failed:', err);
			error = err?.message || 'Erreur lors du chargement des données.';
		});

		// Animate steps on fixed timer (independent of API)
		let elapsed = 0;
		for (let i = 0; i < steps.length; i++) {
			setTimeout(() => { currentStep = i + 1; }, elapsed);
			elapsed += steps[i].duration;
		}

		// Progress bar animation
		const interval = setInterval(() => {
			progress = Math.min(progress + 1.5, 100);
		}, totalDuration / 67);

		// Rotate facts
		const factTimer = setInterval(() => {
			factIndex = (factIndex + 1) % facts.length;
		}, 2500);

		// Redirect after animation completes (wait for API too)
		setTimeout(async () => {
			clearInterval(interval);
			clearInterval(factTimer);
			progress = 100;
			await seedPromise;
			// Small delay for 100% to render
			setTimeout(() => {
				goto('/dashboard', { replaceState: true });
			}, 300);
		}, totalDuration);
	});
</script>

<svelte:head><title>Bienvenue | GérerSCI</title></svelte:head>

<div class="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-950">
	<div class="w-full max-w-md px-6 text-center">
		<!-- Logo -->
		<h1 class="mb-2 text-2xl font-bold tracking-tight text-slate-900 dark:text-white">
			GérerSCI
		</h1>
		<p class="mb-8 text-sm text-slate-600 dark:text-slate-400">
			Bienvenue ! Nous préparons votre espace.
		</p>

		<!-- Steps -->
		<div class="mb-8 space-y-3 text-left">
			{#each steps as step, i}
				<div class="flex items-center gap-3 text-sm transition-opacity duration-300 {i < currentStep ? 'opacity-100' : i === currentStep ? 'opacity-70' : 'opacity-30'}">
					{#if i < currentStep}
						<span class="flex h-6 w-6 items-center justify-center rounded-full bg-emerald-500 text-white text-xs">✓</span>
					{:else if i === currentStep}
						<span class="flex h-6 w-6 items-center justify-center">
							<span class="h-5 w-5 animate-spin rounded-full border-2 border-slate-300 border-t-blue-600 dark:border-slate-700 dark:border-t-blue-400"></span>
						</span>
					{:else}
						<span class="flex h-6 w-6 items-center justify-center rounded-full bg-slate-200 text-slate-400 text-xs dark:bg-slate-800 dark:text-slate-600">
							{i + 1}
						</span>
					{/if}
					<span class="text-slate-700 dark:text-slate-300 {i < currentStep ? 'text-emerald-700 dark:text-emerald-400' : ''}">
						{step.text}
					</span>
				</div>
			{/each}
		</div>

		<!-- Progress bar -->
		<div class="mb-6 h-2 w-full overflow-hidden rounded-full bg-slate-200 dark:bg-slate-800">
			<div
				class="h-full rounded-full bg-gradient-to-r from-blue-600 to-cyan-500 transition-all duration-200"
				style="width: {progress}%"
			></div>
		</div>

		<!-- Rotating facts -->
		<div class="min-h-[3rem] text-sm text-slate-500 dark:text-slate-400" style="animation: fadeIn 0.3s ease-out">
			<p>💡 {facts[factIndex]}</p>
		</div>

		{#if error}
			<p class="mt-4 text-xs text-rose-500">{error}</p>
		{/if}
	</div>
</div>

<style>
	@keyframes fadeIn {
		from { opacity: 0; }
		to { opacity: 1; }
	}
</style>
```

- [ ] **Step 2: Verify compilation**

Run: `cd /Users/radnoumanemossabely/Code/sci-manager-renew/frontend && pnpm run check 2>&1 | tail -3`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/routes/welcome/+page.svelte
git commit -m "feat: add /welcome credibility loading screen — Kayak-style animated steps"
```

---

## Task 9: Layout Bypass — Remove Paywall for Demo Users

**Files:**
- Modify: `frontend/src/routes/(app)/+layout.ts`
- Modify: `frontend/src/routes/(app)/+layout.svelte`
- Modify: `frontend/src/lib/auth/route-guard.ts`

- [ ] **Step 1: Modify layout.ts to bypass paywall for demo users**

Read the current `frontend/src/routes/(app)/+layout.ts` first. Then replace the paywall redirect logic:

```typescript
// BEFORE (current):
// if (!subscription.is_active) {
//     throw redirect(302, '/pricing');
// }

// AFTER:
if (!subscription.is_active) {
    // Demo mode: check if demo has been seeded
    if (!subscription.demo_seeded && !url.pathname.startsWith('/welcome')) {
        // First visit — redirect to credibility loading screen
        throw redirect(302, '/welcome');
    }
    // If demo_seeded=true, let them through (demo mode)
    // The DemoBanner + LockedAction handle restrictions
}
```

Also update the onboarding check: only enforce onboarding for PAYING users:

```typescript
// Only redirect to onboarding if user has an active subscription
if (subscription.is_active && !subscription.onboarding_completed && !url.pathname.startsWith('/onboarding')) {
    throw redirect(302, '/onboarding');
}
```

- [ ] **Step 2: Add /welcome to public routes**

In `frontend/src/lib/auth/route-guard.ts`, add `/welcome` to the public route prefixes so it's accessible without auth checks:

Find the `PUBLIC_ROUTE_PREFIXES` or equivalent array and add `'/welcome'`.

- [ ] **Step 3: Add DemoBanner to app layout**

In `frontend/src/routes/(app)/+layout.svelte`, add the banner:

Import:
```typescript
import DemoBanner from '$lib/components/DemoBanner.svelte';
```

Add in the template, after `<AppNavbar>` and before `<main>`:
```svelte
{#if !props.data.subscription?.is_active}
	<DemoBanner />
{/if}
```

- [ ] **Step 4: Verify compilation**

Run: `cd /Users/radnoumanemossabely/Code/sci-manager-renew/frontend && pnpm run check 2>&1 | tail -3`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/routes/\(app\)/+layout.ts frontend/src/routes/\(app\)/+layout.svelte frontend/src/lib/auth/route-guard.ts
git commit -m "feat(layout): bypass paywall for demo users, show DemoBanner, redirect /welcome"
```

---

## Task 10: Wire LockedAction on Write Buttons

**Files:**
- Modify: Multiple `(app)` page files

This task wraps all write-action buttons with `LockedAction` across the app. The component needs `isDemo` prop which comes from the subscription context.

- [ ] **Step 1: Create a demo-aware store or helper**

Read how subscription context is accessed in child components. The subscription is set via `setContext('subscription', ...)` in `(app)/+layout.svelte`.

In each page that needs locking, the pattern is:

```svelte
<script lang="ts">
	import { getContext } from 'svelte';
	import LockedAction from '$lib/components/LockedAction.svelte';
	import type { SubscriptionEntitlements } from '$lib/api';

	const subscription = getContext<SubscriptionEntitlements>('subscription');
	const isDemo = !subscription?.is_active;
</script>

<!-- Then wrap write buttons: -->
<LockedAction {isDemo} action="enregistrer un loyer">
	<Button onclick={handleCreateLoyer}>Enregistrer le loyer</Button>
</LockedAction>
```

- [ ] **Step 2: Add LockedAction to dashboard page**

In `frontend/src/routes/(app)/dashboard/+page.svelte`:
- Import `LockedAction` and `getContext`
- Get `isDemo` from subscription context
- Wrap the "Commencer la mise en route" CTA button (the one linking to `/onboarding`) — this one should NOT be locked since it leads to onboarding
- No write actions on dashboard itself — skip this file

- [ ] **Step 3: Add LockedAction to SCI pages**

In `frontend/src/routes/(app)/scis/+page.svelte`:
- Wrap the "Créer une SCI" button with `LockedAction isDemo={isDemo} action="créer une SCI"`

- [ ] **Step 4: Add LockedAction to biens page**

In `frontend/src/routes/(app)/scis/[sciId]/biens/+page.svelte`:
- Wrap the "Ajouter un bien" button with `LockedAction isDemo={isDemo} action="ajouter un bien"`

- [ ] **Step 5: Add LockedAction to FicheBienLoyers**

In `frontend/src/lib/components/fiche-bien/FicheBienLoyers.svelte`:
- Import `LockedAction` and get `isDemo` from context
- Wrap the loyer creation form submit button with `LockedAction isDemo={isDemo} action="enregistrer un loyer"`
- Wrap the "Générer quittance" buttons with `LockedAction isDemo={isDemo} action="générer une quittance"`

- [ ] **Step 6: Add LockedAction to FicheBienIdentite**

In `frontend/src/lib/components/fiche-bien/FicheBienIdentite.svelte`:
- Wrap the "Modifier" / "Enregistrer" button with `LockedAction isDemo={isDemo} action="modifier ce bien"`

- [ ] **Step 7: Add LockedAction to charges, baux, documents, associés**

Apply the same pattern to:
- `FicheBienCharges.svelte` — wrap "Ajouter une charge" → `action="ajouter une charge"`
- `FicheBienDocuments.svelte` — wrap upload button → `action="uploader un document"`
- Baux creation/edit buttons → `action="créer un bail"`
- Associés page — wrap "Ajouter un associé" → `action="ajouter un associé"`
- Export CSV buttons → `action="exporter les données"`
- Import CSV button → `action="importer des données"`
- Notification settings save button → `action="configurer les notifications"`

For each file:
1. Import `LockedAction` and `getContext`
2. Get subscription context: `const subscription = getContext<SubscriptionEntitlements>('subscription');`
3. Derive: `const isDemo = !subscription?.is_active;`
4. Wrap the relevant button

- [ ] **Step 8: Verify compilation**

Run: `cd /Users/radnoumanemossabely/Code/sci-manager-renew/frontend && pnpm run check 2>&1 | tail -5`
Fix any errors.

- [ ] **Step 9: Commit**

```bash
git add frontend/src/
git commit -m "feat: wire LockedAction on all write buttons — demo users see upgrade prompts"
```

---

## Task 11: Backend — Return demo_seeded in Subscription Entitlements

**Files:**
- Modify: `backend/app/api/v1/stripe.py` (the subscription entitlements endpoint)

- [ ] **Step 1: Find the subscription entitlements endpoint**

Search for the endpoint that returns subscription/entitlements data (the one called by `fetchSubscriptionEntitlements()`). It's likely `GET /api/v1/stripe/subscription`.

Read the handler and find where the response dict is built. Add `demo_seeded` to the response:

```python
# Add to the response dict:
"demo_seeded": subscription_row.get("demo_seeded", False) if subscription_row else False,
```

- [ ] **Step 2: Run backend tests**

Run: `cd /Users/radnoumanemossabely/Code/sci-manager-renew/backend && PYTHONPATH=. pytest -x -q 2>&1 | tail -5`

- [ ] **Step 3: Commit**

```bash
git add backend/app/api/v1/stripe.py
git commit -m "feat(stripe): include demo_seeded in subscription entitlements response"
```

---

## Task 12: Final Verification

- [ ] **Step 1: Run full frontend check**

Run: `cd /Users/radnoumanemossabely/Code/sci-manager-renew/frontend && pnpm run check`
Expected: 0 errors, 0 warnings

- [ ] **Step 2: Run frontend build**

Run: `cd /Users/radnoumanemossabely/Code/sci-manager-renew/frontend && pnpm run build`
Expected: Build succeeds

- [ ] **Step 3: Run backend tests**

Run: `cd /Users/radnoumanemossabely/Code/sci-manager-renew/backend && PYTHONPATH=. pytest -x -q`
Expected: All tests pass

- [ ] **Step 4: Push everything**

```bash
git push
```

---

## Summary

| Task | Component | Key Deliverable |
|------|-----------|----------------|
| 1 | DB Migration | `is_demo` columns + `demo_seeded` flag |
| 2 | Demo Service | Seed realistic SCI data + cleanup logic |
| 3 | Demo API | `POST /demo/seed` + `DELETE /demo/cleanup` |
| 4 | Stripe Webhook | Auto-cleanup demo on payment |
| 5 | Frontend API | `seedDemo()` + `cleanupDemo()` + types |
| 6 | DemoBanner | Persistent amber banner for demo users |
| 7 | LockedAction + UpgradePrompt | Cadenas + upgrade modal |
| 8 | Welcome Page | Credibility loading screen (7s, 4 steps) |
| 9 | Layout Bypass | Remove paywall redirect, add DemoBanner |
| 10 | Wire LockedAction | ~15 write buttons wrapped across app |
| 11 | Backend Entitlements | Return `demo_seeded` in subscription response |
| 12 | Verification | Full check + build + tests + push |
