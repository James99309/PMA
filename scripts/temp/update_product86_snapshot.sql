-- ============================================
-- 重建产品86的规格快照 (code_definition_snapshot)
-- 使用与 v2 批量脚本相同的去重逻辑
-- ============================================

DO $$
DECLARE
    pid INTEGER := 86;
    snapshot JSONB;
    p_record RECORD;
    specs_json JSONB;
BEGIN
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

    -- 构建规格数组JSON（使用子查询去重spec_definitions）
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
END $$;

-- 验证
SELECT id, product_mn,
       json_array_length(code_definition_snapshot::json->'code_parts') as snapshot_specs,
       (SELECT COUNT(*) FROM product_specs WHERE product_id = 86) as actual_specs
FROM products
WHERE id = 86;
