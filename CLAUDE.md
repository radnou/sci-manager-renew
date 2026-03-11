# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GererSCI est une application SaaS pour la gestion de SCI (Sociétés Civiles Immobilières) en France. L'application suit une architecture full-stack moderne avec:

- **Frontend**: SvelteKit 2.x + TypeScript + Tailwind CSS 4
- **Backend**: FastAPI (Python 3.12) avec architecture en couches
- **Base de données**: Supabase (PostgreSQL) avec RLS (Row-Level Security)
- **Paiements**: Stripe (abonnements + lifetime deals)
- **Emails**: Resend pour les emails transactionnels et magic links
- **Infrastructure**: Docker Compose (nginx reverse proxy + services)

## Development Commands

### Frontend (SvelteKit)
```bash
cd frontend
pnpm install                    # Installer les dépendances
pnpm run dev                    # Serveur de développement (port 5173)
pnpm run check                  # Vérification TypeScript + Svelte
pnpm run lint                   # ESLint
pnpm run format                 # Prettier
pnpm run test:unit              # Tests unitaires Vitest
pnpm run test:high-value        # Tests avec couverture ≥90%
pnpm run test:e2e               # Tests E2E Playwright
pnpm run storybook              # Storybook (port 6006)
pnpm run build                  # Build de production
```

### Backend (FastAPI)
```bash
cd backend
pip install -r requirements.txt                    # Installer les dépendances
uvicorn app.main:app --reload --port 8000          # Serveur de développement
PYTHONPATH=. pytest                                # Lancer les tests
PYTHONPATH=. pytest tests/test_specific.py::test_name  # Test spécifique
PYTHONPATH=. pytest --cov=app --cov-report=term-missing  # Tests + couverture
bandit -r app                                      # Scan de sécurité
```

### Docker (Production-like)
```bash
docker compose up -d                # Démarrer tous les services
docker compose down                 # Arrêter tous les services
docker compose logs backend         # Logs du backend
docker compose logs frontend        # Logs du frontend
docker compose ps                   # Status des services
docker compose exec backend bash    # Shell dans le backend
```

### Deployment
```bash
./deploy.sh                         # Déploiement automatique sur VPS
```

## Architecture Notes

### Backend Structure
```
backend/app/
├── api/v1/              # API routers
│   ├── auth.py          # Login, magic links, JWT refresh
│   ├── scis_biens.py    # Nested CRUD: /scis/{id}/biens/{id}/baux, loyers, charges, documents...
│   ├── scis.py          # SCI listing + creation
│   ├── dashboard.py     # KPIs, alertes, activité récente
│   ├── finances.py      # Vue financière consolidée
│   ├── onboarding.py    # Wizard onboarding multi-étapes
│   ├── admin.py         # Admin panel (users, stats) — requires is_admin flag
│   ├── notification_preferences.py  # Préférences email/in-app par type
│   ├── notifications.py # CRUD notifications + mark read
│   ├── stripe.py        # Checkout, webhooks, portail
│   ├── quitus.py        # Génération quittances PDF
│   ├── cerfa.py         # Génération CERFA 2044
│   └── ...              # associes, biens, charges, export, files, fiscalite, gdpr, loyers, locataires
├── core/
│   ├── config.py        # Settings (Pydantic BaseSettings)
│   ├── security.py      # JWT verification, get_current_user, get_admin_user
│   ├── paywall.py       # Plan gating decorator (@require_plan)
│   ├── entitlements.py  # Feature limits par plan (max biens, max SCI, etc.)
│   ├── rate_limit.py    # slowapi rate limiting
│   ├── supabase_client.py  # Client Supabase factory
│   ├── audit_log.py     # Audit trail
│   └── logging_config.py   # Sentry + structured logging
├── models/              # Modèles de données (placeholders, data vient de Supabase)
├── schemas/             # Pydantic schemas (baux, fiche_bien, documents, assurance_pno, frais_agence, etc.)
└── services/
    ├── dashboard_service.py     # Agrégation KPIs multi-SCI
    ├── finances_service.py      # Calculs financiers consolidés
    ├── notification_service.py  # Création/envoi notifications
    ├── notification_cron.py     # Cron: loyers impayés, baux expirants
    ├── rentabilite_service.py   # Calculs rentabilité brute/nette/cashflow
    ├── subscription_service.py  # Gestion abonnements Stripe
    ├── quitus_service.py        # PDF quittances (ReportLab)
    ├── storage_service.py       # Upload documents (Supabase Storage)
    └── ...                      # auth, email, biens, loyers, sci
```

**Points importants**:
- **Auth**: Supabase Auth + JWT vérifié dans `core.security`. Admin via `get_admin_user()`
- **RLS**: Toutes les requêtes DB passent par Supabase client avec JWT utilisateur
- **Paywall**: `@require_plan("pro")` decorator dans `core.paywall` — vérifie le plan avant accès
- **Nested Routes API**: `scis_biens.py` est le plus gros module (~1000 lignes) avec routes `/scis/{sci_id}/biens/{bien_id}/[baux|loyers|charges|documents|assurance-pno|frais-agence]`
- **Rate Limiting**: slowapi avec limites par endpoint (voir `core.rate_limit`)
- **PDF Generation**: ReportLab pour quittances + CERFA 2044
- **File Upload**: Supabase Storage pour documents

### Frontend Structure
```
frontend/src/
├── lib/
│   ├── components/
│   │   ├── AppSidebarV2.svelte    # Navigation principale (SCI switcher + sections)
│   │   ├── RoleGate.svelte        # Contrôle d'accès par rôle (gérant vs associé)
│   │   ├── NotificationCenter.svelte
│   │   ├── CommandPalette.svelte
│   │   ├── dashboard/             # DashboardKpis, DashboardAlerts, DashboardSciCards, DashboardActivity
│   │   ├── fiche-bien/            # FicheBienHeader, Identite, Bail, Loyers, Charges, Documents, Rentabilite
│   │   ├── charts/                # Composants graphiques
│   │   └── ui/                    # Primitives UI réutilisables
│   ├── high-value/     # Modules métier critiques (≥90% test coverage requis)
│   │                   # associes, biens, charges, fiscalite, formatters, loyers, portfolio, presentation
│   ├── stores/         # Svelte stores (sci-context.ts pour SCI sélectionnée)
│   ├── auth/           # route-guard.ts (protection routes hors layout (app))
│   ├── api.ts          # Client API (~95% couvert, gère headers + tokens + erreurs)
│   ├── supabase.ts     # Client Supabase
│   ├── stripe.ts       # Client Stripe
│   └── matomo.ts       # Analytics Matomo
└── routes/
    ├── (app)/                          # Route group auth-gated (layout vérifie session)
    │   ├── dashboard/+page.svelte      # Tableau de bord multi-SCI
    │   ├── scis/+page.svelte           # Liste des SCI
    │   ├── scis/[sciId]/               # Contexte SCI
    │   │   ├── +page.svelte            # Vue SCI détaillée
    │   │   ├── biens/+page.svelte      # Biens de la SCI
    │   │   ├── biens/[bienId]/+page.svelte   # Fiche bien (7 onglets)
    │   │   ├── biens/[bienId]/baux/    # Gestion des baux
    │   │   ├── associes/               # Associés de la SCI
    │   │   ├── fiscalite/              # Fiscalité annuelle
    │   │   └── documents/              # GED par SCI
    │   ├── finances/                   # Vue financière consolidée
    │   ├── onboarding/                 # Wizard onboarding
    │   ├── admin/                      # Panel admin (is_admin required)
    │   ├── settings/                   # Préférences + notifications
    │   └── account/                    # Profil + privacy
    ├── login/            # Auth entry (magic link)
    ├── pricing/          # Plans & checkout Stripe
    └── +layout.svelte    # Root layout (Supabase listener, theme, cookie consent)
```

**Points importants**:
- **Route Group `(app)/`**: Layout auth-gated — redirige vers `/login` si pas de session. Les routes publiques (`/login`, `/pricing`, `/`) sont hors du groupe
- **Nested SCI Context**: `scis/[sciId]/+layout.ts` charge le contexte SCI et le passe aux sous-routes via `sci-context` store
- **API Calls**: `$lib/api.ts` gère headers, tokens, et expose des fonctions typées par domaine (fetchSciBiens, createBail, etc.)
- **Dark Mode**: Supporté via Tailwind `dark:` classes
- **i18n**: Paraglide-JS (structure dans `messages/`)

### Database (Supabase)
Le schéma SQL est dans `supabase/migrations/` (9 fichiers, `001_init` → `008_ux_redesign_v2`). Tables principales:
- `sci` → Sociétés civiles immobilières
- `associes` → Associés liés aux SCI (RLS par user_id, rôle: gérant/associé)
- `biens` → Biens immobiliers
- `baux` → Baux locatifs (date_debut, date_fin, loyer_hc, charges_provisions)
- `locataires` → Locataires liés aux baux (relation many-to-many via `bail_locataires`)
- `loyers` → Enregistrements de loyers mensuels
- `charges` → Charges liées aux biens (copropriété, taxe foncière, etc.)
- `assurance_pno` → Assurances propriétaire non-occupant
- `frais_agence` → Frais de gestion agence
- `documents` → GED (fichiers uploadés par bien/SCI)
- `fiscalite` → Données fiscales annuelles
- `notifications` → Notifications in-app (loyer impayé, bail expirant, etc.)
- `notification_preferences` → Préférences email/in-app par type et par user
- `subscriptions` → Abonnements Stripe (plan, status, dates)

**RLS est activé sur toutes les tables**. Les policies filtrent via `associes.user_id`. La migration `006` corrige la récursion RLS sur `associes`.

## Environment Variables

### Backend (.env)
```bash
# Supabase
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
SUPABASE_JWT_SECRET=

# Stripe
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_STARTER_PRICE_ID=
STRIPE_PRO_PRICE_ID=
STRIPE_LIFETIME_PRICE_ID=

# Resend
RESEND_API_KEY=
RESEND_FROM_EMAIL=

# Database (Docker local)
DATABASE_URL=postgresql://...
```

### Frontend (.env)
```bash
VITE_API_URL=http://localhost:8000
VITE_SUPABASE_URL=
VITE_SUPABASE_ANON_KEY=
VITE_STRIPE_PUBLISHABLE_KEY=
PUBLIC_FEATURE_MULTI_SCI_DASHBOARD_V2=true
```

## Testing Strategy

### Frontend
- **Unit Tests**: Vitest avec `@vitest/browser-playwright` pour les tests DOM
- **High-Value Tests**: `test:high-value` applique un seuil de couverture ≥90% sur les modules critiques (`lib/high-value/`)
- **E2E Tests**: Playwright pour les parcours utilisateurs complets
- **Storybook**: Documentation interactive des composants UI

### Backend
- **pytest** avec fixtures pour isolation
- **pytest-asyncio** pour tests async
- **pytest-cov** pour couverture de code
- Tests de sécurité avec `bandit`

## Important Patterns

### Authentication Flow
1. User submits email on `/login`
2. Backend génère magic link via Supabase Auth
3. Resend envoie l'email avec le lien
4. User clique → Supabase Auth valide → JWT créé
5. Frontend stocke JWT et l'utilise pour toutes les API calls

### Payment Flow (Stripe)
1. User sélectionne plan sur `/pricing`
2. Frontend crée Checkout Session via `/api/v1/stripe/create-checkout`
3. Stripe redirige vers URL de succès
4. Webhook Stripe notifie backend → mise à jour du statut abonnement

### Document Generation
1. Backend génère PDF via ReportLab (quittances, CERFA 2044)
2. Upload sur Supabase Storage
3. Retourne URL signée avec expiration

### Paywall / Plan Gating
1. `core.entitlements` définit les limites par plan (max biens, max SCI, features)
2. `core.paywall.require_plan()` decorator sur les endpoints protégés
3. Frontend vérifie le plan via `subscription_service` et affiche upgrade prompt
4. Plans: `free` (Standard, ≤5 biens) → `starter` → `pro` (illimité) → `lifetime`

### Onboarding Flow
1. `/onboarding` wizard multi-étapes (créer SCI → ajouter bien → créer bail → configurer notifications)
2. Backend track progression via `/api/v1/onboarding` (status + complete)
3. Redirect automatique depuis dashboard si onboarding non complété

## Common Gotchas

1. **PYTHONPATH**: Toujours lancer pytest avec `PYTHONPATH=. pytest` depuis `backend/`, sinon les imports échouent.
2. **CORS**: Le backend utilise CORS middleware. Ajuster `CORS_ORIGINS` dans `.env` si problèmes.
3. **RLS**: Les requêtes DB doivent toujours passer par le client Supabase avec JWT. Ne pas utiliser de connexion directe PostgreSQL pour les requêtes utilisateur.
4. **RLS Recursion**: La migration `006` corrige un bug de récursion infinie sur les policies `associes`. Ne pas réécrire ces policies sans vérifier.
5. **Tailwind 4**: Utilise `@tailwindcss/vite` (pas PostCSS). La config est dans `tailwind.config.js`.
6. **Pnpm**: Le frontend utilise `pnpm`, pas `npm`. Toujours utiliser `pnpm install`.
7. **Test Coverage**: Les modules dans `frontend/src/lib/high-value/` doivent maintenir ≥90% de couverture.
8. **Paywall**: Les endpoints protégés utilisent `@require_plan("pro")`. Tester avec un user ayant un plan actif, ou mocker `get_subscription_status`.
9. **Nested Routes**: Les routes frontend `(app)/scis/[sciId]/...` dépendent du layout `[sciId]/+layout.ts` qui charge le contexte SCI. Toujours vérifier que `sciId` est propagé.
10. **AppSidebar**: L'ancien `AppSidebar.svelte` est supprimé. Utiliser uniquement `AppSidebarV2.svelte`.

## Business Context

Ce projet suit une approche produit/marketing avec:
- **Target**: Gérants de SCI indépendants, cabinets comptables, opérateurs patrimoniaux
- **Value Prop**: Passer du tableur bricolé au cockpit SCI professionnel
- **Pricing**: Freemium (Standard jusqu'à 5 biens) + Pro (multi-biens illimités) + Lifetime deal
- **North Star Metric**: Nombre de SCI actives avec ≥1 loyer enregistré sur 30 jours

Documentation business complète dans `/docs/` (functional requirements, GTM strategy, audit Big4).
