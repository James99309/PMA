#!/usr/bin/env python
# -*- coding: utf-8 -*-

import psycopg2
from werkzeug.security import generate_password_hash

# 数据库连接配置
postgres_url = "postgresql://pma_user:pma_password@localhost:5432/pma_db_local"

def reset_admin_password():
    """重置admin用户密码为默认值"""
    # 连接PostgreSQL
    conn = psycopg2.connect(postgres_url)
    cursor = conn.cursor()
    
    # 默认密码
    default_password = "1505562299AaBb"
    
    # 生成密码哈希
    password_hash = generate_password_hash(default_password)
    
    try:
        # 更新admin用户密码
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE username = 'admin'",
            (password_hash,)
        )
        conn.commit()
        print(f"Admin用户密码已重置为默认值: {default_password}")
        
        # 验证更新
        cursor.execute(
            "SELECT id, username, substring(password_hash from 1 for 20) as pass_prefix FROM users WHERE username = 'admin'"
        )
        user = cursor.fetchone()
        if user:
            print(f"用户ID: {user[0]}, 用户名: {user[1]}, 密码哈希前缀: {user[2]}")
            print("密码重置成功！")
        else:
            print("警告: 找不到admin用户！")
    
    except Exception as e:
        conn.rollback()
        print(f"密码重置失败: {e}")
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    reset_admin_password() 
# -*- coding: utf-8 -*-

import psycopg2
from werkzeug.security import generate_password_hash

# 数据库连接配置
postgres_url = "postgresql://pma_user:pma_password@localhost:5432/pma_db_local"

def reset_admin_password():
    """重置admin用户密码为默认值"""
    # 连接PostgreSQL
    conn = psycopg2.connect(postgres_url)
    cursor = conn.cursor()
    
    # 默认密码
    default_password = "1505562299AaBb"
    
    # 生成密码哈希
    password_hash = generate_password_hash(default_password)
    
    try:
        # 更新admin用户密码
        cursor.execute(
            "UPDATE users SET password_hash = %s WHERE username = 'admin'",
            (password_hash,)
        )
        conn.commit()
        print(f"Admin用户密码已重置为默认值: {default_password}")
        
        # 验证更新
        cursor.execute(
            "SELECT id, username, substring(password_hash from 1 for 20) as pass_prefix FROM users WHERE username = 'admin'"
        )
        user = cursor.fetchone()
        if user:
            print(f"用户ID: {user[0]}, 用户名: {user[1]}, 密码哈希前缀: {user[2]}")
            print("密码重置成功！")
        else:
            print("警告: 找不到admin用户！")
    
    except Exception as e:
        conn.rollback()
        print(f"密码重置失败: {e}")
    
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    reset_admin_password() 