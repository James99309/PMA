-- 为 project_customer_associations 表添加 created_by 字段
-- 执行日期: 2025-01-15

-- 检查表是否存在
DO $$
BEGIN
    -- 检查 created_by 列是否已存在
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'project_customer_associations' 
        AND column_name = 'created_by'
    ) THEN
        -- 添加 created_by 字段
        ALTER TABLE project_customer_associations 
        ADD COLUMN created_by INTEGER REFERENCES users(id);
        
        RAISE NOTICE 'Successfully added created_by column to project_customer_associations table';
    ELSE
        RAISE NOTICE 'Column created_by already exists in project_customer_associations table';
    END IF;
END $$;

-- 为现有记录添加注释（可选）
COMMENT ON COLUMN project_customer_associations.created_by IS '创建此客户关联的用户ID';

-- 验证字段是否添加成功
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'project_customer_associations' 
AND column_name = 'created_by';