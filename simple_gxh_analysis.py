#!/usr/bin/env python3
"""
简化的gxh用户权限分析脚本
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
        
        print("=== 分析gxh用户的权限配置和公司访问权限 ===")
        
        # 查找gxh用户
        cursor.execute("SELECT * FROM users WHERE username = 'gxh'")
        gxh_user = cursor.fetchone()
        
        if not gxh_user:
            print("❌ 未找到gxh用户")
            return
        
        # 获取用户字段名
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [col[1] for col in cursor.fetchall()]
        
        # 创建用户信息字典
        user_info = dict(zip(user_columns, gxh_user))
        
        print(f"\n用户信息:")
        print(f"  ID: {user_info.get('id')}")
        print(f"  用户名: {user_info.get('username')}")
        print(f"  真实姓名: {user_info.get('real_name')}")
        print(f"  角色: {user_info.get('role')}")
        print(f"  公司: {user_info.get('company_name')}")
        print(f"  部门: {user_info.get('department')}")
        print(f"  是否部门负责人: {user_info.get('is_department_manager')}")
        print(f"  是否激活: {user_info.get('is_active')}")
        
        # 检查角色权限配置
        print(f"\n=== 角色权限配置 ===")
        cursor.execute("SELECT * FROM role_permissions WHERE role = ?", (user_info.get('role'),))
        role_permissions = cursor.fetchall()
        
        if role_permissions:
            # 获取角色权限字段名
            cursor.execute("PRAGMA table_info(role_permissions)")
            role_perm_columns = [col[1] for col in cursor.fetchall()]
            
            print(f"角色 '{user_info.get('role')}' 的权限配置:")
            for perm_row in role_permissions:
                perm_info = dict(zip(role_perm_columns, perm_row))
                print(f"  模块: {perm_info.get('module')}")
                print(f"    查看: {perm_info.get('can_view')}")
                print(f"    创建: {perm_info.get('can_create')}")
                print(f"    编辑: {perm_info.get('can_edit')}")
                print(f"    删除: {perm_info.get('can_delete')}")
                print(f"    权限级别: {perm_info.get('permission_level')}")
                print(f"    权限说明: {perm_info.get('permission_level_description')}")
                print()
        else:
            print(f"❌ 未找到角色 '{user_info.get('role')}' 的权限配置")
        
        # 检查用户个人权限
        print(f"\n=== 用户个人权限 ===")
        cursor.execute("SELECT * FROM permissions WHERE user_id = ?", (user_info.get('id'),))
        personal_permissions = cursor.fetchall()
        
        if personal_permissions:
            # 获取个人权限字段名
            cursor.execute("PRAGMA table_info(permissions)")
            personal_perm_columns = [col[1] for col in cursor.fetchall()]
            
            print(f"用户的个人权限配置:")
            for perm_row in personal_permissions:
                perm_info = dict(zip(personal_perm_columns, perm_row))
                print(f"  模块: {perm_info.get('module')}")
                print(f"    查看: {perm_info.get('can_view')}")
                print(f"    创建: {perm_info.get('can_create')}")
                print(f"    编辑: {perm_info.get('can_edit')}")
                print(f"    删除: {perm_info.get('can_delete')}")
                print()
        else:
            print("用户没有个人权限配置")
        
        # 检查公司数据
        print(f"\n=== 公司数据分析 ===")
        cursor.execute("SELECT COUNT(*) FROM companies WHERE is_deleted = 0")
        total_companies = cursor.fetchone()[0]
        print(f"系统中总共有 {total_companies} 个有效公司")
        
        # 检查gxh用户创建的公司
        cursor.execute("SELECT COUNT(*) FROM companies WHERE owner_id = ? AND is_deleted = 0", (user_info.get('id'),))
        own_companies = cursor.fetchone()[0]
        print(f"gxh用户创建的公司数量: {own_companies}")
        
        # 检查同公司同部门的其他用户
        if user_info.get('company_name') and user_info.get('department'):
            cursor.execute("""
                SELECT COUNT(*) FROM users 
                WHERE company_name = ? AND department = ? AND id != ?
            """, (user_info.get('company_name'), user_info.get('department'), user_info.get('id')))
            dept_users = cursor.fetchone()[0]
            print(f"同公司同部门的其他用户数量: {dept_users}")
            
            # 检查同部门其他用户创建的公司
            cursor.execute("""
                SELECT COUNT(*) FROM companies c
                JOIN users u ON c.owner_id = u.id
                WHERE u.company_name = ? AND u.department = ? AND u.id != ? AND c.is_deleted = 0
            """, (user_info.get('company_name'), user_info.get('department'), user_info.get('id')))
            dept_companies = cursor.fetchone()[0]
            print(f"同部门其他用户创建的公司数量: {dept_companies}")
        
        # 检查归属关系
        cursor.execute("SELECT COUNT(*) FROM affiliations WHERE viewer_id = ?", (user_info.get('id'),))
        affiliations_count = cursor.fetchone()[0]
        print(f"gxh用户的归属关系数量: {affiliations_count}")
        
        # 检查sales_director角色的特殊权限
        print(f"\n=== 权限问题诊断 ===")
        user_role = user_info.get('role', '').strip()
        print(f"用户角色（去空格后）: '{user_role}'")
        
        # 检查customer模块的权限
        customer_role_perm = None
        for perm_row in role_permissions:
            perm_info = dict(zip(role_perm_columns, perm_row))
            if perm_info.get('module') == 'customer':
                customer_role_perm = perm_info
                break
        
        if customer_role_perm:
            print(f"customer模块角色权限:")
            print(f"  查看: {customer_role_perm.get('can_view')}")
            print(f"  创建: {customer_role_perm.get('can_create')}")
            print(f"  编辑: {customer_role_perm.get('can_edit')}")
            print(f"  删除: {customer_role_perm.get('can_delete')}")
            print(f"  权限级别: {customer_role_perm.get('permission_level')}")
            
            if not customer_role_perm.get('can_view'):
                print("❌ 问题发现：用户角色没有customer模块的查看权限")
        else:
            print("❌ 问题发现：未找到customer模块的角色权限配置")
        
        # 检查project模块的权限
        project_role_perm = None
        for perm_row in role_permissions:
            perm_info = dict(zip(role_perm_columns, perm_row))
            if perm_info.get('module') == 'project':
                project_role_perm = perm_info
                break
        
        if project_role_perm:
            print(f"project模块角色权限:")
            print(f"  查看: {project_role_perm.get('can_view')}")
            print(f"  创建: {project_role_perm.get('can_create')}")
            print(f"  编辑: {project_role_perm.get('can_edit')}")
            print(f"  删除: {project_role_perm.get('can_delete')}")
            print(f"  权限级别: {project_role_perm.get('permission_level')}")
            
            if not project_role_perm.get('can_create'):
                print("❌ 问题发现：用户角色没有project模块的创建权限")
        else:
            print("❌ 问题发现：未找到project模块的角色权限配置")
        
        print(f"\n=== 总结 ===")
        print(f"如果gxh用户在项目创建时看不到公司列表，可能的原因：")
        print(f"1. 没有customer模块的查看权限")
        print(f"2. 权限级别配置问题")
        print(f"3. 数据库中没有符合条件的公司记录")
        print(f"4. 公司记录的is_deleted字段为True")
        print(f"5. 归属关系配置问题")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 分析过程中发生错误: {str(e)}")

if __name__ == '__main__':
    main()