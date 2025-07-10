#!/usr/bin/env python3
"""
用户访问权限诊断脚本
可以用于诊断任何用户的访问权限问题
"""

import sqlite3
import os
import sys

def diagnose_user_access(db_path, username):
    """
    诊断指定用户的访问权限问题
    
    Args:
        db_path: 数据库文件路径
        username: 用户名
    """
    
    if not os.path.exists(db_path):
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"=== 诊断用户 '{username}' 的访问权限问题 ===")
        
        # 1. 查找用户基本信息
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ 未找到用户 '{username}'")
            return
        
        # 获取用户字段名
        cursor.execute("PRAGMA table_info(users)")
        user_columns = [col[1] for col in cursor.fetchall()]
        user_info = dict(zip(user_columns, user))
        
        print(f"\n✅ 用户基本信息:")
        print(f"  ID: {user_info.get('id')}")
        print(f"  用户名: {user_info.get('username')}")
        print(f"  真实姓名: {user_info.get('real_name')}")
        print(f"  角色: {user_info.get('role')}")
        print(f"  公司: {user_info.get('company_name')}")
        print(f"  部门: {user_info.get('department')}")
        print(f"  是否部门负责人: {user_info.get('is_department_manager')}")
        print(f"  是否激活: {user_info.get('is_active')}")
        
        # 2. 检查角色权限配置
        print(f"\n📋 角色权限配置检查:")
        cursor.execute("SELECT * FROM role_permissions WHERE role = ?", (user_info.get('role'),))
        role_permissions = cursor.fetchall()
        
        customer_perm = None
        project_perm = None
        role_perm_columns = []
        
        if role_permissions:
            # 获取角色权限字段名
            cursor.execute("PRAGMA table_info(role_permissions)")
            role_perm_columns = [col[1] for col in cursor.fetchall()]
            
            print(f"  角色 '{user_info.get('role')}' 的权限配置:")
            
            for perm_row in role_permissions:
                perm_info = dict(zip(role_perm_columns, perm_row))
                module = perm_info.get('module')
                print(f"    模块 {module}:")
                print(f"      查看: {perm_info.get('can_view')}")
                print(f"      创建: {perm_info.get('can_create')}")
                print(f"      编辑: {perm_info.get('can_edit')}")
                print(f"      删除: {perm_info.get('can_delete')}")
                print(f"      权限级别: {perm_info.get('permission_level')}")
                
                if module == 'customer':
                    customer_perm = perm_info
                elif module == 'project':
                    project_perm = perm_info
        else:
            print(f"  ❌ 未找到角色 '{user_info.get('role')}' 的权限配置")
        
        # 3. 检查个人权限配置
        print(f"\n👤 个人权限配置检查:")
        cursor.execute("SELECT * FROM permissions WHERE user_id = ?", (user_info.get('id'),))
        personal_permissions = cursor.fetchall()
        personal_perm_columns = []
        
        if personal_permissions:
            # 获取个人权限字段名
            cursor.execute("PRAGMA table_info(permissions)")
            personal_perm_columns = [col[1] for col in cursor.fetchall()]
            
            print(f"  用户的个人权限配置:")
            for perm_row in personal_permissions:
                perm_info = dict(zip(personal_perm_columns, perm_row))
                module = perm_info.get('module')
                print(f"    模块 {module}:")
                print(f"      查看: {perm_info.get('can_view')}")
                print(f"      创建: {perm_info.get('can_create')}")
                print(f"      编辑: {perm_info.get('can_edit')}")
                print(f"      删除: {perm_info.get('can_delete')}")
        else:
            print("  ℹ️  用户没有个人权限配置")
        
        # 4. 检查公司数据访问权限
        print(f"\n🏢 公司数据访问权限分析:")
        
        # 检查系统中的公司总数
        cursor.execute("SELECT COUNT(*) FROM companies WHERE is_deleted = 0")
        total_companies = cursor.fetchone()[0]
        print(f"  系统中有效公司总数: {total_companies}")
        
        # 检查用户自己创建的公司
        cursor.execute("SELECT COUNT(*) FROM companies WHERE owner_id = ? AND is_deleted = 0", (user_info.get('id'),))
        own_companies = cursor.fetchone()[0]
        print(f"  用户创建的公司数量: {own_companies}")
        
        # 检查同部门用户创建的公司
        if user_info.get('company_name') and user_info.get('department'):
            cursor.execute("""
                SELECT COUNT(*) FROM companies c
                JOIN users u ON c.owner_id = u.id
                WHERE u.company_name = ? AND u.department = ? AND c.is_deleted = 0
            """, (user_info.get('company_name'), user_info.get('department')))
            dept_companies = cursor.fetchone()[0]
            print(f"  同部门用户创建的公司数量: {dept_companies}")
        
        # 检查同公司用户创建的公司
        if user_info.get('company_name'):
            cursor.execute("""
                SELECT COUNT(*) FROM companies c
                JOIN users u ON c.owner_id = u.id
                WHERE u.company_name = ? AND c.is_deleted = 0
            """, (user_info.get('company_name'),))
            company_companies = cursor.fetchone()[0]
            print(f"  同公司用户创建的公司数量: {company_companies}")
        
        # 5. 检查归属关系
        print(f"\n🔗 归属关系检查:")
        cursor.execute("SELECT COUNT(*) FROM affiliations WHERE viewer_id = ?", (user_info.get('id'),))
        affiliations_count = cursor.fetchone()[0]
        print(f"  用户的归属关系数量: {affiliations_count}")
        
        if affiliations_count > 0:
            cursor.execute("""
                SELECT u.username, u.real_name, u.role 
                FROM affiliations a
                JOIN users u ON a.owner_id = u.id
                WHERE a.viewer_id = ?
            """, (user_info.get('id'),))
            affiliations = cursor.fetchall()
            print(f"  可查看的其他用户:")
            for aff in affiliations:
                print(f"    - {aff[0]} ({aff[1]}) - {aff[2]}")
        
        # 6. 问题诊断
        print(f"\n🔍 问题诊断:")
        
        issues = []
        
        # 检查customer模块查看权限
        has_customer_view = False
        if customer_perm and customer_perm.get('can_view'):
            has_customer_view = True
        
        # 检查个人权限是否补充了customer查看权限
        if personal_permissions:
            for perm_row in personal_permissions:
                perm_info = dict(zip(personal_perm_columns, perm_row))
                if perm_info.get('module') == 'customer' and perm_info.get('can_view'):
                    has_customer_view = True
                    break
        
        if not has_customer_view:
            issues.append("❌ 没有customer模块的查看权限")
        else:
            print("  ✅ 有customer模块的查看权限")
        
        # 检查project模块创建权限
        has_project_create = False
        if project_perm and project_perm.get('can_create'):
            has_project_create = True
        
        # 检查个人权限是否补充了project创建权限
        if personal_permissions:
            for perm_row in personal_permissions:
                perm_info = dict(zip(personal_perm_columns, perm_row))
                if perm_info.get('module') == 'project' and perm_info.get('can_create'):
                    has_project_create = True
                    break
        
        if not has_project_create:
            issues.append("❌ 没有project模块的创建权限")
        else:
            print("  ✅ 有project模块的创建权限")
        
        # 检查权限级别配置
        if customer_perm:
            permission_level = customer_perm.get('permission_level', 'personal')
            print(f"  ✅ customer模块权限级别: {permission_level}")
            
            if permission_level == 'personal':
                if own_companies == 0 and affiliations_count == 0:
                    issues.append("❌ 个人级权限但没有自己创建的公司且没有归属关系")
            elif permission_level == 'department':
                if not user_info.get('department'):
                    issues.append("❌ 部门级权限但用户没有设置部门")
            elif permission_level == 'company':
                if not user_info.get('company_name'):
                    issues.append("❌ 企业级权限但用户没有设置公司")
        
        # 检查基本信息完整性
        if not user_info.get('is_active'):
            issues.append("❌ 用户账号未激活")
        
        if not user_info.get('real_name'):
            issues.append("⚠️  用户没有设置真实姓名")
        
        # 7. 输出问题总结
        if issues:
            print(f"\n❌ 发现以下问题:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print(f"\n✅ 权限配置看起来正常")
        
        # 8. 修复建议
        print(f"\n🔧 修复建议:")
        
        if not has_customer_view:
            print("  1. 添加customer模块的查看权限到角色权限或个人权限")
        
        if not has_project_create:
            print("  2. 添加project模块的创建权限到角色权限或个人权限")
        
        if customer_perm and customer_perm.get('permission_level') == 'personal' and own_companies == 0 and affiliations_count == 0:
            print("  3. 为用户创建一些公司数据或配置归属关系")
        
        if customer_perm and customer_perm.get('permission_level') == 'department' and not user_info.get('department'):
            print("  4. 为用户设置部门信息")
        
        if customer_perm and customer_perm.get('permission_level') == 'company' and not user_info.get('company_name'):
            print("  5. 为用户设置公司信息")
        
        if not user_info.get('is_active'):
            print("  6. 激活用户账号")
        
        print(f"\n📝 SQL修复示例:")
        print(f"  -- 添加customer模块查看权限到角色权限")
        print(f"  INSERT OR REPLACE INTO role_permissions (role, module, can_view, can_create, can_edit, can_delete, permission_level)")
        print(f"  VALUES ('{user_info.get('role')}', 'customer', 1, 0, 0, 0, 'personal');")
        
        print(f"  -- 添加project模块创建权限到角色权限")
        print(f"  INSERT OR REPLACE INTO role_permissions (role, module, can_view, can_create, can_edit, can_delete, permission_level)")
        print(f"  VALUES ('{user_info.get('role')}', 'project', 1, 1, 1, 0, 'personal');")
        
        print(f"  -- 激活用户账号")
        print(f"  UPDATE users SET is_active = 1 WHERE id = {user_info.get('id')};")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 诊断过程中发生错误: {str(e)}")

def main():
    if len(sys.argv) != 2:
        print("使用方法: python3 diagnose_user_access.py <username>")
        print("例如: python3 diagnose_user_access.py gxh")
        return
    
    username = sys.argv[1]
    db_path = '/Users/nijie/Documents/PMA/pma_local.db'
    
    diagnose_user_access(db_path, username)

if __name__ == '__main__':
    main()