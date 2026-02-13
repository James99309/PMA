-- ============================================
-- 修复「分路器」6个产品规格编码 (产品ID: 23-28)
-- 日期: 2026-02-13
-- ============================================

-- Step 1: 删除空尺寸
DELETE FROM product_specs
WHERE product_id IN (23,24,25,26,27,28)
  AND field_name = '尺寸';
-- 预期: DELETE 6

-- Step 2: 批量重命名字段 + 修值/code

-- 频率范围 → 工作频率
UPDATE product_specs SET field_name = '工作频率'
WHERE product_id IN (23,24,25,26,27,28) AND field_name = '频率范围';

-- 阻抗 → 射频阻抗, code→R
UPDATE product_specs SET field_name = '射频阻抗', field_code = 'R'
WHERE product_id IN (23,24,25,26,27,28) AND field_name = '阻抗';

-- 最大接入信道数 → 载波容量支持
UPDATE product_specs SET field_name = '载波容量支持'
WHERE product_id IN (23,24,25,26,27,28) AND field_name = '最大接入信道数';

-- 射频接口类型 → 接口类型, code N→D
UPDATE product_specs SET field_name = '接口类型', field_code = 'D'
WHERE product_id IN (23,24,25,26,27,28) AND field_name = '射频接口类型';

-- 工作湿度 → 相对湿度, 值→≤95, code→8
UPDATE product_specs SET field_name = '相对湿度', field_value = '≤95', field_code = '8'
WHERE product_id IN (23,24,25,26,27,28) AND field_name = '工作湿度';

-- 安装方式: 值 机柜安装→机柜式, code→T
UPDATE product_specs SET field_value = '机柜式', field_code = 'T'
WHERE product_id IN (23,24,25,26,27,28) AND field_name = '安装方式';

-- 工作温度: 值→-20~+55, code→H
UPDATE product_specs SET field_value = '-20~+55', field_code = 'H'
WHERE product_id IN (23,24,25,26,27,28) AND field_name = '工作温度';

-- 防护等级: code I→E
UPDATE product_specs SET field_code = 'E'
WHERE product_id IN (23,24,25,26,27,28) AND field_name = '防护等级';

-- 驻波比: code 1→K
UPDATE product_specs SET field_code = 'K'
WHERE product_id IN (23,24,25,26,27,28) AND field_name = '驻波比';

-- Step 3: 各产品单独设工作频率 code
-- 产品 23,24: 136-174 → code C (已经是C，无需改)
-- 产品 25-28: 350-470 → code 3→7
UPDATE product_specs SET field_code = '7'
WHERE product_id IN (25,26,27,28) AND field_name = '工作频率';

-- Step 4: 各产品单独设载波容量支持 code
UPDATE product_specs SET field_code = 'V' WHERE product_id IN (23,25) AND field_name = '载波容量支持';  -- 2→V
UPDATE product_specs SET field_code = 'X' WHERE product_id IN (24,26) AND field_name = '载波容量支持';  -- 4→X
UPDATE product_specs SET field_code = '3' WHERE product_id = 27 AND field_name = '载波容量支持';  -- 6→3
UPDATE product_specs SET field_code = '6' WHERE product_id = 28 AND field_name = '载波容量支持';  -- 8→6

-- Step 5: 设置 display_order（9项, 0-8）
DO $$
DECLARE
    pid INTEGER;
    product_ids INTEGER[] := ARRAY[23,24,25,26,27,28];
BEGIN
    FOREACH pid IN ARRAY product_ids
    LOOP
        UPDATE product_specs SET display_order = 0 WHERE product_id = pid AND field_name = '工作频率';
        UPDATE product_specs SET display_order = 1 WHERE product_id = pid AND field_name = '载波容量支持';
        UPDATE product_specs SET display_order = 2 WHERE product_id = pid AND field_name = '射频阻抗';
        UPDATE product_specs SET display_order = 3 WHERE product_id = pid AND field_name = '驻波比';
        UPDATE product_specs SET display_order = 4 WHERE product_id = pid AND field_name = '工作温度';
        UPDATE product_specs SET display_order = 5 WHERE product_id = pid AND field_name = '相对湿度';
        UPDATE product_specs SET display_order = 6 WHERE product_id = pid AND field_name = '安装方式';
        UPDATE product_specs SET display_order = 7 WHERE product_id = pid AND field_name = '接口类型';
        UPDATE product_specs SET display_order = 8 WHERE product_id = pid AND field_name = '防护等级';
    END LOOP;
END $$;

-- Step 6: 重建快照 (code_definition_snapshot)
DO $$
DECLARE
    pid INTEGER;
    product_ids INTEGER[] := ARRAY[23,24,25,26,27,28];
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

-- Step 6b: 更新 specification 文本字段
DO $$
DECLARE
    pid INTEGER;
    product_ids INTEGER[] := ARRAY[23,24,25,26,27,28];
    spec_text TEXT;
BEGIN
    FOREACH pid IN ARRAY product_ids
    LOOP
        SELECT string_agg(field_name || ': ' || COALESCE(field_value, ''), E'\n' ORDER BY display_order, id)
        INTO spec_text
        FROM product_specs
        WHERE product_id = pid;

        UPDATE products SET specification = spec_text WHERE id = pid;

        RAISE NOTICE 'Product % specification text updated', pid;
    END LOOP;
END $$;

-- Step 7: 验证

-- 数量检查: 全部应为 9 项
SELECT product_id, COUNT(*) as spec_count FROM product_specs
WHERE product_id IN (23,24,25,26,27,28) GROUP BY product_id ORDER BY product_id;

-- 快照一致性
SELECT id, product_mn,
       (SELECT COUNT(*) FROM product_specs WHERE product_id = p.id) as db_specs,
       json_array_length(code_definition_snapshot::json->'code_parts') as snapshot_specs
FROM products p WHERE id IN (23,24,25,26,27,28) ORDER BY id;

-- 查看所有规格详情
SELECT product_id, display_order, field_name, field_value, field_code
FROM product_specs
WHERE product_id IN (23,24,25,26,27,28)
ORDER BY product_id, display_order;
