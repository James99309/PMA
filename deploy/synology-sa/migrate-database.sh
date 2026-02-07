#!/bin/bash
# PMA-SA Database Migration: Supabase OVS → NAS PostgreSQL
# Run on Mac (not on NAS)
#
# This script:
# 1. Backs up Supabase OVS database using simple_ovs_backup.py
# 2. Transfers the backup to NAS via SCP
# 3. Imports into the local pma_sa database on NAS
# 4. Verifies data integrity
#
# Prerequisites:
# - NAS is running with pma-postgres container (via init-deploy.sh)
# - Python venv with required packages available locally

set -e

# ============ Configuration ============

# DS925+ SSH connection (via Cloudflare Tunnel)
NAS_SSH_HOST="${NAS_SSH_HOST:-sg-nas}"
NAS_DOCKER_DIR="/volume1/docker/pma"

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/cloud_db_backups"

# ============ Colors ============

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  PMA-SA Database Migration${NC}"
echo -e "${GREEN}  Supabase OVS → NAS PostgreSQL${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# ============ Step 1: Backup Supabase OVS ============

echo -e "${YELLOW}[1/4] Backing up Supabase OVS database...${NC}"

cd "$PROJECT_ROOT"
mkdir -p "$BACKUP_DIR"

# Run the OVS backup script
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib
python3 simple_ovs_backup.py

# Find the latest backup file
LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/ovs_backup_*.sql 2>/dev/null | head -1)
if [ -z "$LATEST_BACKUP" ]; then
    # Also check for .gz files
    LATEST_BACKUP=$(ls -t "$BACKUP_DIR"/ovs_backup_*.sql.gz 2>/dev/null | head -1)
fi

if [ -z "$LATEST_BACKUP" ]; then
    error "No backup file found in $BACKUP_DIR"
fi

BACKUP_SIZE=$(du -h "$LATEST_BACKUP" | cut -f1)
info "Backup created: $(basename "$LATEST_BACKUP") ($BACKUP_SIZE)"

# ============ Step 2: Transfer to NAS ============

echo -e "\n${YELLOW}[2/4] Transferring backup to NAS...${NC}"

NAS_BACKUP_PATH="$NAS_DOCKER_DIR/db_backup_ovs.sql"
BACKUP_FILE="$LATEST_BACKUP"

# Handle gzipped backups
if [[ "$LATEST_BACKUP" == *.gz ]]; then
    info "Decompressing backup..."
    gunzip -k "$LATEST_BACKUP"
    BACKUP_FILE="${LATEST_BACKUP%.gz}"
    NAS_BACKUP_PATH="$NAS_DOCKER_DIR/db_backup_ovs.sql"
fi

scp -O "$BACKUP_FILE" "$NAS_SSH_HOST:$NAS_BACKUP_PATH"
info "Backup transferred to NAS: $NAS_BACKUP_PATH"

# ============ Step 3: Import into NAS PostgreSQL ============

echo -e "\n${YELLOW}[3/4] Importing database on NAS...${NC}"

warn "This will DROP and recreate the pma_sa database!"
read -p "Continue? (y/N) " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    info "Aborted."
    exit 0
fi

# SSH to NAS and import
ssh "$NAS_SSH_HOST" bash -s << 'REMOTE_SCRIPT'
set -e
DOCKER="/usr/local/bin/docker"
BACKUP_FILE="/volume1/docker/pma/db_backup_ovs.sql"

echo "Dropping and recreating pma_sa database..."
sudo $DOCKER exec pma-postgres psql -U pma -d postgres -c "
    SELECT pg_terminate_backend(pg_stat_activity.pid)
    FROM pg_stat_activity
    WHERE pg_stat_activity.datname = 'pma_sa' AND pid <> pg_backend_pid();
" 2>/dev/null || true

sudo $DOCKER exec pma-postgres psql -U pma -d postgres -c "DROP DATABASE IF EXISTS pma_sa;"
sudo $DOCKER exec pma-postgres psql -U pma -d postgres -c "CREATE DATABASE pma_sa ENCODING 'UTF8';"

echo "Importing backup (this may take a few minutes)..."
sudo $DOCKER exec -i pma-postgres psql -U pma -d pma_sa < "$BACKUP_FILE"

echo "Import complete."

# Cleanup backup file on NAS
rm -f "$BACKUP_FILE"
echo "Cleaned up backup file on NAS."
REMOTE_SCRIPT

info "Database imported successfully"

# ============ Step 4: Verify data ============

echo -e "\n${YELLOW}[4/4] Verifying data integrity...${NC}"

ssh "$NAS_SSH_HOST" bash -s << 'VERIFY_SCRIPT'
DOCKER="/usr/local/bin/docker"

echo ""
echo "=== Table Count ==="
$DOCKER exec pma-postgres psql -U pma -d pma_sa -t -c "
    SELECT count(*) as table_count
    FROM information_schema.tables
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
"

echo ""
echo "=== Key Tables Row Count ==="
$DOCKER exec pma-postgres psql -U pma -d pma_sa -c "
    SELECT 'users' as table_name, count(*) as rows FROM \"user\"
    UNION ALL SELECT 'companies', count(*) FROM company
    UNION ALL SELECT 'contacts', count(*) FROM contact
    UNION ALL SELECT 'projects', count(*) FROM project
    UNION ALL SELECT 'quotations', count(*) FROM quotation
    ORDER BY table_name;
"

echo ""
echo "=== Database Size ==="
$DOCKER exec pma-postgres psql -U pma -d pma_sa -t -c "
    SELECT pg_size_pretty(pg_database_size('pma_sa'));
"
VERIFY_SCRIPT

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Database Migration Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Compare table/row counts with Supabase to verify completeness"
echo "  2. Run: bash deploy/synology-sa/migrate-storage.sh"
echo "  3. Restart PMA app: ssh $NAS_SSH_HOST 'sudo docker restart pma-app'"
echo "  4. Test login at https://sg-pma.jamesgpone.win"
