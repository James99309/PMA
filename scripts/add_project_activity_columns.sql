-- 添加项目活跃度相关字段
ALTER TABLE projects ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE projects ADD COLUMN IF NOT EXISTS last_activity_date TIMESTAMP DEFAULT NOW(); 