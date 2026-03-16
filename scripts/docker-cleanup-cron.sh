#!/bin/bash
# GererSCI — Docker cleanup cron job
# Installed by deploy.sh, runs weekly via cron
#
# Cleans: dangling images, stopped containers, unused volumes, build cache
# Safe: only removes unused resources, never touches running containers

set -euo pipefail

LOG="/var/log/gerersci-docker-cleanup.log"

echo "$(date '+%Y-%m-%d %H:%M:%S') — Docker cleanup started" >> "$LOG"

# Remove dangling images (untagged, no container using them)
docker image prune -f >> "$LOG" 2>&1

# Remove stopped containers older than 24h
docker container prune -f --filter "until=24h" >> "$LOG" 2>&1

# Remove unused volumes (not attached to any container)
docker volume prune -f >> "$LOG" 2>&1

# Remove build cache older than 7 days
docker builder prune -f --filter "until=168h" >> "$LOG" 2>&1

# Remove unused networks
docker network prune -f --filter "until=24h" >> "$LOG" 2>&1

# Log disk usage after cleanup
echo "$(date '+%Y-%m-%d %H:%M:%S') — Disk after cleanup:" >> "$LOG"
df -h / | tail -1 >> "$LOG"
docker system df >> "$LOG" 2>&1

echo "$(date '+%Y-%m-%d %H:%M:%S') — Docker cleanup completed" >> "$LOG"
echo "---" >> "$LOG"
