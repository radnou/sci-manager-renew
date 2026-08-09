#!/bin/bash
# ═══════════════════════════════════════════════════════
# GererSCI — Build + Seed + Run + Supervision tmux
#
# Usage: ./start-dev.sh [SOUS-COMMANDE] [OPTIONS]
#   ./start-dev.sh              démarre tout et s'attache à la session tmux
#   ./start-dev.sh status       état des services, une passe, puis sort
#   ./start-dev.sh doctor       diagnostic seul, ne démarre rien
#   ./start-dev.sh stop         arrête les services (jamais Supabase ni Docker)
#   ./start-dev.sh --help       aide complète
#
# Bash 3.2 compatible (macOS) : pas de declare -A, pas de mapfile.
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
DETACH=false
NO_TMUX=false
WANT_BACKEND=true
WANT_FRONTEND=true

# ── Ports fixes ──────────────────────────────────────────────
BACKEND_PORT=8001  # 8000 est pris par Supabase Kong
FRONTEND_PORT=5173
SUPABASE_API_PORT=54321
SUPABASE_DB_PORT=54322
SUPABASE_STUDIO_PORT=54323
MAILPIT_PORT=54324

PG_DSN="postgresql://postgres:postgres@127.0.0.1:$SUPABASE_DB_PORT/postgres"
SUPABASE_DB_CONTAINER="supabase_db_sci-manager-renew"

# ── Session tmux ─────────────────────────────────────────────
SESSION="${TMUX_SESSION:-gerersci}"
MONITOR_INTERVAL="${MONITOR_INTERVAL:-3}"

# ── Fichiers ─────────────────────────────────────────────────
LOG_DIR="$ROOT/.dev-logs"
mkdir -p "$LOG_DIR"
BACKEND_LOG="$LOG_DIR/backend.log"
FRONTEND_LOG="$LOG_DIR/frontend.log"
ALERT_LOG="$LOG_DIR/monitor-alerts.log"
SESSION_START_FILE="$LOG_DIR/.session-start"
MONITOR_STATE="$LOG_DIR/.monitor-state"

# ── Interpréteurs résolus (remplis par les resolvers) ────────
PYTHON_BIN=""
PNPM_BIN=""
CAN_BACKEND=false
CAN_FRONTEND=false

# ── PIDs (chemin de repli sans tmux) ─────────────────────────
BACKEND_PID=""
FRONTEND_PID=""
TAIL_BACKEND_PID=""
TAIL_FRONTEND_PID=""
HEALTH_PID=""
SHUTTING_DOWN=false
USE_TMUX=false

ERR_PATTERN='error|exception|traceback|ERR!|CRITICAL'

# ── Helpers d'affichage ──────────────────────────────────────
step_start() { echo -e "\n${YELLOW}[$1]${NC} $2"; }
step_ok()    { echo -e "${GREEN}  ✅ $1${NC}"; }
step_skip()  { echo -e "${CYAN}  ⏭  $1 (skipped)${NC}"; }
step_fail()  { echo -e "${RED}  ❌ $1${NC}"; }
step_warn()  { echo -e "${YELLOW}  ⚠️  $1${NC}"; }

# ═════════════════════════════════════════════════════════════
#  RÉSOLUTION RÉSILIENTE DES INTERPRÉTEURS
#  On valide en EXÉCUTANT, pas en testant la présence dans PATH.
#  Un shim pyenv sans version installée répond à `command -v`
#  mais échoue à l'exécution : il doit être rejeté.
# ═════════════════════════════════════════════════════════════

python_is_usable() {
    local cand="$1"
    [ -n "$cand" ] || return 1
    "$cand" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1
}

resolve_python() {
    local cand

    if [ -n "${PYTHON_BIN_OVERRIDE:-}" ]; then
        python_is_usable "$PYTHON_BIN_OVERRIDE" && { PYTHON_BIN="$PYTHON_BIN_OVERRIDE"; return 0; }
    fi

    for cand in \
        "$ROOT/backend/.venv/bin/python" \
        "$ROOT/backend/venv/bin/python" \
        "$ROOT/.venv/bin/python"
    do
        if [ -x "$cand" ] && python_is_usable "$cand"; then
            PYTHON_BIN="$cand"; return 0
        fi
    done

    # La version cible du projet vient du Dockerfile (FROM python:3.12-slim),
    # source de vérité partagée avec la production. On l'essaie EN PREMIER.
    # Sans ça, un `python3` plus récent est retenu et la suite backend casse
    # pour des raisons sans rapport avec le code : en 3.14, pytest-asyncio
    # déclenche « There is no current event loop in thread 'MainThread' »
    # (asyncio.get_event_loop ne crée plus de boucle implicite).
    local target=""
    target="$(grep -iEm1 '^FROM python:[0-9]+\.[0-9]+' "$ROOT/backend/Dockerfile" 2>/dev/null \
              | sed -E 's/.*python:([0-9]+\.[0-9]+).*/\1/' || true)"

    for cand in ${target:+"python$target"} python3.12 python3 python python3.11; do
        local resolved
        resolved="$(command -v "$cand" 2>/dev/null || true)"
        if [ -n "$resolved" ] && python_is_usable "$resolved"; then
            PYTHON_BIN="$resolved"; return 0
        fi
    done

    if command -v uv >/dev/null 2>&1; then
        if uv run python -c 'import sys; sys.exit(0 if sys.version_info >= (3,11) else 1)' >/dev/null 2>&1; then
            PYTHON_BIN="uv-run"; return 0
        fi
    fi

    return 1
}

# Exécute Python quel que soit le mode résolu (binaire direct ou `uv run`).
py() {
    if [ "$PYTHON_BIN" = "uv-run" ]; then
        ( cd "$ROOT/backend" && uv run python "$@" )
    else
        "$PYTHON_BIN" "$@"
    fi
}

python_version_label() {
    if [ "$PYTHON_BIN" = "uv-run" ]; then
        echo "uv run python ($( (cd "$ROOT/backend" && uv run python -V 2>&1) | head -1 ))"
    else
        echo "$PYTHON_BIN ($("$PYTHON_BIN" -V 2>&1 | head -1))"
    fi
}

# node/pnpm ne résolvent souvent que dans un shell de login (nvm paresseux).
resolve_node_cmd() {
    local name="$1" resolved=""
    resolved="$(command -v "$name" 2>/dev/null || true)"
    if [ -z "$resolved" ] && command -v zsh >/dev/null 2>&1; then
        resolved="$(zsh -lc "command -v $name" 2>/dev/null | tail -1 || true)"
    fi
    if [ -z "$resolved" ] && command -v bash >/dev/null 2>&1; then
        resolved="$(bash -lc "command -v $name" 2>/dev/null | tail -1 || true)"
    fi
    [ -n "$resolved" ] && [ -x "$resolved" ] || return 1
    echo "$resolved"
}

require_hard() {
    if ! command -v "$1" >/dev/null 2>&1; then
        step_fail "$1 n'est pas installé"
        echo -e "  ${DIM}Installez $1 : $2${NC}"
        exit 1
    fi
}

# ═════════════════════════════════════════════════════════════
#  SONDES DE SANTÉ
# ═════════════════════════════════════════════════════════════

# Renvoie "CODE MILLISECONDES" sur stdout. CODE=000 si injoignable.
probe_http() {
    local url="$1" timeout="${2:-3}" out
    out="$(curl -s -o /dev/null -w '%{http_code} %{time_total}' --max-time "$timeout" "$url" 2>/dev/null || echo '000 0')"
    local code ms
    code="$(echo "$out" | awk '{print $1}')"
    ms="$(echo "$out" | awk '{printf "%d", $2 * 1000}')"
    echo "$code $ms"
}

port_proc() {
    if lsof -ti:"$1" >/dev/null 2>&1; then echo up; else echo down; fi
}

probe_postgres() {
    if command -v psql >/dev/null 2>&1; then
        psql "$PG_DSN" -tAc 'select 1' >/dev/null 2>&1 && echo ok || echo ko
    elif command -v nc >/dev/null 2>&1; then
        nc -z 127.0.0.1 "$SUPABASE_DB_PORT" >/dev/null 2>&1 && echo ok || echo ko
    else
        echo "?"
    fi
}

log_err_count() {
    # grep -c écrit le compte ET sort en 1 quand il vaut 0 : un `|| echo 0`
    # naïf produit deux lignes, ce qui décale ensuite tout le printf.
    local n
    [ -s "$1" ] || { echo 0; return 0; }
    n="$(grep -ciE "$ERR_PATTERN" "$1" 2>/dev/null | head -1)"
    case "$n" in ''|*[!0-9]*) n=0 ;; esac
    echo "$n"
    return 0
}

log_last_err() {
    # grep sort en 1 quand il ne trouve rien. Avec `set -o pipefail`, le
    # pipeline propage ce 1, l'affectation par substitution de commande en
    # hérite, et `set -e` tue le script. Autrement dit la sonde cassait
    # précisément quand le service était sain. Toujours renvoyer 0.
    [ -s "$1" ] || return 0
    grep -iE "$ERR_PATTERN" "$1" 2>/dev/null | tail -1 | cut -c1-120 || true
    return 0
}

uptime_label() {
    [ -f "$SESSION_START_FILE" ] || { echo "-"; return; }
    local start now d h m
    start="$(cat "$SESSION_START_FILE" 2>/dev/null || echo 0)"
    case "$start" in ''|*[!0-9]*) echo "-"; return ;; esac
    now="$(date +%s)"
    d=$(( now - start ))
    h=$(( d / 3600 )); m=$(( (d % 3600) / 60 ))
    if [ "$h" -gt 0 ]; then echo "${h}h${m}m"; else echo "${m}m$(( d % 60 ))s"; fi
}

# Colorise selon le code HTTP et l'état du processus.
status_dot() {
    local code="$1" proc="$2"
    if [ "$proc" = down ] || [ "$code" = 000 ]; then echo -e "${RED}●${NC}"; return; fi
    case "$code" in
        2*|3*) echo -e "${GREEN}●${NC}" ;;
        4*)    echo -e "${YELLOW}●${NC}" ;;
        *)     echo -e "${RED}●${NC}" ;;
    esac
}

# ═════════════════════════════════════════════════════════════
#  TABLEAU DE BORD
#  render_dashboard : une passe. Utilisé par `status` et par la
#  boucle de la fenêtre tmux `monitor`.
# ═════════════════════════════════════════════════════════════

render_dashboard() {
    local all_ok=0

    printf "\n"
    printf "${BLUE}${BOLD}  GererSCI — supervision${NC}   ${DIM}%s${NC}\n" "$(date '+%Y-%m-%d %H:%M:%S')"
    printf "${DIM}  session tmux : %s • uptime : %s • logs : %s${NC}\n\n" "$SESSION" "$(uptime_label)" ".dev-logs/"

    printf "  ${BOLD}%-16s %-7s %-6s %-6s %-9s %-6s${NC}\n" "Service" "Port" "Proc" "HTTP" "Latence" "Err"
    printf "  ${DIM}%s${NC}\n" "------------------------------------------------------------"

    local r code ms proc dot errs

    # frontend
    proc="$(port_proc $FRONTEND_PORT)"
    r="$(probe_http "http://localhost:$FRONTEND_PORT" 3)"
    code="${r%% *}"; ms="${r##* }"
    errs="$(log_err_count "$FRONTEND_LOG")"
    dot="$(status_dot "$code" "$proc")"
    printf "  %b %-14s %-7s %-6s %-6s %-9s %-6s\n" "$dot" "frontend" "$FRONTEND_PORT" "$proc" "$code" "${ms}ms" "$errs"
    [ "$code" = 000 ] && all_ok=1

    # backend liveness
    proc="$(port_proc $BACKEND_PORT)"
    r="$(probe_http "http://localhost:$BACKEND_PORT/health/live" 3)"
    code="${r%% *}"; ms="${r##* }"
    errs="$(log_err_count "$BACKEND_LOG")"
    dot="$(status_dot "$code" "$proc")"
    printf "  %b %-14s %-7s %-6s %-6s %-9s %-6s\n" "$dot" "backend" "$BACKEND_PORT" "$proc" "$code" "${ms}ms" "$errs"
    [ "$code" = 000 ] && all_ok=1

    # backend readiness (dépendances externes)
    r="$(probe_http "http://localhost:$BACKEND_PORT/health/ready" 5)"
    code="${r%% *}"; ms="${r##* }"
    dot="$(status_dot "$code" "$proc")"
    printf "  %b %-14s %-7s %-6s %-6s %-9s %-6s\n" "$dot" "backend/ready" "$BACKEND_PORT" "$proc" "$code" "${ms}ms" "-"

    # supabase api
    proc="$(port_proc $SUPABASE_API_PORT)"
    r="$(probe_http "http://127.0.0.1:$SUPABASE_API_PORT/rest/v1/" 3)"
    code="${r%% *}"; ms="${r##* }"
    dot="$(status_dot "$code" "$proc")"
    printf "  %b %-14s %-7s %-6s %-6s %-9s %-6s\n" "$dot" "supabase-api" "$SUPABASE_API_PORT" "$proc" "$code" "${ms}ms" "-"
    [ "$code" = 000 ] && all_ok=1

    # postgres
    proc="$(port_proc $SUPABASE_DB_PORT)"
    local pg; pg="$(probe_postgres)"
    if [ "$pg" = ok ]; then dot="$(echo -e "${GREEN}●${NC}")"; else dot="$(echo -e "${RED}●${NC}")"; all_ok=1; fi
    printf "  %b %-14s %-7s %-6s %-6s %-9s %-6s\n" "$dot" "postgres" "$SUPABASE_DB_PORT" "$proc" "$pg" "-" "-"

    # studio + mailpit (informatif, n'influence pas le code de sortie)
    proc="$(port_proc $SUPABASE_STUDIO_PORT)"
    r="$(probe_http "http://127.0.0.1:$SUPABASE_STUDIO_PORT" 3)"
    code="${r%% *}"; ms="${r##* }"
    printf "  %b %-14s %-7s %-6s %-6s %-9s %-6s\n" "$(status_dot "$code" "$proc")" "studio" "$SUPABASE_STUDIO_PORT" "$proc" "$code" "${ms}ms" "-"

    proc="$(port_proc $MAILPIT_PORT)"
    r="$(probe_http "http://127.0.0.1:$MAILPIT_PORT" 3)"
    code="${r%% *}"; ms="${r##* }"
    printf "  %b %-14s %-7s %-6s %-6s %-9s %-6s\n" "$(status_dot "$code" "$proc")" "mailpit" "$MAILPIT_PORT" "$proc" "$code" "${ms}ms" "-"

    # Dernières erreurs
    local be fe
    be="$(log_last_err "$BACKEND_LOG")"
    fe="$(log_last_err "$FRONTEND_LOG")"
    if [ -n "$be" ] || [ -n "$fe" ]; then
        printf "\n  ${BOLD}Dernière erreur${NC}\n"
        [ -n "$be" ] && printf "  ${DIM}backend ${NC} %s\n" "$be"
        [ -n "$fe" ] && printf "  ${DIM}frontend${NC} %s\n" "$fe"
    fi

    # Alertes récentes
    if [ -s "$ALERT_LOG" ]; then
        printf "\n  ${BOLD}Alertes récentes${NC}\n"
        tail -5 "$ALERT_LOG" | sed 's/^/  /'
    fi

    return $all_ok
}

# Détecte les transitions up -> down entre deux cycles.
detect_transitions() {
    local current="" prev=""
    current="fe=$(port_proc $FRONTEND_PORT) be=$(port_proc $BACKEND_PORT) sb=$(port_proc $SUPABASE_API_PORT)"
    [ -f "$MONITOR_STATE" ] && prev="$(cat "$MONITOR_STATE" 2>/dev/null || true)"
    echo "$current" > "$MONITOR_STATE"
    [ -n "$prev" ] || return 0
    [ "$prev" = "$current" ] && return 0

    local svc
    for svc in fe be sb; do
        local was is
        was="$(echo "$prev"    | tr ' ' '\n' | grep "^$svc=" | cut -d= -f2)"
        is="$(echo "$current" | tr ' ' '\n' | grep "^$svc=" | cut -d= -f2)"
        if [ "$was" = up ] && [ "$is" = down ]; then
            echo "$(date '+%H:%M:%S') $svc est passé de up à down" >> "$ALERT_LOG"
        fi
    done
}

monitor_loop() {
    while true; do
        detect_transitions
        clear
        render_dashboard || true
        printf "\n  ${BOLD}Raccourcis${NC}\n"
        printf "  ${DIM}Ctrl+b 1${NC} backend   ${DIM}Ctrl+b 2${NC} frontend   ${DIM}Ctrl+b 3${NC} supabase   ${DIM}Ctrl+b 4${NC} shell\n"
        printf "  ${DIM}Ctrl+b d${NC} détacher (les services continuent)\n"
        printf "  ${CYAN}./start-dev.sh stop${NC} pour tout arrêter   ${DIM}rafraîchi toutes les %ss${NC}\n" "$MONITOR_INTERVAL"
        sleep "$MONITOR_INTERVAL"
    done
}

# ═════════════════════════════════════════════════════════════
#  SOUS-COMMANDES
# ═════════════════════════════════════════════════════════════

session_exists() { tmux has-session -t "$SESSION" 2>/dev/null; }

cmd_attach() {
    if ! command -v tmux >/dev/null 2>&1; then
        step_fail "tmux n'est pas installé"; exit 1
    fi
    if ! session_exists; then
        step_fail "Aucune session '$SESSION'. Lancez ./start-dev.sh"; exit 1
    fi
    exec tmux attach -t "$SESSION"
}

cmd_status() {
    render_dashboard
    local rc=$?
    echo ""
    exit $rc
}

# stop ne touche JAMAIS Supabase ni Docker : d'autres projets tournent
# sur le même daemon.
cmd_stop() {
    echo -e "${CYAN}  Arrêt des services applicatifs ...${NC}"
    if command -v tmux >/dev/null 2>&1 && session_exists; then
        tmux kill-session -t "$SESSION" 2>/dev/null || true
        echo -e "  ${DIM}↳ Session tmux '$SESSION' fermée${NC}"
    fi
    local port
    for port in $BACKEND_PORT $FRONTEND_PORT; do
        local pids
        pids="$(lsof -ti:"$port" 2>/dev/null || true)"
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill 2>/dev/null || true
            sleep 1
            pids="$(lsof -ti:"$port" 2>/dev/null || true)"
            [ -n "$pids" ] && echo "$pids" | xargs kill -9 2>/dev/null || true
            echo -e "  ${DIM}↳ Port $port libéré${NC}"
        fi
    done
    rm -f "$MONITOR_STATE"
    echo -e "${GREEN}  ✅ Services arrêtés. Supabase et Docker n'ont pas été touchés.${NC}"
    exit 0
}

cmd_restart() {
    local svc="${1:-}"
    case "$svc" in
        backend|frontend) ;;
        *) step_fail "Usage : ./start-dev.sh restart <backend|frontend>"; exit 1 ;;
    esac
    if ! command -v tmux >/dev/null 2>&1 || ! session_exists; then
        step_fail "Aucune session tmux '$SESSION' à redémarrer"; exit 1
    fi
    tmux respawn-window -k -t "$SESSION:$svc" 2>/dev/null || {
        step_fail "Fenêtre '$svc' introuvable dans la session"; exit 1
    }
    step_ok "Fenêtre '$svc' relancée"
    exit 0
}

cmd_logs() {
    local svc="${1:-}" f=""
    case "$svc" in
        backend)  f="$BACKEND_LOG" ;;
        frontend) f="$FRONTEND_LOG" ;;
        supabase) exec docker logs -f "$SUPABASE_DB_CONTAINER" ;;
        alerts)   f="$ALERT_LOG" ;;
        *) step_fail "Usage : ./start-dev.sh logs <backend|frontend|supabase|alerts>"; exit 1 ;;
    esac
    [ -f "$f" ] || { step_warn "Aucun log : $f"; exit 1; }
    exec tail -n 50 -f "$f"
}

cmd_doctor() {
    echo -e "${BLUE}${BOLD}  Diagnostic environnement GererSCI${NC}"
    echo -e "${DIM}  Aucun service n'est démarré par cette commande.${NC}\n"

    echo -e "  ${BOLD}Interpréteurs${NC}"
    if resolve_python; then
        echo -e "  ${GREEN}✅${NC} python  : $(python_version_label)"
    else
        echo -e "  ${RED}❌${NC} python  : aucun interpréteur >= 3.11 utilisable"
        echo -e "     ${DIM}python3 -m venv backend/.venv && backend/.venv/bin/pip install -r backend/requirements.txt${NC}"
    fi
    if PNPM_BIN="$(resolve_node_cmd pnpm)"; then
        echo -e "  ${GREEN}✅${NC} pnpm    : $PNPM_BIN ($("$PNPM_BIN" --version 2>/dev/null || echo '?'))"
    else
        echo -e "  ${RED}❌${NC} pnpm    : introuvable, même via shell de login"
        echo -e "     ${DIM}npm install -g pnpm${NC}"
    fi

    echo -e "\n  ${BOLD}Outils${NC}"
    local t
    for t in tmux docker supabase psql curl lsof jq; do
        if command -v "$t" >/dev/null 2>&1; then
            echo -e "  ${GREEN}✅${NC} $t"
        else
            echo -e "  ${YELLOW}⚠️${NC}  $t absent"
        fi
    done

    echo -e "\n  ${BOLD}Docker${NC}"
    if docker info >/dev/null 2>&1; then
        echo -e "  ${GREEN}✅${NC} daemon actif"
    else
        echo -e "  ${RED}❌${NC} daemon injoignable (lancez OrbStack ou Docker Desktop)"
    fi

    echo -e "\n  ${BOLD}Environnement Python backend${NC}"
    if [ -d "$ROOT/backend/.venv" ] || [ -d "$ROOT/backend/venv" ]; then
        echo -e "  ${GREEN}✅${NC} venv présent"
    else
        echo -e "  ${YELLOW}⚠️${NC}  aucun venv dans backend/ — les scénarios paywall, quotas et Stripe resteront indisponibles"
    fi

    echo -e "\n  ${BOLD}Configuration${NC}"
    if [ -f "$ROOT/.env" ]; then
        echo -e "  ${GREEN}✅${NC} .env présent"
        local k
        for k in SUPABASE_URL SUPABASE_ANON_KEY STRIPE_SECRET_KEY; do
            if grep -qE "^${k}=" "$ROOT/.env" 2>/dev/null; then
                echo -e "     ${DIM}$k : présent${NC}"
            else
                echo -e "     ${YELLOW}$k : absent${NC}"
            fi
        done
        # Contrôle de sûreté : on n'affiche jamais de valeur, seulement le mode.
        if grep -qE "^STRIPE_SECRET_KEY=sk_live_" "$ROOT/.env" 2>/dev/null; then
            echo -e "  ${RED}❌ STRIPE_SECRET_KEY est une clé de PRODUCTION${NC}"
            echo -e "     ${DIM}Un backend local avec cette clé crée de vrais paiements. Basculez en sk_test_.${NC}"
        fi
    else
        echo -e "  ${RED}❌${NC} .env absent à la racine (vite.config.ts déclare envDir '..')"
    fi

    echo -e "\n  ${BOLD}Ports${NC}"
    local p
    for p in $FRONTEND_PORT $BACKEND_PORT $SUPABASE_API_PORT $SUPABASE_DB_PORT $SUPABASE_STUDIO_PORT $MAILPIT_PORT; do
        if [ "$(port_proc "$p")" = up ]; then
            echo -e "  ${DIM}$p occupé par PID $(lsof -ti:"$p" 2>/dev/null | tr '\n' ' ')${NC}"
        else
            echo -e "  ${DIM}$p libre${NC}"
        fi
    done

    echo -e "\n  ${BOLD}Session tmux${NC}"
    if command -v tmux >/dev/null 2>&1 && session_exists; then
        echo -e "  ${GREEN}✅${NC} session '$SESSION' active"
        tmux list-windows -t "$SESSION" -F '     #{window_index}: #{window_name}' 2>/dev/null || true
    else
        echo -e "  ${DIM}aucune session '$SESSION'${NC}"
    fi
    echo ""
    exit 0
}

show_help() {
    cat <<EOF
Usage: ./start-dev.sh [SOUS-COMMANDE] [OPTIONS]

Sous-commandes:
  start              Build, seed puis démarrage supervisé (défaut)
  status             État des services, une passe, puis sortie
                     Code 0 si tout répond, 1 sinon
  doctor             Diagnostic seul. Ne démarre rien, ne modifie rien
  stop               Arrête backend et frontend + ferme la session tmux
                     Ne touche jamais à Supabase ni à Docker
  restart <svc>      Relance backend ou frontend dans sa fenêtre tmux
  logs <svc>         Suit un log : backend, frontend, supabase, alerts
  attach             S'attache à la session tmux existante

Options:
  --skip-tests       Sauter les tests backend + typecheck frontend
  --reset-db         Supprimer et recréer toutes les données Supabase
  --seed-only        Juste re-seeder les données (pas de build ni serveurs)
  --no-seed          Démarrer sans seeder les données
  --clean            Tout nettoyer (containers, node_modules, caches)
  --detach           Démarrer sans s'attacher à la session tmux
  --no-tmux          Forcer le mode processus en arrière-plan
  --no-backend       Ne pas démarrer le backend
  --no-frontend      Ne pas démarrer le frontend
  --verbose, -v      Afficher les logs dans la console (mode sans tmux)
  --help, -h         Afficher cette aide

Résilience:
  L'interpréteur Python est résolu en l'exécutant, pas en testant sa
  présence dans le PATH : venv du dépôt, puis python3, python,
  python3.12, python3.11, puis 'uv run python'. Un shim pyenv sans
  version installée est rejeté.
  pnpm est cherché dans le PATH puis via un shell de login (nvm en
  chargement paresseux ne l'expose pas autrement).
  Si un seul des deux manque, le service correspondant est sauté et
  le reste démarre. Le script ne s'arrête que si aucun ne peut tourner.

Variables:
  TMUX_SESSION       Nom de session tmux (défaut: gerersci)
  MONITOR_INTERVAL   Rafraîchissement du tableau de bord en s (défaut: 3)
  PYTHON_BIN_OVERRIDE  Forcer un interpréteur Python

Logs:
  Backend  → $BACKEND_LOG
  Frontend → $FRONTEND_LOG
  Alertes  → $ALERT_LOG
EOF
    exit 0
}

# ═════════════════════════════════════════════════════════════
#  PARSING
# ═════════════════════════════════════════════════════════════

SUBCOMMAND="start"
if [ $# -gt 0 ]; then
    case "$1" in
        start|status|stop|restart|logs|attach|doctor|__monitor-loop)
            SUBCOMMAND="$1"; shift ;;
    esac
fi

SUBCOMMAND_ARG="${1:-}"

for arg in "$@"; do
    case $arg in
        --skip-tests)   SKIP_TESTS=true ;;
        --reset-db)     RESET_DB=true ;;
        --seed-only)    SEED_ONLY=true ;;
        --no-seed)      NO_SEED=true ;;
        --clean)        CLEAN_ALL=true ;;
        --detach)       DETACH=true ;;
        --no-tmux)      NO_TMUX=true ;;
        --no-backend)   WANT_BACKEND=false ;;
        --no-frontend)  WANT_FRONTEND=false ;;
        --verbose|-v)   VERBOSE=true ;;
        --help|-h)      show_help ;;
    esac
done

case "$SUBCOMMAND" in
    __monitor-loop) monitor_loop ;;   # usage interne, fenêtre tmux
    attach)  cmd_attach ;;
    status)  cmd_status ;;
    doctor)  cmd_doctor ;;
    stop)    cmd_stop ;;
    restart) cmd_restart "$SUBCOMMAND_ARG" ;;
    logs)    cmd_logs "$SUBCOMMAND_ARG" ;;
esac

# ═════════════════════════════════════════════════════════════
#  À PARTIR D'ICI : SOUS-COMMANDE `start`
# ═════════════════════════════════════════════════════════════

cleanup() {
    # Ne s'applique qu'au chemin de repli sans tmux. En mode tmux les
    # services doivent survivre au détachement.
    [ "$USE_TMUX" = true ] && return
    [ "$SHUTTING_DOWN" = true ] && return
    SHUTTING_DOWN=true

    echo ""
    echo -e "${CYAN}  Arrêt des serveurs ...${NC}"

    for pid in "$TAIL_BACKEND_PID" "$TAIL_FRONTEND_PID" "$HEALTH_PID"; do
        [ -n "$pid" ] && kill "$pid" 2>/dev/null || true
    done
    for pid in "$BACKEND_PID" "$FRONTEND_PID"; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            pkill -TERM -P "$pid" 2>/dev/null || true
            kill "$pid" 2>/dev/null || true
        fi
    done
    for port in $BACKEND_PORT $FRONTEND_PORT; do
        lsof -ti:"$port" 2>/dev/null | xargs kill 2>/dev/null || true
    done
    sleep 1
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

echo -e "${BLUE}${BOLD}═══════════════════════════════════════════${NC}"
echo -e "${BLUE}${BOLD}  GererSCI — Build & Run supervisé${NC}"
echo -e "${BLUE}${BOLD}═══════════════════════════════════════════${NC}"
echo -e "${DIM}  $(date '+%Y-%m-%d %H:%M:%S') • logs → $LOG_DIR/${NC}"

# ── 0. Prérequis ─────────────────────────────────────────────
step_start "0/7" "Résolution des prérequis + libération ports ..."

# Durs : sans eux rien n'a de sens.
require_hard "docker" "https://docs.docker.com/get-docker/"
require_hard "supabase" "https://supabase.com/docs/guides/cli"

# Souples : on dégrade au lieu d'abandonner.
if [ "$WANT_BACKEND" = true ] && resolve_python; then
    if py -c 'import uvicorn' >/dev/null 2>&1; then
        CAN_BACKEND=true
        echo -e "  ${DIM}↳ python  : $(python_version_label)${NC}"
    else
        step_warn "uvicorn n'est pas importable — backend désactivé"
        echo -e "     ${DIM}$PYTHON_BIN -m pip install -r backend/requirements.txt${NC}"
    fi
elif [ "$WANT_BACKEND" = true ]; then
    step_warn "Aucun Python >= 3.11 utilisable — backend désactivé"
    echo -e "     ${DIM}python3 -m venv backend/.venv && backend/.venv/bin/pip install -r backend/requirements.txt${NC}"
else
    step_skip "backend (--no-backend)"
fi

if [ "$WANT_FRONTEND" = true ]; then
    if PNPM_BIN="$(resolve_node_cmd pnpm)"; then
        CAN_FRONTEND=true
        echo -e "  ${DIM}↳ pnpm    : $PNPM_BIN${NC}"
    else
        step_warn "pnpm introuvable même via shell de login — frontend désactivé"
        echo -e "     ${DIM}npm install -g pnpm${NC}"
    fi
else
    step_skip "frontend (--no-frontend)"
fi

if [ "$CAN_BACKEND" = false ] && [ "$CAN_FRONTEND" = false ]; then
    step_fail "Ni le backend ni le frontend ne peuvent démarrer"
    echo -e "  ${DIM}Lancez ./start-dev.sh doctor pour le détail${NC}"
    exit 1
fi

kill_port() {
    local port=$1 pids
    pids=$(lsof -ti:"$port" 2>/dev/null) || true
    if [ -n "$pids" ]; then
        echo "$pids" | xargs kill -9 2>/dev/null || true
        echo -e "  ${DIM}↳ Port $port libéré (PID: $(echo "$pids" | tr '\n' ' '))${NC}"
    fi
}

[ "$CAN_BACKEND" = true ]  && kill_port $BACKEND_PORT
[ "$CAN_FRONTEND" = true ] && kill_port $FRONTEND_PORT
for port in 5174 5175 5176 5177 5178 5179; do
    kill_port "$port"
done
sleep 1
step_ok "Prérequis résolus, ports libérés"

# ── 0b. Clean all si demandé ─────────────────────────────────
if [ "$CLEAN_ALL" = true ]; then
    step_start "clean" "Nettoyage complet ..."

    echo -e "  ${DIM}↳ Arrêt Supabase ...${NC}"
    cd "$ROOT" && supabase stop --no-backup 2>&1 | tail -2 || true

    for port in $BACKEND_PORT $FRONTEND_PORT 5174 5175 5176 5177 5178 5179; do
        lsof -ti:"$port" 2>/dev/null | xargs kill -9 2>/dev/null || true
    done

    echo -e "  ${DIM}↳ Suppression node_modules, .svelte-kit, caches Vite ...${NC}"
    rm -rf "$ROOT/frontend/node_modules"
    rm -rf "$ROOT/frontend/.svelte-kit"
    rm -rf "$ROOT/frontend/build"
    rm -rf "$ROOT/frontend/dist"

    echo -e "  ${DIM}↳ Suppression __pycache__, .pytest_cache, .mypy_cache ...${NC}"
    find "$ROOT/backend" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$ROOT/backend" -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find "$ROOT/backend" -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
    find "$ROOT/backend" -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true

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

docker_healthy() { docker info > /dev/null 2>&1; }

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
    echo -e "  ${DIM}Lancez OrbStack (orb start) ou Docker Desktop${NC}"
    exit 1
fi

if supabase_healthy; then
    step_ok "Supabase OK"
else
    step_warn "Supabase non disponible. Diagnostic ..."

    if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "supabase.*sci-manager"; then
        echo -e "  ${CYAN}↳ Containers Supabase détectés. Nettoyage ...${NC}"
        cd "$ROOT" && supabase stop --no-backup 2>&1 | tail -2 || true
        sleep 2
    fi

    SUPABASE_OK=false
    for attempt in 1 2 3; do
        if start_supabase "$attempt"; then
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
    if [ "$CAN_BACKEND" = false ]; then
        step_fail "Seed impossible : aucun Python utilisable"
        exit 1
    fi
    cd "$ROOT/backend"
    py scripts/seed_dev_data.py
    step_ok "Seed terminé. Serveurs non démarrés (--seed-only)."
    exit 0
fi

# ── 3. Backend: install deps ──────────────────────────────────
# Un Python système Homebrew ou Debian est « externally managed » (PEP 668) :
# pip y refuse toute installation, à raison. Plutôt que d'échouer, on crée un
# venv dédié et on s'y installe. resolve_python le préférera aux prochains runs.
if [ "$CAN_BACKEND" = true ]; then
    step_start "3/7" "Backend: installation dépendances ..."
    cd "$ROOT/backend"

    case "$PYTHON_BIN" in
        "$ROOT"/backend/.venv/bin/python|"$ROOT"/backend/venv/bin/python|"$ROOT"/.venv/bin/python)
            IN_VENV=true ;;
        *)  IN_VENV=false ;;
    esac

    DEPS_OK=false
    if py -m pip install -q -r requirements.txt >/dev/null 2>&1; then
        DEPS_OK=true
    elif [ "$IN_VENV" = false ]; then
        step_warn "Installation refusée (interpréteur externally-managed, PEP 668)"
        echo -e "  ${CYAN}↳ Création d'un venv dédié : backend/.venv ...${NC}"
        if "$PYTHON_BIN" -m venv "$ROOT/backend/.venv" >/dev/null 2>&1 \
           && [ -x "$ROOT/backend/.venv/bin/python" ]; then
            PYTHON_BIN="$ROOT/backend/.venv/bin/python"
            "$PYTHON_BIN" -m pip install -q --upgrade pip >/dev/null 2>&1 || true
            if "$PYTHON_BIN" -m pip install -q -r requirements.txt >/dev/null 2>&1; then
                DEPS_OK=true
                echo -e "  ${DIM}↳ venv : $(python_version_label)${NC}"
            fi
        fi
    fi

    if [ "$DEPS_OK" = true ]; then
        step_ok "Backend deps OK"
    else
        # Cohérence : sans dépendances, les tests et uvicorn échoueront de
        # toute façon. On désactive le backend au lieu de mourir deux étapes
        # plus loin, et le frontend démarre quand même.
        CAN_BACKEND=false
        step_warn "Dépendances backend indisponibles — backend désactivé"
        echo -e "     ${DIM}python3 -m venv backend/.venv && backend/.venv/bin/pip install -r backend/requirements.txt${NC}"
        if [ "$CAN_FRONTEND" = false ]; then
            step_fail "Plus aucun service ne peut démarrer"
            exit 1
        fi
    fi
else
    step_start "3/7" "Backend: dépendances"
    step_skip "backend indisponible"
fi

# ── 4. Backend: tests ─────────────────────────────────────────
if [ "$CAN_BACKEND" = true ] && [ "$SKIP_TESTS" = false ]; then
    step_start "4/7" "Backend: tests ..."
    cd "$ROOT/backend"
    set +e
    PYTHONPATH=. py -m pytest --tb=short -q 2>&1 | tail -10
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
if [ "$CAN_FRONTEND" = true ]; then
    step_start "5/7" "Frontend: clean install ..."
    cd "$ROOT/frontend"
    rm -rf .svelte-kit node_modules/.vite
    if ! "$PNPM_BIN" install --frozen-lockfile 2>&1 | tail -3; then
        step_fail "Échec installation dépendances frontend"
        exit 1
    fi
    step_ok "Frontend deps OK"

    if [ "$SKIP_TESTS" = false ]; then
        step_start "5b/7" "Frontend: type check ..."
        set +e
        "$PNPM_BIN" run check 2>&1 | tail -10
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
else
    step_start "5/7" "Frontend"
    step_skip "frontend indisponible"
fi

# ── 6. Seed données ──────────────────────────────────────────
if [ "$NO_SEED" = false ] && [ "$CAN_BACKEND" = true ]; then
    step_start "6/7" "Seed données de démonstration ..."
    cd "$ROOT/backend"
    if ! py scripts/seed_dev_data.py --clean; then
        step_warn "Seed échoué — serveurs démarrent sans données fraîches"
    fi
else
    step_start "6/7" "Seed données"
    if [ "$CAN_BACKEND" = false ]; then
        step_skip "seed (Python indisponible — utilisez le compte de supabase/seed.sql)"
    else
        step_skip "seed (--no-seed)"
    fi
fi

# ── 7. Démarrage des serveurs ─────────────────────────────────
step_start "7/7" "Démarrage des serveurs ..."

: > "$BACKEND_LOG"
: > "$FRONTEND_LOG"
date +%s > "$SESSION_START_FILE"
rm -f "$MONITOR_STATE"

if command -v tmux >/dev/null 2>&1 && [ "$NO_TMUX" = false ]; then
    USE_TMUX=true
fi

# ─────────────────────────────────────────────────────────────
#  MODE TMUX
# ─────────────────────────────────────────────────────────────
if [ "$USE_TMUX" = true ]; then

    if session_exists; then
        step_warn "Une session tmux '$SESSION' existe déjà"
        echo -e "  ${DIM}./start-dev.sh attach    s'y attacher${NC}"
        echo -e "  ${DIM}./start-dev.sh restart backend${NC}"
        echo -e "  ${DIM}./start-dev.sh stop      tout arrêter${NC}"
        exit 0
    fi

    # Fenêtre 0 : moniteur. Le script se ré-invoque en boucle interne.
    tmux new-session -d -s "$SESSION" -n monitor -c "$ROOT" \
        "'$ROOT/start-dev.sh' __monitor-loop"

    # Une fenêtre morte reste visible : on veut lire la trace du crash.
    tmux set-option -t "$SESSION" remain-on-exit on >/dev/null 2>&1 || true

    if [ "$CAN_BACKEND" = true ]; then
        PY_CMD="$PYTHON_BIN"
        if [ "$PYTHON_BIN" = "uv-run" ]; then
            tmux new-window -t "$SESSION:1" -n backend -c "$ROOT/backend" \
                "PYTHONPATH=. uv run python -m uvicorn app.main:app --reload --port $BACKEND_PORT 2>&1 | tee -a '$BACKEND_LOG'"
        else
            tmux new-window -t "$SESSION:1" -n backend -c "$ROOT/backend" \
                "PYTHONPATH=. '$PY_CMD' -m uvicorn app.main:app --reload --port $BACKEND_PORT 2>&1 | tee -a '$BACKEND_LOG'"
        fi
        echo -e "  ${DIM}↳ fenêtre 1 backend${NC}"
    fi

    if [ "$CAN_FRONTEND" = true ]; then
        tmux new-window -t "$SESSION:2" -n frontend -c "$ROOT/frontend" \
            "VITE_API_URL=http://localhost:$BACKEND_PORT '$PNPM_BIN' run dev -- --port $FRONTEND_PORT --strictPort 2>&1 | tee -a '$FRONTEND_LOG'"
        echo -e "  ${DIM}↳ fenêtre 2 frontend${NC}"
    fi

    if docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^${SUPABASE_DB_CONTAINER}$"; then
        tmux new-window -t "$SESSION:3" -n supabase -c "$ROOT" \
            "docker logs -f --tail 50 '$SUPABASE_DB_CONTAINER'"
        echo -e "  ${DIM}↳ fenêtre 3 supabase${NC}"
    fi

    tmux new-window -t "$SESSION:4" -n shell -c "$ROOT"
    tmux select-window -t "$SESSION:0" >/dev/null 2>&1 || true

    # Attente de disponibilité, sans bloquer indéfiniment.
    echo ""
    B_OK=false; F_OK=false
    [ "$CAN_BACKEND"  = true ] || B_OK=true
    [ "$CAN_FRONTEND" = true ] || F_OK=true
    for i in $(seq 1 45); do
        sleep 1
        if [ "$B_OK" = false ]; then
            r="$(probe_http "http://localhost:$BACKEND_PORT/health/live" 2)"
            [ "${r%% *}" != "000" ] && B_OK=true
        fi
        if [ "$F_OK" = false ]; then
            r="$(probe_http "http://localhost:$FRONTEND_PORT" 2)"
            [ "${r%% *}" != "000" ] && F_OK=true
        fi
        bs=$( [ "$B_OK" = true ] && echo "✓" || echo "…" )
        fs=$( [ "$F_OK" = true ] && echo "✓" || echo "…" )
        echo -ne "  ${CYAN}·${NC} Backend [$bs]  Frontend [$fs]  (${i}s)    \r"
        [ "$B_OK" = true ] && [ "$F_OK" = true ] && break
    done
    echo ""

    [ "$B_OK" = false ] && step_warn "Backend sans réponse après 45s — voir la fenêtre 1"
    [ "$F_OK" = false ] && step_warn "Frontend sans réponse après 45s — voir la fenêtre 2"

    echo ""
    echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}${BOLD}  GererSCI supervisé dans tmux « $SESSION »${NC}"
    echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${BOLD}Services${NC}"
    [ "$CAN_FRONTEND" = true ] && echo -e "  Frontend    http://localhost:$FRONTEND_PORT"
    [ "$CAN_BACKEND"  = true ] && echo -e "  Backend     http://localhost:$BACKEND_PORT"
    [ "$CAN_BACKEND"  = true ] && echo -e "  API Docs    http://localhost:$BACKEND_PORT/docs"
    echo -e "  Supabase    http://localhost:$SUPABASE_STUDIO_PORT"
    echo -e "  Mailpit     http://localhost:$MAILPIT_PORT"
    echo ""
    echo -e "  ${BOLD}Compte de test${NC}"
    echo -e "  📧 test@gerersci.fr  🔑 testpassword123   ${DIM}(supabase/seed.sql, sans Python)${NC}"
    if [ "$CAN_BACKEND" = true ]; then
        echo -e "  ${DIM}demo@gerersci.fr / password123 après seed_dev_data.py${NC}"
    fi
    echo ""
    echo -e "  ${BOLD}Pilotage${NC}"
    echo -e "  ${CYAN}./start-dev.sh status${NC}    état en une passe"
    echo -e "  ${CYAN}./start-dev.sh attach${NC}    revenir au tableau de bord"
    echo -e "  ${CYAN}./start-dev.sh restart backend${NC}"
    echo -e "  ${CYAN}./start-dev.sh stop${NC}      arrêter (Supabase reste debout)"
    echo -e "${BLUE}${BOLD}═══════════════════════════════════════════════════${NC}"
    echo ""

    if [ "$DETACH" = true ]; then
        echo -e "  ${DIM}Session détachée. ./start-dev.sh attach pour la rejoindre.${NC}"
        exit 0
    fi

    exec tmux attach -t "$SESSION"
fi

# ─────────────────────────────────────────────────────────────
#  CHEMIN DE REPLI : processus en arrière-plan (tmux absent)
# ─────────────────────────────────────────────────────────────
step_warn "tmux indisponible — mode processus en arrière-plan"

if [ "$CAN_BACKEND" = true ]; then
    cd "$ROOT/backend"
    if [ "$VERBOSE" = true ]; then
        PYTHONPATH=. "$PYTHON_BIN" -m uvicorn app.main:app --reload --port $BACKEND_PORT 2>&1 | tee "$BACKEND_LOG" &
    else
        PYTHONPATH=. "$PYTHON_BIN" -m uvicorn app.main:app --reload --port $BACKEND_PORT > "$BACKEND_LOG" 2>&1 &
    fi
    BACKEND_PID=$!
fi

if [ "$CAN_FRONTEND" = true ]; then
    cd "$ROOT/frontend"
    export VITE_API_URL="http://localhost:$BACKEND_PORT"
    if [ "$VERBOSE" = true ]; then
        "$PNPM_BIN" run dev -- --port $FRONTEND_PORT --strictPort 2>&1 | tee "$FRONTEND_LOG" &
    else
        "$PNPM_BIN" run dev -- --port $FRONTEND_PORT --strictPort > "$FRONTEND_LOG" 2>&1 &
    fi
    FRONTEND_PID=$!
fi

echo -e "  ${DIM}Backend PID=${BACKEND_PID:-none} • Frontend PID=${FRONTEND_PID:-none}${NC}"

BACKEND_OK=false
FRONTEND_OK=false
[ "$CAN_BACKEND"  = true ] || BACKEND_OK=true
[ "$CAN_FRONTEND" = true ] || FRONTEND_OK=true

for i in $(seq 1 45); do
    sleep 1
    if [ "$CAN_BACKEND" = true ] && [ "$BACKEND_OK" = false ] && ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo ""; step_fail "Le backend a crashé au démarrage"
        tail -10 "$BACKEND_LOG" 2>/dev/null | sed 's/^/  /' || true
        exit 1
    fi
    if [ "$CAN_FRONTEND" = true ] && [ "$FRONTEND_OK" = false ] && ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo ""; step_fail "Le frontend a crashé au démarrage"
        tail -10 "$FRONTEND_LOG" 2>/dev/null | sed 's/^/  /' || true
        exit 1
    fi

    [ "$BACKEND_OK"  = false ] && curl -sf --max-time 2 "http://localhost:$BACKEND_PORT/health/live" >/dev/null 2>&1 && BACKEND_OK=true
    [ "$FRONTEND_OK" = false ] && curl -sf --max-time 2 "http://localhost:$FRONTEND_PORT" >/dev/null 2>&1 && FRONTEND_OK=true

    bs=$( [ "$BACKEND_OK" = true ] && echo "✓" || echo "…" )
    fs=$( [ "$FRONTEND_OK" = true ] && echo "✓" || echo "…" )
    echo -ne "  ${CYAN}·${NC} Backend [$bs]  Frontend [$fs]  (${i}s)    \r"
    [ "$BACKEND_OK" = true ] && [ "$FRONTEND_OK" = true ] && { echo ""; break; }
done

render_dashboard || true
echo ""
echo -e "  ${BOLD}Compte de test${NC}  📧 test@gerersci.fr  🔑 testpassword123"
echo -e "  ${CYAN}Ctrl+C${NC} pour arrêter"
echo ""

[ "$CAN_BACKEND"  = true ] && { tail -n 0 -f "$BACKEND_LOG"  2>/dev/null | sed -u "s/^/$(printf "${YELLOW}[backend]${NC} ")/" & TAIL_BACKEND_PID=$!; }
[ "$CAN_FRONTEND" = true ] && { tail -n 0 -f "$FRONTEND_LOG" 2>/dev/null | sed -u "s/^/$(printf "${CYAN}[frontend]${NC} ")/" & TAIL_FRONTEND_PID=$!; }

(
    while true; do
        sleep 5
        detect_transitions
        if [ -n "$BACKEND_PID" ] && ! kill -0 "$BACKEND_PID" 2>/dev/null; then
            echo -e "\n${RED}  ⚠ Backend arrêté${NC}"
            tail -5 "$BACKEND_LOG" 2>/dev/null | sed 's/^/    /'
        fi
        if [ -n "$FRONTEND_PID" ] && ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
            echo -e "\n${RED}  ⚠ Frontend arrêté${NC}"
            tail -5 "$FRONTEND_LOG" 2>/dev/null | sed 's/^/    /'
        fi
    done
) &
HEALTH_PID=$!

wait ${BACKEND_PID:-} ${FRONTEND_PID:-} 2>/dev/null || true
kill "$TAIL_BACKEND_PID" "$TAIL_FRONTEND_PID" "$HEALTH_PID" 2>/dev/null || true
