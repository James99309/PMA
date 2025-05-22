-- 添加项目活跃原因字段
ALTER TABLE projects ADD COLUMN IF NOT EXISTS activity_reason VARCHAR(50) NULL; 