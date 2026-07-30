# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

GererSCI est une application SaaS pour la gestion de SCI (Sociétés Civiles Immobilières) en France. L'application suit une architecture full-stack moderne avec:

- **Frontend**: SvelteKit 2.x + **Svelte 5** (runes: `$state`, `$derived`, `$props`, `$effect`) + TypeScript + Tailwind CSS 4
- **Backend**: FastAPI (Python 3.12) avec architecture en couches
- **Base de données**: Supabase (PostgreSQL) avec RLS (Row-Level Security)
- **Paiements**: Stripe (abonnements + lifetime deals)
- **Emails**: Resend pour les emails transactionnels et magic links
- **Analytics**: Plausible, hébergé hors de ce dépôt (`/home/ubuntu/infra/services/plausible/`). Les services `matomo` et `uptime-kuma` du compose sont en `profiles: ["disabled"]` et ne tournent pas.
- **Infrastructure**: Docker Compose + **Caddy** en reverse proxy (service systemd sur le VPS, configuré dans le dépôt `vps-infra` — PAS dans ce repo). `docker/nginx.conf` est du **code mort**, ne pas s'y fier.

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
uvicorn app.main:app --reload --port 8001          # Serveur de développement
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
├── api/v1/              # API routers (34 modules)
│   ├── auth.py          # Login, magic links, JWT refresh
│   ├── scis_biens.py    # Nested CRUD: /scis/{id}/biens/{id}/baux, loyers, charges, documents...
│   ├── scis.py          # SCI listing + creation
│   ├── dashboard.py     # KPIs, alertes, activité récente
│   ├── finances.py      # Vue financière consolidée
│   ├── onboarding.py    # Wizard onboarding multi-étapes
│   ├── admin.py         # Admin panel (users, stats) — requires is_admin flag
│   ├── demo.py          # Seed/cleanup demo data (rate-limited 10/hour)
│   ├── credits.py       # CRUD crédits immobiliers + amortissement
│   ├── bilans.py        # Bilans mensuels (entrées/sorties/solde)
│   ├── calendrier_fiscal.py  # Calendrier fiscal dynamique
│   ├── echeances.py     # Échéances (baux, PNO, charges)
│   ├── sci_lifecycle.py # Dissolution, changement gérant, capital
│   ├── leads.py         # Lead capture (email + UTM)
│   ├── comptabilite.py  # Comptabilité simplifiée
│   ├── stripe.py        # Checkout, webhooks (idempotent), portail
│   ├── quitus.py        # Quittances PDF + envoi email
│   ├── cerfa.py         # Génération CERFA 2044
│   ├── assemblees_generales.py  # Registre AG + PV
│   ├── mouvements_parts.py      # Cessions/transmissions de parts
│   ├── import_csv.py    # Import CSV (biens + loyers)
│   ├── gdpr.py          # Export données + suppression compte (cascade safe)
│   ├── health.py        # Health check endpoint
│   └── ...              # associes, biens, charges, export, files, fiscalite, loyers, locataires, notifications, notification_preferences
├── core/
│   ├── config.py        # Settings (Pydantic BaseSettings)
│   ├── security.py      # JWT verification, get_current_user, get_admin_user
│   ├── paywall.py       # check_write_access, require_active_subscription, require_gerant_role
│   ├── entitlements.py  # Feature limits par plan (max biens, max SCI, etc.)
│   ├── rate_limit.py    # slowapi rate limiting
│   ├── supabase_client.py  # Client Supabase factory
│   ├── audit_log.py     # Audit trail
│   └── logging_config.py   # Sentry + structured logging
├── models/              # Modèles de données (placeholders, data vient de Supabase)
├── schemas/             # Pydantic schemas (baux, fiche_bien, documents, assurance_pno, frais_agence, credit_immobilier, etc.)
└── services/
    ├── dashboard_service.py     # Agrégation KPIs multi-SCI
    ├── finances_service.py      # Calculs financiers consolidés
    ├── demo_service.py          # Seed demo data (1 SCI, 2 biens, baux, loyers, charges)
    ├── credit_service.py        # Amortissement crédit (formule française)
    ├── bilan_mensuel_service.py # Bilans mensuels (lignes, KPIs, totaux)
    ├── regularisation_service.py # Régularisation charges annuelle
    ├── notification_service.py  # Création/envoi notifications
    ├── notification_cron.py     # Cron: loyers impayés, baux expirants, PNO
    ├── signup_nurture_service.py # Nurture emails post-inscription (J1, J3, J7)
    ├── rentabilite_service.py   # Calculs rentabilité brute/nette/cashflow
    ├── subscription_service.py  # Gestion abonnements Stripe
    ├── quitus_service.py        # PDF quittances (ReportLab)
    ├── storage_service.py       # Upload documents (Supabase Storage)
    ├── admin_metrics_service.py # KPIs admin (funnel, alertes, actions)
    ├── associe_linking.py       # Auto-link associés par email
    ├── document_links.py        # URLs signées documents
    └── ...                      # auth, email, biens, loyers, sci, comptabilite, echeances, obligations
```

**Points importants**:
- **Auth**: Supabase Auth + JWT vérifié dans `core.security`. Admin via `get_admin_user()`
- **RLS**: Toutes les requêtes DB passent par Supabase client avec JWT utilisateur. Writes via `_get_write_client()` (service role), reads via `_get_client(request)` (user JWT)
- **Paywall**: `write_protection_middleware` (main.py) + `require_active_subscription` / `require_gerant_role` / `SubscriptionService.enforce_limit`. ⚠️ Le décorateur `@require_plan` **n'existe pas** (erreur de doc historique)
- **Nested Routes API**: `scis_biens.py` est le plus gros module (~1000 lignes) avec routes `/scis/{sci_id}/biens/{bien_id}/[baux|loyers|charges|documents|assurance-pno|frais-agence]`
- **Rate Limiting**: slowapi avec limites par endpoint (voir `core.rate_limit`)
- **PDF Generation**: ReportLab pour quittances + CERFA 2044 + résumé fiscal
- **File Upload**: Supabase Storage pour documents
- **Cron Jobs**: notification_cron (loyers/baux/PNO), signup_nurture (emails J1/J3/J7)

### Frontend Structure
```
frontend/src/
├── lib/
│   ├── components/
│   │   ├── AppNavbar.svelte       # Navigation principale (4 items: Dashboard, Mes SCI, Finances, Pilotage ▾)
│   │   ├── DemoBanner.svelte      # Bandeau demo persistant (amber, non-dismissable)
│   │   ├── DemoConversionPrompt.svelte  # Toast conversion sur actions haute valeur
│   │   ├── LockedAction.svelte    # Lock badge + intercept pour users demo
│   │   ├── UpgradePrompt.svelte   # Modale upgrade ("Fonctionnalité réservée aux abonnés")
│   │   ├── CheckoutConfirmModal.svelte  # Recap plan + consent L221-28 avant Stripe
│   │   ├── Celebration.svelte     # Animations milestone (checkmark, badge, confetti)
│   │   ├── AppDemoVideo.svelte    # Vidéo démo interactive (6 scènes, annotations séquentielles)
│   │   ├── EmailCapture.svelte    # Capture email RGPD (lead magnets)
│   │   ├── FieldHint.svelte       # Tooltips contextuels ⓘ pour champs formulaire
│   │   ├── RoleGate.svelte        # Contrôle d'accès par rôle (gérant vs associé)
│   │   ├── NotificationCenter.svelte
│   │   ├── CommandPalette.svelte
│   │   ├── dashboard/             # DashboardKpis, DashboardAlerts, DashboardSciCards, DashboardActivity
│   │   ├── fiche-bien/            # 10 onglets: Header, Identite, Bail, Loyers, Charges, PNO, Agence, Credit, Rentabilite, Documents, Evenements
│   │   ├── charts/                # Composants graphiques
│   │   └── ui/                    # Primitives UI réutilisables
│   ├── high-value/     # Modules métier critiques (≥90% test coverage requis)
│   ├── stores/         # Svelte stores (sci-context, sidebar, theme, notifications, connectivity, breadcrumb-names)
│   ├── auth/           # route-guard.ts, session.ts
│   ├── api/            # Client API modulaire (client.ts, types.ts, + modules par domaine)
│   ├── analytics.ts    # Umami tracking (40+ events)
│   ├── config/         # plans.ts (shared pricing config)
│   ├── supabase.ts     # Client Supabase
│   └── stripe.ts       # Client Stripe
└── routes/
    ├── (app)/                          # Route group auth-gated (layout vérifie session + demo banner)
    │   ├── dashboard/+page.svelte      # Tableau de bord multi-SCI
    │   ├── scis/+page.svelte           # Liste des SCI
    │   ├── scis/[sciId]/               # Contexte SCI
    │   │   ├── +page.svelte            # Vue SCI détaillée
    │   │   ├── biens/+page.svelte      # Biens de la SCI
    │   │   ├── biens/[bienId]/+page.svelte   # Fiche bien (10 onglets)
    │   │   ├── biens/[bienId]/baux/    # Gestion des baux
    │   │   ├── associes/               # Associés de la SCI
    │   │   ├── fiscalite/              # Fiscalité annuelle
    │   │   ├── assemblees-generales/   # Registre AG + PV
    │   │   ├── mouvements-parts/       # Cessions de parts
    │   │   └── documents/              # GED par SCI
    │   ├── finances/                   # Vue financière consolidée
    │   ├── bilans/                     # Bilans mensuels
    │   ├── echeances/                  # Échéances (baux, PNO, charges)
    │   ├── exploitation/               # Vue exploitation
    │   ├── onboarding/                 # Wizard onboarding (4 étapes + value preview)
    │   ├── settings/                   # Préférences + notifications
    │   └── account/                    # Profil + privacy
    ├── welcome/            # Écran chargement crédibilité (seed demo data, 4 étapes animées)
    ├── register/           # Inscription (message Hormozi si ?plan= présent)
    ├── admin/              # Panel admin (HORS (app), secret-key auth)
    ├── login/              # Auth entry (magic link)
    ├── pricing/            # Plans & checkout Stripe (CheckoutConfirmModal pour users connectés)
    ├── generateur-quittance/   # Lead magnet SEO (quittance PDF gratuite + email capture)
    ├── simulateur-cerfa/       # Lead magnet SEO (simulateur CERFA 2044 + email capture)
    ├── simulateur-plus-value/  # Lead magnet SEO (calcul plus-value)
    ├── calendrier-fiscal/      # Calendrier fiscal public
    ├── cgu/ cgv/ mentions-legales/ confidentialite/  # Pages légales
    └── +layout.svelte      # Root layout (Supabase listener, theme, cookie consent, View Transitions API)
```

**Points importants**:
- **Route Group `(app)/`**: Layout auth-gated. Si pas de session → `/login`. Si pas d'abonnement actif et pas de demo → `/welcome`. Si demo_seeded → laisse passer (DemoBanner gère les restrictions)
- **Demo-First Flow**: Register → `/welcome` (seed demo) → `/dashboard` avec données fictives → actions write verrouillées (LockedAction) → conversion via DemoBanner/UpgradePrompt/DemoConversionPrompt
- **Nested SCI Context**: `scis/[sciId]/+layout.ts` charge le contexte SCI et le passe aux sous-routes via `sci-context` store
- **API Client**: `$lib/api/client.ts` — en dev `API_URL=''` (passe par Vite proxy), en prod utilise `VITE_API_URL`
- **Dark Mode**: Supporté via Tailwind `dark:` classes
- **Svelte 5 Runes**: Utilise `$state`, `$derived`, `$props`, `$effect`, `Snippet` — PAS les anciennes syntaxes (`export let`, `$:`, stores réactifs)

### Database (Supabase)
Le schéma SQL est dans `supabase/migrations/` (46 fichiers, `001_init` → `043_security_fix_c1_c3_rls`). ⚠️ L'ordre lexicographique est cassé : `0045_`/`0046_` trient **avant** `004_`, et le préfixe `035` est dupliqué (cf. AUDIT HIGH-11). Tables principales:
- `sci` → Sociétés civiles immobilières
- `associes` → Associés liés aux SCI (RLS par user_id, rôle: gérant/associé)
- `biens` → Biens immobiliers (+ `is_demo` flag)
- `baux` → Baux locatifs (date_debut, date_fin, loyer_hc, charges_provisions, etat_lieux_date/notes/document_url)
- `locataires` → Locataires liés aux baux (relation many-to-many via `bail_locataires`)
- `loyers` → Enregistrements de loyers mensuels
- `charges` → Charges liées aux biens (copropriété, taxe foncière, etc.)
- `assurances_pno` → Assurances propriétaire non-occupant (noter: pluriel)
- `frais_agence` → Frais de gestion agence
- `credits_immobiliers` → Crédits immobiliers (banque, taux, durée, mensualité)
- `regularisations_charges` → Régularisation charges annuelle (provisions vs réel)
- `documents` → GED (fichiers uploadés par bien/SCI)
- `fiscalite` → Données fiscales annuelles
- `evenements_bien` → Événements bien (sinistre, travaux, etc.)
- `lead_captures` → Leads email + UTM (rate-limited 10/min)
- `notifications` → Notifications in-app (loyer impayé, bail expirant, etc.)
- `notification_preferences` → Préférences email/in-app par type et par user
- `subscriptions` → Abonnements Stripe (plan, status, dates, demo_seeded, guarantee_expires_at)
- `stripe_webhook_events` → Idempotency (event_id unique)

**RLS est activé sur toutes les tables**. Les policies filtrent via `associes.user_id`. La migration `006` corrige la récursion RLS sur `associes`. Plusieurs tables supportent `is_demo` flag (migration `025`) pour les données de démonstration.

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
VITE_API_URL=http://localhost:8001  # En dev, préférer API_URL='' avec Vite proxy
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

### Demo-First Flow (modèle "Full Steak")
1. Visiteur anonyme clique plan sur `/pricing` → redirect `/register?plan=<key>` (pas de modale)
2. User s'inscrit sur `/register` (message Hormozi si `?plan=` présent)
3. Redirect `/welcome` → écran crédibilité (4 étapes animées) + `POST /api/v1/demo/seed`
4. Redirect `/dashboard` → données demo pré-remplies (1 SCI, 2 biens, baux, loyers, charges)
5. User explore librement — actions write verrouillées par `LockedAction.svelte`
6. Triggers de conversion : `DemoConversionPrompt` sur quittance/bilan/fiscalité, `DemoBanner` persistant
7. Clic "Souscrire" → `/pricing` → `CheckoutConfirmModal` (consent L221-28) → Stripe checkout
8. Webhook `checkout.session.completed` → cleanup demo data + activation abonnement

### Payment Flow (Stripe)
1. User connecté sélectionne plan sur `/pricing` → `CheckoutConfirmModal` (recap plan + consent L221-28)
2. Confirm → `POST /api/v1/stripe/create-checkout` → redirect Stripe
3. Stripe redirige vers URL de succès
4. Webhook Stripe notifie backend (idempotent via `stripe_webhook_events`) → mise à jour abonnement + cleanup demo

### Document Generation
1. Backend génère PDF via ReportLab (quittances, CERFA 2044, résumé fiscal)
2. Upload sur Supabase Storage
3. Retourne URL signée avec expiration

### ⚠️ Invariants de sécurité (audit externe 2026-07-25 — NE PAS CASSER)

Ces règles corrigent des vulnérabilités **critiques vérifiées en production**.
Voir `AUDIT_EXTERNE_2026-07-25.md` et `BACKLOG.md`.

1. **`subscriptions` n'est JAMAIS écrite par le client utilisateur.** Migration
   `043` supprime les policies d'écriture user. Toute écriture passe par
   `get_supabase_service_client()`. Sinon : un utilisateur s'auto-attribue un
   plan payant illimité (exploit reproduit en prod, finding C1).
2. **Le catalogue serveur prime sur la ligne DB** :
   `row = {**row, **snapshot}` dans `subscription_service.py`. Ne jamais
   réinverser — la ligne DB imposerait ses propres quotas.
3. **La gestion des associés est réservée aux rôles de gouvernance**
   (`gerant`, `co_gerant`) via `_require_gerant()` sur POST/PATCH/DELETE. La
   simple appartenance à la SCI ne suffit pas, sinon un associé se promeut
   gérant (finding C3).
4. **`user_id` et `role` fournis par le client sont ignorés/contraints** à la
   création d'un associé. Le rattachement d'un compte passe par l'invitation
   email (`associe_linking`).
5. **Rôles associés : 4 valeurs** — `gerant`, `co_gerant`, `associe`,
   `usufruitier` (cf. `frontend/src/lib/high-value/associes.ts` et contrainte
   `associes_role_check`). Restreindre ce référentiel casse la migration et
   prive les co-gérants de leurs droits.
6. **Supabase est exposé publiquement** (`/rest/`, `/auth/` sur
   `api.gerersci.fr`) : **RLS est la seule frontière de sécurité réelle**. Tout
   contrôle purement applicatif est contournable par appel direct à PostgREST.
   Toute nouvelle table DOIT avoir RLS activé et des policies explicites.
   Fermeture de cette exposition à faire dans `vps-infra` (finding C2).

### Paywall / Plan Gating
1. `core.entitlements` définit les limites par plan (max biens, max SCI, features)
2. `write_protection_middleware` (402 sur les writes sans abonnement actif) + `require_active_subscription` / `require_gerant_role` sur les endpoints protégés
3. Frontend : `LockedAction` verrouille les writes en demo, `UpgradePrompt` pour les features payantes
4. Plans: `free` (bloqué, is_active=false) → `starter` (Gestion, 19€/mois) → `pro` (Pilotage, 39€/mois) → `lifetime` (Fondateur, 990€)
5. **ACTIVE_SUBSCRIPTION_STATUSES**: `{"active", "paid"}` uniquement — pas de trial
6. Garantie 30 jours remboursement (art. L221-28, clause en CGV)

### Onboarding Flow
1. `/onboarding` wizard 4 étapes (créer SCI → ajouter bien → créer bail → value preview avec KPI cards)
2. Backend track progression via `/api/v1/onboarding` (status + complete)
3. Confetti sur clic bouton "Terminer" (pas avant — délai 3s pour ne pas masquer le tour)

## Common Gotchas

1. **PYTHONPATH**: Toujours lancer pytest avec `PYTHONPATH=. pytest` depuis `backend/`, sinon les imports échouent.
2. **CORS**: Le backend utilise CORS middleware. Ajuster `CORS_ORIGINS` dans `.env` si problèmes.
3. **RLS**: Les requêtes DB doivent toujours passer par le client Supabase avec JWT. Ne pas utiliser de connexion directe PostgreSQL pour les requêtes utilisateur.
4. **RLS Recursion**: La migration `006` corrige un bug de récursion infinie sur les policies `associes`. Ne pas réécrire ces policies sans vérifier.
5. **Tailwind 4**: Utilise `@tailwindcss/vite` (pas PostCSS). La config est dans `tailwind.config.js`.
6. **Pnpm**: Le frontend utilise `pnpm`, pas `npm`. Toujours utiliser `pnpm install`.
7. **Test Coverage**: Les modules dans `frontend/src/lib/high-value/` doivent maintenir ≥90% de couverture.
8. **Paywall**: Il n'y a PAS de décorateur `@require_plan`. Le gating réel = `write_protection_middleware` (main.py) + `require_active_subscription` / `require_gerant_role` + `SubscriptionService.enforce_limit`. Tester avec un user ayant un plan actif, ou mocker `_load_subscription_row`.
9. **Nested Routes**: Les routes frontend `(app)/scis/[sciId]/...` dépendent du layout `[sciId]/+layout.ts` qui charge le contexte SCI. Toujours vérifier que `sciId` est propagé.
10. **Navigation**: `AppSidebarV2.svelte` est supprimé. La navigation est `AppNavbar.svelte` (4 items: Tableau de bord, Mes SCI ▾, Finances, Pilotage ▾).
11. **Admin**: Le dashboard admin est à `/admin?secret=ADMIN_SECRET_KEY`. Pas de login requis — protégé par secret URL. Route hors du groupe `(app)` et dans `PUBLIC_ROUTE_PREFIXES`.
12. **Subscriptions table**: La colonne `plan_key` **existe** (ajoutée en `0045_subscription_entitlements.sql`). Résoudre en priorité via `stripe_price_id` + `resolve_plan_key_from_price_id()`, avec fallback sur `plan_key`. ⚠️ Ne pas supprimer ce fallback tant que `stripe_price_id` n'est pas renseigné au checkout (audit HIGH-10) : cela rétrograderait tous les clients payants en `free`.
13. **VPS git**: Ne jamais faire `sudo git pull` sur le VPS — casse les permissions `.git/objects` pour l'auto-deploy CI. Utiliser `git pull` sans sudo.
14. **Proxy /api**: Le reverse proxy est **Caddy** (systemd, dépôt `vps-infra`), pas nginx. Il route `/api/` vers le backend — nécessaire pour les appels API depuis les pages publiques (admin). Toute modif du bord public (TLS, headers, rate-limit) se fait dans `vps-infra`, hors CI de ce repo.
15. **Emplacements de production** : voir la section « Production Infrastructure & Deployment Standard (vps-infra) » en fin de fichier. Rien de tout cela n'est géré ici — ne jamais réintroduire de sauvegarde, de configuration proxy ou de chemin de déploiement dans ce dépôt.
16. **Supabase de production = stack de la CLI**. Les conteneurs s'appellent `supabase_*_sci-manager-renew` (convention `supabase start`, aucun label docker-compose). Conséquences : `supabase_studio` et `supabase_inbucket` tournent en production, et **il n'y a aucun conteneur `realtime` pour gerersci** alors que Caddy route `/realtime/*` vers Kong. Ne pas supposer un déploiement Supabase self-hosted classique.
17. **Analytics** : Matomo et Uptime Kuma sont en `profiles: ["disabled"]` dans le compose et ne tournent pas. L'analytics réel du VPS est Plausible (`/home/ubuntu/infra/services/plausible/`), hors de ce dépôt.
15. **SUPABASE_PUBLIC_URL**: Configuré dans `.env` production pour réécrire les magic links de `host.docker.internal:54321` vers `api.gerersci.fr`.
16. **Vite Proxy**: En dev, `API_URL=''` dans `client.ts` fait passer les appels API par le proxy Vite (port 8001). Évite les problèmes CORS. Configuré dans `vite.config.ts`.
17. **assurances_pno**: Le nom de table est au **pluriel** (`assurances_pno`), pas `assurance_pno`. Colonnes: `compagnie` (pas `assureur`), `montant_annuel` (pas `prime_annuelle`), `date_echeance` (pas `date_fin`).
18. **Demo data**: Les tables avec `is_demo=true` sont nettoyées au checkout. Ne jamais hardcoder `siren` dans les données demo (contrainte unique).
19. **Svelte 5**: Ne PAS utiliser `export let` (Svelte 4). Utiliser `let { prop } = $props()`. Ne PAS utiliser `$:` réactif. Utiliser `$derived()` et `$effect()`.
20. **get_current_user()**: Retourne un `str` (user_id), PAS un dict. Ne pas faire `user["sub"]`.

## Business Context

Ce projet suit une approche produit/marketing avec:
- **Target**: Gérants de SCI indépendants, cabinets comptables, opérateurs patrimoniaux
- **Value Prop**: Passer du tableur bricolé au cockpit SCI professionnel
- **Pricing**: Gestion (19€/mois, 10 biens) + Pilotage (39€/mois, illimité) + Fondateur (990€ lifetime) — pas de free tier, pas de trial
- **Modèle**: Demo-first ("Full Steak") — l'utilisateur explore des données fictives avant de payer
- **North Star Metric**: Nombre de SCI actives avec ≥1 loyer enregistré sur 30 jours

Documentation business complète dans `/docs/` (functional requirements, GTM strategy, audit Big4).

### Lead Magnets (SEO)
- `/generateur-quittance` — Génération quittance PDF gratuite (email gate avant CTA)
- `/simulateur-cerfa` — Simulateur CERFA 2044 (email capture)
- `/simulateur-plus-value` — Calculateur plus-value immobilière
- `/calendrier-fiscal` — Calendrier fiscal dynamique

## Expert Agents Team

Voir `docs/AGENTS.md` pour la liste complète. Combinaisons principales :

```
Fiscalité/CERFA    → Legal Compliance Checker + Finance Tracker + backend-architect
Nouvelle feature   → Product Manager + Software Architect + quality-engineer
Sécurité/Auth      → security-engineer + backend-architect + Code Reviewer
Dashboard/KPIs     → Analytics Reporter + Finance Tracker + frontend-architect
Infra/Deploy       → devops-architect + security-engineer
Refactoring        → Software Architect + Code Reviewer + quality-engineer
```

## Production Infrastructure & Deployment Standard (vps-infra)

- **Canonical Path on VPS**: `/opt/vps-infra/services/gerersci/` (symlinked to `/opt/gerersci` for 100% path parity).
- **Reverse Proxy**: Managed host-wide by Caddy in `/etc/caddy/sites/gerersci.caddy` (versioned in `radnou/vps-infra`).
  - `app.gerersci.fr`, `gerersci.fr` -> Frontend (`127.0.0.1:14173`)
  - `api.gerersci.fr` -> Backend (`127.0.0.1:18000`) & Supabase Kong (`127.0.0.1:54321`)
- **Production Database**: Supabase stack (`supabase_db_sci-manager-renew`), running PostgreSQL 17.
- **Nightly Backups & Restoration**: Managed centrally by `vps-infra/scripts/backup.sh` (03:00 UTC daily) and `vps-infra/scripts/restore.sh gerersci`.
- **Status Dashboard**: Live container logs and status visible at `https://status.radnoumane.com` (Dozzle).
