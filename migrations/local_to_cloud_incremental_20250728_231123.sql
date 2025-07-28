-- 本地到云端增量迁移脚本
-- 生成时间: 2025-07-28 23:11:23
-- 目标: 将本地 pma_local 的最新结构同步到云端 sp8d

BEGIN;

-- 安全检查：确认当前版本
DO $$
DECLARE
    current_version TEXT;
BEGIN
    SELECT version_num INTO current_version FROM alembic_version LIMIT 1;
    
    IF current_version != 'c8d3eaeaf234' THEN
        RAISE EXCEPTION '版本不匹配：期望 c8d3eaeaf234，实际 %', current_version;
    END IF;
    
    RAISE NOTICE '✅ 版本检查通过：%', current_version;
END
$$;

-- 1. 添加本地新增的索引（从 592b90d54921 迁移）
-- 这些索引在本地存在但云端可能缺失

-- 报价单性能索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quotations_project_id ON quotations(project_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quotations_owner_id ON quotations(owner_id);  
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quotations_created_at ON quotations(created_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quotations_updated_at ON quotations(updated_at);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quotations_amount ON quotations(amount);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_quotations_project_owner ON quotations(project_id, owner_id);

-- 项目性能索引
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_project_type ON projects(project_type);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_current_stage ON projects(current_stage);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_type_stage ON projects(project_type, current_stage);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_owner_id ON projects(owner_id);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_vendor_sales_manager ON projects(vendor_sales_manager_id);

-- 2. 更新迁移版本到本地最新版本
UPDATE alembic_version SET version_num = '592b90d54921';

-- 添加迁移记录
INSERT INTO alembic_version (version_num) VALUES ('592b90d54921') 
ON CONFLICT (version_num) DO NOTHING;

COMMIT;

-- 验证迁移结果
SELECT '✅ 迁移完成，当前版本: ' || version_num FROM alembic_version;
