-- 修复现有数据的汇率字段
-- 基于实际的 invoice_amount 和 current_amount 重新计算汇率
-- 执行时间：2025-08-03

-- 1. 修复汇率字段：当发票金额和当前金额不同时，重新计算汇率
UPDATE expense_details 
SET exchange_rate = CASE 
    WHEN invoice_amount > 0 AND current_amount != invoice_amount THEN 
        ROUND(current_amount / invoice_amount, 4)
    ELSE 
        1.0000
END
WHERE invoice_amount > 0;

-- 2. 验证修复结果
SELECT 
    ed.id,
    e.expense_number,
    ed.currency as detail_currency,
    e.currency as expense_currency,
    ed.invoice_amount,
    ed.current_amount,
    ed.exchange_rate as stored_rate,
    CASE 
        WHEN ed.invoice_amount > 0 THEN 
            ROUND(ed.current_amount / ed.invoice_amount, 4)
        ELSE 1.0000
    END as calculated_rate,
    CASE 
        WHEN ed.invoice_amount > 0 AND 
             ABS(ed.exchange_rate - (ed.current_amount / ed.invoice_amount)) > 0.0001 THEN 
            '汇率不一致'
        ELSE '汇率正确'
    END as rate_status
FROM expense_details ed
JOIN expenses e ON ed.expense_id = e.id
WHERE ed.invoice_amount > 0
ORDER BY e.expense_number, ed.id;

-- 3. 显示修复统计
SELECT 
    COUNT(*) as total_details,
    COUNT(CASE WHEN exchange_rate = 1.0000 THEN 1 END) as same_currency_count,
    COUNT(CASE WHEN exchange_rate != 1.0000 THEN 1 END) as converted_currency_count,
    MIN(exchange_rate) as min_rate,
    MAX(exchange_rate) as max_rate
FROM expense_details
WHERE invoice_amount > 0;