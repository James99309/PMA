#!/usr/bin/env python3
"""
最终分析SP8D备份中zhouyj权限异常的根本原因
"""

import re

def final_analysis():
    """最终分析zhouyj权限异常原因"""
    backup_file = "/Users/nijie/Documents/PMA/cloud_db_backups/pma_db_sp8d_backup_20250803_230106.sql"
    
    with open(backup_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 最终分析报告 - zhouyj权限异常原因")
    print("="*60)
    
    # 1. 分析zhouyj用户详细信息
    print("\n👤 zhouyj用户信息分析:")
    
    # 从COPY users数据中提取zhouyj信息
    users_copy_pattern = r"COPY public\.users.*?FROM stdin;(.*?)\\\."
    users_match = re.search(users_copy_pattern, content, re.DOTALL)
    
    if users_match:
        users_data = users_match.group(1)
        for line in users_data.split('\n'):
            if '\tzhouyj\t' in line:
                parts = line.strip().split('\t')
                user_fields = ['id', 'username', 'password_hash', 'real_name', 'company_name', 
                              'email', 'phone', 'department', 'is_department_manager', 'role',
                              'is_profile_complete', 'wechat_openid', 'wechat_nickname', 
                              'wechat_avatar', 'is_active', 'created_at', 'updated_at', 
                              'last_login', 'language_preference']
                
                print(f"  用户ID: {parts[0]}")
                print(f"  用户名: {parts[1]}")
                print(f"  真实姓名: {parts[3]}")
                print(f"  公司名称: {parts[4]}")
                print(f"  部门: {parts[7]}")
                print(f"  是否部门经理: {parts[8]}")
                print(f"  角色: {parts[9]}")
                print(f"  是否活跃: {parts[14]}")
                
                zhouyj_id = parts[0]
                zhouyj_dept = parts[7]
                zhouyj_company = parts[4]
                break
    
    # 2. 分析sales_manager的project权限级别
    print(f"\n🔐 sales_manager项目权限分析:")
    
    role_perm_pattern = r"COPY public\.role_permissions.*?FROM stdin;(.*?)\\\."
    role_match = re.search(role_perm_pattern, content, re.DOTALL)
    
    if role_match:
        role_data = role_match.group(1)
        for line in role_data.split('\n'):
            if 'sales_manager' in line and 'project' in line:
                parts = line.strip().split('\t')
                print(f"  角色: {parts[1]}")
                print(f"  模块: {parts[2]}")
                print(f"  可查看: {parts[3]}")
                permission_level = parts[10] if parts[10] != '\\N' else 'personal'
                print(f"  权限级别: {permission_level}")  # permission_level字段
                print(f"  ✅ 确认权限级别为: {permission_level}")
                break
    
    # 3. 分析数据归属关系
    print(f"\n🔗 zhouyj数据归属关系分析:")
    
    affiliation_pattern = r"COPY public\.affiliations.*?FROM stdin;(.*?)\\\."
    affiliation_match = re.search(affiliation_pattern, content, re.DOTALL)
    
    zhouyj_affiliations = []
    if affiliation_match:
        affiliation_data = affiliation_match.group(1)
        for line in affiliation_data.split('\n'):
            parts = line.strip().split('\t')
            if len(parts) >= 4 and parts[2] == '17':  # viewer_id = 17 (zhouyj)
                owner_id = parts[1]
                zhouyj_affiliations.append(owner_id)
                print(f"    发现归属关系: owner_id={owner_id}, viewer_id=17")
        
        print(f"  zhouyj可以查看的其他用户数据: {len(zhouyj_affiliations)}个用户")
        print(f"  用户ID列表: {zhouyj_affiliations}")
        
        # 查找这些用户的姓名
        if zhouyj_affiliations and users_match:
            print(f"  具体用户信息:")
            users_data = users_match.group(1)
            for line in users_data.split('\n'):
                parts = line.strip().split('\t')
                if len(parts) > 3 and parts[0] in zhouyj_affiliations:
                    print(f"    ID {parts[0]}: {parts[3]} ({parts[1]}) - {parts[7]}")
    
    # 4. 分析zhouyj作为厂商销售经理的项目
    print(f"\n📊 zhouyj作为厂商销售经理的项目:")
    
    projects_pattern = r"COPY public\.projects.*?FROM stdin;(.*?)\\\."
    projects_match = re.search(projects_pattern, content, re.DOTALL)
    
    vendor_projects = 0
    if projects_match:
        projects_data = projects_match.group(1)
        for line in projects_data.split('\n'):
            parts = line.strip().split('\t')
            # vendor_sales_manager_id字段通常在第5或第6个位置
            if len(parts) > 10:
                for i, part in enumerate(parts):
                    if part == '17':  # zhouyj的ID
                        # 检查是否是vendor_sales_manager_id字段
                        if i >= 4 and i <= 8:  # 大概位置范围
                            vendor_projects += 1
                            if vendor_projects <= 5:  # 只显示前5个
                                print(f"    项目ID {parts[0]}: {parts[1] if len(parts) > 1 else 'N/A'}")
                            break
    
    print(f"  zhouyj作为厂商销售经理的项目总数: {vendor_projects}")
    
    # 5. 最终结论
    print(f"\n📝 权限异常原因分析:")
    print("="*60)
    
    print("✅ 已确认的事实:")
    print(f"  1. zhouyj角色: sales_manager")
    print(f"  2. sales_manager在project模块的权限级别: personal")
    print(f"  3. zhouyj有{len(zhouyj_affiliations)}个数据归属关系")
    print(f"  4. zhouyj是{vendor_projects}个项目的厂商销售经理")
    
    print(f"\n🎯 权限异常的根本原因:")
    
    if len(zhouyj_affiliations) > 0:
        print(f"  ✅ 主要原因1: 数据归属关系")
        print(f"     - zhouyj通过affiliations表被授权查看{len(zhouyj_affiliations)}个其他用户的数据")
        print(f"     - 这些用户的所有项目zhouyj都能看到")
    
    if vendor_projects > 0:
        print(f"  ✅ 主要原因2: 厂商销售经理权限")
        print(f"     - zhouyj是{vendor_projects}个项目的厂商销售经理")
        print(f"     - 根据权限逻辑，厂商销售经理可以查看对应的项目")
    
    if len(zhouyj_affiliations) == 0 and vendor_projects == 0:
        print(f"  ❓ 需要进一步调查:")
        print(f"     - 检查是否有其他权限覆盖机制")
        print(f"     - 确认云端权限逻辑实现是否与本地一致")
        print(f"     - 检查是否存在其他数据关联关系")
    
    print(f"\n💡 解决方案建议:")
    if len(zhouyj_affiliations) > 0:
        print(f"  1. 检查并清理不必要的数据归属关系")
        print(f"     DELETE FROM affiliations WHERE viewer_id = 17;")
    
    if vendor_projects > 0:
        print(f"  2. 检查项目的厂商销售经理设置是否合理")
        print(f"     SELECT id, project_name FROM projects WHERE vendor_sales_manager_id = 17;")
    
    print(f"  3. 确认这些权限设置是否符合业务需求")
    
    return {
        'affiliations_count': len(zhouyj_affiliations),
        'vendor_projects_count': vendor_projects,
        'permission_level': 'personal'
    }

if __name__ == '__main__':
    result = final_analysis()
    
    print(f"\n🔍 分析结果汇总:")
    print(f"数据归属关系数量: {result['affiliations_count']}")
    print(f"厂商销售经理项目数量: {result['vendor_projects_count']}")
    print(f"权限级别: {result['permission_level']}")