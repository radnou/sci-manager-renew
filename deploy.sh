#!/bin/bash
set -e

# GererSCI — Production Deployment Script
# Usage: ./deploy.sh [--initial] [--with-staging]
#
# --initial      First-time setup (installs Docker, configures firewall, gets SSL)
# --with-staging Also deploy the staging environment

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

INITIAL=false
WITH_STAGING=false

for arg in "$@"; do
    case $arg in
        --initial) INITIAL=true ;;
        --with-staging) WITH_STAGING=true ;;
    esac
done

echo -e "${GREEN}=== GererSCI Deployment ===${NC}"

# ------------------------------------------------------------------
# INITIAL SETUP (first time only)
# ------------------------------------------------------------------
if [ "$INITIAL" = true ]; then
    echo -e "${YELLOW}Running initial server setup...${NC}"

    # Update system
    sudo apt update && sudo apt upgrade -y

    # Install dependencies
    sudo apt install -y apt-transport-https ca-certificates curl gnupg lsb-release \
        ufw fail2ban dnsutils jq

    # Install Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${GREEN}Installing Docker...${NC}"
        curl -fsSL https://get.docker.com | sudo sh
        sudo usermod -aG docker "$USER"
        sudo systemctl enable --now docker
    fi

    # Configure firewall
    echo -e "${GREEN}Configuring firewall...${NC}"
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow OpenSSH
    sudo ufw allow 80/tcp
    sudo ufw allow 443/tcp
    sudo ufw --force enable

    # Configure fail2ban
    sudo systemctl enable --now fail2ban

    # Harden SSH
    echo -e "${YELLOW}Hardening SSH...${NC}"
    sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak.$(date +%s)
    sudo sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
    # Note: enable key-only auth after setting up SSH keys
    # sudo sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
    sudo systemctl reload ssh

    # Create app directory
    sudo mkdir -p /opt/gerersci
    sudo chown -R "$USER":"$USER" /opt/gerersci

    echo -e "${GREEN}Initial setup complete.${NC}"
    echo -e "${YELLOW}Next: clone the repo to /opt/gerersci, configure .env, run init-ssl.sh${NC}"
    exit 0
fi

# ------------------------------------------------------------------
# DEPLOYMENT
# ------------------------------------------------------------------

# Check .env exists
if [ ! -f .env ]; then
    echo -e "${RED}ERROR: .env file not found!${NC}"
    echo -e "Run: cp .env.production.example .env && nano .env"
    exit 1
fi

# Check SSL certificates exist
if [ ! -d "/var/lib/docker/volumes/gerersci_certbot_conf/_data/live/gerersci.fr" ] && \
   [ ! -d "$(docker volume inspect gerersci_certbot_conf --format '{{.Mountpoint}}' 2>/dev/null)/live/gerersci.fr" ]; then
    # Try to check inside the volume
    CERT_CHECK=$(docker run --rm -v gerersci_certbot_conf:/etc/letsencrypt alpine ls /etc/letsencrypt/live/gerersci.fr/fullchain.pem 2>/dev/null || echo "MISSING")
    if [ "$CERT_CHECK" = "MISSING" ]; then
        echo -e "${YELLOW}WARNING: SSL certificates not found. Run scripts/init-ssl.sh first.${NC}"
        echo -e "Continuing with HTTP only..."
    fi
fi

# Pull latest code (if in git repo)
if [ -d .git ]; then
    echo -e "${GREEN}Pulling latest code...${NC}"
    git pull origin main 2>/dev/null || echo -e "${YELLOW}Git pull skipped${NC}"
fi

# Build and deploy
echo -e "${GREEN}Building and deploying...${NC}"

if [ "$WITH_STAGING" = true ]; then
    echo -e "${YELLOW}Including staging environment...${NC}"
    docker compose -f docker-compose.yml -f docker-compose.staging.yml build
    docker compose -f docker-compose.yml -f docker-compose.staging.yml up -d
else
    docker compose build
    docker compose up -d
fi

# Wait for services
echo -e "${GREEN}Waiting for services to start...${NC}"
sleep 15

# Health checks
echo -e "${GREEN}Running health checks...${NC}"
echo ""

check_service() {
    local name=$1
    local url=$2
    local result
    result=$(curl -sf --max-time 10 "$url" 2>/dev/null || echo "FAIL")
    if echo "$result" | grep -qi "FAIL\|error\|refused"; then
        echo -e "  ${RED}✗${NC} $name — FAILED"
        return 1
    else
        echo -e "  ${GREEN}✓${NC} $name — OK"
        return 0
    fi
}

FAILURES=0
check_service "Backend liveness" "http://localhost:8000/health/live" || ((FAILURES++))
check_service "Backend readiness" "http://localhost:8000/health/ready" || ((FAILURES++))
check_service "Frontend" "http://localhost:4173/" || ((FAILURES++))
check_service "Nginx" "http://localhost:80/nginx-health" || ((FAILURES++))

echo ""
echo -e "${GREEN}Service status:${NC}"
docker compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

if [ $FAILURES -gt 0 ]; then
    echo ""
    echo -e "${RED}$FAILURES health check(s) failed. Check logs:${NC}"
    echo -e "  docker compose logs backend --tail=50"
    echo -e "  docker compose logs frontend --tail=50"
    echo -e "  docker compose logs nginx --tail=50"
    exit 1
fi

echo ""
echo -e "${GREEN}=== Deployment successful! ===${NC}"
echo -e "  Frontend: https://app.gerersci.fr"
echo -e "  API:      https://api.gerersci.fr"
echo -e "  Matomo:   https://analytics.gerersci.fr"
echo -e "  Status:   https://status.gerersci.fr"
