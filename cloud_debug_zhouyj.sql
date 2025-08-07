-- 云端SP8D数据库zhouyj权限调试SQL
-- 请在云端数据库管理界面运行这些查询

-- 1. 查看zhouyj基本信息
SELECT 
    id,
    username,
    real_name,
    role,
    department,
    company_name,
    data_permission_level,
    is_active,
    created_at
FROM users 
WHERE username = 'zhouyj';

-- 2. 查看sales_manager角色在project模块的权限配置
SELECT 
    role,
    module,
    can_view,
    can_create,
    can_edit,
    can_delete,
    permission_level,
    permission_level_description
FROM role_permissions 
WHERE role = 'sales_manager' AND module = 'project';

-- 3. 查看zhouyj的数据归属关系
SELECT 
    a.id,
    a.viewer_id,
    a.owner_id,
    o.username as owner_username,
    o.real_name as owner_name,
    o.department as owner_department,
    a.created_at
FROM affiliations a
JOIN users o ON a.owner_id = o.id
WHERE a.viewer_id = (SELECT id FROM users WHERE username = 'zhouyj');

-- 4. 查看zhouyj作为厂商销售经理的项目
SELECT 
    p.id,
    p.project_name,
    p.owner_id,
    u.username as owner_name,
    p.created_at
FROM projects p
JOIN users u ON p.owner_id = u.id
WHERE p.vendor_sales_manager_id = (SELECT id FROM users WHERE username = 'zhouyj')
AND p.is_deleted = false
LIMIT 5;

-- 5. 查看zhouyj拥有的项目
SELECT 
    p.id,
    p.project_name,
    p.owner_id,
    p.created_at
FROM projects p
WHERE p.owner_id = (SELECT id FROM users WHERE username = 'zhouyj')
AND p.is_deleted = false
LIMIT 5;

-- 6. 查看同部门用户的项目（如果权限级别是department）
SELECT 
    p.id,
    p.project_name,
    p.owner_id,
    u.username as owner_name,
    u.department,
    p.created_at
FROM projects p
JOIN users u ON p.owner_id = u.id
WHERE u.department = (SELECT department FROM users WHERE username = 'zhouyj')
AND u.company_name = (SELECT company_name FROM users WHERE username = 'zhouyj')
AND u.id != (SELECT id FROM users WHERE username = 'zhouyj')
AND p.is_deleted = false
LIMIT 5;

-- 7. 统计各类项目数量
SELECT 
    'zhouyj拥有的项目' as category,
    COUNT(*) as count
FROM projects p
WHERE p.owner_id = (SELECT id FROM users WHERE username = 'zhouyj')
AND p.is_deleted = false

UNION ALL

SELECT 
    'zhouyj作为厂商销售经理的项目' as category,
    COUNT(*) as count
FROM projects p
WHERE p.vendor_sales_manager_id = (SELECT id FROM users WHERE username = 'zhouyj')
AND p.is_deleted = false

UNION ALL

SELECT 
    '同部门项目总数' as category,
    COUNT(*) as count
FROM projects p
JOIN users u ON p.owner_id = u.id
WHERE u.department = (SELECT department FROM users WHERE username = 'zhouyj')
AND u.company_name = (SELECT company_name FROM users WHERE username = 'zhouyj')
AND p.is_deleted = false

UNION ALL

SELECT 
    '系统总项目数' as category,
    COUNT(*) as count
FROM projects p
WHERE p.is_deleted = false;

-- 8. 检查zhouyj的用户权限覆盖配置（如果存在user_permissions表）
SELECT 
    module,
    can_view,
    can_create,
    can_edit,
    can_delete,
    permission_level_override
FROM user_permissions 
WHERE user_id = (SELECT id FROM users WHERE username = 'zhouyj');

-- 9. 查看最近的项目活动（检查是否有权限异常）
SELECT 
    p.id,
    p.project_name,
    p.owner_id,
    u.username as owner_name,
    u.department as owner_dept,
    p.updated_at
FROM projects p
JOIN users u ON p.owner_id = u.id
WHERE p.is_deleted = false
ORDER BY p.updated_at DESC
LIMIT 10;