-- 中等风险数据库迁移
-- 生成时间: 2025-06-02 21:12:01.253542

BEGIN;

-- 添加列: quotations.is_locked
ALTER TABLE quotations ADD COLUMN IF NOT EXISTS is_locked BOOLEAN NULL DEFAULT false;

-- 添加列: quotations.lock_reason
ALTER TABLE quotations ADD COLUMN IF NOT EXISTS lock_reason VARCHAR(200) NULL ;

-- 添加列: quotations.locked_by
ALTER TABLE quotations ADD COLUMN IF NOT EXISTS locked_by INTEGER NULL ;

-- 添加列: quotations.locked_at
ALTER TABLE quotations ADD COLUMN IF NOT EXISTS locked_at TIMESTAMP NULL ;

COMMIT;
