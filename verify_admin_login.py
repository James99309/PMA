#!/usr/bin/env python
# -*- coding: utf-8 -*-

import psycopg2
from werkzeug.security import check_password_hash

# 数据库连接配置
postgres_url = "postgresql://pma_user:pma_password@localhost:5432/pma_db_local"

def verify_admin_login():
    """验证admin用户登录凭据"""
    # 连接PostgreSQL
    conn = psycopg2.connect(postgres_url)
    cursor = conn.cursor()
    
    # 检查admin用户是否存在
    cursor.execute("SELECT id, username, password_hash FROM users WHERE username = 'admin'")
    user = cursor.fetchone()
    
    if not user:
        print("错误: admin用户不存在！")
        return
    
    # 进行密码验证
    default_password = "1505562299AaBb"
    user_id, username, password_hash = user
    
    if check_password_hash(password_hash, default_password):
        print(f"用户 {username} (ID: {user_id}) 使用默认密码验证成功！")
        print("可以使用以下凭据登录系统:")
        print(f"用户名: {username}")
        print(f"密码: {default_password}")
    else:
        print(f"用户 {username} (ID: {user_id}) 使用默认密码验证失败！")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    verify_admin_login() 
# -*- coding: utf-8 -*-

import psycopg2
from werkzeug.security import check_password_hash

# 数据库连接配置
postgres_url = "postgresql://pma_user:pma_password@localhost:5432/pma_db_local"

def verify_admin_login():
    """验证admin用户登录凭据"""
    # 连接PostgreSQL
    conn = psycopg2.connect(postgres_url)
    cursor = conn.cursor()
    
    # 检查admin用户是否存在
    cursor.execute("SELECT id, username, password_hash FROM users WHERE username = 'admin'")
    user = cursor.fetchone()
    
    if not user:
        print("错误: admin用户不存在！")
        return
    
    # 进行密码验证
    default_password = "1505562299AaBb"
    user_id, username, password_hash = user
    
    if check_password_hash(password_hash, default_password):
        print(f"用户 {username} (ID: {user_id}) 使用默认密码验证成功！")
        print("可以使用以下凭据登录系统:")
        print(f"用户名: {username}")
        print(f"密码: {default_password}")
    else:
        print(f"用户 {username} (ID: {user_id}) 使用默认密码验证失败！")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    verify_admin_login() 