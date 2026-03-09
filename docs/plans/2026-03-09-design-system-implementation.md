# Design System Light-First — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform GererSCI from dark-only to light-first design system with unified components, simplified dashboard UX, and accessibility fixes.

**Architecture:** Enrich existing layout.css tokens (already has light/dark oklch variables) + refactor 3 existing components (EmptyState, KPI-Card, WorkspaceHeader) + create 2 new (StatusBadge, TabBar) + refactor all pages to consume them. CCPM orchestration with Kanban Pull.

**Tech Stack:** SvelteKit 2.x, Svelte 5 runes, Tailwind CSS 4, Storybook, Playwright E2E

**Design doc:** `docs/plans/2026-03-09-design-system-light-first.md`

---

## Phase T0 — Tokens (Critical Chain, sequential)

### Task 1: Change default theme to light

**Files:**
- Modify: `frontend/src/lib/stores/theme.ts:25`

**Step 1: Change writable default from 'dark' to 'light'**

In `theme.ts` line 25, change:
```typescript
const { subscribe, set, update } = writable<Theme>('light');
```

The `initialize()` function already respects `prefers-color-scheme: dark` and saved localStorage, so users who prefer dark will still get dark. This only changes the SSR/initial fallback.

**Step 2: Verify the app loads in light mode**

Run: `pnpm run dev` → open http://localhost:5173 → should render light theme (white background).
Clear localStorage `theme` key first to test fresh state.

**Step 3: Commit**

```bash
git add frontend/src/lib/stores/theme.ts
git commit -m "feat: switch default theme to light-first"
```

---

### Task 2: Add design system semantic tokens to layout.css

**Files:**
- Modify: `frontend/src/routes/layout.css:21-88`

**Step 1: Add --ds-* semantic tokens alongside existing oklch variables in :root**

Add after line 53 (end of existing :root block), before closing `}`:
```css
  /* ── Design System semantic tokens ── */
  --ds-accent: oklch(0.50 0.17 265);       /* indigo-600 */
  --ds-accent-hover: oklch(0.44 0.18 265); /* indigo-700 */
  --ds-accent-soft: oklch(0.96 0.03 265);  /* indigo-50 */
  --ds-accent-foreground: oklch(0.99 0.01 90);
  --ds-success: oklch(0.55 0.16 150);      /* green-600 */
  --ds-success-soft: oklch(0.96 0.04 150); /* green-50 */
  --ds-warning: oklch(0.65 0.16 75);       /* amber-600 */
  --ds-warning-soft: oklch(0.96 0.04 85);  /* amber-50 */
  --ds-error: oklch(0.58 0.22 27);         /* red-600 */
  --ds-error-soft: oklch(0.96 0.03 25);    /* red-50 */
  --ds-info: oklch(0.55 0.15 250);         /* blue-600 */
  --ds-info-soft: oklch(0.96 0.03 250);    /* blue-50 */
```

Add matching dark overrides inside `.dark` block (after line 87):
```css
  /* ── Design System semantic tokens (dark) ── */
  --ds-accent: oklch(0.70 0.14 265);
  --ds-accent-hover: oklch(0.76 0.12 265);
  --ds-accent-soft: oklch(0.25 0.06 265);
  --ds-accent-foreground: oklch(0.15 0.02 265);
  --ds-success: oklch(0.70 0.14 150);
  --ds-success-soft: oklch(0.25 0.06 150);
  --ds-warning: oklch(0.75 0.14 75);
  --ds-warning-soft: oklch(0.25 0.06 75);
  --ds-error: oklch(0.70 0.18 27);
  --ds-error-soft: oklch(0.25 0.06 27);
  --ds-info: oklch(0.70 0.12 250);
  --ds-info-soft: oklch(0.25 0.06 250);
```

**Step 2: Add @theme inline mappings**

Add inside `@theme inline` block (after line 125):
```css
  --color-ds-accent: var(--ds-accent);
  --color-ds-accent-hover: var(--ds-accent-hover);
  --color-ds-accent-soft: var(--ds-accent-soft);
  --color-ds-accent-foreground: var(--ds-accent-foreground);
  --color-ds-success: var(--ds-success);
  --color-ds-success-soft: var(--ds-success-soft);
  --color-ds-warning: var(--ds-warning);
  --color-ds-warning-soft: var(--ds-warning-soft);
  --color-ds-error: var(--ds-error);
  --color-ds-error-soft: var(--ds-error-soft);
  --color-ds-info: var(--ds-info);
  --color-ds-info-soft: var(--ds-info-soft);
```

**Step 3: Replace cyan/teal accent with indigo in existing sidebar tokens**

In `:root`, update sidebar-primary to use indigo:
```css
  --sidebar-primary: oklch(0.50 0.17 265);
```

**Step 4: Verify Tailwind consumes tokens**

Run: `pnpm run check`
Expected: 0 errors. Classes like `bg-ds-accent`, `text-ds-success` should be available.

**Step 5: Commit**

```bash
git add frontend/src/routes/layout.css
git commit -m "feat: add design system semantic tokens (indigo accent, functional colors)"
```

---

### Task 3: Update body background gradients for light-first

**Files:**
- Modify: `frontend/src/routes/layout.css:136-147`

**Step 1: Replace the dark-first gradient tones with light-friendly subtle gradient**

Replace body background-image in `@layer base`:
```css
  body {
    @apply bg-background text-foreground min-h-screen antialiased;
    font-family: "Space Grotesk", "Avenir Next", "Trebuchet MS", sans-serif;
    background-image:
      radial-gradient(circle at 12% -5%, oklch(0.92 0.04 265 / 0.15), transparent 38%),
      radial-gradient(circle at 85% 0%, oklch(0.92 0.03 150 / 0.10), transparent 35%),
      linear-gradient(180deg, oklch(0.99 0.005 265 / 0.5), oklch(0.98 0.003 265));
  }

  .dark body {
    background-image:
      radial-gradient(circle at 12% -5%, oklch(0.50 0.17 265 / 0.12), transparent 34%),
      radial-gradient(circle at 85% 0%, oklch(0.55 0.16 150 / 0.08), transparent 28%),
      linear-gradient(180deg, oklch(0.15 0.02 265 / 0.96), oklch(0.13 0.02 265 / 0.99));
  }
```

**Step 2: Verify visually**

Run dev server → light mode should show subtle indigo/green gradient, dark mode should show deep indigo tones.

**Step 3: Commit**

```bash
git add frontend/src/routes/layout.css
git commit -m "feat: update body gradients for light-first indigo theme"
```

---

### BUFFER 1: Verify tokens compile

Run: `pnpm run check && pnpm run build`
Expected: 0 errors, build succeeds.

---

## Phase T1 — Components (parallel, 6 agents)

### Task 4: Refactor KPI-Card.svelte to Svelte 5 runes + tokens (CRITICAL CHAIN)

**Files:**
- Modify: `frontend/src/lib/components/KPI-Card.svelte`
- Modify: `frontend/src/stories/components/KPI-Card.stories.svelte`

**Step 1: Migrate from `export let` to `$props()`**

KPI-Card.svelte currently uses `export let` (Svelte 4). Convert to Svelte 5 runes:

```svelte
<script lang="ts">
  import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '$lib/components/ui/card';
  import { cn } from '$lib/utils';

  type Trend = 'up' | 'down' | 'neutral';
  type Tone = 'default' | 'success' | 'warning' | 'danger' | 'accent';

  interface Props {
    label?: string;
    value?: string | number;
    caption?: string;
    trend?: Trend;
    trendValue?: string;
    tone?: Tone;
    loading?: boolean;
  }

  let {
    label = 'Indicateur',
    value = '-',
    caption = '',
    trend = 'neutral',
    trendValue = '',
    tone = 'default',
    loading = false
  }: Props = $props();

  const toneClasses: Record<Tone, string> = {
    default: 'border-border bg-card',
    success: 'border-ds-success/30 bg-ds-success-soft',
    warning: 'border-ds-warning/30 bg-ds-warning-soft',
    danger: 'border-ds-error/30 bg-ds-error-soft',
    accent: 'border-ds-accent/30 bg-ds-accent-soft'
  };

  const trendBadgeClasses: Record<Trend, string> = {
    up: 'bg-ds-success-soft text-ds-success',
    down: 'bg-ds-error-soft text-ds-error',
    neutral: 'bg-secondary text-secondary-foreground'
  };

  const trendIcons: Record<Trend, string> = {
    up: '↗',
    down: '↘',
    neutral: '→'
  };
</script>
```

**Step 2: Simplify the template — remove the top gradient bar**

Replace the Card template to use tokens instead of hardcoded oklch:

```svelte
<Card
  class={cn(
    'relative overflow-hidden border shadow-sm',
    toneClasses[tone]
  )}
  aria-busy={loading}
>
  <CardHeader class="pb-2">
    <CardDescription class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-muted-foreground">
      {label}
    </CardDescription>
    <CardTitle class="text-2xl font-semibold tracking-tight text-foreground">
      {#if loading}
        <span class="inline-flex h-8 w-28 animate-pulse rounded-md bg-muted"></span>
      {:else}
        {value}
      {/if}
    </CardTitle>
  </CardHeader>
  <CardContent class="pt-0">
    <div class="flex items-center justify-between gap-3">
      {#if caption}
        <p class="text-xs text-muted-foreground">{caption}</p>
      {/if}
      {#if trendValue}
        <span
          class={cn(
            'inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-semibold tracking-wide uppercase',
            trendBadgeClasses[trend]
          )}
        >
          <span>{trendIcons[trend]}</span>
          {trendValue}
        </span>
      {/if}
    </div>
  </CardContent>
</Card>
```

**Step 3: Update Storybook story**

Update `KPI-Card.stories.svelte` to pass new props format if needed.

**Step 4: Run tests + check**

Run: `pnpm run check && pnpm run test:unit`
Expected: 0 errors, all tests pass.

**Step 5: Commit**

```bash
git add frontend/src/lib/components/KPI-Card.svelte frontend/src/stories/components/KPI-Card.stories.svelte
git commit -m "refactor: migrate KPI-Card to Svelte 5 runes + design system tokens"
```

---

### Task 5: Create TabBar.svelte component (CRITICAL CHAIN)

**Files:**
- Create: `frontend/src/lib/components/TabBar.svelte`
- Create: `frontend/src/stories/components/TabBar.stories.svelte`

**Step 1: Create the component**

```svelte
<script lang="ts">
  interface Tab {
    id: string;
    label: string;
    badge?: number;
  }

  interface Props {
    tabs: Tab[];
    activeTab: string;
    onTabChange?: (id: string) => void;
  }

  let { tabs, activeTab, onTabChange }: Props = $props();
</script>

<div class="flex gap-1 overflow-x-auto border-b border-border" role="tablist">
  {#each tabs as tab (tab.id)}
    <button
      type="button"
      role="tab"
      aria-selected={activeTab === tab.id}
      class="relative flex shrink-0 items-center gap-2 px-4 py-2.5 text-sm font-medium whitespace-nowrap transition-colors
        {activeTab === tab.id
          ? 'text-ds-accent after:absolute after:inset-x-0 after:bottom-0 after:h-0.5 after:bg-ds-accent'
          : 'text-muted-foreground hover:text-foreground'}"
      onclick={() => onTabChange?.(tab.id)}
    >
      {tab.label}
      {#if tab.badge && tab.badge > 0}
        <span class="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-ds-error px-1.5 text-[11px] font-semibold text-white">
          {tab.badge}
        </span>
      {/if}
    </button>
  {/each}
</div>
```

**Step 2: Create Storybook story**

```svelte
<script module>
  import { defineMeta } from '@storybook/addon-svelte-csf';
  import TabBar from '$lib/components/TabBar.svelte';

  const { Story } = defineMeta({
    title: 'Components/TabBar',
    component: TabBar
  });
</script>

<Story name="Default">
  <TabBar
    tabs={[
      { id: 'flux', label: 'Flux' },
      { id: 'patrimoine', label: 'Patrimoine' },
      { id: 'documents', label: 'Documents' },
      { id: 'gouvernance', label: 'Gouvernance' },
      { id: 'analytique', label: 'Analytique' }
    ]}
    activeTab="flux"
  />
</Story>

<Story name="With Badge">
  <TabBar
    tabs={[
      { id: 'flux', label: 'Flux', badge: 3 },
      { id: 'patrimoine', label: 'Patrimoine' },
      { id: 'documents', label: 'Documents' }
    ]}
    activeTab="flux"
  />
</Story>
```

**Step 3: Run check**

Run: `pnpm run check`
Expected: 0 errors.

**Step 4: Commit**

```bash
git add frontend/src/lib/components/TabBar.svelte frontend/src/stories/components/TabBar.stories.svelte
git commit -m "feat: add TabBar design system component"
```

---

### Task 6: Create StatusBadge.svelte component (FC1)

**Files:**
- Create: `frontend/src/lib/components/StatusBadge.svelte`

**Step 1: Create the component**

```svelte
<script lang="ts">
  type Variant = 'info' | 'success' | 'warning' | 'error' | 'neutral';
  type Size = 'sm' | 'md';

  interface Props {
    text: string;
    variant?: Variant;
    size?: Size;
  }

  let { text, variant = 'neutral', size = 'sm' }: Props = $props();

  const variantClasses: Record<Variant, string> = {
    info: 'bg-ds-info-soft text-ds-info',
    success: 'bg-ds-success-soft text-ds-success',
    warning: 'bg-ds-warning-soft text-ds-warning',
    error: 'bg-ds-error-soft text-ds-error',
    neutral: 'bg-secondary text-secondary-foreground'
  };

  const sizeClasses: Record<Size, string> = {
    sm: 'px-2 py-0.5 text-[10px]',
    md: 'px-2.5 py-1 text-[11px]'
  };
</script>

<span class="inline-flex items-center rounded-full font-semibold uppercase tracking-wider {variantClasses[variant]} {sizeClasses[size]}">
  {text}
</span>
```

**Step 2: Commit**

```bash
git add frontend/src/lib/components/StatusBadge.svelte
git commit -m "feat: add StatusBadge design system component"
```

---

### Task 7: Refactor EmptyState — merge EmptyState + EmptyStateOperator (FC1)

**Files:**
- Modify: `frontend/src/lib/components/EmptyState.svelte`
- Delete: `frontend/src/lib/components/EmptyStateOperator.svelte`

**Step 1: Merge both components into one unified EmptyState**

Replace EmptyState.svelte with unified version:

```svelte
<script lang="ts">
  import { Button } from '$lib/components/ui/button';

  interface Action {
    label: string;
    href?: string;
    onclick?: () => void;
    variant?: 'default' | 'outline';
  }

  interface Props {
    icon?: any;
    eyebrow?: string;
    title: string;
    description?: string;
    actions?: Action[];
    align?: 'center' | 'left';
  }

  let {
    icon: Icon,
    eyebrow,
    title,
    description,
    actions = [],
    align = 'center'
  }: Props = $props();
</script>

<div class="rounded-2xl border border-dashed border-border bg-muted/50 px-6 py-10 {align === 'center' ? 'text-center' : 'text-left'}">
  {#if eyebrow}
    <p class="text-[0.68rem] font-semibold tracking-[0.18em] uppercase text-muted-foreground">{eyebrow}</p>
  {/if}
  {#if Icon}
    <div class="mb-4 {align === 'center' ? 'mx-auto' : ''} flex h-12 w-12 items-center justify-center rounded-full bg-muted">
      <Icon class="h-6 w-6 text-muted-foreground" />
    </div>
  {/if}
  <h3 class="text-sm font-semibold text-foreground {eyebrow ? 'mt-3 text-lg' : ''}">{title}</h3>
  {#if description}
    <p class="mt-1.5 max-w-sm text-sm text-muted-foreground {align === 'center' ? 'mx-auto' : ''}">{description}</p>
  {/if}
  {#if actions.length > 0}
    <div class="mt-5 flex flex-wrap gap-3 {align === 'center' ? 'justify-center' : ''}">
      {#each actions as action}
        {#if action.href}
          <Button href={action.href} variant={action.variant ?? 'default'} size="sm">{action.label}</Button>
        {:else if action.onclick}
          <Button onclick={action.onclick} variant={action.variant ?? 'default'} size="sm">{action.label}</Button>
        {/if}
      {/each}
    </div>
  {/if}
</div>
```

**Step 2: Find all EmptyStateOperator imports and replace**

Run: `grep -r "EmptyStateOperator" frontend/src/ --files-with-matches`

Replace each import with `EmptyState` and adapt props:
- `eyebrow` → same
- `primaryHref/primaryLabel` → `actions: [{ label, href }]`
- `secondaryHref/secondaryLabel` → `actions: [{ label, href, variant: 'outline' }]`
- Add `align="left"` where EmptyStateOperator was used

**Step 3: Delete EmptyStateOperator.svelte**

```bash
git rm frontend/src/lib/components/EmptyStateOperator.svelte
```

**Step 4: Run check + tests**

Run: `pnpm run check && pnpm run test:unit`

**Step 5: Commit**

```bash
git add -A
git commit -m "refactor: merge EmptyState + EmptyStateOperator into unified component"
```

---

### Task 8: Refactor WorkspaceHeader to use tokens (FC1)

**Files:**
- Modify: `frontend/src/lib/components/WorkspaceHeader.svelte`

**Step 1: Replace hardcoded dark: classes with token-based classes**

Replace the context card div (line 43) hardcoded classes with:
```
class="mt-2 max-w-xl rounded-xl border border-border bg-card px-4 py-4 shadow-sm"
```

The `sci-page-header`, `sci-eyebrow`, `sci-page-title`, `sci-page-subtitle` classes in layout.css already handle light/dark correctly via Tailwind dark: prefix — no changes needed for those.

**Step 2: Run check**

Run: `pnpm run check`

**Step 3: Commit**

```bash
git add frontend/src/lib/components/WorkspaceHeader.svelte
git commit -m "refactor: WorkspaceHeader uses design system tokens"
```

---

### Task 9: A11y — Add main landmark + page titles (FC5)

**Files:**
- Modify: `frontend/src/routes/+layout.svelte`
- Modify: `frontend/src/app.html` (if `<title>` missing)

**Step 1: Wrap main content area in `<main>` landmark**

In `+layout.svelte`, find the content div and wrap with `<main>`:
```svelte
<main class="flex-1 overflow-y-auto">
  {@render children?.()}
</main>
```

**Step 2: Add default `<title>` in app.html**

Ensure `<title>GererSCI — Gestion de SCI</title>` exists in `<head>`.

**Step 3: Add `<svelte:head>` with page-specific titles to key pages**

Each page should have:
```svelte
<svelte:head>
  <title>Dashboard — GererSCI</title>
  <meta name="description" content="Pilotez vos SCI depuis un tableau de bord unifié." />
</svelte:head>
```

Pages to update: /dashboard, /biens, /locataires, /loyers, /charges, /documents, /fiscalite, /associes, /pricing, /settings, /account, /login, /register

**Step 4: Run Lighthouse snapshot**

Verify SEO score improves from 60 to 90+.

**Step 5: Commit**

```bash
git add -A
git commit -m "fix: add main landmark, page titles and meta descriptions (a11y/SEO)"
```

---

### BUFFER 2: Verify components in Storybook

Run: `pnpm run storybook` → verify KPICard, TabBar, StatusBadge, EmptyState stories render correctly in light and dark themes.

Run: `pnpm run check && pnpm run test:unit`
Expected: 0 errors, all tests pass.

---

## Phase T2 — Page Refactoring (parallel, 6 agents)

### Task 10: Dashboard — simplify KPIs + use TabBar (CRITICAL CHAIN)

**Files:**
- Modify: `frontend/src/routes/dashboard/+page.svelte`

**Step 1: Replace inline tab implementation with TabBar component**

Import and use the new `TabBar` component instead of the inline button-based tabs.

**Step 2: Reduce Zone 2 from 8 KPIs to 4**

Keep: SCI SUIVIES, PATRIMOINE CONSOLIDÉ, LOYER CIBLE GLOBAL, RECOUVREMENT.
Move to Analytique tab: ENCAISSEMENTS SÉCURISÉS, BIENS ACTIFS, LOYERS DE LA SCI ACTIVE, FLUX ENCAISSÉS.

**Step 3: Import KPICard from design system**

Replace any inline KPI markup with the refactored `KPI-Card` component.

**Step 4: Run E2E tests**

Run: `pnpm run test:e2e`
Expected: 8/8 pass. Fix any selector changes in test files.

**Step 5: Commit**

```bash
git add frontend/src/routes/dashboard/+page.svelte frontend/tests/e2e/
git commit -m "refactor: dashboard uses TabBar + simplified 4 KPIs"
```

---

### Task 11: Workspaces-core — /biens, /locataires, /loyers (FC2)

**Files:**
- Modify: `frontend/src/routes/biens/+page.svelte`
- Modify: `frontend/src/routes/locataires/+page.svelte`
- Modify: `frontend/src/routes/loyers/+page.svelte`

**Step 1: Replace EmptyStateOperator with unified EmptyState**

Find all `EmptyStateOperator` imports, replace with `EmptyState` + adapt props (actions array, align="left").

**Step 2: Replace inline KPI cards with KPI-Card component**

Each workspace has inline styled KPI sections. Replace with `<KPICard>` imports.

**Step 3: Replace inline status badges with StatusBadge**

Find hardcoded badge spans → replace with `<StatusBadge text="..." variant="..." />`.

**Step 4: Add `<svelte:head>` with title + meta**

**Step 5: Run check + tests**

Run: `pnpm run check && pnpm run test:unit && pnpm run test:e2e`

**Step 6: Commit**

```bash
git add frontend/src/routes/biens/ frontend/src/routes/locataires/ frontend/src/routes/loyers/
git commit -m "refactor: biens/locataires/loyers consume design system components"
```

---

### Task 12: Workspaces-finance — /charges, /fiscalite (FC2)

**Files:**
- Modify: `frontend/src/routes/charges/+page.svelte`
- Modify: `frontend/src/routes/fiscalite/+page.svelte`

Same pattern as Task 11: EmptyState, KPICard, StatusBadge, svelte:head.

**Commit:**
```bash
git commit -m "refactor: charges/fiscalite consume design system components"
```

---

### Task 13: Workspaces-gov — /associes, /documents (FC2)

**Files:**
- Modify: `frontend/src/routes/associes/+page.svelte`
- Modify: `frontend/src/routes/documents/+page.svelte`

Same pattern. Also replace inline tab buttons in /associes with TabBar component.

**Commit:**
```bash
git commit -m "refactor: associes/documents consume design system components"
```

---

### Task 14: Pricing + Landing — light theme + cas d'usage (FC3)

**Files:**
- Modify: `frontend/src/routes/pricing/+page.svelte`
- Modify: `frontend/src/routes/+page.svelte`

**Step 1: Pricing — Replace "Ils nous font confiance" with real use cases**

Remove star ratings and fake trust signals. Replace with 3 concrete use case cards:

```
1. Gérant solo → "Marc gère 2 SCI familiales. Il génère ses quittances en un clic
   et suit ses loyers sans tableur."
2. Cabinet comptable → "Le cabinet Fidal accompagne 15 SCI. Chaque associé accède
   à son portefeuille, le cabinet centralise la conformité."
3. Opérateur patrimonial → "Patrimonia pilote 8 SCI en exploitation. Le dashboard
   consolide le cashflow et les échéances fiscales."
```

**Step 2: Landing — ensure light theme renders correctly**

Remove any dark-only hardcoded colors. The existing Tailwind dark: prefixes should handle it, but verify:
- Hero section gradients
- Feature cards backgrounds
- CTA button colors → switch to `bg-ds-accent`

**Step 3: Add svelte:head to both pages**

**Step 4: Commit**

```bash
git add frontend/src/routes/pricing/+page.svelte frontend/src/routes/+page.svelte
git commit -m "refactor: pricing use cases + landing light theme alignment"
```

---

### Task 15: Compte — /settings, /account (FC4)

**Files:**
- Modify: `frontend/src/routes/settings/+page.svelte`
- Modify: `frontend/src/routes/account/+page.svelte`

**Step 1: Replace inline tabs in /account with TabBar component**

**Step 2: Ensure all dark: hardcoded colors work correctly in light mode**

**Step 3: Add svelte:head**

**Step 4: Commit**

```bash
git add frontend/src/routes/settings/ frontend/src/routes/account/
git commit -m "refactor: settings/account consume TabBar + design system tokens"
```

---

### BUFFER 3: Full verification gate

Run ALL checks:
```bash
pnpm run check      # 0 errors
pnpm run lint        # clean
pnpm run test:unit   # all pass
pnpm run test:e2e    # 8/8 pass
```

Fix any failures before proceeding to Phase T3.

---

## Phase T3 — Accessibility + Final Audit (parallel, 2 agents)

### Task 16: Fix heading order across all pages

**Files:**
- All page files in `frontend/src/routes/`

**Step 1: Audit heading hierarchy**

Run in browser DevTools or via script: check every page has exactly one `<h1>`, followed by `<h2>`, then `<h3>`. No skipping levels.

Common fixes:
- WorkspaceHeader uses `<h1>` → correct
- Sub-sections using `<h2>` → verify not jumping to `<h4>`
- Card titles using `<h3>` → ensure parent section has `<h2>`

**Step 2: Fix link distinguishability**

In layout.css `@layer base`, add:
```css
  a:not([class]) {
    text-decoration: underline;
    text-underline-offset: 2px;
  }
```

This ensures inline links in text blocks are visually distinguishable without affecting styled component links.

**Step 3: Commit**

```bash
git add -A
git commit -m "fix: correct heading order + link distinguishability (a11y)"
```

---

### Task 17: Final Lighthouse re-audit

**Step 1: Run Lighthouse on landing page**

Target: Accessibility ≥ 95, SEO 100, Best Practices 100

**Step 2: Run Lighthouse on dashboard**

Target: Accessibility ≥ 95, SEO ≥ 90, Best Practices 100

**Step 3: Fix any remaining issues**

**Step 4: Take final screenshots (light + dark)**

**Step 5: Commit any final fixes**

```bash
git commit -m "fix: final accessibility and SEO improvements post-audit"
```

---

## Verification Checklist

- [ ] `pnpm run check` — 0 errors
- [ ] `pnpm run lint` — clean
- [ ] `pnpm run test:unit` — all pass
- [ ] `pnpm run test:e2e` — 8/8 pass
- [ ] `pnpm run test:high-value` — all pass
- [ ] Lighthouse landing: Accessibility ≥ 95, SEO 100
- [ ] Lighthouse dashboard: Accessibility ≥ 95, SEO ≥ 90
- [ ] Light theme renders correctly on all pages
- [ ] Dark theme toggle works on all pages
- [ ] No EmptyStateOperator imports remain
- [ ] All pages have `<svelte:head>` with title + meta
