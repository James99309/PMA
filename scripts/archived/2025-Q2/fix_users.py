#!/usr/bin/env python
# -*- coding: utf-8 -*-

import psycopg2
import sqlite3

# 数据库连接配置
sqlite_db_path = 'app.db'
postgres_url = "postgresql://pma_user:pma_password@localhost:5432/pma_db_local"

def fix_users():
    """修复用户表数据"""
    # 连接SQLite获取用户数据
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # 获取用户数据
    sqlite_cursor.execute("SELECT id, username, password_hash, email, phone, role, department, is_department_manager FROM users;")
    users = []
    for row in sqlite_cursor.fetchall():
        user = {
            'id': row['id'],
            'username': row['username'],
            'password_hash': row['password_hash'],
            'email': row['email'],
            'phone': row['phone'],
            'role': row['role'],
            'department': row['department'],
            'is_department_manager': bool(row['is_department_manager']) if row['is_department_manager'] is not None else False
        }
        users.append(user)
    
    sqlite_conn.close()
    
    # 连接PostgreSQL
    pg_conn = psycopg2.connect(postgres_url)
    pg_cursor = pg_conn.cursor()
    
    # 清空用户表
    pg_cursor.execute("TRUNCATE TABLE users CASCADE;")
    pg_conn.commit()
    
    # 检查用户表结构
    pg_cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users';")
    columns = [column[0] for column in pg_cursor.fetchall()]
    
    # 获取用户表的基本字段
    basic_fields = ['id', 'username', 'password_hash', 'email', 'phone', 'role', 'department', 'is_department_manager']
    
    # 导入用户数据
    for user in users:
        # 构建字段和值列表
        fields = []
        values = []
        for field in basic_fields:
            if field in columns:
                fields.append(field)
                values.append(user[field])
        
        # 构建INSERT语句
        placeholders = ['%s'] * len(fields)
        sql = f"INSERT INTO users ({', '.join(fields)}) VALUES ({', '.join(placeholders)});"
        
        # 执行插入
        try:
            pg_cursor.execute(sql, values)
            pg_conn.commit()
            print(f"成功导入用户: {user['username']} (ID: {user['id']})")
        except Exception as e:
            print(f"导入用户 {user['username']} 失败: {e}")
            pg_conn.rollback()
    
    pg_cursor.close()
    pg_conn.close()
    
    print("用户数据修复完成!")

if __name__ == "__main__":
    fix_users() 
# -*- coding: utf-8 -*-

import psycopg2
import sqlite3

# 数据库连接配置
sqlite_db_path = 'app.db'
postgres_url = "postgresql://pma_user:pma_password@localhost:5432/pma_db_local"

def fix_users():
    """修复用户表数据"""
    # 连接SQLite获取用户数据
    sqlite_conn = sqlite3.connect(sqlite_db_path)
    sqlite_conn.row_factory = sqlite3.Row
    sqlite_cursor = sqlite_conn.cursor()
    
    # 获取用户数据
    sqlite_cursor.execute("SELECT id, username, password_hash, email, phone, role, department, is_department_manager FROM users;")
    users = []
    for row in sqlite_cursor.fetchall():
        user = {
            'id': row['id'],
            'username': row['username'],
            'password_hash': row['password_hash'],
            'email': row['email'],
            'phone': row['phone'],
            'role': row['role'],
            'department': row['department'],
            'is_department_manager': bool(row['is_department_manager']) if row['is_department_manager'] is not None else False
        }
        users.append(user)
    
    sqlite_conn.close()
    
    # 连接PostgreSQL
    pg_conn = psycopg2.connect(postgres_url)
    pg_cursor = pg_conn.cursor()
    
    # 清空用户表
    pg_cursor.execute("TRUNCATE TABLE users CASCADE;")
    pg_conn.commit()
    
    # 检查用户表结构
    pg_cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'users';")
    columns = [column[0] for column in pg_cursor.fetchall()]
    
    # 获取用户表的基本字段
    basic_fields = ['id', 'username', 'password_hash', 'email', 'phone', 'role', 'department', 'is_department_manager']
    
    # 导入用户数据
    for user in users:
        # 构建字段和值列表
        fields = []
        values = []
        for field in basic_fields:
            if field in columns:
                fields.append(field)
                values.append(user[field])
        
        # 构建INSERT语句
        placeholders = ['%s'] * len(fields)
        sql = f"INSERT INTO users ({', '.join(fields)}) VALUES ({', '.join(placeholders)});"
        
        # 执行插入
        try:
            pg_cursor.execute(sql, values)
            pg_conn.commit()
            print(f"成功导入用户: {user['username']} (ID: {user['id']})")
        except Exception as e:
            print(f"导入用户 {user['username']} 失败: {e}")
            pg_conn.rollback()
    
    pg_cursor.close()
    pg_conn.close()
    
    print("用户数据修复完成!")

if __name__ == "__main__":
    fix_users() 