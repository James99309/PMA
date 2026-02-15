-- ============================================================
-- 修复「功率分配器/定向耦合器/馈电」15个产品规格编码
-- 产品ID: 88-102
-- 日期: 2026-02-14
-- ============================================================
-- 产品概况:
--   ID 90: 功率分配器 (88-470MHz)
--   ID 88,89,91,92: 定向耦合器 (88-170MHz)
--   ID 93-97: 定向耦合器 (350-470MHz)
--   ID 98: 馈电功率分配器 (350-470MHz)
--   ID 99-102: 馈电定向耦合器 (350-470MHz)
-- 预期: 145条→125条, code错误 145→0
-- ============================================================

BEGIN;

-- ============================================================
-- Step 1: 删除无意义字段 (预期 DELETE 20)
-- ============================================================

-- 1a. 非馈电产品的「馈电功能=无馈电」(10行)
DELETE FROM product_specs
WHERE product_id IN (88,89,90,91,92,93,94,95,96,97)
  AND field_name = '馈电功能';
-- 预期: DELETE 10

-- 1b. 馈电产品的「馈电电压」和「馈电电流」(10行)
DELETE FROM product_specs
WHERE product_id IN (98,99,100,101,102)
  AND field_name IN ('馈电电压', '馈电电流');
-- 预期: DELETE 10

-- ============================================================
-- Step 2: A类通用修复 - 全15产品 (6字段)
-- ============================================================

-- 阻抗→射频阻抗, code=R
UPDATE product_specs SET field_name = '射频阻抗', field_code = 'R'
WHERE product_id IN (88,89,90,91,92,93,94,95,96,97,98,99,100,101,102)
  AND field_name = '阻抗';

-- 工作温度 value修正, code=H
UPDATE product_specs SET field_value = '-20~+55', field_code = 'H'
WHERE product_id IN (88,89,90,91,92,93,94,95,96,97,98,99,100,101,102)
  AND field_name = '工作温度';

-- 工作湿度→相对湿度, value=≤95, code=8
UPDATE product_specs SET field_name = '相对湿度', field_value = '≤95', field_code = '8'
WHERE product_id IN (88,89,90,91,92,93,94,95,96,97,98,99,100,101,102)
  AND field_name = '工作湿度';

-- 射频接口类型→接口类型, code=D
UPDATE product_specs SET field_name = '接口类型', field_code = 'D'
WHERE product_id IN (88,89,90,91,92,93,94,95,96,97,98,99,100,101,102)
  AND field_name = '射频接口类型';

-- 驻波比 code=K
UPDATE product_specs SET field_code = 'K'
WHERE product_id IN (88,89,90,91,92,93,94,95,96,97,98,99,100,101,102)
  AND field_name = '驻波比';

-- 承载功率→功率容量, code=R
UPDATE product_specs SET field_name = '功率容量', field_code = 'R'
WHERE product_id IN (88,89,90,91,92,93,94,95,96,97,98,99,100,101,102)
  AND field_name = '承载功率';

-- ============================================================
-- Step 3: B类 - 频率范围→工作频率 (按频段分组)
-- ============================================================

-- ID 90: 88-470MHz, code=K
UPDATE product_specs SET field_name = '工作频率', field_code = 'K'
WHERE product_id = 90
  AND field_name = '频率范围';

-- ID 88,89,91,92: 88-170MHz, code=H
UPDATE product_specs SET field_name = '工作频率', field_code = 'H'
WHERE product_id IN (88,89,91,92)
  AND field_name = '频率范围';

-- ID 93-102: 350-470MHz, code=7
UPDATE product_specs SET field_name = '工作频率', field_code = '7'
WHERE product_id IN (93,94,95,96,97,98,99,100,101,102)
  AND field_name = '频率范围';

-- ============================================================
-- Step 4: C类 - 耦合损耗→耦合度
-- ============================================================

-- 耦合6 → 6±1, code=E
UPDATE product_specs SET field_name = '耦合度', field_value = '6±1', field_code = 'E'
WHERE product_id IN (88,93,99)
  AND field_name = '耦合损耗';

-- 耦合10 → 10±1, code=Y
UPDATE product_specs SET field_name = '耦合度', field_value = '10±1', field_code = 'Y'
WHERE product_id IN (89,94,100)
  AND field_name = '耦合损耗';

-- 耦合15 → 15±1, code=8
UPDATE product_specs SET field_name = '耦合度', field_value = '15±1', field_code = '8'
WHERE product_id IN (91,95,101)
  AND field_name = '耦合损耗';

-- 耦合20 → 20±1, code=3
UPDATE product_specs SET field_name = '耦合度', field_value = '20±1', field_code = '3'
WHERE product_id IN (92,96,102)
  AND field_name = '耦合损耗';

-- 耦合30 → 30±1, code=4
UPDATE product_specs SET field_name = '耦合度', field_value = '30±1', field_code = '4'
WHERE product_id = 97
  AND field_name = '耦合损耗';

-- ============================================================
-- Step 5: D类 - 其他特定修复
-- ============================================================

-- 分配损耗 code=K (ID 90, 98)
UPDATE product_specs SET field_code = 'K'
WHERE product_id IN (90,98)
  AND field_name = '分配损耗';

-- 馈电功能→馈电通过, value=具备, code=J (ID 98-102)
UPDATE product_specs SET field_name = '馈电通过', field_value = '具备', field_code = 'J'
WHERE product_id IN (98,99,100,101,102)
  AND field_name = '馈电功能';

-- ============================================================
-- Step 6: display_order 设置
-- ============================================================
DO $$
DECLARE
    pid INTEGER;
    field TEXT;
    ord INTEGER;

    -- 功率分配器 (ID 90): 8项
    splitter_fields TEXT[] := ARRAY[
        '工作频率','分配损耗','功率容量','驻波比',
        '射频阻抗','接口类型','工作温度','相对湿度'
    ];

    -- 定向耦合器 (ID 88-97): 8项
    coupler_fields TEXT[] := ARRAY[
        '工作频率','耦合度','功率容量','驻波比',
        '射频阻抗','接口类型','工作温度','相对湿度'
    ];

    -- 馈电功率分配器 (ID 98): 9项
    feed_splitter_fields TEXT[] := ARRAY[
        '工作频率','分配损耗','馈电通过','功率容量','驻波比',
        '射频阻抗','接口类型','工作温度','相对湿度'
    ];

    -- 馈电定向耦合器 (ID 99-102): 9项
    feed_coupler_fields TEXT[] := ARRAY[
        '工作频率','耦合度','馈电通过','功率容量','驻波比',
        '射频阻抗','接口类型','工作温度','相对湿度'
    ];
BEGIN
    -- 功率分配器 ID 90
    FOR ord IN 0..array_length(splitter_fields, 1)-1 LOOP
        field := splitter_fields[ord + 1];
        UPDATE product_specs SET display_order = ord
        WHERE product_id = 90 AND field_name = field;
    END LOOP;

    -- 定向耦合器 ID 88,89,91-97
    FOREACH pid IN ARRAY ARRAY[88,89,91,92,93,94,95,96,97] LOOP
        FOR ord IN 0..array_length(coupler_fields, 1)-1 LOOP
            field := coupler_fields[ord + 1];
            UPDATE product_specs SET display_order = ord
            WHERE product_id = pid AND field_name = field;
        END LOOP;
    END LOOP;

    -- 馈电功率分配器 ID 98
    FOR ord IN 0..array_length(feed_splitter_fields, 1)-1 LOOP
        field := feed_splitter_fields[ord + 1];
        UPDATE product_specs SET display_order = ord
        WHERE product_id = 98 AND field_name = field;
    END LOOP;

    -- 馈电定向耦合器 ID 99-102
    FOREACH pid IN ARRAY ARRAY[99,100,101,102] LOOP
        FOR ord IN 0..array_length(feed_coupler_fields, 1)-1 LOOP
            field := feed_coupler_fields[ord + 1];
            UPDATE product_specs SET display_order = ord
            WHERE product_id = pid AND field_name = field;
        END LOOP;
    END LOOP;
END $$;

-- ============================================================
-- Step 7: 重建快照 + specification 文本
-- ============================================================
DO $$
DECLARE
    pid INTEGER;
    product_ids INTEGER[] := ARRAY[88,89,90,91,92,93,94,95,96,97,98,99,100,101,102];
    snapshot JSONB;
    p_record RECORD;
    specs_json JSONB;
    spec_text TEXT;
BEGIN
    FOREACH pid IN ARRAY product_ids LOOP
        -- 获取产品元数据
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

        -- 构建 specs JSON (使用 DISTINCT ON 去重)
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

        -- 重建 specification 文本
        SELECT string_agg(
            ps2.field_name || ': ' || ps2.field_value,
            E'\n' ORDER BY ps2.display_order, ps2.id
        )
        INTO spec_text
        FROM product_specs ps2
        WHERE ps2.product_id = pid;

        UPDATE products SET specification = spec_text WHERE id = pid;

        RAISE NOTICE 'Product % snapshot rebuilt', pid;
    END LOOP;
END $$;

COMMIT;

-- ============================================================
-- Step 8: 验证查询 (COMMIT后执行)
-- ============================================================

-- 8a. 数量检查: ID90=8, ID88-97=8, ID98=9, ID99-102=9
SELECT product_id, COUNT(*) as spec_count,
       CASE
           WHEN product_id = 90 THEN 8
           WHEN product_id IN (88,89,91,92,93,94,95,96,97) THEN 8
           WHEN product_id = 98 THEN 9
           WHEN product_id IN (99,100,101,102) THEN 9
       END as expected_count
FROM product_specs
WHERE product_id IN (88,89,90,91,92,93,94,95,96,97,98,99,100,101,102)
GROUP BY product_id
ORDER BY product_id;

-- 8b. code匹配审计: 期望0行错误
SELECT ps.product_id, ps.field_name, ps.field_value, ps.field_code,
       so.code as dict_code
FROM product_specs ps
JOIN specification_dictionary sd ON sd.name = ps.field_name
JOIN specification_options so ON so.spec_id = sd.id AND so.value = ps.field_value
WHERE ps.product_id IN (88,89,90,91,92,93,94,95,96,97,98,99,100,101,102)
  AND ps.field_code != so.code;

-- 8c. 快照一致性检查
SELECT p.id, p.product_name,
       jsonb_array_length(p.code_definition_snapshot->'code_parts') as snapshot_specs,
       (SELECT COUNT(*) FROM product_specs ps WHERE ps.product_id = p.id) as db_specs
FROM products p
WHERE p.id IN (88,89,90,91,92,93,94,95,96,97,98,99,100,101,102)
  AND jsonb_array_length(p.code_definition_snapshot->'code_parts') !=
      (SELECT COUNT(*) FROM product_specs ps WHERE ps.product_id = p.id)
ORDER BY p.id;
