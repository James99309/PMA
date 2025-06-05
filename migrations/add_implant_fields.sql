-- 报价单植入字段数据库迁移脚本
-- 为报价单产品明细表和报价单表添加植入相关字段

-- 1. 为报价单产品明细表添加植入小计字段
ALTER TABLE quotation_details 
ADD COLUMN IF NOT EXISTS implant_subtotal DECIMAL(12,2) DEFAULT 0.00;

-- 2. 为报价单表添加植入总额合计字段
ALTER TABLE quotations 
ADD COLUMN IF NOT EXISTS implant_total_amount DECIMAL(12,2) DEFAULT 0.00;

-- 3. 添加字段注释
COMMENT ON COLUMN quotation_details.implant_subtotal IS '植入小计：当产品品牌是和源通信时，零售价格 * 产品数量的值';
COMMENT ON COLUMN quotations.implant_total_amount IS '植入总额合计：该报价单产品明细下所有植入小计值的合计';

-- 4. 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_quotation_details_implant_subtotal ON quotation_details(implant_subtotal);
CREATE INDEX IF NOT EXISTS idx_quotations_implant_total_amount ON quotations(implant_total_amount);

-- 5. 更新现有数据，计算植入小计
-- 当产品品牌是"和源通信"时，计算植入小计
UPDATE quotation_details 
SET implant_subtotal = CASE 
    WHEN brand = '和源通信' THEN COALESCE(market_price, 0) * COALESCE(quantity, 0)
    ELSE 0.00
END
WHERE implant_subtotal IS NULL OR implant_subtotal = 0;

-- 6. 更新现有数据，计算植入总额合计
-- 为每个报价单计算植入总额合计
UPDATE quotations 
SET implant_total_amount = (
    SELECT COALESCE(SUM(implant_subtotal), 0.00)
    FROM quotation_details 
    WHERE quotation_details.quotation_id = quotations.id
)
WHERE implant_total_amount IS NULL OR implant_total_amount = 0;

-- 7. 验证数据更新
-- 显示更新后的统计信息
SELECT 
    '报价单产品明细' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN implant_subtotal > 0 THEN 1 END) as records_with_implant,
    SUM(implant_subtotal) as total_implant_subtotal
FROM quotation_details
UNION ALL
SELECT 
    '报价单' as table_name,
    COUNT(*) as total_records,
    COUNT(CASE WHEN implant_total_amount > 0 THEN 1 END) as records_with_implant,
    SUM(implant_total_amount) as total_implant_amount
FROM quotations; 