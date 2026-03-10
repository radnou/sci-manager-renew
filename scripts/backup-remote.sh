#!/bin/bash
# GererSCI Backup Script with Remote Storage
# Supports: local + S3-compatible (OVH Object Storage)

set -euo pipefail

BACKUP_DIR="/opt/gerersci/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_LOCAL=7
RETENTION_REMOTE=30

mkdir -p "$BACKUP_DIR"

echo "[$(date)] Starting backup..."

# 1. Database backup via Supabase (production uses Supabase cloud)
# For local Docker DB:
if docker compose ps db --status running 2>/dev/null | grep -q running; then
    docker compose exec -T db pg_dump -U "${DATABASE_USER:-gerersci}" "${DATABASE_NAME:-gerersci}" | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"
    echo "Database backup: db_$DATE.sql.gz"
fi

# 2. Application config backup
tar czf "$BACKUP_DIR/config_$DATE.tar.gz" \
    --exclude='*.pyc' --exclude='node_modules' --exclude='.git' \
    /opt/gerersci/.env \
    /opt/gerersci/docker-compose.yml \
    /opt/gerersci/docker/ \
    2>/dev/null || true
echo "Config backup: config_$DATE.tar.gz"

# 3. Encrypt backups (if GPG key available)
if gpg --list-keys "gerersci-backup" 2>/dev/null; then
    for f in "$BACKUP_DIR"/*_"$DATE".*; do
        gpg --encrypt --recipient "gerersci-backup" "$f" && rm "$f"
        echo "Encrypted: $(basename "$f").gpg"
    done
fi

# 4. Upload to remote (S3-compatible)
if command -v aws &>/dev/null && [ -n "${S3_BACKUP_BUCKET:-}" ]; then
    aws s3 sync "$BACKUP_DIR/" "s3://$S3_BACKUP_BUCKET/gerersci/" \
        --exclude "*" --include "*_${DATE}*" \
        --endpoint-url "${S3_ENDPOINT_URL:-}"
    echo "Uploaded to S3: $S3_BACKUP_BUCKET"

    # Remote retention
    aws s3 ls "s3://$S3_BACKUP_BUCKET/gerersci/" --endpoint-url "${S3_ENDPOINT_URL:-}" \
        | sort | head -n -$RETENTION_REMOTE \
        | awk '{print $4}' \
        | xargs -I{} aws s3 rm "s3://$S3_BACKUP_BUCKET/gerersci/{}" --endpoint-url "${S3_ENDPOINT_URL:-}" 2>/dev/null || true
fi

# 5. Local retention
cd "$BACKUP_DIR"
ls -t db_*.sql.gz 2>/dev/null | tail -n +$((RETENTION_LOCAL + 1)) | xargs rm -f 2>/dev/null || true
ls -t config_*.tar.gz 2>/dev/null | tail -n +$((RETENTION_LOCAL + 1)) | xargs rm -f 2>/dev/null || true

echo "[$(date)] Backup complete!"
