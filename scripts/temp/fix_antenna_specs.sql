-- ============================================================
-- 修复「天线」分类 9个活跃产品规格编码
-- 产品ID: 104-111, 113
-- 日期: 2026-02-14
-- ============================================================
-- 产品概况:
--   ID 104: 超薄室内全向吸顶天线 (350-470)
--   ID 105: 智能室内全向吸顶天线 (350-470)
--   ID 106: 智能室内蓝牙全向吸顶天线 (350-470)
--   ID 107: 室外定向板状天线 (400-430)
--   ID 108: 室外全向玻璃钢天线 (136-174)
--   ID 109: 室外全向玻璃钢天线 (350-370)
--   ID 110: 室外全向玻璃钢天线 (400-430)
--   ID 111: 室外八木定向天线 (87-108)
--   ID 113: 防爆型高防护全向天线 (350-470)
-- 预期: 131条→130条, code错误 131→0
-- ============================================================

BEGIN;

-- ============================================================
-- Step 1: 删除无意义/空值字段 (预期 DELETE 12)
-- ============================================================

-- 1a. 功能字段: ALL 9产品 (9行)
DELETE FROM product_specs
WHERE product_id IN (104,105,106,107,108,109,110,111,113)
  AND field_name = '功能';
-- 预期: DELETE 9

-- 1b. 馈电电流: ID 105,106 (2行)
DELETE FROM product_specs
WHERE product_id IN (105,106)
  AND field_name = '馈电电流';
-- 预期: DELETE 2

-- 1c. 空值垂直辐射角度: ID 111 (1行)
DELETE FROM product_specs
WHERE product_id = 111
  AND field_name = '垂直辐射角度'
  AND (field_value IS NULL OR field_value = '');
-- 预期: DELETE 1

-- ============================================================
-- Step 2: 通用重命名+值修正 (全9产品)
-- ============================================================

-- 2a. 频率范围→工作频率 (按频段分code)
-- ID 104,105,106,113: 350-470, code=7
UPDATE product_specs SET field_name = '工作频率', field_code = '7'
WHERE product_id IN (104,105,106,113)
  AND field_name = '频率范围';

-- ID 107,110: 400-430, code=R
UPDATE product_specs SET field_name = '工作频率', field_code = 'R'
WHERE product_id IN (107,110)
  AND field_name = '频率范围';

-- ID 108: 136-174, code=C
UPDATE product_specs SET field_name = '工作频率', field_code = 'C'
WHERE product_id = 108
  AND field_name = '频率范围';

-- ID 109: 350-370, code=3
UPDATE product_specs SET field_name = '工作频率', field_code = '3'
WHERE product_id = 109
  AND field_name = '频率范围';

-- ID 111: 87-108, code=G
UPDATE product_specs SET field_name = '工作频率', field_code = 'G'
WHERE product_id = 111
  AND field_name = '频率范围';

-- 2b. 承载功率→功率容量 (按值分code)
-- 50W产品: code=R
UPDATE product_specs SET field_name = '功率容量', field_code = 'R'
WHERE product_id IN (104,105,106,107,108,109,110,111,113)
  AND field_name = '承载功率'
  AND field_value = '50';

-- 100W产品: code=E
UPDATE product_specs SET field_name = '功率容量', field_code = 'E'
WHERE product_id IN (104,105,106,107,108,109,110,111,113)
  AND field_name = '承载功率'
  AND field_value = '100';

-- 2c. 天线增益→增益 (按值分code和值修正)
-- 0+3 → 0±3, code=A
UPDATE product_specs SET field_name = '增益', field_value = '0±3', field_code = 'A'
WHERE product_id IN (104,105,106,107,108,109,110,111,113)
  AND field_name = '天线增益'
  AND field_value LIKE '%0%3%';

-- 5 ± 0.5 → 5±0.5, code=Y
UPDATE product_specs SET field_name = '增益', field_value = '5±0.5', field_code = 'Y'
WHERE product_id IN (104,105,106,107,108,109,110,111,113)
  AND field_name = '天线增益'
  AND field_value LIKE '%5%0.5%';

-- 2d. 辐射方向 值修正 (只改值不改名)
-- 垂直极化，全向→全向, code=X
UPDATE product_specs SET field_value = '全向', field_code = 'X'
WHERE product_id IN (104,105,106,107,108,109,110,111,113)
  AND field_name = '辐射方向'
  AND field_value LIKE '%全向%';

-- 垂直极化，定向→定向, code=L
UPDATE product_specs SET field_value = '定向', field_code = 'L'
WHERE product_id IN (104,105,106,107,108,109,110,111,113)
  AND field_name = '辐射方向'
  AND field_value LIKE '%定向%';

-- 2e. 阻抗→射频阻抗, code=R
UPDATE product_specs SET field_name = '射频阻抗', field_code = 'R'
WHERE product_id IN (104,105,106,107,108,109,110,111,113)
  AND field_name = '阻抗';

-- 2f. 射频接口类型→接口类型, code=D
UPDATE product_specs SET field_name = '接口类型', field_code = 'D'
WHERE product_id IN (104,105,106,107,108,109,110,111,113)
  AND field_name = '射频接口类型';

-- 2g. 工作温度 值修正, code=H
UPDATE product_specs SET field_value = '-20~+55', field_code = 'H'
WHERE product_id IN (104,105,106,107,108,109,110,111,113)
  AND field_name = '工作温度';

-- 2h. 工作湿度→相对湿度, value=≤95, code=8
UPDATE product_specs SET field_name = '相对湿度', field_value = '≤95', field_code = '8'
WHERE product_id IN (104,105,106,107,108,109,110,111,113)
  AND field_name = '工作湿度';

-- 2i. 水平辐射角度→水平辐射角, value=360°, code=9
UPDATE product_specs SET field_name = '水平辐射角', field_value = '360°', field_code = '9'
WHERE product_id IN (104,105,106,107,108,109,110,111,113)
  AND field_name = '水平辐射角度';

-- 2j. 垂直辐射角度→垂直辐射角, value=45°, code=F (8产品, 排除ID111)
UPDATE product_specs SET field_name = '垂直辐射角', field_value = '45°', field_code = 'F'
WHERE product_id IN (104,105,106,107,108,109,110,113)
  AND field_name = '垂直辐射角度';

-- 2k. 驻波比 code修正 (按值分code)
-- ≤2.5 → code=L
UPDATE product_specs SET field_code = 'L'
WHERE product_id IN (104,105,106,107,108,109,110,111,113)
  AND field_name = '驻波比'
  AND field_value LIKE '%2.5%';

-- ≤1.5 → code=K
UPDATE product_specs SET field_code = 'K'
WHERE product_id IN (104,105,106,107,108,109,110,111,113)
  AND field_name = '驻波比'
  AND field_value LIKE '%1.5%';

-- 2l. 防护等级 code修正 (按值分code)
-- IP53 → code=J
UPDATE product_specs SET field_code = 'J'
WHERE product_id IN (104,105,106,107,108,109,110,111,113)
  AND field_name = '防护等级'
  AND field_value = 'IP53';

-- IP65 → code=M
UPDATE product_specs SET field_code = 'M'
WHERE product_id IN (104,105,106,107,108,109,110,111,113)
  AND field_name = '防护等级'
  AND field_value = 'IP65';

-- 2m. 安装方式 值+code修正
-- 吊顶 / 壁挂 → 吊顶/壁挂, code=E
UPDATE product_specs SET field_value = '吊顶/壁挂', field_code = 'E'
WHERE product_id IN (104,105,106,107,108,109,110,111,113)
  AND field_name = '安装方式'
  AND field_value LIKE '%吊顶%壁挂%';

-- 室外支架 → code=B
UPDATE product_specs SET field_code = 'B'
WHERE product_id IN (104,105,106,107,108,109,110,111,113)
  AND field_name = '安装方式'
  AND field_value = '室外支架';

-- 室外壁挂 → 室外支架, code=B
UPDATE product_specs SET field_value = '室外支架', field_code = 'B'
WHERE product_id IN (104,105,106,107,108,109,110,111,113)
  AND field_name = '安装方式'
  AND field_value = '室外壁挂';

-- 2n. 防爆等级 code修正 (仅ID 113)
UPDATE product_specs SET field_code = 'G'
WHERE product_id = 113
  AND field_name = '防爆等级';

-- ============================================================
-- Step 3: 馈电产品特殊处理 (ID 105,106)
-- ============================================================

-- 馈电电压→输入电压(DC), value=≤5-28, code=M
UPDATE product_specs SET field_name = '输入电压(DC)', field_value = '≤5-28', field_code = 'M'
WHERE product_id IN (105,106)
  AND field_name = '馈电电压';

-- ============================================================
-- Step 4: 新增字段 (INSERT)
-- ============================================================

-- 4a. 极化方式=垂直极化/P: ALL 9产品 (9行)
INSERT INTO product_specs (product_id, field_name, field_value, field_code, include_in_description, display_order)
VALUES
  (104, '极化方式', '垂直极化', 'P', false, 3),
  (105, '极化方式', '垂直极化', 'P', false, 3),
  (106, '极化方式', '垂直极化', 'P', false, 3),
  (107, '极化方式', '垂直极化', 'P', false, 3),
  (108, '极化方式', '垂直极化', 'P', false, 3),
  (109, '极化方式', '垂直极化', 'P', false, 3),
  (110, '极化方式', '垂直极化', 'P', false, 3),
  (111, '极化方式', '垂直极化', 'P', false, 3),
  (113, '极化方式', '垂直极化', 'P', false, 3);

-- 4b. 状态指示灯=具备/J: ID 105 (1行)
INSERT INTO product_specs (product_id, field_name, field_value, field_code, include_in_description, display_order)
VALUES (105, '状态指示灯', '具备', 'J', false, 14);

-- 4c. 蓝牙信标=具备/J: ID 106 (1行)
INSERT INTO product_specs (product_id, field_name, field_value, field_code, include_in_description, display_order)
VALUES (106, '蓝牙信标', '具备', 'J', false, 14);

-- ============================================================
-- Step 5: display_order 设置
-- ============================================================

-- 5a. 标准天线 (ID 104,107,108,109,110), 14项
-- 0:工作频率 1:增益 2:辐射方向 3:极化方式 4:功率容量 5:驻波比
-- 6:射频阻抗 7:水平辐射角 8:垂直辐射角 9:防护等级 10:安装方式
-- 11:接口类型 12:工作温度 13:相对湿度
UPDATE product_specs SET display_order = 0 WHERE product_id IN (104,107,108,109,110) AND field_name = '工作频率';
UPDATE product_specs SET display_order = 1 WHERE product_id IN (104,107,108,109,110) AND field_name = '增益';
UPDATE product_specs SET display_order = 2 WHERE product_id IN (104,107,108,109,110) AND field_name = '辐射方向';
UPDATE product_specs SET display_order = 3 WHERE product_id IN (104,107,108,109,110) AND field_name = '极化方式';
UPDATE product_specs SET display_order = 4 WHERE product_id IN (104,107,108,109,110) AND field_name = '功率容量';
UPDATE product_specs SET display_order = 5 WHERE product_id IN (104,107,108,109,110) AND field_name = '驻波比';
UPDATE product_specs SET display_order = 6 WHERE product_id IN (104,107,108,109,110) AND field_name = '射频阻抗';
UPDATE product_specs SET display_order = 7 WHERE product_id IN (104,107,108,109,110) AND field_name = '水平辐射角';
UPDATE product_specs SET display_order = 8 WHERE product_id IN (104,107,108,109,110) AND field_name = '垂直辐射角';
UPDATE product_specs SET display_order = 9 WHERE product_id IN (104,107,108,109,110) AND field_name = '防护等级';
UPDATE product_specs SET display_order = 10 WHERE product_id IN (104,107,108,109,110) AND field_name = '安装方式';
UPDATE product_specs SET display_order = 11 WHERE product_id IN (104,107,108,109,110) AND field_name = '接口类型';
UPDATE product_specs SET display_order = 12 WHERE product_id IN (104,107,108,109,110) AND field_name = '工作温度';
UPDATE product_specs SET display_order = 13 WHERE product_id IN (104,107,108,109,110) AND field_name = '相对湿度';

-- 5b. 智能LED (ID 105), 16项
-- 同标准14项 + 14:状态指示灯 + 15:输入电压(DC)
UPDATE product_specs SET display_order = 0 WHERE product_id = 105 AND field_name = '工作频率';
UPDATE product_specs SET display_order = 1 WHERE product_id = 105 AND field_name = '增益';
UPDATE product_specs SET display_order = 2 WHERE product_id = 105 AND field_name = '辐射方向';
UPDATE product_specs SET display_order = 3 WHERE product_id = 105 AND field_name = '极化方式';
UPDATE product_specs SET display_order = 4 WHERE product_id = 105 AND field_name = '功率容量';
UPDATE product_specs SET display_order = 5 WHERE product_id = 105 AND field_name = '驻波比';
UPDATE product_specs SET display_order = 6 WHERE product_id = 105 AND field_name = '射频阻抗';
UPDATE product_specs SET display_order = 7 WHERE product_id = 105 AND field_name = '水平辐射角';
UPDATE product_specs SET display_order = 8 WHERE product_id = 105 AND field_name = '垂直辐射角';
UPDATE product_specs SET display_order = 9 WHERE product_id = 105 AND field_name = '防护等级';
UPDATE product_specs SET display_order = 10 WHERE product_id = 105 AND field_name = '安装方式';
UPDATE product_specs SET display_order = 11 WHERE product_id = 105 AND field_name = '接口类型';
UPDATE product_specs SET display_order = 12 WHERE product_id = 105 AND field_name = '工作温度';
UPDATE product_specs SET display_order = 13 WHERE product_id = 105 AND field_name = '相对湿度';
UPDATE product_specs SET display_order = 14 WHERE product_id = 105 AND field_name = '状态指示灯';
UPDATE product_specs SET display_order = 15 WHERE product_id = 105 AND field_name = '输入电压(DC)';

-- 5c. 智能蓝牙 (ID 106), 16项
-- 同标准14项 + 14:蓝牙信标 + 15:输入电压(DC)
UPDATE product_specs SET display_order = 0 WHERE product_id = 106 AND field_name = '工作频率';
UPDATE product_specs SET display_order = 1 WHERE product_id = 106 AND field_name = '增益';
UPDATE product_specs SET display_order = 2 WHERE product_id = 106 AND field_name = '辐射方向';
UPDATE product_specs SET display_order = 3 WHERE product_id = 106 AND field_name = '极化方式';
UPDATE product_specs SET display_order = 4 WHERE product_id = 106 AND field_name = '功率容量';
UPDATE product_specs SET display_order = 5 WHERE product_id = 106 AND field_name = '驻波比';
UPDATE product_specs SET display_order = 6 WHERE product_id = 106 AND field_name = '射频阻抗';
UPDATE product_specs SET display_order = 7 WHERE product_id = 106 AND field_name = '水平辐射角';
UPDATE product_specs SET display_order = 8 WHERE product_id = 106 AND field_name = '垂直辐射角';
UPDATE product_specs SET display_order = 9 WHERE product_id = 106 AND field_name = '防护等级';
UPDATE product_specs SET display_order = 10 WHERE product_id = 106 AND field_name = '安装方式';
UPDATE product_specs SET display_order = 11 WHERE product_id = 106 AND field_name = '接口类型';
UPDATE product_specs SET display_order = 12 WHERE product_id = 106 AND field_name = '工作温度';
UPDATE product_specs SET display_order = 13 WHERE product_id = 106 AND field_name = '相对湿度';
UPDATE product_specs SET display_order = 14 WHERE product_id = 106 AND field_name = '蓝牙信标';
UPDATE product_specs SET display_order = 15 WHERE product_id = 106 AND field_name = '输入电压(DC)';

-- 5d. 八木 (ID 111), 13项 (无垂直辐射角)
-- 0:工作频率 1:增益 2:辐射方向 3:极化方式 4:功率容量 5:驻波比
-- 6:射频阻抗 7:水平辐射角 8:防护等级 9:安装方式
-- 10:接口类型 11:工作温度 12:相对湿度
UPDATE product_specs SET display_order = 0 WHERE product_id = 111 AND field_name = '工作频率';
UPDATE product_specs SET display_order = 1 WHERE product_id = 111 AND field_name = '增益';
UPDATE product_specs SET display_order = 2 WHERE product_id = 111 AND field_name = '辐射方向';
UPDATE product_specs SET display_order = 3 WHERE product_id = 111 AND field_name = '极化方式';
UPDATE product_specs SET display_order = 4 WHERE product_id = 111 AND field_name = '功率容量';
UPDATE product_specs SET display_order = 5 WHERE product_id = 111 AND field_name = '驻波比';
UPDATE product_specs SET display_order = 6 WHERE product_id = 111 AND field_name = '射频阻抗';
UPDATE product_specs SET display_order = 7 WHERE product_id = 111 AND field_name = '水平辐射角';
UPDATE product_specs SET display_order = 8 WHERE product_id = 111 AND field_name = '防护等级';
UPDATE product_specs SET display_order = 9 WHERE product_id = 111 AND field_name = '安装方式';
UPDATE product_specs SET display_order = 10 WHERE product_id = 111 AND field_name = '接口类型';
UPDATE product_specs SET display_order = 11 WHERE product_id = 111 AND field_name = '工作温度';
UPDATE product_specs SET display_order = 12 WHERE product_id = 111 AND field_name = '相对湿度';

-- 5e. 防爆 (ID 113), 15项
-- 0:工作频率 1:增益 2:辐射方向 3:极化方式 4:功率容量 5:驻波比
-- 6:射频阻抗 7:水平辐射角 8:垂直辐射角 9:防爆等级 10:防护等级
-- 11:安装方式 12:接口类型 13:工作温度 14:相对湿度
UPDATE product_specs SET display_order = 0 WHERE product_id = 113 AND field_name = '工作频率';
UPDATE product_specs SET display_order = 1 WHERE product_id = 113 AND field_name = '增益';
UPDATE product_specs SET display_order = 2 WHERE product_id = 113 AND field_name = '辐射方向';
UPDATE product_specs SET display_order = 3 WHERE product_id = 113 AND field_name = '极化方式';
UPDATE product_specs SET display_order = 4 WHERE product_id = 113 AND field_name = '功率容量';
UPDATE product_specs SET display_order = 5 WHERE product_id = 113 AND field_name = '驻波比';
UPDATE product_specs SET display_order = 6 WHERE product_id = 113 AND field_name = '射频阻抗';
UPDATE product_specs SET display_order = 7 WHERE product_id = 113 AND field_name = '水平辐射角';
UPDATE product_specs SET display_order = 8 WHERE product_id = 113 AND field_name = '垂直辐射角';
UPDATE product_specs SET display_order = 9 WHERE product_id = 113 AND field_name = '防爆等级';
UPDATE product_specs SET display_order = 10 WHERE product_id = 113 AND field_name = '防护等级';
UPDATE product_specs SET display_order = 11 WHERE product_id = 113 AND field_name = '安装方式';
UPDATE product_specs SET display_order = 12 WHERE product_id = 113 AND field_name = '接口类型';
UPDATE product_specs SET display_order = 13 WHERE product_id = 113 AND field_name = '工作温度';
UPDATE product_specs SET display_order = 14 WHERE product_id = 113 AND field_name = '相对湿度';

-- ============================================================
-- Step 6: 验证
-- ============================================================

-- 6a. 总行数验证 (预期 130)
SELECT '总行数' AS check_name, COUNT(*) AS cnt,
  CASE WHEN COUNT(*) = 130 THEN 'PASS' ELSE 'FAIL (expected 130)' END AS result
FROM product_specs
WHERE product_id IN (104,105,106,107,108,109,110,111,113);

-- 6b. 每个产品行数验证
SELECT p.id, p.product_name, COUNT(ps.id) AS spec_count,
  CASE
    WHEN p.id IN (104,107,108,109,110) AND COUNT(ps.id) = 14 THEN 'PASS (14)'
    WHEN p.id = 105 AND COUNT(ps.id) = 16 THEN 'PASS (16)'
    WHEN p.id = 106 AND COUNT(ps.id) = 16 THEN 'PASS (16)'
    WHEN p.id = 111 AND COUNT(ps.id) = 13 THEN 'PASS (13)'
    WHEN p.id = 113 AND COUNT(ps.id) = 15 THEN 'PASS (15)'
    ELSE 'FAIL'
  END AS result
FROM products p
LEFT JOIN product_specs ps ON ps.product_id = p.id
WHERE p.id IN (104,105,106,107,108,109,110,111,113)
GROUP BY p.id, p.product_name
ORDER BY p.id;

-- 6c. code匹配验证 (与字典对照, 预期0 MISMATCH)
SELECT ps.product_id, ps.field_name, ps.field_value, ps.field_code,
  so.code AS dict_code,
  CASE WHEN ps.field_code = so.code THEN 'MATCH' ELSE 'MISMATCH' END AS status
FROM product_specs ps
JOIN specification_dictionary sd ON sd.name = ps.field_name
JOIN specification_options so ON so.spec_id = sd.id AND so.value = ps.field_value
WHERE ps.product_id IN (104,105,106,107,108,109,110,111,113)
ORDER BY ps.product_id, ps.display_order;

-- 6d. 无字典匹配检查 (预期 0)
SELECT ps.product_id, ps.field_name, ps.field_value, ps.field_code
FROM product_specs ps
WHERE ps.product_id IN (104,105,106,107,108,109,110,111,113)
  AND NOT EXISTS (
    SELECT 1 FROM specification_dictionary sd
    JOIN specification_options so ON so.spec_id = sd.id
    WHERE sd.name = ps.field_name AND so.value = ps.field_value
  );

COMMIT;
