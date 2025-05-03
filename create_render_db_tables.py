#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为Render创建数据库表结构
直接使用SQL语句在Render环境中创建所有必要的表

作者: Claude
创建日期: 2025-05-03
"""

import os
import sys
import logging
import sqlalchemy
from sqlalchemy import create_engine, text

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('render_db_init.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Render数据库初始化')

# Render数据库连接信息
RENDER_DB_URL = 'postgresql://pma_db_sp8d_user:LXNGJmR6bFrNecoaWbdbdzPpltIAd40w@dpg-d0b1gl1r0fns73d1jc1g-a.singapore-postgres.render.com/pma_db_sp8d'

# 表结构定义 SQL
CREATE_TABLES_SQL = """
-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(128) NOT NULL,
    real_name VARCHAR(80),
    company_name VARCHAR(100),
    email VARCHAR(120),
    phone VARCHAR(20),
    department VARCHAR(100),
    is_department_manager BOOLEAN,
    role VARCHAR(20),
    is_profile_complete BOOLEAN,
    wechat_openid VARCHAR(64),
    wechat_nickname VARCHAR(64),
    wechat_avatar VARCHAR(256),
    is_active BOOLEAN,
    created_at FLOAT8,
    last_login FLOAT8,
    company_id INTEGER
);

-- 权限表
CREATE TABLE IF NOT EXISTS permissions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    module VARCHAR(50) NOT NULL,
    can_view BOOLEAN,
    can_create BOOLEAN,
    can_edit BOOLEAN,
    can_delete BOOLEAN
);

-- 字典表
CREATE TABLE IF NOT EXISTS dictionaries (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    key VARCHAR(50) NOT NULL,
    value VARCHAR(100) NOT NULL,
    is_active BOOLEAN,
    sort_order INTEGER,
    created_at FLOAT8,
    updated_at FLOAT8
);

-- 数据关联表
CREATE TABLE IF NOT EXISTS data_affiliations (
    id SERIAL PRIMARY KEY,
    owner_id INTEGER NOT NULL,
    viewer_id INTEGER NOT NULL,
    created_at FLOAT8
);

-- 公司表
CREATE TABLE IF NOT EXISTS companies (
    id SERIAL PRIMARY KEY,
    company_code VARCHAR(20) NOT NULL,
    company_name VARCHAR(100) NOT NULL,
    country VARCHAR(50),
    region VARCHAR(50),
    address VARCHAR(200),
    industry VARCHAR(50),
    company_type VARCHAR(20),
    status VARCHAR(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    notes TEXT,
    is_deleted BOOLEAN,
    owner_id INTEGER
);

-- 联系人表
CREATE TABLE IF NOT EXISTS contacts (
    id SERIAL PRIMARY KEY,
    company_id INTEGER NOT NULL,
    name VARCHAR(50) NOT NULL,
    department VARCHAR(50),
    position VARCHAR(50),
    phone VARCHAR(20),
    email VARCHAR(100),
    is_primary BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    notes TEXT,
    owner_id INTEGER
);

-- 项目表
CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    project_name VARCHAR(64) NOT NULL,
    report_time DATE,
    project_type VARCHAR(64),
    report_source VARCHAR(64),
    product_situation VARCHAR(128),
    end_user VARCHAR(128),
    design_issues VARCHAR(128),
    dealer VARCHAR(128),
    contractor VARCHAR(128),
    system_integrator VARCHAR(128),
    current_stage VARCHAR(64),
    stage_description TEXT,
    authorization_code VARCHAR(64),
    delivery_forecast DATE,
    quotation_customer FLOAT8,
    authorization_status VARCHAR(20),
    feedback TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    owner_id INTEGER
);

-- 项目成员表
CREATE TABLE IF NOT EXISTS project_members (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role VARCHAR(50) NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 产品表
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    type VARCHAR(50),
    category VARCHAR(50),
    product_mn VARCHAR(50),
    product_name VARCHAR(100),
    model VARCHAR(100),
    specification TEXT,
    brand VARCHAR(50),
    unit VARCHAR(20),
    retail_price NUMERIC,
    status VARCHAR(20),
    image_path VARCHAR(255),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    owner_id INTEGER
);

-- 开发产品表
CREATE TABLE IF NOT EXISTS dev_products (
    id SERIAL PRIMARY KEY,
    category_id INTEGER,
    subcategory_id INTEGER,
    region_id INTEGER,
    name VARCHAR(100),
    model VARCHAR(100),
    status VARCHAR(50),
    unit VARCHAR(20),
    retail_price FLOAT8,
    description TEXT,
    image_path VARCHAR(255),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    owner_id INTEGER,
    created_by INTEGER,
    mn_code VARCHAR(20)
);

-- 开发产品规格表
CREATE TABLE IF NOT EXISTS dev_product_specs (
    id SERIAL PRIMARY KEY,
    dev_product_id INTEGER,
    field_name VARCHAR(100),
    field_value VARCHAR(255),
    field_code VARCHAR(10)
);

-- 产品类别表
CREATE TABLE IF NOT EXISTS product_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code_letter VARCHAR(1) NOT NULL,
    description TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 产品子类别表
CREATE TABLE IF NOT EXISTS product_subcategories (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    code_letter VARCHAR(1) NOT NULL,
    description TEXT,
    display_order INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    position INTEGER
);

-- 产品区域表
CREATE TABLE IF NOT EXISTS product_regions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    code_letter VARCHAR(1) NOT NULL,
    description TEXT,
    created_at TIMESTAMP
);

-- 产品代码表
CREATE TABLE IF NOT EXISTS product_codes (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    subcategory_id INTEGER NOT NULL,
    full_code VARCHAR(50) NOT NULL,
    status VARCHAR(20),
    created_by INTEGER NOT NULL,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 产品代码字段表
CREATE TABLE IF NOT EXISTS product_code_fields (
    id SERIAL PRIMARY KEY,
    subcategory_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(10),
    description TEXT,
    field_type VARCHAR(20) NOT NULL,
    position INTEGER NOT NULL,
    max_length INTEGER,
    is_required BOOLEAN,
    use_in_code BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    name_en VARCHAR(255)
);

-- 产品代码字段选项表
CREATE TABLE IF NOT EXISTS product_code_field_options (
    id SERIAL PRIMARY KEY,
    field_id INTEGER NOT NULL,
    value VARCHAR(100) NOT NULL,
    code VARCHAR(10) NOT NULL,
    description TEXT,
    is_active BOOLEAN,
    position INTEGER,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 产品代码字段值表
CREATE TABLE IF NOT EXISTS product_code_field_values (
    id SERIAL PRIMARY KEY,
    product_code_id INTEGER NOT NULL,
    field_id INTEGER NOT NULL,
    option_id INTEGER,
    custom_value VARCHAR(100)
);

-- 报价单表
CREATE TABLE IF NOT EXISTS quotations (
    id SERIAL PRIMARY KEY,
    quotation_number VARCHAR(20) NOT NULL,
    project_id INTEGER NOT NULL,
    contact_id INTEGER,
    amount FLOAT8,
    project_stage VARCHAR(20),
    project_type VARCHAR(20),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    owner_id INTEGER
);

-- 报价单明细表
CREATE TABLE IF NOT EXISTS quotation_details (
    id SERIAL PRIMARY KEY,
    quotation_id INTEGER,
    product_name VARCHAR(100),
    product_model VARCHAR(100),
    product_desc TEXT,
    brand VARCHAR(50),
    unit VARCHAR(20),
    quantity INTEGER,
    discount FLOAT8,
    market_price FLOAT8,
    unit_price FLOAT8,
    total_price FLOAT8,
    product_mn VARCHAR(100),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 授权表
CREATE TABLE IF NOT EXISTS affiliations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    company_id INTEGER NOT NULL,
    role VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 版本管理表
CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    PRIMARY KEY (version_num)
);

-- 创建外键约束

-- 联系人表外键
ALTER TABLE contacts ADD CONSTRAINT fk_contacts_company
    FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE;

-- 项目成员表外键
ALTER TABLE project_members ADD CONSTRAINT fk_project_members_project
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;
ALTER TABLE project_members ADD CONSTRAINT fk_project_members_user
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;

-- 报价单表外键
ALTER TABLE quotations ADD CONSTRAINT fk_quotations_project
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE;

-- 报价单明细表外键
ALTER TABLE quotation_details ADD CONSTRAINT fk_quotation_details_quotation
    FOREIGN KEY (quotation_id) REFERENCES quotations(id) ON DELETE CASCADE;

-- 产品代码表外键
ALTER TABLE product_codes ADD CONSTRAINT fk_product_codes_category
    FOREIGN KEY (category_id) REFERENCES product_categories(id);
ALTER TABLE product_codes ADD CONSTRAINT fk_product_codes_subcategory
    FOREIGN KEY (subcategory_id) REFERENCES product_subcategories(id);

-- 产品子类别表外键
ALTER TABLE product_subcategories ADD CONSTRAINT fk_product_subcategories_category
    FOREIGN KEY (category_id) REFERENCES product_categories(id);

-- 产品代码字段表外键
ALTER TABLE product_code_fields ADD CONSTRAINT fk_product_code_fields_subcategory
    FOREIGN KEY (subcategory_id) REFERENCES product_subcategories(id);

-- 产品代码字段选项表外键
ALTER TABLE product_code_field_options ADD CONSTRAINT fk_product_code_field_options_field
    FOREIGN KEY (field_id) REFERENCES product_code_fields(id);

-- 产品代码字段值表外键
ALTER TABLE product_code_field_values ADD CONSTRAINT fk_product_code_field_values_product_code
    FOREIGN KEY (product_code_id) REFERENCES product_codes(id);
ALTER TABLE product_code_field_values ADD CONSTRAINT fk_product_code_field_values_field
    FOREIGN KEY (field_id) REFERENCES product_code_fields(id);
ALTER TABLE product_code_field_values ADD CONSTRAINT fk_product_code_field_values_option
    FOREIGN KEY (option_id) REFERENCES product_code_field_options(id);

-- 开发产品规格表外键
ALTER TABLE dev_product_specs ADD CONSTRAINT fk_dev_product_specs_product
    FOREIGN KEY (dev_product_id) REFERENCES dev_products(id);

-- 开发产品表外键
ALTER TABLE dev_products ADD CONSTRAINT fk_dev_products_category
    FOREIGN KEY (category_id) REFERENCES product_categories(id);
ALTER TABLE dev_products ADD CONSTRAINT fk_dev_products_subcategory
    FOREIGN KEY (subcategory_id) REFERENCES product_subcategories(id);
ALTER TABLE dev_products ADD CONSTRAINT fk_dev_products_region
    FOREIGN KEY (region_id) REFERENCES product_regions(id);

-- 授权表外键
ALTER TABLE affiliations ADD CONSTRAINT fk_affiliations_user
    FOREIGN KEY (user_id) REFERENCES users(id);
ALTER TABLE affiliations ADD CONSTRAINT fk_affiliations_company
    FOREIGN KEY (company_id) REFERENCES companies(id);

-- 插入初始管理员用户
INSERT INTO users (username, password_hash, email, role, is_active)
VALUES ('admin', 'pbkdf2:sha256:260000$S5jnpMrV0drX8w5g$36fa6e1e5c336bf9430b0dc2ffad3c6cc21bb34bf0cd0f1be8fa1379bc6fff8b', 'admin@example.com', 'admin', true)
ON CONFLICT (username) DO NOTHING;

-- 插入初始版本号
INSERT INTO alembic_version (version_num)
VALUES ('add_missing_region_column')
ON CONFLICT (version_num) DO NOTHING;
"""

def create_engine_from_url(db_url):
    """创建数据库引擎"""
    return create_engine(db_url)

def create_tables(engine):
    """创建所有表"""
    try:
        # 使用with语句自动处理事务(commit/rollback)
        with engine.begin() as conn:
            conn.execute(text(CREATE_TABLES_SQL))
            logger.info("数据库表创建成功")
        return True
    except Exception as e:
        logger.error(f"创建数据库表时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    """主函数"""
    logger.info(f"开始初始化Render数据库...")
    
    try:
        # 创建数据库引擎
        engine = create_engine_from_url(RENDER_DB_URL)
        logger.info("成功连接到Render数据库")
        
        # 创建表
        if create_tables(engine):
            logger.info("所有表创建完成")
            return 0
        else:
            logger.error("表创建失败")
            return 1
    
    except Exception as e:
        logger.error(f"初始化数据库时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main()) 