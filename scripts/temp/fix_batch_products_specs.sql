-- ============================================
-- 批量修正7个同名产品的规格字段
-- 产品ID: 66, 68, 69, 70, 71, 72, 73
-- 与产品67修正内容完全一致
-- ============================================

BEGIN;

-- ============================================
-- Step 1: 重命名字段名（16个字段 × 7产品）
-- ============================================
UPDATE product_specs SET field_name='工作频率' WHERE field_name='频率范围' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET field_name='设备净增益' WHERE field_name='增益' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET field_name='射频阻抗' WHERE field_name='阻抗' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET field_name='噪声系数(上行)' WHERE field_name='噪声系数' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET field_name='自动电平控制范围（ALC）' WHERE field_name='ALC自动调节范围' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET field_name='延时' WHERE field_name='时延' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET field_name='允许最大输入' WHERE field_name='上行最大允许输入电平' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET field_name='光模块输出功率' WHERE field_name='光输出功率' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET field_name='光模块接收灵敏度' WHERE field_name='光接收灵敏度' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET field_name='光模块波长' WHERE field_name='光波长规格' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET field_name='光口工作模式' WHERE field_name='光口规格' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET field_name='供电规格' WHERE field_name='电源类型' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET field_name='相对湿度' WHERE field_name='工作湿度' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET field_name='接口类型' WHERE field_name='射频接口类型' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET field_name='外形尺寸' WHERE field_name='尺寸' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET field_name='驻波比' WHERE field_name='输入输出驻波比' AND product_id IN (66,68,69,70,71,72,73);

-- ============================================
-- Step 2: 拆分"增益调节步进"（值=30/1）
-- 将原"增益调节步进"改为"增益调节范围"，值=30
-- 新增"增益调节步进"，值=1
-- ============================================
UPDATE product_specs SET field_name='增益调节范围', field_value='30'
WHERE field_name='增益调节步进' AND product_id IN (66,68,69,70,71,72,73);

INSERT INTO product_specs (product_id, field_name, field_value, include_in_description, display_order)
SELECT pid, '增益调节步进', '1', false, 0
FROM unnest(ARRAY[66,68,69,70,71,72,73]) AS pid;

-- ============================================
-- Step 3: 删除多余项（4条 × 7产品）
-- 注：这7个产品没有"延迟同步功能"字段
-- ============================================
DELETE FROM product_specs
WHERE field_name IN ('功能', '频率特性', '馈电功能', '重量')
AND product_id IN (66,68,69,70,71,72,73);

-- ============================================
-- Step 4: 新增缺失项（2条 × 7产品）
-- ============================================
INSERT INTO product_specs (product_id, field_name, field_value, include_in_description, display_order)
SELECT pid, '电源线类型', '国标三芯', false, 0
FROM unnest(ARRAY[66,68,69,70,71,72,73]) AS pid;

INSERT INTO product_specs (product_id, field_name, field_value, include_in_description, display_order)
SELECT pid, '光跳纤', '', false, 0
FROM unnest(ARRAY[66,68,69,70,71,72,73]) AS pid;

-- ============================================
-- Step 5: 按标准顺序更新 display_order（34个字段）
-- 顺序与产品67/206一致
-- ============================================
UPDATE product_specs SET display_order = 1 WHERE field_name='工作频率' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 2 WHERE field_name='最大输出功率' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 3 WHERE field_name='载波容量' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 4 WHERE field_name='增益调节范围' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 5 WHERE field_name='增益调节步进' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 6 WHERE field_name='增益调节线性' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 7 WHERE field_name='设备净增益' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 8 WHERE field_name='带内波动' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 9 WHERE field_name='上下行隔离度' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 10 WHERE field_name='带外杂散' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 11 WHERE field_name='互调衰减' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 12 WHERE field_name='射频阻抗' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 13 WHERE field_name='噪声系数(上行)' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 14 WHERE field_name='自动电平控制范围（ALC）' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 15 WHERE field_name='延时' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 16 WHERE field_name='允许最大输入' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 17 WHERE field_name='驻波比' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 18 WHERE field_name='接口类型' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 19 WHERE field_name='光口类型' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 20 WHERE field_name='光口数量' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 21 WHERE field_name='光模块输出功率' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 22 WHERE field_name='光模块接收灵敏度' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 23 WHERE field_name='光模块波长' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 24 WHERE field_name='光口工作模式' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 25 WHERE field_name='光跳纤' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 26 WHERE field_name='供电规格' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 27 WHERE field_name='电源线类型' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 28 WHERE field_name='显示方式' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 29 WHERE field_name='工作温度' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 30 WHERE field_name='相对湿度' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 31 WHERE field_name='安装方式' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 32 WHERE field_name='防护等级' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 33 WHERE field_name='监控接口类型' AND product_id IN (66,68,69,70,71,72,73);
UPDATE product_specs SET display_order = 34 WHERE field_name='外形尺寸' AND product_id IN (66,68,69,70,71,72,73);

COMMIT;

-- ============================================
-- 验证查询：每个产品的记录数应为34
-- ============================================
SELECT product_id, COUNT(*) as spec_count
FROM product_specs
WHERE product_id IN (66,67,68,69,70,71,72,73)
GROUP BY product_id
ORDER BY product_id;

-- 验证：显示产品66的完整规格（作为样本检查）
SELECT id, field_name, field_value, display_order
FROM product_specs
WHERE product_id = 66
ORDER BY display_order, id;
