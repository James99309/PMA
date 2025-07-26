-- 企业字典资产字段迁移SQL
-- 为dictionaries表添加企业详细信息和Logo、邮件签名字段

-- 企业详细信息字段
ALTER TABLE dictionaries ADD COLUMN address VARCHAR(500) COMMENT '详细地址（仅对company类型有效）';
ALTER TABLE dictionaries ADD COLUMN postal_code VARCHAR(20) COMMENT '邮政编码（仅对company类型有效）';
ALTER TABLE dictionaries ADD COLUMN phone VARCHAR(50) COMMENT '企业电话（仅对company类型有效）';
ALTER TABLE dictionaries ADD COLUMN fax VARCHAR(50) COMMENT '传真（仅对company类型有效）';
ALTER TABLE dictionaries ADD COLUMN email VARCHAR(100) COMMENT '企业邮箱（仅对company类型有效）';
ALTER TABLE dictionaries ADD COLUMN website VARCHAR(200) COMMENT '网站地址（仅对company类型有效）';

-- Logo资产字段
ALTER TABLE dictionaries ADD COLUMN logo_content TEXT COMMENT 'Logo的Base64内容（仅对company类型有效）';
ALTER TABLE dictionaries ADD COLUMN logo_filename VARCHAR(100) COMMENT 'Logo原始文件名（仅对company类型有效）';
ALTER TABLE dictionaries ADD COLUMN logo_type VARCHAR(50) COMMENT 'Logo文件类型（仅对company类型有效）';
ALTER TABLE dictionaries ADD COLUMN logo_size INTEGER COMMENT 'Logo文件大小字节（仅对company类型有效）';

-- 邮件签名资产字段
ALTER TABLE dictionaries ADD COLUMN email_signature_content TEXT COMMENT '邮件签名图片的Base64内容（仅对company类型有效）';
ALTER TABLE dictionaries ADD COLUMN email_signature_filename VARCHAR(100) COMMENT '邮件签名原始文件名（仅对company类型有效）';
ALTER TABLE dictionaries ADD COLUMN email_signature_type VARCHAR(50) COMMENT '邮件签名文件类型（仅对company类型有效）';
ALTER TABLE dictionaries ADD COLUMN email_signature_size INTEGER COMMENT '邮件签名文件大小字节（仅对company类型有效）';

-- 创建索引以提高查询性能
CREATE INDEX idx_dictionaries_company_logo ON dictionaries(type, logo_content(100));
CREATE INDEX idx_dictionaries_company_phone ON dictionaries(type, phone);
CREATE INDEX idx_dictionaries_company_email ON dictionaries(type, email);

-- 验证表结构
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'dictionaries' 
  AND COLUMN_NAME IN (
    'address', 'postal_code', 'phone', 'fax', 'email', 'website',
    'logo_content', 'logo_filename', 'logo_type', 'logo_size',
    'email_signature_content', 'email_signature_filename', 
    'email_signature_type', 'email_signature_size'
  )
ORDER BY ORDINAL_POSITION;