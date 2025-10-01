#!/usr/bin/env python
# -*- coding: utf-8 -*-

import psycopg2

# 数据库连接配置
postgres_url = "postgresql://pma_user:pma_password@localhost:5432/pma_db_local"

def fix_schema():
    """修复数据库架构问题"""
    conn = psycopg2.connect(postgres_url)
    cursor = conn.cursor()
    
    # 检查并修复表结构
    schema_fixes = [
        # 添加缺失的列
        "ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS company_id INTEGER",
        "ALTER TABLE IF EXISTS product_code_fields ADD COLUMN IF NOT EXISTS name_en VARCHAR(255)",
        "ALTER TABLE IF EXISTS product_subcategories ADD COLUMN IF NOT EXISTS position INTEGER",
        
        # 修复列类型
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'contacts' AND column_name = 'is_primary' AND data_type = 'integer'
            ) THEN
                ALTER TABLE contacts ALTER COLUMN is_primary TYPE boolean USING (is_primary::boolean);
            END IF;
        END
        $$;
        """,
        
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'permissions' AND column_name = 'can_view' AND data_type = 'integer'
            ) THEN
                ALTER TABLE permissions ALTER COLUMN can_view TYPE boolean USING (can_view::boolean);
                ALTER TABLE permissions ALTER COLUMN can_edit TYPE boolean USING (can_edit::boolean);
                ALTER TABLE permissions ALTER COLUMN can_create TYPE boolean USING (can_create::boolean);
                ALTER TABLE permissions ALTER COLUMN can_delete TYPE boolean USING (can_delete::boolean);
            END IF;
        END
        $$;
        """,
        
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'companies' AND column_name = 'is_deleted' AND data_type = 'integer'
            ) THEN
                ALTER TABLE companies ALTER COLUMN is_deleted TYPE boolean USING (is_deleted::boolean);
            END IF;
        END
        $$;
        """,
        
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'product_code_field_options' AND column_name = 'is_active' AND data_type = 'integer'
            ) THEN
                ALTER TABLE product_code_field_options ALTER COLUMN is_active TYPE boolean USING (is_active::boolean);
            END IF;
        END
        $$;
        """,
        
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'dictionaries' AND column_name = 'is_active' AND data_type = 'integer'
            ) THEN
                ALTER TABLE dictionaries ALTER COLUMN is_active TYPE boolean USING (is_active::boolean);
            END IF;
        END
        $$;
        """
    ]
    
    for sql in schema_fixes:
        try:
            cursor.execute(sql)
            conn.commit()
            print(f"执行SQL成功: {sql[:50]}...")
        except Exception as e:
            print(f"执行SQL失败: {sql[:50]}... - 错误: {e}")
            conn.rollback()
    
    cursor.close()
    conn.close()
    
    print("数据库架构修复完成!")

if __name__ == "__main__":
    fix_schema() 
# -*- coding: utf-8 -*-

import psycopg2

# 数据库连接配置
postgres_url = "postgresql://pma_user:pma_password@localhost:5432/pma_db_local"

def fix_schema():
    """修复数据库架构问题"""
    conn = psycopg2.connect(postgres_url)
    cursor = conn.cursor()
    
    # 检查并修复表结构
    schema_fixes = [
        # 添加缺失的列
        "ALTER TABLE IF EXISTS users ADD COLUMN IF NOT EXISTS company_id INTEGER",
        "ALTER TABLE IF EXISTS product_code_fields ADD COLUMN IF NOT EXISTS name_en VARCHAR(255)",
        "ALTER TABLE IF EXISTS product_subcategories ADD COLUMN IF NOT EXISTS position INTEGER",
        
        # 修复列类型
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'contacts' AND column_name = 'is_primary' AND data_type = 'integer'
            ) THEN
                ALTER TABLE contacts ALTER COLUMN is_primary TYPE boolean USING (is_primary::boolean);
            END IF;
        END
        $$;
        """,
        
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'permissions' AND column_name = 'can_view' AND data_type = 'integer'
            ) THEN
                ALTER TABLE permissions ALTER COLUMN can_view TYPE boolean USING (can_view::boolean);
                ALTER TABLE permissions ALTER COLUMN can_edit TYPE boolean USING (can_edit::boolean);
                ALTER TABLE permissions ALTER COLUMN can_create TYPE boolean USING (can_create::boolean);
                ALTER TABLE permissions ALTER COLUMN can_delete TYPE boolean USING (can_delete::boolean);
            END IF;
        END
        $$;
        """,
        
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'companies' AND column_name = 'is_deleted' AND data_type = 'integer'
            ) THEN
                ALTER TABLE companies ALTER COLUMN is_deleted TYPE boolean USING (is_deleted::boolean);
            END IF;
        END
        $$;
        """,
        
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'product_code_field_options' AND column_name = 'is_active' AND data_type = 'integer'
            ) THEN
                ALTER TABLE product_code_field_options ALTER COLUMN is_active TYPE boolean USING (is_active::boolean);
            END IF;
        END
        $$;
        """,
        
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_name = 'dictionaries' AND column_name = 'is_active' AND data_type = 'integer'
            ) THEN
                ALTER TABLE dictionaries ALTER COLUMN is_active TYPE boolean USING (is_active::boolean);
            END IF;
        END
        $$;
        """
    ]
    
    for sql in schema_fixes:
        try:
            cursor.execute(sql)
            conn.commit()
            print(f"执行SQL成功: {sql[:50]}...")
        except Exception as e:
            print(f"执行SQL失败: {sql[:50]}... - 错误: {e}")
            conn.rollback()
    
    cursor.close()
    conn.close()
    
    print("数据库架构修复完成!")

if __name__ == "__main__":
    fix_schema() 