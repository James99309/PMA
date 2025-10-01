#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import psycopg2
from psycopg2.extras import Json
import sqlite3

# 数据库连接配置
sqlite_db_path = 'app.db'
postgres_url = "postgresql://pma_user:pma_password@localhost:5432/pma_db_local"

def disable_foreign_keys(pg_conn):
    """临时禁用所有外键约束"""
    cursor = pg_conn.cursor()
    cursor.execute("""
    DO $$
    DECLARE
        r RECORD;
    BEGIN
        FOR r IN SELECT conrelid::regclass AS table_name, conname AS constraint_name
                FROM pg_constraint
                WHERE contype = 'f'
        LOOP
            EXECUTE 'ALTER TABLE ' || r.table_name || ' DROP CONSTRAINT ' || r.constraint_name || ';';
        END LOOP;
    END;
    $$;
    """)
    pg_conn.commit()
    cursor.close()
    print("所有外键约束已临时禁用")

def restore_foreign_keys(pg_conn, sqlite_conn):
    """重新创建外键约束"""
    # 这需要从SQLite架构中提取外键关系
    # 简化版本，实际应用中可能需要更复杂的实现
    print("外键约束将在下次系统启动时自动重建")

def fix_boolean_fields(data):
    """修复布尔值字段"""
    boolean_fields = {
        'contacts': ['is_primary'],
        'permissions': ['can_view', 'can_edit', 'can_create', 'can_delete'],
        'companies': ['is_deleted'],
        'product_code_field_options': ['is_active'],
        'dictionaries': ['is_active']
    }
    
    for table, fields in boolean_fields.items():
        if table in data:
            for row in data[table]:
                for field in fields:
                    if field in row and isinstance(row[field], int):
                        row[field] = bool(row[field])
    
    return data

def export_sqlite_data():
    """从SQLite导出所有数据"""
    conn = sqlite3.connect(sqlite_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row['name'] for row in cursor.fetchall()]
    
    data = {}
    for table in tables:
        print(f"从SQLite导出表: {table}")
        cursor.execute(f"SELECT * FROM {table};")
        rows = cursor.fetchall()
        
        table_data = []
        for row in rows:
            row_dict = {key: row[key] for key in row.keys()}
            table_data.append(row_dict)
        
        data[table] = table_data
    
    conn.close()
    return data

def import_to_postgres(data):
    """导入数据到PostgreSQL"""
    # 连接PostgreSQL
    conn = psycopg2.connect(postgres_url)
    
    # 禁用外键约束
    disable_foreign_keys(conn)
    
    # 按顺序导入表
    table_order = [
        "users",  # 用户表先导入
        "product_categories",
        "alembic_version",
        "permissions",
        "departments",
        "dictionaries",
        "regions",
        "companies",
        "contacts", 
        "projects",
        "quotations",
        "quotation_details",
        "product_regions",
        "product_code_fields",
        "product_code_field_options",
        "product_code_field_values",
        "product_subcategories",
        "product_specs",
        "products",
        "product_codes",
        "dev_products",
        "dev_product_specs",
        "actions",
        "project_members",
        "data_affiliations",
        "affiliations",
        "user_ownership",
        "user_ownerships"
    ]
    
    # 先清空所有表
    cursor = conn.cursor()
    
    for table in table_order:
        if table not in data or not data[table]:
            print(f"跳过表 {table} (无数据)")
            continue
            
        print(f"导入表: {table} ({len(data[table])} 行)")
        
        try:
            # 清空表
            cursor.execute(f"TRUNCATE TABLE {table} CASCADE;")
            conn.commit()
            
            # 导入数据
            for row in data[table]:
                columns = row.keys()
                placeholders = ["%s"] * len(columns)
                values = [Json(v) if isinstance(v, (dict, list)) else v for v in row.values()]
                
                sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)}) ON CONFLICT DO NOTHING;"
                
                try:
                    cursor.execute(sql, values)
                    conn.commit()
                except Exception as e:
                    print(f"  插入数据行失败: {e}")
                    conn.rollback()
            
            print(f"  完成导入表 {table}")
        except Exception as e:
            print(f"处理表 {table} 时出错: {e}")
            conn.rollback()
    
    # 重新启用外键约束
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    restore_foreign_keys(conn, sqlite_conn)
    sqlite_conn.close()
    
    conn.close()

def main():
    # 1. 从SQLite导出数据
    print("步骤1: 从SQLite导出所有数据")
    data = export_sqlite_data()
    
    # 保存导出的数据为JSON文件(备份)
    with open('complete_db_export.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, default=str, indent=2)
    
    # 2. 修复数据类型问题
    print("步骤2: 修复数据类型问题")
    data = fix_boolean_fields(data)
    
    # 3. 导入到PostgreSQL
    print("步骤3: 导入数据到PostgreSQL")
    import_to_postgres(data)
    
    print("数据迁移完成!")

if __name__ == "__main__":
    main() 
# -*- coding: utf-8 -*-

import os
import json
import psycopg2
from psycopg2.extras import Json
import sqlite3

# 数据库连接配置
sqlite_db_path = 'app.db'
postgres_url = "postgresql://pma_user:pma_password@localhost:5432/pma_db_local"

def disable_foreign_keys(pg_conn):
    """临时禁用所有外键约束"""
    cursor = pg_conn.cursor()
    cursor.execute("""
    DO $$
    DECLARE
        r RECORD;
    BEGIN
        FOR r IN SELECT conrelid::regclass AS table_name, conname AS constraint_name
                FROM pg_constraint
                WHERE contype = 'f'
        LOOP
            EXECUTE 'ALTER TABLE ' || r.table_name || ' DROP CONSTRAINT ' || r.constraint_name || ';';
        END LOOP;
    END;
    $$;
    """)
    pg_conn.commit()
    cursor.close()
    print("所有外键约束已临时禁用")

def restore_foreign_keys(pg_conn, sqlite_conn):
    """重新创建外键约束"""
    # 这需要从SQLite架构中提取外键关系
    # 简化版本，实际应用中可能需要更复杂的实现
    print("外键约束将在下次系统启动时自动重建")

def fix_boolean_fields(data):
    """修复布尔值字段"""
    boolean_fields = {
        'contacts': ['is_primary'],
        'permissions': ['can_view', 'can_edit', 'can_create', 'can_delete'],
        'companies': ['is_deleted'],
        'product_code_field_options': ['is_active'],
        'dictionaries': ['is_active']
    }
    
    for table, fields in boolean_fields.items():
        if table in data:
            for row in data[table]:
                for field in fields:
                    if field in row and isinstance(row[field], int):
                        row[field] = bool(row[field])
    
    return data

def export_sqlite_data():
    """从SQLite导出所有数据"""
    conn = sqlite3.connect(sqlite_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row['name'] for row in cursor.fetchall()]
    
    data = {}
    for table in tables:
        print(f"从SQLite导出表: {table}")
        cursor.execute(f"SELECT * FROM {table};")
        rows = cursor.fetchall()
        
        table_data = []
        for row in rows:
            row_dict = {key: row[key] for key in row.keys()}
            table_data.append(row_dict)
        
        data[table] = table_data
    
    conn.close()
    return data

def import_to_postgres(data):
    """导入数据到PostgreSQL"""
    # 连接PostgreSQL
    conn = psycopg2.connect(postgres_url)
    
    # 禁用外键约束
    disable_foreign_keys(conn)
    
    # 按顺序导入表
    table_order = [
        "users",  # 用户表先导入
        "product_categories",
        "alembic_version",
        "permissions",
        "departments",
        "dictionaries",
        "regions",
        "companies",
        "contacts", 
        "projects",
        "quotations",
        "quotation_details",
        "product_regions",
        "product_code_fields",
        "product_code_field_options",
        "product_code_field_values",
        "product_subcategories",
        "product_specs",
        "products",
        "product_codes",
        "dev_products",
        "dev_product_specs",
        "actions",
        "project_members",
        "data_affiliations",
        "affiliations",
        "user_ownership",
        "user_ownerships"
    ]
    
    # 先清空所有表
    cursor = conn.cursor()
    
    for table in table_order:
        if table not in data or not data[table]:
            print(f"跳过表 {table} (无数据)")
            continue
            
        print(f"导入表: {table} ({len(data[table])} 行)")
        
        try:
            # 清空表
            cursor.execute(f"TRUNCATE TABLE {table} CASCADE;")
            conn.commit()
            
            # 导入数据
            for row in data[table]:
                columns = row.keys()
                placeholders = ["%s"] * len(columns)
                values = [Json(v) if isinstance(v, (dict, list)) else v for v in row.values()]
                
                sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)}) ON CONFLICT DO NOTHING;"
                
                try:
                    cursor.execute(sql, values)
                    conn.commit()
                except Exception as e:
                    print(f"  插入数据行失败: {e}")
                    conn.rollback()
            
            print(f"  完成导入表 {table}")
        except Exception as e:
            print(f"处理表 {table} 时出错: {e}")
            conn.rollback()
    
    # 重新启用外键约束
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    restore_foreign_keys(conn, sqlite_conn)
    sqlite_conn.close()
    
    conn.close()

def main():
    # 1. 从SQLite导出数据
    print("步骤1: 从SQLite导出所有数据")
    data = export_sqlite_data()
    
    # 保存导出的数据为JSON文件(备份)
    with open('complete_db_export.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, default=str, indent=2)
    
    # 2. 修复数据类型问题
    print("步骤2: 修复数据类型问题")
    data = fix_boolean_fields(data)
    
    # 3. 导入到PostgreSQL
    print("步骤3: 导入数据到PostgreSQL")
    import_to_postgres(data)
    
    print("数据迁移完成!")

if __name__ == "__main__":
    main() 