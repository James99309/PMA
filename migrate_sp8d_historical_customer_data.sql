-- SP8D数据库历史项目客户关联数据迁移脚本
-- 目的：将SP8D数据库projects表中的字符串客户数据迁移到project_customer_associations表中的关系数据
-- 创建日期：2025-08-09
-- 遵循CLAUDE.md规范，使用与本地数据库和OVS相同的迁移方法
-- 问题：SP8D环境升级后历史客户关联数据不显示，因为存储在projects表的字符串字段中

-- 迁移策略：
-- 1. 从projects表中提取非空的客户字段（end_user, design_issues, dealer, contractor, system_integrator）
-- 2. 通过公司名称匹配找到对应的companies.id
-- 3. 创建project_customer_associations记录，created_by设置为项目的owner_id
-- 4. 处理可能的重复公司名称问题：优先选择未删除且ID较小的记录
-- 5. SP8D数据规模最大，预计迁移880条记录

BEGIN;

-- 显示迁移前状态
SELECT 'SP8D迁移前状态检查' as info;
SELECT 
    '当前关联记录数' as item,
    COUNT(*) as count
FROM project_customer_associations;

-- 1. 迁移经销商数据（预计363条）
INSERT INTO project_customer_associations (project_id, company_id, customer_type, created_by, created_at, updated_at)
SELECT DISTINCT
    p.id as project_id,
    c.id as company_id,
    'dealer' as customer_type,
    p.owner_id as created_by,
    p.created_at,
    p.updated_at
FROM projects p
JOIN (
    -- 子查询：对于每个公司名称，选择ID最小的未删除记录
    SELECT DISTINCT ON (company_name) 
        id, company_name
    FROM companies 
    WHERE is_deleted = false
    ORDER BY company_name, id ASC
) c ON TRIM(p.dealer) = TRIM(c.company_name)
WHERE p.dealer IS NOT NULL 
  AND p.dealer <> ''
  AND NOT EXISTS (
    SELECT 1 FROM project_customer_associations pca 
    WHERE pca.project_id = p.id 
    AND pca.company_id = c.id 
    AND pca.customer_type = 'dealer'
  );

-- 显示经销商迁移结果
SELECT 
    'SP8D经销商数据迁移完成' as info,
    COUNT(*) as "迁移记录数"
FROM project_customer_associations 
WHERE customer_type = 'dealer';

-- 2. 迁移系统集成商数据（预计282条）
INSERT INTO project_customer_associations (project_id, company_id, customer_type, created_by, created_at, updated_at)
SELECT DISTINCT
    p.id as project_id,
    c.id as company_id,
    'system_integrator' as customer_type,
    p.owner_id as created_by,
    p.created_at,
    p.updated_at
FROM projects p
JOIN (
    -- 子查询：对于每个公司名称，选择ID最小的未删除记录
    SELECT DISTINCT ON (company_name) 
        id, company_name
    FROM companies 
    WHERE is_deleted = false
    ORDER BY company_name, id ASC
) c ON TRIM(p.system_integrator) = TRIM(c.company_name)
WHERE p.system_integrator IS NOT NULL 
  AND p.system_integrator <> ''
  AND NOT EXISTS (
    SELECT 1 FROM project_customer_associations pca 
    WHERE pca.project_id = p.id 
    AND pca.company_id = c.id 
    AND pca.customer_type = 'system_integrator'
  );

-- 显示系统集成商迁移结果
SELECT 
    'SP8D系统集成商数据迁移完成' as info,
    COUNT(*) as "迁移记录数"
FROM project_customer_associations 
WHERE customer_type = 'system_integrator';

-- 3. 迁移直接用户数据（预计56条）
INSERT INTO project_customer_associations (project_id, company_id, customer_type, created_by, created_at, updated_at)
SELECT DISTINCT
    p.id as project_id,
    c.id as company_id,
    'end_user' as customer_type,
    p.owner_id as created_by,
    p.created_at,
    p.updated_at
FROM projects p
JOIN (
    -- 子查询：对于每个公司名称，选择ID最小的未删除记录
    SELECT DISTINCT ON (company_name) 
        id, company_name
    FROM companies 
    WHERE is_deleted = false
    ORDER BY company_name, id ASC
) c ON TRIM(p.end_user) = TRIM(c.company_name)
WHERE p.end_user IS NOT NULL 
  AND p.end_user <> ''
  AND NOT EXISTS (
    SELECT 1 FROM project_customer_associations pca 
    WHERE pca.project_id = p.id 
    AND pca.company_id = c.id 
    AND pca.customer_type = 'end_user'
  );

-- 显示直接用户迁移结果
SELECT 
    'SP8D直接用户数据迁移完成' as info,
    COUNT(*) as "迁移记录数"
FROM project_customer_associations 
WHERE customer_type = 'end_user';

-- 4. 迁移设计院及顾问数据（预计179条）
INSERT INTO project_customer_associations (project_id, company_id, customer_type, created_by, created_at, updated_at)
SELECT DISTINCT
    p.id as project_id,
    c.id as company_id,
    'design_issues' as customer_type,
    p.owner_id as created_by,
    p.created_at,
    p.updated_at
FROM projects p
JOIN (
    -- 子查询：对于每个公司名称，选择ID最小的未删除记录
    SELECT DISTINCT ON (company_name) 
        id, company_name
    FROM companies 
    WHERE is_deleted = false
    ORDER BY company_name, id ASC
) c ON TRIM(p.design_issues) = TRIM(c.company_name)
WHERE p.design_issues IS NOT NULL 
  AND p.design_issues <> ''
  AND NOT EXISTS (
    SELECT 1 FROM project_customer_associations pca 
    WHERE pca.project_id = p.id 
    AND pca.company_id = c.id 
    AND pca.customer_type = 'design_issues'
  );

-- 显示设计院顾问迁移结果
SELECT 
    'SP8D设计院顾问数据迁移完成' as info,
    COUNT(*) as "迁移记录数"
FROM project_customer_associations 
WHERE customer_type = 'design_issues';

-- 5. 迁移总承包单位数据（预计0条）
INSERT INTO project_customer_associations (project_id, company_id, customer_type, created_by, created_at, updated_at)
SELECT DISTINCT
    p.id as project_id,
    c.id as company_id,
    'contractor' as customer_type,
    p.owner_id as created_by,
    p.created_at,
    p.updated_at
FROM projects p
JOIN (
    -- 子查询：对于每个公司名称，选择ID最小的未删除记录
    SELECT DISTINCT ON (company_name) 
        id, company_name
    FROM companies 
    WHERE is_deleted = false
    ORDER BY company_name, id ASC
) c ON TRIM(p.contractor) = TRIM(c.company_name)
WHERE p.contractor IS NOT NULL 
  AND p.contractor <> ''
  AND NOT EXISTS (
    SELECT 1 FROM project_customer_associations pca 
    WHERE pca.project_id = p.id 
    AND pca.company_id = c.id 
    AND pca.customer_type = 'contractor'
  );

-- SP8D迁移完成后的验证和统计
SELECT 
    'SP8D迁移总统计' as info,
    COUNT(*) as total_migrated
FROM project_customer_associations 
WHERE created_by IS NOT NULL;

-- 按类型显示迁移统计
SELECT 
    customer_type,
    COUNT(*) as count
FROM project_customer_associations
GROUP BY customer_type
ORDER BY count DESC, customer_type;

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
    'SP8D验证get_active_associations逻辑' as info,
    COUNT(*) as total_active_associations
FROM project_customer_associations pca
JOIN companies c ON pca.company_id = c.id
WHERE c.is_deleted = false;

-- 显示顶级客户关联统计
SELECT 
    'SP8D顶级客户关联统计' as info;

SELECT 
    c.company_name,
    COUNT(DISTINCT pca.project_id) as project_count,
    pca.customer_type,
    CASE pca.customer_type
        WHEN 'end_user' THEN '直接用户'
        WHEN 'design_issues' THEN '设计院及顾问'
        WHEN 'contractor' THEN '总承包单位'
        WHEN 'system_integrator' THEN '系统集成商'
        WHEN 'dealer' THEN '经销商'
        ELSE pca.customer_type
    END as customer_type_label
FROM project_customer_associations pca
JOIN companies c ON pca.company_id = c.id
GROUP BY c.company_name, pca.customer_type
HAVING COUNT(DISTINCT pca.project_id) >= 5
ORDER BY project_count DESC, c.company_name
LIMIT 15;

COMMIT;

-- 最终验证信息
SELECT 
    '✅ SP8D历史客户数据迁移完成' as status,
    COUNT(*) as total_associations
FROM project_customer_associations;