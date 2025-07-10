#!/usr/bin/env python3
"""
检查数据库中的用户列表
"""

import sqlite3
import os

# 数据库文件路径
db_path = '/Users/nijie/Documents/PMA/pma_local.db'

def main():
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("=== 检查数据库中的用户列表 ===")
        
        # 查看所有用户
        cursor.execute("SELECT id, username, real_name, role, company_name, department FROM users ORDER BY id")
        users = cursor.fetchall()
        
        if users:
            print(f"数据库中共有 {len(users)} 个用户:")
            for user in users:
                print(f"  ID: {user[0]}, 用户名: {user[1]}, 真实姓名: {user[2]}, 角色: {user[3]}, 公司: {user[4]}, 部门: {user[5]}")
        else:
            print("❌ 数据库中没有用户记录")
        
        # 查找类似gxh的用户名
        cursor.execute("SELECT id, username, real_name, role FROM users WHERE username LIKE '%gxh%' OR real_name LIKE '%gxh%'")
        gxh_users = cursor.fetchall()
        
        if gxh_users:
            print(f"\n找到包含'gxh'的用户:")
            for user in gxh_users:
                print(f"  ID: {user[0]}, 用户名: {user[1]}, 真实姓名: {user[2]}, 角色: {user[3]}")
        else:
            print("\n❌ 未找到包含'gxh'的用户")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查过程中发生错误: {str(e)}")

if __name__ == '__main__':
    main()