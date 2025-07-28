-- 添加绩效目标合格值字段
-- 执行前请确保已备份数据库

-- 检查 performance_targets 表是否存在
-- 如果表不存在，请先创建基础表

-- 添加植入合格值字段
ALTER TABLE performance_targets 
ADD COLUMN IF NOT EXISTS implant_rate INTEGER DEFAULT 0;

-- 添加销售合格值字段  
ALTER TABLE performance_targets 
ADD COLUMN IF NOT EXISTS sales_rate INTEGER DEFAULT 0;

-- 添加客户合格值字段
ALTER TABLE performance_targets 
ADD COLUMN IF NOT EXISTS customers_rate INTEGER DEFAULT 0;

-- 添加项目合格值字段
ALTER TABLE performance_targets 
ADD COLUMN IF NOT EXISTS projects_rate INTEGER DEFAULT 0;

-- 添加注释
COMMENT ON COLUMN performance_targets.implant_rate IS '植入合格值';
COMMENT ON COLUMN performance_targets.sales_rate IS '销售合格值';
COMMENT ON COLUMN performance_targets.customers_rate IS '客户合格值'; 
COMMENT ON COLUMN performance_targets.projects_rate IS '项目合格值';

-- 验证字段添加成功
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'performance_targets' 
AND column_name IN ('implant_rate', 'sales_rate', 'customers_rate', 'projects_rate')
ORDER BY column_name;