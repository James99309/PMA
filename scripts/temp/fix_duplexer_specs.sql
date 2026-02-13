-- ============================================
-- 修复「双工器」12个产品规格编码
-- 产品ID: 40,41,42,43,44,45,46,188,189,190,191,192
-- 日期: 2026-02-13
-- ============================================

BEGIN;

-- ============================================
-- Step 2: 添加缺失的 spec_definitions (UI树显示)
-- ============================================

-- 双工类型 → 射频性能(category_id=2)
INSERT INTO spec_definitions (category_id, name, name_en, unit, display_order, is_active, created_at)
SELECT 2, '双工类型', 'Duplex Type', NULL, 32, true, NOW()
WHERE NOT EXISTS (SELECT 1 FROM spec_definitions WHERE name = '双工类型');

-- 带外抑制 → 射频性能(category_id=2)
INSERT INTO spec_definitions (category_id, name, name_en, unit, display_order, is_active, created_at)
SELECT 2, '带外抑制', 'Out-of-band Rejection', 'dB', 33, true, NOW()
WHERE NOT EXISTS (SELECT 1 FROM spec_definitions WHERE name = '带外抑制');

-- ============================================
-- Step 3: 删除空值行 (预期20行)
-- ============================================

-- 删除全12个产品的空「尺寸」行 (预期12)
DELETE FROM product_specs
WHERE product_id IN (40,41,42,43,44,45,46,188,189,190,191,192)
  AND field_name = '尺寸';

-- 删除产品43,45的空值行: 射频接口类型、工作温度、工作湿度、三阶互调 (预期8)
DELETE FROM product_specs
WHERE product_id IN (43,45)
  AND field_name IN ('射频接口类型', '工作温度', '工作湿度', '三阶互调')
  AND (field_value IS NULL OR field_value = '');

-- ============================================
-- Step 4: 批量重命名 + 修code
-- ============================================

-- 频率范围 → 工作频率
UPDATE product_specs SET field_name = '工作频率'
WHERE product_id IN (40,41,42,43,44,45,46,188,189,190,191,192) AND field_name = '频率范围';

-- 阻抗 → 射频阻抗, code→R
UPDATE product_specs SET field_name = '射频阻抗', field_code = 'R'
WHERE product_id IN (40,41,42,43,44,45,46,188,189,190,191,192) AND field_name = '阻抗';

-- 收发隔离度 → 上下行隔离度, code→7
UPDATE product_specs SET field_name = '上下行隔离度', field_code = '7'
WHERE product_id IN (40,41,42,43,44,45,46,188,189,190,191,192) AND field_name = '收发隔离度';

-- 承载功率 → 功率容量 (先改名)
UPDATE product_specs SET field_name = '功率容量'
WHERE product_id IN (40,41,42,43,44,45,46,188,189,190,191,192) AND field_name = '承载功率';

-- 功率容量 code: 100→E
UPDATE product_specs SET field_code = 'E'
WHERE product_id IN (40,41,42,43,44,45,46,188,189,190,191,192)
  AND field_name = '功率容量' AND field_value = '100';

-- 功率容量 code: 50→R
UPDATE product_specs SET field_code = 'R'
WHERE product_id IN (40,41,42,43,44,45,46,188,189,190,191,192)
  AND field_name = '功率容量' AND field_value = '50';

-- 射频接口类型 → 接口类型, code→D (10个有值的产品)
UPDATE product_specs SET field_name = '接口类型', field_code = 'D'
WHERE product_id IN (40,41,42,44,46,188,189,190,191,192) AND field_name = '射频接口类型';

-- 工作湿度 → 相对湿度, 值→≤95, code→8 (10个有值的产品)
UPDATE product_specs SET field_name = '相对湿度', field_value = '≤95', field_code = '8'
WHERE product_id IN (40,41,42,44,46,188,189,190,191,192) AND field_name = '工作湿度';

-- 安装方式: 值→机柜式, code→T
UPDATE product_specs SET field_value = '机柜式', field_code = 'T'
WHERE product_id IN (40,41,42,43,44,45,46,188,189,190,191,192) AND field_name = '安装方式';

-- 工作温度: 值→-20~+55, code→H (10个有值的产品)
UPDATE product_specs SET field_value = '-20~+55', field_code = 'H'
WHERE product_id IN (40,41,42,44,46,188,189,190,191,192) AND field_name = '工作温度';

-- 防护等级: code I→E
UPDATE product_specs SET field_code = 'E'
WHERE product_id IN (40,41,42,43,44,45,46,188,189,190,191,192) AND field_name = '防护等级';

-- 驻波比: code 1→K
UPDATE product_specs SET field_code = 'K'
WHERE product_id IN (40,41,42,43,44,45,46,188,189,190,191,192) AND field_name = '驻波比';

-- 插入损耗: code 7→L
UPDATE product_specs SET field_code = 'L'
WHERE product_id IN (40,41,42,43,44,45,46,188,189,190,191,192) AND field_name = '插入损耗';

-- 双工类型 带通型: code→3 (9个产品)
UPDATE product_specs SET field_code = '3'
WHERE product_id IN (40,41,44,45,46,189,190,191,192) AND field_name = '双工类型' AND field_value = '带通型';

-- 双工类型 带阻型: code→7 (产品42,43,188)
UPDATE product_specs SET field_code = '7'
WHERE product_id IN (42,43,188) AND field_name = '双工类型' AND field_value = '带阻型';

-- 带外抑制: code→7
UPDATE product_specs SET field_code = '7'
WHERE product_id IN (40,41,42,43,44,45,46,188,189,190,191,192) AND field_name = '带外抑制';

-- 收发频率间隔: code→L (产品43,45)
UPDATE product_specs SET field_code = 'L'
WHERE product_id IN (43,45) AND field_name = '收发频率间隔';

-- ============================================
-- Step 5: 各产品设工作频率 code
-- ============================================

UPDATE product_specs SET field_code = 'M' WHERE product_id = 40 AND field_name = '工作频率';
UPDATE product_specs SET field_code = 'P' WHERE product_id = 41 AND field_name = '工作频率';
UPDATE product_specs SET field_code = 'A' WHERE product_id IN (42,45) AND field_name = '工作频率';
UPDATE product_specs SET field_code = '4' WHERE product_id IN (43,44) AND field_name = '工作频率';
UPDATE product_specs SET field_code = '8' WHERE product_id = 46 AND field_name = '工作频率';
UPDATE product_specs SET field_code = 'W' WHERE product_id IN (188,189) AND field_name = '工作频率';
UPDATE product_specs SET field_code = 'T' WHERE product_id = 190 AND field_name = '工作频率';
-- 191: 136-174 code=C 已正确，无需更新
UPDATE product_specs SET field_code = '9' WHERE product_id = 192 AND field_name = '工作频率';

-- ============================================
-- Step 6: 设 display_order
-- ============================================

DO $$
DECLARE
    pid INTEGER;
    ids_13 INTEGER[] := ARRAY[40,41,42,44,46,188,189,190,191,192];
    ids_11 INTEGER[] := ARRAY[43,45];
BEGIN
    -- 13项产品: 工作频率/双工类型/插入损耗/功率容量/上下行隔离度/带外抑制/射频阻抗/驻波比/工作温度/相对湿度/安装方式/接口类型/防护等级
    FOREACH pid IN ARRAY ids_13 LOOP
        UPDATE product_specs SET display_order = 0 WHERE product_id = pid AND field_name = '工作频率';
        UPDATE product_specs SET display_order = 1 WHERE product_id = pid AND field_name = '双工类型';
        UPDATE product_specs SET display_order = 2 WHERE product_id = pid AND field_name = '插入损耗';
        UPDATE product_specs SET display_order = 3 WHERE product_id = pid AND field_name = '功率容量';
        UPDATE product_specs SET display_order = 4 WHERE product_id = pid AND field_name = '上下行隔离度';
        UPDATE product_specs SET display_order = 5 WHERE product_id = pid AND field_name = '带外抑制';
        UPDATE product_specs SET display_order = 6 WHERE product_id = pid AND field_name = '射频阻抗';
        UPDATE product_specs SET display_order = 7 WHERE product_id = pid AND field_name = '驻波比';
        UPDATE product_specs SET display_order = 8 WHERE product_id = pid AND field_name = '工作温度';
        UPDATE product_specs SET display_order = 9 WHERE product_id = pid AND field_name = '相对湿度';
        UPDATE product_specs SET display_order = 10 WHERE product_id = pid AND field_name = '安装方式';
        UPDATE product_specs SET display_order = 11 WHERE product_id = pid AND field_name = '接口类型';
        UPDATE product_specs SET display_order = 12 WHERE product_id = pid AND field_name = '防护等级';
    END LOOP;

    -- 11项产品(43,45): 工作频率/双工类型/插入损耗/功率容量/上下行隔离度/带外抑制/收发频率间隔/射频阻抗/驻波比/安装方式/防护等级
    FOREACH pid IN ARRAY ids_11 LOOP
        UPDATE product_specs SET display_order = 0 WHERE product_id = pid AND field_name = '工作频率';
        UPDATE product_specs SET display_order = 1 WHERE product_id = pid AND field_name = '双工类型';
        UPDATE product_specs SET display_order = 2 WHERE product_id = pid AND field_name = '插入损耗';
        UPDATE product_specs SET display_order = 3 WHERE product_id = pid AND field_name = '功率容量';
        UPDATE product_specs SET display_order = 4 WHERE product_id = pid AND field_name = '上下行隔离度';
        UPDATE product_specs SET display_order = 5 WHERE product_id = pid AND field_name = '带外抑制';
        UPDATE product_specs SET display_order = 6 WHERE product_id = pid AND field_name = '收发频率间隔';
        UPDATE product_specs SET display_order = 7 WHERE product_id = pid AND field_name = '射频阻抗';
        UPDATE product_specs SET display_order = 8 WHERE product_id = pid AND field_name = '驻波比';
        UPDATE product_specs SET display_order = 9 WHERE product_id = pid AND field_name = '安装方式';
        UPDATE product_specs SET display_order = 10 WHERE product_id = pid AND field_name = '防护等级';
    END LOOP;
END $$;

COMMIT;

-- ============================================
-- Step 7: 重建快照 + specification 文本
-- ============================================

DO $$
DECLARE
    pid INTEGER;
    product_ids INTEGER[] := ARRAY[40,41,42,43,44,45,46,188,189,190,191,192];
    snapshot JSONB;
    p_record RECORD;
    specs_json JSONB;
    spec_text TEXT;
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

        -- 构建 specification 文本
        SELECT string_agg(
            ps2.field_name || ': ' || ps2.field_value || COALESCE(' ' || sd.unit, ''),
            ', '
            ORDER BY ps2.display_order
        )
        INTO spec_text
        FROM product_specs ps2
        LEFT JOIN (
            SELECT DISTINCT ON (name) name, unit
            FROM spec_definitions
            ORDER BY name, id
        ) sd ON sd.name = ps2.field_name
        WHERE ps2.product_id = pid
          AND ps2.field_value IS NOT NULL AND ps2.field_value != '';

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

        -- 更新快照和specification文本
        UPDATE products
        SET code_definition_snapshot = snapshot,
            specification = spec_text
        WHERE id = pid;

        RAISE NOTICE 'Product % (%) updated: % specs, snapshot + specification',
            pid, p_record.product_mn, jsonb_array_length(specs_json);
    END LOOP;
END $$;

-- ============================================
-- Step 8: 验证
-- ============================================

-- 8a: 数量验证 (10产品=13项, 2产品(43,45)=11项)
SELECT product_id, COUNT(*) as spec_count
FROM product_specs
WHERE product_id IN (40,41,42,43,44,45,46,188,189,190,191,192)
GROUP BY product_id ORDER BY product_id;

-- 8b: code匹配审计 (应返回0行)
SELECT ps.product_id, ps.field_name, ps.field_value, ps.field_code, so.code as dict_code,
       CASE WHEN so.code IS NULL THEN 'NO_DICT_MATCH' ELSE 'CODE_WRONG' END as error_type
FROM product_specs ps
JOIN products p ON p.id = ps.product_id
LEFT JOIN specification_dictionary sd ON sd.name = ps.field_name
LEFT JOIN specification_options so ON so.spec_id = sd.id AND so.value = ps.field_value
WHERE p.product_name = '双工器'
  AND ps.field_code IS NOT NULL AND ps.field_code != ''
  AND (so.code IS NULL OR ps.field_code != so.code);

-- 8c: 快照一致性
SELECT id, product_mn,
       (SELECT COUNT(*) FROM product_specs WHERE product_id = p.id) as db_specs,
       jsonb_array_length(code_definition_snapshot::jsonb->'code_parts') as snapshot_specs
FROM products p WHERE id IN (40,41,42,43,44,45,46,188,189,190,191,192) ORDER BY id;
