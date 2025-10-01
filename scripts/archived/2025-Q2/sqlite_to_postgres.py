#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SQLite到PostgreSQL数据库迁移工具
用于将SQLite数据库内容迁移到PostgreSQL数据库
"""

import os
import sys
import json
import datetime
import sqlite3
import psycopg2
from psycopg2.extras import Json
from flask_migrate import upgrade
from app import create_app, db


def serialize_datetime(obj):
    """序列化datetime对象为ISO格式字符串"""
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def sqlite_to_json(sqlite_db_path):
    """从SQLite导出数据到JSON格式"""
    print(f"从SQLite数据库导出数据: {sqlite_db_path}")
    
    # 连接SQLite数据库
    conn = sqlite3.connect(sqlite_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row['name'] for row in cursor.fetchall()]
    
    exported_data = {}
    
    for table in tables:
        print(f"导出表: {table}")
        cursor.execute(f"SELECT * FROM {table};")
        rows = cursor.fetchall()
        
        table_data = []
        for row in rows:
            # 将行转换为字典
            row_dict = {key: row[key] for key in row.keys()}
            table_data.append(row_dict)
        
        exported_data[table] = table_data
    
    conn.close()
    return exported_data


def json_to_postgres(data, postgres_uri):
    """将JSON数据导入到PostgreSQL数据库"""
    print(f"导入数据到PostgreSQL: {postgres_uri}")
    
    # 连接PostgreSQL数据库
    conn = psycopg2.connect(postgres_uri)
    cursor = conn.cursor()
    
    # 遍历所有表
    for table, rows in data.items():
        if not rows:
            print(f"表 {table} 没有数据，跳过")
            continue
        
        print(f"导入表: {table} ({len(rows)} 行)")
        
        # 清空目标表
        try:
            cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
            conn.commit()
        except psycopg2.Error as e:
            print(f"清空表 {table} 失败: {e}")
            conn.rollback()
            continue
        
        # 导入数据
        for row in rows:
            # 构建INSERT语句
            columns = row.keys()
            placeholders = ["%s"] * len(columns)
            values = [
                Json(v) if isinstance(v, (dict, list)) else v 
                for v in row.values()
            ]
            
            sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)});"
            
            try:
                cursor.execute(sql, values)
            except psycopg2.Error as e:
                print(f"插入数据到表 {table} 失败: {e}")
                conn.rollback()
                break
        
        conn.commit()
    
    conn.close()


def main():
    """主函数"""
    # 检查参数
    if len(sys.argv) < 2:
        print("用法: python sqlite_to_postgres.py <postgres_uri>")
        print("示例: python sqlite_to_postgres.py postgresql://username:password@localhost/pma_development")
        return 1
    
    postgres_uri = sys.argv[1]
    sqlite_db_path = os.path.join(os.path.dirname(__file__), 'app.db')
    
    print("步骤 1: 导出 SQLite 数据到 JSON")
    try:
        data = sqlite_to_json(sqlite_db_path)
    except Exception as e:
        print(f"导出 SQLite 数据失败: {e}")
        return 1
    
    # 保存JSON数据到文件（备份）
    with open('db_export.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, default=serialize_datetime, indent=2)
    
    print("步骤 2: 设置环境变量并应用迁移")
    os.environ['DATABASE_URL'] = postgres_uri
    
    # 创建Flask应用上下文并应用迁移
    app = create_app()
    with app.app_context():
        print("应用数据库迁移...")
        upgrade()
    
    print("步骤 3: 导入数据到 PostgreSQL")
    try:
        json_to_postgres(data, postgres_uri)
    except Exception as e:
        print(f"导入数据到 PostgreSQL 失败: {e}")
        return 1
    
    print("数据库迁移完成!")
    return 0


if __name__ == "__main__":
    sys.exit(main()) 
# -*- coding: utf-8 -*-

"""
SQLite到PostgreSQL数据库迁移工具
用于将SQLite数据库内容迁移到PostgreSQL数据库
"""

import os
import sys
import json
import datetime
import sqlite3
import psycopg2
from psycopg2.extras import Json
from flask_migrate import upgrade
from app import create_app, db


def serialize_datetime(obj):
    """序列化datetime对象为ISO格式字符串"""
    if isinstance(obj, (datetime.datetime, datetime.date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def sqlite_to_json(sqlite_db_path):
    """从SQLite导出数据到JSON格式"""
    print(f"从SQLite数据库导出数据: {sqlite_db_path}")
    
    # 连接SQLite数据库
    conn = sqlite3.connect(sqlite_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取所有表名
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row['name'] for row in cursor.fetchall()]
    
    exported_data = {}
    
    for table in tables:
        print(f"导出表: {table}")
        cursor.execute(f"SELECT * FROM {table};")
        rows = cursor.fetchall()
        
        table_data = []
        for row in rows:
            # 将行转换为字典
            row_dict = {key: row[key] for key in row.keys()}
            table_data.append(row_dict)
        
        exported_data[table] = table_data
    
    conn.close()
    return exported_data


def json_to_postgres(data, postgres_uri):
    """将JSON数据导入到PostgreSQL数据库"""
    print(f"导入数据到PostgreSQL: {postgres_uri}")
    
    # 连接PostgreSQL数据库
    conn = psycopg2.connect(postgres_uri)
    cursor = conn.cursor()
    
    # 遍历所有表
    for table, rows in data.items():
        if not rows:
            print(f"表 {table} 没有数据，跳过")
            continue
        
        print(f"导入表: {table} ({len(rows)} 行)")
        
        # 清空目标表
        try:
            cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE;")
            conn.commit()
        except psycopg2.Error as e:
            print(f"清空表 {table} 失败: {e}")
            conn.rollback()
            continue
        
        # 导入数据
        for row in rows:
            # 构建INSERT语句
            columns = row.keys()
            placeholders = ["%s"] * len(columns)
            values = [
                Json(v) if isinstance(v, (dict, list)) else v 
                for v in row.values()
            ]
            
            sql = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)});"
            
            try:
                cursor.execute(sql, values)
            except psycopg2.Error as e:
                print(f"插入数据到表 {table} 失败: {e}")
                conn.rollback()
                break
        
        conn.commit()
    
    conn.close()


def main():
    """主函数"""
    # 检查参数
    if len(sys.argv) < 2:
        print("用法: python sqlite_to_postgres.py <postgres_uri>")
        print("示例: python sqlite_to_postgres.py postgresql://username:password@localhost/pma_development")
        return 1
    
    postgres_uri = sys.argv[1]
    sqlite_db_path = os.path.join(os.path.dirname(__file__), 'app.db')
    
    print("步骤 1: 导出 SQLite 数据到 JSON")
    try:
        data = sqlite_to_json(sqlite_db_path)
    except Exception as e:
        print(f"导出 SQLite 数据失败: {e}")
        return 1
    
    # 保存JSON数据到文件（备份）
    with open('db_export.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, default=serialize_datetime, indent=2)
    
    print("步骤 2: 设置环境变量并应用迁移")
    os.environ['DATABASE_URL'] = postgres_uri
    
    # 创建Flask应用上下文并应用迁移
    app = create_app()
    with app.app_context():
        print("应用数据库迁移...")
        upgrade()
    
    print("步骤 3: 导入数据到 PostgreSQL")
    try:
        json_to_postgres(data, postgres_uri)
    except Exception as e:
        print(f"导入数据到 PostgreSQL 失败: {e}")
        return 1
    
    print("数据库迁移完成!")
    return 0


if __name__ == "__main__":
    sys.exit(main()) 