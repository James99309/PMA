-- 为报销单模块添加货币支持（PostgreSQL兼容版本）
-- 执行时间：2025-08-03

-- 1. 为报销单主表添加货币字段
ALTER TABLE expense 
ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'CNY';

-- 2. 为报销明细表添加货币和换算字段
-- 添加明细货币字段（发票实际货币）
ALTER TABLE expense_detail 
ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'CNY';

-- 添加发票金额字段（原始货币）
ALTER TABLE expense_detail 
ADD COLUMN IF NOT EXISTS invoice_amount DECIMAL(15,2) DEFAULT 0.00;

-- 添加当前金额字段（换算为报销单货币的金额）
ALTER TABLE expense_detail 
ADD COLUMN IF NOT EXISTS current_amount DECIMAL(15,2) DEFAULT 0.00;

-- 添加汇率字段（用于记录转换时的汇率）
ALTER TABLE expense_detail 
ADD COLUMN IF NOT EXISTS exchange_rate DECIMAL(10,4) DEFAULT 1.0000;

-- 3. 数据迁移：将原有的amount数据迁移到新字段
-- 将现有的amount值复制到invoice_amount和current_amount
UPDATE expense_detail 
SET invoice_amount = amount, 
    current_amount = amount 
WHERE invoice_amount = 0.00 AND current_amount = 0.00;

-- 4. 为新字段创建索引
-- 报销单货币索引
CREATE INDEX IF NOT EXISTS idx_expense_currency 
ON expense(currency);

-- 明细货币索引  
CREATE INDEX IF NOT EXISTS idx_expense_detail_currency 
ON expense_detail(currency);

-- 明细的报销单ID和货币复合索引（用于汇总计算）
CREATE INDEX IF NOT EXISTS idx_expense_detail_expense_currency 
ON expense_detail(expense_id, currency);

-- 5. 添加字段注释（PostgreSQL语法）
COMMENT ON COLUMN expense.currency IS '报销单主货币，用于最终结算和统计';
COMMENT ON COLUMN expense_detail.currency IS '发票实际货币类型';
COMMENT ON COLUMN expense_detail.invoice_amount IS '发票原始金额（发票货币）';
COMMENT ON COLUMN expense_detail.current_amount IS '换算金额（报销单货币）';
COMMENT ON COLUMN expense_detail.exchange_rate IS '换算汇率（发票货币→报销单货币）';