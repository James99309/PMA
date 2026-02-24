-- SE/SA 绩效目标插入脚本 (2026年)
-- 单位：万元（与 user_performance_targets 表一致）
-- 植入额年度目标：14720万，批价额年度目标：2344万

-- Step 1: 查找 SE 用户
SELECT id, username, real_name, role FROM users WHERE role = 'solution_engineer';
-- 如果没有 solution_engineer，也查看 solution_manager
SELECT id, username, real_name, role FROM users WHERE role IN ('solution_engineer', 'solution_manager');

-- Step 2: 检查是否已有2026年SE目标（避免重复插入）
SELECT * FROM user_performance_targets
WHERE year = 2026 AND item_code IN ('se_implant_amount', 'se_sales_amount');

-- Step 3: 插入 SE 植入额目标（请替换 <SE_USER_ID> 为实际用户ID）
-- 年度：14720万，按季度均分：3680万/季度，按月均分：~1226.67万/月
INSERT INTO user_performance_targets (
    user_id, year, item_code, annual_target_override,
    enable_quarterly_override, q1_target_override, q2_target_override, q3_target_override, q4_target_override,
    enable_monthly_override, monthly_targets_override, created_at
) VALUES (
    <SE_USER_ID>, 2026, 'se_implant_amount', 14720,
    true, 3680, 3680, 3680, 3680,
    false, NULL, NOW()
);

-- Step 4: 插入 SE 批价额目标
-- 年度：2344万，按季度均分：586万/季度
INSERT INTO user_performance_targets (
    user_id, year, item_code, annual_target_override,
    enable_quarterly_override, q1_target_override, q2_target_override, q3_target_override, q4_target_override,
    enable_monthly_override, monthly_targets_override, created_at
) VALUES (
    <SE_USER_ID>, 2026, 'se_sales_amount', 2344,
    true, 586, 586, 586, 586,
    false, NULL, NOW()
);

-- Step 5: 验证插入结果
SELECT user_id, year, item_code, annual_target_override,
       q1_target_override, q2_target_override, q3_target_override, q4_target_override
FROM user_performance_targets
WHERE year = 2026 AND item_code IN ('se_implant_amount', 'se_sales_amount');
