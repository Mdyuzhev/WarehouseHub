#!/bin/bash
# =============================================================================
# PostgreSQL Backup Script for Warehouse
# Usage: ./scripts/backup-postgres.sh [prod|dev]
# =============================================================================

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

# =============================================================================
# Configuration
# =============================================================================

ENV="${1:-prod}"
BACKUP_DIR="${BACKUP_DIR:-/home/flomaster/backups/postgres}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"
DATE=$(date +%Y%m%d_%H%M%S)

case "$ENV" in
    prod)
        NAMESPACE="warehouse"
        DB_NAME="warehouse"
        POD_LABEL="app=postgres"
        ;;
    dev)
        NAMESPACE="warehouse-dev"
        DB_NAME="warehouse_dev"
        POD_LABEL="app=postgres,environment=development"
        ;;
    *)
        error "Unknown environment: $ENV. Use 'prod' or 'dev'"
        ;;
esac

BACKUP_FILE="${BACKUP_DIR}/${ENV}_${DB_NAME}_${DATE}.sql.gz"

# =============================================================================
# Pre-checks
# =============================================================================

info "Starting PostgreSQL backup for $ENV environment..."

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Check if pod exists
POD_NAME=$(kubectl get pods -n "$NAMESPACE" -l "$POD_LABEL" -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
if [ -z "$POD_NAME" ]; then
    error "PostgreSQL pod not found in namespace $NAMESPACE with label $POD_LABEL"
fi

info "Found PostgreSQL pod: $POD_NAME"

# =============================================================================
# Backup
# =============================================================================

info "Creating backup: $BACKUP_FILE"

# Get credentials from secret
DB_USER=$(kubectl get secret postgres-credentials -n "$NAMESPACE" -o jsonpath='{.data.APP_DB_USER}' 2>/dev/null | base64 -d)
if [ -z "$DB_USER" ]; then
    DB_USER="postgres"  # fallback to default
fi

# Run pg_dump inside the pod
kubectl exec -n "$NAMESPACE" "$POD_NAME" -- \
    pg_dump -U "$DB_USER" -d "$DB_NAME" --no-owner --no-acl \
    | gzip > "$BACKUP_FILE"

# Verify backup
if [ -s "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(ls -lh "$BACKUP_FILE" | awk '{print $5}')
    success "Backup created: $BACKUP_FILE ($BACKUP_SIZE)"
else
    rm -f "$BACKUP_FILE"
    error "Backup file is empty or failed"
fi

# =============================================================================
# Cleanup old backups
# =============================================================================

info "Cleaning up backups older than $RETENTION_DAYS days..."

DELETED_COUNT=$(find "$BACKUP_DIR" -name "${ENV}_*.sql.gz" -mtime +$RETENTION_DAYS -delete -print | wc -l)
if [ "$DELETED_COUNT" -gt 0 ]; then
    info "Deleted $DELETED_COUNT old backup(s)"
fi

# =============================================================================
# Summary
# =============================================================================

echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║     PostgreSQL Backup Complete!                               ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Environment: $ENV"
echo "Database:    $DB_NAME"
echo "Backup:      $BACKUP_FILE"
echo "Size:        $BACKUP_SIZE"
echo ""
echo "Restore command:"
echo "  gunzip -c $BACKUP_FILE | kubectl exec -i -n $NAMESPACE $POD_NAME -- psql -U $DB_USER -d $DB_NAME"
echo ""
