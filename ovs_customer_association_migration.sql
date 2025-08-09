-- OVS数据库客户关联表迁移脚本
-- 创建日期: 2025-08-09
-- 目的: 将本地的project_customer_associations表结构迁移到OVS云端数据库
-- 遵循CLAUDE.md规范的通用迁移方法

-- 1. 创建project_customer_associations表
CREATE TABLE IF NOT EXISTS project_customer_associations (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    customer_type VARCHAR NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE,
    updated_at TIMESTAMP WITHOUT TIME ZONE,
    created_by INTEGER,
    
    -- 外键约束
    CONSTRAINT fk_project_customer_associations_project_id 
        FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_project_customer_associations_company_id 
        FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE,
    CONSTRAINT fk_project_customer_associations_created_by 
        FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL,
        
    -- 唯一约束：防止同一项目关联同一公司多次
    CONSTRAINT uq_project_company_customer_type 
        UNIQUE (project_id, company_id, customer_type)
);

-- 2. 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_project_customer_associations_project_id 
    ON project_customer_associations(project_id);

CREATE INDEX IF NOT EXISTS idx_project_customer_associations_company_id 
    ON project_customer_associations(company_id);

CREATE INDEX IF NOT EXISTS idx_project_customer_associations_created_by 
    ON project_customer_associations(created_by);

-- 3. 添加注释
COMMENT ON TABLE project_customer_associations IS '项目客户关联表';
COMMENT ON COLUMN project_customer_associations.id IS '主键ID';
COMMENT ON COLUMN project_customer_associations.project_id IS '关联的项目ID';
COMMENT ON COLUMN project_customer_associations.company_id IS '关联的公司ID';
COMMENT ON COLUMN project_customer_associations.customer_type IS '客户类型（end_user等）';
COMMENT ON COLUMN project_customer_associations.created_at IS '创建时间';
COMMENT ON COLUMN project_customer_associations.updated_at IS '更新时间';
COMMENT ON COLUMN project_customer_associations.created_by IS '创建者用户ID';

-- 4. 验证表创建是否成功
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_name = 'project_customer_associations' 
ORDER BY ordinal_position;