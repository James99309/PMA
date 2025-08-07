#!/usr/bin/env python3
"""
调试zhouyj账户权限问题
"""

import os
import sys
sys.path.append('.')

from app import create_app
from app.models.user import User, Affiliation
from app.models.project import Project
from app.utils.access_control import get_viewable_data
from flask import g
import psycopg2

def debug_cloud_zhouyj_permissions():
    """调试云端zhouyj账户权限配置"""
    
    # 云端数据库连接配置
    cloud_config = {
        'host': 'pqzviljbpfoqvyfulakl.supabase.co',
        'port': 5432,
        'user': 'postgres',
        'password': 'pma2024!@#',
        'database': 'postgres'
    }
    
    try:
        print("🌐 连接云端SP8D数据库...")
        conn = psycopg2.connect(**cloud_config)
        cursor = conn.cursor()
        
        # 1. 查看zhouyj基本信息
        print("\n" + "="*60)
        print("👤 zhouyj账户基本信息")
        print("="*60)
        
        cursor.execute("""
            SELECT 
                id, username, real_name, role, department, company_name,
                data_permission_level, is_active, created_at
            FROM users 
            WHERE username = 'zhouyj'
        """)
        
        user_info = cursor.fetchone()
        if not user_info:
            print("❌ 未找到zhouyj账户")
            return
            
        user_id, username, real_name, role, department, company_name, data_permission_level, is_active, created_at = user_info
        print(f"用户ID: {user_id}")
        print(f"用户名: {username}")
        print(f"真实姓名: {real_name}")
        print(f"角色: {role}")
        print(f"部门: {department}")
        print(f"公司: {company_name}")
        print(f"数据权限级别: {data_permission_level}")
        print(f"是否激活: {is_active}")
        print(f"创建时间: {created_at}")
        
        # 2. 查看数据归属关系
        print("\n" + "="*60)
        print("🔗 数据归属关系")
        print("="*60)
        
        cursor.execute("""
            SELECT 
                a.id,
                a.owner_id,
                o.username as owner_username,
                o.real_name as owner_name,
                a.created_at
            FROM affiliations a
            JOIN users o ON a.owner_id = o.id
            WHERE a.viewer_id = %s
            ORDER BY a.created_at DESC
        """, (user_id,))
        
        affiliations = cursor.fetchall()
        if affiliations:
            print("归属关系列表:")
            for aff in affiliations:
                aff_id, owner_id, owner_username, owner_name, aff_created_at = aff
                print(f"  - ID:{aff_id} 可查看 {owner_username}({owner_name}) 的数据，创建时间: {aff_created_at}")
        else:
            print("❌ 无数据归属关系")
            
        # 3. 查看同部门用户
        print("\n" + "="*60)
        print("👥 同部门用户")
        print("="*60)
        
        if department:
            cursor.execute("""
                SELECT id, username, real_name, role, data_permission_level
                FROM users 
                WHERE department = %s AND company_name = %s AND id != %s
                ORDER BY username
            """, (department, company_name, user_id))
            
            dept_users = cursor.fetchall()
            if dept_users:
                print(f"部门 '{department}' 中的其他用户:")
                for dept_user in dept_users:
                    dept_id, dept_username, dept_real_name, dept_role, dept_data_level = dept_user
                    print(f"  - {dept_username}({dept_real_name}) - {dept_role} - 数据级别:{dept_data_level}")
            else:
                print(f"部门 '{department}' 中没有其他用户")
        else:
            print("用户没有部门信息")
            
        # 4. 查看zhouyj能看到的项目数量
        print("\n" + "="*60)
        print("📊 项目可见性分析")
        print("="*60)
        
        # 查看zhouyj拥有的项目
        cursor.execute("""
            SELECT COUNT(*) FROM projects 
            WHERE owner_id = %s AND is_deleted = false
        """, (user_id,))
        own_projects = cursor.fetchone()[0]
        print(f"自己拥有的项目数量: {own_projects}")
        
        # 查看作为厂商销售经理的项目
        cursor.execute("""
            SELECT COUNT(*) FROM projects 
            WHERE vendor_sales_manager_id = %s AND is_deleted = false
        """, (user_id,))
        vendor_projects = cursor.fetchone()[0]
        print(f"作为厂商销售经理的项目数量: {vendor_projects}")
        
        # 查看同部门的项目（如果是部门级权限）
        if data_permission_level == 'department' and department:
            cursor.execute("""
                SELECT COUNT(*) FROM projects p
                JOIN users u ON p.owner_id = u.id
                WHERE u.department = %s AND u.company_name = %s 
                AND p.is_deleted = false
            """, (department, company_name))
            dept_projects = cursor.fetchone()[0]
            print(f"同部门项目总数: {dept_projects}")
        
        # 查看通过数据归属可见的项目
        if affiliations:
            owner_ids = [str(aff[1]) for aff in affiliations]
            cursor.execute(f"""
                SELECT COUNT(*) FROM projects 
                WHERE owner_id IN ({','.join(owner_ids)}) AND is_deleted = false
            """)
            affiliated_projects = cursor.fetchone()[0]
            print(f"通过数据归属可见的项目数量: {affiliated_projects}")
        
        # 5. 查看实际的项目数据示例
        print("\n" + "="*60)
        print("📋 项目数据示例 (前10条)")
        print("="*60)
        
        # 根据数据权限级别构建查询
        if data_permission_level == 'personal':
            # 个人级别：只能看自己的 + 归属关系的
            owner_conditions = [f"p.owner_id = {user_id}"]
            if affiliations:
                owner_ids = [str(aff[1]) for aff in affiliations]
                owner_conditions.append(f"p.owner_id IN ({','.join(owner_ids)})")
            
            where_clause = f"({' OR '.join(owner_conditions)})"
            
        elif data_permission_level == 'department' and department:
            # 部门级别：同部门的 + 归属关系的
            base_condition = f"(u.department = '{department}' AND u.company_name = '{company_name}')"
            
            if affiliations:
                owner_ids = [str(aff[1]) for aff in affiliations]
                where_clause = f"({base_condition} OR p.owner_id IN ({','.join(owner_ids)}))"
            else:
                where_clause = base_condition
        else:
            where_clause = f"p.owner_id = {user_id}"
        
        query = f"""
            SELECT 
                p.id,
                p.project_name,
                p.owner_id,
                u.username as owner_name,
                u.department as owner_dept,
                p.created_at
            FROM projects p
            JOIN users u ON p.owner_id = u.id
            WHERE {where_clause} AND p.is_deleted = false
            ORDER BY p.created_at DESC
            LIMIT 10
        """
        
        print(f"查询SQL: {query}")
        
        cursor.execute(query)
        visible_projects = cursor.fetchall()
        
        if visible_projects:
            print(f"可见项目列表 (前10条，共{len(visible_projects)}条):")
            for project in visible_projects:
                proj_id, proj_name, proj_owner_id, owner_name, owner_dept, proj_created = project
                visibility_reason = "自己的项目" if proj_owner_id == user_id else "其他可见项目"
                print(f"  - ID:{proj_id} {proj_name} (拥有者:{owner_name}/{owner_dept}) [{visibility_reason}]")
        else:
            print("❌ 没有可见的项目")
            
        # 6. 检查权限函数实现
        print("\n" + "="*60)
        print("🔍 权限逻辑分析")
        print("="*60)
        
        print(f"根据当前配置:")
        print(f"- 角色: {role}")
        print(f"- 数据权限级别: {data_permission_level}")
        print(f"- 部门: {department}")
        print(f"- 归属关系数量: {len(affiliations)}")
        
        expected_visibility = "仅自己的项目"
        if data_permission_level == 'department' and department:
            expected_visibility = f"同部门({department})的所有项目"
        if affiliations:
            expected_visibility += f" + {len(affiliations)}个归属用户的项目"
        
        print(f"预期可见范围: {expected_visibility}")
        
    except Exception as e:
        print(f"❌ 查询过程出错: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    debug_cloud_zhouyj_permissions()