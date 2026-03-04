# sci-manager-renew

MicroSaaS de gestion SCI + parc immobilier locatif (phase 1/6 en cours).

## Prérequis
- Docker & docker-compose
- Node.js 24+, pnpm/npm
- Python 3.12+

## MCP installés

MCP pertinents pour ce projet (installés globalement le 2026-03-04):
- `@playwright/mcp@0.0.68` (tests E2E / navigation)
- `@sveltejs/mcp@0.1.20` (documentation et aide Svelte)
- `@supabase/mcp-server-supabase@0.7.0` (base Supabase)
- `@upstash/context7-mcp@2.1.3` (documentation technique)

Commande d'installation:
```bash
npm install -g @playwright/mcp@0.0.68 @sveltejs/mcp@0.1.20 @supabase/mcp-server-supabase@0.7.0 @upstash/context7-mcp@2.1.3
```

Configuration du workspace VS Code:
- fichier: `.vscode/mcp.json`
- serveurs conservés: `context7`, `playwright`, `supabase`, `svelte`, `stripe`
- suppression des serveurs non nécessaires au stack Svelte/Supabase

Variables/inputs MCP à renseigner au premier usage:
- `CONTEXT7_API_KEY`
- `SUPABASE_ACCESS_TOKEN`
- `project-ref`
- `read-only`
- `features`
- `api-url`

## Démarrage rapide
```bash
# lever la base Supabase locale
docker-compose up -d

# configurer les variables d'environnement (copier et éditer le fichier voisin)
cp .env.example .env
# puis remplir SUPABASE_URL, SUPABASE_ANON_KEY et/ou SUPABASE_SERVICE_ROLE_KEY
# ainsi que les clés Stripe

# lancer le backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8001

# lancer le frontend
cd frontend && pnpm install && pnpm run dev -- --port 5173
```

L'API est accessible sur `http://localhost:8001`, le frontend sur `http://localhost:5173`.

## Structure
Voir `.github/copilot-instructions.md` pour l'architecture et le workflow.
