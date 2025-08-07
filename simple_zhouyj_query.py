#!/usr/bin/env python3
"""
简化版 zhouyj 权限查询
"""

import psycopg2
import sys

def quick_query():
    """快速查询zhouyj信息"""
    
    cloud_config = {
        'host': 'pqzviljbpfoqvyfulakl.supabase.co',
        'port': 5432,
        'user': 'postgres',
        'password': 'pma2024!@#',
        'database': 'postgres',
        'connect_timeout': 10
    }
    
    try:
        print("连接云端数据库...")
        conn = psycopg2.connect(**cloud_config)
        cursor = conn.cursor()
        
        # 基本信息
        print("查询zhouyj基本信息...")
        cursor.execute("""
            SELECT id, username, real_name, role, department, data_permission_level, is_active
            FROM users WHERE username = 'zhouyj'
        """)
        
        user = cursor.fetchone()
        if user:
            user_id, username, real_name, role, department, data_permission_level, is_active = user
            print(f"用户ID: {user_id}")
            print(f"角色: {role}")
            print(f"部门: {department}")
            print(f"数据权限级别: {data_permission_level}")
            print(f"是否激活: {is_active}")
            
            # 检查归属关系
            print(f"\n查询归属关系...")
            cursor.execute("""
                SELECT COUNT(*) FROM affiliations WHERE viewer_id = %s
            """, (user_id,))
            aff_count = cursor.fetchone()[0]
            print(f"归属关系数量: {aff_count}")
            
            # 检查项目可见性
            print(f"\n项目可见性:")
            cursor.execute("SELECT COUNT(*) FROM projects WHERE owner_id = %s AND is_deleted = false", (user_id,))
            own_projects = cursor.fetchone()[0]
            print(f"自己的项目: {own_projects}")
            
            # 总项目数
            cursor.execute("SELECT COUNT(*) FROM projects WHERE is_deleted = false")
            total_projects = cursor.fetchone()[0]
            print(f"系统总项目数: {total_projects}")
            
        else:
            print("未找到zhouyj用户")
            
    except Exception as e:
        print(f"错误: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    quick_query()