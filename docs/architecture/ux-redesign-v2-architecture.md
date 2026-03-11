# GererSCI — Architecture Technique UX Redesign V2

> Date: 2026-03-10
> Statut: DRAFT
> Source: `docs/specs/ux-redesign-v2.md`
> Scope: Database, Backend API, Frontend routing/layout, middleware, permissions

---

## Table des matières

1. [Vue d'ensemble des changements](#1-vue-densemble)
2. [Base de données — Migration 008](#2-base-de-données)
3. [Backend — Nouveaux endpoints et middleware](#3-backend)
4. [Frontend — Routes et layout](#4-frontend)
5. [Paywall & Onboarding](#5-paywall--onboarding)
6. [Permissions associés](#6-permissions-associés)
7. [Notifications](#7-notifications)
8. [Migration des données existantes](#8-migration-données)
9. [Impacts sur le code existant](#9-impacts-existant)

---

## 1. Vue d'ensemble

### Architecture actuelle (AS-IS)

```
Routes plates:     /biens, /loyers, /locataires, /charges, /associes, /fiscalite
Auth guard:        +layout.svelte $effect → isProtectedRoute() → redirect /login
SCI context:       localStorage (selectedSciId), pas dans l'URL
API:               /api/v1/{resource}/ — flat, SCI filtré via query param ?id_sci=
Subscription:      subscriptions table avec plan_key + entitlements, pas de paywall
Sidebar:           AppSidebar.svelte — flat nav items
```

### Architecture cible (TO-BE)

```
Routes imbriquées: /scis/:sciId/biens/:bienId
Auth guard:        Layout middleware → auth + subscription active + onboarding done
SCI context:       URL param (sciId), synced to store
API:               /api/v1/scis/{sci_id}/biens/{bien_id} — nested, ownership implicit
Subscription:      Paywall obligatoire — redirect /pricing si !is_active
Sidebar:           Dynamique selon SCI sélectionnée, role-aware
```

### Diagramme de flux utilisateur

```
Visiteur → / → /pricing → Stripe → magic link → /auth/callback
                                                       ↓
                                              onboarding_completed?
                                              ├─ false → /onboarding (wizard 5 steps)
                                              └─ true  → /dashboard
                                                              ↓
                                                    subscription.is_active?
                                                    ├─ false → /pricing
                                                    └─ true  → app complète
```

---

## 2. Base de données

### 2.1 Migration 008 — Nouvelles tables et colonnes

Fichier: `supabase/migrations/008_ux_redesign_v2.sql`

#### Colonnes ajoutées

```sql
-- biens: enrichissement fiche bien
ALTER TABLE biens ADD COLUMN IF NOT EXISTS surface_m2 NUMERIC;
ALTER TABLE biens ADD COLUMN IF NOT EXISTS nb_pieces INTEGER;
ALTER TABLE biens ADD COLUMN IF NOT EXISTS dpe_classe TEXT CHECK (dpe_classe IN ('A','B','C','D','E','F','G'));
ALTER TABLE biens ADD COLUMN IF NOT EXISTS photo_url TEXT;
ALTER TABLE biens ADD COLUMN IF NOT EXISTS prix_acquisition NUMERIC(14,2);
-- Note: prix_acquisition existe peut-être déjà — vérifier avant migration

-- locataires: téléphone
ALTER TABLE locataires ADD COLUMN IF NOT EXISTS telephone TEXT;

-- subscriptions: flag onboarding
ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN DEFAULT FALSE;
```

#### Nouvelles tables

**baux** — remplace le lien date direct locataire→bien

```sql
CREATE TABLE baux (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  id_bien UUID NOT NULL REFERENCES biens(id) ON DELETE CASCADE,
  date_debut DATE NOT NULL,
  date_fin DATE,
  loyer_hc NUMERIC(12,2) NOT NULL CHECK (loyer_hc >= 0),
  charges_locatives NUMERIC(12,2) DEFAULT 0 CHECK (charges_locatives >= 0),
  depot_garantie NUMERIC(12,2) DEFAULT 0 CHECK (depot_garantie >= 0),
  indice_irl_reference TEXT,
  date_revision DATE,
  etat_lieux_entree DATE,
  etat_lieux_sortie DATE,
  statut TEXT NOT NULL DEFAULT 'en_cours' CHECK (statut IN ('en_cours','expire','resilie')),
  document_url TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_baux_id_bien ON baux(id_bien);
CREATE INDEX idx_baux_statut ON baux(statut);
```

**bail_locataires** — jointure N:N pour colocation

```sql
CREATE TABLE bail_locataires (
  id_bail UUID NOT NULL REFERENCES baux(id) ON DELETE CASCADE,
  id_locataire UUID NOT NULL REFERENCES locataires(id) ON DELETE CASCADE,
  PRIMARY KEY (id_bail, id_locataire)
);
```

**assurances_pno** — assurance propriétaire non-occupant

```sql
CREATE TABLE assurances_pno (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  id_bien UUID NOT NULL REFERENCES biens(id) ON DELETE CASCADE,
  compagnie TEXT NOT NULL,
  numero_contrat TEXT,
  montant_annuel NUMERIC(12,2) NOT NULL CHECK (montant_annuel >= 0),
  date_echeance DATE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_assurances_pno_id_bien ON assurances_pno(id_bien);
```

**frais_agence** — frais de gestion locative

```sql
CREATE TABLE frais_agence (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  id_bien UUID NOT NULL REFERENCES biens(id) ON DELETE CASCADE,
  nom_agence TEXT NOT NULL,
  contact TEXT,
  type_frais TEXT NOT NULL CHECK (type_frais IN ('pourcentage','fixe')),
  montant_ou_pourcentage NUMERIC(12,2) NOT NULL CHECK (montant_ou_pourcentage >= 0),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_frais_agence_id_bien ON frais_agence(id_bien);
```

**notification_preferences** — config email/in-app par type

```sql
CREATE TABLE notification_preferences (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL,
  type TEXT NOT NULL,
  email_enabled BOOLEAN DEFAULT FALSE,
  in_app_enabled BOOLEAN DEFAULT TRUE,
  UNIQUE(user_id, type)
);

CREATE INDEX idx_notification_prefs_user ON notification_preferences(user_id);
```

**documents_bien** — fichiers attachés aux biens

```sql
CREATE TABLE documents_bien (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  id_bien UUID NOT NULL REFERENCES biens(id) ON DELETE CASCADE,
  categorie TEXT NOT NULL CHECK (categorie IN ('bail','diagnostic','etat_lieux','quittance','photo','autre')),
  nom TEXT NOT NULL,
  file_url TEXT NOT NULL,
  file_size INTEGER,
  uploaded_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_documents_bien_id_bien ON documents_bien(id_bien);
```

#### Triggers updated_at

```sql
-- Toutes les nouvelles tables avec updated_at
CREATE TRIGGER trg_baux_updated_at BEFORE UPDATE ON baux
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_assurances_pno_updated_at BEFORE UPDATE ON assurances_pno
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

CREATE TRIGGER trg_frais_agence_updated_at BEFORE UPDATE ON frais_agence
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();
```

### 2.2 RLS Policies

**Pattern commun** : accès via `biens.id_sci → associes.user_id = auth.uid()`

Pour les tables liées à un bien (`baux`, `assurances_pno`, `frais_agence`, `documents_bien`) :

```sql
-- SELECT: tous les associés de la SCI
CREATE POLICY {table}_member_select ON {table}
FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = {table}.id_bien AND a.user_id = auth.uid()
  )
);

-- INSERT/UPDATE/DELETE: gérants uniquement
CREATE POLICY {table}_gerant_insert ON {table}
FOR INSERT WITH CHECK (
  EXISTS (
    SELECT 1 FROM biens b
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE b.id = {table}.id_bien
      AND a.user_id = auth.uid()
      AND a.role = 'gerant'
  )
);
-- Idem pour UPDATE (USING + WITH CHECK) et DELETE (USING)
```

Pour `notification_preferences` :
```sql
-- Owner only (user_id = auth.uid())
CREATE POLICY notif_prefs_owner ON notification_preferences
FOR ALL USING (user_id = auth.uid());
```

Pour `bail_locataires` :
```sql
-- Via le bail → bien → SCI → associes
CREATE POLICY bail_loc_member_select ON bail_locataires
FOR SELECT USING (
  EXISTS (
    SELECT 1 FROM baux bx
    JOIN biens b ON b.id = bx.id_bien
    JOIN associes a ON a.id_sci = b.id_sci
    WHERE bx.id = bail_locataires.id_bail AND a.user_id = auth.uid()
  )
);
```

### 2.3 Schéma relationnel final

```
auth.users (Supabase)
  └─> subscriptions (1:1 via user_id) ← paywall + onboarding_completed
  └─> notification_preferences (1:N via user_id)
  └─> associes (1:N via user_id)
        └─> sci (N:1 via id_sci)
              └─> biens (1:N via id_sci)
                    ├─> baux (1:N via id_bien)
                    │     └─> bail_locataires (N:N baux↔locataires)
                    ├─> locataires (1:N via id_bien)
                    ├─> loyers (1:N via id_bien)
                    ├─> charges (1:N via id_bien)
                    ├─> assurances_pno (1:N via id_bien)
                    ├─> frais_agence (1:N via id_bien)
                    └─> documents_bien (1:N via id_bien)
              └─> fiscalite (1:N via id_sci)
  └─> admins (1:1 via user_id)
  └─> notifications (1:N via user_id)
  └─> gdpr_exports (1:N via user_id)
```

---

## 3. Backend

### 3.1 Nouveaux routers

#### Structure API cible

```
/api/v1/
├── auth/              (existant — inchangé)
├── health/            (existant — inchangé)
├── stripe/            (existant — inchangé)
├── admin/             (existant — inchangé)
├── gdpr/              (existant — inchangé)
│
├── scis/                          GET (list), POST (create)
│   └── {sci_id}/
│       ├──                        GET (detail + KPIs)
│       ├── biens/                 GET (list), POST (create)
│       │   └── {bien_id}/
│       │       ├──                GET (fiche complète), PATCH, DELETE
│       │       ├── baux/          GET (list), POST (create)
│       │       │   └── {bail_id}/ GET, PATCH, DELETE
│       │       │       └── locataires/  POST (attach), DELETE (detach)
│       │       ├── loyers/        GET (list, filtered), POST
│       │       │   └── {loyer_id}/  PATCH, DELETE
│       │       ├── charges/       GET, POST
│       │       │   └── {charge_id}/  PATCH, DELETE
│       │       ├── assurance-pno/ GET, POST, PATCH, DELETE
│       │       ├── frais-agence/  GET, POST, PATCH, DELETE
│       │       └── documents/     GET, POST (upload), DELETE
│       ├── associes/              GET, POST (invite), PATCH, DELETE
│       ├── fiscalite/             GET, POST, PATCH, DELETE
│       └── documents/             GET (SCI-level docs)
│
├── finances/                      GET (cross-SCI aggregates)
├── notifications/                 (existant — enrichir types)
├── onboarding/                    POST (complete step), GET (status)
│
├── user/
│   └── notification-preferences/  GET, PUT
│
└── quitus/                        (existant — inchangé)
```

#### Rétrocompatibilité

Les anciens endpoints plats (`/api/v1/biens/`, `/api/v1/loyers/`, etc.) restent fonctionnels pendant la transition mais marqués `@deprecated`. Le frontend v2 utilise exclusivement les endpoints imbriqués.

### 3.2 Nouveau middleware — Paywall

Fichier: `backend/app/core/paywall.py`

```python
# Dependency function pour FastAPI
async def require_active_subscription(
    user_id: str = Depends(get_current_user_id)
) -> SubscriptionInfo:
    """
    Vérifie que l'utilisateur a un abonnement actif.
    Raise HTTP 402 (Payment Required) si non.
    """
    sub = await get_subscription(user_id)
    if not sub or not sub.is_active:
        raise HTTPException(
            status_code=402,
            detail={"code": "subscription_required", "redirect": "/pricing"}
        )
    return sub
```

Appliqué sur tous les routers protégés via `dependencies=[Depends(require_active_subscription)]`.

### 3.3 Middleware — Ownership validation

```python
async def require_sci_membership(
    sci_id: UUID,
    user_id: str = Depends(get_current_user_id)
) -> AssocieMembership:
    """
    Vérifie que l'utilisateur est associé de la SCI.
    Retourne le rôle (gerant/associe).
    """
    membership = await get_membership(user_id, sci_id)
    if not membership:
        raise HTTPException(status_code=404)
    return membership


async def require_gerant_role(
    membership: AssocieMembership = Depends(require_sci_membership)
) -> AssocieMembership:
    """
    Vérifie que l'utilisateur est gérant (pas juste associé).
    Pour les opérations d'écriture.
    """
    if membership.role != 'gerant':
        raise HTTPException(status_code=403, detail="Gérant access required")
    return membership
```

### 3.4 Nouveaux schemas Pydantic

Fichier: `backend/app/schemas/`

```python
# baux.py
class BailCreate(BaseModel):
    date_debut: date
    date_fin: date | None = None
    loyer_hc: Decimal
    charges_locatives: Decimal = 0
    depot_garantie: Decimal = 0
    indice_irl_reference: str | None = None
    date_revision: date | None = None
    etat_lieux_entree: date | None = None
    statut: Literal['en_cours', 'expire', 'resilie'] = 'en_cours'
    locataire_ids: list[UUID] = []  # Pour la colocation

class BailResponse(BailCreate):
    id: UUID
    id_bien: UUID
    locataires: list[LocataireResponse] = []
    created_at: datetime
    updated_at: datetime

# assurance_pno.py
class AssurancePnoCreate(BaseModel):
    compagnie: str
    numero_contrat: str | None = None
    montant_annuel: Decimal
    date_echeance: date

# frais_agence.py
class FraisAgenceCreate(BaseModel):
    nom_agence: str
    contact: str | None = None
    type_frais: Literal['pourcentage', 'fixe']
    montant_ou_pourcentage: Decimal

# documents.py
class DocumentBienResponse(BaseModel):
    id: UUID
    categorie: str
    nom: str
    file_url: str
    file_size: int | None
    uploaded_at: datetime

# onboarding.py
class OnboardingStatus(BaseModel):
    completed: bool
    current_step: int  # 0-5
    sci_created: bool
    bien_created: bool
    bail_configured: bool
    notifications_set: bool

# fiche_bien.py — réponse enrichie
class FicheBienResponse(BaseModel):
    bien: BienResponse
    bail_actif: BailResponse | None
    loyers_recents: list[LoyerResponse]
    charges: list[ChargeResponse]
    assurance_pno: AssurancePnoResponse | None
    frais_agence: FraisAgenceResponse | None
    documents: list[DocumentBienResponse]
    rentabilite: RentabiliteCalculee
```

### 3.5 Endpoint Dashboard — KPIs agrégés

```python
# GET /api/v1/dashboard
@router.get("/dashboard")
async def get_dashboard(
    user_id: str = Depends(get_current_user_id),
    sub: SubscriptionInfo = Depends(require_active_subscription)
):
    return {
        "alertes": await get_alertes(user_id),      # loyers retard, baux expirant, quittances
        "kpis": await get_portfolio_kpis(user_id),   # SCI count, biens, recouvrement, cashflow
        "scis": await get_sci_cards(user_id),        # SCI list with summary
        "activite": await get_recent_activity(user_id, limit=10)
    }
```

### 3.6 Endpoint Finances transversales

```python
# GET /api/v1/finances
@router.get("/finances")
async def get_finances(
    user_id: str = Depends(get_current_user_id),
    sub: SubscriptionInfo = Depends(require_active_subscription),
    period: str = Query(default="12m")
):
    return {
        "revenus_mensuels": ...,
        "charges_mensuelles": ...,
        "cashflow_net": ...,
        "taux_recouvrement": ...,
        "loyers_en_retard": ...,
        "patrimoine_total": ...,
        "rentabilite_moyenne": ...,
        "evolution_12m": [...],       # Pour bar chart
        "repartition_par_sci": [...]  # Pour donut chart
    }
```

---

## 4. Frontend

### 4.1 Nouvelle structure de routes SvelteKit

```
frontend/src/routes/
├── +layout.svelte                    (root — nav publique/privée)
├── +page.svelte                      (landing page)
├── pricing/+page.svelte              (existant)
├── login/+page.svelte                (existant)
├── register/+page.svelte             (existant — redirect vers /pricing)
├── auth/callback/+page.svelte        (existant)
├── success/+page.svelte              (existant)
│
├── (app)/                            ← route group pour layout authentifié
│   ├── +layout.svelte                ← PAYWALL + ONBOARDING GUARD
│   ├── +layout.ts                    ← load subscription + onboarding status
│   │
│   ├── onboarding/+page.svelte       ← wizard 5 étapes
│   │
│   ├── dashboard/+page.svelte        ← 4 blocs compartimentés
│   │
│   ├── scis/
│   │   ├── +page.svelte              ← liste des SCI
│   │   └── [sciId]/
│   │       ├── +layout.svelte        ← SCI context provider
│   │       ├── +layout.ts            ← load SCI detail + validate membership
│   │       ├── +page.svelte          ← vue d'ensemble SCI
│   │       ├── biens/
│   │       │   ├── +page.svelte      ← liste biens de la SCI
│   │       │   └── [bienId]/
│   │       │       ├── +page.svelte  ← FICHE BIEN COMPLÈTE
│   │       │       └── baux/+page.svelte  ← historique des baux
│   │       ├── associes/+page.svelte
│   │       ├── fiscalite/+page.svelte
│   │       └── documents/+page.svelte
│   │
│   ├── finances/+page.svelte
│   │
│   ├── settings/+page.svelte         ← notifications + interface
│   ├── account/
│   │   ├── +page.svelte
│   │   └── privacy/+page.svelte
│   │
│   └── admin/                        ← existant, inchangé
│       ├── +layout.svelte
│       ├── +page.svelte
│       └── users/+page.svelte
│
├── confidentialite/+page.svelte      (existant, public)
├── mentions-legales/+page.svelte     (existant, public)
└── cgu/+page.svelte                  (existant, public)
```

### 4.2 Layout (app) — Paywall & Onboarding Guard

Fichier: `frontend/src/routes/(app)/+layout.ts`

```typescript
import type { LayoutLoad } from './$types';
import { redirect } from '@sveltejs/kit';
import { getCurrentSession } from '$lib/auth/session';
import { fetchSubscriptionEntitlements } from '$lib/api';

export const load: LayoutLoad = async ({ url }) => {
  const session = await getCurrentSession();
  if (!session?.user) {
    throw redirect(302, `/login?redirect=${encodeURIComponent(url.pathname)}`);
  }

  const subscription = await fetchSubscriptionEntitlements();

  // Paywall: redirect si pas d'abonnement actif
  if (!subscription.is_active && url.pathname !== '/pricing') {
    throw redirect(302, '/pricing');
  }

  // Onboarding: redirect si pas complété (sauf si déjà sur /onboarding)
  if (!subscription.onboarding_completed && !url.pathname.startsWith('/onboarding')) {
    throw redirect(302, '/onboarding');
  }

  return { user: session.user, subscription };
};
```

Fichier: `frontend/src/routes/(app)/+layout.svelte`

```svelte
<script lang="ts">
  import AppSidebar from '$lib/components/AppSidebarV2.svelte';
  import { setContext } from 'svelte';

  let { data, children } = $props();

  // Provide subscription and user to all child routes
  setContext('user', data.user);
  setContext('subscription', data.subscription);
</script>

<div class="flex min-h-screen">
  <AppSidebar user={data.user} subscription={data.subscription} />
  <main class="flex-1 overflow-auto">
    {@render children()}
  </main>
</div>
```

### 4.3 Layout SCI context

Fichier: `frontend/src/routes/(app)/scis/[sciId]/+layout.ts`

```typescript
import type { LayoutLoad } from './$types';
import { error } from '@sveltejs/kit';
import { apiFetch, type SCIDetail } from '$lib/api';

export const load: LayoutLoad = async ({ params, parent }) => {
  const { user } = await parent();
  const sci = await apiFetch<SCIDetail>(`/api/v1/scis/${params.sciId}`);
  if (!sci) throw error(404, 'SCI non trouvée');

  // Find user's role in this SCI
  const membership = sci.associes?.find(a => a.user_id === user.id);
  const userRole = membership?.role ?? 'associe';

  return { sci, userRole, sciId: params.sciId };
};
```

### 4.4 SCI Context Store

Fichier: `frontend/src/lib/stores/sci-context.ts`

```typescript
import { writable, derived } from 'svelte/store';
import type { SCIDetail } from '$lib/api';

export const currentSci = writable<SCIDetail | null>(null);
export const currentSciId = derived(currentSci, $sci => $sci?.id ?? null);
export const userRole = writable<'gerant' | 'associe'>('associe');
export const isGerant = derived(userRole, $role => $role === 'gerant');
```

### 4.5 Sidebar V2

Fichier: `frontend/src/lib/components/AppSidebarV2.svelte`

La sidebar est dynamique :
- **Sans SCI sélectionnée** : Dashboard, Mes SCI, Finances, Paramètres, Compte
- **Avec SCI sélectionnée** : sous-nav SCI (Vue d'ensemble, Biens, Associés, Fiscalité, Documents)
- **Responsive** : drawer sur mobile, fixed sur desktop

```
┌──────────────────┐
│ Logo GererSCI    │
├──────────────────┤
│ 📊 Dashboard     │
├──────────────────┤
│ 🏢 Mes SCI       │
│   ├─ SCI Alpha ◀ │ (active)
│   │  ├─ Biens    │
│   │  ├─ Associés │
│   │  ├─ Fiscalité│
│   │  └─ Docs     │
│   └─ SCI Beta    │
├──────────────────┤
│ 💰 Finances      │
├──────────────────┤
│ ⚙️ Paramètres    │
│ 👤 Compte        │
└──────────────────┘
```

### 4.6 API Client — Nouvelles fonctions

Fichier: `frontend/src/lib/api.ts` — Ajouts

```typescript
// --- Baux ---
export type Bail = {
  id: EntityId;
  id_bien: EntityId;
  date_debut: string;
  date_fin: string | null;
  loyer_hc: number;
  charges_locatives: number;
  depot_garantie: number;
  indice_irl_reference: string | null;
  date_revision: string | null;
  etat_lieux_entree: string | null;
  etat_lieux_sortie: string | null;
  statut: 'en_cours' | 'expire' | 'resilie';
  document_url: string | null;
  locataires: Locataire[];
  created_at?: string;
  updated_at?: string;
};

export type AssurancePno = {
  id: EntityId;
  id_bien: EntityId;
  compagnie: string;
  numero_contrat: string | null;
  montant_annuel: number;
  date_echeance: string;
};

export type FraisAgence = {
  id: EntityId;
  id_bien: EntityId;
  nom_agence: string;
  contact: string | null;
  type_frais: 'pourcentage' | 'fixe';
  montant_ou_pourcentage: number;
};

export type DocumentBien = {
  id: EntityId;
  id_bien: EntityId;
  categorie: string;
  nom: string;
  file_url: string;
  file_size: number | null;
  uploaded_at: string;
};

// --- Fiche Bien (aggregated response) ---
export type FicheBien = {
  bien: Bien;
  bail_actif: Bail | null;
  loyers_recents: Loyer[];
  charges: Charge[];
  assurance_pno: AssurancePno | null;
  frais_agence: FraisAgence | null;
  documents: DocumentBien[];
  rentabilite: {
    brute: number | null;
    nette: number | null;
    cashflow_mensuel: number | null;
    cashflow_annuel: number | null;
  };
};

// --- Dashboard ---
export type DashboardData = {
  alertes: DashboardAlerte[];
  kpis: DashboardKpis;
  scis: SCICard[];
  activite: ActivityItem[];
};

// --- Nested API calls ---
export function fetchSciBiens(sciId: EntityId) {
  return apiFetch<Bien[]>(`/api/v1/scis/${sciId}/biens`);
}

export function fetchFicheBien(sciId: EntityId, bienId: EntityId) {
  return apiFetch<FicheBien>(`/api/v1/scis/${sciId}/biens/${bienId}`);
}

export function fetchBienBaux(sciId: EntityId, bienId: EntityId) {
  return apiFetch<Bail[]>(`/api/v1/scis/${sciId}/biens/${bienId}/baux`);
}

export function fetchDashboard() {
  return apiFetch<DashboardData>('/api/v1/dashboard');
}

export function fetchFinances(period = '12m') {
  return apiFetch<FinancesData>(`/api/v1/finances?period=${period}`);
}

// --- Onboarding ---
export function fetchOnboardingStatus() {
  return apiFetch<OnboardingStatus>('/api/v1/onboarding');
}

export function completeOnboardingStep(step: number, data: Record<string, unknown>) {
  return apiFetch<OnboardingStatus>('/api/v1/onboarding', {
    method: 'POST',
    body: JSON.stringify({ step, data })
  });
}
```

### 4.7 Composants clés à créer

| Composant | Rôle | Priorité |
|-----------|------|----------|
| `AppSidebarV2.svelte` | Sidebar dynamique avec SCI tree | P0 |
| `OnboardingWizard.svelte` | Wizard 5 steps | P0 |
| `DashboardAlerts.svelte` | Bloc 1 — alertes actions urgentes | P0 |
| `DashboardKpis.svelte` | Bloc 2 — 4 KPI cards | P0 |
| `DashboardSciCards.svelte` | Bloc 3 — grille SCI cliquables | P0 |
| `DashboardActivity.svelte` | Bloc 4 — timeline activité | P0 |
| `FicheBienHeader.svelte` | Header fiche bien + breadcrumb | P0 |
| `FicheBienIdentite.svelte` | Section A — identité | P0 |
| `FicheBienLoyers.svelte` | Section C — loyers du bien | P0 |
| `FicheBienBail.svelte` | Section B — bail actif + historique | P1 |
| `FicheBienCharges.svelte` | Section D — charges + PNO + agence | P1 |
| `FicheBienRentabilite.svelte` | Section E — indicateurs calculés | P2 |
| `FicheBienDocuments.svelte` | Section F — documents uploadés | P2 |
| `FinancesDashboard.svelte` | Vue finances transversale | P2 |
| `RoleGate.svelte` | Wrapper conditionnel gérant/associé | P1 |

---

## 5. Paywall & Onboarding

### 5.1 Paywall Flow

```
Toute route dans (app)/ :
  1. +layout.ts vérifie auth (session Supabase)
  2. Charge subscription via /api/v1/stripe/subscription
  3. Si !is_active → redirect /pricing
  4. Si !onboarding_completed → redirect /onboarding
  5. Sinon → render la page
```

**Backend** : Le endpoint `GET /api/v1/stripe/subscription` retourne déjà `is_active` et `plan_key`. Ajouter `onboarding_completed` au `SubscriptionEntitlements` response.

**Cas edge** :
- Stripe webhook reçu avant 1ère connexion → subscription active, onboarding non complété → ok
- User désabonné → `is_active = false` → redirigé vers /pricing à la prochaine navigation
- Lifetime → `is_active = true` permanent

### 5.2 Onboarding Wizard

Route: `/onboarding`

5 étapes séquentielles, non-skippable :

| Step | Action | API call |
|------|--------|----------|
| 1 | Créer 1ère SCI | POST /api/v1/scis/ |
| 2 | Ajouter 1er bien | POST /api/v1/scis/{id}/biens |
| 3 | Configurer bail + locataire | POST /api/v1/scis/{id}/biens/{id}/baux |
| 4 | Préférences notifications | PUT /api/v1/user/notification-preferences |
| 5 | Tour guidé (frontend only) | PATCH /api/v1/onboarding (complete) |

Le wizard utilise un composant stepper avec état local. Chaque étape valide côté backend avant de passer à la suivante. Step 5 marque `onboarding_completed = true`.

---

## 6. Permissions Associés

### 6.1 Matrice Backend

| Opération | Gérant | Associé |
|-----------|--------|---------|
| GET (lecture) | Toutes tables | Toutes tables |
| POST/PATCH/DELETE (écriture) | Toutes tables | Aucune |

**Implémentation** :
- `Depends(require_sci_membership)` sur tous les GET → retourne le rôle
- `Depends(require_gerant_role)` sur tous les POST/PATCH/DELETE
- RLS Supabase : policies SELECT (tous associés) vs INSERT/UPDATE/DELETE (gérant only)

### 6.2 Frontend

Composant `RoleGate.svelte` :

```svelte
<script lang="ts">
  import { getContext } from 'svelte';
  let { children, fallback } = $props();
  const userRole = getContext<string>('userRole');
</script>

{#if userRole === 'gerant'}
  {@render children()}
{:else if fallback}
  {@render fallback()}
{/if}
```

Usage dans les pages :
```svelte
<RoleGate>
  <Button onclick={addBien}>Ajouter un bien</Button>
</RoleGate>
```

---

## 7. Notifications

### 7.1 Types à ajouter

| Type | Trigger backend | Email | In-app |
|------|----------------|-------|--------|
| `late_payment` | Cron : loyer date < now - 5j, statut != 'paye' | opt-in | oui |
| `bail_expiring` | Cron : bail.date_fin < now + 90j | opt-in | oui |
| `quittance_pending` | Cron : 1er du mois, baux actifs sans quittance | opt-in | oui |
| `pno_expiring` | Cron : assurance.date_echeance < now + 30j | opt-in | oui |
| `new_loyer` | After INSERT loyer | non | oui |
| `new_associe` | After INSERT associé | opt-in | oui |
| `subscription_expiring` | Cron : current_period_end < now + 7j | oui | oui |

### 7.2 Configuration

- **Table** : `notification_preferences` (user_id, type, email_enabled, in_app_enabled)
- **Default** : in-app ON, email OFF (sauf subscription_expiring)
- **UI** : `/settings` → section Notifications avec toggles par type
- **Onboarding step 4** : toggle global email ON/OFF → popule les preferences par défaut

---

## 8. Migration des données existantes

### 8.1 Locataires → Baux

Les locataires actuels ont `date_debut` et `date_fin` directement. Il faut :

```sql
-- Créer un bail pour chaque locataire existant
INSERT INTO baux (id_bien, date_debut, date_fin, loyer_hc, statut)
SELECT
  l.id_bien,
  l.date_debut,
  l.date_fin,
  b.loyer_cc,  -- approximation: loyer CC du bien
  CASE
    WHEN l.date_fin IS NOT NULL AND l.date_fin < CURRENT_DATE THEN 'expire'
    ELSE 'en_cours'
  END
FROM locataires l
JOIN biens b ON b.id = l.id_bien;

-- Créer les jointures bail_locataires
INSERT INTO bail_locataires (id_bail, id_locataire)
SELECT bx.id, l.id
FROM baux bx
JOIN locataires l ON l.id_bien = bx.id_bien
  AND l.date_debut = bx.date_debut;
```

### 8.2 Prix acquisition

Vérifier si `biens.prix_acquisition` existe déjà (non présent dans migration 001 mais présent dans le type TypeScript). Si pas en DB, l'ajouter dans migration 008.

### 8.3 Onboarding pour utilisateurs existants

Les utilisateurs existants avec un abonnement actif ont `onboarding_completed = false` par défaut. Options :

**Option A** (recommandée) : Mettre `onboarding_completed = true` pour tous les users existants avec `is_active = true` dans la migration.

```sql
UPDATE subscriptions SET onboarding_completed = true WHERE is_active = true;
```

**Option B** : Forcer l'onboarding même pour les anciens users. Risque de friction.

---

## 9. Impacts sur le code existant

### 9.1 Routes à supprimer (après migration frontend complète)

| Ancienne route | Remplacée par |
|---------------|---------------|
| `/biens` | `/scis/:sciId/biens` |
| `/locataires` | Intégré dans fiche bien |
| `/loyers` | `/scis/:sciId/biens/:bienId` (section C) |
| `/charges` | `/scis/:sciId/biens/:bienId` (section D) |
| `/associes` | `/scis/:sciId/associes` |
| `/fiscalite` | `/scis/:sciId/fiscalite` |
| `/exploitation` | Supprimée (remplacée par dashboard) |
| `/finance` | `/finances` |
| `/documents` | `/scis/:sciId/documents` |
| `/register` | Redirect vers `/pricing` |

### 9.2 Composants à modifier

| Composant | Changement |
|-----------|------------|
| `+layout.svelte` (root) | Retirer sidebar logic, garder nav publique |
| `AppSidebar.svelte` | Remplacé par `AppSidebarV2.svelte` |
| `AppBreadcrumbs.svelte` | Adapter au nouveau routage imbriqué |
| `route-guard.ts` | Simplifier : tout (app)/ est protégé par layout |
| `api.ts` | Ajouter types et fonctions nested, deprecate flat |

### 9.3 Backend — Endpoints à enrichir

| Endpoint existant | Enrichissement |
|-------------------|---------------|
| `GET /api/v1/scis/{id}` | Ajouter KPIs (biens_count, loyer_total, recouvrement) |
| `GET /api/v1/stripe/subscription` | Ajouter `onboarding_completed` |
| Tous les endpoints | Ajouter `Depends(require_active_subscription)` |

### 9.4 Fichiers backend inchangés

- `app/core/config.py` — pas de nouvelle config nécessaire
- `app/core/security.py` — JWT validation inchangée
- `app/api/v1/stripe.py` — checkout + webhook inchangés
- `app/api/v1/auth.py` — auth flow inchangé
- `app/api/v1/quitus.py` — génération PDF inchangée

---

## Annexe A — Estimation de scope par sprint

| Sprint | Scope | Composants |
|--------|-------|------------|
| **S1** (P0) | DB migration + paywall + onboarding + route structure | Migration 008, (app) layout, onboarding wizard, nested routes skeleton |
| **S2** (P0) | Dashboard 4 blocs + sidebar V2 | Dashboard endpoints, 4 composants blocs, AppSidebarV2 |
| **S3** (P0) | Fiche Bien (sections A + C) + nested API | GET fiche bien, identité + loyers sections |
| **S4** (P1) | Bail + locataires + colocation | baux CRUD, bail_locataires, fiche bien section B |
| **S5** (P1) | Charges + PNO + frais agence + permissions | Sections D, RoleGate, RLS gérant-only |
| **S6** (P1) | Notifications email + preferences | Cron jobs, email triggers, settings UI |
| **S7** (P2) | Documents + Finances + Rentabilité | Upload, finances dashboard, section E |
| **S8** | Cleanup anciennes routes + tests E2E | Supprimer flat routes, Playwright tests |

---

## Annexe B — Risques et mitigations

| Risque | Impact | Mitigation |
|--------|--------|------------|
| Migration données locataires→baux perd des données | Haut | Script SQL testé en staging d'abord, backup complet avant |
| RLS gérant-only casse les opérations existantes | Haut | Déployer RLS en dernier, après backend + frontend prêts |
| Paywall bloque les users existants | Moyen | Migration: `onboarding_completed = true` pour users actifs |
| Performance endpoints nested (N+1) | Moyen | Fiche bien = 1 query agrégée, pas N sous-queries |
| Rétrocompatibilité API flat endpoints | Bas | Garder les anciens endpoints pendant 1 sprint de transition |
