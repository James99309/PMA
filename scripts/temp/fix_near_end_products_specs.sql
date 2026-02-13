-- ============================================
-- 批量修正「数字智能光纤直放站 (近端)」规格到标准字典
-- 产品ID: 75, 76, 78, 79 (跳过77已停产)
-- 参照产品: 74 (HYR2DI000) 标准版
-- 目标: 23项规格，field_name + field_code 与 spec_definitions 完全一致
-- ============================================

BEGIN;

-- ============================================
-- Step 1: 删除不在标准23项中的旧字段 (3个字段 × 4产品)
-- ============================================
DELETE FROM product_specs
WHERE field_name IN ('功能', '阻抗', '电源类型')
AND product_id IN (75,76,78,79);

-- ============================================
-- Step 2: 重命名字段 (10个字段 × 4产品)
-- 旧编码字典名 → 标准规格字典名
-- ============================================
UPDATE product_specs SET field_name='工作频率'
WHERE field_name='频率范围' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_name='允许最大输入'
WHERE field_name='下行最大允许输入电平' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_name='光模块输出功率'
WHERE field_name='光输出功率' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_name='光模块接收灵敏度'
WHERE field_name='光接收灵敏度' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_name='光模块波长'
WHERE field_name='光波长规格' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_name='光口工作模式'
WHERE field_name='光口规格' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_name='接口类型'
WHERE field_name='射频接口类型' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_name='相对湿度'
WHERE field_name='工作湿度' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_name='外形尺寸'
WHERE field_name='尺寸' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_name='延迟同步'
WHERE field_name='延迟同步功能' AND product_id IN (75,76,78,79);

-- ============================================
-- Step 3: 更新 field_code 到标准编码 (19个字段)
-- 包含重命名后的10个 + 同名需改code的9个
-- ============================================

-- 重命名后的10个字段 - 更新code
UPDATE product_specs SET field_code='G'
WHERE field_name='工作频率' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_code='E'
WHERE field_name='允许最大输入' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_code='T'
WHERE field_name='光模块输出功率' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_code='J'
WHERE field_name='光模块接收灵敏度' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_code='K'
WHERE field_name='光模块波长' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_code='6'
WHERE field_name='光口工作模式' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_code='D'
WHERE field_name='接口类型' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_code='8'
WHERE field_name='相对湿度' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_code='K'
WHERE field_name='外形尺寸' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_code='J'
WHERE field_name='延迟同步' AND product_id IN (75,76,78,79);

-- 同名字段 - 更新code
UPDATE product_specs SET field_code='U'
WHERE field_name='增益调节步进' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_code='4'
WHERE field_name='增益调节线性' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_code='X'
WHERE field_name='光口数量' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_code='C'
WHERE field_name='光口类型' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_code='R'
WHERE field_name='显示方式' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_code='H'
WHERE field_name='工作温度' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_code='T'
WHERE field_name='安装方式' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_code='E'
WHERE field_name='防护等级' AND product_id IN (75,76,78,79);

UPDATE product_specs SET field_code='P'
WHERE field_name='监控接口类型' AND product_id IN (75,76,78,79);

-- ============================================
-- Step 4: 新增缺失字段 (3个字段 × 4产品)
-- ============================================

-- 最大输出功率 (code: 7, value留空 - 各产品不同)
INSERT INTO product_specs (product_id, field_name, field_value, field_code, include_in_description, display_order)
SELECT pid, '最大输出功率', '', '7', false, 0
FROM unnest(ARRAY[75,76,78,79]) AS pid;

-- 输入电压(AC) (code: K, value: 220VAC - 从旧"电源类型"拆出)
INSERT INTO product_specs (product_id, field_name, field_value, field_code, include_in_description, display_order)
SELECT pid, '输入电压(AC)', '220VAC', 'K', false, 0
FROM unnest(ARRAY[75,76,78,79]) AS pid;

-- 电源线类型 (code: 6, value: 国标三芯 - 从旧"电源类型"拆出)
INSERT INTO product_specs (product_id, field_name, field_value, field_code, include_in_description, display_order)
SELECT pid, '电源线类型', '国标三芯', '6', false, 0
FROM unnest(ARRAY[75,76,78,79]) AS pid;

-- ============================================
-- Step 5: 统一 value 格式（与产品74一致）
-- 工作频率保留各产品独有值，其余统一
-- ============================================

-- 允许最大输入: 统一为 "+10dBm"
UPDATE product_specs SET field_value='+10dBm'
WHERE field_name='允许最大输入' AND product_id IN (75,76,78,79);

-- 增益调节步进: 统一为 "1"
UPDATE product_specs SET field_value='1'
WHERE field_name='增益调节步进' AND product_id IN (75,76,78,79);

-- 增益调节线性: 统一为 "0–10 ±1"
UPDATE product_specs SET field_value='0–10 ±1'
WHERE field_name='增益调节线性' AND product_id IN (75,76,78,79);

-- 光模块输出功率: 统一为 "≥-6"
UPDATE product_specs SET field_value='≥-6'
WHERE field_name='光模块输出功率' AND product_id IN (75,76,78,79);

-- 光模块接收灵敏度: 统一为 "≤-15"
UPDATE product_specs SET field_value='≤-15'
WHERE field_name='光模块接收灵敏度' AND product_id IN (75,76,78,79);

-- 光模块波长: 统一为 "1310/1550"
UPDATE product_specs SET field_value='1310/1550'
WHERE field_name='光模块波长' AND product_id IN (75,76,78,79);

-- 光口数量: 统一为 "4"
UPDATE product_specs SET field_value='4'
WHERE field_name='光口数量' AND product_id IN (75,76,78,79);

-- 光口类型: 统一为 "LC"
UPDATE product_specs SET field_value='LC'
WHERE field_name='光口类型' AND product_id IN (75,76,78,79);

-- 光口工作模式: 统一为 "双向收发复用"
UPDATE product_specs SET field_value='双向收发复用'
WHERE field_name='光口工作模式' AND product_id IN (75,76,78,79);

-- 输入电压(AC): 已在INSERT时设置为 "220VAC"

-- 电源线类型: 已在INSERT时设置为 "国标三芯"

-- 显示方式: 统一为 "彩色触摸屏"
UPDATE product_specs SET field_value='彩色触摸屏'
WHERE field_name='显示方式' AND product_id IN (75,76,78,79);

-- 延迟同步: 统一为 "具备"
UPDATE product_specs SET field_value='具备'
WHERE field_name='延迟同步' AND product_id IN (75,76,78,79);

-- 工作温度: 统一为 "-20~+55"
UPDATE product_specs SET field_value='-20~+55'
WHERE field_name='工作温度' AND product_id IN (75,76,78,79);

-- 相对湿度: 统一为 "≤95"
UPDATE product_specs SET field_value='≤95'
WHERE field_name='相对湿度' AND product_id IN (75,76,78,79);

-- 外形尺寸: 统一为 "480*480*90"
UPDATE product_specs SET field_value='480*480*90'
WHERE field_name='外形尺寸' AND product_id IN (75,76,78,79);

-- 重量: 清空值（标准中value为空）
UPDATE product_specs SET field_value='', field_code=''
WHERE field_name='重量' AND product_id IN (75,76,78,79);

-- 安装方式: 统一为 "机柜式"
UPDATE product_specs SET field_value='机柜式'
WHERE field_name='安装方式' AND product_id IN (75,76,78,79);

-- 接口类型: 统一为 "N-K"
UPDATE product_specs SET field_value='N-K'
WHERE field_name='接口类型' AND product_id IN (75,76,78,79);

-- 防护等级: 统一为 "IP40"
UPDATE product_specs SET field_value='IP40'
WHERE field_name='防护等级' AND product_id IN (75,76,78,79);

-- 监控接口类型: 统一为 "RJ45"
UPDATE product_specs SET field_value='RJ45'
WHERE field_name='监控接口类型' AND product_id IN (75,76,78,79);

-- ============================================
-- Step 6: 按标准顺序更新 display_order (23项)
-- 与产品74完全一致
-- ============================================
UPDATE product_specs SET display_order = 0 WHERE field_name='工作频率' AND product_id IN (75,76,78,79);
UPDATE product_specs SET display_order = 1 WHERE field_name='最大输出功率' AND product_id IN (75,76,78,79);
UPDATE product_specs SET display_order = 2 WHERE field_name='允许最大输入' AND product_id IN (75,76,78,79);
UPDATE product_specs SET display_order = 3 WHERE field_name='增益调节步进' AND product_id IN (75,76,78,79);
UPDATE product_specs SET display_order = 4 WHERE field_name='增益调节线性' AND product_id IN (75,76,78,79);
UPDATE product_specs SET display_order = 5 WHERE field_name='光模块输出功率' AND product_id IN (75,76,78,79);
UPDATE product_specs SET display_order = 6 WHERE field_name='光模块接收灵敏度' AND product_id IN (75,76,78,79);
UPDATE product_specs SET display_order = 7 WHERE field_name='光模块波长' AND product_id IN (75,76,78,79);
UPDATE product_specs SET display_order = 8 WHERE field_name='光口数量' AND product_id IN (75,76,78,79);
UPDATE product_specs SET display_order = 9 WHERE field_name='光口类型' AND product_id IN (75,76,78,79);
UPDATE product_specs SET display_order = 10 WHERE field_name='光口工作模式' AND product_id IN (75,76,78,79);
UPDATE product_specs SET display_order = 11 WHERE field_name='输入电压(AC)' AND product_id IN (75,76,78,79);
UPDATE product_specs SET display_order = 12 WHERE field_name='电源线类型' AND product_id IN (75,76,78,79);
UPDATE product_specs SET display_order = 13 WHERE field_name='显示方式' AND product_id IN (75,76,78,79);
UPDATE product_specs SET display_order = 14 WHERE field_name='延迟同步' AND product_id IN (75,76,78,79);
UPDATE product_specs SET display_order = 15 WHERE field_name='工作温度' AND product_id IN (75,76,78,79);
UPDATE product_specs SET display_order = 16 WHERE field_name='相对湿度' AND product_id IN (75,76,78,79);
UPDATE product_specs SET display_order = 17 WHERE field_name='外形尺寸' AND product_id IN (75,76,78,79);
UPDATE product_specs SET display_order = 18 WHERE field_name='重量' AND product_id IN (75,76,78,79);
UPDATE product_specs SET display_order = 19 WHERE field_name='安装方式' AND product_id IN (75,76,78,79);
UPDATE product_specs SET display_order = 20 WHERE field_name='接口类型' AND product_id IN (75,76,78,79);
UPDATE product_specs SET display_order = 21 WHERE field_name='防护等级' AND product_id IN (75,76,78,79);
UPDATE product_specs SET display_order = 22 WHERE field_name='监控接口类型' AND product_id IN (75,76,78,79);

COMMIT;

-- ============================================
-- 验证查询：每个产品的记录数应为23
-- ============================================
SELECT product_id, COUNT(*) as spec_count
FROM product_specs
WHERE product_id IN (74,75,76,78,79)
GROUP BY product_id
ORDER BY product_id;

-- 验证：显示产品75的完整规格（作为样本检查）
SELECT id, field_name, field_value, field_code, display_order
FROM product_specs
WHERE product_id = 75
ORDER BY display_order, id;
