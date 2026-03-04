# sci-manager-renew

MicroSaaS de gestion SCI + parc immobilier locatif (phase 1/6 en cours).

## Prérequis
- Docker & docker-compose
- Node.js 24+, pnpm/npm
- Python 3.12+

## Démarrage rapide
```bash
# lever la base Supabase locale
docker-compose up -d

# lancer le backend
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8001

# lancer le frontend
cd frontend && pnpm install && pnpm run dev -- --port 5173
```

L'API est accessible sur `http://localhost:8001`, le frontend sur `http://localhost:5173`.

## Structure
Voir `.github/copilot-instructions.md` pour l'architecture et le workflow.
