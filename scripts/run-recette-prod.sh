#!/bin/bash
set -e

# ─── GérerSCI — Recette automatique sur production ──────────
#
# Usage:
#   ./scripts/run-recette-prod.sh
#
# Pré-requis:
#   - Supabase prod accessible
#   - Compte démo radnoumane@gerersci.fr avec mot de passe
#   - Playwright installé (pnpm exec playwright install chromium)
#
# Variables d'environnement (auto-détectées ou configurables):
#   E2E_AUTH_TOKEN    JWT token (auto-obtenu via Supabase login)
#   E2E_SCI_ID        ID de la SCI Belleville
#   E2E_SCI_ID_2      ID de la SCI Montsouris
#   E2E_BIEN_ID       ID d'un bien
#   E2E_BASE_URL      URL de base (default: https://gerersci.fr)
# ─────────────────────────────────────────────────────────────

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

SUPABASE_URL="${SUPABASE_URL:-https://api.gerersci.fr}"
SUPABASE_ANON_KEY="${SUPABASE_ANON_KEY:-}"
DEMO_EMAIL="${DEMO_EMAIL:-radnoumane@gerersci.fr}"
DEMO_PASSWORD="${DEMO_PASSWORD:-}"

# IDs du compte démo
export E2E_SCI_ID="${E2E_SCI_ID:-98d2ef33-92c0-43d7-9c71-d3f0acd95dd7}"
export E2E_SCI_ID_2="${E2E_SCI_ID_2:-93109c6d-b845-4d67-ab27-99445db662c4}"
export E2E_BIEN_ID="${E2E_BIEN_ID:-f80f8234-2a83-4ad9-a3d2-94eee688b5cb}"
export E2E_BASE_URL="${E2E_BASE_URL:-https://gerersci.fr}"

echo -e "${CYAN}══════════════════════════════════════════════${NC}"
echo -e "${CYAN}   GérerSCI — Recette Automatique (Prod)${NC}"
echo -e "${CYAN}══════════════════════════════════════════════${NC}"
echo ""

# ─── Step 1: Obtenir le JWT ─────────────────────────────────

if [ -z "$E2E_AUTH_TOKEN" ]; then
    if [ -z "$SUPABASE_ANON_KEY" ]; then
        echo -e "${YELLOW}⚠ SUPABASE_ANON_KEY non défini.${NC}"
        echo "  Fournir: export SUPABASE_ANON_KEY=<votre clé>"
        echo "  Ou:      export E2E_AUTH_TOKEN=<jwt token>"
        echo ""
        echo "  Pour obtenir un token manuellement:"
        echo "  curl -X POST '$SUPABASE_URL/auth/v1/token?grant_type=password' \\"
        echo "    -H 'apikey: <ANON_KEY>' -H 'Content-Type: application/json' \\"
        echo "    -d '{\"email\":\"$DEMO_EMAIL\",\"password\":\"<MOT_DE_PASSE>\"}'"
        exit 1
    fi

    if [ -z "$DEMO_PASSWORD" ]; then
        echo -e "${YELLOW}⚠ DEMO_PASSWORD non défini.${NC}"
        echo "  Fournir: export DEMO_PASSWORD=<mot de passe du compte démo>"
        exit 1
    fi

    echo -e "${CYAN}→ Authentification Supabase...${NC}"
    TOKEN_RESPONSE=$(curl -s -X POST "${SUPABASE_URL}/auth/v1/token?grant_type=password" \
        -H "apikey: ${SUPABASE_ANON_KEY}" \
        -H "Content-Type: application/json" \
        -d "{\"email\":\"${DEMO_EMAIL}\",\"password\":\"${DEMO_PASSWORD}\"}")

    E2E_AUTH_TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)

    if [ -z "$E2E_AUTH_TOKEN" ]; then
        echo -e "${RED}✗ Login échoué.${NC}"
        echo "$TOKEN_RESPONSE" | head -3
        exit 1
    fi
    echo -e "${GREEN}✓ Token obtenu${NC}"
fi

export E2E_AUTH_TOKEN

# ─── Step 2: Lancer Playwright ──────────────────────────────

echo ""
echo -e "${CYAN}→ Lancement Playwright (15 modules de test)...${NC}"
echo -e "  Base URL: ${E2E_BASE_URL}"
echo -e "  SCI 1:    ${E2E_SCI_ID}"
echo -e "  SCI 2:    ${E2E_SCI_ID_2}"
echo -e "  Bien:     ${E2E_BIEN_ID}"
echo ""

cd "$(dirname "$0")/../frontend"

# Ensure screenshots dir exists
mkdir -p e2e-artifacts/recette

# Run the recette
pnpm exec playwright test \
    --config e2e/playwright.production.config.ts \
    e2e/production/recette-complete.spec.ts \
    --reporter=list \
    "$@"

EXIT_CODE=$?

# ─── Step 3: Rapport ────────────────────────────────────────

echo ""
echo -e "${CYAN}══════════════════════════════════════════════${NC}"
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}   ✅ RECETTE RÉUSSIE — Tous les tests passent${NC}"
else
    echo -e "${RED}   ❌ RECETTE ÉCHOUÉE — Voir le rapport ci-dessus${NC}"
fi
echo -e "${CYAN}══════════════════════════════════════════════${NC}"
echo ""
echo "Screenshots: frontend/e2e-artifacts/recette/"
echo "Rapport HTML: pnpm exec playwright show-report playwright-report/production"
echo ""

exit $EXIT_CODE
