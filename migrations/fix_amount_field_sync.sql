-- 修复amount字段数据同步问题
-- 执行时间：2025-08-03

-- 确保原有的amount字段与新的current_amount字段保持同步
-- 这样既能满足向后兼容，又能支持新的货币功能

-- 1. 首先检查amount字段是否存在NOT NULL约束
-- 如果current_amount有值而amount为NULL，则同步数据
UPDATE expense_details 
SET amount = current_amount 
WHERE amount IS NULL 
  AND current_amount IS NOT NULL 
  AND current_amount > 0;

-- 2. 如果amount有值而current_amount为空，则反向同步
UPDATE expense_details 
SET current_amount = amount,
    invoice_amount = amount
WHERE current_amount = 0.00 
  AND amount IS NOT NULL 
  AND amount > 0;

-- 3. 确保两个字段都不为NULL的情况下保持一致
-- 优先使用current_amount的值（新的货币转换系统）
UPDATE expense_details 
SET amount = current_amount 
WHERE current_amount IS NOT NULL 
  AND current_amount > 0 
  AND (amount IS NULL OR amount != current_amount);

-- 4. 验证数据一致性：确保没有NULL值
-- 如果仍有NULL值，设置为0.01（最小金额）
UPDATE expense_details 
SET amount = 0.01,
    current_amount = 0.01,
    invoice_amount = 0.01
WHERE amount IS NULL 
   OR current_amount IS NULL 
   OR invoice_amount IS NULL;