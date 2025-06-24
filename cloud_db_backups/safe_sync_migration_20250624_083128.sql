-- 数据库结构安全同步脚本
-- 生成时间: 2025-06-24 08:31:28.988941
-- 注意: 此脚本仅添加缺失的结构，不会删除现有数据
-- 警告: 不会删除云端多余的约束，以保护数据完整性

BEGIN;

-- 添加缺失的列
ALTER TABLE approval_step ADD COLUMN IF NOT EXISTS approver_type character varying(50);
ALTER TABLE approval_step ADD COLUMN IF NOT EXISTS description text;
ALTER TABLE dev_products ADD COLUMN IF NOT EXISTS currency character varying(3) DEFAULT 'USD';
ALTER TABLE pricing_order_details ADD COLUMN IF NOT EXISTS currency character varying(3) DEFAULT 'USD';
ALTER TABLE pricing_orders ADD COLUMN IF NOT EXISTS currency character varying(3) DEFAULT 'USD';
ALTER TABLE products ADD COLUMN IF NOT EXISTS currency character varying(3) DEFAULT 'USD';
ALTER TABLE products ADD COLUMN IF NOT EXISTS is_vendor_product boolean DEFAULT false;
ALTER TABLE quotation_details ADD COLUMN IF NOT EXISTS converted_market_price numeric(10,2);
ALTER TABLE quotation_details ADD COLUMN IF NOT EXISTS currency character varying(3) DEFAULT 'USD';
ALTER TABLE quotation_details ADD COLUMN IF NOT EXISTS original_market_price numeric(10,2);
ALTER TABLE quotations ADD COLUMN IF NOT EXISTS currency character varying(3) DEFAULT 'USD';
ALTER TABLE quotations ADD COLUMN IF NOT EXISTS exchange_rate numeric(10,4) DEFAULT 1.0;
ALTER TABLE quotations ADD COLUMN IF NOT EXISTS original_currency character varying(3);
ALTER TABLE settlement_order_details ADD COLUMN IF NOT EXISTS currency character varying(3) DEFAULT 'USD';

-- 修改列定义以匹配本地结构
ALTER TABLE approval_step ALTER COLUMN approver_user_id DROP NOT NULL;

-- 注意事项:
-- 1. 未删除云端多余的列，以避免数据丢失
-- 2. 未删除云端多余的约束，以保护数据完整性
-- 3. 未添加缺失的约束，因为可能与现有数据冲突
-- 4. 如需完全同步约束，请手动检查数据一致性后操作

COMMIT;

-- 同步完成