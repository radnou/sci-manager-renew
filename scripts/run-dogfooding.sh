#!/bin/bash
set -e

# ─── GérerSCI — QA Dogfooding (Level 2) ──────────────────────
#
# Parcours métier complets simulant un utilisateur réel.
# Plus profond que le smoke : vérifie cohérence données, CRUD, PDF, console.
#
# Usage:
#   ./scripts/run-dogfooding.sh              # dogfooding seul
#   ./scripts/run-dogfooding.sh --all        # dogfooding + recette complète
#   ./scripts/run-dogfooding.sh --smoke      # smoke + dogfooding
#
# Prérequis:
#   export DEMO_PASSWORD=<password>
#   export SUPABASE_ANON_KEY=<key>          # ou E2E_EMAIL + E2E_PASSWORD
# ─────────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

SUPABASE_URL="${SUPABASE_URL:-https://api.gerersci.fr}"
SUPABASE_ANON_KEY="${SUPABASE_ANON_KEY:-}"
DEMO_EMAIL="${DEMO_EMAIL:-radnoumane@gerersci.fr}"
DEMO_PASSWORD="${DEMO_PASSWORD:-}"

export E2E_SCI_ID="${E2E_SCI_ID:-98d2ef33-92c0-43d7-9c71-d3f0acd95dd7}"
export E2E_SCI_ID_2="${E2E_SCI_ID_2:-93109c6d-b845-4d67-ab27-99445db662c4}"
export E2E_BIEN_ID="${E2E_BIEN_ID:-f80f8234-2a83-4ad9-a3d2-94eee688b5cb}"
export E2E_BASE_URL="${E2E_BASE_URL:-https://gerersci.fr}"
export E2E_API_BASE_URL="${E2E_API_BASE_URL:-https://api.gerersci.fr}"

MODE="dogfooding"
if [ "$1" = "--all" ]; then MODE="all"; fi
if [ "$1" = "--smoke" ]; then MODE="smoke+dogfooding"; fi

echo -e "${CYAN}${BOLD}══════════════════════════════════════════════${NC}"
echo -e "${CYAN}${BOLD}   🐕 GérerSCI — QA Dogfooding${NC}"
echo -e "${CYAN}${BOLD}══════════════════════════════════════════════${NC}"
echo -e "  Mode: ${YELLOW}${MODE}${NC}"
echo -e "  Date: $(date '+%Y-%m-%d %H:%M')"
echo ""

# ─── Auth ──────────────────────────────────────────────────────

if [ -n "$E2E_EMAIL" ] && [ -n "$E2E_PASSWORD" ]; then
    echo -e "${GREEN}✓ Auth via E2E_EMAIL/E2E_PASSWORD${NC}"
    export E2E_EMAIL E2E_PASSWORD
elif [ -n "$E2E_AUTH_TOKEN" ]; then
    echo -e "${GREEN}✓ Auth via E2E_AUTH_TOKEN${NC}"
elif [ -n "$SUPABASE_ANON_KEY" ] && [ -n "$DEMO_PASSWORD" ]; then
    echo -e "${CYAN}→ Authentification Supabase...${NC}"
    TOKEN_RESPONSE=$(curl -s -X POST "${SUPABASE_URL}/auth/v1/token?grant_type=password" \
        -H "apikey: ${SUPABASE_ANON_KEY}" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"${DEMO_EMAIL}\",\"password\":\"${DEMO_PASSWORD}\"}")

    export E2E_EMAIL="$DEMO_EMAIL"
    export E2E_PASSWORD="$DEMO_PASSWORD"
    echo -e "${GREEN}✓ Credentials configurées${NC}"
else
    echo -e "${YELLOW}⚠ Pas de credentials auth.${NC}"
    echo "  Les tests authentifiés seront skippés."
    echo ""
    echo "  Options:"
    echo "    export E2E_EMAIL=demo@gerersci.fr E2E_PASSWORD=<password>"
    echo "    export SUPABASE_ANON_KEY=<key> DEMO_PASSWORD=<password>"
    echo ""
fi

cd "$(dirname "$0")/../frontend"
mkdir -p e2e-artifacts/dogfooding

TOTAL_EXIT=0

# ─── Level 1: Smoke (si --smoke ou --all) ─────────────────────

if [ "$MODE" = "smoke+dogfooding" ] || [ "$MODE" = "all" ]; then
    echo ""
    echo -e "${CYAN}━━━ Level 1: Smoke Public ━━━${NC}"
    pnpm exec playwright test \
        --config e2e/playwright.production.config.ts \
        e2e/production/smoke-public.spec.ts \
        --reporter=list || TOTAL_EXIT=1
fi

# ─── Level 2: Dogfooding ──────────────────────────────────────

echo ""
echo -e "${CYAN}━━━ Level 2: Dogfooding Automatisé ━━━${NC}"
pnpm exec playwright test \
    --config e2e/playwright.production.config.ts \
    e2e/production/dogfooding.spec.ts \
    --reporter=list || TOTAL_EXIT=1

# ─── Level 2+: Recette complète (si --all) ────────────────────

if [ "$MODE" = "all" ]; then
    echo ""
    echo -e "${CYAN}━━━ Recette Complète (15 modules) ━━━${NC}"
    pnpm exec playwright test \
        --config e2e/playwright.production.config.ts \
        e2e/production/recette-complete.spec.ts \
        --reporter=list || TOTAL_EXIT=1
fi

# ─── Rapport ───────────────────────────────────────────────────

echo ""
echo -e "${CYAN}${BOLD}══════════════════════════════════════════════${NC}"
if [ $TOTAL_EXIT -eq 0 ]; then
    echo -e "${GREEN}${BOLD}   ✅ DOGFOODING RÉUSSI${NC}"
else
    echo -e "${RED}${BOLD}   ❌ FINDINGS DÉTECTÉS — Voir rapport${NC}"
fi
echo -e "${CYAN}${BOLD}══════════════════════════════════════════════${NC}"
echo ""
echo "  Screenshots : frontend/e2e-artifacts/dogfooding/"
echo "  Rapport HTML: cd frontend && pnpm exec playwright show-report playwright-report/production"
echo ""

exit $TOTAL_EXIT
