-- 修复liuq用户绩效管理权限的SQL脚本
-- 请在数据库管理界面中执行此脚本

-- 1. 首先检查liuq用户的基本信息
SELECT 
    id,
    username, 
    role, 
    real_name,
    company_name
FROM "user" 
WHERE username = 'liuq';

-- 2. 检查liuq用户当前的权限情况
SELECT 
    u.username,
    u.role,
    p.module,
    p.can_view,
    p.can_create,
    p.can_edit,
    p.can_delete
FROM "user" u
LEFT JOIN permission p ON u.id = p.user_id
WHERE u.username = 'liuq'
ORDER BY p.module;

-- 3. 检查是否已经存在performance_management权限
SELECT 
    COUNT(*) as existing_count
FROM permission p
JOIN "user" u ON p.user_id = u.id
WHERE u.username = 'liuq' 
AND p.module = 'performance_management';

-- 4. 为liuq用户添加performance_management权限（如果不存在）
-- 根据human_resources角色，应该有查看、创建、编辑权限
INSERT INTO permission (user_id, module, can_view, can_create, can_edit, can_delete)
SELECT 
    u.id,
    'performance_management',
    true,  -- can_view
    true,  -- can_create  
    true,  -- can_edit
    false  -- can_delete
FROM "user" u
WHERE u.username = 'liuq'
AND u.id NOT IN (
    SELECT user_id 
    FROM permission 
    WHERE module = 'performance_management'
);

-- 5. 验证权限是否添加成功
SELECT 
    u.username,
    u.role,
    p.module,
    p.can_view,
    p.can_create,
    p.can_edit,
    p.can_delete
FROM "user" u
JOIN permission p ON u.id = p.user_id
WHERE u.username = 'liuq' 
AND p.module = 'performance_management';

-- 6. 检查系统中所有用户的performance_management权限统计
SELECT 
    u.role,
    COUNT(*) as total_users,
    COUNT(p.id) as users_with_permission,
    COUNT(CASE WHEN p.can_view = true THEN 1 END) as can_view_count
FROM "user" u
LEFT JOIN permission p ON u.id = p.user_id AND p.module = 'performance_management'
GROUP BY u.role
ORDER BY u.role;

-- 如果发现其他用户也缺少performance_management权限，可以批量添加：

-- 为所有管理员添加完整权限
-- INSERT INTO permission (user_id, module, can_view, can_create, can_edit, can_delete)
-- SELECT id, 'performance_management', true, true, true, true
-- FROM "user" 
-- WHERE role = 'admin'
-- AND id NOT IN (SELECT user_id FROM permission WHERE module = 'performance_management');

-- 为人事相关角色添加管理权限
-- INSERT INTO permission (user_id, module, can_view, can_create, can_edit, can_delete)
-- SELECT id, 'performance_management', true, true, true, false
-- FROM "user" 
-- WHERE role IN ('human_resources', 'hr', 'ceo', 'sales_director', 'service_manager')
-- AND id NOT IN (SELECT user_id FROM permission WHERE module = 'performance_management');

-- 为其他角色添加查看权限
-- INSERT INTO permission (user_id, module, can_view, can_create, can_edit, can_delete)
-- SELECT id, 'performance_management', true, false, false, false
-- FROM "user" 
-- WHERE role IN ('business_admin', 'solution', 'service', 'sales')
-- AND id NOT IN (SELECT user_id FROM permission WHERE module = 'performance_management');