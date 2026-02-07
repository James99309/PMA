#!/bin/bash
# PMA-SA File Storage Migration: Supabase Storage → NAS WebDAV
# Run on Mac (not on NAS)
#
# Uses the existing sync_supabase_to_nas.py script to migrate files
# from Supabase Storage buckets to NAS WebDAV.
#
# Supabase Buckets → NAS WebDAV Paths:
#   invoice-images   → /pma-files/invoices/
#   product-images   → /pma-files/products/
#   rd-product-images → /pma-files/rd_products/
#
# Prerequisites:
# - .env.supabase.prod configured with Supabase credentials
# - NAS WebDAV running and accessible
# - Python venv with supabase and webdavclient3 packages

set -e

# ============ Configuration ============

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SYNC_SCRIPT="$PROJECT_ROOT/scripts/tools/sync_supabase_to_nas.py"

# Use external WebDAV URL (via Cloudflare Tunnel) since we run from Mac
NAS_WEBDAV_URL="${NAS_WEBDAV_URL:-https://webdav.jamesgpone.win}"
NAS_WEBDAV_USER="${NAS_WEBDAV_USER:-pma-storage}"
NAS_WEBDAV_PATH="/pma-files"

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
echo -e "${GREEN}  PMA-SA File Storage Migration${NC}"
echo -e "${GREEN}  Supabase → NAS WebDAV${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# ============ Check prerequisites ============

if [ ! -f "$SYNC_SCRIPT" ]; then
    error "Sync script not found: $SYNC_SCRIPT"
fi

if [ ! -f "$PROJECT_ROOT/.env.supabase.prod" ]; then
    warn ".env.supabase.prod not found. Supabase credentials needed."
    echo "Create it with SUPABASE_URL and SUPABASE_KEY."
    exit 1
fi

cd "$PROJECT_ROOT"
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib

# ============ Migration ============

echo -e "${CYAN}Bucket migration plan:${NC}"
echo "  invoice-images    → ${NAS_WEBDAV_PATH}/invoices/"
echo "  product-images    → ${NAS_WEBDAV_PATH}/products/"
echo "  rd-product-images → ${NAS_WEBDAV_PATH}/rd_products/"
echo ""

# Step 1: Dry run
echo -e "${YELLOW}[1/3] Running dry-run to preview files...${NC}"
echo ""

read -p "Run dry-run first? (Y/n) " do_dry_run
if [ "$do_dry_run" != "n" ] && [ "$do_dry_run" != "N" ]; then
    python3 "$SYNC_SCRIPT" --dry-run 2>&1 || {
        warn "Dry run encountered issues. Check the output above."
        read -p "Continue anyway? (y/N) " continue_anyway
        if [ "$continue_anyway" != "y" ] && [ "$continue_anyway" != "Y" ]; then
            exit 1
        fi
    }
    echo ""
fi

# Step 2: Execute sync
echo -e "${YELLOW}[2/3] Executing file migration...${NC}"
echo ""
warn "This will download files from Supabase and upload to NAS WebDAV."
read -p "Start migration? (y/N) " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    info "Aborted."
    exit 0
fi

python3 "$SYNC_SCRIPT" 2>&1

# Step 3: Verify
echo -e "\n${YELLOW}[3/3] Verifying files on NAS WebDAV...${NC}"

echo ""
echo "Checking WebDAV directories..."
for dir in invoices products rd_products; do
    count=$(curl -s -X PROPFIND \
        -H "Depth: 1" \
        -u "$NAS_WEBDAV_USER:$NAS_WEBDAV_PASSWORD" \
        "$NAS_WEBDAV_URL${NAS_WEBDAV_PATH}/${dir}/" 2>/dev/null \
        | grep -c "<D:response>" 2>/dev/null || echo "?")
    echo "  ${NAS_WEBDAV_PATH}/${dir}/: ~$count items"
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  File Migration Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Login to PMA and verify file attachments display correctly"
echo "  2. Test uploading a new file"
echo "  3. If everything works, you can decommission Supabase Storage"
