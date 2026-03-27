# Hormozi Full Funnel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rework the entire GérerSCI funnel — from landing page to in-app UX — to maximize conversion using Hormozi's value equation adapted for French market psychology.

**Architecture:** Pure frontend changes across 9 files + 3 new components + 1 backend endpoint. No database migrations. All changes are additive (no breaking changes to existing behavior). The landing page `+page.svelte` gets the most edits (hero rewrite, new section, pricing modal integration).

**Tech Stack:** SvelteKit 2 + Svelte 5 runes, Tailwind CSS 4, lucide-svelte icons, existing UI primitives (Button, Badge, Card), FastAPI + Resend for email endpoint.

**Spec:** `docs/superpowers/specs/2026-03-27-hormozi-audit-full-funnel-design.md`

**Note:** Section 8 (Notification Preferences) is ALREADY IMPLEMENTED in `settings/+page.svelte` lines 167-745. Skipped in this plan.

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `frontend/src/routes/+page.svelte` | Modify | Hero rewrite, new "Comment ça marche" section, pricing modal integration |
| `frontend/src/routes/pricing/+page.svelte` | Modify | Value header, consent modal (remove inline checkbox) |
| `frontend/src/routes/simulateur-cerfa/+page.svelte` | Modify | Stronger product bridge CTA after results |
| `frontend/src/routes/(app)/onboarding/+page.svelte` | Modify | New step 4 value preview |
| `frontend/src/lib/components/CheckoutConfirmModal.svelte` | Create | Consent + plan recap modal |
| `frontend/src/lib/components/Celebration.svelte` | Create | Reusable milestone celebration overlay |
| `frontend/src/lib/components/FieldHint.svelte` | Create | Contextual help tooltip for form fields |
| `frontend/src/lib/components/fiche-bien/FicheBienLoyers.svelte` | Modify | Quittance toast, email send, status column |
| `frontend/src/lib/components/fiche-bien/FicheBienIdentite.svelte` | Modify | Field hints + completeness bar |
| `frontend/src/routes/(app)/dashboard/+page.svelte` | Modify | Milestone 3 celebration trigger |
| `backend/app/api/v1/quitus.py` | Modify | New send-email endpoint |
| `backend/app/services/quitus_service.py` | Modify | Email send logic |
| `frontend/src/lib/api.ts` | Modify | New sendQuittanceEmail() function |

---

## Task 1: Hero + CTA Rewrite

**Files:**
- Modify: `frontend/src/routes/+page.svelte` (hero section, lines ~210-310)

- [ ] **Step 1: Locate the hero section and read current content**

The hero section starts after the `<svelte:head>` block. Find the section containing "Votre SCI mérite mieux qu'un tableur Excel".

- [ ] **Step 2: Replace the hero badge, headline, subtitle, and CTA**

Replace the hero content block. Find the badge "Pour les gérants de SCI en France" and the h1 containing "Votre SCI mérite mieux qu'un tableur Excel" and replace the entire hero text block:

```svelte
<!-- Badge -->
<Badge variant="secondary" class="mb-6 px-4 py-1.5 text-sm font-medium">
	Utilisé par des gérants de SCI partout en France
</Badge>

<!-- Headline -->
<h1 class="text-4xl font-extrabold tracking-tight text-slate-900 sm:text-5xl lg:text-6xl dark:text-white">
	<span class="block">Vos loyers encaissés.</span>
	<span class="block bg-gradient-to-r from-blue-600 to-cyan-500 bg-clip-text text-transparent">
		Votre fiscalité claire.
	</span>
	<span class="block">Votre SCI sous contrôle.</span>
</h1>

<!-- Subtitle -->
<p class="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-slate-600 dark:text-slate-400">
	Tout ce qu'il faut pour piloter votre SCI en 10 minutes par mois —
	biens, baux, quittances, CERFA 2044, le tout au même endroit.
</p>

<!-- CTAs -->
<div class="mt-8 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
	<Button
		size="lg"
		class="bg-gradient-to-r from-blue-600 to-cyan-500 px-8 text-white hover:from-blue-700 hover:to-cyan-600"
		onclick={() => document.getElementById('comment-ca-marche')?.scrollIntoView({ behavior: 'smooth' })}
	>
		Voir comment ça marche
	</Button>
	<Button
		variant="outline"
		size="lg"
		onclick={() => document.getElementById('pricing')?.scrollIntoView({ behavior: 'smooth' })}
	>
		Comparer les plans
	</Button>
</div>
```

- [ ] **Step 3: Update the trust bar**

Find the trust bar below the CTAs (contains "Hébergé en Europe" or similar) and replace with:

```svelte
<div class="mt-8 flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm text-slate-500 dark:text-slate-400">
	<span class="flex items-center gap-1.5">🇫🇷 Hébergé en France</span>
	<span class="flex items-center gap-1.5">🔒 Conforme RGPD</span>
	<span class="flex items-center gap-1.5">💶 Satisfait ou remboursé 30j</span>
</div>
```

- [ ] **Step 4: Verify the page compiles**

Run: `cd frontend && pnpm run check 2>&1 | head -20`
Expected: No errors related to `+page.svelte`

- [ ] **Step 5: Commit**

```bash
git add frontend/src/routes/+page.svelte
git commit -m "feat(landing): rewrite hero — dream outcomes, scroll CTAs, FR trust bar"
```

---

## Task 2: "Comment ça marche" Section

**Files:**
- Modify: `frontend/src/routes/+page.svelte` (insert new section after hero screenshot, before feature sections)

- [ ] **Step 1: Add the new section after the hero screenshot section**

Find the comment `<!-- FEATURE SECTIONS -->` and insert BEFORE it:

```svelte
<!-- ============================================================ -->
<!-- COMMENT ÇA MARCHE -->
<!-- ============================================================ -->
<section id="comment-ca-marche" class="bg-white py-20 dark:bg-slate-900">
	<div class="mx-auto max-w-6xl px-4 sm:px-6 lg:px-8">
		<div class="mb-12 text-center">
			<Badge variant="secondary" class="mb-4 px-3 py-1 text-sm font-medium">Simple</Badge>
			<h2 class="text-3xl font-bold text-slate-900 sm:text-4xl dark:text-slate-100">
				Comment ça marche — en 3 étapes
			</h2>
		</div>

		<div class="grid gap-8 md:grid-cols-3">
			{#each [
				{
					step: '①',
					title: 'Créez votre SCI',
					time: '2 minutes',
					description: 'Nom, régime fiscal, c\'est tout. GérerSCI crée votre espace de gestion.',
					image: '/images/showcase-onboarding.webp',
					alt: 'Écran de création de SCI'
				},
				{
					step: '②',
					title: 'Ajoutez vos biens et locataires',
					time: '5 minutes',
					description: 'Adresse, loyer, bail — on vous guide étape par étape.',
					image: '/images/showcase-fiche-bien.webp',
					alt: 'Fiche bien avec détails du bail'
				},
				{
					step: '③',
					title: 'Pilotez en 10 min/mois',
					time: 'Chaque mois',
					description: 'Quittances, alertes impayés, CERFA 2044 — tout est automatisé.',
					image: '/images/showcase-dashboard-light.webp',
					alt: 'Tableau de bord avec KPIs'
				}
			] as card, i}
				<button
					onclick={() => openLightbox(i)}
					class="group cursor-zoom-in text-left"
				>
					<div class="rounded-xl border border-slate-200 bg-slate-50 p-6 transition-all duration-300 group-hover:shadow-lg group-hover:-translate-y-1 dark:border-slate-700 dark:bg-slate-800">
						<div class="mb-4 flex items-center gap-3">
							<span class="flex h-10 w-10 items-center justify-center rounded-full bg-blue-100 text-lg font-bold text-blue-600 dark:bg-blue-900/30 dark:text-blue-400">
								{card.step}
							</span>
							<span class="rounded-full bg-slate-200 px-2.5 py-0.5 text-xs font-medium text-slate-600 dark:bg-slate-700 dark:text-slate-400">
								{card.time}
							</span>
						</div>
						<h3 class="text-lg font-semibold text-slate-900 dark:text-slate-100">{card.title}</h3>
						<p class="mt-2 text-sm text-slate-600 dark:text-slate-400">{card.description}</p>
						<div class="mt-4 overflow-hidden rounded-lg border border-slate-200 dark:border-slate-700">
							<img
								src={card.image}
								alt={card.alt}
								class="w-full transition-transform duration-300 group-hover:scale-105"
								loading="lazy"
								decoding="async"
								width="400"
								height="250"
							/>
						</div>
					</div>
				</button>
			{/each}
		</div>
	</div>
</section>
```

- [ ] **Step 2: Verify the images exist**

Run: `ls frontend/static/images/showcase-*.webp 2>/dev/null | head -10`

If images don't exist with these exact names, adjust the `image` paths to match the actual screenshot filenames available in `frontend/static/images/`. Use whatever dashboard/fiche-bien/onboarding screenshots are available.

- [ ] **Step 3: Verify compilation**

Run: `cd frontend && pnpm run check 2>&1 | head -20`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/routes/+page.svelte
git commit -m "feat(landing): add 'Comment ça marche' 3-step section with screenshots"
```

---

## Task 3: CheckoutConfirmModal Component

**Files:**
- Create: `frontend/src/lib/components/CheckoutConfirmModal.svelte`

- [ ] **Step 1: Create the modal component**

```svelte
<script lang="ts">
	import { Button } from '$lib/components/ui/button';
	import { Check, Loader2, X } from 'lucide-svelte';

	interface Props {
		open: boolean;
		planName: string;
		planPrice: string;
		planPeriod: string;
		planFeatures: string[];
		loading: boolean;
		onConfirm: () => void;
		onCancel: () => void;
	}

	let { open, planName, planPrice, planPeriod, planFeatures, loading, onConfirm, onCancel }: Props = $props();
	let consentChecked = $state(false);

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape' && !loading) onCancel();
	}

	// Reset consent when modal opens
	$effect(() => {
		if (open) consentChecked = false;
	});
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open}
	<!-- Backdrop -->
	<div class="fixed inset-0 z-50 flex items-center justify-center p-4">
		<button
			class="absolute inset-0 bg-black/50 backdrop-blur-sm"
			onclick={() => !loading && onCancel()}
			aria-label="Fermer"
		></button>

		<!-- Modal -->
		<div class="relative z-10 w-full max-w-md rounded-2xl border border-slate-200 bg-white p-6 shadow-2xl dark:border-slate-700 dark:bg-slate-900">
			<!-- Close -->
			<button
				class="absolute right-4 top-4 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
				onclick={onCancel}
				disabled={loading}
				aria-label="Fermer"
			>
				<X class="h-5 w-5" />
			</button>

			<!-- Plan recap -->
			<h3 class="text-lg font-bold text-slate-900 dark:text-slate-100">
				Confirmer votre choix
			</h3>
			<div class="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800">
				<div class="flex items-baseline justify-between">
					<span class="text-base font-semibold text-slate-900 dark:text-slate-100">{planName}</span>
					<span class="text-lg font-bold text-blue-600 dark:text-blue-400">
						{planPrice} HT{planPeriod}
					</span>
				</div>
				<ul class="mt-3 space-y-1.5">
					{#each planFeatures.slice(0, 4) as feat}
						<li class="flex items-center gap-2 text-xs text-slate-600 dark:text-slate-400">
							<Check class="h-3.5 w-3.5 flex-shrink-0 text-blue-500" />
							{feat}
						</li>
					{/each}
					{#if planFeatures.length > 4}
						<li class="text-xs text-slate-400">+ {planFeatures.length - 4} autres fonctionnalités</li>
					{/if}
				</ul>
			</div>

			<!-- Legal consent -->
			<label class="mt-4 flex cursor-pointer items-start gap-3 rounded-lg border border-slate-200 p-3 text-left text-xs text-slate-600 transition-colors hover:border-blue-300 dark:border-slate-700 dark:text-slate-400 dark:hover:border-blue-600">
				<input
					type="checkbox"
					bind:checked={consentChecked}
					class="mt-0.5 h-4 w-4 flex-shrink-0 rounded border-slate-300 text-blue-600 focus:ring-blue-500 dark:border-slate-600"
				/>
				<span>
					Conformément à l'article L221-28 du Code de la consommation, je souhaite accéder
					immédiatement au Service et je reconnais expressément <strong>renoncer à mon droit
					de rétractation de 14 jours</strong>. Je bénéficie de la
					<a href="/cgv#garantie" class="text-blue-600 underline hover:text-blue-800 dark:text-blue-400" onclick|stopPropagation>garantie satisfait ou remboursé de 30 jours</a>.
				</span>
			</label>

			<!-- Actions -->
			<div class="mt-5 flex gap-3">
				<Button
					variant="outline"
					class="flex-1"
					onclick={onCancel}
					disabled={loading}
				>
					Annuler
				</Button>
				<Button
					class="flex-1 bg-blue-600 text-white hover:bg-blue-700"
					onclick={onConfirm}
					disabled={!consentChecked || loading}
				>
					{#if loading}
						<Loader2 class="mr-2 h-4 w-4 animate-spin" />
						Redirection...
					{:else}
						Confirmer et payer
					{/if}
				</Button>
			</div>

			<p class="mt-3 text-center text-xs text-slate-400 dark:text-slate-500">
				Paiement sécurisé · Garanti 30 jours · Annulation en 1 clic
			</p>
		</div>
	</div>
{/if}
```

- [ ] **Step 2: Verify compilation**

Run: `cd frontend && pnpm run check 2>&1 | head -20`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/components/CheckoutConfirmModal.svelte
git commit -m "feat: add CheckoutConfirmModal — plan recap + L221-28 consent"
```

---

## Task 4: Landing Page Pricing — Integrate Modal

**Files:**
- Modify: `frontend/src/routes/+page.svelte`

- [ ] **Step 1: Add import and state for the modal**

At the top of the script section, add the import:

```typescript
import CheckoutConfirmModal from '$lib/components/CheckoutConfirmModal.svelte';
```

Add state variables near the existing `checkoutLoading` declaration:

```typescript
let modalOpen = $state(false);
let modalPlanKey = $state('');
let modalPlanName = $state('');
let modalPlanPrice = $state('');
let modalPlanPeriod = $state('');
let modalPlanFeatures = $state<string[]>([]);
```

- [ ] **Step 2: Add a function to open the modal instead of direct checkout**

Add after the existing `createGuestCheckout` function:

```typescript
function openCheckoutModal(planKey: string) {
	const plan = plans.find((p: any) => p.key === planKey);
	if (!plan) return;
	modalPlanKey = planKey;
	modalPlanName = plan.name;
	modalPlanPrice = billingPeriod === 'month' ? `${plan.monthlyPrice}€` : `${plan.yearlyPrice}€`;
	modalPlanPeriod = billingPeriod === 'month' ? '/mois' : '/an';
	modalPlanFeatures = plan.features;
	modalOpen = true;
}

function handleModalConfirm() {
	createGuestCheckout(modalPlanKey);
}
```

- [ ] **Step 3: Change plan buttons to open modal instead of direct checkout**

In the pricing section, find the plan card `onclick` that calls `createGuestCheckout(plan.key)` and replace with `openCheckoutModal(plan.key)`. There are two instances: one for regular plans and one for the Fondateur offer.

For regular plans, change:
```svelte
onclick={() => createGuestCheckout(plan.key)}
```
to:
```svelte
onclick={() => openCheckoutModal(plan.key)}
```

For the Fondateur button, change:
```svelte
onclick={() => createGuestCheckout('lifetime')}
```
to:
```svelte
onclick={() => { modalPlanKey = 'lifetime'; modalPlanName = 'Fondateur'; modalPlanPrice = '500€'; modalPlanPeriod = ''; modalPlanFeatures = ['Tout Pilotage inclus — à vie', 'Ligne directe avec le fondateur', 'Accès beta aux nouvelles fonctionnalités']; modalOpen = true; }}
```

- [ ] **Step 4: Add the modal component at the end of the template**

Just before the closing lightbox markup (or at the very end of the template before `</section>` or similar), add:

```svelte
<CheckoutConfirmModal
	open={modalOpen}
	planName={modalPlanName}
	planPrice={modalPlanPrice}
	planPeriod={modalPlanPeriod}
	planFeatures={modalPlanFeatures}
	loading={checkoutLoading !== null}
	onConfirm={handleModalConfirm}
	onCancel={() => { modalOpen = false; }}
/>
```

- [ ] **Step 5: Verify compilation**

Run: `cd frontend && pnpm run check 2>&1 | head -20`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add frontend/src/routes/+page.svelte
git commit -m "feat(landing): integrate checkout confirm modal — consent after plan choice"
```

---

## Task 5: Pricing Page — Value Header + Modal

**Files:**
- Modify: `frontend/src/routes/pricing/+page.svelte`

- [ ] **Step 1: Add import for CheckoutConfirmModal**

Add at the top of the script:

```typescript
import CheckoutConfirmModal from '$lib/components/CheckoutConfirmModal.svelte';
```

Add state near existing state variables:

```typescript
let modalOpen = $state(false);
let modalPlanKey = $state('');
let modalPlanName = $state('');
let modalPlanPrice = $state('');
let modalPlanPeriod = $state('');
let modalPlanFeatures = $state<string[]>([]);
```

- [ ] **Step 2: Add openCheckoutModal function**

Add after `handlePlanClick`:

```typescript
function openCheckoutModal(planKey: string) {
	const plan = plans.find(p => p.key === planKey);
	if (!plan) return;
	modalPlanKey = planKey;
	modalPlanName = plan.name;
	modalPlanPrice = billingPeriod === 'month' ? `${plan.monthlyPrice}€` : `${plan.yearlyPrice}€`;
	modalPlanPeriod = billingPeriod === 'month' ? '/mois' : '/an';
	modalPlanFeatures = plan.features;
	modalOpen = true;
}

function handleModalConfirm() {
	modalOpen = false;
	handlePlanClick(modalPlanKey, null);
}
```

- [ ] **Step 3: Remove inline consent checkbox**

Delete the entire `<label>` block containing `consentRetractation` checkbox (around lines 195-206). Also remove the `consentRetractation` state variable from the script.

- [ ] **Step 4: Remove consent dependency from plan buttons**

Change the Button `disabled` prop from:
```svelte
disabled={checkoutLoading === plan.key || !consentRetractation}
```
to:
```svelte
disabled={checkoutLoading === plan.key}
```

Do the same for the Fondateur button.

- [ ] **Step 5: Change plan button onclick to open modal**

For regular plans, change:
```svelte
onclick={() => handlePlanClick(plan.key, plan.href)}
```
to:
```svelte
onclick={() => openCheckoutModal(plan.key)}
```

For the Fondateur button:
```svelte
onclick={() => { modalPlanKey = 'lifetime'; modalPlanName = 'Fondateur'; modalPlanPrice = '500€'; modalPlanPeriod = ''; modalPlanFeatures = ['Tout Pilotage inclus — à vie', 'Ligne directe avec le fondateur', 'Accès beta aux nouvelles fonctionnalités']; modalOpen = true; }}
```

- [ ] **Step 6: Add value header before pricing plans**

After the billing toggle div and before the `<div class="grid gap-8 md:grid-cols-2">`, insert:

```svelte
<!-- Value header -->
<div class="mx-auto mt-10 mb-10 max-w-2xl rounded-xl border border-blue-200 bg-blue-50 p-6 dark:border-blue-900 dark:bg-blue-950/30">
	<p class="mb-3 text-sm font-semibold text-blue-800 dark:text-blue-300">Ce que GérerSCI remplace :</p>
	<ul class="space-y-2">
		{#each [
			'Suivi des loyers et alertes impayés automatiques',
			'Génération de quittances PDF en 1 clic',
			'Pré-remplissage CERFA 2044 automatique',
			'Vue financière consolidée multi-SCI'
		] as item}
			<li class="flex items-center gap-2 text-sm text-blue-700 dark:text-blue-400">
				<Check class="h-4 w-4 flex-shrink-0 text-blue-500" />
				{item}
			</li>
		{/each}
	</ul>
	<p class="mt-3 text-xs text-blue-600 dark:text-blue-500">
		→ En moyenne, ça remplace 150€/mois de tableurs, erreurs et temps perdu.
	</p>
</div>
```

- [ ] **Step 7: Add modal at the end of the template**

Before the closing `</section>` tag, add:

```svelte
<CheckoutConfirmModal
	open={modalOpen}
	planName={modalPlanName}
	planPrice={modalPlanPrice}
	planPeriod={modalPlanPeriod}
	planFeatures={modalPlanFeatures}
	loading={checkoutLoading !== null}
	onConfirm={handleModalConfirm}
	onCancel={() => { modalOpen = false; }}
/>
```

- [ ] **Step 8: Verify compilation**

Run: `cd frontend && pnpm run check 2>&1 | head -20`
Expected: No errors

- [ ] **Step 9: Commit**

```bash
git add frontend/src/routes/pricing/+page.svelte
git commit -m "feat(pricing): add value header + checkout confirm modal, remove inline consent"
```

---

## Task 6: Simulateur CERFA — Product Bridge

**Files:**
- Modify: `frontend/src/routes/simulateur-cerfa/+page.svelte`

- [ ] **Step 1: Find the results section**

Search for where the CERFA simulation results are displayed (the section showing the calculated deficit/surplus). Look for the area after the calculation is complete.

- [ ] **Step 2: Add product bridge CTA after results**

After the results display (after the email capture gate / after the CTA area), add:

```svelte
<!-- Product bridge -->
{#if showResults}
	<div class="mt-8 rounded-xl border border-blue-200 bg-blue-50 p-6 dark:border-blue-900 dark:bg-blue-950/30">
		<p class="text-sm font-medium text-blue-800 dark:text-blue-300">
			📊 Ce calcul est une estimation simplifiée.
		</p>
		<p class="mt-2 text-sm text-blue-700 dark:text-blue-400">
			Avec GérerSCI, le CERFA 2044 se pré-remplit automatiquement à partir de vos loyers
			et charges réels — pas besoin de ressaisir.
		</p>
		<div class="mt-4 flex flex-col gap-3 sm:flex-row">
			<a
				href="/#comment-ca-marche"
				class="inline-flex items-center justify-center gap-2 rounded-lg border border-blue-300 bg-white px-4 py-2 text-sm font-medium text-blue-700 transition-colors hover:bg-blue-100 dark:border-blue-700 dark:bg-blue-900 dark:text-blue-300 dark:hover:bg-blue-800"
			>
				Voir comment ça marche →
			</a>
			<a
				href="/#pricing"
				class="inline-flex items-center justify-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700"
			>
				Démarrer maintenant →
			</a>
		</div>
	</div>
{/if}
```

Adjust the `showResults` variable name to match whatever boolean the component uses to indicate results are shown (could be a computed state or conditional in the template).

- [ ] **Step 3: Verify compilation**

Run: `cd frontend && pnpm run check 2>&1 | head -20`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/routes/simulateur-cerfa/+page.svelte
git commit -m "feat(simulateur): add product bridge CTA after CERFA results"
```

---

## Task 7: Onboarding Step 4 — Value Preview

**Files:**
- Modify: `frontend/src/routes/(app)/onboarding/+page.svelte`

- [ ] **Step 1: Replace step 4 content**

Find `{:else if currentStep === 4}` (around line 651). Replace the entire step 4 block (from `{:else if currentStep === 4}` to the next `{/if}`) with:

```svelte
{:else if currentStep === 4}
	<div class="text-center">
		<div
			class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900"
		>
			<Sparkles class="h-8 w-8 text-emerald-600 dark:text-emerald-400" />
		</div>
		<h2 class="text-xl font-bold text-slate-900 dark:text-slate-100">
			Votre SCI « {sciNom} » est configurée !
		</h2>
		<p class="mt-2 text-sm text-slate-600 dark:text-slate-400">
			Voici ce que GérerSCI a préparé pour vous :
		</p>

		<!-- KPI preview cards -->
		<div class="mt-6 grid grid-cols-3 gap-3">
			{#each [
				{ label: 'Bien actif', value: '1', icon: '🏠' },
				{ label: 'Bail en cours', value: '1', icon: '📄' },
				{ label: 'Prochain loyer', value: new Date(new Date().getFullYear(), new Date().getMonth() + 1, 1).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' }), icon: '📅' }
			] as kpi, i}
				<div
					class="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800"
					style="animation: fadeInUp 0.4s ease-out {i * 100}ms both"
				>
					<span class="text-2xl">{kpi.icon}</span>
					<p class="mt-2 text-lg font-bold text-slate-900 dark:text-slate-100">{kpi.value}</p>
					<p class="text-xs text-slate-500 dark:text-slate-400">{kpi.label}</p>
				</div>
			{/each}
		</div>

		<!-- Next actions -->
		<div class="mt-6 rounded-xl border border-slate-200 bg-slate-50 p-4 text-left dark:border-slate-700 dark:bg-slate-800">
			<p class="mb-3 text-sm font-medium text-slate-700 dark:text-slate-300">
				💡 Prochaines actions suggérées :
			</p>
			<ul class="space-y-2 text-sm text-slate-600 dark:text-slate-400">
				<li class="flex items-center gap-2">
					<span class="text-emerald-500">→</span>
					Enregistrer votre premier loyer (2 clics)
				</li>
				<li class="flex items-center gap-2">
					<span class="text-emerald-500">→</span>
					Générer votre première quittance PDF
				</li>
				<li class="flex items-center gap-2">
					<span class="text-emerald-500">→</span>
					Configurer les alertes de retard
				</li>
			</ul>
		</div>

		<div class="mt-6 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
			<Button onclick={() => handleFinish('loyer')} disabled={submitting}>
				{submitting ? 'Finalisation...' : 'Enregistrer mon premier loyer →'}
			</Button>
			<Button variant="outline" onclick={() => handleFinish('dashboard')} disabled={submitting}>
				Voir le tableau de bord
			</Button>
		</div>
	</div>
```

- [ ] **Step 2: Add CSS animation keyframes**

Add in the `<svelte:head>` or as a `<style>` block at the end of the file:

```svelte
<style>
	@keyframes fadeInUp {
		from {
			opacity: 0;
			transform: translateY(12px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
</style>
```

- [ ] **Step 3: Verify compilation**

Run: `cd frontend && pnpm run check 2>&1 | head -20`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/routes/\(app\)/onboarding/+page.svelte
git commit -m "feat(onboarding): replace step 4 with value preview — KPI cards + next actions"
```

---

## Task 8: Celebration.svelte Component

**Files:**
- Create: `frontend/src/lib/components/Celebration.svelte`

- [ ] **Step 1: Create the component**

```svelte
<script lang="ts">
	import { onMount } from 'svelte';
	import { Check, Target, FileText } from 'lucide-svelte';

	interface Props {
		type: 'checkmark' | 'badge' | 'confetti';
		title: string;
		subtitle: string;
		duration?: number;
		onDismiss?: () => void;
	}

	let { type, title, subtitle, duration = 3000, onDismiss }: Props = $props();
	let visible = $state(true);
	let particles = $state<{ x: number; y: number; color: string; delay: number }[]>([]);

	onMount(() => {
		if (type === 'confetti') {
			const colors = ['#3b82f6', '#06b6d4', '#10b981', '#f59e0b', '#8b5cf6'];
			particles = Array.from({ length: 15 }, () => ({
				x: Math.random() * 100,
				y: Math.random() * 100,
				color: colors[Math.floor(Math.random() * colors.length)],
				delay: Math.random() * 500
			}));
		}

		const timer = setTimeout(() => {
			visible = false;
			onDismiss?.();
		}, duration);

		return () => clearTimeout(timer);
	});

	function dismiss() {
		visible = false;
		onDismiss?.();
	}
</script>

{#if visible}
	<button
		class="fixed inset-0 z-50 flex items-center justify-center p-4"
		onclick={dismiss}
		aria-label="Fermer"
	>
		<!-- Backdrop (subtle) -->
		<div class="absolute inset-0 bg-black/10" style="animation: fadeIn 0.2s ease-out"></div>

		<!-- Confetti particles -->
		{#if type === 'confetti'}
			{#each particles as p}
				<div
					class="pointer-events-none absolute h-2 w-2 rounded-full"
					style="left: {p.x}%; top: {p.y}%; background: {p.color}; animation: confettiFall 2s ease-out {p.delay}ms both"
				></div>
			{/each}
		{/if}

		<!-- Content -->
		<div
			class="relative z-10 w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-6 text-center shadow-2xl dark:border-slate-700 dark:bg-slate-900"
			style="animation: scaleIn 0.3s ease-out"
		>
			<!-- Icon -->
			{#if type === 'checkmark'}
				<div class="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-900" style="animation: checkDraw 0.5s ease-out 0.2s both">
					<Check class="h-7 w-7 text-emerald-600 dark:text-emerald-400" />
				</div>
			{:else if type === 'badge'}
				<div class="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900" style="animation: slideIn 0.4s ease-out">
					<FileText class="h-7 w-7 text-blue-600 dark:text-blue-400" />
				</div>
			{:else}
				<div class="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-amber-100 dark:bg-amber-900">
					<Target class="h-7 w-7 text-amber-600 dark:text-amber-400" />
				</div>
			{/if}

			<h3 class="text-base font-bold text-slate-900 dark:text-slate-100">{title}</h3>
			<p class="mt-1.5 text-sm text-slate-600 dark:text-slate-400">{subtitle}</p>

			<p class="mt-3 text-xs text-slate-400">Cliquez pour fermer</p>
		</div>
	</button>
{/if}

<style>
	@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
	@keyframes scaleIn { from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: scale(1); } }
	@keyframes slideIn { from { opacity: 0; transform: translateX(-20px); } to { opacity: 1; transform: translateX(0); } }
	@keyframes checkDraw { from { opacity: 0; transform: scale(0.5); } to { opacity: 1; transform: scale(1); } }
	@keyframes confettiFall {
		0% { opacity: 1; transform: translateY(-20px) rotate(0deg); }
		100% { opacity: 0; transform: translateY(100vh) rotate(720deg); }
	}
</style>
```

- [ ] **Step 2: Verify compilation**

Run: `cd frontend && pnpm run check 2>&1 | head -20`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/components/Celebration.svelte
git commit -m "feat: add Celebration component — checkmark, badge, confetti overlays"
```

---

## Task 9: Milestone Integrations (3 trigger points)

**Files:**
- Modify: `frontend/src/lib/components/fiche-bien/FicheBienLoyers.svelte` (milestone 1 + 2)
- Modify: `frontend/src/routes/(app)/dashboard/+page.svelte` (milestone 3)

- [ ] **Step 1: Add milestone 1 — first loyer — to FicheBienLoyers**

At the top of the script section in `FicheBienLoyers.svelte`, add import:

```typescript
import Celebration from '$lib/components/Celebration.svelte';
```

Add state:

```typescript
let showCelebration = $state<{ type: 'checkmark' | 'badge' | 'confetti'; title: string; subtitle: string } | null>(null);
```

In the `handleCreateLoyer` function, after the successful API call (after `loyers = ...` reload), add:

```typescript
// Milestone: first loyer
if (!localStorage.getItem('milestone_first_loyer')) {
	localStorage.setItem('milestone_first_loyer', 'true');
	showCelebration = {
		type: 'checkmark',
		title: 'Premier loyer enregistré !',
		subtitle: 'Votre suivi de trésorerie commence. GérerSCI calcule maintenant votre taux de recouvrement automatiquement.'
	};
}
```

- [ ] **Step 2: Add milestone 2 — first quittance — to FicheBienLoyers**

In the `handleGenerateQuittance` function (or however the quittance generation is named), after successful PDF generation, add:

```typescript
// Milestone: first quittance
if (!localStorage.getItem('milestone_first_quittance')) {
	localStorage.setItem('milestone_first_quittance', 'true');
	showCelebration = {
		type: 'badge',
		title: 'Quittance générée !',
		subtitle: 'Vos locataires reçoivent un document professionnel conforme. Fini les modèles Word.'
	};
}
```

- [ ] **Step 3: Add Celebration component to FicheBienLoyers template**

At the end of the template (before the last closing tag), add:

```svelte
{#if showCelebration}
	<Celebration
		type={showCelebration.type}
		title={showCelebration.title}
		subtitle={showCelebration.subtitle}
		onDismiss={() => { showCelebration = null; }}
	/>
{/if}
```

- [ ] **Step 4: Add milestone 3 — dashboard complete — to dashboard**

In `frontend/src/routes/(app)/dashboard/+page.svelte`, add import:

```typescript
import Celebration from '$lib/components/Celebration.svelte';
```

Add state:

```typescript
let showCelebration = $state(false);
```

After the dashboard data has loaded (in the onMount or after the fetch succeeds), check:

```typescript
// Milestone: dashboard complete
if (data.sci_count >= 1 && data.biens_count >= 1 && !localStorage.getItem('milestone_dashboard_complete')) {
	// Check if user has at least 1 loyer (approximate via taux_recouvrement > 0 or cashflow_net !== 0)
	if (data.taux_recouvrement > 0 || data.cashflow_net !== 0) {
		localStorage.setItem('milestone_dashboard_complete', 'true');
		showCelebration = true;
	}
}
```

Add to the template:

```svelte
{#if showCelebration}
	<Celebration
		type="confetti"
		title="Votre SCI est 100% opérationnelle"
		subtitle="Loyers, quittances, fiscalité — tout est en place. GérerSCI travaille pour vous."
		onDismiss={() => { showCelebration = false; }}
	/>
{/if}
```

- [ ] **Step 5: Verify compilation**

Run: `cd frontend && pnpm run check 2>&1 | head -20`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/components/fiche-bien/FicheBienLoyers.svelte frontend/src/routes/\(app\)/dashboard/+page.svelte
git commit -m "feat: add 3 celebration milestones — first loyer, first quittance, dashboard complete"
```

---

## Task 10: Quittance UX — Toast + Status Column

**Files:**
- Modify: `frontend/src/lib/components/fiche-bien/FicheBienLoyers.svelte`

- [ ] **Step 1: Improve quittance generation feedback**

In the quittance generation handler, replace the `window.open(url)` pattern with a toast that includes actions. After the PDF URL is received:

```typescript
// Replace: window.open(pdfUrl, '_blank');
// With toast + optional window.open:
addToast({
	title: `Quittance ${periodLabel} générée`,
	description: 'Ouvrir le PDF · Envoyer par email',
	variant: 'success',
	timeoutMs: 8000
});
window.open(pdfUrl, '_blank');
```

Import `addToast` if not already imported:
```typescript
import { addToast } from '$lib/components/ui/toast';
```

- [ ] **Step 2: Add quittance status indicator to loyer table**

In the table header row, add a new column header after the "Statut" column:

```svelte
<th class="px-3 py-2 text-left text-xs font-medium text-slate-500 dark:text-slate-400">Quittance</th>
```

In the table body rows, add a new cell after the status cell. This requires checking if a quittance exists for each loyer. Since the current data model doesn't track quittance existence per loyer, use a simple icon button that triggers generation:

```svelte
<td class="px-3 py-2">
	{#if loyer.statut === 'paye'}
		<button
			class="text-slate-400 hover:text-blue-600 dark:hover:text-blue-400"
			title="Générer la quittance"
			onclick={() => handleGenerateQuittance(loyer)}
		>
			<FileText class="h-4 w-4" />
		</button>
	{:else}
		<span class="text-slate-300 dark:text-slate-600">—</span>
	{/if}
</td>
```

Import `FileText` from lucide-svelte if not already imported.

- [ ] **Step 3: Verify compilation**

Run: `cd frontend && pnpm run check 2>&1 | head -20`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/components/fiche-bien/FicheBienLoyers.svelte
git commit -m "feat(loyers): add quittance toast feedback + status column in table"
```

---

## Task 11: Quittance Email Send — Backend Endpoint

**Files:**
- Modify: `backend/app/api/v1/quitus.py`
- Modify: `backend/app/services/quitus_service.py`
- Modify: `frontend/src/lib/api.ts`

- [ ] **Step 1: Add send-email endpoint to quitus.py**

At the end of `backend/app/api/v1/quitus.py`, add:

```python
@router.post("/send-email/{filename}", status_code=200)
@limiter.limit("10/minute")
async def send_quittance_email(
    request: Request,
    filename: str,
    user=Depends(get_current_user),
):
    """Send a generated quittance PDF to the tenant by email."""
    import structlog
    from app.core.supabase_client import get_supabase_service_client
    from app.services.email_service import send_email_with_retry

    logger = structlog.get_logger()

    # Validate filename
    if not validate_filename(filename):
        raise GererSCIException(status_code=400, detail="Nom de fichier invalide.")

    # Extract sci_id from filename to verify access
    sci_id = extract_sci_id_from_filename(filename)
    if not sci_id:
        raise GererSCIException(status_code=400, detail="Impossible d'extraire l'ID SCI du fichier.")

    await verify_quitus_download_access(request, user, sci_id)

    # Get enrichment data to find tenant email
    client = get_supabase_service_client()

    # Download PDF from storage
    try:
        pdf_bytes = client.storage.from_("quittances").download(filename)
    except Exception:
        raise GererSCIException(status_code=404, detail="Quittance introuvable dans le stockage.")

    # Find tenant email from the bail associated with this quittance
    # Filename format: quitus_{sci_id}_{bien_id}_{period}.pdf
    parts = filename.replace(".pdf", "").split("_")
    if len(parts) < 4:
        raise GererSCIException(status_code=400, detail="Format de fichier non reconnu.")

    bien_id = parts[2]

    # Get active bail for this bien
    bail_resp = client.table("baux").select("id").eq("id_bien", bien_id).eq("statut", "actif").limit(1).execute()
    if not bail_resp.data:
        raise GererSCIException(status_code=404, detail="Aucun bail actif trouvé pour ce bien.")

    bail_id = bail_resp.data[0]["id"]

    # Get locataires via bail_locataires join
    loc_resp = (
        client.table("bail_locataires")
        .select("locataire_id, locataires(email, nom)")
        .eq("bail_id", bail_id)
        .execute()
    )

    if not loc_resp.data:
        raise GererSCIException(status_code=404, detail="Aucun locataire associé à ce bail.")

    # Find first locataire with email
    tenant_email = None
    tenant_name = None
    for entry in loc_resp.data:
        loc = entry.get("locataires", {})
        if loc and loc.get("email"):
            tenant_email = loc["email"]
            tenant_name = loc.get("nom", "Locataire")
            break

    if not tenant_email:
        raise GererSCIException(
            status_code=400,
            detail="Aucun email renseigné pour le locataire. Ajoutez l'email dans l'onglet Bail."
        )

    # Send email with PDF attachment
    period = parts[3] if len(parts) > 3 else "période"
    await send_email_with_retry(
        to=tenant_email,
        subject=f"Votre quittance de loyer — {period}",
        html=f"<p>Bonjour {tenant_name},</p><p>Veuillez trouver ci-joint votre quittance de loyer pour la période {period}.</p><p>Cordialement,<br>Votre gestionnaire SCI</p>",
        attachments=[{"filename": filename, "content": pdf_bytes, "content_type": "application/pdf"}],
    )

    logger.info("quittance_email_sent", filename=filename, to=tenant_email)
    return {"message": f"Quittance envoyée à {tenant_email}"}
```

Note: The `send_email_with_retry` function may need to be adapted to support attachments. Check the existing implementation. If it doesn't support attachments, use `resend.Emails.send()` directly with the attachment parameter.

- [ ] **Step 2: Add frontend API function**

In `frontend/src/lib/api.ts`, add (or in the appropriate api module file):

```typescript
export async function sendQuittanceEmail(filename: string): Promise<{ message: string }> {
	const res = await apiFetch(`/api/v1/quitus/send-email/${encodeURIComponent(filename)}`, {
		method: 'POST',
	});
	return res;
}
```

- [ ] **Step 3: Run backend tests**

Run: `cd backend && PYTHONPATH=. pytest tests/ -x -q 2>&1 | tail -10`
Expected: All existing tests pass (the new endpoint is additive)

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/v1/quitus.py frontend/src/lib/api.ts
git commit -m "feat(quitus): add POST /send-email/{filename} endpoint + frontend API"
```

---

## Task 12: FieldHint.svelte + Completeness Bar

**Files:**
- Create: `frontend/src/lib/components/FieldHint.svelte`

- [ ] **Step 1: Create the FieldHint component**

```svelte
<script lang="ts">
	import { Info } from 'lucide-svelte';

	interface Props {
		text: string;
	}

	let { text }: Props = $props();
	let showTooltip = $state(false);
</script>

<span class="relative ml-1 inline-block">
	<button
		class="inline-flex items-center text-slate-400 hover:text-blue-500 dark:text-slate-500 dark:hover:text-blue-400"
		onmouseenter={() => { showTooltip = true; }}
		onmouseleave={() => { showTooltip = false; }}
		onclick={() => { showTooltip = !showTooltip; }}
		aria-label="Plus d'informations"
		type="button"
	>
		<Info class="h-3.5 w-3.5" />
	</button>
	{#if showTooltip}
		<div
			class="absolute bottom-full left-1/2 z-20 mb-2 w-56 -translate-x-1/2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs leading-relaxed text-slate-600 shadow-lg dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400"
			role="tooltip"
		>
			{text}
			<div class="absolute left-1/2 top-full -translate-x-1/2 border-4 border-transparent border-t-white dark:border-t-slate-800"></div>
		</div>
	{/if}
</span>
```

- [ ] **Step 2: Verify compilation**

Run: `cd frontend && pnpm run check 2>&1 | head -20`
Expected: No errors

- [ ] **Step 3: Commit**

```bash
git add frontend/src/lib/components/FieldHint.svelte
git commit -m "feat: add FieldHint tooltip component for contextual field guidance"
```

---

## Task 13: FicheBienIdentite — Hints + Completeness Bar

**Files:**
- Modify: `frontend/src/lib/components/fiche-bien/FicheBienIdentite.svelte`

- [ ] **Step 1: Add import for FieldHint**

At the top of the script in `FicheBienIdentite.svelte`:

```typescript
import FieldHint from '$lib/components/FieldHint.svelte';
```

- [ ] **Step 2: Add completeness calculation**

Add a derived state after the form state variables:

```typescript
const fieldHints: Record<string, string> = {
	surface_m2: 'Obligatoire pour le bail et le calcul de la taxe foncière. Loi Boutin pour les locations.',
	dpe_classe: 'Obligatoire dans toute annonce et bail depuis 2023. Les logements F et G sont progressivement interdits à la location.',
	prix_acquisition: 'Nécessaire pour calculer votre rentabilité et la plus-value en cas de revente. Frais de notaire inclus.',
	type_locatif: 'Détermine le régime fiscal applicable (micro-foncier vs réel) et les obligations déclaratives.',
	type_bien: 'Permet d\'adapter les calculs de charges et les obligations réglementaires.'
};

const completenessFields = ['adresse', 'ville', 'code_postal', 'type_bien', 'type_locatif', 'surface_m2', 'nb_pieces', 'dpe_classe', 'prix_acquisition', 'loyer_cc'];

let completeness = $derived(() => {
	if (!bien) return { filled: 0, total: completenessFields.length, percent: 0, missing: [] as string[] };
	let filled = 0;
	const missing: string[] = [];
	for (const f of completenessFields) {
		const val = (bien as any)[f];
		if (val !== null && val !== undefined && val !== '' && val !== 0) {
			filled++;
		} else {
			missing.push(f);
		}
	}
	const percent = Math.round((filled / completenessFields.length) * 100);
	return { filled, total: completenessFields.length, percent, missing };
});

const completenessColor = $derived(() => {
	const p = completeness().percent;
	if (p >= 80) return 'bg-emerald-500';
	if (p >= 50) return 'bg-amber-500';
	return 'bg-rose-500';
});

const completenessMessage = $derived(() => {
	const m = completeness().missing;
	if (m.length === 0) return '';
	const labels: Record<string, string> = {
		dpe_classe: 'DPE', prix_acquisition: 'prix d\'acquisition', surface_m2: 'surface',
		type_locatif: 'type de location', type_bien: 'type de bien', loyer_cc: 'loyer',
		nb_pieces: 'nombre de pièces', adresse: 'adresse', ville: 'ville', code_postal: 'code postal'
	};
	const top = m.slice(0, 2).map(f => labels[f] || f);
	if (top.some(t => t === 'DPE' || t === 'prix d\'acquisition')) {
		return `Complétez le ${top.join(' et le ')} pour débloquer le calcul de rentabilité.`;
	}
	return `Complétez le ${top.join(' et le ')} pour enrichir votre fiche.`;
});
```

- [ ] **Step 3: Add completeness bar at the top of the component template**

Just after the opening card/container div and before the edit button, add:

```svelte
{#if completeness().percent < 100}
	<div class="mb-4 rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-800">
		<div class="flex items-center justify-between text-sm">
			<span class="text-slate-600 dark:text-slate-400">
				Profil du bien : {completeness().filled}/{completeness().total} champs renseignés
			</span>
			<span class="font-medium text-slate-700 dark:text-slate-300">{completeness().percent}%</span>
		</div>
		<div class="mt-2 h-1.5 w-full rounded-full bg-slate-200 dark:bg-slate-700">
			<div
				class="h-full rounded-full transition-all duration-500 {completenessColor()}"
				style="width: {completeness().percent}%"
			></div>
		</div>
		{#if completenessMessage()}
			<p class="mt-2 text-xs text-slate-500 dark:text-slate-400">
				💡 {completenessMessage()}
			</p>
		{/if}
	</div>
{/if}
```

- [ ] **Step 4: Add FieldHint to relevant form labels**

In the edit mode form, find labels for: surface, DPE, prix acquisition, type locatif, type bien. Add `<FieldHint text={fieldHints.field_name} />` after each label text.

Example — for the surface field label:
```svelte
<label for="surface" class="mb-1 block text-sm font-medium text-slate-700 dark:text-slate-300">
	Surface (m²) <FieldHint text={fieldHints.surface_m2} />
</label>
```

Do the same for:
- DPE label → `<FieldHint text={fieldHints.dpe_classe} />`
- Prix d'acquisition label → `<FieldHint text={fieldHints.prix_acquisition} />`
- Type de location label → `<FieldHint text={fieldHints.type_locatif} />`
- Type de bien label → `<FieldHint text={fieldHints.type_bien} />`

- [ ] **Step 5: Verify compilation**

Run: `cd frontend && pnpm run check 2>&1 | head -20`
Expected: No errors

- [ ] **Step 6: Commit**

```bash
git add frontend/src/lib/components/fiche-bien/FicheBienIdentite.svelte
git commit -m "feat(fiche-bien): add contextual field hints + completeness bar"
```

---

## Task 14: Final Verification

- [ ] **Step 1: Run full frontend check**

Run: `cd frontend && pnpm run check`
Expected: 0 errors, 0 warnings (or same baseline as before)

- [ ] **Step 2: Run frontend build**

Run: `cd frontend && pnpm run build`
Expected: Build succeeds

- [ ] **Step 3: Run backend tests**

Run: `cd backend && PYTHONPATH=. pytest -x -q`
Expected: All tests pass

- [ ] **Step 4: Final commit if any fixes needed**

```bash
git add -A
git commit -m "fix: resolve any compilation issues from funnel audit implementation"
```

---

## Summary

| Task | Section | Key Deliverable |
|------|---------|----------------|
| 1 | Hero | Dream outcomes headline + scroll CTAs |
| 2 | Aperçu | "Comment ça marche" 3-step section |
| 3 | Modal | CheckoutConfirmModal.svelte |
| 4 | Landing pricing | Modal integration, remove direct checkout |
| 5 | /pricing page | Value header + modal, remove inline consent |
| 6 | Simulateur | Product bridge CTA |
| 7 | Onboarding | Step 4 value preview with KPI cards |
| 8 | Celebration | Celebration.svelte component |
| 9 | Milestones | 3 trigger points (loyer, quittance, dashboard) |
| 10 | Quittance UX | Toast feedback + status column |
| 11 | Backend | Send quittance email endpoint |
| 12 | FieldHint | Tooltip component |
| 13 | Fiche bien | Hints + completeness bar |
| 14 | Verification | Full check + build + tests |

**Section 8 (Notification Preferences)**: Already implemented in `settings/+page.svelte` — no work needed.
