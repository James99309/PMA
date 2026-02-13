-- ============================================================
-- 批量修复5个「数字智能光纤直放站 (远端)」产品规格编码
-- 产品: 80(HYR3DI300), 81(HYR3DI310), 82(HYR3DI330),
--        84(HYR3DI340), 85(HYR3DI380)
-- 参考: 产品86 (HYR3DI34J) 已修复结构
-- 36项 → 删4项 + 加1项 = 33项
-- ============================================================

BEGIN;

-- ============================================================
-- Step 1: 删除 4 个废弃字段（比产品86多删1个「功能」）
-- 产品86的「功能=交织」→ 改名「组网结构」
-- 产品80-85的「功能=无」→ 字典无「无」选项 → 直接删除
-- 预期: DELETE 20 (4字段 × 5产品)
-- ============================================================
DELETE FROM product_specs
WHERE product_id IN (80,81,82,84,85)
  AND field_name IN ('频率特性', '馈电功能', '重量', '功能');

-- ============================================================
-- Step 2: 重命名 16 个字段 + 修值 + 修 code（批量）
-- ============================================================

-- 增益 → 设备净增益
UPDATE product_specs
SET field_name = '设备净增益', field_value = '50±2', field_code = '8'
WHERE product_id IN (80,81,82,84,85) AND field_name = '增益';

-- 噪声系数 → 噪声系数(上行)
UPDATE product_specs
SET field_name = '噪声系数(上行)', field_value = '≤7', field_code = '7'
WHERE product_id IN (80,81,82,84,85) AND field_name = '噪声系数';

-- ALC自动调节范围 → 自动电平控制范围（ALC）
UPDATE product_specs
SET field_name = '自动电平控制范围（ALC）', field_value = '≥30', field_code = 'T'
WHERE product_id IN (80,81,82,84,85) AND field_name = 'ALC自动调节范围';

-- 上行最大允许输入电平 → 允许最大输入
UPDATE product_specs
SET field_name = '允许最大输入', field_value = 'RX: ≥-25', field_code = 'A'
WHERE product_id IN (80,81,82,84,85) AND field_name = '上行最大允许输入电平';

-- 阻抗 → 射频阻抗
UPDATE product_specs
SET field_name = '射频阻抗', field_value = '50', field_code = 'R'
WHERE product_id IN (80,81,82,84,85) AND field_name = '阻抗';

-- 时延 → 延时
UPDATE product_specs
SET field_name = '延时', field_value = '≤35', field_code = 'X'
WHERE product_id IN (80,81,82,84,85) AND field_name = '时延';

-- 射频接口类型 → 接口类型
UPDATE product_specs
SET field_name = '接口类型', field_value = 'N-K', field_code = 'D'
WHERE product_id IN (80,81,82,84,85) AND field_name = '射频接口类型';

-- 电源类型 → 供电规格
UPDATE product_specs
SET field_name = '供电规格', field_value = '220V±15%', field_code = 'E'
WHERE product_id IN (80,81,82,84,85) AND field_name = '电源类型';

-- 尺寸 → 外形尺寸
UPDATE product_specs
SET field_name = '外形尺寸', field_value = '480*480*90', field_code = 'K'
WHERE product_id IN (80,81,82,84,85) AND field_name = '尺寸';

-- 工作湿度 → 相对湿度
UPDATE product_specs
SET field_name = '相对湿度', field_value = '≤95', field_code = '8'
WHERE product_id IN (80,81,82,84,85) AND field_name = '工作湿度';

-- 输入输出驻波比 → 驻波比
UPDATE product_specs
SET field_name = '驻波比', field_value = '≤1.5', field_code = 'K'
WHERE product_id IN (80,81,82,84,85) AND field_name = '输入输出驻波比';

-- 光输出功率 → 光模块输出功率
UPDATE product_specs
SET field_name = '光模块输出功率', field_value = '≥-6', field_code = 'T'
WHERE product_id IN (80,81,82,84,85) AND field_name = '光输出功率';

-- 光接收灵敏度 → 光模块接收灵敏度
UPDATE product_specs
SET field_name = '光模块接收灵敏度', field_value = '≤-15', field_code = 'J'
WHERE product_id IN (80,81,82,84,85) AND field_name = '光接收灵敏度';

-- 光波长规格 → 光模块波长
UPDATE product_specs
SET field_name = '光模块波长', field_value = '1310/1550', field_code = 'K'
WHERE product_id IN (80,81,82,84,85) AND field_name = '光波长规格';

-- 光口规格 → 光口工作模式
UPDATE product_specs
SET field_name = '光口工作模式', field_value = '双向收发复用', field_code = '6'
WHERE product_id IN (80,81,82,84,85) AND field_name = '光口规格';

-- 延迟同步功能 → 延迟同步
UPDATE product_specs
SET field_name = '延迟同步', field_value = '具备', field_code = 'J'
WHERE product_id IN (80,81,82,84,85) AND field_name = '延迟同步功能';

-- ============================================================
-- Step 3: 修正未改名但需修值/code 的字段（批量）
-- ============================================================

UPDATE product_specs SET field_value = '40±2', field_code = '7'
WHERE product_id IN (80,81,82,84,85) AND field_name = '最大输出功率';

UPDATE product_specs SET field_value = '9kHz~1GHz：≤-36dBm；1GHz~12.75GHz：≤-30dBm', field_code = 'P'
WHERE product_id IN (80,81,82,84,85) AND field_name = '带外杂散';

UPDATE product_specs SET field_value = '≤-50dBc@2 tone 0dBm； ≤-45dBc@2 tone 33dBm', field_code = 'B'
WHERE product_id IN (80,81,82,84,85) AND field_name = '互调衰减';

UPDATE product_specs SET field_value = '0–10 ±1', field_code = '4'
WHERE product_id IN (80,81,82,84,85) AND field_name = '增益调节线性';

UPDATE product_specs SET field_value = '10/1', field_code = '8'
WHERE product_id IN (80,81,82,84,85) AND field_name = '增益调节步进';

UPDATE product_specs SET field_value = '≥60', field_code = 'W'
WHERE product_id IN (80,81,82,84,85) AND field_name = '上下行隔离度';

UPDATE product_specs SET field_value = '≤3', field_code = 'Y'
WHERE product_id IN (80,81,82,84,85) AND field_name = '带内波动';

UPDATE product_specs SET field_value = '彩色触摸屏', field_code = 'R'
WHERE product_id IN (80,81,82,84,85) AND field_name = '显示方式';

UPDATE product_specs SET field_value = '-20~+55', field_code = 'H'
WHERE product_id IN (80,81,82,84,85) AND field_name = '工作温度';

UPDATE product_specs SET field_value = '机柜式', field_code = 'T'
WHERE product_id IN (80,81,82,84,85) AND field_name = '安装方式';

UPDATE product_specs SET field_value = 'IP40', field_code = 'E'
WHERE product_id IN (80,81,82,84,85) AND field_name = '防护等级';

UPDATE product_specs SET field_value = 'USB', field_code = 'N'
WHERE product_id IN (80,81,82,84,85) AND field_name = '监控接口类型';

UPDATE product_specs SET field_value = '12', field_code = 'N'
WHERE product_id IN (80,81,82,84,85) AND field_name = '载波容量';

UPDATE product_specs SET field_value = 'LC', field_code = 'C'
WHERE product_id IN (80,81,82,84,85) AND field_name = '光口类型';

UPDATE product_specs SET field_value = '2', field_code = 'V'
WHERE product_id IN (80,81,82,84,85) AND field_name = '光口数量';

-- ============================================================
-- Step 4: 单独处理频率（每个产品不同值/code）
-- ============================================================

-- 产品80: HYR3DI300 → 87-108 (FM广播)
UPDATE product_specs
SET field_name = '工作频率', field_value = '87-108', field_code = 'G'
WHERE product_id = 80 AND field_name = '频率范围';

-- 产品81: HYR3DI310 → 136-174 (VHF)
UPDATE product_specs
SET field_name = '工作频率', field_value = '136-174', field_code = 'C'
WHERE product_id = 81 AND field_name = '频率范围';

-- 产品82: HYR3DI330 → 350-400 (UHF低段)
UPDATE product_specs
SET field_name = '工作频率', field_value = '350-400', field_code = 'T'
WHERE product_id = 82 AND field_name = '频率范围';

-- 产品84: HYR3DI340 → 400-470 (UHF高段)
UPDATE product_specs
SET field_name = '工作频率', field_value = '400-470', field_code = 'W'
WHERE product_id = 84 AND field_name = '频率范围';

-- 产品85: HYR3DI380 → 87-108 (FM广播)
UPDATE product_specs
SET field_name = '工作频率', field_value = '87-108', field_code = 'G'
WHERE product_id = 85 AND field_name = '频率范围';

-- ============================================================
-- Step 5: INSERT 缺失字段「增益调节范围」
-- 产品80-85都没有此字段，需要新增
-- ============================================================
INSERT INTO product_specs (product_id, field_name, field_value, field_code, display_order)
VALUES
  (80, '增益调节范围', '30', 'N', 9),
  (81, '增益调节范围', '30', 'N', 9),
  (82, '增益调节范围', '30', 'N', 9),
  (84, '增益调节范围', '30', 'N', 9),
  (85, '增益调节范围', '30', 'N', 9);

-- ============================================================
-- Step 6: 设置 display_order（0-32，共33项）
-- 与计划中的标准排序一致
-- ============================================================
UPDATE product_specs SET display_order = 0  WHERE product_id IN (80,81,82,84,85) AND field_name = '工作频率';
UPDATE product_specs SET display_order = 1  WHERE product_id IN (80,81,82,84,85) AND field_name = '载波容量';
UPDATE product_specs SET display_order = 2  WHERE product_id IN (80,81,82,84,85) AND field_name = '最大输出功率';
UPDATE product_specs SET display_order = 3  WHERE product_id IN (80,81,82,84,85) AND field_name = '设备净增益';
UPDATE product_specs SET display_order = 4  WHERE product_id IN (80,81,82,84,85) AND field_name = '噪声系数(上行)';
UPDATE product_specs SET display_order = 5  WHERE product_id IN (80,81,82,84,85) AND field_name = '自动电平控制范围（ALC）';
UPDATE product_specs SET display_order = 6  WHERE product_id IN (80,81,82,84,85) AND field_name = '带外杂散';
UPDATE product_specs SET display_order = 7  WHERE product_id IN (80,81,82,84,85) AND field_name = '互调衰减';
UPDATE product_specs SET display_order = 8  WHERE product_id IN (80,81,82,84,85) AND field_name = '允许最大输入';
UPDATE product_specs SET display_order = 9  WHERE product_id IN (80,81,82,84,85) AND field_name = '增益调节范围';
UPDATE product_specs SET display_order = 10 WHERE product_id IN (80,81,82,84,85) AND field_name = '增益调节步进';
UPDATE product_specs SET display_order = 11 WHERE product_id IN (80,81,82,84,85) AND field_name = '增益调节线性';
UPDATE product_specs SET display_order = 12 WHERE product_id IN (80,81,82,84,85) AND field_name = '上下行隔离度';
UPDATE product_specs SET display_order = 13 WHERE product_id IN (80,81,82,84,85) AND field_name = '延时';
UPDATE product_specs SET display_order = 14 WHERE product_id IN (80,81,82,84,85) AND field_name = '带内波动';
UPDATE product_specs SET display_order = 15 WHERE product_id IN (80,81,82,84,85) AND field_name = '射频阻抗';
UPDATE product_specs SET display_order = 16 WHERE product_id IN (80,81,82,84,85) AND field_name = '光模块输出功率';
UPDATE product_specs SET display_order = 17 WHERE product_id IN (80,81,82,84,85) AND field_name = '光模块接收灵敏度';
UPDATE product_specs SET display_order = 18 WHERE product_id IN (80,81,82,84,85) AND field_name = '光模块波长';
UPDATE product_specs SET display_order = 19 WHERE product_id IN (80,81,82,84,85) AND field_name = '光口数量';
UPDATE product_specs SET display_order = 20 WHERE product_id IN (80,81,82,84,85) AND field_name = '光口类型';
UPDATE product_specs SET display_order = 21 WHERE product_id IN (80,81,82,84,85) AND field_name = '光口工作模式';
UPDATE product_specs SET display_order = 22 WHERE product_id IN (80,81,82,84,85) AND field_name = '供电规格';
UPDATE product_specs SET display_order = 23 WHERE product_id IN (80,81,82,84,85) AND field_name = '显示方式';
UPDATE product_specs SET display_order = 24 WHERE product_id IN (80,81,82,84,85) AND field_name = '延迟同步';
UPDATE product_specs SET display_order = 25 WHERE product_id IN (80,81,82,84,85) AND field_name = '工作温度';
UPDATE product_specs SET display_order = 26 WHERE product_id IN (80,81,82,84,85) AND field_name = '相对湿度';
UPDATE product_specs SET display_order = 27 WHERE product_id IN (80,81,82,84,85) AND field_name = '外形尺寸';
UPDATE product_specs SET display_order = 28 WHERE product_id IN (80,81,82,84,85) AND field_name = '安装方式';
UPDATE product_specs SET display_order = 29 WHERE product_id IN (80,81,82,84,85) AND field_name = '接口类型';
UPDATE product_specs SET display_order = 30 WHERE product_id IN (80,81,82,84,85) AND field_name = '防护等级';
UPDATE product_specs SET display_order = 31 WHERE product_id IN (80,81,82,84,85) AND field_name = '监控接口类型';
UPDATE product_specs SET display_order = 32 WHERE product_id IN (80,81,82,84,85) AND field_name = '驻波比';

-- ============================================================
-- Step 7: 中间验证（COMMIT前检查数量）
-- ============================================================
SELECT product_id, COUNT(*) as spec_count
FROM product_specs
WHERE product_id IN (80,81,82,84,85)
GROUP BY product_id
ORDER BY product_id;

COMMIT;

-- ============================================================
-- Step 8: 重建 code_definition_snapshot（5个产品）
-- 复用 v2 去重逻辑
-- ============================================================
DO $$
DECLARE
    pid INTEGER;
    product_ids INTEGER[] := ARRAY[80,81,82,84,85];
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
    END LOOP;
END $$;

-- ============================================================
-- Step 9: 重建 specification 文本摘要（5个产品）
-- ============================================================
UPDATE products SET specification = (
    SELECT string_agg(
        ps.field_name || ': ' || ps.field_value || COALESCE(' ' || sd.unit, ''),
        ', '
        ORDER BY ps.display_order
    )
    FROM product_specs ps
    LEFT JOIN (
        SELECT DISTINCT ON (name) name, unit
        FROM spec_definitions
        ORDER BY name, id
    ) sd ON sd.name = ps.field_name
    WHERE ps.product_id = products.id
    AND ps.field_value IS NOT NULL AND ps.field_value != ''
) WHERE id IN (80,81,82,84,85);

-- ============================================================
-- Step 10: 最终验证
-- ============================================================

-- 10a: 每个产品的规格数量
SELECT p.id, p.product_mn,
       (SELECT COUNT(*) FROM product_specs WHERE product_id = p.id) as spec_count,
       json_array_length(p.code_definition_snapshot::json->'code_parts') as snapshot_count
FROM products p
WHERE p.id IN (80,81,82,84,85)
ORDER BY p.id;

-- 10b: 审计查询 - 检查 MISMATCH
SELECT
    ps.product_id,
    p.product_mn,
    ps.field_name,
    ps.field_code,
    so.code as dict_code,
    CASE
        WHEN so.code IS NULL THEN 'NO_DICT'
        WHEN ps.field_code = so.code THEN 'OK'
        ELSE 'MISMATCH'
    END as status
FROM product_specs ps
JOIN products p ON p.id = ps.product_id
LEFT JOIN specification_dictionary sd ON sd.name = ps.field_name
LEFT JOIN specification_options so ON so.spec_id = sd.id AND so.value = ps.field_value
WHERE ps.product_id IN (80,81,82,84,85)
ORDER BY ps.product_id, ps.display_order;
