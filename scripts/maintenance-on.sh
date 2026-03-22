#!/bin/bash
# Active le mode maintenance sur le VPS
# Usage: ./scripts/maintenance-on.sh
#
# Fonctionne en ajoutant un fichier flag que nginx detecte.
# Les requetes vers /api/v1/stripe/webhooks passent toujours (Stripe ne doit pas perdre d'events).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "==> Activation du mode maintenance..."

# Creer le flag de maintenance
touch "$PROJECT_DIR/docker/maintenance.flag"

# Copier la page de maintenance dans le volume nginx
docker cp "$PROJECT_DIR/docker/maintenance.html" gerersci_nginx:/usr/share/nginx/html/maintenance.html 2>/dev/null || true

# Recharger nginx avec la config de maintenance
docker exec gerersci_nginx sh -c '
cat > /tmp/maintenance.conf << "MCONF"
# Maintenance mode: serve static page for all requests
# EXCEPT Stripe webhooks (critical payment events)
if (-f /etc/nginx/maintenance.flag) {
    set $maintenance 1;
}
if ($uri ~* ^/api/v1/stripe/webhooks) {
    set $maintenance 0;
}
if ($uri ~* ^/api/v1/health) {
    set $maintenance 0;
}
if ($maintenance = 1) {
    return 503;
}
MCONF
'

# Creer le flag dans le container
docker exec gerersci_nginx touch /etc/nginx/maintenance.flag

# Creer la page 503 custom
docker exec gerersci_nginx sh -c 'mkdir -p /usr/share/nginx/html'

echo ""
echo "============================================"
echo "  MODE MAINTENANCE ACTIF"
echo "============================================"
echo ""
echo "  Les visiteurs voient la page de maintenance."
echo "  Les webhooks Stripe continuent de fonctionner."
echo "  Le health check reste accessible."
echo ""
echo "  Pour desactiver: ./scripts/maintenance-off.sh"
echo "============================================"
