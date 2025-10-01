#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查云端数据库的admin用户信息
"""

import psycopg2
from urllib.parse import urlparse

# 云端数据库URL
CLOUD_DB_URL = 'postgresql://pma_db_ovs_user:oUKdxwqXDvCrgkg3fkZ33axXgDF21D51@dpg-d170laodl3ps739trgp0-a.singapore-postgres.render.com/pma_db_ovs'

def main():
    try:
        print("🔍 检查云端数据库信息...")
        conn = psycopg2.connect(CLOUD_DB_URL)
        cursor = conn.cursor()
        
        # 检查数据库名称
        cursor.execute('SELECT current_database();')
        db_name = cursor.fetchone()[0]
        print(f'📊 当前数据库名称: {db_name}')
        
        # 解析URL获取连接信息
        parsed = urlparse(CLOUD_DB_URL)
        print(f'📊 数据库主机: {parsed.hostname}')
        print(f'📊 数据库用户: {parsed.username}')
        print(f'📊 数据库路径: {parsed.path}')
        
        # 检查users表是否存在
        cursor.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_name = 'users'
        """)
        users_table_exists = cursor.fetchone()[0] > 0
        print(f'📊 users表存在: {users_table_exists}')
        
        if users_table_exists:
            # 检查users表结构
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users'
                ORDER BY ordinal_position
            """)
            columns = cursor.fetchall()
            print(f'📊 users表字段: {len(columns)}个')
            for col_name, col_type in columns:
                print(f'   - {col_name}: {col_type}')
            
            # 检查所有用户
            cursor.execute("""
                SELECT id, username, email, password_hash, is_active, role, real_name 
                FROM users 
                ORDER BY id
            """)
            all_users = cursor.fetchall()
            print(f'\n👥 所有用户: {len(all_users)}个')
            
            for user in all_users:
                print(f'  ID: {user[0]}, 用户名: {user[1]}, 邮箱: {user[2]}')
                print(f'  真实姓名: {user[6] if user[6] else "无"}')
                print(f'  密码哈希: {user[3][:50] if user[3] else "无"}...')
                print(f'  激活状态: {user[4]}, 角色: {user[5]}')
                print('---')
            
            # 特别检查admin用户
            cursor.execute("""
                SELECT id, username, email, password_hash, is_active, role, real_name 
                FROM users 
                WHERE username = 'admin' OR email LIKE '%admin%' OR role = 'admin'
            """)
            admin_users = cursor.fetchall()
            print(f'\n🔑 管理员用户: {len(admin_users)}个')
            
            for user in admin_users:
                print(f'  ID: {user[0]}, 用户名: {user[1]}, 邮箱: {user[2]}')
                print(f'  真实姓名: {user[6] if user[6] else "无"}')
                print(f'  密码哈希: {user[3][:50] if user[3] else "无"}...')
                print(f'  激活状态: {user[4]}, 角色: {user[5]}')
                print('---')
        else:
            print('❌ users表不存在，可能需要先创建用户数据')
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f'❌ 连接失败: {e}')

if __name__ == "__main__":
    main() 