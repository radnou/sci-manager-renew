# Workflow Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Simplify the user flow — redirect anonymous visitors to register instead of checkout modal, add Hormozi messaging, shorten navigation paths, simplify navbar, and add demo conversion triggers.

**Architecture:** All frontend changes. Landing + pricing pages detect auth state before opening checkout modal. Register page shows contextual Hormozi copy. Dashboard SCI cards include inline bien links. Navbar restructured from 7 to 4 items with "Pilotage" dropdown. New DemoConversionPrompt component triggers on high-value demo actions.

**Tech Stack:** SvelteKit 2, Svelte 5 runes, Tailwind CSS 4, lucide-svelte

**Spec:** `docs/superpowers/specs/2026-03-29-workflow-optimization-design.md`

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `frontend/src/routes/+page.svelte` | Modify | Redirect anonymous to /register instead of modal |
| `frontend/src/routes/pricing/+page.svelte` | Modify | Same redirect logic |
| `frontend/src/routes/register/+page.svelte` | Modify | Hormozi message, hide price, show plan features |
| `frontend/src/lib/components/dashboard/DashboardSciCards.svelte` | Modify | Add bien links with status indicators |
| `frontend/src/lib/components/AppNavbar.svelte` | Modify | Simplify 7→4 items, add Pilotage dropdown, improve breadcrumb |
| `frontend/src/lib/components/DemoConversionPrompt.svelte` | Create | Conversion trigger for demo users |
| `frontend/src/lib/components/fiche-bien/FicheBienLoyers.svelte` | Modify | Integrate conversion trigger after quittance |
| `frontend/src/routes/(app)/+layout.svelte` | Modify | Page visit counter + trigger for 3rd page |

---

## Task 1: Checkout Redirect for Anonymous Visitors

**Files:**
- Modify: `frontend/src/routes/+page.svelte`
- Modify: `frontend/src/routes/pricing/+page.svelte`

- [ ] **Step 1: Modify landing page openCheckoutModal**

In `frontend/src/routes/+page.svelte`, find `openCheckoutModal` function (~line 98). Add auth check at the top:

```typescript
async function openCheckoutModal(planKey: string) {
    trackEvent(EVENTS.LANDING_PLAN_SELECT, { plan: planKey });

    // Anonymous visitors → redirect to register with plan context
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
        goto(`/register?plan=${planKey}`);
        return;
    }

    // Authenticated users → show checkout modal (existing behavior)
    const plan = plans.find((p: any) => p.key === planKey);
    // ... rest of existing modal logic
}
```

Add `import { goto } from '$app/navigation'` if not already imported (it should be).
Add `import { supabase } from '$lib/supabase'` if not already imported.

Also update the Fondateur button onclick similarly — check auth, redirect if anonymous.

- [ ] **Step 2: Modify pricing page openCheckoutModal**

In `frontend/src/routes/pricing/+page.svelte`, find `openCheckoutModal` function (~line 86). Add the same auth check:

```typescript
function openCheckoutModal(planKey: string) {
    trackEvent(EVENTS.PRICING_PLAN_SELECT, { plan: planKey });

    // Anonymous visitors → redirect to register
    if (!isAuthenticated) {
        window.location.href = `/register?plan=${planKey}`;
        return;
    }

    // Authenticated → show modal (existing logic)
    // ...
}
```

Note: pricing page already has `isAuthenticated` state (line 13). No need for async session check.

- [ ] **Step 3: Verify**

Run: `cd frontend && pnpm run check 2>&1 | tail -3`

- [ ] **Step 4: Commit**

```bash
git add frontend/src/routes/+page.svelte frontend/src/routes/pricing/+page.svelte
git commit -m "feat: redirect anonymous visitors to /register instead of checkout modal"
```

---

## Task 2: Hormozi Register Message

**Files:**
- Modify: `frontend/src/routes/register/+page.svelte`

- [ ] **Step 1: Update plan labels and messages**

Find the `planLabels` map (~line 25) and the conditional header/description sections.

Replace the plan labels:
```typescript
const planLabels: Record<string, { name: string; features: string }> = {
    starter: { name: 'Gestion', features: '1 SCI, 5 biens, quittances PDF, CERFA 2044' },
    pro: { name: 'Pilotage', features: 'SCI illimitées, CERFA 2044, fiscalité complète' },
    lifetime: { name: 'Fondateur', features: 'Tout Pilotage inclus — à vie' },
};
```

- [ ] **Step 2: Replace header section**

Replace the card header content (around lines 100-107) with:

```svelte
<CardHeader>
    {#if selectedPlan}
        <Badge variant="secondary" class="mb-2 w-fit">Accès gratuit — aucune carte bancaire requise</Badge>
    {/if}
    <CardTitle class="text-xl">
        {#if selectedPlan}
            Voyez ce que donnerait votre SCI dans un vrai cockpit de gestion.
        {:else}
            Créez votre compte
        {/if}
    </CardTitle>
    <CardDescription>
        {#if selectedPlan}
            Données de démo pré-remplies. Zéro carte bancaire. 2 minutes pour comprendre.
        {:else}
            Explorez GérerSCI avec des données de démonstration.
        {/if}
    </CardDescription>
</CardHeader>
```

- [ ] **Step 3: Add plan info below the form (no price)**

After the form submit button, add:

```svelte
{#if selectedPlan && planLabels[selectedPlan]}
    <div class="mt-4 rounded-lg border border-blue-200 bg-blue-50 p-3 text-sm dark:border-blue-800 dark:bg-blue-950/30">
        <p class="font-medium text-blue-800 dark:text-blue-300">
            Plan retenu : {planLabels[selectedPlan].name}
        </p>
        <p class="mt-1 text-blue-600 dark:text-blue-400">
            {planLabels[selectedPlan].features}
        </p>
        <p class="mt-1 text-xs text-blue-500 dark:text-blue-500">
            Activable après exploration. Annulable sous 30 jours.
        </p>
    </div>
{/if}
```

- [ ] **Step 4: Verify**

Run: `cd frontend && pnpm run check 2>&1 | tail -3`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/routes/register/+page.svelte
git commit -m "feat(register): Hormozi message — transformation over features, no price shown"
```

---

## Task 3: Dashboard SCI Cards — Direct Bien Links

**Files:**
- Modify: `frontend/src/lib/components/dashboard/DashboardSciCards.svelte`

- [ ] **Step 1: Check if biens data is available**

The dashboard API may not return individual biens per SCI card. Check the `SCICard` type. If `biens` array is not available, we need to add a simple list with just name + status.

Read the current `SCICard` type from `frontend/src/lib/api/types.ts`. If it doesn't include biens, the dashboard API response needs to be checked too.

For now, add optional biens display. The API already returns `biens_count` — we need individual biens. If not available in the API response, add a secondary fetch or skip this for now and just link to `/scis/{id}/biens`.

- [ ] **Step 2: Add bien links to each SCI card**

After the recouvrement progress bar section in the SCI card, add:

```svelte
{#if sci.biens && sci.biens.length > 0}
    <div class="mt-3 border-t border-slate-100 pt-3 dark:border-slate-800">
        {#each sci.biens.slice(0, 3) as bien}
            <a
                href="/scis/{sci.id}/biens/{bien.id}"
                class="flex items-center justify-between rounded px-2 py-1 text-xs hover:bg-slate-50 dark:hover:bg-slate-800"
                onclick|stopPropagation
            >
                <span class="flex items-center gap-1.5 text-slate-600 dark:text-slate-400">
                    🏠 {bien.adresse}
                </span>
                <span class="flex items-center gap-1.5">
                    <span class="text-slate-500">{bien.loyer_cc}€</span>
                    {#if bien.has_unpaid}
                        <span class="h-2 w-2 rounded-full bg-rose-500" title="Impayé"></span>
                    {:else}
                        <span class="h-2 w-2 rounded-full bg-emerald-500" title="À jour"></span>
                    {/if}
                </span>
            </a>
        {/each}
        {#if sci.biens.length > 3}
            <p class="mt-1 px-2 text-xs text-slate-400">+ {sci.biens.length - 3} autres</p>
        {/if}
    </div>
{/if}
```

If `sci.biens` is not available, add a simple "Voir les biens →" link instead:

```svelte
<div class="mt-3 border-t border-slate-100 pt-2 dark:border-slate-800">
    <span class="text-xs text-blue-600 dark:text-blue-400">Voir les {sci.biens_count} biens →</span>
</div>
```

- [ ] **Step 3: Verify**

Run: `cd frontend && pnpm run check 2>&1 | tail -3`

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/components/dashboard/DashboardSciCards.svelte
git commit -m "feat(dashboard): add direct bien links on SCI cards — 2 clicks instead of 4"
```

---

## Task 4: Navbar Simplification 7→4

**Files:**
- Modify: `frontend/src/lib/components/AppNavbar.svelte`

- [ ] **Step 1: Remove Exploitation, Échéances, Bilans from top-level nav**

Find the nav items section (~lines 280-315). Remove these three links:
- `/exploitation` (Briefcase)
- `/echeances` (CalendarClock)
- `/bilans` (FileSpreadsheet)

Keep only:
- `/dashboard` (Tableau de bord)
- SCI Switcher dropdown (Mes SCI)
- `/finances` (Finances)
- NEW: Pilotage dropdown

- [ ] **Step 2: Add Pilotage dropdown**

After the Finances link, add a new dropdown:

```svelte
<!-- Pilotage dropdown -->
<div class="relative">
    <button
        class="flex items-center gap-1.5 rounded-lg px-3 py-2 text-sm font-medium transition-colors {pilotageOpen ? 'bg-slate-100 dark:bg-slate-800' : 'text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100'}"
        onclick={() => { pilotageOpen = !pilotageOpen; }}
    >
        <Briefcase class="h-4 w-4" />
        <span>Pilotage</span>
        <ChevronDown class="h-3.5 w-3.5 transition-transform {pilotageOpen ? 'rotate-180' : ''}" />
    </button>
    {#if pilotageOpen}
        <div class="absolute left-0 top-full z-50 mt-1 w-48 rounded-xl border border-slate-200 bg-white p-1 shadow-lg dark:border-slate-700 dark:bg-slate-900">
            <a href="/exploitation" class="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800" onclick={() => { pilotageOpen = false; }}>
                <Briefcase class="h-4 w-4" /> Exploitation
            </a>
            <a href="/echeances" class="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800" onclick={() => { pilotageOpen = false; }}>
                <CalendarClock class="h-4 w-4" /> Échéances
            </a>
            <a href="/bilans" class="flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-slate-600 hover:bg-slate-50 dark:text-slate-400 dark:hover:bg-slate-800" onclick={() => { pilotageOpen = false; }}>
                <FileSpreadsheet class="h-4 w-4" /> Bilans mensuels
            </a>
        </div>
    {/if}
</div>
```

Add state: `let pilotageOpen = $state(false);`

Add outside-click close logic (same pattern as SCI switcher).

- [ ] **Step 3: Improve breadcrumb styling**

Find the breadcrumb section (~lines 556-638). Add background and increase size:

Change the breadcrumb container from plain to:
```svelte
<div class="border-b border-slate-100 bg-slate-50/50 px-4 py-1.5 dark:border-slate-800 dark:bg-slate-900/50">
```

Change breadcrumb text from `text-xs` to `text-sm font-medium`.

Add a back button (← arrow) at the start of the breadcrumb when depth > 1:
```svelte
{#if breadcrumbs.length > 1}
    <button onclick={() => history.back()} class="mr-2 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300">
        <ArrowLeft class="h-4 w-4" />
    </button>
{/if}
```

Import `ArrowLeft` from lucide-svelte if not already imported.

- [ ] **Step 4: Verify**

Run: `cd frontend && pnpm run check 2>&1 | tail -3`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/components/AppNavbar.svelte
git commit -m "feat(navbar): simplify 7→4 items, add Pilotage dropdown, improve breadcrumb"
```

---

## Task 5: DemoConversionPrompt Component

**Files:**
- Create: `frontend/src/lib/components/DemoConversionPrompt.svelte`

- [ ] **Step 1: Create the component**

```svelte
<script lang="ts">
    import { Button } from '$lib/components/ui/button';
    import { X } from 'lucide-svelte';
    import { trackEvent, EVENTS } from '$lib/analytics';

    interface Props {
        message: string;
        open: boolean;
        onClose: () => void;
    }

    let { message, open, onClose }: Props = $props();

    function handleConvert() {
        trackEvent(EVENTS.DEMO_UPGRADE_PROMPT, { action: 'convert_from_prompt' });
        window.location.href = '/pricing';
    }

    function handleContinue() {
        // Don't show again for 10 minutes
        localStorage.setItem('demo_prompt_dismissed', String(Date.now()));
        onClose();
    }
</script>

{#if open}
    <div class="fixed bottom-6 left-1/2 z-40 w-full max-w-lg -translate-x-1/2 px-4" style="animation: slideUp 0.3s ease-out">
        <div class="rounded-2xl border border-blue-200 bg-white p-5 shadow-2xl dark:border-blue-800 dark:bg-slate-900">
            <button
                class="absolute right-3 top-3 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                onclick={handleContinue}
                aria-label="Fermer"
            >
                <X class="h-4 w-4" />
            </button>

            <p class="pr-6 text-sm font-medium text-slate-700 dark:text-slate-300">
                {message}
            </p>
            <p class="mt-1.5 text-sm text-slate-500 dark:text-slate-400">
                Ajoutez votre première SCI pour gérer vos vraies données.
            </p>

            <div class="mt-4 flex items-center gap-3">
                <Button
                    class="bg-blue-600 text-white hover:bg-blue-700"
                    size="sm"
                    onclick={handleConvert}
                >
                    Commencer avec mes vraies données →
                </Button>
                <button
                    class="text-sm text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                    onclick={handleContinue}
                >
                    Continuer l'exploration
                </button>
            </div>
        </div>
    </div>
{/if}

<style>
    @keyframes slideUp {
        from { opacity: 0; transform: translate(-50%, 20px); }
        to { opacity: 1; transform: translate(-50%, 0); }
    }
</style>
```

- [ ] **Step 2: Verify**

Run: `cd frontend && pnpm run check 2>&1 | tail -3`

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/components/DemoConversionPrompt.svelte
git commit -m "feat: add DemoConversionPrompt — bottom toast for demo conversion triggers"
```

---

## Task 6: Wire Conversion Triggers

**Files:**
- Modify: `frontend/src/lib/components/fiche-bien/FicheBienLoyers.svelte`
- Modify: `frontend/src/routes/(app)/+layout.svelte`

- [ ] **Step 1: Add quittance trigger to FicheBienLoyers**

In `FicheBienLoyers.svelte`, after the quittance generation success (where the toast is shown), add:

```typescript
import DemoConversionPrompt from '$lib/components/DemoConversionPrompt.svelte';

// Add state
let showConversionPrompt = $state(false);
let conversionMessage = $state('');
```

After the quittance success toast, check if demo user:

```typescript
// After quittance generation success
if (isDemo) {
    const dismissed = localStorage.getItem('demo_prompt_dismissed');
    if (!dismissed || Date.now() - parseInt(dismissed) > 600000) { // 10 min cooldown
        conversionMessage = 'Cette quittance a été générée avec des données de démonstration.';
        showConversionPrompt = true;
    }
}
```

Add to template (at the end):

```svelte
<DemoConversionPrompt
    message={conversionMessage}
    open={showConversionPrompt}
    onClose={() => { showConversionPrompt = false; }}
/>
```

- [ ] **Step 2: Add 3rd page visit trigger to app layout**

In `frontend/src/routes/(app)/+layout.svelte`, add a page visit counter for demo users:

```typescript
import DemoConversionPrompt from '$lib/components/DemoConversionPrompt.svelte';
import { page } from '$app/stores';

let showConversionPrompt = $state(false);

// Track page visits for demo users
$effect(() => {
    if (!props.data.subscription?.is_active) {
        const count = parseInt(localStorage.getItem('demo_page_visits') || '0') + 1;
        localStorage.setItem('demo_page_visits', String(count));

        if (count === 3) {
            const dismissed = localStorage.getItem('demo_prompt_dismissed');
            if (!dismissed || Date.now() - parseInt(dismissed) > 600000) {
                showConversionPrompt = true;
            }
        }
    }
});
```

Add to template (after `{@render props.children()}`):

```svelte
{#if showConversionPrompt}
    <DemoConversionPrompt
        message="Vous explorez depuis quelques minutes. Prêt à gérer vos vraies SCI ?"
        open={showConversionPrompt}
        onClose={() => { showConversionPrompt = false; }}
    />
{/if}
```

- [ ] **Step 3: Verify**

Run: `cd frontend && pnpm run check 2>&1 | tail -3`

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/components/fiche-bien/FicheBienLoyers.svelte frontend/src/routes/\(app\)/+layout.svelte
git commit -m "feat: wire demo conversion triggers — quittance action + 3rd page visit"
```

---

## Task 7: Final Verification

- [ ] **Step 1: Run full check**

Run: `cd frontend && pnpm run check`

- [ ] **Step 2: Run build**

Run: `cd frontend && pnpm run build`

- [ ] **Step 3: Push**

```bash
git push
```

---

## Summary

| Task | Deliverable |
|------|------------|
| 1 | Anonymous visitors → /register redirect (no modal) |
| 2 | Hormozi register message (transformation > features) |
| 3 | Direct bien links on dashboard SCI cards |
| 4 | Navbar 7→4 + Pilotage dropdown + breadcrumb |
| 5 | DemoConversionPrompt component |
| 6 | Conversion triggers wired (quittance + 3rd page) |
| 7 | Final verification |
