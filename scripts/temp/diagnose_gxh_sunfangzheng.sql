-- 诊断 gxh 账户看不到"孙方正"联系人的问题
-- 执行数据库: SP8D (Supabase)
-- 问题描述: gxh在"深圳市瑞迪兴智能设计研究院"项目的行动记录中能看到"孙方正",但客户关联区看不到此联系人

-- ================================================================================
-- 步骤1: 查找 gxh 用户信息
-- ================================================================================
SELECT
    id as user_id,
    username,
    real_name,
    role,
    department,
    company_name
FROM users
WHERE username = 'gxh'
LIMIT 1;

-- ================================================================================
-- 步骤2: 查找"深圳市瑞迪兴智能设计研究院"项目
-- ================================================================================
SELECT
    id as project_id,
    project_name,
    owner_id,
    created_at,
    status
FROM projects
WHERE project_name LIKE '%瑞迪兴%'
  AND is_deleted = false
ORDER BY created_at DESC;

-- ================================================================================
-- 步骤3: 查找名为"孙方正"的联系人
-- ================================================================================
SELECT
    c.id as contact_id,
    c.name as contact_name,
    c.company_id,
    c.owner_id as contact_owner_id,
    c.is_deleted,
    c.created_at,
    comp.company_name,
    comp.owner_id as company_owner_id,
    comp.is_deleted as company_is_deleted,
    u.username as contact_owner_username,
    u.real_name as contact_owner_real_name
FROM contacts c
LEFT JOIN companies comp ON c.company_id = comp.id
LEFT JOIN users u ON c.owner_id = u.id
WHERE c.name LIKE '%孙方正%'
ORDER BY c.created_at DESC;

-- ================================================================================
-- 步骤4: 检查"深圳市瑞迪兴智能设计研究院"客户公司
-- ================================================================================
SELECT
    id as company_id,
    company_name,
    owner_id,
    is_deleted,
    created_at
FROM companies
WHERE company_name LIKE '%瑞迪兴%'
  AND is_deleted = false
ORDER BY created_at DESC;

-- ================================================================================
-- 步骤5: 检查项目的客户关联 (关键!)
-- ================================================================================
-- 假设项目ID为XXX (从步骤2获取),检查该项目关联了哪些客户公司
SELECT
    pca.id as association_id,
    pca.project_id,
    pca.company_id,
    pca.customer_type,
    pca.created_by,
    pca.created_at,
    comp.company_name,
    comp.is_deleted as company_is_deleted,
    u.username as created_by_username,
    u.real_name as created_by_real_name
FROM project_customer_associations pca
LEFT JOIN companies comp ON pca.company_id = comp.id
LEFT JOIN users u ON pca.created_by = u.id
WHERE pca.project_id = (
    SELECT id FROM projects
    WHERE project_name LIKE '%深圳市瑞迪兴智能设计研究院%'
    AND is_deleted = false
    LIMIT 1
)
ORDER BY pca.created_at DESC;

-- ================================================================================
-- 步骤6: 检查关联公司下的所有联系人
-- ================================================================================
-- 查看项目关联的所有公司下的联系人列表
SELECT
    c.id as contact_id,
    c.name as contact_name,
    c.company_id,
    c.owner_id as contact_owner_id,
    c.is_deleted as contact_is_deleted,
    comp.company_name,
    u.username as contact_owner_username,
    u.real_name as contact_owner_real_name
FROM contacts c
INNER JOIN companies comp ON c.company_id = comp.id
LEFT JOIN users u ON c.owner_id = u.id
WHERE c.company_id IN (
    SELECT pca.company_id
    FROM project_customer_associations pca
    WHERE pca.project_id = (
        SELECT id FROM projects
        WHERE project_name LIKE '%深圳市瑞迪兴智能设计研究院%'
        AND is_deleted = false
        LIMIT 1
    )
)
ORDER BY c.name;

-- ================================================================================
-- 步骤7: 检查行动记录中提到"孙方正"的记录
-- ================================================================================
SELECT
    a.id as action_id,
    a.project_id,
    a.contact_id,
    a.company_id,
    a.communication,
    a.date as action_date,
    a.owner_id as action_owner_id,
    a.created_at,
    c.name as contact_name,
    c.company_id as contact_company_id,
    comp.company_name as action_company_name,
    u.username as action_owner_username,
    u.real_name as action_owner_real_name
FROM actions a
LEFT JOIN contacts c ON a.contact_id = c.id
LEFT JOIN companies comp ON a.company_id = comp.id
LEFT JOIN users u ON a.owner_id = u.id
WHERE a.project_id = (
    SELECT id FROM projects
    WHERE project_name LIKE '%深圳市瑞迪兴智能设计研究院%'
    AND is_deleted = false
    LIMIT 1
)
AND a.communication LIKE '%孙方正%'
ORDER BY a.created_at DESC;

-- ================================================================================
-- 步骤8: 诊断总结 - 核心问题检查
-- ================================================================================
-- 问题A: 孙方正联系人是否存在?
-- 答案: 从步骤3的结果判断

-- 问题B: 孙方正所属公司是否已关联到项目?
-- 答案: 对比步骤3中孙方正的company_id 和 步骤5中项目关联的company_id列表
--       如果孙方正的company_id不在步骤5的列表中 → 这就是问题根源!

-- 问题C: gxh 是否有查看孙方正联系人的权限?
-- 答案: 从步骤3中查看contact_owner_id:
--       - 如果 contact_owner_id = gxh的user_id → gxh可见
--       - 否则需要检查gxh的权限级别和数据归属关系

-- 问题D: 孙方正联系人是否被标记为已删除?
-- 答案: 从步骤3的 is_deleted 字段判断

-- ================================================================================
-- 解决方案 (根据诊断结果选择)
-- ================================================================================

-- 方案A: 如果孙方正所属公司未关联到项目
-- 执行: 添加项目-客户关联
/*
INSERT INTO project_customer_associations (project_id, company_id, customer_type, created_by, created_at, updated_at)
VALUES (
    (SELECT id FROM projects WHERE project_name LIKE '%深圳市瑞迪兴智能设计研究院%' AND is_deleted = false LIMIT 1),
    (SELECT company_id FROM contacts WHERE name LIKE '%孙方正%' AND is_deleted = false LIMIT 1),
    'end_user',  -- 或其他合适的客户类型
    (SELECT id FROM users WHERE username = 'gxh' LIMIT 1),
    NOW(),
    NOW()
);
*/

-- 方案B: 如果孙方正联系人已删除
-- 执行: 恢复联系人
/*
UPDATE contacts
SET is_deleted = false
WHERE name LIKE '%孙方正%';
*/

-- 方案C: 如果孙方正联系人不存在
-- 执行: 创建孙方正联系人记录
/*
INSERT INTO contacts (name, company_id, owner_id, created_at, updated_at, is_deleted)
VALUES (
    '孙方正',
    (SELECT id FROM companies WHERE company_name LIKE '%瑞迪兴%' AND is_deleted = false LIMIT 1),
    (SELECT id FROM users WHERE username = 'gxh' LIMIT 1),
    NOW(),
    NOW(),
    false
);
*/
