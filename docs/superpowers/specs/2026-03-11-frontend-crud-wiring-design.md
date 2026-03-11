# Spec: Frontend CRUD Wiring

**Date**: 2026-03-11
**Status**: Reviewed
**Scope**: Connect 15 dead UI buttons to backend APIs, create modal forms, add missing API functions

## Problem

The audit revealed that 14/23 features are PARTIAL: backend endpoints exist but frontend buttons have no `onclick` handlers. Users see action buttons (create bail, record loyer, add charge, etc.) that do nothing when clicked.

## Goals

1. Wire all 15 dead buttons to functional CRUD flows
2. Create reusable modal components for forms
3. Add 8 genuinely missing API functions in `api.ts` + type existing `any` params/returns
4. Add 2 missing backend endpoints (`PATCH /scis/{id}`, `DELETE /scis/{id}`)
5. Replace `alert()`/`confirm()` with toast undo pattern
6. Type all `any` returns in existing API functions

## Non-Goals

- Redesigning the fiche-bien layout
- Adding new features beyond existing buttons
- Refactoring the backend architecture
- E2E test coverage (separate sub-project)

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Form pattern | Modals (not drawers, not pages) | Short forms (3-8 fields), keeps user in fiche-bien context |
| Modal sizes | Compact (420px) + Wide (560px, 2-col) | Compact for 3-5 fields, wide for 7+ fields |
| Deletion UX | Toast with undo (5s) | Non-blocking, reversible, replaces native `confirm()` |
| Mark as paid | Popover date picker | Quick (1 click + Enter) but captures actual payment date |
| Quittance | Direct PDF download | Data already known, no preview needed |
| Refresh strategy | Per-section targeted refetch | Avoids re-fetching entire fiche-bien (7 queries) |
| Frais agence | Create + delete only (no edit) | Backend has no PATCH endpoint; deliberate simplification |

## Architecture

### New Components

#### `CrudModal.svelte` (reusable)
- **Props**: `open: boolean`, `title: string`, `subtitle?: string`, `size: 'compact' | 'wide'`, `submitLabel: string`, `loading: boolean`
- **Slots**: Form body as child slot
- **Behavior**: Focus trap, Escape/click-outside close, disabled submit during loading
- **Animation**: Fade overlay + scale modal (Svelte transition)
- **Accessibility**: `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, auto-focus first input

#### `DatePopover.svelte`
- **Props**: `open: boolean`, `defaultDate: string` (ISO), `onConfirm: (date: string) => void`
- **Behavior**: Positioned relative to trigger button, date input with today as default, Confirm/Cancel
- **Usage**: "Mark as paid" on loyer rows

#### Toast Undo Extension
- Extend existing `ui/toast/toaster.svelte`
- New type `undo`: message + "Annuler" button + 5s progress bar
- Callbacks: `onUndo()` cancels, `onExpire()` executes backend delete
- Add `aria-live="polite"` to toast container
- **Edge case**: On `beforeunload`, execute all pending deletes immediately (prevents data inconsistency if user navigates away during undo window)

### Modal Forms (8 total)

All in `frontend/src/lib/components/fiche-bien/modals/`:

| Modal | Size | Fields | API Call |
|-------|------|--------|----------|
| `LoyerModal.svelte` | Compact | période (mois/année), montant (pre-filled from bail.loyer_hc), statut (pills: payé/en_attente/en_retard) | `createLoyerForBien()` (existing, needs typing) |
| `BailModal.svelte` | Wide | date_debut, date_fin, loyer_hc, charges_provisions, depot_garantie, revision_indice, locataires (tag chips) | `createBail()` / `updateBail()` (existing, need typing) |
| `ChargeModal.svelte` | Compact | type_charge (select: copropriété/taxe_foncière/entretien/autre), montant, date_paiement | `createChargeForBien()` (NEW) |
| `PnoModal.svelte` | Compact | assureur, numéro_contrat, prime_annuelle, date_debut, date_fin | `createPnoForBien()` / `updatePnoForBien()` (NEW) |
| `FraisModal.svelte` | Compact | type_frais (select), montant, date_frais, description | `createFraisForBien()` (NEW) |
| `AssocieModal.svelte` | Compact | email, nom, rôle (pills: gérant/associé), part (%) | `inviteAssocie()` (NEW) |
| `SciModal.svelte` | Wide | nom, siren, regime_fiscal (IR/IS) | `createSci()` (existing, needs typing) |
| `BienModal.svelte` | Wide | adresse, ville, code_postal, type_bien, surface_m2, nb_pieces, prix_acquisition | `createBienForSci()` (existing, needs typing) |

**Notes on fields**:
- BailModal uses `revision_indice` (not `type_bail` — field doesn't exist on backend)
- SciModal uses `nom, siren, regime_fiscal` (matching existing `SCICreatePayload`)
- PnoModal uses `date_debut, date_fin` (matching `AssurancePnoEmbed` fields, not `date_echeance`)

### Form Validation Rules

| Modal | Required | Constraints |
|-------|----------|-------------|
| LoyerModal | période, montant, statut | montant >= 0 |
| BailModal | date_debut, loyer_hc | date_fin > date_debut if set; loyer_hc >= 0; charges_provisions >= 0; depot_garantie >= 0 |
| ChargeModal | type_charge, montant, date_paiement | montant >= 0 |
| PnoModal | assureur, prime_annuelle, date_debut | prime_annuelle >= 0 |
| FraisModal | type_frais, montant, date_frais | montant >= 0 |
| AssocieModal | email, nom, role, part | email format; 0 < part <= 100 |
| SciModal | nom | siren: 9 digits if provided |
| BienModal | adresse | surface_m2 >= 0; nb_pieces >= 0; prix_acquisition >= 0 |

### Error Handling

| Error | Display |
|-------|---------|
| Network error | Toast error: "Erreur de connexion. Réessayez." |
| 403 Forbidden (non-gérant) | Toast error: "Vous n'avez pas les droits pour cette action." |
| 402 Paywall | Toast info: "Fonctionnalité réservée au plan Pro." + link to /pricing |
| 409 Conflict | Toast error: "Un élément en conflit existe déjà." |
| 422 Validation | Display field-level errors in modal (red border + message under field) |
| Generic server error | Toast error: "Une erreur est survenue. Réessayez." |

### Wiring Pattern (same for all)

```
1. State:    let showModal = $state(false), editItem = $state(null)
2. Button:   onclick={() => { editItem = null; showModal = true }}      // create
             onclick={() => { editItem = item; showModal = true }}      // edit
3. Modal:    <XxxModal bind:open={showModal} {editItem} onSuccess={refresh} />
4. Success:  refresh() re-fetches section data only (not full fiche-bien)
5. Delete:   onclick → remove from local list → toast undo → on timeout: API delete
             On beforeunload: flush all pending deletes immediately
```

### Button-to-Action Mapping

#### FicheBienLoyers.svelte (3 buttons)
| Button (line) | Action |
|---------------|--------|
| "Enregistrer un loyer" (:43) | `showModal = true` → LoyerModal → `createLoyerForBien()` → refresh loyers |
| "Marquer comme payé" (:107) | DatePopover → `updateLoyer(id, {statut:'paye'})` → refresh inline → toast success |
| "Quittance" (:115) | `renderQuitus({loyer data})` → download blob PDF (visible only if statut=payé) |

**Note on "Mark as paid"**: `LoyerUpdatePayload` currently lacks `date_paiement`. The popover captures the date but we store it via `statut: 'paye'` only. If payment date tracking is needed later, add `date_paiement` to the backend `LoyerUpdate` schema and `LoyerUpdatePayload` type. For now, the date picker serves as UX confirmation, not data capture.

#### FicheBienBail.svelte (2 buttons)
| Button (line) | Action |
|---------------|--------|
| "Créer un bail" (:53) | `showModal = true` → BailModal → `createBail()` → refresh bail |
| "Modifier" (:86) | `editItem = bail; showModal = true` → BailModal prefilled → `updateBail()` |

Bail modal includes locataire management: tag chips with search. "Nouveau locataire" inline sub-form calls `createLocataire()` then `attachLocataireToBail()`. Both functions already exist in `api.ts`.

#### FicheBienCharges.svelte (7 buttons)
| Button (line) | Action |
|---------------|--------|
| "Ajouter une charge" (:34) | ChargeModal → `createChargeForBien()` |
| "Supprimer" charge (:99) | Toast undo → `deleteChargeForBien()` |
| PNO "Ajouter" (:124) | PnoModal → `createPnoForBien()` |
| PNO "Modifier" (:169) | PnoModal prefilled → `updatePnoForBien()` |
| PNO "Supprimer" (:174) | Toast undo → `deletePnoForBien()` |
| Frais "Ajouter" (:202) | FraisModal → `createFraisForBien()` |
| Frais "Supprimer" (:269) | Toast undo → `deleteFraisForBien()` |

#### FicheBienDocuments.svelte (modification)
| Current (line) | Change |
|----------------|--------|
| `confirm()` (:77) | Replace with toast undo pattern (using existing `deleteDocumentBien()`) |
| `alert()` (:82) | Replace with toast error |

#### associes/+page.svelte (1 button)
| Button (line) | Action |
|---------------|--------|
| "Inviter un associé" (:61) | AssocieModal → `inviteAssocie()` → refresh list |

#### scis/+page.svelte (1 fix)
| Button (line) | Action |
|---------------|--------|
| "Nouvelle SCI" (:28) | Change from `goto('/scis')` → `showModal = true` → SciModal → `createSci()` → navigate to `/scis/{newId}` |

#### biens/+page.svelte (1 fix)
| Button (line) | Action |
|---------------|--------|
| "Ajouter un bien" (:48) | Add `onclick` → BienModal → `createBienForSci()` → navigate to fiche bien |

### API Changes in `api.ts`

#### Genuinely New Functions (8)

```typescript
// Charge CRUD (no nested functions exist yet)
createChargeForBien(sciId: EntityId, bienId: EntityId, data: ChargeCreate): Promise<ChargeEmbed>
deleteChargeForBien(sciId: EntityId, bienId: EntityId, chargeId: number): Promise<void>

// PNO CRUD (no nested functions exist yet)
createPnoForBien(sciId: EntityId, bienId: EntityId, data: PnoCreate): Promise<AssurancePnoEmbed>
updatePnoForBien(sciId: EntityId, bienId: EntityId, pnoId: number, data: PnoUpdate): Promise<AssurancePnoEmbed>
deletePnoForBien(sciId: EntityId, bienId: EntityId, pnoId: number): Promise<void>

// Frais Agence (no mutation functions exist yet)
createFraisForBien(sciId: EntityId, bienId: EntityId, data: FraisCreate): Promise<FraisAgenceEmbed>
deleteFraisForBien(sciId: EntityId, bienId: EntityId, fraisId: number): Promise<void>

// Associés (invite function doesn't exist yet)
inviteAssocie(sciId: EntityId, data: InviteAssociePayload): Promise<any>
```

#### Existing Functions to Type (stop using `any`)

| Function | Current Return | Correct Return |
|----------|---------------|----------------|
| `fetchSciBiensList()` | `Promise<any[]>` | `Promise<Bien[]>` |
| `createBienForSci()` | `Promise<any>` | `Promise<Bien>` |
| `createLoyerForBien()` | `Promise<any>` | `Promise<LoyerEmbed>` |
| `fetchBienBaux()` | `Promise<any[]>` | `Promise<BailEmbed[]>` |
| `createBail()` | `Promise<any>` | `Promise<BailEmbed>` |
| `updateBail()` | `Promise<any>` | `Promise<BailEmbed>` |
| `fetchBienCharges()` | `Promise<any[]>` | `Promise<ChargeEmbed[]>` |
| `fetchBienPno()` | `Promise<any[]>` | `Promise<AssurancePnoEmbed[]>` |
| `fetchBienFraisAgence()` | `Promise<any[]>` | `Promise<FraisAgenceEmbed[]>` |
| `fetchSciAssociesList()` | `Promise<any[]>` | `Promise<AssocieEmbed[]>` |

Also type `FicheBien.loyers_recents: Array<any>` → `LoyerEmbed[]` and `FicheBien.charges_list: Array<any>` → `ChargeEmbed[]`.

#### New Types to Add

```typescript
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

export type LoyerEmbed = {
  id: number;
  date_loyer: string;
  montant: number;
  statut: LoyerStatus;
  quitus_genere: boolean;
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

export type AssocieEmbed = {
  id: number;
  nom: string;
  email: string;
  role: string;
  part: number;
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

### Backend Additions

Two new endpoints in `backend/app/api/v1/scis.py`:

1. `PATCH /api/v1/scis/{sci_id}` — update SCI (nom, siren, regime_fiscal)
   - Requires `require_gerant_role` dependency
   - Returns updated SCI object

2. `DELETE /api/v1/scis/{sci_id}` — delete SCI with cascade
   - Requires `require_gerant_role` dependency
   - Cascades via Supabase foreign keys (biens → baux → loyers → etc.)
   - Returns 204 No Content

### File Changes Summary

| File | Action | Scope |
|------|--------|-------|
| `lib/components/ui/CrudModal.svelte` | **Create** | Reusable modal component |
| `lib/components/ui/DatePopover.svelte` | **Create** | Date picker popover |
| `lib/components/ui/toast/toaster.svelte` | **Modify** | Add undo type + aria-live + beforeunload flush |
| `lib/components/fiche-bien/modals/LoyerModal.svelte` | **Create** | Loyer form |
| `lib/components/fiche-bien/modals/BailModal.svelte` | **Create** | Bail form (wide, locataire tags) |
| `lib/components/fiche-bien/modals/ChargeModal.svelte` | **Create** | Charge form |
| `lib/components/fiche-bien/modals/PnoModal.svelte` | **Create** | PNO form |
| `lib/components/fiche-bien/modals/FraisModal.svelte` | **Create** | Frais agence form |
| `lib/components/fiche-bien/modals/AssocieModal.svelte` | **Create** | Invite associé form |
| `lib/components/fiche-bien/modals/SciModal.svelte` | **Create** | Create SCI form (wide) |
| `lib/components/fiche-bien/modals/BienModal.svelte` | **Create** | Create bien form (wide) |
| `lib/components/fiche-bien/FicheBienLoyers.svelte` | **Modify** | Wire 3 buttons + import modals + type props |
| `lib/components/fiche-bien/FicheBienBail.svelte` | **Modify** | Wire 2 buttons + import modal |
| `lib/components/fiche-bien/FicheBienCharges.svelte` | **Modify** | Wire 7 buttons + import modals + type props |
| `lib/components/fiche-bien/FicheBienDocuments.svelte` | **Modify** | Replace confirm/alert with toast undo |
| `routes/(app)/scis/[sciId]/associes/+page.svelte` | **Modify** | Wire invite button |
| `routes/(app)/scis/+page.svelte` | **Modify** | Wire "Nouvelle SCI" → modal |
| `routes/(app)/scis/[sciId]/biens/+page.svelte` | **Modify** | Wire "Ajouter un bien" → modal |
| `lib/api.ts` | **Modify** | Add 8 new functions + 12 type fixes + new types |
| `backend/app/api/v1/scis.py` | **Modify** | Add PATCH + DELETE endpoints |

**Total: 11 new files, 9 modified files, 2 backend endpoints**

## Success Criteria

1. All 15 previously-dead buttons trigger functional CRUD flows
2. Zero `any` types in API functions related to fiche-bien domain
3. All modals have proper accessibility (focus trap, aria attributes, keyboard nav)
4. Toast undo replaces all native `confirm()`/`alert()` usage
5. Each modal shows loading state during API call and error toast on failure
6. Existing tests continue to pass
7. New unit tests for CrudModal and each modal form
8. Form validation prevents invalid submissions (required fields, numeric constraints)
