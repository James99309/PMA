-- 企业字典资产字段迁移SQL (PostgreSQL版本)
-- 为dictionaries表添加企业详细信息和Logo、邮件签名字段

-- 企业详细信息字段
ALTER TABLE dictionaries ADD COLUMN IF NOT EXISTS address VARCHAR(500);
ALTER TABLE dictionaries ADD COLUMN IF NOT EXISTS postal_code VARCHAR(20);
ALTER TABLE dictionaries ADD COLUMN IF NOT EXISTS phone VARCHAR(50);
ALTER TABLE dictionaries ADD COLUMN IF NOT EXISTS fax VARCHAR(50);
ALTER TABLE dictionaries ADD COLUMN IF NOT EXISTS email VARCHAR(100);
ALTER TABLE dictionaries ADD COLUMN IF NOT EXISTS website VARCHAR(200);

-- Logo资产字段
ALTER TABLE dictionaries ADD COLUMN IF NOT EXISTS logo_content TEXT;
ALTER TABLE dictionaries ADD COLUMN IF NOT EXISTS logo_filename VARCHAR(100);
ALTER TABLE dictionaries ADD COLUMN IF NOT EXISTS logo_type VARCHAR(50);
ALTER TABLE dictionaries ADD COLUMN IF NOT EXISTS logo_size INTEGER;

-- 邮件签名资产字段
ALTER TABLE dictionaries ADD COLUMN IF NOT EXISTS email_signature_content TEXT;
ALTER TABLE dictionaries ADD COLUMN IF NOT EXISTS email_signature_filename VARCHAR(100);
ALTER TABLE dictionaries ADD COLUMN IF NOT EXISTS email_signature_type VARCHAR(50);
ALTER TABLE dictionaries ADD COLUMN IF NOT EXISTS email_signature_size INTEGER;

-- 添加字段注释 (PostgreSQL语法)
COMMENT ON COLUMN dictionaries.address IS '详细地址（仅对company类型有效）';
COMMENT ON COLUMN dictionaries.postal_code IS '邮政编码（仅对company类型有效）';
COMMENT ON COLUMN dictionaries.phone IS '企业电话（仅对company类型有效）';
COMMENT ON COLUMN dictionaries.fax IS '传真（仅对company类型有效）';
COMMENT ON COLUMN dictionaries.email IS '企业邮箱（仅对company类型有效）';
COMMENT ON COLUMN dictionaries.website IS '网站地址（仅对company类型有效）';

COMMENT ON COLUMN dictionaries.logo_content IS 'Logo的Base64内容（仅对company类型有效）';
COMMENT ON COLUMN dictionaries.logo_filename IS 'Logo原始文件名（仅对company类型有效）';
COMMENT ON COLUMN dictionaries.logo_type IS 'Logo文件类型（仅对company类型有效）';
COMMENT ON COLUMN dictionaries.logo_size IS 'Logo文件大小字节（仅对company类型有效）';

COMMENT ON COLUMN dictionaries.email_signature_content IS '邮件签名图片的Base64内容（仅对company类型有效）';
COMMENT ON COLUMN dictionaries.email_signature_filename IS '邮件签名原始文件名（仅对company类型有效）';
COMMENT ON COLUMN dictionaries.email_signature_type IS '邮件签名文件类型（仅对company类型有效）';
COMMENT ON COLUMN dictionaries.email_signature_size IS '邮件签名文件大小字节（仅对company类型有效）';

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_dictionaries_company_logo ON dictionaries(type) WHERE logo_content IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_dictionaries_company_phone ON dictionaries(type, phone) WHERE type = 'company';
CREATE INDEX IF NOT EXISTS idx_dictionaries_company_email ON dictionaries(type, email) WHERE type = 'company';

-- 验证表结构
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'dictionaries' 
  AND column_name IN (
    'address', 'postal_code', 'phone', 'fax', 'email', 'website',
    'logo_content', 'logo_filename', 'logo_type', 'logo_size',
    'email_signature_content', 'email_signature_filename', 
    'email_signature_type', 'email_signature_size'
  )
ORDER BY ordinal_position;