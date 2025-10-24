-- ============================================================================
-- 修复云端SP8D数据库 settlement_orders.distributor_id 的NOT NULL约束
-- ============================================================================
--
-- 问题：
--   settlement_orders.distributor_id 字段有 NOT NULL 约束
--   导致常规渠道但没有分销商的批价单无法创建结算单
--
-- 解决方案：
--   将 distributor_id 字段修改为可空 (nullable)
--
-- 执行方式：
--   方式1: 在 Supabase Dashboard -> SQL Editor 中执行
--   方式2: 使用 psql 连接后执行
--
-- 数据库信息：
--   主机: aws-0-ap-southeast-1.pooler.supabase.com:6543
--   数据库: postgres
--   项目: SP8D
-- ============================================================================

-- 开始事务
BEGIN;

-- 1. 修改 distributor_id 约束为可空
ALTER TABLE settlement_orders
ALTER COLUMN distributor_id DROP NOT NULL;

-- 2. 验证修改结果
SELECT
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'settlement_orders'
AND column_name = 'distributor_id';

-- 预期结果应该显示: is_nullable = 'YES'

-- 3. 提交事务（如果上述验证通过）
COMMIT;

-- ============================================================================
-- 如果出现任何问题，可以回滚（在COMMIT之前执行）:
-- ROLLBACK;
-- ============================================================================
