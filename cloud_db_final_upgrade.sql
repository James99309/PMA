-- PMA云端数据库完整升级脚本
-- 生成时间: 2025-06-05 00:25:00
-- 将云端数据库结构同步到本地版本

BEGIN;

-- ============================================================================
-- 1. 修改 projects 表
-- ============================================================================

-- 修改 projects.rating 列类型从 NUMERIC(2,1) 改为 INTEGER
ALTER TABLE projects ALTER COLUMN rating TYPE INTEGER USING rating::integer;

-- ============================================================================
-- 2. 修改 project_stage_history 表  
-- ============================================================================

-- 删除多余的 user_id 列和相关索引
DROP INDEX IF EXISTS ix_project_stage_history_user_id;
ALTER TABLE project_stage_history DROP COLUMN IF EXISTS user_id;

-- ============================================================================
-- 3. 修改 quotations 表
-- ============================================================================

-- 删除不需要的列
ALTER TABLE quotations DROP COLUMN IF EXISTS approval_required_fields;
ALTER TABLE quotations DROP COLUMN IF EXISTS approval_comments;
ALTER TABLE quotations DROP COLUMN IF EXISTS approved_at;
ALTER TABLE quotations DROP COLUMN IF EXISTS approved_by;

-- 添加新的列
ALTER TABLE quotations ADD COLUMN IF NOT EXISTS confirmed_at TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE quotations ADD COLUMN IF NOT EXISTS confirmation_badge_color VARCHAR(20) DEFAULT NULL;
ALTER TABLE quotations ADD COLUMN IF NOT EXISTS product_signature VARCHAR(64) DEFAULT NULL;
ALTER TABLE quotations ADD COLUMN IF NOT EXISTS confirmed_by INTEGER;
ALTER TABLE quotations ADD COLUMN IF NOT EXISTS confirmation_badge_status VARCHAR(20) DEFAULT 'none';

-- 添加外键约束
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'quotations_confirmed_by_fkey'
        AND table_name = 'quotations'
    ) THEN
        ALTER TABLE quotations ADD CONSTRAINT quotations_confirmed_by_fkey 
        FOREIGN KEY (confirmed_by) REFERENCES users(id);
    END IF;
END $$;

-- ============================================================================
-- 4. 修改 event_registry 表
-- ============================================================================

-- 删除多余的索引
DROP INDEX IF EXISTS ix_event_registry_event_key;

-- ============================================================================
-- 5. 修改 project_rating_records 表
-- ============================================================================

-- 删除多余的列
ALTER TABLE project_rating_records DROP COLUMN IF EXISTS comment;

-- 修改 rating 列类型从 NUMERIC(2,1) 改为 INTEGER
ALTER TABLE project_rating_records ALTER COLUMN rating TYPE INTEGER USING rating::integer;

-- 删除旧的索引和约束
DROP INDEX IF EXISTS idx_project_rating_records_created_at;
DROP INDEX IF EXISTS uq_project_rating_project_user;
DROP INDEX IF EXISTS idx_project_rating_records_project_id;
DROP INDEX IF EXISTS idx_project_rating_records_user_id;

-- 删除旧的约束（如果存在）
ALTER TABLE project_rating_records DROP CONSTRAINT IF EXISTS uq_project_rating_project_user;

-- 创建新的唯一约束和索引
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE indexname = 'uq_project_user_rating'
        AND tablename = 'project_rating_records'
    ) THEN
        CREATE UNIQUE INDEX uq_project_user_rating ON project_rating_records (project_id, user_id);
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'uq_project_user_rating'
        AND table_name = 'project_rating_records'
    ) THEN
        ALTER TABLE project_rating_records ADD CONSTRAINT uq_project_user_rating UNIQUE (project_id, user_id);
    END IF;
END $$;

-- ============================================================================
-- 6. 更新 Alembic 版本
-- ============================================================================

-- 更新 Alembic 迁移版本到最新
UPDATE alembic_version SET version_num = 'c1308c08d0c9';

-- ============================================================================
-- 7. 验证升级结果
-- ============================================================================

-- 检查关键表和列是否存在
DO $$
DECLARE
    missing_items TEXT[] := ARRAY[]::TEXT[];
BEGIN
    -- 检查 quotations 表的新列
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quotations' AND column_name = 'confirmed_at') THEN
        missing_items := array_append(missing_items, 'quotations.confirmed_at');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quotations' AND column_name = 'confirmation_badge_status') THEN
        missing_items := array_append(missing_items, 'quotations.confirmation_badge_status');
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'quotations' AND column_name = 'product_signature') THEN
        missing_items := array_append(missing_items, 'quotations.product_signature');
    END IF;
    
    -- 检查 projects.rating 列类型
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'projects' AND column_name = 'rating' 
        AND data_type != 'integer'
    ) THEN
        missing_items := array_append(missing_items, 'projects.rating type should be integer');
    END IF;
    
    -- 检查 project_rating_records.rating 列类型
    IF EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'project_rating_records' AND column_name = 'rating' 
        AND data_type != 'integer'
    ) THEN
        missing_items := array_append(missing_items, 'project_rating_records.rating type should be integer');
    END IF;
    
    IF array_length(missing_items, 1) > 0 THEN
        RAISE EXCEPTION '升级验证失败，缺失项目: %', array_to_string(missing_items, ', ');
    ELSE
        RAISE NOTICE '✅ 数据库升级验证成功！所有结构已同步到本地版本';
    END IF;
END $$;

COMMIT;

-- 升级完成提示
SELECT 
    '🎉 PMA云端数据库升级完成！' as status,
    current_timestamp as completed_at,
    version_num as current_migration_version
FROM alembic_version; 