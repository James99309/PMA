-- 报销单锁定功能数据库迁移脚本
-- 为报销单表添加锁定状态字段

-- 1. 为报销单表添加锁定状态字段
ALTER TABLE expenses 
ADD COLUMN IF NOT EXISTS is_locked BOOLEAN DEFAULT FALSE NOT NULL;

-- 2. 添加字段注释
COMMENT ON COLUMN expenses.is_locked IS '锁定状态，草稿状态下默认未锁定';

-- 3. 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_expenses_is_locked ON expenses(is_locked);

-- 4. 更新现有数据，确保所有报销单默认为未锁定状态
UPDATE expenses SET is_locked = FALSE WHERE is_locked IS NULL;