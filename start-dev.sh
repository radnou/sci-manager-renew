#!/bin/bash
# ═══════════════════════════════════════════════════════
# GererSCI — Clean Build + Seed + Run (idempotent)
# Usage: ./start-dev.sh [--skip-tests] [--reset-db] [--seed-only]
# ═══════════════════════════════════════════════════════
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

ROOT="$(cd "$(dirname "$0")" && pwd)"
SKIP_TESTS=false
RESET_DB=false
SEED_ONLY=false

# ── Ports fixes ──────────────────────────────────────────────
BACKEND_PORT=8000
FRONTEND_PORT=5173

for arg in "$@"; do
    case $arg in
        --skip-tests) SKIP_TESTS=true ;;
        --reset-db)   RESET_DB=true ;;
        --seed-only)  SEED_ONLY=true ;;
        --help|-h)
            echo "Usage: ./start-dev.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-tests   Sauter les tests backend + typecheck frontend"
            echo "  --reset-db     Supprimer et recréer toutes les données Supabase"
            echo "  --seed-only    Juste re-seeder les données (pas de build ni serveurs)"
            echo "  --help         Afficher cette aide"
            exit 0
            ;;
    esac
done

echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}  GererSCI — Clean Build & Run${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"

# ── 0. Libérer les ports (kill tout ce qui tourne dessus) ─────
echo -e "\n${YELLOW}[0/7]${NC} Libération des ports $BACKEND_PORT + $FRONTEND_PORT ..."

kill_port() {
    local port=$1
    local pids
    pids=$(lsof -ti:"$port" 2>/dev/null) || true
    if [ -n "$pids" ]; then
        echo "$pids" | xargs kill -9 2>/dev/null
        echo -e "  ${CYAN}↳ Port $port libéré (PID: $(echo $pids | tr '\n' ' '))${NC}"
    fi
}

kill_port $BACKEND_PORT
kill_port $FRONTEND_PORT
# Aussi nettoyer les ports vite overflow (5174-5179) au cas où
for port in 5174 5175 5176 5177 5178 5179; do
    kill_port $port
done
sleep 1
echo -e "${GREEN}  ✅ Ports libérés${NC}"

# ── 1. Vérifier Supabase ──────────────────────────────────────
echo -e "\n${YELLOW}[1/7]${NC} Vérification Supabase local ..."
ANON_KEY=$(grep "^SUPABASE_ANON_KEY=" "$ROOT/backend/.env" | cut -d= -f2)
if ! curl -sf http://127.0.0.1:54321/rest/v1/ -H "apikey: $ANON_KEY" > /dev/null 2>&1; then
    echo -e "${RED}  Supabase non démarré. Lancement...${NC}"
    cd "$ROOT" && supabase start
    echo -e "${GREEN}  ✅ Supabase démarré${NC}"
else
    echo -e "${GREEN}  ✅ Supabase OK${NC}"
fi

# ── 2. Reset DB si demandé ─────────────────────────────────────
if [ "$RESET_DB" = true ]; then
    echo -e "\n${YELLOW}[2/7]${NC} Reset base de données ..."
    cd "$ROOT"
    supabase db reset
    echo -e "${GREEN}  ✅ DB reset (migrations rejouées)${NC}"
fi

if [ "$SEED_ONLY" = true ]; then
    echo -e "\n${YELLOW}[seed]${NC} Seed données de démonstration ..."
    cd "$ROOT/backend"
    python scripts/seed_dev_data.py
    echo -e "\n${GREEN}✅ Seed terminé. Serveurs non démarrés (--seed-only).${NC}"
    exit 0
fi

# ── 3. Backend: install deps ──────────────────────────────────
echo -e "\n${YELLOW}[3/7]${NC} Backend: installation dépendances ..."
cd "$ROOT/backend"
pip install -q -r requirements.txt 2>&1 | tail -3
echo -e "${GREEN}  ✅ Backend deps OK${NC}"

# ── 4. Backend: tests ─────────────────────────────────────────
if [ "$SKIP_TESTS" = false ]; then
    echo -e "\n${YELLOW}[4/7]${NC} Backend: tests ..."
    PYTHONPATH=. pytest --tb=short -q 2>&1 | tail -5
    PYTEST_EXIT=$?
    if [ $PYTEST_EXIT -ne 0 ]; then
        echo -e "${RED}  ❌ Tests backend échoués (exit $PYTEST_EXIT)${NC}"
        echo -e "${YELLOW}  Continuez avec --skip-tests pour ignorer${NC}"
        exit 1
    fi
    echo -e "${GREEN}  ✅ Backend tests OK${NC}"
else
    echo -e "\n${YELLOW}[4/7]${NC} Backend: tests ${CYAN}(skipped)${NC}"
fi

# ── 5. Frontend: clean install + check ────────────────────────
echo -e "\n${YELLOW}[5/7]${NC} Frontend: clean install ..."
cd "$ROOT/frontend"
rm -rf .svelte-kit node_modules/.vite
pnpm install --frozen-lockfile 2>&1 | tail -3
echo -e "${GREEN}  ✅ Frontend deps OK${NC}"

if [ "$SKIP_TESTS" = false ]; then
    echo -e "\n${YELLOW}[5b/7]${NC} Frontend: type check ..."
    pnpm run check 2>&1 | tail -5
    echo -e "${GREEN}  ✅ Type check OK${NC}"
else
    echo -e "\n${YELLOW}[5b/7]${NC} Frontend: type check ${CYAN}(skipped)${NC}"
fi

# ── 6. Seed données (--clean pour idempotence) ───────────────
echo -e "\n${YELLOW}[6/7]${NC} Seed données de démonstration ..."
cd "$ROOT/backend"
python scripts/seed_dev_data.py --clean

# ── 7. Démarrage des serveurs ─────────────────────────────────
echo -e "\n${YELLOW}[7/7]${NC} Démarrage des serveurs ..."

# Backend — port fixe
cd "$ROOT/backend"
PYTHONPATH=. uvicorn app.main:app --reload --port $BACKEND_PORT &
BACKEND_PID=$!

# Frontend — port fixe strict (fail si pris au lieu de fallback)
cd "$ROOT/frontend"
pnpm run dev -- --port $FRONTEND_PORT --strictPort &
FRONTEND_PID=$!

# Attendre que les serveurs soient prêts
echo -e "\n${CYAN}Attente des serveurs ...${NC}"
for i in $(seq 1 15); do
    sleep 1
    BACKEND_OK=false
    FRONTEND_OK=false
    curl -sf http://localhost:$BACKEND_PORT/docs > /dev/null 2>&1 && BACKEND_OK=true
    curl -sf http://localhost:$FRONTEND_PORT > /dev/null 2>&1 && FRONTEND_OK=true
    if [ "$BACKEND_OK" = true ] && [ "$FRONTEND_OK" = true ]; then
        break
    fi
done

echo ""
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo -e "${GREEN}  ✅ GererSCI est prêt !${NC}"
echo -e "${BLUE}═══════════════════════════════════════════${NC}"
echo ""
echo -e "  ${CYAN}Frontend${NC}   http://localhost:$FRONTEND_PORT"
echo -e "  ${CYAN}Backend${NC}    http://localhost:$BACKEND_PORT"
echo -e "  ${CYAN}API Docs${NC}   http://localhost:$BACKEND_PORT/docs"
echo -e "  ${CYAN}Studio${NC}     http://localhost:54323"
echo -e "  ${CYAN}Mailpit${NC}    http://localhost:54324"
echo ""
echo -e "  ${YELLOW}📧 Email${NC}    demo@gerersci.fr"
echo -e "  ${YELLOW}🔑 Password${NC} password123"
echo -e "  ${YELLOW}👑 Admin${NC}    oui  •  ${YELLOW}💳 Plan${NC} Pro actif"
echo ""
echo -e "  ${CYAN}Ctrl+C${NC} pour arrêter les serveurs"
echo ""

# Cleanup on exit
trap "
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    echo -e '\n${RED}Serveurs arrêtés${NC}'
" EXIT INT TERM

wait
