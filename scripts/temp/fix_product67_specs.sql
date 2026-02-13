-- ============================================
-- 产品 67 (RFT-BDA110 LT/M) 规格修正脚本
-- 以产品 206 (EORAEK9C63) 的规格名称为标准
-- ============================================

BEGIN;

-- ============================================
-- Step 1: 重命名字段名（16条 UPDATE）
-- ============================================
UPDATE product_specs SET field_name='工作频率' WHERE id=4253;
UPDATE product_specs SET field_name='设备净增益' WHERE id=4263;
UPDATE product_specs SET field_name='射频阻抗' WHERE id=4268;
UPDATE product_specs SET field_name='噪声系数(上行)' WHERE id=4265;
UPDATE product_specs SET field_name='自动电平控制范围（ALC）' WHERE id=4267;
UPDATE product_specs SET field_name='延时' WHERE id=4269;
UPDATE product_specs SET field_name='允许最大输入' WHERE id=4271;
UPDATE product_specs SET field_name='光模块输出功率' WHERE id=4282;
UPDATE product_specs SET field_name='光模块接收灵敏度' WHERE id=4283;
UPDATE product_specs SET field_name='光模块波长' WHERE id=4284;
UPDATE product_specs SET field_name='光口工作模式' WHERE id=4285;
UPDATE product_specs SET field_name='供电规格' WHERE id=4255;
UPDATE product_specs SET field_name='相对湿度' WHERE id=4276;
UPDATE product_specs SET field_name='接口类型' WHERE id=4266;
UPDATE product_specs SET field_name='外形尺寸' WHERE id=4272;
UPDATE product_specs SET field_name='驻波比' WHERE id=4280;

-- ============================================
-- Step 2: 拆分"增益调节步进"为两条
-- ============================================
-- 将原 id=4262 修改为"增益调节范围"，值=30
UPDATE product_specs SET field_name='增益调节范围', field_value='30' WHERE id=4262;
-- 新增"增益调节步进"，值=1
INSERT INTO product_specs (product_id, field_name, field_value, include_in_description, display_order)
VALUES (67, '增益调节步进', '1', false, 0);

-- ============================================
-- Step 3: 删除多余项（5条）
-- ============================================
DELETE FROM product_specs WHERE id IN (
    4258,  -- 功能=无
    4288,  -- 延迟同步功能=具备
    4270,  -- 重量=(空)
    4260,  -- 频率特性=双工器可调
    4261   -- 馈电功能=无馈电
);

-- ============================================
-- Step 4: 新增缺失项（2条）
-- ============================================
INSERT INTO product_specs (product_id, field_name, field_value, include_in_description, display_order)
VALUES (67, '电源线类型', '国标三芯', false, 0);

INSERT INTO product_specs (product_id, field_name, field_value, include_in_description, display_order)
VALUES (67, '光跳纤', '', false, 0);

-- ============================================
-- Step 5: 按标准顺序更新 display_order
-- 顺序参照产品206的规格排列
-- ============================================
UPDATE product_specs SET display_order = 1 WHERE product_id=67 AND field_name='工作频率';
UPDATE product_specs SET display_order = 2 WHERE product_id=67 AND field_name='最大输出功率';
UPDATE product_specs SET display_order = 3 WHERE product_id=67 AND field_name='载波容量';
UPDATE product_specs SET display_order = 4 WHERE product_id=67 AND field_name='增益调节范围';
UPDATE product_specs SET display_order = 5 WHERE product_id=67 AND field_name='增益调节步进';
UPDATE product_specs SET display_order = 6 WHERE product_id=67 AND field_name='增益调节线性';
UPDATE product_specs SET display_order = 7 WHERE product_id=67 AND field_name='设备净增益';
UPDATE product_specs SET display_order = 8 WHERE product_id=67 AND field_name='带内波动';
UPDATE product_specs SET display_order = 9 WHERE product_id=67 AND field_name='上下行隔离度';
UPDATE product_specs SET display_order = 10 WHERE product_id=67 AND field_name='带外杂散';
UPDATE product_specs SET display_order = 11 WHERE product_id=67 AND field_name='互调衰减';
UPDATE product_specs SET display_order = 12 WHERE product_id=67 AND field_name='射频阻抗';
UPDATE product_specs SET display_order = 13 WHERE product_id=67 AND field_name='噪声系数(上行)';
UPDATE product_specs SET display_order = 14 WHERE product_id=67 AND field_name='自动电平控制范围（ALC）';
UPDATE product_specs SET display_order = 15 WHERE product_id=67 AND field_name='延时';
UPDATE product_specs SET display_order = 16 WHERE product_id=67 AND field_name='允许最大输入';
UPDATE product_specs SET display_order = 17 WHERE product_id=67 AND field_name='驻波比';
UPDATE product_specs SET display_order = 18 WHERE product_id=67 AND field_name='接口类型';
UPDATE product_specs SET display_order = 19 WHERE product_id=67 AND field_name='光口类型';
UPDATE product_specs SET display_order = 20 WHERE product_id=67 AND field_name='光口数量';
UPDATE product_specs SET display_order = 21 WHERE product_id=67 AND field_name='光模块输出功率';
UPDATE product_specs SET display_order = 22 WHERE product_id=67 AND field_name='光模块接收灵敏度';
UPDATE product_specs SET display_order = 23 WHERE product_id=67 AND field_name='光模块波长';
UPDATE product_specs SET display_order = 24 WHERE product_id=67 AND field_name='光口工作模式';
UPDATE product_specs SET display_order = 25 WHERE product_id=67 AND field_name='光跳纤';
UPDATE product_specs SET display_order = 26 WHERE product_id=67 AND field_name='供电规格';
UPDATE product_specs SET display_order = 27 WHERE product_id=67 AND field_name='电源线类型';
UPDATE product_specs SET display_order = 28 WHERE product_id=67 AND field_name='显示方式';
UPDATE product_specs SET display_order = 29 WHERE product_id=67 AND field_name='工作温度';
UPDATE product_specs SET display_order = 30 WHERE product_id=67 AND field_name='相对湿度';
UPDATE product_specs SET display_order = 31 WHERE product_id=67 AND field_name='安装方式';
UPDATE product_specs SET display_order = 32 WHERE product_id=67 AND field_name='防护等级';
UPDATE product_specs SET display_order = 33 WHERE product_id=67 AND field_name='监控接口类型';
UPDATE product_specs SET display_order = 34 WHERE product_id=67 AND field_name='外形尺寸';

COMMIT;

-- ============================================
-- 验证查询
-- ============================================
SELECT id, field_name, field_value, display_order
FROM product_specs
WHERE product_id=67
ORDER BY display_order, id;
