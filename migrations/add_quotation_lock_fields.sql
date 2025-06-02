-- 报价单锁定功能数据库迁移脚本
-- 为报价单表添加锁定相关字段

-- 1. 为报价单表添加锁定相关字段
ALTER TABLE quotations 
ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT FALSE;

ALTER TABLE quotations 
ADD COLUMN IF NOT EXISTS lock_reason VARCHAR(200);

ALTER TABLE quotations 
ADD COLUMN IF NOT EXISTS locked_by INTEGER REFERENCES users(id);

ALTER TABLE quotations 
ADD COLUMN IF NOT EXISTS locked_at TIMESTAMP;

-- 2. 添加字段注释
COMMENT ON COLUMN quotations.is_locked IS '是否被锁定';
COMMENT ON COLUMN quotations.lock_reason IS '锁定原因';
COMMENT ON COLUMN quotations.locked_by IS '锁定人ID';
COMMENT ON COLUMN quotations.locked_at IS '锁定时间';

-- 3. 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_quotations_is_locked ON quotations(is_locked);
CREATE INDEX IF NOT EXISTS idx_quotations_locked_by ON quotations(locked_by);

-- 4. 更新现有数据，确保所有报价单默认为未锁定状态
UPDATE quotations SET is_locked = FALSE WHERE is_locked IS NULL; 