-- 检查字段是否存在，如果不存在则添加
DO $$
BEGIN
    -- 检查字段是否已存在
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'approval_process_template' 
        AND column_name = 'required_fields'
    ) THEN
        -- 如果不存在，添加字段
        EXECUTE 'ALTER TABLE approval_process_template ADD COLUMN IF NOT EXISTS required_fields JSONB DEFAULT ''[]''';
        RAISE NOTICE 'required_fields字段已添加到approval_process_template表';
    ELSE
        RAISE NOTICE 'required_fields字段已存在于approval_process_template表中，无需添加';
    END IF;
END $$; 