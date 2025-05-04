#!/usr/bin/env python
# -*- coding: utf-8 -*-

import psycopg2
import sqlite3

# 数据库连接配置
sqlite_db_path = 'app.db'
postgres_url = "postgresql://pma_user:pma_password@localhost:5432/pma_db_local"

def fix_product_code_fields():
    """修复产品代码字段表数据"""
    # 连接SQLite获取数据
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # 获取字段数据
    sqlite_cursor.execute("SELECT * FROM product_code_fields;")
    fields = []
    for row in sqlite_cursor.fetchall():
        field = {}
        for key in row.keys():
            if key in ['is_active', 'is_required', 'use_in_code']:
                field[key] = bool(row[key]) if row[key] is not None else False
            else:
                field[key] = row[key]
        fields.append(field)
    
    sqlite_conn.close()
    
    # 连接PostgreSQL
    pg_conn = psycopg2.connect(postgres_url)
    pg_cursor = pg_conn.cursor()
    
    # 清空表
    pg_cursor.execute("TRUNCATE TABLE product_code_fields CASCADE;")
    pg_conn.commit()
    
    # 检查表结构
    pg_cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'product_code_fields';")
    columns = [column[0] for column in pg_cursor.fetchall()]
    
    # 导入数据
    for field in fields:
        # 构建字段和值列表
        field_names = []
        values = []
        
        for key, value in field.items():
            if key in columns:
                field_names.append(key)
                values.append(value)
        
        # 构建INSERT语句
        placeholders = ['%s'] * len(field_names)
        sql = f"INSERT INTO product_code_fields ({', '.join(field_names)}) VALUES ({', '.join(placeholders)});"
        
        # 执行插入
        try:
            pg_cursor.execute(sql, values)
            pg_conn.commit()
            print(f"成功导入产品代码字段: ID={field.get('id')}, 名称={field.get('name')}")
        except Exception as e:
            print(f"导入产品代码字段失败 ID={field.get('id')}: {e}")
            pg_conn.rollback()
    
    pg_cursor.close()
    pg_conn.close()
    
    print("产品代码字段数据修复完成!")

if __name__ == "__main__":
    fix_product_code_fields() 
# -*- coding: utf-8 -*-

import psycopg2
import sqlite3

# 数据库连接配置
sqlite_db_path = 'app.db'
postgres_url = "postgresql://pma_user:pma_password@localhost:5432/pma_db_local"

def fix_product_code_fields():
    """修复产品代码字段表数据"""
    # 连接SQLite获取数据
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # 获取字段数据
    sqlite_cursor.execute("SELECT * FROM product_code_fields;")
    fields = []
    for row in sqlite_cursor.fetchall():
        field = {}
        for key in row.keys():
            if key in ['is_active', 'is_required', 'use_in_code']:
                field[key] = bool(row[key]) if row[key] is not None else False
            else:
                field[key] = row[key]
        fields.append(field)
    
    sqlite_conn.close()
    
    # 连接PostgreSQL
    pg_conn = psycopg2.connect(postgres_url)
    pg_cursor = pg_conn.cursor()
    
    # 清空表
    pg_cursor.execute("TRUNCATE TABLE product_code_fields CASCADE;")
    pg_conn.commit()
    
    # 检查表结构
    pg_cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'product_code_fields';")
    columns = [column[0] for column in pg_cursor.fetchall()]
    
    # 导入数据
    for field in fields:
        # 构建字段和值列表
        field_names = []
        values = []
        
        for key, value in field.items():
            if key in columns:
                field_names.append(key)
                values.append(value)
        
        # 构建INSERT语句
        placeholders = ['%s'] * len(field_names)
        sql = f"INSERT INTO product_code_fields ({', '.join(field_names)}) VALUES ({', '.join(placeholders)});"
        
        # 执行插入
        try:
            pg_cursor.execute(sql, values)
            pg_conn.commit()
            print(f"成功导入产品代码字段: ID={field.get('id')}, 名称={field.get('name')}")
        except Exception as e:
            print(f"导入产品代码字段失败 ID={field.get('id')}: {e}")
            pg_conn.rollback()
    
    pg_cursor.close()
    pg_conn.close()
    
    print("产品代码字段数据修复完成!")

if __name__ == "__main__":
    fix_product_code_fields() 