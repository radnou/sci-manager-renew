# Frontend CRUD Wiring — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire 15 dead UI buttons to backend APIs via modal forms, toast undo, and typed API functions.

**Architecture:** Reusable CrudModal + DatePopover components, extended toast system with undo, 8 modal forms per domain, targeted per-section refetch after mutations. All state via Svelte 5 runes (`$state`, `$derived`, `$props`).

**Tech Stack:** SvelteKit 2.x, TypeScript, Tailwind CSS 4, Svelte 5 runes, existing `apiFetch<T>` in `$lib/api.ts`

**Spec:** `docs/superpowers/specs/2026-03-11-frontend-crud-wiring-design.md`

---

## Chunk 1: Foundation Layer (API types + CrudModal + Toast Undo + DatePopover)

### Task 1: Add missing types + type existing `any` returns in `api.ts`

**Files:**
- Modify: `frontend/src/lib/api.ts`
- Test: `frontend/src/lib/api.test.ts` (existing — verify no regressions)

- [ ] **Step 1: Add new types after existing `FraisAgenceEmbed` (line ~677)**

```typescript
// After FraisAgenceEmbed definition (~line 677)

export type LoyerEmbed = {
  id: number;
  date_loyer: string;
  montant: number;
  statut: LoyerStatus;
  quitus_genere: boolean;
  date_paiement?: string | null;
};

export type ChargeEmbed = {
  id: number;
  type_charge: string;
  montant: number;
  date_paiement: string;
};

export type ChargeCreate = {
  type_charge: string;
  montant: number;
  date_paiement: string;
};

export type PnoCreate = {
  assureur: string;
  numero_contrat?: string;
  prime_annuelle: number;
  date_debut: string;
  date_fin?: string;
};

export type PnoUpdate = Partial<PnoCreate>;

export type FraisCreate = {
  type_frais: string;
  montant: number;
  date_frais: string;
  description?: string;
};

export type InviteAssociePayload = {
  nom: string;
  email?: string | null;
  part: number;
  role: string;
};

export type AssocieEmbed = {
  id: number | string;
  nom: string;
  email: string | null;
  role: string | null;
  part: number | null;
};

export type BailCreate = {
  date_debut: string;
  date_fin?: string;
  loyer_hc: number;
  charges_provisions?: number;
  depot_garantie?: number;
  revision_indice?: string;
};

export type BailUpdate = Partial<BailCreate>;
```

- [ ] **Step 2: Type `FicheBien.loyers_recents` and `charges_list`**

Change in `FicheBien` type (~line 694):
```typescript
// Before:
loyers_recents: Array<any>;
charges_list: Array<any>;
// After:
loyers_recents: LoyerEmbed[];
charges_list: ChargeEmbed[];
```

- [ ] **Step 3: Type existing function return types**

Replace `any` returns in these functions:
```typescript
// ~line 725
export async function fetchSciBiensList(sciId: EntityId): Promise<Bien[]> {
// ~line 729
export async function createBienForSci(sciId: EntityId, data: BienCreatePayload): Promise<Bien> {
// ~line 737
export async function createLoyerForBien(sciId: EntityId, bienId: EntityId, data: LoyerCreatePayload): Promise<LoyerEmbed> {
// ~line 751
export async function fetchBienBaux(sciId: EntityId, bienId: EntityId): Promise<BailEmbed[]> {
// ~line 755
export async function createBail(sciId: EntityId, bienId: EntityId, data: BailCreate): Promise<BailEmbed> {
// ~line 763
export async function updateBail(sciId: EntityId, bienId: EntityId, bailId: number, data: BailUpdate): Promise<BailEmbed> {
// ~line 812
export async function fetchBienCharges(sciId: EntityId, bienId: EntityId): Promise<ChargeEmbed[]> {
// ~line 816
export async function fetchBienPno(sciId: EntityId, bienId: EntityId): Promise<AssurancePnoEmbed[]> {
// ~line 820
export async function fetchBienFraisAgence(sciId: EntityId, bienId: EntityId): Promise<FraisAgenceEmbed[]> {
// ~line 824
export async function fetchSciAssociesList(sciId: EntityId): Promise<AssocieEmbed[]> {
```

- [ ] **Step 4: Add 8 new API functions after `fetchSciAssociesList` (~line 826)**

```typescript
// --- Charge mutations ---
export async function createChargeForBien(
  sciId: EntityId, bienId: EntityId, data: ChargeCreate
): Promise<ChargeEmbed> {
  return apiFetch(`/api/v1/scis/${sciId}/biens/${bienId}/charges`, {
    method: 'POST',
    body: JSON.stringify(data),
    headers: { 'Content-Type': 'application/json' }
  });
}

export async function deleteChargeForBien(
  sciId: EntityId, bienId: EntityId, chargeId: number
): Promise<void> {
  return apiFetch(`/api/v1/scis/${sciId}/biens/${bienId}/charges/${chargeId}`, {
    method: 'DELETE'
  });
}

// --- PNO mutations ---
export async function createPnoForBien(
  sciId: EntityId, bienId: EntityId, data: PnoCreate
): Promise<AssurancePnoEmbed> {
  return apiFetch(`/api/v1/scis/${sciId}/biens/${bienId}/assurance-pno`, {
    method: 'POST',
    body: JSON.stringify(data),
    headers: { 'Content-Type': 'application/json' }
  });
}

export async function updatePnoForBien(
  sciId: EntityId, bienId: EntityId, pnoId: number, data: PnoUpdate
): Promise<AssurancePnoEmbed> {
  return apiFetch(`/api/v1/scis/${sciId}/biens/${bienId}/assurance-pno/${pnoId}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
    headers: { 'Content-Type': 'application/json' }
  });
}

export async function deletePnoForBien(
  sciId: EntityId, bienId: EntityId, pnoId: number
): Promise<void> {
  return apiFetch(`/api/v1/scis/${sciId}/biens/${bienId}/assurance-pno/${pnoId}`, {
    method: 'DELETE'
  });
}

// --- Frais Agence mutations ---
export async function createFraisForBien(
  sciId: EntityId, bienId: EntityId, data: FraisCreate
): Promise<FraisAgenceEmbed> {
  return apiFetch(`/api/v1/scis/${sciId}/biens/${bienId}/frais-agence`, {
    method: 'POST',
    body: JSON.stringify(data),
    headers: { 'Content-Type': 'application/json' }
  });
}

export async function deleteFraisForBien(
  sciId: EntityId, bienId: EntityId, fraisId: number
): Promise<void> {
  return apiFetch(`/api/v1/scis/${sciId}/biens/${bienId}/frais-agence/${fraisId}`, {
    method: 'DELETE'
  });
}

// --- Associe invite ---
export async function inviteAssocie(
  sciId: EntityId, data: InviteAssociePayload
): Promise<any> {
  return apiFetch(`/api/v1/scis/${sciId}/associes`, {
    method: 'POST',
    body: JSON.stringify(data),
    headers: { 'Content-Type': 'application/json' }
  });
}
```

- [ ] **Step 5: Run TypeScript check**

Run: `cd frontend && pnpm run check`
Expected: PASS (no type errors)

- [ ] **Step 6: Run existing tests**

Run: `cd frontend && pnpm run test:unit -- --run`
Expected: All existing tests pass

- [ ] **Step 7: Commit**

```bash
git add frontend/src/lib/api.ts
git commit -m "feat: add typed API functions for CRUD wiring (8 new + 12 typed)"
```

---

### Task 2: Create `CrudModal.svelte` reusable component

**Files:**
- Create: `frontend/src/lib/components/ui/CrudModal.svelte`
- Create: `frontend/src/lib/components/ui/__tests__/CrudModal.test.ts`

- [ ] **Step 1: Write the test file**

```typescript
// frontend/src/lib/components/ui/__tests__/CrudModal.test.ts
import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/svelte';
import CrudModal from '../CrudModal.svelte';

describe('CrudModal', () => {
  it('renders nothing when open=false', () => {
    const { container } = render(CrudModal, {
      props: { open: false, title: 'Test', submitLabel: 'Save', loading: false }
    });
    expect(container.querySelector('[role="dialog"]')).toBeNull();
  });

  it('renders dialog when open=true', () => {
    render(CrudModal, {
      props: { open: true, title: 'Test Modal', submitLabel: 'Enregistrer', loading: false }
    });
    expect(screen.getByRole('dialog')).toBeTruthy();
    expect(screen.getByText('Test Modal')).toBeTruthy();
    expect(screen.getByText('Enregistrer')).toBeTruthy();
    expect(screen.getByText('Annuler')).toBeTruthy();
  });

  it('shows subtitle when provided', () => {
    render(CrudModal, {
      props: { open: true, title: 'T', subtitle: 'Sub text', submitLabel: 'OK', loading: false }
    });
    expect(screen.getByText('Sub text')).toBeTruthy();
  });

  it('disables submit button when loading', () => {
    render(CrudModal, {
      props: { open: true, title: 'T', submitLabel: 'Save', loading: true }
    });
    const btn = screen.getByText('Save').closest('button');
    expect(btn?.disabled).toBe(true);
  });

  it('has correct aria attributes', () => {
    render(CrudModal, {
      props: { open: true, title: 'Accessible', submitLabel: 'OK', loading: false }
    });
    const dialog = screen.getByRole('dialog');
    expect(dialog.getAttribute('aria-modal')).toBe('true');
    expect(dialog.getAttribute('aria-labelledby')).toBeTruthy();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && pnpm vitest run src/lib/components/ui/__tests__/CrudModal.test.ts`
Expected: FAIL (CrudModal.svelte not found)

- [ ] **Step 3: Create CrudModal.svelte**

```svelte
<!-- frontend/src/lib/components/ui/CrudModal.svelte -->
<script lang="ts">
  import { scale, fade } from 'svelte/transition';

  interface Props {
    open: boolean;
    title: string;
    subtitle?: string;
    size?: 'compact' | 'wide';
    submitLabel: string;
    loading: boolean;
    onclose?: () => void;
    onsubmit?: () => void;
    children?: import('svelte').Snippet;
  }

  let {
    open = $bindable(),
    title,
    subtitle,
    size = 'compact',
    submitLabel,
    loading,
    onclose,
    onsubmit,
    children
  }: Props = $props();

  const modalId = `modal-${Math.random().toString(36).slice(2, 9)}`;

  function close() {
    if (loading) return;
    open = false;
    onclose?.();
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') close();
  }

  function handleSubmit(e: Event) {
    e.preventDefault();
    onsubmit?.();
  }

  function handleBackdropClick(e: MouseEvent) {
    if (e.target === e.currentTarget) close();
  }
</script>

{#if open}
  <!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
  <div
    role="dialog"
    aria-modal="true"
    aria-labelledby="{modalId}-title"
    class="fixed inset-0 z-50 flex items-center justify-center p-4"
    onkeydown={handleKeydown}
  >
    <!-- Backdrop -->
    <!-- svelte-ignore a11y_click_events_have_key_events -->
    <!-- svelte-ignore a11y_no_static_element_interactions -->
    <div
      class="absolute inset-0 bg-black/50 backdrop-blur-sm"
      transition:fade={{ duration: 150 }}
      onclick={handleBackdropClick}
    ></div>

    <!-- Modal -->
    <form
      class="relative w-full overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl dark:border-slate-700 dark:bg-slate-900 {size === 'wide' ? 'max-w-[560px]' : 'max-w-[420px]'}"
      transition:scale={{ start: 0.95, duration: 150 }}
      onsubmit={handleSubmit}
    >
      <!-- Header -->
      <div class="flex items-center justify-between border-b border-slate-200 px-5 py-4 dark:border-slate-700">
        <div>
          <h2 id="{modalId}-title" class="text-base font-semibold text-slate-900 dark:text-slate-100">
            {title}
          </h2>
          {#if subtitle}
            <p class="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{subtitle}</p>
          {/if}
        </div>
        <button
          type="button"
          onclick={close}
          class="rounded-lg p-1 text-slate-400 transition-colors hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-300"
          aria-label="Fermer"
        >
          <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      <!-- Body -->
      <div class="px-5 py-4 {size === 'wide' ? 'grid grid-cols-2 gap-4' : 'space-y-4'}">
        {#if children}
          {@render children()}
        {/if}
      </div>

      <!-- Footer -->
      <div class="flex items-center justify-end gap-2 border-t border-slate-200 px-5 py-3 dark:border-slate-700">
        <button
          type="button"
          onclick={close}
          disabled={loading}
          class="rounded-lg px-4 py-2 text-sm font-medium text-slate-600 transition-colors hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"
        >
          Annuler
        </button>
        <button
          type="submit"
          disabled={loading}
          class="rounded-lg bg-sky-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-sky-700 disabled:opacity-50"
        >
          {#if loading}
            <span class="inline-flex items-center gap-2">
              <svg class="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"></path>
              </svg>
              Chargement...
            </span>
          {:else}
            {submitLabel}
          {/if}
        </button>
      </div>
    </form>
  </div>
{/if}
```

- [ ] **Step 4: Run test**

Run: `cd frontend && pnpm vitest run src/lib/components/ui/__tests__/CrudModal.test.ts`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/components/ui/CrudModal.svelte frontend/src/lib/components/ui/__tests__/CrudModal.test.ts
git commit -m "feat: create CrudModal reusable component with a11y"
```

---

### Task 3: Extend toast system with undo variant

**Files:**
- Modify: `frontend/src/lib/components/ui/toast/toast-store.ts`
- Modify: `frontend/src/lib/components/ui/toast/toaster.svelte`
- Create: `frontend/src/lib/components/ui/toast/__tests__/toast-store.test.ts`

- [ ] **Step 1: Write the test**

```typescript
// frontend/src/lib/components/ui/toast/__tests__/toast-store.test.ts
import { describe, it, expect, vi } from 'vitest';
import { get } from 'svelte/store';
import { addToast, dismissToast, toasts, flushPendingDeletes, type ToastItem } from '../toast-store';

describe('toast-store', () => {
  it('adds a toast', () => {
    const id = addToast({ title: 'Test' });
    const items = get(toasts);
    expect(items.some(t => t.id === id)).toBe(true);
  });

  it('adds undo toast with callbacks', () => {
    const onUndo = vi.fn();
    const onExpire = vi.fn();
    const id = addToast({
      title: 'Supprimé',
      variant: 'undo',
      undoCallbacks: { onUndo, onExpire },
      timeoutMs: 5000
    });
    const items = get(toasts);
    const toast = items.find(t => t.id === id);
    expect(toast?.variant).toBe('undo');
  });

  it('flushPendingDeletes calls onExpire for all undo toasts', () => {
    const onExpire1 = vi.fn();
    const onExpire2 = vi.fn();
    addToast({ title: 'A', variant: 'undo', undoCallbacks: { onUndo: vi.fn(), onExpire: onExpire1 }, timeoutMs: 50000 });
    addToast({ title: 'B', variant: 'undo', undoCallbacks: { onUndo: vi.fn(), onExpire: onExpire2 }, timeoutMs: 50000 });
    flushPendingDeletes();
    expect(onExpire1).toHaveBeenCalledOnce();
    expect(onExpire2).toHaveBeenCalledOnce();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && pnpm vitest run src/lib/components/ui/toast/__tests__/toast-store.test.ts`
Expected: FAIL

- [ ] **Step 3: Update toast-store.ts**

```typescript
// frontend/src/lib/components/ui/toast/toast-store.ts
import { writable } from 'svelte/store';

export type ToastVariant = 'default' | 'success' | 'error' | 'undo';

export type UndoCallbacks = {
  onUndo: () => void;
  onExpire: () => void;
};

export type ToastItem = {
  id: number;
  title: string;
  description?: string;
  variant: ToastVariant;
  timeoutMs: number;
  undoCallbacks?: UndoCallbacks;
};

const toastsStore = writable<ToastItem[]>([]);
let nextToastId = 1;
const activeTimers = new Map<number, ReturnType<typeof setTimeout>>();

export const toasts = {
  subscribe: toastsStore.subscribe
};

export function dismissToast(id: number) {
  activeTimers.delete(id);
  toastsStore.update((current) => current.filter((toast) => toast.id !== id));
}

export function handleUndo(id: number) {
  let found: ToastItem | undefined;
  toastsStore.update((current) => {
    found = current.find((t) => t.id === id);
    return current.filter((t) => t.id !== id);
  });
  const timer = activeTimers.get(id);
  if (timer) clearTimeout(timer);
  activeTimers.delete(id);
  found?.undoCallbacks?.onUndo();
}

export function flushPendingDeletes() {
  let undoToasts: ToastItem[] = [];
  toastsStore.update((current) => {
    undoToasts = current.filter((t) => t.variant === 'undo' && t.undoCallbacks);
    return current.filter((t) => t.variant !== 'undo');
  });
  for (const toast of undoToasts) {
    const timer = activeTimers.get(toast.id);
    if (timer) clearTimeout(timer);
    activeTimers.delete(toast.id);
    toast.undoCallbacks?.onExpire();
  }
}

export function addToast(input: {
  title: string;
  description?: string;
  variant?: ToastVariant;
  timeoutMs?: number;
  undoCallbacks?: UndoCallbacks;
}) {
  const toast: ToastItem = {
    id: nextToastId++,
    title: input.title,
    description: input.description,
    variant: input.variant ?? 'default',
    timeoutMs: input.timeoutMs ?? 4200,
    undoCallbacks: input.undoCallbacks
  };

  toastsStore.update((current) => [toast, ...current].slice(0, 5));

  if (toast.timeoutMs > 0) {
    const timer = setTimeout(() => {
      if (toast.variant === 'undo' && toast.undoCallbacks) {
        toast.undoCallbacks.onExpire();
      }
      dismissToast(toast.id);
    }, toast.timeoutMs);
    activeTimers.set(toast.id, timer);
  }

  return toast.id;
}

// Register beforeunload handler
if (typeof window !== 'undefined') {
  window.addEventListener('beforeunload', () => {
    flushPendingDeletes();
  });
}
```

- [ ] **Step 4: Update toaster.svelte with undo UI + aria-live**

```svelte
<!-- frontend/src/lib/components/ui/toast/toaster.svelte -->
<script lang="ts">
  import { cn } from '$lib/utils';
  import { dismissToast, handleUndo, toasts, type ToastItem } from './toast-store';

  function cardClass(toast: ToastItem) {
    if (toast.variant === 'success') {
      return 'border-emerald-200 bg-emerald-50 text-emerald-900';
    }
    if (toast.variant === 'error') {
      return 'border-rose-200 bg-rose-50 text-rose-900';
    }
    if (toast.variant === 'undo') {
      return 'border-amber-200 bg-amber-50 text-amber-900';
    }
    return 'border-slate-200 bg-white text-slate-900';
  }
</script>

<div
  aria-live="polite"
  class="pointer-events-none fixed right-4 bottom-4 z-50 flex w-[min(92vw,22rem)] flex-col gap-2"
>
  {#each $toasts as toast (toast.id)}
    <div class={cn('pointer-events-auto rounded-xl border p-3 shadow-xl backdrop-blur-md', cardClass(toast))}>
      <div class="flex items-start justify-between gap-3">
        <div class="space-y-1">
          <p class="text-sm font-semibold">{toast.title}</p>
          {#if toast.description}
            <p class="text-xs opacity-90">{toast.description}</p>
          {/if}
        </div>
        {#if toast.variant === 'undo'}
          <button
            type="button"
            class="rounded-md bg-amber-600 px-3 py-1 text-xs font-semibold text-white transition hover:bg-amber-700"
            onclick={() => handleUndo(toast.id)}
          >
            Annuler
          </button>
        {:else}
          <button
            type="button"
            class="rounded-md px-2 py-1 text-xs font-semibold opacity-70 transition hover:opacity-100"
            onclick={() => dismissToast(toast.id)}
          >
            Fermer
          </button>
        {/if}
      </div>
      {#if toast.variant === 'undo'}
        <div class="mt-2 h-1 w-full overflow-hidden rounded-full bg-amber-200">
          <div
            class="h-full bg-amber-500 rounded-full"
            style="animation: shrink {toast.timeoutMs}ms linear forwards"
          ></div>
        </div>
      {/if}
    </div>
  {/each}
</div>

<style>
  @keyframes shrink {
    from { width: 100%; }
    to { width: 0%; }
  }
</style>
```

- [ ] **Step 5: Run tests**

Run: `cd frontend && pnpm vitest run src/lib/components/ui/toast/__tests__/toast-store.test.ts`
Expected: PASS

- [ ] **Step 6: Run full check**

Run: `cd frontend && pnpm run check && pnpm run test:unit -- --run`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add frontend/src/lib/components/ui/toast/
git commit -m "feat: extend toast system with undo variant + beforeunload flush"
```

---

### Task 4: Create `DatePopover.svelte`

**Files:**
- Create: `frontend/src/lib/components/ui/DatePopover.svelte`

- [ ] **Step 1: Create DatePopover.svelte**

```svelte
<!-- frontend/src/lib/components/ui/DatePopover.svelte -->
<script lang="ts">
  import { fade } from 'svelte/transition';

  interface Props {
    open: boolean;
    defaultDate?: string;
    onconfirm: (date: string) => void;
    oncancel?: () => void;
  }

  let { open = $bindable(), defaultDate, onconfirm, oncancel }: Props = $props();

  let dateValue = $state(defaultDate ?? new Date().toISOString().slice(0, 10));

  function confirm() {
    onconfirm(dateValue);
    open = false;
  }

  function cancel() {
    open = false;
    oncancel?.();
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') cancel();
    if (e.key === 'Enter') { e.preventDefault(); confirm(); }
  }
</script>

{#if open}
  <!-- svelte-ignore a11y_no_static_element_interactions -->
  <div
    class="absolute top-full right-0 z-40 mt-1 rounded-xl border border-slate-200 bg-white p-3 shadow-lg dark:border-slate-700 dark:bg-slate-900"
    transition:fade={{ duration: 100 }}
    onkeydown={handleKeydown}
  >
    <label class="mb-1 block text-xs font-medium text-slate-500 dark:text-slate-400">
      Date de paiement
    </label>
    <input
      type="date"
      bind:value={dateValue}
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-900 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100"
    />
    <div class="mt-2 flex justify-end gap-2">
      <button
        type="button"
        onclick={cancel}
        class="rounded-md px-3 py-1 text-xs font-medium text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800"
      >
        Annuler
      </button>
      <button
        type="button"
        onclick={confirm}
        class="rounded-md bg-emerald-600 px-3 py-1 text-xs font-medium text-white hover:bg-emerald-700"
      >
        Confirmer
      </button>
    </div>
  </div>
{/if}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/components/ui/DatePopover.svelte
git commit -m "feat: create DatePopover component for mark-as-paid"
```

---

## Chunk 2: Modal Forms (8 modals)

All modals go in `frontend/src/lib/components/fiche-bien/modals/`.

Each modal follows the same pattern:
1. Import `CrudModal` + relevant API function + `addToast`
2. Accept `open: boolean` (bindable), optional `editItem`, `sciId`, `bienId`, `onSuccess` callback
3. Use `$state` for form fields, `$effect` to populate from `editItem` when editing
4. On submit: call API, `addToast({variant:'success'})`, `onSuccess()`, close
5. On error: `addToast({variant:'error'})` or show field-level error for 422

### Task 5: LoyerModal.svelte

**Files:**
- Create: `frontend/src/lib/components/fiche-bien/modals/LoyerModal.svelte`

- [ ] **Step 1: Create the modal**

```svelte
<script lang="ts">
  import CrudModal from '$lib/components/ui/CrudModal.svelte';
  import { createLoyerForBien, type LoyerCreatePayload, type EntityId, type LoyerStatus } from '$lib/api';
  import { addToast } from '$lib/components/ui/toast/toast-store';

  interface Props {
    open: boolean;
    sciId: EntityId;
    bienId: EntityId;
    defaultMontant?: number;
    onSuccess: () => void;
  }

  let { open = $bindable(), sciId, bienId, defaultMontant = 0, onSuccess }: Props = $props();

  let loading = $state(false);
  let periode = $state(new Date().toISOString().slice(0, 7)); // YYYY-MM
  let montant = $state(defaultMontant);
  let statut = $state<LoyerStatus>('en_attente');

  $effect(() => {
    if (open) {
      montant = defaultMontant;
      statut = 'en_attente';
      periode = new Date().toISOString().slice(0, 7);
    }
  });

  async function handleSubmit() {
    if (!periode || montant < 0) return;
    loading = true;
    try {
      const data: LoyerCreatePayload = {
        id_bien: bienId,
        date_loyer: `${periode}-01`,
        montant,
        statut
      };
      await createLoyerForBien(sciId, bienId, data);
      addToast({ title: 'Loyer enregistré', variant: 'success' });
      onSuccess();
      open = false;
    } catch (err: any) {
      addToast({ title: err?.message ?? 'Erreur', variant: 'error' });
    } finally {
      loading = false;
    }
  }
</script>

<CrudModal bind:open title="Enregistrer un loyer" submitLabel="Enregistrer" {loading} onsubmit={handleSubmit}>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Période</label>
    <input type="month" bind:value={periode} required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Montant (EUR)</label>
    <input type="number" bind:value={montant} min="0" step="0.01" required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Statut</label>
    <div class="flex gap-2">
      {#each (['en_attente', 'paye', 'en_retard'] as const) as s}
        <button type="button"
          class="rounded-full px-3 py-1 text-xs font-medium transition-colors {statut === s ? 'bg-sky-600 text-white' : 'border border-slate-300 text-slate-600 dark:border-slate-600 dark:text-slate-400'}"
          onclick={() => statut = s}>
          {s === 'paye' ? 'Payé' : s === 'en_attente' ? 'En attente' : 'En retard'}
        </button>
      {/each}
    </div>
  </div>
</CrudModal>
```

- [ ] **Step 2: Commit**

```bash
mkdir -p frontend/src/lib/components/fiche-bien/modals
git add frontend/src/lib/components/fiche-bien/modals/LoyerModal.svelte
git commit -m "feat: create LoyerModal for loyer creation"
```

---

### Task 6: BailModal.svelte (wide)

**Files:**
- Create: `frontend/src/lib/components/fiche-bien/modals/BailModal.svelte`

- [ ] **Step 1: Create the modal**

```svelte
<script lang="ts">
  import CrudModal from '$lib/components/ui/CrudModal.svelte';
  import { createBail, updateBail, type BailCreate, type BailUpdate, type BailEmbed, type EntityId } from '$lib/api';
  import { addToast } from '$lib/components/ui/toast/toast-store';

  interface Props {
    open: boolean;
    sciId: EntityId;
    bienId: EntityId;
    editItem?: BailEmbed | null;
    onSuccess: () => void;
  }

  let { open = $bindable(), sciId, bienId, editItem = null, onSuccess }: Props = $props();

  let loading = $state(false);
  let date_debut = $state('');
  let date_fin = $state('');
  let loyer_hc = $state(0);
  let charges_provisions = $state(0);
  let depot_garantie = $state(0);
  let revision_indice = $state('');

  const isEdit = $derived(!!editItem);

  $effect(() => {
    if (open && editItem) {
      date_debut = editItem.date_debut ?? '';
      date_fin = editItem.date_fin ?? '';
      loyer_hc = editItem.loyer_hc ?? 0;
      charges_provisions = editItem.charges_provisions ?? 0;
      depot_garantie = editItem.depot_garantie ?? 0;
      revision_indice = editItem.revision_indice ?? '';
    } else if (open) {
      date_debut = ''; date_fin = ''; loyer_hc = 0;
      charges_provisions = 0; depot_garantie = 0; revision_indice = '';
    }
  });

  async function handleSubmit() {
    if (!date_debut || loyer_hc < 0) return;
    loading = true;
    try {
      if (isEdit && editItem) {
        const data: BailUpdate = { date_fin: date_fin || undefined, loyer_hc, charges_provisions, depot_garantie, revision_indice: revision_indice || undefined };
        await updateBail(sciId, bienId, editItem.id, data);
        addToast({ title: 'Bail mis à jour', variant: 'success' });
      } else {
        const data: BailCreate = { date_debut, date_fin: date_fin || undefined, loyer_hc, charges_provisions, depot_garantie, revision_indice: revision_indice || undefined };
        await createBail(sciId, bienId, data);
        addToast({ title: 'Bail créé', variant: 'success' });
      }
      onSuccess();
      open = false;
    } catch (err: any) {
      addToast({ title: err?.message ?? 'Erreur', variant: 'error' });
    } finally {
      loading = false;
    }
  }
</script>

<CrudModal bind:open title={isEdit ? 'Modifier le bail' : 'Créer un bail'} size="wide" submitLabel={isEdit ? 'Mettre à jour' : 'Créer le bail'} {loading} onsubmit={handleSubmit}>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Date début</label>
    <input type="date" bind:value={date_debut} required disabled={isEdit}
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 disabled:opacity-50" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Date fin</label>
    <input type="date" bind:value={date_fin}
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Loyer HC (EUR)</label>
    <input type="number" bind:value={loyer_hc} min="0" step="0.01" required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Charges provisions (EUR)</label>
    <input type="number" bind:value={charges_provisions} min="0" step="0.01"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Dépôt garantie (EUR)</label>
    <input type="number" bind:value={depot_garantie} min="0" step="0.01"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Indice de révision</label>
    <input type="text" bind:value={revision_indice} placeholder="IRL, ICC..."
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
</CrudModal>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/components/fiche-bien/modals/BailModal.svelte
git commit -m "feat: create BailModal for bail create/edit (wide)"
```

---

### Task 7: ChargeModal.svelte

**Files:**
- Create: `frontend/src/lib/components/fiche-bien/modals/ChargeModal.svelte`

- [ ] **Step 1: Create the modal**

```svelte
<script lang="ts">
  import CrudModal from '$lib/components/ui/CrudModal.svelte';
  import { createChargeForBien, type ChargeCreate, type EntityId } from '$lib/api';
  import { addToast } from '$lib/components/ui/toast/toast-store';

  interface Props {
    open: boolean;
    sciId: EntityId;
    bienId: EntityId;
    onSuccess: () => void;
  }

  let { open = $bindable(), sciId, bienId, onSuccess }: Props = $props();

  let loading = $state(false);
  let type_charge = $state('copropriete');
  let montant = $state(0);
  let date_paiement = $state(new Date().toISOString().slice(0, 10));

  $effect(() => {
    if (open) {
      type_charge = 'copropriete'; montant = 0;
      date_paiement = new Date().toISOString().slice(0, 10);
    }
  });

  const chargeTypes = [
    { value: 'copropriete', label: 'Copropriété' },
    { value: 'taxe_fonciere', label: 'Taxe foncière' },
    { value: 'entretien', label: 'Entretien' },
    { value: 'autre', label: 'Autre' }
  ];

  async function handleSubmit() {
    if (montant < 0) return;
    loading = true;
    try {
      const data: ChargeCreate = { type_charge, montant, date_paiement };
      await createChargeForBien(sciId, bienId, data);
      addToast({ title: 'Charge ajoutée', variant: 'success' });
      onSuccess();
      open = false;
    } catch (err: any) {
      addToast({ title: err?.message ?? 'Erreur', variant: 'error' });
    } finally {
      loading = false;
    }
  }
</script>

<CrudModal bind:open title="Ajouter une charge" submitLabel="Ajouter" {loading} onsubmit={handleSubmit}>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Type de charge</label>
    <select bind:value={type_charge} required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100">
      {#each chargeTypes as ct}
        <option value={ct.value}>{ct.label}</option>
      {/each}
    </select>
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Montant (EUR)</label>
    <input type="number" bind:value={montant} min="0" step="0.01" required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Date</label>
    <input type="date" bind:value={date_paiement} required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
</CrudModal>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/components/fiche-bien/modals/ChargeModal.svelte
git commit -m "feat: create ChargeModal for charge creation"
```

---

### Task 8: PnoModal.svelte

**Files:**
- Create: `frontend/src/lib/components/fiche-bien/modals/PnoModal.svelte`

- [ ] **Step 1: Create the modal**

```svelte
<script lang="ts">
  import CrudModal from '$lib/components/ui/CrudModal.svelte';
  import { createPnoForBien, updatePnoForBien, type PnoCreate, type PnoUpdate, type AssurancePnoEmbed, type EntityId } from '$lib/api';
  import { addToast } from '$lib/components/ui/toast/toast-store';

  interface Props {
    open: boolean;
    sciId: EntityId;
    bienId: EntityId;
    editItem?: AssurancePnoEmbed | null;
    onSuccess: () => void;
  }

  let { open = $bindable(), sciId, bienId, editItem = null, onSuccess }: Props = $props();

  let loading = $state(false);
  let assureur = $state('');
  let numero_contrat = $state('');
  let prime_annuelle = $state(0);
  let date_debut = $state('');
  let date_fin = $state('');

  const isEdit = $derived(!!editItem);

  $effect(() => {
    if (open && editItem) {
      assureur = editItem.assureur; numero_contrat = editItem.numero_contrat ?? '';
      prime_annuelle = editItem.prime_annuelle; date_debut = editItem.date_debut;
      date_fin = editItem.date_fin ?? '';
    } else if (open) {
      assureur = ''; numero_contrat = ''; prime_annuelle = 0; date_debut = ''; date_fin = '';
    }
  });

  async function handleSubmit() {
    if (!assureur || !date_debut || prime_annuelle < 0) return;
    loading = true;
    try {
      if (isEdit && editItem) {
        const data: PnoUpdate = { assureur, numero_contrat: numero_contrat || undefined, prime_annuelle, date_debut, date_fin: date_fin || undefined };
        await updatePnoForBien(sciId, bienId, editItem.id, data);
        addToast({ title: 'Assurance PNO mise à jour', variant: 'success' });
      } else {
        const data: PnoCreate = { assureur, numero_contrat: numero_contrat || undefined, prime_annuelle, date_debut, date_fin: date_fin || undefined };
        await createPnoForBien(sciId, bienId, data);
        addToast({ title: 'Assurance PNO ajoutée', variant: 'success' });
      }
      onSuccess();
      open = false;
    } catch (err: any) {
      addToast({ title: err?.message ?? 'Erreur', variant: 'error' });
    } finally {
      loading = false;
    }
  }
</script>

<CrudModal bind:open title={isEdit ? 'Modifier assurance PNO' : 'Ajouter assurance PNO'} submitLabel={isEdit ? 'Mettre à jour' : 'Ajouter'} {loading} onsubmit={handleSubmit}>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Assureur</label>
    <input type="text" bind:value={assureur} required placeholder="Nom de l'assureur"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">N° contrat</label>
    <input type="text" bind:value={numero_contrat} placeholder="Optionnel"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Prime annuelle (EUR)</label>
    <input type="number" bind:value={prime_annuelle} min="0" step="0.01" required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Date début</label>
    <input type="date" bind:value={date_debut} required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Date fin</label>
    <input type="date" bind:value={date_fin}
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
</CrudModal>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/components/fiche-bien/modals/PnoModal.svelte
git commit -m "feat: create PnoModal for PNO create/edit"
```

---

### Task 9: FraisModal.svelte

**Files:**
- Create: `frontend/src/lib/components/fiche-bien/modals/FraisModal.svelte`

- [ ] **Step 1: Create the modal**

```svelte
<script lang="ts">
  import CrudModal from '$lib/components/ui/CrudModal.svelte';
  import { createFraisForBien, type FraisCreate, type EntityId } from '$lib/api';
  import { addToast } from '$lib/components/ui/toast/toast-store';

  interface Props {
    open: boolean;
    sciId: EntityId;
    bienId: EntityId;
    onSuccess: () => void;
  }

  let { open = $bindable(), sciId, bienId, onSuccess }: Props = $props();

  let loading = $state(false);
  let type_frais = $state('gestion_locative');
  let montant = $state(0);
  let date_frais = $state(new Date().toISOString().slice(0, 10));
  let description = $state('');

  $effect(() => {
    if (open) {
      type_frais = 'gestion_locative'; montant = 0;
      date_frais = new Date().toISOString().slice(0, 10); description = '';
    }
  });

  const fraisTypes = [
    { value: 'gestion_locative', label: 'Gestion locative' },
    { value: 'mise_en_location', label: 'Mise en location' },
    { value: 'autre', label: 'Autre' }
  ];

  async function handleSubmit() {
    if (montant < 0) return;
    loading = true;
    try {
      const data: FraisCreate = { type_frais, montant, date_frais, description: description || undefined };
      await createFraisForBien(sciId, bienId, data);
      addToast({ title: 'Frais ajoutés', variant: 'success' });
      onSuccess();
      open = false;
    } catch (err: any) {
      addToast({ title: err?.message ?? 'Erreur', variant: 'error' });
    } finally {
      loading = false;
    }
  }
</script>

<CrudModal bind:open title="Ajouter des frais d'agence" submitLabel="Ajouter" {loading} onsubmit={handleSubmit}>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Type</label>
    <select bind:value={type_frais} required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100">
      {#each fraisTypes as ft}
        <option value={ft.value}>{ft.label}</option>
      {/each}
    </select>
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Montant (EUR)</label>
    <input type="number" bind:value={montant} min="0" step="0.01" required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Date</label>
    <input type="date" bind:value={date_frais} required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Description</label>
    <input type="text" bind:value={description} placeholder="Optionnel"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
</CrudModal>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/components/fiche-bien/modals/FraisModal.svelte
git commit -m "feat: create FraisModal for frais agence creation"
```

---

### Task 10: AssocieModal.svelte

**Files:**
- Create: `frontend/src/lib/components/fiche-bien/modals/AssocieModal.svelte`

- [ ] **Step 1: Create the modal**

```svelte
<script lang="ts">
  import CrudModal from '$lib/components/ui/CrudModal.svelte';
  import { inviteAssocie, type InviteAssociePayload, type EntityId } from '$lib/api';
  import { addToast } from '$lib/components/ui/toast/toast-store';

  interface Props {
    open: boolean;
    sciId: EntityId;
    onSuccess: () => void;
  }

  let { open = $bindable(), sciId, onSuccess }: Props = $props();

  let loading = $state(false);
  let nom = $state('');
  let email = $state('');
  let role = $state('associe');
  let part = $state(0);

  $effect(() => {
    if (open) { nom = ''; email = ''; role = 'associe'; part = 0; }
  });

  async function handleSubmit() {
    if (!nom.trim() || part <= 0 || part > 100) return;
    loading = true;
    try {
      const data: InviteAssociePayload = { nom: nom.trim(), email: email || undefined, part, role };
      await inviteAssocie(sciId, data);
      addToast({ title: 'Associé invité', variant: 'success' });
      onSuccess();
      open = false;
    } catch (err: any) {
      addToast({ title: err?.message ?? 'Erreur', variant: 'error' });
    } finally {
      loading = false;
    }
  }
</script>

<CrudModal bind:open title="Inviter un associé" submitLabel="Inviter" {loading} onsubmit={handleSubmit}>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Nom</label>
    <input type="text" bind:value={nom} required placeholder="Nom complet"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Email</label>
    <input type="email" bind:value={email} placeholder="optionnel@email.com"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Rôle</label>
    <div class="flex gap-2">
      {#each (['associe', 'gerant'] as const) as r}
        <button type="button"
          class="rounded-full px-3 py-1 text-xs font-medium transition-colors {role === r ? 'bg-sky-600 text-white' : 'border border-slate-300 text-slate-600 dark:border-slate-600 dark:text-slate-400'}"
          onclick={() => role = r}>
          {r === 'gerant' ? 'Gérant' : 'Associé'}
        </button>
      {/each}
    </div>
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Part (%)</label>
    <input type="number" bind:value={part} min="0" max="100" step="0.01" required
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
</CrudModal>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/components/fiche-bien/modals/AssocieModal.svelte
git commit -m "feat: create AssocieModal for inviting associates"
```

---

### Task 11: SciModal.svelte (wide)

**Files:**
- Create: `frontend/src/lib/components/fiche-bien/modals/SciModal.svelte`

- [ ] **Step 1: Create the modal**

```svelte
<script lang="ts">
  import CrudModal from '$lib/components/ui/CrudModal.svelte';
  import { createSci, type SCICreatePayload } from '$lib/api';
  import { addToast } from '$lib/components/ui/toast/toast-store';
  import { goto } from '$app/navigation';

  interface Props {
    open: boolean;
  }

  let { open = $bindable() }: Props = $props();

  let loading = $state(false);
  let nom = $state('');
  let siren = $state('');
  let regime_fiscal = $state<'IR' | 'IS'>('IR');

  $effect(() => {
    if (open) { nom = ''; siren = ''; regime_fiscal = 'IR'; }
  });

  async function handleSubmit() {
    if (!nom.trim()) return;
    if (siren && !/^\d{9}$/.test(siren)) {
      addToast({ title: 'SIREN invalide (9 chiffres)', variant: 'error' });
      return;
    }
    loading = true;
    try {
      const data: SCICreatePayload = { nom: nom.trim(), siren: siren || undefined, regime_fiscal };
      const created = await createSci(data);
      addToast({ title: 'SCI créée', variant: 'success' });
      open = false;
      goto(`/scis/${created.id}`);
    } catch (err: any) {
      addToast({ title: err?.message ?? 'Erreur', variant: 'error' });
    } finally {
      loading = false;
    }
  }
</script>

<CrudModal bind:open title="Créer une SCI" size="wide" submitLabel="Créer la SCI" {loading} onsubmit={handleSubmit}>
  <div class="col-span-2">
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Nom de la SCI</label>
    <input type="text" bind:value={nom} required placeholder="SCI Mon Patrimoine"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">SIREN (optionnel)</label>
    <input type="text" bind:value={siren} placeholder="123456789" maxlength="9"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Régime fiscal</label>
    <div class="flex gap-2">
      {#each (['IR', 'IS'] as const) as rf}
        <button type="button"
          class="rounded-full px-4 py-1.5 text-xs font-medium transition-colors {regime_fiscal === rf ? 'bg-sky-600 text-white' : 'border border-slate-300 text-slate-600 dark:border-slate-600 dark:text-slate-400'}"
          onclick={() => regime_fiscal = rf}>
          {rf}
        </button>
      {/each}
    </div>
  </div>
</CrudModal>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/components/fiche-bien/modals/SciModal.svelte
git commit -m "feat: create SciModal for SCI creation"
```

---

### Task 12: BienModal.svelte (wide)

**Files:**
- Create: `frontend/src/lib/components/fiche-bien/modals/BienModal.svelte`

- [ ] **Step 1: Create the modal**

```svelte
<script lang="ts">
  import CrudModal from '$lib/components/ui/CrudModal.svelte';
  import { createBienForSci, type BienCreatePayload, type EntityId, type BienType } from '$lib/api';
  import { addToast } from '$lib/components/ui/toast/toast-store';
  import { goto } from '$app/navigation';

  interface Props {
    open: boolean;
    sciId: EntityId;
  }

  let { open = $bindable(), sciId }: Props = $props();

  let loading = $state(false);
  let adresse = $state('');
  let ville = $state('');
  let code_postal = $state('');
  let type_locatif = $state<BienType>('nu');
  let loyer_cc = $state(0);
  let charges = $state(0);
  let tmi = $state(0);
  let prix_acquisition = $state<number | undefined>(undefined);

  $effect(() => {
    if (open) {
      adresse = ''; ville = ''; code_postal = ''; type_locatif = 'nu';
      loyer_cc = 0; charges = 0; tmi = 0; prix_acquisition = undefined;
    }
  });

  async function handleSubmit() {
    if (!adresse.trim()) return;
    loading = true;
    try {
      const data: BienCreatePayload = {
        id_sci: sciId, adresse: adresse.trim(), ville, code_postal,
        type_locatif, loyer_cc, charges, tmi, prix_acquisition
      };
      const created = await createBienForSci(sciId, data);
      addToast({ title: 'Bien ajouté', variant: 'success' });
      open = false;
      goto(`/scis/${sciId}/biens/${created.id}`);
    } catch (err: any) {
      addToast({ title: err?.message ?? 'Erreur', variant: 'error' });
    } finally {
      loading = false;
    }
  }
</script>

<CrudModal bind:open title="Ajouter un bien" size="wide" submitLabel="Ajouter le bien" {loading} onsubmit={handleSubmit}>
  <div class="col-span-2">
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Adresse</label>
    <input type="text" bind:value={adresse} required placeholder="15 rue de la Paix"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Ville</label>
    <input type="text" bind:value={ville} placeholder="Paris"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Code postal</label>
    <input type="text" bind:value={code_postal} placeholder="75001" maxlength="5"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Type</label>
    <select bind:value={type_locatif}
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100">
      <option value="nu">Nu</option>
      <option value="meuble">Meublé</option>
      <option value="mixte">Mixte</option>
    </select>
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Loyer CC (EUR)</label>
    <input type="number" bind:value={loyer_cc} min="0" step="0.01"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
  <div>
    <label class="mb-1 block text-xs font-medium text-slate-500 uppercase dark:text-slate-400">Prix acquisition (EUR)</label>
    <input type="number" bind:value={prix_acquisition} min="0" step="1"
      class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100" />
  </div>
</CrudModal>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/components/fiche-bien/modals/BienModal.svelte
git commit -m "feat: create BienModal for bien creation (wide)"
```

---

## Chunk 3: Wiring Components + Pages + Backend

### Task 13: Wire FicheBienLoyers.svelte (3 buttons)

**Files:**
- Modify: `frontend/src/lib/components/fiche-bien/FicheBienLoyers.svelte`

- [ ] **Step 1: Add imports + state + handlers**

At top of `<script>`, add imports for `LoyerModal`, `DatePopover`, toast, and API functions (`updateLoyer`, `renderQuitus`). Add state: `showLoyerModal`, `showDatePopover`, `datePopoverLoyerId`. Add `refreshLoyers()` that re-fetches via `fetchFicheBien` or emits event. Add `handleMarkPaid(loyerId, date)` and `handleQuittance(loyer)`.

Key changes:
```typescript
import LoyerModal from './modals/LoyerModal.svelte';
import DatePopover from '$lib/components/ui/DatePopover.svelte';
import { updateLoyer, renderQuitus, type LoyerEmbed } from '$lib/api';
import { addToast } from '$lib/components/ui/toast/toast-store';

// Change props type
loyers: LoyerEmbed[];

let showLoyerModal = $state(false);
let datePopoverLoyerId = $state<number | null>(null);

// onSuccess callback — parent must provide a refresh function
interface Props {
  loyers: LoyerEmbed[];
  isGerant: boolean;
  sciId: string | number;
  bienId: string | number;
  onRefresh: () => void;
}

let { loyers, isGerant, sciId, bienId, onRefresh }: Props = $props();

async function handleMarkPaid(loyerId: number, date: string) {
  try {
    await updateLoyer(sciId, bienId, loyerId, { statut: 'paye' });
    addToast({ title: 'Loyer marqué comme payé', variant: 'success' });
    onRefresh();
  } catch (err: any) {
    addToast({ title: err?.message ?? 'Erreur', variant: 'error' });
  }
  datePopoverLoyerId = null;
}

async function handleQuittance(loyer: LoyerEmbed) {
  try {
    const result = await renderQuitus({
      id_loyer: loyer.id, id_bien: bienId,
      nom_locataire: '', periode: loyer.date_loyer, montant: loyer.montant
    });
    window.open(result.pdf_url, '_blank');
  } catch (err: any) {
    addToast({ title: err?.message ?? 'Erreur de génération', variant: 'error' });
  }
}
```

- [ ] **Step 2: Wire the 3 buttons**

1. "Enregistrer un loyer" button (line ~43): add `onclick={() => showLoyerModal = true}`
2. "Payé" button (line ~107): add `onclick={() => datePopoverLoyerId = loyer.id}` + wrap in `relative` div + add `<DatePopover>` after button
3. "Quittance" button (line ~115): add `onclick={() => handleQuittance(loyer)}`

- [ ] **Step 3: Add LoyerModal at bottom of template**

```svelte
<LoyerModal bind:open={showLoyerModal} {sciId} {bienId} onSuccess={onRefresh} />
```

- [ ] **Step 4: Run check**

Run: `cd frontend && pnpm run check`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/components/fiche-bien/FicheBienLoyers.svelte
git commit -m "feat: wire FicheBienLoyers — 3 buttons (create, mark paid, quittance)"
```

---

### Task 14: Wire FicheBienBail.svelte (2 buttons)

**Files:**
- Modify: `frontend/src/lib/components/fiche-bien/FicheBienBail.svelte`

- [ ] **Step 1: Add imports + state**

```typescript
import BailModal from './modals/BailModal.svelte';

let showBailModal = $state(false);
let editBail = $state<BailEmbed | null>(null);

// Add onRefresh to Props
interface Props {
  bail: BailEmbed | null;
  isGerant: boolean;
  sciId: string;
  bienId: string | number;
  onRefresh: () => void;
}

let { bail, isGerant, sciId, bienId, onRefresh }: Props = $props();
```

- [ ] **Step 2: Wire the 2 buttons**

1. "Créer un bail" (line ~53): `onclick={() => { editBail = null; showBailModal = true; }}`
2. "Modifier" (line ~86): `onclick={() => { editBail = bail; showBailModal = true; }}`

- [ ] **Step 3: Add BailModal at bottom**

```svelte
<BailModal bind:open={showBailModal} {sciId} {bienId} editItem={editBail} onSuccess={onRefresh} />
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/components/fiche-bien/FicheBienBail.svelte
git commit -m "feat: wire FicheBienBail — create + edit buttons"
```

---

### Task 15: Wire FicheBienCharges.svelte (7 buttons)

**Files:**
- Modify: `frontend/src/lib/components/fiche-bien/FicheBienCharges.svelte`

- [ ] **Step 1: Add imports + state**

```typescript
import ChargeModal from './modals/ChargeModal.svelte';
import PnoModal from './modals/PnoModal.svelte';
import FraisModal from './modals/FraisModal.svelte';
import { deleteChargeForBien, deletePnoForBien, deleteFraisForBien, type ChargeEmbed } from '$lib/api';
import { addToast } from '$lib/components/ui/toast/toast-store';

// Change charges type
charges: ChargeEmbed[];

let showChargeModal = $state(false);
let showPnoModal = $state(false);
let showFraisModal = $state(false);
let editPno = $state<AssurancePnoEmbed | null>(null);

// Add onRefresh to Props
interface Props {
  charges: ChargeEmbed[];
  assurancePno: AssurancePnoEmbed | null;
  fraisAgence: FraisAgenceEmbed[];
  isGerant: boolean;
  sciId: string;
  bienId: string | number;
  onRefresh: () => void;
}

function deleteCharge(charge: ChargeEmbed) {
  charges = charges.filter(c => c.id !== charge.id);
  addToast({
    title: 'Charge supprimée',
    variant: 'undo',
    timeoutMs: 5000,
    undoCallbacks: {
      onUndo: () => { charges = [charge, ...charges]; },
      onExpire: () => { deleteChargeForBien(sciId, bienId, charge.id).catch(() => onRefresh()); }
    }
  });
}

function deletePno() {
  const saved = assurancePno;
  assurancePno = null;
  addToast({
    title: 'Assurance PNO supprimée',
    variant: 'undo',
    timeoutMs: 5000,
    undoCallbacks: {
      onUndo: () => { assurancePno = saved; },
      onExpire: () => { if (saved) deletePnoForBien(sciId, bienId, saved.id).catch(() => onRefresh()); }
    }
  });
}

function deleteFrais(frais: FraisAgenceEmbed) {
  fraisAgence = fraisAgence.filter(f => f.id !== frais.id);
  addToast({
    title: 'Frais supprimés',
    variant: 'undo',
    timeoutMs: 5000,
    undoCallbacks: {
      onUndo: () => { fraisAgence = [frais, ...fraisAgence]; },
      onExpire: () => { deleteFraisForBien(sciId, bienId, frais.id).catch(() => onRefresh()); }
    }
  });
}
```

- [ ] **Step 2: Wire all 7 buttons**

1. "Ajouter une charge" (line ~34): `onclick={() => showChargeModal = true}`
2. "Supprimer" charge (line ~99): `onclick={() => deleteCharge(charge)}`
3. PNO "Ajouter" (line ~124): `onclick={() => { editPno = null; showPnoModal = true; }}`
4. PNO "Modifier" (line ~169): `onclick={() => { editPno = assurancePno; showPnoModal = true; }}`
5. PNO "Supprimer" (line ~174): `onclick={deletePno}`
6. Frais "Ajouter" (line ~202): `onclick={() => showFraisModal = true}`
7. Frais "Supprimer" (line ~269): `onclick={() => deleteFrais(frais)}`

- [ ] **Step 3: Add modals at bottom**

```svelte
<ChargeModal bind:open={showChargeModal} {sciId} {bienId} onSuccess={onRefresh} />
<PnoModal bind:open={showPnoModal} {sciId} {bienId} editItem={editPno} onSuccess={onRefresh} />
<FraisModal bind:open={showFraisModal} {sciId} {bienId} onSuccess={onRefresh} />
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/lib/components/fiche-bien/FicheBienCharges.svelte
git commit -m "feat: wire FicheBienCharges — 7 buttons (create, delete with undo)"
```

---

### Task 16: Wire FicheBienDocuments.svelte (replace confirm/alert)

**Files:**
- Modify: `frontend/src/lib/components/fiche-bien/FicheBienDocuments.svelte`

- [ ] **Step 1: Replace handleDelete with toast undo**

Replace lines 76-84 (`handleDelete` function):

```typescript
import { addToast } from '$lib/components/ui/toast/toast-store';

async function handleDelete(docId: number) {
  const doc = documents.find(d => d.id === docId);
  if (!doc) return;
  documents = documents.filter(d => d.id !== docId);
  addToast({
    title: 'Document supprimé',
    variant: 'undo',
    timeoutMs: 5000,
    undoCallbacks: {
      onUndo: () => { documents = [doc, ...documents]; },
      onExpire: async () => {
        try {
          await deleteDocumentBien(sciId, bienId, docId);
        } catch {
          documents = [doc, ...documents];
          addToast({ title: 'Erreur suppression document', variant: 'error' });
        }
      }
    }
  });
}
```

Also replace the `alert()` in `handleUpload` catch block (line ~70) with:
```typescript
addToast({ title: err?.message ?? "Erreur lors de l'upload.", variant: 'error' });
```
And remove the `uploadError` state variable since we use toasts now.

- [ ] **Step 2: Commit**

```bash
git add frontend/src/lib/components/fiche-bien/FicheBienDocuments.svelte
git commit -m "fix: replace confirm/alert with toast undo in Documents"
```

---

### Task 17: Wire scis/+page.svelte (Nouvelle SCI button)

**Files:**
- Modify: `frontend/src/routes/(app)/scis/+page.svelte`

- [ ] **Step 1: Add modal import + state**

```typescript
import SciModal from '$lib/components/fiche-bien/modals/SciModal.svelte';
let showSciModal = $state(false);
```

- [ ] **Step 2: Replace button onclick**

Change `onclick={() => goto('/scis')}` to `onclick={() => showSciModal = true}`

- [ ] **Step 3: Add modal before closing `</section>`**

```svelte
<SciModal bind:open={showSciModal} />
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/routes/(app)/scis/+page.svelte
git commit -m "feat: wire Nouvelle SCI button to SciModal"
```

---

### Task 18: Wire biens/+page.svelte (Ajouter un bien)

**Files:**
- Modify: `frontend/src/routes/(app)/scis/[sciId]/biens/+page.svelte`

- [ ] **Step 1: Add modal import + state**

```typescript
import BienModal from '$lib/components/fiche-bien/modals/BienModal.svelte';
let showBienModal = $state(false);
```

- [ ] **Step 2: Wire button**

Add `onclick={() => showBienModal = true}` to "Ajouter un bien" button (line ~48)

- [ ] **Step 3: Add modal**

```svelte
<BienModal bind:open={showBienModal} {sciId} />
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/routes/(app)/scis/[sciId]/biens/+page.svelte
git commit -m "feat: wire Ajouter un bien button to BienModal"
```

---

### Task 19: Wire associes/+page.svelte (Inviter un associé)

**Files:**
- Modify: `frontend/src/routes/(app)/scis/[sciId]/associes/+page.svelte`

- [ ] **Step 1: Add modal import + state**

```typescript
import AssocieModal from '$lib/components/fiche-bien/modals/AssocieModal.svelte';
let showAssocieModal = $state(false);
```

- [ ] **Step 2: Wire button**

Add `onclick={() => showAssocieModal = true}` to "Inviter un associé" button (line ~61)

- [ ] **Step 3: Add modal + refresh**

```svelte
<AssocieModal bind:open={showAssocieModal} {sciId} onSuccess={loadAssocies} />
```

- [ ] **Step 4: Commit**

```bash
git add frontend/src/routes/(app)/scis/[sciId]/associes/+page.svelte
git commit -m "feat: wire Inviter un associé button to AssocieModal"
```

---

### Task 20: Backend — Add PATCH + DELETE /scis/{id}

**Files:**
- Modify: `backend/app/api/v1/scis.py`
- Create: `backend/tests/test_scis_patch_delete.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/tests/test_scis_patch_delete.py
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@pytest.fixture
def mock_auth():
    with patch("app.core.security.get_current_user", return_value="user-123"):
        yield

@pytest.fixture
def mock_gerant():
    with patch("app.core.paywall.require_gerant_role") as mock:
        mock.return_value = MagicMock(user_id="user-123", sci_id="sci-1", role="gerant")
        yield mock

def test_patch_sci_returns_updated(mock_auth, mock_gerant):
    with patch("app.api.v1.scis._get_client") as mock_client:
        table_mock = MagicMock()
        table_mock.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "sci-1", "nom": "Updated", "siren": None, "regime_fiscal": "IR"}],
            error=None
        )
        mock_client.return_value.table.return_value = table_mock
        resp = client.patch("/api/v1/scis/sci-1", json={"nom": "Updated"})
        assert resp.status_code == 200
        assert resp.json()["nom"] == "Updated"

def test_delete_sci_returns_204(mock_auth, mock_gerant):
    with patch("app.api.v1.scis._get_client") as mock_client:
        table_mock = MagicMock()
        table_mock.delete.return_value.eq.return_value.execute.return_value = MagicMock(data=[], error=None)
        mock_client.return_value.table.return_value = table_mock
        resp = client.delete("/api/v1/scis/sci-1")
        assert resp.status_code == 204
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && PYTHONPATH=. pytest tests/test_scis_patch_delete.py -v`
Expected: FAIL (404 — endpoints don't exist)

- [ ] **Step 3: Add endpoints to scis.py**

Add after `invite_sci_associe` function:

```python
class SCIUpdatePayload(BaseModel):
    nom: str | None = None
    siren: str | None = None
    regime_fiscal: str | None = None


@router.patch("/{sci_id}", response_model=SCIResponse)
async def update_sci(
    sci_id: str,
    payload: SCIUpdatePayload,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Update a SCI (gerant only)."""
    client = _get_client()
    update_data = payload.model_dump(exclude_none=True, mode="json")
    if not update_data:
        raise ResourceNotFoundError("SCI", sci_id)

    result = client.table("sci").update(update_data).eq("id", sci_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))

    rows = result.data or []
    if not rows:
        raise ResourceNotFoundError("SCI", sci_id)

    return rows[0]


@router.delete("/{sci_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sci(
    sci_id: str,
    membership: AssocieMembership = Depends(require_gerant_role),
):
    """Delete a SCI with cascade (gerant only)."""
    client = _get_client()
    result = client.table("sci").delete().eq("id", sci_id).execute()
    if getattr(result, "error", None):
        raise DatabaseError(str(result.error))
```

- [ ] **Step 4: Run test**

Run: `cd backend && PYTHONPATH=. pytest tests/test_scis_patch_delete.py -v`
Expected: PASS

- [ ] **Step 5: Run all backend tests**

Run: `cd backend && PYTHONPATH=. pytest --tb=short`
Expected: All tests pass

- [ ] **Step 6: Commit**

```bash
git add backend/app/api/v1/scis.py backend/tests/test_scis_patch_delete.py
git commit -m "feat: add PATCH + DELETE /scis/{id} endpoints"
```

---

### Task 21: Update fiche-bien page to pass onRefresh to children

**Files:**
- Modify: `frontend/src/routes/(app)/scis/[sciId]/biens/[bienId]/+page.svelte`

- [ ] **Step 1: Examine current fiche-bien page**

Read the fiche-bien page to understand how child components receive props and add `onRefresh` callback that re-fetches the relevant section data.

- [ ] **Step 2: Add targeted refresh functions**

Add functions `refreshLoyers()`, `refreshBail()`, `refreshCharges()` that call the respective fetch APIs and update local state. Pass these as `onRefresh` props to the respective child components.

- [ ] **Step 3: Run full frontend check**

Run: `cd frontend && pnpm run check && pnpm run test:unit -- --run`
Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add frontend/src/routes/(app)/scis/[sciId]/biens/[bienId]/+page.svelte
git commit -m "feat: add targeted refresh callbacks for fiche-bien sections"
```

---

### Task 22: Final verification

- [ ] **Step 1: TypeScript check**

Run: `cd frontend && pnpm run check`
Expected: PASS — 0 errors

- [ ] **Step 2: Run all frontend tests**

Run: `cd frontend && pnpm run test:unit -- --run`
Expected: All pass

- [ ] **Step 3: Run all backend tests**

Run: `cd backend && PYTHONPATH=. pytest --tb=short`
Expected: All pass

- [ ] **Step 4: Run frontend build**

Run: `cd frontend && pnpm run build`
Expected: Build succeeds

- [ ] **Step 5: Final commit**

```bash
git add -A
git commit -m "chore: final verification — all checks pass"
```

---

## Summary

| Chunk | Tasks | Files | Description |
|-------|-------|-------|-------------|
| 1 | 1-4 | 5 created, 2 modified | Foundation: types, CrudModal, toast undo, DatePopover |
| 2 | 5-12 | 8 created | 8 modal forms (Loyer, Bail, Charge, PNO, Frais, Associe, SCI, Bien) |
| 3 | 13-22 | 8 modified, 1 created | Wire buttons + backend PATCH/DELETE + verification |

**Total: 22 tasks, 14 new files, 10 modified files, 2 backend endpoints**
