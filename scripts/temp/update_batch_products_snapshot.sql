-- ============================================
-- 批量更新7个产品的规格快照 (code_definition_snapshot)
-- 产品ID: 66, 68, 69, 70, 71, 72, 73
-- 使用纯SQL构建JSON快照
-- ============================================

-- 用DO块循环处理每个产品
DO $$
DECLARE
    pid INTEGER;
    product_ids INTEGER[] := ARRAY[66,68,69,70,71,72,73];
    snapshot JSONB;
    p_record RECORD;
    specs_json JSONB;
BEGIN
    FOREACH pid IN ARRAY product_ids
    LOOP
        -- 获取产品基本信息
        SELECT p.id, p.product_mn, p.spec_mn, p.category_id, p.subcategory_id,
               COALESCE(pc.name, '') as cat_name,
               COALESCE(pc.code_letter, '') as cat_code,
               COALESCE(ps.name, '') as subcat_name,
               COALESCE(ps.code_letter, '') as subcat_code
        INTO p_record
        FROM products p
        LEFT JOIN product_categories pc ON p.category_id = pc.id
        LEFT JOIN product_subcategories ps ON p.subcategory_id = ps.id
        WHERE p.id = pid;

        IF NOT FOUND THEN
            RAISE NOTICE 'Product % not found, skipping', pid;
            CONTINUE;
        END IF;

        -- 构建规格数组JSON
        SELECT COALESCE(jsonb_agg(
            jsonb_build_object(
                'position', row_number - 1,
                'field_name', spec.field_name,
                'field_code', COALESCE(spec.field_code, ''),
                'code', COALESCE(spec.field_code, ''),
                'value', COALESCE(spec.field_value, ''),
                'use_in_code', (spec.field_code IS NOT NULL AND spec.field_code != ''),
                'unit', COALESCE(sd.unit, '')
            ) ORDER BY spec.row_number
        ), '[]'::jsonb)
        INTO specs_json
        FROM (
            SELECT ps2.field_name, ps2.field_value, ps2.field_code,
                   ROW_NUMBER() OVER (ORDER BY ps2.display_order, ps2.id) as row_number
            FROM product_specs ps2
            WHERE ps2.product_id = pid
        ) spec
        LEFT JOIN spec_definitions sd ON sd.name = spec.field_name;

        -- 构建完整快照
        snapshot := jsonb_build_object(
            'version', '1.0',
            'source', 'manual_update',
            'generated_at', to_char(NOW() AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS'),
            'full_code', COALESCE(p_record.spec_mn, p_record.product_mn),
            'category', jsonb_build_object(
                'id', p_record.category_id,
                'name', p_record.cat_name,
                'code_letter', p_record.cat_code
            ),
            'subcategory', jsonb_build_object(
                'id', p_record.subcategory_id,
                'name', p_record.subcat_name,
                'code_letter', p_record.subcat_code
            ),
            'code_parts', specs_json
        );

        -- 更新快照
        UPDATE products SET code_definition_snapshot = snapshot WHERE id = pid;

        RAISE NOTICE 'Product % (%) snapshot updated with % specs',
            pid, p_record.product_mn, jsonb_array_length(specs_json);
    END LOOP;
END $$;

-- 验证快照更新结果
SELECT id, product_mn,
       jsonb_array_length(code_definition_snapshot->'code_parts') as snapshot_specs
FROM products
WHERE id IN (66,67,68,69,70,71,72,73)
ORDER BY id;
