#!/bin/bash
# ═══════════════════════════════════════════════════════
# GererSCI — Clean Build + Seed + Run (idempotent)
# Usage: ./start-dev.sh [--skip-tests] [--reset-db] [--seed-only] [--verbose]
# ═══════════════════════════════════════════════════════
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
DIM='\033[2m'
BOLD='\033[1m'
NC='\033[0m'

ROOT="$(cd "$(dirname "$0")" && pwd)"
SKIP_TESTS=false
RESET_DB=false
SEED_ONLY=false
NO_SEED=false
CLEAN_ALL=false
VERBOSE=false

# ── Ports fixes ──────────────────────────────────────────────
BACKEND_PORT=8000
FRONTEND_PORT=5173
SUPABASE_API_PORT=54321
SUPABASE_STUDIO_PORT=54323
MAILPIT_PORT=54324

# ── Log files ────────────────────────────────────────────────
LOG_DIR="$ROOT/.dev-logs"
mkdir -p "$LOG_DIR"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"

# ── PIDs pour cleanup ────────────────────────────────────────
BACKEND_PID=""
FRONTEND_PID=""
TAIL_BACKEND_PID=""
TAIL_FRONTEND_PID=""
HEALTH_PID=""

SHUTTING_DOWN=false

cleanup() {
    # Prevent re-entrance
    [ "$SHUTTING_DOWN" = true ] && return
    SHUTTING_DOWN=true

    echo ""
    echo -e "${CYAN}  Arrêt des serveurs ...${NC}"

    # Kill monitoring processes first
    for pid in "$TAIL_BACKEND_PID" "$TAIL_FRONTEND_PID" "$HEALTH_PID"; do
        [ -n "$pid" ] && kill "$pid" 2>/dev/null || true
    done

    # Kill process trees: first SIGTERM, then SIGKILL
    for pid in "$BACKEND_PID" "$FRONTEND_PID"; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            # pkill kills all children of the process
            pkill -TERM -P "$pid" 2>/dev/null || true
            kill "$pid" 2>/dev/null || true
        fi
    done

    # Also kill by port as safety net (uvicorn/vite spawn workers)
    for port in $BACKEND_PORT $FRONTEND_PORT; do
        lsof -ti:"$port" 2>/dev/null | xargs kill 2>/dev/null || true
    done

    # Brief wait for graceful exit
    sleep 1

    # Force kill anything remaining
    for pid in "$BACKEND_PID" "$FRONTEND_PID"; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            pkill -9 -P "$pid" 2>/dev/null || true
            kill -9 "$pid" 2>/dev/null || true
        fi
    done
    for port in $BACKEND_PORT $FRONTEND_PORT; do
        lsof -ti:"$port" 2>/dev/null | xargs kill -9 2>/dev/null || true
    done

    echo -e "${CYAN}  Serveurs arrêtés${NC}"
    exit 0
}
trap cleanup INT TERM
trap 'cleanup' EXIT

for arg in "$@"; do
    case $arg in
        --skip-tests) SKIP_TESTS=true ;;
        --reset-db)   RESET_DB=true ;;
        --seed-only)  SEED_ONLY=true ;;
        --no-seed)    NO_SEED=true ;;
        --clean)      CLEAN_ALL=true ;;
        --verbose|-v) VERBOSE=true ;;
        --help|-h)
            echo "Usage: ./start-dev.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --skip-tests   Sauter les tests backend + typecheck frontend"
            echo "  --reset-db     Supprimer et recréer toutes les données Supabase"
            echo "  --seed-only    Juste re-seeder les données (pas de build ni serveurs)"
            echo "  --no-seed      Démarrer sans seeder les données"
            echo "  --clean        Tout nettoyer (containers, node_modules, caches, __pycache__)"
            echo "  --verbose, -v  Afficher les logs des serveurs dans la console"
            echo "  --help         Afficher cette aide"
            echo ""
            echo "Logs:"
            echo "  Backend  → $BACKEND_LOG"
            echo "  Frontend → $FRONTEND_LOG"
            exit 0
            ;;
    esac
done

# ── Helpers ──────────────────────────────────────────────────
step_start() { echo -e "\n${YELLOW}[$1]${NC} $2"; }
step_ok()    { echo -e "${GREEN}  ✅ $1${NC}"; }
step_skip()  { echo -e "${CYAN}  ⏭  $1 (skipped)${NC}"; }
step_fail()  { echo -e "${RED}  ❌ $1${NC}"; }
step_warn()  { echo -e "${YELLOW}  ⚠️  $1${NC}"; }

check_dependency() {
    if ! command -v "$1" &>/dev/null; then
        step_fail "$1 n'est pas installé"
        echo -e "  ${DIM}Installez $1 : $2${NC}"
        exit 1
    fi
}

echo -e "${BLUE}${BOLD}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}${BOLD}  GererSCI — Clean Build & Run${NC}"
echo -e "${BLUE}${BOLD}═══════════════════════════════════════════${NC}"
echo -e "${DIM}  $(date '+%Y-%m-%d %H:%M:%S') • logs → $LOG_DIR/${NC}"

# ── 0. Prérequis ─────────────────────────────────────────────
step_start "0/7" "Vérification prérequis + libération ports ..."

check_dependency "python" "https://python.org"
check_dependency "pnpm" "npm install -g pnpm"
check_dependency "docker" "https://docs.docker.com/get-docker/"
check_dependency "supabase" "https://supabase.com/docs/guides/cli"

kill_port() {
    local port=$1
    local pids
    pids=$(lsof -ti:"$port" 2>/dev/null) || true
    if [ -n "$pids" ]; then
        echo "$pids" | xargs kill -9 2>/dev/null || true
        echo -e "  ${DIM}↳ Port $port libéré (PID: $(echo "$pids" | tr '\n' ' '))${NC}"
    fi
}

kill_port $BACKEND_PORT
kill_port $FRONTEND_PORT
for port in 5174 5175 5176 5177 5178 5179; do
    kill_port "$port"
done
sleep 1
step_ok "Prérequis OK, ports libérés"

# ── 0b. Clean all si demandé ─────────────────────────────────
if [ "$CLEAN_ALL" = true ]; then
    step_start "clean" "Nettoyage complet ..."

    # Stop Supabase containers
    echo -e "  ${DIM}↳ Arrêt Supabase ...${NC}"
    cd "$ROOT" && supabase stop --no-backup 2>&1 | tail -2 || true

    # Kill all dev processes on known ports
    for port in $BACKEND_PORT $FRONTEND_PORT 5174 5175 5176 5177 5178 5179; do
        lsof -ti:"$port" 2>/dev/null | xargs kill -9 2>/dev/null || true
    done

    # Frontend caches
    echo -e "  ${DIM}↳ Suppression node_modules, .svelte-kit, caches Vite ...${NC}"
    rm -rf "$ROOT/frontend/node_modules"
    rm -rf "$ROOT/frontend/.svelte-kit"
    rm -rf "$ROOT/frontend/node_modules/.vite"
    rm -rf "$ROOT/frontend/build"
    rm -rf "$ROOT/frontend/dist"

    # Backend caches
    echo -e "  ${DIM}↳ Suppression __pycache__, .pytest_cache, .mypy_cache ...${NC}"
    find "$ROOT/backend" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$ROOT/backend" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find "$ROOT/backend" -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
    find "$ROOT/backend" -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

    # Dev logs
    rm -rf "$LOG_DIR"
    mkdir -p "$LOG_DIR"

    step_ok "Nettoyage terminé"
fi

# ── 1. Vérifier Supabase ──────────────────────────────────────
step_start "1/7" "Vérification Supabase local ..."

supabase_healthy() {
    local anon_key
    anon_key=$(grep "^SUPABASE_ANON_KEY=" "$ROOT/.env" 2>/dev/null | cut -d= -f2)
    if [ -z "$anon_key" ]; then
        echo -e "  ${RED}↳ SUPABASE_ANON_KEY manquant dans .env${NC}"
        return 1
    fi
    curl -sf --max-time 5 http://127.0.0.1:$SUPABASE_API_PORT/rest/v1/ \
        -H "apikey: $anon_key" > /dev/null 2>&1
}

docker_healthy() {
    docker info > /dev/null 2>&1
}

start_supabase() {
    local attempt=$1
    echo -e "  ${CYAN}↳ Tentative $attempt/3 : supabase start ...${NC}"
    if cd "$ROOT" && supabase start 2>&1 | tail -5; then
        return 0
    fi
    return 1
}

if ! docker_healthy; then
    step_fail "Docker n'est pas démarré"
    echo -e "  ${DIM}Lancez Docker Desktop ou le daemon Docker${NC}"
    exit 1
fi

if supabase_healthy; then
    step_ok "Supabase OK"
else
    step_warn "Supabase non disponible. Diagnostic ..."

    # Check if containers exist but are stopped/crashed
    if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "supabase.*sci-manager"; then
        echo -e "  ${CYAN}↳ Containers Supabase détectés. Nettoyage ...${NC}"
        cd "$ROOT" && supabase stop --no-backup 2>&1 | tail -2 || true
        sleep 2
    fi

    SUPABASE_OK=false
    for attempt in 1 2 3; do
        if start_supabase "$attempt"; then
            # Wait up to 30s for API to become healthy
            for i in $(seq 1 10); do
                sleep 3
                if supabase_healthy; then
                    SUPABASE_OK=true
                    break 2
                fi
                echo -ne "  ${DIM}↳ Attente API ($((i*3))s) ...${NC}\r"
            done
        fi

        if [ "$attempt" -lt 3 ]; then
            echo -e "  ${YELLOW}↳ Échec. Arrêt complet avant retry ...${NC}"
            cd "$ROOT" && supabase stop --no-backup 2>&1 | tail -2 || true
            sleep 3
        fi
    done

    if [ "$SUPABASE_OK" = true ]; then
        step_ok "Supabase démarré"
    else
        step_fail "Impossible de démarrer Supabase après 3 tentatives"
        echo -e "  ${DIM}Debug : supabase stop && supabase start --debug${NC}"
        echo -e "  ${DIM}État  : docker ps -a | grep supabase${NC}"
        exit 1
    fi
fi

# ── 2. Reset DB si demandé ─────────────────────────────────────
if [ "$RESET_DB" = true ]; then
    step_start "2/7" "Reset base de données ..."
    cd "$ROOT"
    supabase db reset
    step_ok "DB reset (migrations rejouées)"
fi

if [ "$SEED_ONLY" = true ]; then
    step_start "seed" "Seed données de démonstration ..."
    cd "$ROOT/backend"
    python scripts/seed_dev_data.py
    step_ok "Seed terminé. Serveurs non démarrés (--seed-only)."
    exit 0
fi

# ── 3. Backend: install deps ──────────────────────────────────
step_start "3/7" "Backend: installation dépendances ..."
cd "$ROOT/backend"
if ! pip install -q -r requirements.txt 2>&1 | tail -3; then
    step_fail "Échec installation dépendances backend"
    exit 1
fi
step_ok "Backend deps OK"

# ── 4. Backend: tests ─────────────────────────────────────────
if [ "$SKIP_TESTS" = false ]; then
    step_start "4/7" "Backend: tests ..."
    set +e
    PYTHONPATH=. pytest --tb=short -q 2>&1 | tail -10
    PYTEST_EXIT=${PIPESTATUS[0]}
    set -e
    if [ "$PYTEST_EXIT" -ne 0 ]; then
        step_fail "Tests backend échoués (exit $PYTEST_EXIT)"
        echo -e "  ${DIM}Relancez avec --skip-tests pour ignorer${NC}"
        exit 1
    fi
    step_ok "Backend tests OK"
else
    step_start "4/7" "Backend: tests"
    step_skip "tests backend"
fi

# ── 5. Frontend: clean install + check ────────────────────────
step_start "5/7" "Frontend: clean install ..."
cd "$ROOT/frontend"
rm -rf .svelte-kit node_modules/.vite
if ! pnpm install --frozen-lockfile 2>&1 | tail -3; then
    step_fail "Échec installation dépendances frontend"
    exit 1
fi
step_ok "Frontend deps OK"

if [ "$SKIP_TESTS" = false ]; then
    step_start "5b/7" "Frontend: type check ..."
    set +e
    pnpm run check 2>&1 | tail -10
    CHECK_EXIT=${PIPESTATUS[0]}
    set -e
    if [ "$CHECK_EXIT" -ne 0 ]; then
        step_fail "Type check échoué (exit $CHECK_EXIT)"
        echo -e "  ${DIM}Relancez avec --skip-tests pour ignorer${NC}"
        exit 1
    fi
    step_ok "Type check OK"
else
    step_start "5b/7" "Frontend: type check"
    step_skip "type check frontend"
fi

# ── 6. Seed données (--clean pour idempotence) ───────────────
if [ "$NO_SEED" = false ]; then
    step_start "6/7" "Seed données de démonstration ..."
    cd "$ROOT/backend"
    if ! python scripts/seed_dev_data.py --clean; then
        step_warn "Seed échoué — serveurs démarrent sans données fraîches"
    fi
else
    step_start "6/7" "Seed données"
    step_skip "seed (--no-seed)"
fi

# ── 7. Démarrage des serveurs ─────────────────────────────────
step_start "7/7" "Démarrage des serveurs ..."

# Truncate logs
> "$BACKEND_LOG"
> "$FRONTEND_LOG"

# Backend — port fixe
cd "$ROOT/backend"
if [ "$VERBOSE" = true ]; then
    PYTHONPATH=. uvicorn app.main:app --reload --port $BACKEND_PORT 2>&1 | tee "$BACKEND_LOG" &
else
    PYTHONPATH=. uvicorn app.main:app --reload --port $BACKEND_PORT > "$BACKEND_LOG" 2>&1 &
fi
BACKEND_PID=$!

# Frontend — port fixe strict
cd "$ROOT/frontend"
if [ "$VERBOSE" = true ]; then
    pnpm run dev -- --port $FRONTEND_PORT --strictPort 2>&1 | tee "$FRONTEND_LOG" &
else
    pnpm run dev -- --port $FRONTEND_PORT --strictPort > "$FRONTEND_LOG" 2>&1 &
fi
FRONTEND_PID=$!

# Attendre que les serveurs soient prêts (timeout 45s)
echo -e "  ${DIM}Backend PID=$BACKEND_PID • Frontend PID=$FRONTEND_PID${NC}"
BACKEND_OK=false
FRONTEND_OK=false
SPINNER=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')

for i in $(seq 1 45); do
    sleep 1
    spin="${SPINNER[$((i % ${#SPINNER[@]}))]}"

    # Check processes still alive
    if [ "$BACKEND_OK" = false ] && ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo ""
        step_fail "Le backend a crashé au démarrage"
        echo -e "  ${DIM}Voir: tail -30 $BACKEND_LOG${NC}"
        tail -10 "$BACKEND_LOG" 2>/dev/null | sed 's/^/  /' || true
        exit 1
    fi
    if [ "$FRONTEND_OK" = false ] && ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo ""
        step_fail "Le frontend a crashé au démarrage"
        echo -e "  ${DIM}Voir: tail -30 $FRONTEND_LOG${NC}"
        tail -10 "$FRONTEND_LOG" 2>/dev/null | sed 's/^/  /' || true
        exit 1
    fi

    # Health checks
    [ "$BACKEND_OK" = false ] && curl -sf --max-time 2 http://localhost:$BACKEND_PORT/docs > /dev/null 2>&1 && BACKEND_OK=true
    [ "$FRONTEND_OK" = false ] && curl -sf --max-time 2 http://localhost:$FRONTEND_PORT > /dev/null 2>&1 && FRONTEND_OK=true

    # Status line
    B_STATUS=$( [ "$BACKEND_OK" = true ] && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}…${NC}" )
    F_STATUS=$( [ "$FRONTEND_OK" = true ] && echo -e "${GREEN}✓${NC}" || echo -e "${YELLOW}…${NC}" )
    echo -ne "  ${CYAN}$spin${NC} Backend [${B_STATUS}]  Frontend [${F_STATUS}]  (${i}s)    \r"

    if [ "$BACKEND_OK" = true ] && [ "$FRONTEND_OK" = true ]; then
        echo ""
        break
    fi
done

if [ "$BACKEND_OK" = false ] || [ "$FRONTEND_OK" = false ]; then
    echo ""
    step_warn "Timeout: certains serveurs n'ont pas répondu dans les 45s"
    [ "$BACKEND_OK" = false ] && echo -e "    ${RED}Backend (port $BACKEND_PORT)${NC} — pas de réponse"
    [ "$FRONTEND_OK" = false ] && echo -e "    ${RED}Frontend (port $FRONTEND_PORT)${NC} — pas de réponse"

    # Show last few lines from logs for debug
    if [ "$BACKEND_OK" = false ] && [ -s "$BACKEND_LOG" ]; then
        echo -e "  ${DIM}Backend log (dernières lignes):${NC}"
        tail -5 "$BACKEND_LOG" | sed 's/^/    /'
    fi
    if [ "$FRONTEND_OK" = false ] && [ -s "$FRONTEND_LOG" ]; then
        echo -e "  ${DIM}Frontend log (dernières lignes):${NC}"
        tail -5 "$FRONTEND_LOG" | sed 's/^/    /'
    fi
fi

# ── Dashboard final ──────────────────────────────────────────
SB_STATUS=$( supabase_healthy && echo -e "${GREEN}●${NC}" || echo -e "${RED}●${NC}" )
BK_STATUS=$( [ "$BACKEND_OK" = true ] && echo -e "${GREEN}●${NC}" || echo -e "${RED}●${NC}" )
FE_STATUS=$( [ "$FRONTEND_OK" = true ] && echo -e "${GREEN}●${NC}" || echo -e "${RED}●${NC}" )

echo ""
echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════${NC}"
echo -e "${GREEN}${BOLD}  GererSCI est prêt !${NC}"
echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════${NC}"
echo ""
echo -e "  ${BOLD}Services${NC}                          ${BOLD}PIDs${NC}"
echo -e "  ${FE_STATUS} Frontend    http://localhost:$FRONTEND_PORT    ${DIM}$FRONTEND_PID${NC}"
echo -e "  ${BK_STATUS} Backend     http://localhost:$BACKEND_PORT       ${DIM}$BACKEND_PID${NC}"
echo -e "  ${BK_STATUS} API Docs    http://localhost:$BACKEND_PORT/docs"
echo -e "  ${SB_STATUS} Supabase    http://localhost:$SUPABASE_STUDIO_PORT"
echo -e "  ${SB_STATUS} Mailpit     http://localhost:$MAILPIT_PORT"
echo ""
echo -e "  ${BOLD}Credentials${NC}"
echo -e "  📧 demo@gerersci.fr  🔑 password123  👑 admin  💳 Pro"
echo ""
echo -e "  ${CYAN}Ctrl+C${NC} pour arrêter"
echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════${NC}"
echo ""

# ── Live monitoring ─────────────────────────────────────────
# Tail both logs with colored prefixes
TAIL_PID=""

tail -n 0 -f "$BACKEND_LOG" 2>/dev/null | sed -u "s/^/$(printf "${YELLOW}[backend]${NC} ")/" &
TAIL_BACKEND_PID=$!

tail -n 0 -f "$FRONTEND_LOG" 2>/dev/null | sed -u "s/^/$(printf "${CYAN}[frontend]${NC} ")/" &
TAIL_FRONTEND_PID=$!

# Health check loop (background) — alerts if a server dies
(
    while true; do
        sleep 5
        B_ALIVE=true; F_ALIVE=true
        kill -0 "$BACKEND_PID" 2>/dev/null || B_ALIVE=false
        kill -0 "$FRONTEND_PID" 2>/dev/null || F_ALIVE=false

        if [ "$B_ALIVE" = false ] && [ "$F_ALIVE" = false ]; then
            echo -e "\n${RED}${BOLD}  ⚠ Les deux serveurs se sont arrêtés !${NC}"
            echo -e "  ${DIM}tail -30 $BACKEND_LOG${NC}"
            echo -e "  ${DIM}tail -30 $FRONTEND_LOG${NC}"
            kill -TERM $$ 2>/dev/null
            break
        elif [ "$B_ALIVE" = false ]; then
            echo -e "\n${RED}  ⚠ Backend crashé (PID $BACKEND_PID)${NC}"
            echo -e "  ${DIM}Dernières lignes :${NC}"
            tail -5 "$BACKEND_LOG" 2>/dev/null | sed 's/^/    /'
        elif [ "$F_ALIVE" = false ]; then
            echo -e "\n${RED}  ⚠ Frontend crashé (PID $FRONTEND_PID)${NC}"
            echo -e "  ${DIM}Dernières lignes :${NC}"
            tail -5 "$FRONTEND_LOG" 2>/dev/null | sed 's/^/    /'
        fi
    done
) &
HEALTH_PID=$!

# Wait for any signal — cleanup will handle everything
wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true

# Kill monitoring helpers
kill "$TAIL_BACKEND_PID" "$TAIL_FRONTEND_PID" "$HEALTH_PID" 2>/dev/null || true
