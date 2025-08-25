-- 清理批价单V1审批系统相关数据库表和字段
-- 警告：执行前请备份数据库！

-- 第一步：删除V1审批记录表（如果存在）
DROP TABLE IF EXISTS pricing_order_approval_records CASCADE;

-- 第二步：清理批价单表中的V1审批相关字段
-- 注意：在生产环境中，建议先备份数据，然后逐步删除字段

-- 检查并删除V1审批流程相关字段
-- ALTER TABLE pricing_orders DROP COLUMN IF EXISTS current_approval_step;
-- ALTER TABLE pricing_orders DROP COLUMN IF EXISTS approval_flow_type;

-- 第三步：验证清理结果
-- 检查是否还有相关表存在
SELECT schemaname, tablename 
FROM pg_tables 
WHERE tablename LIKE '%approval_record%' 
  AND schemaname = 'public';

-- 检查批价单表结构
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'pricing_orders' 
  AND table_schema = 'public'
  AND column_name IN ('current_approval_step', 'approval_flow_type')
ORDER BY ordinal_position;