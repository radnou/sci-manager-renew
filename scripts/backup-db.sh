#!/bin/bash
set -euo pipefail

# GererSCI — Database Backup Script
# -----------------------------------
# Dumps the PostgreSQL database, compresses it with gzip,
# and cleans up backups older than 30 days.
#
# Required env var:
#   DATABASE_URL — PostgreSQL connection string
#
# Cron setup (daily at 3 AM):
#   0 3 * * * /app/scripts/backup-db.sh >> /var/log/gerersci-backup.log 2>&1

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/gerersci-${TIMESTAMP}.sql.gz"

# Validate DATABASE_URL
if [ -z "${DATABASE_URL:-}" ]; then
    echo "[ERROR] DATABASE_URL is not set. Aborting backup."
    exit 1
fi

# Ensure backup directory exists
mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting database backup..."

# Dump and compress
pg_dump "$DATABASE_URL" | gzip > "$BACKUP_FILE"

echo "[$(date)] Backup saved to ${BACKUP_FILE} ($(du -h "$BACKUP_FILE" | cut -f1))"

# Delete backups older than 30 days
DELETED=$(find "$BACKUP_DIR" -name "gerersci-*.sql.gz" -mtime +30 -print -delete | wc -l)
if [ "$DELETED" -gt 0 ]; then
    echo "[$(date)] Cleaned up ${DELETED} backup(s) older than 30 days."
fi

echo "[$(date)] Backup complete."
