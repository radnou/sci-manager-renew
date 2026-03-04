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
