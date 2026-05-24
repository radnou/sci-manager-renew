#!/bin/bash
set -e

# GererSCI — Production Deployment Script
# Usage: ./deploy.sh [--initial] [--caddy] [--no-maintenance]
#
# --initial           First-time setup (installs Docker, configures firewall)
# --caddy             Use Caddy instead of nginx (auto-HTTPS)
# --no-maintenance    Skip maintenance page during deploy

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

INITIAL=false
USE_CADDY=false
NO_MAINTENANCE=false
MAINTENANCE_FILE="/tmp/gerersci-maintenance"

for arg in "$@"; do
    case $arg in
        --initial) INITIAL=true ;;
        --caddy) USE_CADDY=true ;;
        --no-maintenance) NO_MAINTENANCE=true ;;
    esac
done

echo -e "${GREEN}=== GererSCI Deployment ===${NC}"

# ------------------------------------------------------------------
# MAINTENANCE MODE HELPERS
# ------------------------------------------------------------------
enable_maintenance() {
    if [ "$NO_MAINTENANCE" = true ]; then return; fi
    echo -e "${CYAN}Enabling maintenance page...${NC}"
    touch "$MAINTENANCE_FILE"
    # Copy flag into Caddy/nginx-visible location
    docker exec gerersci_caddy sh -c 'touch /tmp/maintenance' 2>/dev/null || \
    docker exec gerersci_nginx sh -c 'touch /tmp/maintenance' 2>/dev/null || true
}

disable_maintenance() {
    if [ "$NO_MAINTENANCE" = true ]; then return; fi
    echo -e "${CYAN}Disabling maintenance page...${NC}"
    rm -f "$MAINTENANCE_FILE"
    docker exec gerersci_caddy sh -c 'rm -f /tmp/maintenance' 2>/dev/null || \
    docker exec gerersci_nginx sh -c 'rm -f /tmp/maintenance' 2>/dev/null || true
}

# Ensure maintenance is disabled on exit (even on error)
trap disable_maintenance EXIT

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
    sudo systemctl reload ssh

    # Create app directory
    sudo mkdir -p /opt/gerersci
    sudo chown -R "$USER":"$USER" /opt/gerersci

    echo -e "${GREEN}Initial setup complete.${NC}"
    echo -e "${YELLOW}Next: clone the repo to /opt/gerersci, configure .env, run deploy.sh${NC}"
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

# Safety: abort if .env contains localhost URLs
if grep -q 'localhost' .env 2>/dev/null; then
    echo -e "${RED}ABORT: .env contains localhost — refusing to deploy!${NC}"
    exit 1
fi

# Pull latest code (if in git repo)
if [ -d .git ]; then
    echo -e "${GREEN}Pulling latest code...${NC}"
    git pull origin main 2>/dev/null || echo -e "${YELLOW}Git pull skipped${NC}"
fi

# Enable maintenance page while rebuilding
enable_maintenance

# Build and deploy
echo -e "${GREEN}Building and deploying...${NC}"

if [ "$USE_CADDY" = true ]; then
    COMPOSE_CMD="docker compose -f docker-compose.yml -f docker-compose.caddy.yml"
else
    COMPOSE_CMD="docker compose"
fi

$COMPOSE_CMD build
$COMPOSE_CMD up -d

# Ensure containers are connected to the shared vps_internal network (Caddy needs it)
echo -e "${CYAN}Ensuring network connectivity with Caddy...${NC}"
for container in gerersci_backend gerersci_frontend; do
    if ! docker network inspect vps_internal --format '{{range .Containers}}{{.Name}} {{end}}' 2>/dev/null | grep -q "$container"; then
        docker network connect vps_internal "$container" 2>/dev/null && \
            echo -e "  ${GREEN}✓${NC} $container → vps_internal" || \
            echo -e "  ${YELLOW}⚠${NC} $container already connected to vps_internal"
    else
        echo -e "  ${GREEN}✓${NC} $container already in vps_internal"
    fi
done

# Wait for services to become healthy
echo -e "${GREEN}Waiting for services to become healthy...${NC}"
TIMEOUT=120
ELAPSED=0
while [ $ELAPSED -lt $TIMEOUT ]; do
    BACKEND_HEALTHY=$(docker inspect --format='{{.State.Health.Status}}' gerersci_backend 2>/dev/null || echo "starting")
    FRONTEND_HEALTHY=$(docker inspect --format='{{.State.Health.Status}}' gerersci_frontend 2>/dev/null || echo "starting")

    if [ "$BACKEND_HEALTHY" = "healthy" ] && [ "$FRONTEND_HEALTHY" = "healthy" ]; then
        echo -e "  ${GREEN}Services healthy after ${ELAPSED}s${NC}"
        break
    fi

    sleep 5
    ELAPSED=$((ELAPSED + 5))
    echo -e "  ${YELLOW}Waiting... backend=$BACKEND_HEALTHY frontend=$FRONTEND_HEALTHY (${ELAPSED}s)${NC}"
done

if [ $ELAPSED -ge $TIMEOUT ]; then
    echo -e "${RED}Timeout waiting for services to become healthy${NC}"
fi

# Disable maintenance page — services are ready
disable_maintenance

# Health checks
echo -e "${GREEN}Running health checks...${NC}"
echo ""

check_service() {
    local name=$1
    local url=$2
    local extra_args=$3
    if curl -sf $extra_args --max-time 10 "$url" >/dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} $name — OK"
        return 0
    else
        echo -e "  ${RED}✗${NC} $name — FAILED"
        return 1
    fi
}

# Resolve container IPs for internal health checks if not mapping ports
BACKEND_IP=$(docker inspect -f '{{.NetworkSettings.Networks.vps_internal.IPAddress}}' gerersci_backend 2>/dev/null || echo "localhost")
FRONTEND_IP=$(docker inspect -f '{{.NetworkSettings.Networks.vps_internal.IPAddress}}' gerersci_frontend 2>/dev/null || echo "localhost")

# Fallback to localhost if IP is empty
if [ -z "$BACKEND_IP" ]; then BACKEND_IP="localhost"; fi
if [ -z "$FRONTEND_IP" ]; then FRONTEND_IP="localhost"; fi

FAILURES=0
check_service "Backend liveness" "http://${BACKEND_IP}:8000/health/live" "-H Host:localhost" || ((FAILURES++))
check_service "Backend readiness" "http://${BACKEND_IP}:8000/health/ready" "-H Host:localhost" || ((FAILURES++))
check_service "Frontend" "http://${FRONTEND_IP}:4173/" || ((FAILURES++))

if [ "$USE_CADDY" = true ]; then
    check_service "Caddy" "http://localhost:80" || ((FAILURES++))
else
    check_service "Nginx" "http://localhost:80/nginx-health" || ((FAILURES++))
fi

echo ""
echo -e "${GREEN}Service status:${NC}"
$COMPOSE_CMD ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

if [ $FAILURES -gt 0 ]; then
    echo ""
    echo -e "${RED}$FAILURES health check(s) failed. Check logs:${NC}"
    echo -e "  docker compose logs backend --tail=50"
    echo -e "  docker compose logs frontend --tail=50"
    exit 1
fi

# ------------------------------------------------------------------
# INSTALL MAINTENANCE CRONS (idempotent)
# ------------------------------------------------------------------
echo -e "${GREEN}Setting up maintenance crons...${NC}"

# Docker cleanup — every Sunday at 4am
CLEANUP_SCRIPT="$(pwd)/scripts/docker-cleanup-cron.sh"
if [ -f "$CLEANUP_SCRIPT" ]; then
    CRON_LINE="0 4 * * 0 $CLEANUP_SCRIPT"
    (crontab -l 2>/dev/null | grep -v "docker-cleanup-cron" ; echo "$CRON_LINE") | crontab -
    echo -e "  ${GREEN}✓${NC} Docker cleanup cron — Sunday 4am"
fi

# Log rotation for cleanup logs
if [ ! -f /etc/logrotate.d/gerersci-docker-cleanup ]; then
    sudo tee /etc/logrotate.d/gerersci-docker-cleanup > /dev/null <<'LOGROTATE'
/var/log/gerersci-docker-cleanup.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
}
LOGROTATE
    echo -e "  ${GREEN}✓${NC} Log rotation configured"
fi

echo ""
echo -e "${GREEN}=== Deployment successful! ===${NC}"
echo -e "  Frontend: https://app.gerersci.fr"
echo -e "  API:      https://api.gerersci.fr"
echo -e "  Matomo:   https://analytics.gerersci.fr"
echo -e "  Status:   https://status.gerersci.fr"
if [ "$USE_CADDY" = true ]; then
    echo -e "  Grafana:  https://grafana.gerersci.fr"
    echo -e "  ${CYAN}Using Caddy (auto-HTTPS)${NC}"
fi
