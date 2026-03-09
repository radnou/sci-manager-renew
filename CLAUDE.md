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
pip install -r requirements.txt    # Installer les dépendances
uvicorn app.main:app --reload --port 8000   # Serveur de développement
pytest                              # Lancer les tests
pytest tests/test_specific.py::test_name   # Lancer un test spécifique
pytest --cov=app --cov-report=term-missing  # Tests avec couverture
bandit -r app                       # Scan de sécurité
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
├── api/v1/          # API routers (auth, biens, loyers, stripe, etc.)
├── core/            # Configuration, sécurité, rate limiting
├── models/          # Modèles de données (placeholders, data vient de Supabase)
├── schemas/         # Pydantic schemas pour validation
└── services/        # Business logic (auth, email, storage, PDF generation)
```

**Points importants**:
- **Authentification**: Supabase Auth avec JWT. Les tokens sont vérifiés dans `app.core.security`
- **RLS**: Toutes les requêtes DB utilisent le contexte utilisateur via Supabase RLS
- **Rate Limiting**: slowapi avec limites par endpoint (voir `app.core.rate_limit`)
- **PDF Generation**: ReportLab pour les quittances de loyer (voir `services/quitus_service.py`)
- **File Upload**: Supabase Storage pour les documents (voir `services/storage_service.py`)

### Frontend Structure
```
frontend/src/
├── lib/
│   ├── components/     # Composants Svelte réutilisables
│   ├── high-value/     # Modules métier critiques (≥90% test coverage)
│   ├── stores/         # Svelte stores pour état global
│   ├── api.ts          # Client API pour communiquer avec backend
│   ├── supabase.ts     # Client Supabase
│   └── stripe.ts       # Client Stripe
└── routes/             # Pages SvelteKit (file-based routing)
```

**Points importants**:
- **SSR**: SvelteKit avec SSR activé par défaut. Utiliser `+page.server.ts` pour data loading côté serveur
- **Auth Flow**: Magic link via Resend → Supabase Auth → JWT stocké dans session
- **API Calls**: Utiliser `$lib/api.ts` qui gère automatiquement les headers et tokens
- **Dark Mode**: Supporté via Tailwind dark: classes
- **i18n**: Paraglide-JS (structure dans `messages/`)

### Database (Supabase)
Le schéma SQL est dans `supabase/migrations/`. Tables principales:
- `sci` → Sociétés civiles immobilières
- `associes` → Associés liés aux SCI (RLS par user_id)
- `biens` → Biens immobiliers
- `locataires` → Locataires liés aux biens
- `loyers` → Enregistrements de loyers mensuels
- `charges` → Charges liées aux biens
- `fiscalite` → Données fiscales annuelles

**RLS est activé sur toutes les tables**. Les policies filtrent automatiquement selon `associes.user_id`.

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
VITE_STRIPE_STARTER_PRICE_ID=
VITE_STRIPE_PRO_PRICE_ID=
VITE_STRIPE_LIFETIME_PRICE_ID=
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

## Common Gotchas

1. **CORS**: Le backend utilise CORS middleware. Ajuster `CORS_ORIGINS` dans `.env` si problèmes.
2. **RLS**: Les requêtes DB doivent toujours passer par le client Supabase avec JWT. Ne pas utiliser de connexion directe PostgreSQL pour les requêtes utilisateur.
3. **Tailwind 4**: Utilise `@tailwindcss/vite` (pas PostCSS). La config est dans `tailwind.config.js`.
4. **Pnpm**: Le frontend utilise `pnpm`, pas `npm`. Toujours utiliser `pnpm install`.
5. **Test Coverage**: Les modules dans `frontend/src/lib/high-value/` doivent maintenir ≥90% de couverture.

## Business Context

Ce projet suit une approche produit/marketing avec:
- **Target**: Gérants de SCI indépendants, cabinets comptables, opérateurs patrimoniaux
- **Value Prop**: Passer du tableur bricolé au cockpit SCI professionnel
- **Pricing**: Freemium (Standard jusqu'à 5 biens) + Pro (multi-biens illimités) + Lifetime deal
- **North Star Metric**: Nombre de SCI actives avec ≥1 loyer enregistré sur 30 jours

Documentation business complète dans `/docs/` (functional requirements, GTM strategy, audit Big4).
