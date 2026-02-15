-- ============================================
-- 修复「信号剥离器/矩阵」6个产品规格编码
-- 产品ID: 32,33,36,37,38,39
-- 修复前: 每产品15条(含1空尺寸+方向特性), 84/84 code错误
-- 修复后: 每产品13条, 0 code错误
-- ============================================

-- Step 1: 删除空值行（尺寸+方向特性）
DELETE FROM product_specs
WHERE product_id IN (32,33,36,37,38,39) AND field_name IN ('尺寸', '方向特性');
-- 预期: DELETE 12

-- Step 2: A类直接修复（6字段×6产品=36条）
UPDATE product_specs SET field_name = '射频阻抗', field_code = 'R'
WHERE product_id IN (32,33,36,37,38,39) AND field_name = '阻抗';

UPDATE product_specs SET field_value = '机柜式', field_code = 'T'
WHERE product_id IN (32,33,36,37,38,39) AND field_name = '安装方式';

UPDATE product_specs SET field_value = '-20~+55', field_code = 'H'
WHERE product_id IN (32,33,36,37,38,39) AND field_name = '工作温度';

UPDATE product_specs SET field_name = '相对湿度', field_value = '≤95', field_code = '8'
WHERE product_id IN (32,33,36,37,38,39) AND field_name = '工作湿度';

UPDATE product_specs SET field_code = 'E'
WHERE product_id IN (32,33,36,37,38,39) AND field_name = '防护等级';

UPDATE product_specs SET field_code = 'K'
WHERE product_id IN (32,33,36,37,38,39) AND field_name = '驻波比';

-- Step 3: B类改名+改值+改code

-- 频率范围→工作频率 (按频段分组)
UPDATE product_specs SET field_name = '工作频率', field_code = 'X'
WHERE product_id IN (32,33,38) AND field_name = '频率范围';

UPDATE product_specs SET field_name = '工作频率', field_code = 'H'
WHERE product_id IN (36,37) AND field_name = '频率范围';

UPDATE product_specs SET field_name = '工作频率', field_code = '7'
WHERE product_id = 39 AND field_name = '频率范围';

-- 最大接入信道数→载波容量支持
UPDATE product_specs SET field_name = '载波容量支持', field_code = 'X'
WHERE product_id = 32 AND field_name = '最大接入信道数';

UPDATE product_specs SET field_name = '载波容量支持', field_code = '3'
WHERE product_id IN (33,36,37,38,39) AND field_name = '最大接入信道数';

-- 射频接口类型→接口类型
UPDATE product_specs SET field_name = '接口类型',
  field_value = 'TX：N-K /  RX：BNC-K', field_code = '4'
WHERE product_id IN (32,33) AND field_name = '射频接口类型';

UPDATE product_specs SET field_name = '接口类型', field_code = 'D'
WHERE product_id IN (36,37,38,39) AND field_name = '射频接口类型';

-- 单端口承载功率→端口承载功率
UPDATE product_specs SET field_name = '端口承载功率', field_code = 'R'
WHERE product_id IN (32,33,36,37,38,39) AND field_name = '单端口承载功率';

-- 插入损耗: 标准化值
UPDATE product_specs SET field_value = '≤1.0', field_code = 'E'
WHERE product_id IN (32,33,36,37,38,39) AND field_name = '插入损耗';

-- 分配损耗: 标准化值
UPDATE product_specs SET field_value = '≤31±2', field_code = '9'
WHERE product_id IN (32,33,36,37,38,39) AND field_name = '分配损耗';

-- 带内波动: 标准化值
UPDATE product_specs SET field_value = '≤2', field_code = 'X'
WHERE product_id IN (32,33,36,37,38,39) AND field_name = '带内波动';

-- Step 4: display_order (13项)
DO $$
DECLARE
    pid INTEGER;
    ids INTEGER[] := ARRAY[32,33,36,37,38,39];
BEGIN
    FOREACH pid IN ARRAY ids LOOP
        UPDATE product_specs SET display_order = 0 WHERE product_id = pid AND field_name = '工作频率';
        UPDATE product_specs SET display_order = 1 WHERE product_id = pid AND field_name = '载波容量支持';
        UPDATE product_specs SET display_order = 2 WHERE product_id = pid AND field_name = '端口承载功率';
        UPDATE product_specs SET display_order = 3 WHERE product_id = pid AND field_name = '插入损耗';
        UPDATE product_specs SET display_order = 4 WHERE product_id = pid AND field_name = '分配损耗';
        UPDATE product_specs SET display_order = 5 WHERE product_id = pid AND field_name = '带内波动';
        UPDATE product_specs SET display_order = 6 WHERE product_id = pid AND field_name = '射频阻抗';
        UPDATE product_specs SET display_order = 7 WHERE product_id = pid AND field_name = '驻波比';
        UPDATE product_specs SET display_order = 8 WHERE product_id = pid AND field_name = '工作温度';
        UPDATE product_specs SET display_order = 9 WHERE product_id = pid AND field_name = '相对湿度';
        UPDATE product_specs SET display_order = 10 WHERE product_id = pid AND field_name = '安装方式';
        UPDATE product_specs SET display_order = 11 WHERE product_id = pid AND field_name = '接口类型';
        UPDATE product_specs SET display_order = 12 WHERE product_id = pid AND field_name = '防护等级';
    END LOOP;
END $$;

-- Step 5: 重建快照 + specification 文本
DO $$
DECLARE
    pid INTEGER;
    product_ids INTEGER[] := ARRAY[32,33,36,37,38,39];
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

        -- 构建 specification 文本
        SELECT string_agg(ps2.field_name || ': ' || ps2.field_value, E'\n' ORDER BY ps2.display_order, ps2.id)
        INTO spec_text
        FROM product_specs ps2
        WHERE ps2.product_id = pid;

        UPDATE products SET specification = spec_text WHERE id = pid;

        RAISE NOTICE 'Product % (%) snapshot updated with % specs',
            pid, p_record.product_mn, jsonb_array_length(specs_json);
    END LOOP;
END $$;

-- Step 6: 验证

-- 6a: 数量检查（每产品应13条）
SELECT product_id, COUNT(*) as spec_count FROM product_specs
WHERE product_id IN (32,33,36,37,38,39) GROUP BY product_id ORDER BY product_id;

-- 6b: code匹配审计（应返回0行）
SELECT ps.product_id, ps.field_name, ps.field_value, ps.field_code, so.code as dict_code
FROM product_specs ps
LEFT JOIN specification_dictionary sd ON sd.name = ps.field_name
LEFT JOIN specification_options so ON so.spec_id = sd.id AND so.value = ps.field_value
WHERE ps.product_id IN (32,33,36,37,38,39)
  AND ps.field_code IS NOT NULL AND ps.field_code != ''
  AND (so.code IS NULL OR ps.field_code != so.code);

-- 6c: 快照一致性
SELECT id, product_mn,
       (SELECT COUNT(*) FROM product_specs WHERE product_id = p.id) as db_specs,
       jsonb_array_length(code_definition_snapshot::jsonb->'code_parts') as snapshot_specs
FROM products p WHERE id IN (32,33,36,37,38,39) ORDER BY id;
