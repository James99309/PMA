-- OVS数据库历史项目客户关联数据迁移脚本
-- 目的：将OVS数据库projects表中的字符串客户数据迁移到project_customer_associations表中的关系数据
-- 创建日期：2025-08-09
-- 遵循CLAUDE.md规范，使用与本地数据库相同的迁移方法
-- 问题：OVS环境升级后历史客户关联数据不显示，因为存储在projects表的字符串字段中

-- 迁移策略：
-- 1. 从projects表中提取非空的客户字段（end_user, design_issues, dealer, contractor, system_integrator）
-- 2. 通过公司名称匹配找到对应的companies.id
-- 3. 创建project_customer_associations记录，created_by设置为项目的owner_id
-- 4. 与本地迁移相同，但针对OVS数据库的实际数据

BEGIN;

-- 显示迁移前状态
SELECT 'OVS迁移前状态检查' as info;
SELECT 
    '当前关联记录数' as item,
    COUNT(*) as count
FROM project_customer_associations;

-- 1. 迁移经销商数据
INSERT INTO project_customer_associations (project_id, company_id, customer_type, created_by, created_at, updated_at)
SELECT DISTINCT
    p.id as project_id,
    c.id as company_id,
    'dealer' as customer_type,
    p.owner_id as created_by,
    p.created_at,
    p.updated_at
FROM projects p
JOIN companies c ON TRIM(p.dealer) = TRIM(c.company_name)
WHERE p.dealer IS NOT NULL 
  AND p.dealer <> ''
  AND c.is_deleted = false
  AND NOT EXISTS (
    SELECT 1 FROM project_customer_associations pca 
    WHERE pca.project_id = p.id 
    AND pca.company_id = c.id 
    AND pca.customer_type = 'dealer'
  );

-- 显示经销商迁移结果
SELECT 
    'OVS经销商数据迁移完成' as info,
    ROW_NUMBER() OVER () as "迁移进度"
FROM project_customer_associations 
WHERE customer_type = 'dealer'
LIMIT 1;

-- 2. 迁移系统集成商数据
INSERT INTO project_customer_associations (project_id, company_id, customer_type, created_by, created_at, updated_at)
SELECT DISTINCT
    p.id as project_id,
    c.id as company_id,
    'system_integrator' as customer_type,
    p.owner_id as created_by,
    p.created_at,
    p.updated_at
FROM projects p
JOIN companies c ON TRIM(p.system_integrator) = TRIM(c.company_name)
WHERE p.system_integrator IS NOT NULL 
  AND p.system_integrator <> ''
  AND c.is_deleted = false
  AND NOT EXISTS (
    SELECT 1 FROM project_customer_associations pca 
    WHERE pca.project_id = p.id 
    AND pca.company_id = c.id 
    AND pca.customer_type = 'system_integrator'
  );

-- 3. 迁移直接用户数据
INSERT INTO project_customer_associations (project_id, company_id, customer_type, created_by, created_at, updated_at)
SELECT DISTINCT
    p.id as project_id,
    c.id as company_id,
    'end_user' as customer_type,
    p.owner_id as created_by,
    p.created_at,
    p.updated_at
FROM projects p
JOIN companies c ON TRIM(p.end_user) = TRIM(c.company_name)
WHERE p.end_user IS NOT NULL 
  AND p.end_user <> ''
  AND c.is_deleted = false
  AND NOT EXISTS (
    SELECT 1 FROM project_customer_associations pca 
    WHERE pca.project_id = p.id 
    AND pca.company_id = c.id 
    AND pca.customer_type = 'end_user'
  );

-- 4. 迁移设计院及顾问数据
INSERT INTO project_customer_associations (project_id, company_id, customer_type, created_by, created_at, updated_at)
SELECT DISTINCT
    p.id as project_id,
    c.id as company_id,
    'design_issues' as customer_type,
    p.owner_id as created_by,
    p.created_at,
    p.updated_at
FROM projects p
JOIN companies c ON TRIM(p.design_issues) = TRIM(c.company_name)
WHERE p.design_issues IS NOT NULL 
  AND p.design_issues <> ''
  AND c.is_deleted = false
  AND NOT EXISTS (
    SELECT 1 FROM project_customer_associations pca 
    WHERE pca.project_id = p.id 
    AND pca.company_id = c.id 
    AND pca.customer_type = 'design_issues'
  );

-- 5. 迁移总承包单位数据
INSERT INTO project_customer_associations (project_id, company_id, customer_type, created_by, created_at, updated_at)
SELECT DISTINCT
    p.id as project_id,
    c.id as company_id,
    'contractor' as customer_type,
    p.owner_id as created_by,
    p.created_at,
    p.updated_at
FROM projects p
JOIN companies c ON TRIM(p.contractor) = TRIM(c.company_name)
WHERE p.contractor IS NOT NULL 
  AND p.contractor <> ''
  AND c.is_deleted = false
  AND NOT EXISTS (
    SELECT 1 FROM project_customer_associations pca 
    WHERE pca.project_id = p.id 
    AND pca.company_id = c.id 
    AND pca.customer_type = 'contractor'
  );

-- OVS迁移完成后的验证和统计
SELECT 
    'OVS迁移统计' as info,
    COUNT(*) as total_migrated
FROM project_customer_associations 
WHERE created_by IS NOT NULL;

-- 按类型显示迁移统计
SELECT 
    customer_type,
    COUNT(*) as count
FROM project_customer_associations
GROUP BY customer_type
ORDER BY customer_type;

-- 显示迁移的具体数据（前10条）
SELECT 
    p.project_name,
    c.company_name,
    pca.customer_type,
    CASE pca.customer_type
        WHEN 'end_user' THEN '直接用户'
        WHEN 'design_issues' THEN '设计院及顾问'
        WHEN 'contractor' THEN '总承包单位'
        WHEN 'system_integrator' THEN '系统集成商'
        WHEN 'dealer' THEN '经销商'
        ELSE pca.customer_type
    END as customer_type_label,
    u.username as created_by_user,
    pca.created_at
FROM project_customer_associations pca
JOIN projects p ON pca.project_id = p.id
JOIN companies c ON pca.company_id = c.id
LEFT JOIN users u ON pca.created_by = u.id
WHERE pca.created_by IS NOT NULL
ORDER BY pca.created_at DESC
LIMIT 10;

-- 验证get_active_associations方法逻辑
SELECT 
    'OVS验证get_active_associations逻辑' as info,
    COUNT(*) as total_active_associations
FROM project_customer_associations pca
JOIN companies c ON pca.company_id = c.id
WHERE c.is_deleted = false;

COMMIT;

-- 最终验证信息
SELECT 
    '✅ OVS历史客户数据迁移完成' as status,
    COUNT(*) as total_associations
FROM project_customer_associations;