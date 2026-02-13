-- ============================================================
-- 修复产品 86「数字智能光纤交织型远端直放站」规格编码
-- 产品编号: HYR3DI34J, product_id = 86
-- 36 项 → 删 3 项 = 33 项
-- ============================================================

BEGIN;

-- ============================================================
-- Step 1: 删除 3 个废弃字段
-- ============================================================
DELETE FROM product_specs
WHERE product_id = 86 AND field_name IN ('频率特性', '馈电功能', '重量');

-- ============================================================
-- Step 2: 重命名「功能」→「组网结构」并设 code
-- ============================================================
UPDATE product_specs
SET field_name = '组网结构', field_value = '交织', field_code = 'N'
WHERE product_id = 86 AND field_name = '功能';

-- ============================================================
-- Step 3: 重命名 17 个字段 + 修值 + 修 code
-- ============================================================

-- 频率范围 → 工作频率
UPDATE product_specs
SET field_name = '工作频率', field_value = '400-470', field_code = 'W'
WHERE product_id = 86 AND field_name = '频率范围';

-- 增益 → 设备净增益
UPDATE product_specs
SET field_name = '设备净增益', field_value = '50±2', field_code = '8'
WHERE product_id = 86 AND field_name = '增益';

-- 噪声系数 → 噪声系数(上行)
UPDATE product_specs
SET field_name = '噪声系数(上行)', field_value = '≤7', field_code = '7'
WHERE product_id = 86 AND field_name = '噪声系数';

-- ALC自动调节范围 → 自动电平控制范围（ALC）
UPDATE product_specs
SET field_name = '自动电平控制范围（ALC）', field_value = '≥30', field_code = 'T'
WHERE product_id = 86 AND field_name = 'ALC自动调节范围';

-- 上行最大允许输入电平 → 允许最大输入
UPDATE product_specs
SET field_name = '允许最大输入', field_value = 'RX: ≥-25', field_code = 'A'
WHERE product_id = 86 AND field_name = '上行最大允许输入电平';

-- 阻抗 → 射频阻抗
UPDATE product_specs
SET field_name = '射频阻抗', field_value = '50', field_code = 'R'
WHERE product_id = 86 AND field_name = '阻抗';

-- 时延 → 延时
UPDATE product_specs
SET field_name = '延时', field_value = '≤35', field_code = 'X'
WHERE product_id = 86 AND field_name = '时延';

-- 射频接口类型 → 接口类型
UPDATE product_specs
SET field_name = '接口类型', field_value = 'N-K', field_code = 'D'
WHERE product_id = 86 AND field_name = '射频接口类型';

-- 电源类型 → 供电规格
UPDATE product_specs
SET field_name = '供电规格', field_value = '220V±15%', field_code = 'E'
WHERE product_id = 86 AND field_name = '电源类型';

-- 尺寸 → 外形尺寸
UPDATE product_specs
SET field_name = '外形尺寸', field_value = '480*480*90', field_code = 'K'
WHERE product_id = 86 AND field_name = '尺寸';

-- 工作湿度 → 相对湿度
UPDATE product_specs
SET field_name = '相对湿度', field_value = '≤95', field_code = '8'
WHERE product_id = 86 AND field_name = '工作湿度';

-- 输入输出驻波比 → 驻波比
UPDATE product_specs
SET field_name = '驻波比', field_value = '≤1.5', field_code = 'K'
WHERE product_id = 86 AND field_name = '输入输出驻波比';

-- 光输出功率 → 光模块输出功率
UPDATE product_specs
SET field_name = '光模块输出功率', field_value = '≥-6', field_code = 'T'
WHERE product_id = 86 AND field_name = '光输出功率';

-- 光接收灵敏度 → 光模块接收灵敏度
UPDATE product_specs
SET field_name = '光模块接收灵敏度', field_value = '≤-15', field_code = 'J'
WHERE product_id = 86 AND field_name = '光接收灵敏度';

-- 光波长规格 → 光模块波长
UPDATE product_specs
SET field_name = '光模块波长', field_value = '1310/1550', field_code = 'K'
WHERE product_id = 86 AND field_name = '光波长规格';

-- 光口规格 → 光口工作模式
UPDATE product_specs
SET field_name = '光口工作模式', field_value = '双向收发复用', field_code = '6'
WHERE product_id = 86 AND field_name = '光口规格';

-- 延迟同步功能 → 延迟同步
UPDATE product_specs
SET field_name = '延迟同步', field_value = '具备', field_code = 'J'
WHERE product_id = 86 AND field_name = '延迟同步功能';

-- ============================================================
-- Step 4: 修正未改名但需修值/code 的字段
-- ============================================================

-- 最大输出功率
UPDATE product_specs
SET field_value = '40±2', field_code = '7'
WHERE product_id = 86 AND field_name = '最大输出功率';

-- 带外杂散
UPDATE product_specs
SET field_value = '9kHz~1GHz：≤-36dBm；1GHz~12.75GHz：≤-30dBm', field_code = 'P'
WHERE product_id = 86 AND field_name = '带外杂散';

-- 互调衰减
UPDATE product_specs
SET field_value = '≤-50dBc@2 tone 0dBm； ≤-45dBc@2 tone 33dBm', field_code = 'B'
WHERE product_id = 86 AND field_name = '互调衰减';

-- 增益调节范围
UPDATE product_specs
SET field_value = '30', field_code = 'N'
WHERE product_id = 86 AND field_name = '增益调节范围';

-- 增益调节线性
UPDATE product_specs
SET field_value = '0–10 ±1', field_code = '4'
WHERE product_id = 86 AND field_name = '增益调节线性';

-- 增益调节步进
UPDATE product_specs
SET field_value = '10/1', field_code = '8'
WHERE product_id = 86 AND field_name = '增益调节步进';

-- 上下行隔离度
UPDATE product_specs
SET field_value = '≥60', field_code = 'W'
WHERE product_id = 86 AND field_name = '上下行隔离度';

-- 带内波动
UPDATE product_specs
SET field_value = '≤3', field_code = 'Y'
WHERE product_id = 86 AND field_name = '带内波动';

-- 显示方式
UPDATE product_specs
SET field_value = '彩色触摸屏', field_code = 'R'
WHERE product_id = 86 AND field_name = '显示方式';

-- 工作温度
UPDATE product_specs
SET field_value = '-20~+55', field_code = 'H'
WHERE product_id = 86 AND field_name = '工作温度';

-- 安装方式
UPDATE product_specs
SET field_value = '机柜式', field_code = 'T'
WHERE product_id = 86 AND field_name = '安装方式';

-- 防护等级
UPDATE product_specs
SET field_value = 'IP40', field_code = 'E'
WHERE product_id = 86 AND field_name = '防护等级';

-- 监控接口类型
UPDATE product_specs
SET field_value = 'USB', field_code = 'N'
WHERE product_id = 86 AND field_name = '监控接口类型';

-- 载波容量
UPDATE product_specs
SET field_value = '12', field_code = 'N'
WHERE product_id = 86 AND field_name = '载波容量';

-- 光口类型
UPDATE product_specs
SET field_value = 'LC', field_code = 'C'
WHERE product_id = 86 AND field_name = '光口类型';

-- 光口数量
UPDATE product_specs
SET field_value = '2', field_code = 'V'
WHERE product_id = 86 AND field_name = '光口数量';

-- ============================================================
-- Step 5: 设置 display_order（标准排序）
-- ============================================================
UPDATE product_specs SET display_order = 1  WHERE product_id = 86 AND field_name = '工作频率';
UPDATE product_specs SET display_order = 2  WHERE product_id = 86 AND field_name = '最大输出功率';
UPDATE product_specs SET display_order = 3  WHERE product_id = 86 AND field_name = '设备净增益';
UPDATE product_specs SET display_order = 4  WHERE product_id = 86 AND field_name = '噪声系数(上行)';
UPDATE product_specs SET display_order = 5  WHERE product_id = 86 AND field_name = '自动电平控制范围（ALC）';
UPDATE product_specs SET display_order = 6  WHERE product_id = 86 AND field_name = '带外杂散';
UPDATE product_specs SET display_order = 7  WHERE product_id = 86 AND field_name = '互调衰减';
UPDATE product_specs SET display_order = 8  WHERE product_id = 86 AND field_name = '允许最大输入';
UPDATE product_specs SET display_order = 9  WHERE product_id = 86 AND field_name = '增益调节范围';
UPDATE product_specs SET display_order = 10 WHERE product_id = 86 AND field_name = '增益调节线性';
UPDATE product_specs SET display_order = 11 WHERE product_id = 86 AND field_name = '增益调节步进';
UPDATE product_specs SET display_order = 12 WHERE product_id = 86 AND field_name = '上下行隔离度';
UPDATE product_specs SET display_order = 13 WHERE product_id = 86 AND field_name = '带内波动';
UPDATE product_specs SET display_order = 14 WHERE product_id = 86 AND field_name = '射频阻抗';
UPDATE product_specs SET display_order = 15 WHERE product_id = 86 AND field_name = '驻波比';
UPDATE product_specs SET display_order = 16 WHERE product_id = 86 AND field_name = '延时';
UPDATE product_specs SET display_order = 17 WHERE product_id = 86 AND field_name = '接口类型';
UPDATE product_specs SET display_order = 18 WHERE product_id = 86 AND field_name = '光模块输出功率';
UPDATE product_specs SET display_order = 19 WHERE product_id = 86 AND field_name = '光模块接收灵敏度';
UPDATE product_specs SET display_order = 20 WHERE product_id = 86 AND field_name = '光模块波长';
UPDATE product_specs SET display_order = 21 WHERE product_id = 86 AND field_name = '光口类型';
UPDATE product_specs SET display_order = 22 WHERE product_id = 86 AND field_name = '光口工作模式';
UPDATE product_specs SET display_order = 23 WHERE product_id = 86 AND field_name = '光口数量';
UPDATE product_specs SET display_order = 24 WHERE product_id = 86 AND field_name = '供电规格';
UPDATE product_specs SET display_order = 25 WHERE product_id = 86 AND field_name = '显示方式';
UPDATE product_specs SET display_order = 26 WHERE product_id = 86 AND field_name = '工作温度';
UPDATE product_specs SET display_order = 27 WHERE product_id = 86 AND field_name = '相对湿度';
UPDATE product_specs SET display_order = 28 WHERE product_id = 86 AND field_name = '外形尺寸';
UPDATE product_specs SET display_order = 29 WHERE product_id = 86 AND field_name = '安装方式';
UPDATE product_specs SET display_order = 30 WHERE product_id = 86 AND field_name = '防护等级';
UPDATE product_specs SET display_order = 31 WHERE product_id = 86 AND field_name = '监控接口类型';
UPDATE product_specs SET display_order = 32 WHERE product_id = 86 AND field_name = '载波容量';
UPDATE product_specs SET display_order = 33 WHERE product_id = 86 AND field_name = '组网结构';
UPDATE product_specs SET display_order = 34 WHERE product_id = 86 AND field_name = '延迟同步';

-- ============================================================
-- Step 6: 验证（33 项，无旧字段名）
-- ============================================================
SELECT 'SPEC_COUNT' AS check_type, COUNT(*) AS val
FROM product_specs WHERE product_id = 86;

SELECT field_name, field_value, field_code, display_order
FROM product_specs
WHERE product_id = 86
ORDER BY display_order;

COMMIT;
