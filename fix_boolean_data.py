#!/usr/bin/env python
# -*- coding: utf-8 -*-

import psycopg2

# 数据库连接配置
postgres_url = "postgresql://pma_user:pma_password@localhost:5432/pma_db_local"

def fix_boolean_data():
    """修复布尔值字段数据"""
    conn = psycopg2.connect(postgres_url)
    cursor = conn.cursor()
    
    # 修复布尔值字段
    boolean_fields = [
        ("product_code_fields", "is_active", "is_active = 1"),
        ("product_code_fields", "is_required", "is_required = 1"),
        ("product_code_fields", "use_in_code", "use_in_code = 1"),
        ("contacts", "is_primary", "is_primary = 1"),
        ("permissions", "can_view", "can_view = 1"),
        ("permissions", "can_edit", "can_edit = 1"),
        ("permissions", "can_create", "can_create = 1"),
        ("permissions", "can_delete", "can_delete = 1"),
        ("companies", "is_deleted", "is_deleted = 1"),
        ("product_code_field_options", "is_active", "is_active = 1"),
        ("dictionaries", "is_active", "is_active = 1")
    ]
    
    for table, field, condition in boolean_fields:
        try:
            # 将整型1转为布尔型true
            sql = f"UPDATE {table} SET {field} = true WHERE {condition};"
            cursor.execute(sql)
            
            # 将整型0转为布尔型false
            sql = f"UPDATE {table} SET {field} = false WHERE {field} = 0;"
            cursor.execute(sql)
            
            conn.commit()
            print(f"修复表 {table} 的字段 {field} 成功")
        except Exception as e:
            print(f"修复表 {table} 的字段 {field} 失败: {e}")
            conn.rollback()
    
    cursor.close()
    conn.close()
    
    print("布尔值字段修复完成!")

if __name__ == "__main__":
    fix_boolean_data() 
# -*- coding: utf-8 -*-

import psycopg2

# 数据库连接配置
postgres_url = "postgresql://pma_user:pma_password@localhost:5432/pma_db_local"

def fix_boolean_data():
    """修复布尔值字段数据"""
    conn = psycopg2.connect(postgres_url)
    cursor = conn.cursor()
    
    # 修复布尔值字段
    boolean_fields = [
        ("product_code_fields", "is_active", "is_active = 1"),
        ("product_code_fields", "is_required", "is_required = 1"),
        ("product_code_fields", "use_in_code", "use_in_code = 1"),
        ("contacts", "is_primary", "is_primary = 1"),
        ("permissions", "can_view", "can_view = 1"),
        ("permissions", "can_edit", "can_edit = 1"),
        ("permissions", "can_create", "can_create = 1"),
        ("permissions", "can_delete", "can_delete = 1"),
        ("companies", "is_deleted", "is_deleted = 1"),
        ("product_code_field_options", "is_active", "is_active = 1"),
        ("dictionaries", "is_active", "is_active = 1")
    ]
    
    for table, field, condition in boolean_fields:
        try:
            # 将整型1转为布尔型true
            sql = f"UPDATE {table} SET {field} = true WHERE {condition};"
            cursor.execute(sql)
            
            # 将整型0转为布尔型false
            sql = f"UPDATE {table} SET {field} = false WHERE {field} = 0;"
            cursor.execute(sql)
            
            conn.commit()
            print(f"修复表 {table} 的字段 {field} 成功")
        except Exception as e:
            print(f"修复表 {table} 的字段 {field} 失败: {e}")
            conn.rollback()
    
    cursor.close()
    conn.close()
    
    print("布尔值字段修复完成!")

if __name__ == "__main__":
    fix_boolean_data() 