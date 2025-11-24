-- SP8D云端数据库字段迁移SQL
-- 生成时间: 2025-11-24 22:22:54
-- 共4个字段需要添加

-- 1. approval_record 表 - 添加审批记录状态字段
ALTER TABLE approval_record
ADD COLUMN status VARCHAR(20) DEFAULT 'approved';

-- 2. dev_product_specs 表 - 添加是否纳入产品描述字段
ALTER TABLE dev_product_specs
ADD COLUMN include_in_description BOOLEAN DEFAULT TRUE;

-- 3. dev_products 表 - 添加研发用途说明字段
ALTER TABLE dev_products
ADD COLUMN development_purpose TEXT;

-- 4. product_specs 表 - 添加是否纳入产品描述字段
ALTER TABLE product_specs
ADD COLUMN include_in_description BOOLEAN DEFAULT TRUE;

-- 迁移完成
