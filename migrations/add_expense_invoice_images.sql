-- 添加发票图片字段到expense_details表
-- 创建时间: 2025-08-03 14:00:00
-- 用途: 为报销明细添加发票图片存储功能

-- 添加invoice_images字段
ALTER TABLE expense_details 
ADD COLUMN invoice_images TEXT DEFAULT NULL;

-- 添加注释
COMMENT ON COLUMN expense_details.invoice_images IS '发票图片JSON数组，格式：[{"filename": "xxx.jpg", "url": "http://...", "size": 123456, "uploaded_at": "2025-08-03T14:00:00"}]';

-- 验证字段已添加
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'expense_details' 
AND column_name = 'invoice_images';