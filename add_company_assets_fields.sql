-- 企业资产字段迁移SQL
-- 为companies表添加Logo、邮件签名和详细信息字段

-- 企业详细信息字段
ALTER TABLE companies ADD COLUMN detailed_address VARCHAR(500) COMMENT '详细地址（扩展）';
ALTER TABLE companies ADD COLUMN postal_code VARCHAR(20) COMMENT '邮政编码';
ALTER TABLE companies ADD COLUMN phone VARCHAR(50) COMMENT '企业电话';
ALTER TABLE companies ADD COLUMN fax VARCHAR(50) COMMENT '传真';
ALTER TABLE companies ADD COLUMN email VARCHAR(100) COMMENT '企业邮箱';
ALTER TABLE companies ADD COLUMN website VARCHAR(200) COMMENT '网站地址';

-- Logo资产字段
ALTER TABLE companies ADD COLUMN logo_content TEXT COMMENT 'Logo的Base64内容';
ALTER TABLE companies ADD COLUMN logo_filename VARCHAR(100) COMMENT 'Logo原始文件名';
ALTER TABLE companies ADD COLUMN logo_type VARCHAR(50) COMMENT 'Logo文件类型';
ALTER TABLE companies ADD COLUMN logo_size INTEGER COMMENT 'Logo文件大小（字节）';

-- 邮件签名资产字段
ALTER TABLE companies ADD COLUMN email_signature_content TEXT COMMENT '邮件签名图片的Base64内容';
ALTER TABLE companies ADD COLUMN email_signature_filename VARCHAR(100) COMMENT '邮件签名原始文件名';
ALTER TABLE companies ADD COLUMN email_signature_type VARCHAR(50) COMMENT '邮件签名文件类型';
ALTER TABLE companies ADD COLUMN email_signature_size INTEGER COMMENT '邮件签名文件大小（字节）';

-- 创建索引以提高查询性能
CREATE INDEX idx_companies_logo ON companies(logo_content(100));
CREATE INDEX idx_companies_email_signature ON companies(email_signature_content(100));
CREATE INDEX idx_companies_phone ON companies(phone);
CREATE INDEX idx_companies_email ON companies(email);

-- 验证表结构
SELECT 
    COLUMN_NAME,
    DATA_TYPE,
    CHARACTER_MAXIMUM_LENGTH,
    IS_NULLABLE,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_NAME = 'companies' 
  AND COLUMN_NAME IN (
    'detailed_address', 'postal_code', 'phone', 'fax', 'email', 'website',
    'logo_content', 'logo_filename', 'logo_type', 'logo_size',
    'email_signature_content', 'email_signature_filename', 
    'email_signature_type', 'email_signature_size'
  )
ORDER BY ORDINAL_POSITION;