-- 修复Render环境数据库中companies表缺少region列的问题
-- 创建于 2025-05-03

BEGIN;

-- 检查并添加region列
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'companies' AND column_name = 'region'
    ) THEN
        ALTER TABLE companies ADD COLUMN region VARCHAR(50);
        RAISE NOTICE 'region列已添加到companies表';
    ELSE
        RAISE NOTICE 'region列已存在，无需添加';
    END IF;
END $$;

-- 将province列数据复制到region列
UPDATE companies 
SET region = province 
WHERE province IS NOT NULL AND region IS NULL;

-- 更新alembic_version表的版本号
UPDATE alembic_version 
SET version_num = 'add_missing_region_column' 
WHERE version_num <> 'add_missing_region_column';

COMMIT;

-- 验证更新结果
SELECT COUNT(*) AS total_rows FROM companies;
SELECT COUNT(*) AS rows_with_region FROM companies WHERE region IS NOT NULL;
SELECT COUNT(*) AS rows_with_null_region FROM companies WHERE region IS NULL; 
-- 创建于 2025-05-03

BEGIN;

-- 检查并添加region列
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'companies' AND column_name = 'region'
    ) THEN
        ALTER TABLE companies ADD COLUMN region VARCHAR(50);
        RAISE NOTICE 'region列已添加到companies表';
    ELSE
        RAISE NOTICE 'region列已存在，无需添加';
    END IF;
END $$;

-- 将province列数据复制到region列
UPDATE companies 
SET region = province 
WHERE province IS NOT NULL AND region IS NULL;

-- 更新alembic_version表的版本号
UPDATE alembic_version 
SET version_num = 'add_missing_region_column' 
WHERE version_num <> 'add_missing_region_column';

COMMIT;

-- 验证更新结果
SELECT COUNT(*) AS total_rows FROM companies;
SELECT COUNT(*) AS rows_with_region FROM companies WHERE region IS NOT NULL;
SELECT COUNT(*) AS rows_with_null_region FROM companies WHERE region IS NULL; 