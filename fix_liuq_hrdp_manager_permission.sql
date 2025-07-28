-- 专门为liuq用户（hrdp_manager角色）添加绩效管理权限
-- 请在数据库管理界面中执行此脚本

-- 1. 确认liuq用户的角色
SELECT 
    id,
    username, 
    role, 
    real_name
FROM "user" 
WHERE username = 'liuq';

-- 2. 检查liuq用户是否已有performance_management权限
SELECT 
    u.username,
    u.role,
    p.module,
    p.can_view,
    p.can_create,
    p.can_edit,
    p.can_delete
FROM "user" u
LEFT JOIN permission p ON u.id = p.user_id AND p.module = 'performance_management'
WHERE u.username = 'liuq';

-- 3. 为liuq用户添加performance_management权限
-- hrdp_manager（人力资源发展经理）应该有完整的绩效管理权限
INSERT INTO permission (user_id, module, can_view, can_create, can_edit, can_delete)
SELECT 
    u.id,
    'performance_management',
    true,  -- can_view: 可以查看绩效数据
    true,  -- can_create: 可以创建绩效目标
    true,  -- can_edit: 可以编辑绩效设置
    false  -- can_delete: 不能删除绩效记录（安全考虑）
FROM "user" u
WHERE u.username = 'liuq'
AND u.role = 'hrdp_manager'
AND u.id NOT IN (
    SELECT user_id 
    FROM permission 
    WHERE module = 'performance_management'
);

-- 4. 验证权限添加是否成功
SELECT 
    u.username,
    u.role,
    p.module,
    p.can_view as "查看权限",
    p.can_create as "创建权限", 
    p.can_edit as "编辑权限",
    p.can_delete as "删除权限"
FROM "user" u
JOIN permission p ON u.id = p.user_id
WHERE u.username = 'liuq' 
AND p.module = 'performance_management';

-- 5. 同时为所有hrdp_manager角色用户添加权限（如果有其他相同角色用户）
INSERT INTO permission (user_id, module, can_view, can_create, can_edit, can_delete)
SELECT 
    u.id,
    'performance_management',
    true,  -- can_view
    true,  -- can_create
    true,  -- can_edit
    false  -- can_delete
FROM "user" u
WHERE u.role = 'hrdp_manager'
AND u.id NOT IN (
    SELECT user_id 
    FROM permission 
    WHERE module = 'performance_management'
);

-- 6. 查看所有hrdp_manager角色用户的权限情况
SELECT 
    u.username,
    u.real_name,
    u.role,
    p.module,
    p.can_view,
    p.can_create,
    p.can_edit,
    p.can_delete
FROM "user" u
LEFT JOIN permission p ON u.id = p.user_id AND p.module = 'performance_management'
WHERE u.role = 'hrdp_manager';

-- 执行完成后，liuq用户应该能够：
-- ✅ 在仪表盘看到绩效看板按钮
-- ✅ 访问绩效管理页面
-- ✅ 查看和编辑绩效数据