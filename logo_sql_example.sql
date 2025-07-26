-- Logo数据库管理SQL示例
-- 在 company_assets 表中插入Logo

-- 1. 查看当前Logo状态
SELECT 
    id,
    asset_name,
    asset_key,
    file_name,
    file_type,
    file_size,
    is_default,
    is_active,
    created_at
FROM company_assets 
WHERE asset_type = 'logo' AND is_active = true
ORDER BY is_default DESC, created_at DESC;

-- 2. 插入新Logo (需要先将文件转换为Base64)
-- 注意：file_content 字段需要存储Base64编码的文件内容
INSERT INTO company_assets (
    asset_type,
    asset_name,
    asset_key,
    file_name,
    file_type,
    file_size,
    file_content,
    is_active,
    is_default,
    created_at,
    updated_at
) VALUES (
    'logo',
    '公司Logo',
    'evertac_logo',
    'company_logo.png',
    'image/png',
    15360,  -- 文件大小（字节）
    'iVBORw0KGgoAAAANSUhEUgAA...', -- Base64编码的文件内容（这里需要实际的Base64数据）
    true,
    true,
    NOW(),
    NOW()
);

-- 3. 更新现有Logo为默认Logo
UPDATE company_assets 
SET is_default = false 
WHERE asset_type = 'logo';

UPDATE company_assets 
SET is_default = true 
WHERE id = 1 AND asset_type = 'logo';

-- 4. 软删除Logo
UPDATE company_assets 
SET is_active = false 
WHERE id = 1 AND asset_type = 'logo';

-- 5. 获取Logo的Base64 Data URL（用于HTML显示）
SELECT 
    CONCAT('data:', file_type, ';base64,', file_content) as data_url
FROM company_assets 
WHERE asset_key = 'evertac_logo' 
  AND asset_type = 'logo' 
  AND is_active = true
LIMIT 1;