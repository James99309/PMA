-- Reset inventory + SN + legacy settlement test data before going live.
--
-- WHO RUNS THIS:
--   - UAT: before final UAT regression on pma_order_test
--   - Production: after Tailwind revamp deployment, ONLY ONCE,
--     after the operator has confirmed the snapshot is taken.
--
-- WHAT IT DOES:
--   - Empties inventory + flow tables + SN tables
--   - Empties legacy settlements (which are scheduled for table drop in Task 10)
--   - Leaves SettlementOrder / SettlementOrderDetail intact (business is using these)
--   - Leaves PurchaseOrder / SalesOrder / Shipment intact
--
-- TO RESTORE FROM SNAPSHOT:
--   psql -U nijie -d <DB> < cloud_db_backups/inventory_snapshot_<db>_<ts>.sql

BEGIN;

-- Truncate tables conditionally — tolerates missing tables on stale DBs.
DO $$
DECLARE
    t TEXT;
    tables_to_clear TEXT[] := ARRAY[
        'inventory_transactions',
        'inventory',
        'serial_number_histories',  -- note: plural (actual table name)
        'product_serial_numbers',
        'settlement_details',
        'settlements'
    ];
BEGIN
    FOREACH t IN ARRAY tables_to_clear LOOP
        IF EXISTS (
            SELECT 1 FROM information_schema.tables
            WHERE table_schema='public' AND table_name=t
        ) THEN
            EXECUTE format('TRUNCATE TABLE %I RESTART IDENTITY CASCADE', t);
            RAISE NOTICE 'Truncated %', t;
        ELSE
            RAISE NOTICE 'Skipped (missing): %', t;
        END IF;
    END LOOP;
END $$;

COMMIT;

-- Post-truncate row counts (run manually to verify):
--   SELECT 'inventory' AS tbl, COUNT(*) FROM inventory
--   UNION ALL SELECT 'inventory_transactions', COUNT(*) FROM inventory_transactions
--   UNION ALL SELECT 'product_serial_numbers', COUNT(*) FROM product_serial_numbers
--   UNION ALL SELECT 'settlements', COUNT(*) FROM settlements
--   UNION ALL SELECT 'settlement_details', COUNT(*) FROM settlement_details;
