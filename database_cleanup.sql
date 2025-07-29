-- ============================================================
-- 数据库数据清理SQL脚本
-- 功能：
-- 1. 清空未报备项目的报备日期
-- 2. 锁定签约项目
-- ============================================================

-- 开始事务
BEGIN;

-- ============================================================
-- 任务1: 查看需要清空报备日期的项目（预览）
-- ============================================================
SELECT 
    '需要清空报备日期的项目预览' as action,
    COUNT(*) as count
FROM projects 
WHERE report_time IS NOT NULL 
  AND (authorization_code IS NULL OR TRIM(authorization_code) = '');

-- 显示前10个将要清空报备日期的项目
SELECT 
    '前10个将清空报备日期的项目' as info,
    id,
    project_name,
    COALESCE(authorization_code, '无') as authorization_code,
    COALESCE(authorization_status, '无') as authorization_status,
    report_time
FROM projects 
WHERE report_time IS NOT NULL 
  AND (authorization_code IS NULL OR TRIM(authorization_code) = '')
ORDER BY updated_at DESC
LIMIT 10;

-- ============================================================
-- 任务2: 查看需要锁定的签约项目（预览）
-- ============================================================
SELECT 
    '需要锁定的签约项目预览' as action,
    COUNT(*) as count
FROM projects 
WHERE current_stage = 'signed' 
  AND is_locked = false;

-- 显示前10个将要锁定的签约项目
SELECT 
    '前10个将锁定的签约项目' as info,
    id,
    project_name,
    COALESCE(authorization_code, '无授权编号') as authorization_code,
    current_stage,
    is_locked
FROM projects 
WHERE current_stage = 'signed' 
  AND is_locked = false
ORDER BY updated_at DESC
LIMIT 10;

-- ============================================================
-- 执行更新操作（取消注释以执行）
-- ============================================================

-- 任务1: 清空未报备项目的报备日期
-- UPDATE projects 
-- SET report_time = NULL
-- WHERE report_time IS NOT NULL 
--   AND (authorization_code IS NULL OR TRIM(authorization_code) = '');

-- 任务2: 锁定签约项目
-- 首先获取管理员用户ID（假设第一个admin用户）
-- WITH admin_user AS (
--     SELECT id FROM users WHERE role = 'admin' LIMIT 1
-- )
-- UPDATE projects 
-- SET 
--     is_locked = true,
--     locked_reason = '项目已签约，自动锁定',
--     locked_by = (SELECT id FROM admin_user),
--     locked_at = NOW()
-- WHERE current_stage = 'signed' 
--   AND is_locked = false;

-- 回滚事务（取消注释COMMIT来提交更改）
ROLLBACK;
-- COMMIT;

-- ============================================================
-- 验证脚本（执行更新后运行以验证结果）
-- ============================================================

-- 验证1: 检查清空报备日期的结果
-- SELECT 
--     '清空报备日期结果验证' as verification,
--     COUNT(*) as remaining_projects_with_report_time
-- FROM projects 
-- WHERE report_time IS NOT NULL 
--   AND (authorization_code IS NULL OR TRIM(authorization_code) = '');

-- 验证2: 检查锁定签约项目的结果
-- SELECT 
--     '锁定签约项目结果验证' as verification,
--     COUNT(*) as unlocked_signed_projects
-- FROM projects 
-- WHERE current_stage = 'signed' 
--   AND is_locked = false;

-- 最终统计
-- SELECT 
--     '最终统计' as summary,
--     (SELECT COUNT(*) FROM projects WHERE report_time IS NOT NULL) as total_projects_with_report_time,
--     (SELECT COUNT(*) FROM projects WHERE current_stage = 'signed' AND is_locked = true) as total_locked_signed_projects;