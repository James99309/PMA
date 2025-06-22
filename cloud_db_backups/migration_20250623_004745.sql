-- 添加新增的列
ALTER TABLE products ADD COLUMN IF NOT EXISTS is_vendor_product boolean DEFAULT false;
