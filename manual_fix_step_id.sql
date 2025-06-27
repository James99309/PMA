-- 手动修复 ApprovalRecord 表的 step_id 字段约束
-- 允许 step_id 为 NULL 以支持模板快照

-- PostgreSQL 语法
ALTER TABLE approval_record ALTER COLUMN step_id DROP NOT NULL;

-- 验证修改结果
SELECT column_name, is_nullable, data_type 
FROM information_schema.columns 
WHERE table_name = 'approval_record' 
AND column_name = 'step_id'; 