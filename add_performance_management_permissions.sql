-- 为所有用户添加performance_management权限模块
-- 这个脚本会为每个用户添加绩效管理权限，根据角色分配不同的权限级别

-- 首先，为管理员添加完整的绩效管理权限
INSERT INTO permission (user_id, module, can_view, can_create, can_edit, can_delete)
SELECT 
    id as user_id,
    'performance_management' as module,
    true as can_view,
    true as can_create, 
    true as can_edit,
    true as can_delete
FROM "user" 
WHERE role = 'admin'
AND id NOT IN (
    SELECT user_id FROM permission WHERE module = 'performance_management'
);

-- 为人事、CEO、销售总监、服务经理添加绩效管理权限（查看、创建、编辑）
INSERT INTO permission (user_id, module, can_view, can_create, can_edit, can_delete)
SELECT 
    id as user_id,
    'performance_management' as module,
    true as can_view,
    true as can_create,
    true as can_edit,
    false as can_delete
FROM "user" 
WHERE role IN ('human_resources', 'hr', 'ceo', 'sales_director', 'service_manager')
AND id NOT IN (
    SELECT user_id FROM permission WHERE module = 'performance_management'
);

-- 为商务助理、解决方案、服务、销售添加绩效管理查看权限
INSERT INTO permission (user_id, module, can_view, can_create, can_edit, can_delete)
SELECT 
    id as user_id,
    'performance_management' as module,
    true as can_view,
    false as can_create,
    false as can_edit,
    false as can_delete
FROM "user" 
WHERE role IN ('business_admin', 'solution', 'service', 'sales')
AND id NOT IN (
    SELECT user_id FROM permission WHERE module = 'performance_management'
);

-- 为其他角色添加无权限记录（确保一致性）
INSERT INTO permission (user_id, module, can_view, can_create, can_edit, can_delete)
SELECT 
    id as user_id,
    'performance_management' as module,
    false as can_view,
    false as can_create,
    false as can_edit,
    false as can_delete
FROM "user" 
WHERE role NOT IN ('admin', 'human_resources', 'hr', 'ceo', 'sales_director', 'service_manager', 'business_admin', 'solution', 'service', 'sales')
AND id NOT IN (
    SELECT user_id FROM permission WHERE module = 'performance_management'
);

-- 查看liuq用户的绩效管理权限
SELECT 
    u.username,
    u.role,
    u.real_name,
    p.module,
    p.can_view,
    p.can_create,
    p.can_edit,
    p.can_delete
FROM "user" u
LEFT JOIN permission p ON u.id = p.user_id AND p.module = 'performance_management'
WHERE u.username = 'liuq';

-- 查看所有用户的绩效管理权限统计
SELECT 
    u.role,
    COUNT(*) as user_count,
    COUNT(CASE WHEN p.can_view = true THEN 1 END) as can_view_count,
    COUNT(CASE WHEN p.can_create = true THEN 1 END) as can_create_count,
    COUNT(CASE WHEN p.can_edit = true THEN 1 END) as can_edit_count,
    COUNT(CASE WHEN p.can_delete = true THEN 1 END) as can_delete_count
FROM "user" u
LEFT JOIN permission p ON u.id = p.user_id AND p.module = 'performance_management'
GROUP BY u.role
ORDER BY u.role;