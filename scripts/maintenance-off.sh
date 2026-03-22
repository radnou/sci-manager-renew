#!/bin/bash
# Desactive le mode maintenance sur le VPS
# Usage: ./scripts/maintenance-off.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "==> Desactivation du mode maintenance..."

# Supprimer le flag local
rm -f "$PROJECT_DIR/docker/maintenance.flag"

# Supprimer le flag dans le container nginx
docker exec gerersci_nginx rm -f /etc/nginx/maintenance.flag 2>/dev/null || true

echo ""
echo "============================================"
echo "  MODE MAINTENANCE DESACTIVE"
echo "============================================"
echo "  Le site est de nouveau accessible."
echo "============================================"
