-- 为结算单表添加结算状态字段
-- 执行时间: 2025-07-19

-- 添加settlement_status字段
ALTER TABLE settlement_orders 
ADD COLUMN settlement_status VARCHAR(20) DEFAULT 'pending';

-- 添加注释
COMMENT ON COLUMN settlement_orders.settlement_status IS '结算状态: pending, partially_settled, fully_settled';

-- 更新现有记录的settlement_status字段为pending（默认值）
UPDATE settlement_orders SET settlement_status = 'pending' WHERE settlement_status IS NULL;

-- 验证添加成功
SELECT 
    column_name, 
    data_type, 
    column_default,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'settlement_orders' 
AND column_name = 'settlement_status';