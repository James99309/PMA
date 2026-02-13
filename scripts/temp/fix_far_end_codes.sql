-- ============================================
-- 修复 智能光纤直放站 (远端) 产品 66-73 全面 code 修正
-- + 新产品 209, 213 工作频率 code 修正
-- + 快照重建 (66-73, 205-210, 213)
-- ============================================

-- =============================================
-- BATCH 1: 纯 code 修正 (所有 66-73 共有)
-- =============================================
UPDATE product_specs SET field_code = 'T' WHERE field_name = '自动电平控制范围（ALC）' AND product_id IN (66,67,68,69,70,71,72,73);
UPDATE product_specs SET field_code = 'N' WHERE field_name = '增益调节范围' AND product_id IN (66,67,68,69,70,71,72,73);
UPDATE product_specs SET field_code = 'U' WHERE field_name = '增益调节线性' AND product_id IN (66,67,68,69,70,71,72,73);
UPDATE product_specs SET field_code = 'W' WHERE field_name = '上下行隔离度' AND product_id IN (66,67,68,69,70,71,72,73);
UPDATE product_specs SET field_code = 'Y' WHERE field_name = '延时' AND product_id IN (66,67,68,69,70,71,72,73);
UPDATE product_specs SET field_code = 'Y' WHERE field_name = '带内波动' AND product_id IN (66,67,68,69,70,71,72,73);
UPDATE product_specs SET field_code = 'R' WHERE field_name = '射频阻抗' AND product_id IN (66,67,68,69,70,71,72,73);
UPDATE product_specs SET field_code = 'T' WHERE field_name = '光模块输出功率' AND product_id IN (66,67,68,69,70,71,72,73);
UPDATE product_specs SET field_code = 'J' WHERE field_name = '光模块接收灵敏度' AND product_id IN (66,67,68,69,70,71,72,73);
UPDATE product_specs SET field_code = 'K' WHERE field_name = '光模块波长' AND product_id IN (66,67,68,69,70,71,72,73);
UPDATE product_specs SET field_code = 'U' WHERE field_name = '光口数量' AND product_id IN (66,67,68,69,70,71,72,73);
UPDATE product_specs SET field_code = '6' WHERE field_name = '光口工作模式' AND product_id IN (66,67,68,69,70,71,72,73);
UPDATE product_specs SET field_code = 'P' WHERE field_name = '显示方式' AND product_id IN (66,67,68,69,70,71,72,73);
UPDATE product_specs SET field_code = 'D' WHERE field_name = '接口类型' AND product_id IN (66,67,68,69,70,71,72,73);
UPDATE product_specs SET field_code = 'E' WHERE field_name = '防护等级' AND product_id IN (66,67,68,69,70,71,72,73);
UPDATE product_specs SET field_code = 'N' WHERE field_name = '监控接口类型' AND product_id IN (66,67,68,69,70,71,72,73);
UPDATE product_specs SET field_code = 'K' WHERE field_name = '驻波比' AND product_id IN (66,67,68,69,70,71,72,73);

-- =============================================
-- BATCH 2: 值 + code 修正 (所有 66-73 共有)
-- =============================================
UPDATE product_specs SET field_value = '220V±15%', field_code = 'E' WHERE field_name = '供电规格' AND product_id IN (66,67,68,69,70,71,72,73);
UPDATE product_specs SET field_value = '-20~+55', field_code = 'H' WHERE field_name = '工作温度' AND product_id IN (66,67,68,69,70,71,72,73);
UPDATE product_specs SET field_value = '≤95', field_code = '8' WHERE field_name = '相对湿度' AND product_id IN (66,67,68,69,70,71,72,73);
UPDATE product_specs SET field_value = '9kHz~1GHz：≤-36dBm；1GHz~12.75GHz：≤-30dBm', field_code = 'P' WHERE field_name = '带外杂散' AND product_id IN (66,67,68,69,70,71,72,73);
UPDATE product_specs SET field_value = '≤-50dBc@2 tone 0dBm； ≤-45dBc@2 tone 33dBm', field_code = 'B' WHERE field_name = '互调衰减' AND product_id IN (66,67,68,69,70,71,72,73);
-- 允许最大输入: ≥-25 → RX: ≥-25, code A
UPDATE product_specs SET field_value = 'RX: ≥-25', field_code = 'A' WHERE field_name = '允许最大输入' AND product_id IN (66,67,68,69,70,71,72,73);

-- =============================================
-- BATCH 3: 按子组修正
-- =============================================
-- 最大输出功率 40W组
UPDATE product_specs SET field_value = '40±2', field_code = '7' WHERE field_name = '最大输出功率' AND product_id IN (66,67,69,72,73);
-- 最大输出功率 2W组
UPDATE product_specs SET field_value = '33±2', field_code = '9' WHERE field_name = '最大输出功率' AND product_id IN (68,70,71);
-- 设备净增益 50±2
UPDATE product_specs SET field_code = '8' WHERE field_name = '设备净增益' AND product_id IN (66,72,73);
-- 设备净增益 45±2
UPDATE product_specs SET field_code = 'C' WHERE field_name = '设备净增益' AND product_id IN (67,68,69,70,71);
-- 载波容量 8
UPDATE product_specs SET field_code = '6' WHERE field_name = '载波容量' AND product_id IN (66,67,69,72,73);
-- 载波容量 4
UPDATE product_specs SET field_code = 'X' WHERE field_name = '载波容量' AND product_id IN (68,70,71);
-- 安装方式: 机柜安装 → 机柜式
UPDATE product_specs SET field_value = '机柜式', field_code = 'T' WHERE field_name = '安装方式' AND product_id IN (66,67,69,72,73);
-- 安装方式: 壁挂安装 → 壁挂式
UPDATE product_specs SET field_value = '壁挂式', field_code = 'K' WHERE field_name = '安装方式' AND product_id IN (68,70,71);
-- 外形尺寸 (仅有值的产品)
UPDATE product_specs SET field_value = '480*480*90', field_code = 'K' WHERE field_name = '外形尺寸' AND product_id IN (66,67,73);
-- 光口类型 LC → code C
UPDATE product_specs SET field_code = 'C' WHERE field_name = '光口类型' AND field_value = 'LC' AND product_id IN (66,67,68,72);
-- 光口类型 FC code F → 6
UPDATE product_specs SET field_code = '6' WHERE field_name = '光口类型' AND field_value = 'FC' AND product_id IN (70,71);

-- =============================================
-- BATCH 4: 工作频率 (每个产品不同)
-- =============================================
UPDATE product_specs SET field_code = 'G' WHERE field_name = '工作频率' AND product_id = 66;
-- 产品 67: 136-174 → C (用户已添加字典)
UPDATE product_specs SET field_code = 'C' WHERE field_name = '工作频率' AND product_id = 67;
UPDATE product_specs SET field_code = 'P' WHERE field_name = '工作频率' AND product_id = 68;
UPDATE product_specs SET field_code = 'T' WHERE field_name = '工作频率' AND product_id = 69;
UPDATE product_specs SET field_code = 'A' WHERE field_name = '工作频率' AND product_id = 70;
UPDATE product_specs SET field_code = '4' WHERE field_name = '工作频率' AND product_id = 71;
UPDATE product_specs SET field_code = 'W' WHERE field_name = '工作频率' AND product_id = 72;
UPDATE product_specs SET field_code = '9' WHERE field_name = '工作频率' AND product_id = 73;

-- =============================================
-- BATCH 5: 新产品工作频率修正
-- =============================================
UPDATE product_specs SET field_code = 'A' WHERE field_name = '工作频率' AND product_id = 209;
UPDATE product_specs SET field_code = '8' WHERE field_name = '工作频率' AND product_id = 213;

-- =============================================
-- BATCH 6: 重建所有受影响产品的快照
-- =============================================
DO $$
DECLARE
    pid INTEGER;
    product_ids INTEGER[] := ARRAY[66,67,68,69,70,71,72,73,205,206,208,209,210,213];
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
