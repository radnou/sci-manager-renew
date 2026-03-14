#!/bin/bash
set -euo pipefail

# GererSCI — Rollback Script
# ----------------------------
# Rolls back to the previous deployment by restoring Docker image tags
# saved in .deploy-history during the last deploy.
#
# Usage: ./scripts/rollback.sh
#
# The deploy process should append image digests to .deploy-history
# before building new images. This script reads the previous entry
# and restores those images.

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

HISTORY_FILE=".deploy-history"

# --- Save current state (pre-deploy hook) ---
# Call with: ./scripts/rollback.sh --save
if [ "${1:-}" = "--save" ]; then
    echo -e "${GREEN}Saving current image state...${NC}"
    BACKEND_IMG=$(docker compose images backend --format '{{.Repository}}:{{.Tag}}' 2>/dev/null | head -1)
    FRONTEND_IMG=$(docker compose images frontend --format '{{.Repository}}:{{.Tag}}' 2>/dev/null | head -1)
    TIMESTAMP=$(date +%Y%m%d-%H%M%S)

    echo "${TIMESTAMP}|${BACKEND_IMG}|${FRONTEND_IMG}" >> "$HISTORY_FILE"
    echo -e "${GREEN}Saved: backend=${BACKEND_IMG} frontend=${FRONTEND_IMG}${NC}"
    exit 0
fi

# --- Rollback ---
if [ ! -f "$HISTORY_FILE" ]; then
    echo -e "${RED}ERROR: No deploy history found (${HISTORY_FILE} missing).${NC}"
    echo -e "Run ${YELLOW}./scripts/rollback.sh --save${NC} before deploying to create a restore point."
    exit 1
fi

# Read the last entry
LAST_ENTRY=$(tail -1 "$HISTORY_FILE")
TIMESTAMP=$(echo "$LAST_ENTRY" | cut -d'|' -f1)
BACKEND_IMG=$(echo "$LAST_ENTRY" | cut -d'|' -f2)
FRONTEND_IMG=$(echo "$LAST_ENTRY" | cut -d'|' -f3)

if [ -z "$BACKEND_IMG" ] || [ -z "$FRONTEND_IMG" ]; then
    echo -e "${RED}ERROR: Deploy history is malformed.${NC}"
    echo -e "Expected format: timestamp|backend_image|frontend_image"
    exit 1
fi

echo -e "${YELLOW}=== Rolling back to deploy from ${TIMESTAMP} ===${NC}"
echo -e "  Backend:  ${BACKEND_IMG}"
echo -e "  Frontend: ${FRONTEND_IMG}"
echo ""

read -rp "Proceed with rollback? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
    echo "Rollback cancelled."
    exit 0
fi

echo -e "${GREEN}Stopping current services...${NC}"
docker compose down

echo -e "${GREEN}Starting services with previous images...${NC}"
BACKEND_IMAGE="$BACKEND_IMG" FRONTEND_IMAGE="$FRONTEND_IMG" docker compose up -d

echo ""
echo -e "${GREEN}Waiting for services to start...${NC}"
sleep 10

echo -e "${GREEN}Service status:${NC}"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo -e "${GREEN}=== Rollback complete ===${NC}"
