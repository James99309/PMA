#!/bin/bash
# Snapshot inventory/SN/settlement related tables before Tailwind revamp.
# Usage: ./snapshot_inventory_pre_refactor.sh [database_name]
#
# Creates: cloud_db_backups/inventory_snapshot_<db>_<timestamp>.sql
# Pure data dump (no schema), restorable on a DB with same schema.

set -euo pipefail

DB="${1:-pma_order_test}"
TS=$(date +%Y%m%d_%H%M%S)
PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT_DIR="${PROJECT_ROOT}/cloud_db_backups"
OUT_FILE="${OUT_DIR}/inventory_snapshot_${DB}_${TS}.sql"

mkdir -p "${OUT_DIR}"

TABLES=(
    inventory
    inventory_transactions
    settlements
    settlement_details
    product_serial_numbers
    serial_number_histories
)

PG_ARGS=()
for t in "${TABLES[@]}"; do
    PG_ARGS+=("--table=${t}")
done

echo "=== Snapshotting ${DB} → ${OUT_FILE} ==="
echo "Tables: ${TABLES[*]}"

pg_dump \
    --username=nijie \
    --dbname="${DB}" \
    --data-only \
    --no-owner \
    --no-acl \
    --column-inserts \
    "${PG_ARGS[@]}" \
    > "${OUT_FILE}"

echo ""
echo "=== Row counts at snapshot ==="
for t in "${TABLES[@]}"; do
    cnt=$(psql -U nijie -d "${DB}" -tc "SELECT COUNT(*) FROM ${t};" 2>/dev/null | tr -d ' ' || echo "table-missing")
    printf "  %-30s %s\n" "${t}" "${cnt}"
done

echo ""
echo "Snapshot written to: ${OUT_FILE}"
echo "Size: $(du -h "${OUT_FILE}" | cut -f1)"
