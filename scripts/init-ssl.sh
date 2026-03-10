#!/bin/bash
set -e

# GererSCI — Initial SSL Certificate Setup
# Run this ONCE on the VPS before starting the full stack.
#
# Prerequisites:
# - DNS A records for all domains pointing to this VPS
# - Ports 80 and 443 open (UFW configured)
# - Docker installed and running

DOMAINS=(
    "gerersci.fr"
    "www.gerersci.fr"
    "app.gerersci.fr"
    "api.gerersci.fr"
    "analytics.gerersci.fr"
    "status.gerersci.fr"
    "staging.gerersci.fr"
)

EMAIL="${CERTBOT_EMAIL:-admin@gerersci.fr}"
STAGING_FLAG="${CERTBOT_STAGING:-0}"  # Set to 1 for testing

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== GererSCI SSL Certificate Setup ===${NC}"

# Check DNS resolution
echo -e "${YELLOW}Checking DNS resolution...${NC}"
VPS_IP=$(curl -s ifconfig.me)
echo -e "VPS IP: ${GREEN}${VPS_IP}${NC}"

for domain in "${DOMAINS[@]}"; do
    resolved=$(dig +short "$domain" 2>/dev/null | head -1)
    if [ "$resolved" = "$VPS_IP" ]; then
        echo -e "  ${GREEN}✓${NC} $domain → $resolved"
    else
        echo -e "  ${RED}✗${NC} $domain → $resolved (expected $VPS_IP)"
        echo -e "${RED}DNS not ready for $domain. Fix DNS and retry.${NC}"
        exit 1
    fi
done

# Stop any services using port 80
echo -e "${YELLOW}Stopping services on port 80...${NC}"
docker compose down 2>/dev/null || true
sudo systemctl stop nginx 2>/dev/null || true

# Build domain args
DOMAIN_ARGS=""
for domain in "${DOMAINS[@]}"; do
    DOMAIN_ARGS="$DOMAIN_ARGS -d $domain"
done

# Staging flag for testing
STAGING_ARG=""
if [ "$CERTBOT_STAGING" = "1" ]; then
    STAGING_ARG="--staging"
    echo -e "${YELLOW}Using Let's Encrypt STAGING (test certificates)${NC}"
fi

# Request certificate using standalone mode
echo -e "${GREEN}Requesting SSL certificate...${NC}"
docker run --rm \
    -p 80:80 \
    -v gerersci_certbot_conf:/etc/letsencrypt \
    -v gerersci_certbot_www:/var/www/certbot \
    certbot/certbot certonly \
    --standalone \
    $STAGING_ARG \
    $DOMAIN_ARGS \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    --force-renewal

echo -e "${GREEN}=== SSL Certificate obtained successfully! ===${NC}"
echo ""
echo -e "Certificate location: /etc/letsencrypt/live/gerersci.fr/"
echo -e ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Copy your .env file:  cp .env.production.example .env"
echo -e "2. Edit secrets:         nano .env"
echo -e "3. Start all services:   docker compose up -d"
echo -e "4. Check status:         docker compose ps"
echo -e "5. Check health:         curl https://api.gerersci.fr/health/live"
