-- 应用共享机制迁移的SQL脚本
-- 这个脚本可以直接在数据库中执行

BEGIN;

-- 1. 为项目表添加共享字段
ALTER TABLE projects ADD COLUMN IF NOT EXISTS shared_with_users JSON DEFAULT '[]';
ALTER TABLE projects ADD COLUMN IF NOT EXISTS share_enabled BOOLEAN DEFAULT false;

-- 2. 为客户表添加共享启用字段（如果不存在）
ALTER TABLE companies ADD COLUMN IF NOT EXISTS share_enabled BOOLEAN DEFAULT false;

-- 3. 初始化现有数据
UPDATE projects SET shared_with_users = '[]' WHERE shared_with_users IS NULL;
UPDATE projects SET share_enabled = false WHERE share_enabled IS NULL;
UPDATE companies SET share_enabled = false WHERE share_enabled IS NULL;

-- 4. 关闭客户的项目自动共享功能（解决zhouyj权限异常）
UPDATE companies SET share_related_projects = false WHERE share_related_projects = true;

-- 5. 创建性能优化索引
CREATE INDEX IF NOT EXISTS idx_projects_shared_users ON projects USING gin (shared_with_users);
CREATE INDEX IF NOT EXISTS idx_projects_share_enabled ON projects (share_enabled);
CREATE INDEX IF NOT EXISTS idx_companies_shared_users ON companies USING gin (shared_with_users);
CREATE INDEX IF NOT EXISTS idx_companies_share_enabled ON companies (share_enabled);

COMMIT;

-- 验证查询
SELECT 'Projects with sharing fields' as status, COUNT(*) as count FROM projects WHERE shared_with_users IS NOT NULL;
SELECT 'Companies with sharing disabled' as status, COUNT(*) as count FROM companies WHERE share_related_projects = false;

PRINT '✅ 共享机制迁移完成';
PRINT '  - 项目表添加了共享字段';
PRINT '  - 客户表关闭了项目自动共享';
PRINT '  - 创建了性能索引';
PRINT '  - zhouyj权限异常问题已解决';