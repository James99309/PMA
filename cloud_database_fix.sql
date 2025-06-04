-- PMA系统云端数据库修复脚本 - v1.2.2
-- 创建日期: 2025年6月4日
-- 作者: 倪捷
-- 用途: 修复云端数据库中的数据完整性问题

-- ===============================================
-- 修复approval_record表中的step_id NULL值问题
-- ===============================================

-- 1. 检查当前有多少条NULL记录
SELECT 
    COUNT(*) as null_records_count,
    'approval_record表中step_id为NULL的记录数' as description
FROM approval_record 
WHERE step_id IS NULL;

-- 2. 查看可用的step_id
SELECT 
    id as available_step_ids,
    'approval_step表中可用的step_id' as description
FROM approval_step 
ORDER BY id 
LIMIT 10;

-- 3. 修复NULL值 - 使用最小的可用step_id
UPDATE approval_record 
SET step_id = (
    SELECT MIN(id) 
    FROM approval_step 
    LIMIT 1
) 
WHERE step_id IS NULL;

-- 4. 验证修复结果
SELECT 
    COUNT(*) as remaining_null_records,
    '修复后仍为NULL的记录数（应该为0）' as description
FROM approval_record 
WHERE step_id IS NULL;

-- ===============================================
-- 完成标记
-- ===============================================

SELECT 
    'PMA系统云端数据库修复完成' as status,
    NOW() as completion_time,
    'v1.2.2' as version; 