-- ============================================
-- 修复报价选择器只显示2个频率的问题
-- 原因: 产品75/76/78的工作频率code都被错误设为G，与74重复
-- ============================================

-- Step 1: 修正 3 个产品的工作频率 field_code
UPDATE product_specs SET field_code = 'B' WHERE field_name = '工作频率' AND product_id = 75;
UPDATE product_specs SET field_code = 'T' WHERE field_name = '工作频率' AND product_id = 76;
UPDATE product_specs SET field_code = 'W' WHERE field_name = '工作频率' AND product_id = 78;

-- Step 2: 补充产品 74 缺失的「最大输出功率」字段
INSERT INTO product_specs (product_id, field_name, field_value, field_code, include_in_description, display_order)
VALUES (74, '最大输出功率', '40±2', '7', false, 1);

-- Step 3: 验证修正结果
SELECT product_id, field_name, field_value, field_code
FROM product_specs
WHERE field_name = '工作频率' AND product_id IN (74, 75, 76, 78, 79)
ORDER BY product_id;

-- 验证产品74的规格数量
SELECT COUNT(*) as spec_count FROM product_specs WHERE product_id = 74;

-- Step 4: 重新生成 5 个产品的快照 (使用 v2 去重逻辑)
DO $$
DECLARE
    pid INTEGER;
    product_ids INTEGER[] := ARRAY[74,75,76,78,79];
    snapshot JSONB;
    p_record RECORD;
    specs_json JSONB;
BEGIN
    FOREACH pid IN ARRAY product_ids
    LOOP
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

        SELECT COALESCE(jsonb_agg(
            jsonb_build_object(
                'position', spec.row_number - 1,
                'field_name', spec.field_name,
                'field_code', COALESCE(spec.field_code, ''),
                'code', COALESCE(spec.field_code, ''),
                'value', COALESCE(spec.field_value, ''),
                'use_in_code', (spec.field_code IS NOT NULL AND spec.field_code != ''),
                'unit', COALESCE(sd_dedup.unit, '')
            ) ORDER BY spec.row_number
        ), '[]'::jsonb)
        INTO specs_json
        FROM (
            SELECT ps2.field_name, ps2.field_value, ps2.field_code,
                   ROW_NUMBER() OVER (ORDER BY ps2.display_order, ps2.id) as row_number
            FROM product_specs ps2
            WHERE ps2.product_id = pid
        ) spec
        LEFT JOIN (
            SELECT DISTINCT ON (name) name, unit
            FROM spec_definitions
            ORDER BY name, id
        ) sd_dedup ON sd_dedup.name = spec.field_name;

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

        UPDATE products SET code_definition_snapshot = snapshot WHERE id = pid;

        RAISE NOTICE 'Product % (%) snapshot updated with % specs',
            pid, p_record.product_mn, jsonb_array_length(specs_json);
    END LOOP;
END $$;

-- Step 5: 最终验证
-- 验证所有5个产品的规格数量
SELECT id, product_mn,
       (SELECT COUNT(*) FROM product_specs WHERE product_id = p.id) as spec_count,
       jsonb_array_length(code_definition_snapshot->'code_parts') as snapshot_specs
FROM products p
WHERE id IN (74, 75, 76, 78, 79)
ORDER BY id;

-- 验证工作频率 code 各不相同
SELECT ps.product_id, ps.field_code, ps.field_value
FROM product_specs ps
WHERE ps.field_name = '工作频率' AND ps.product_id IN (74, 75, 76, 78, 79)
ORDER BY ps.product_id;
