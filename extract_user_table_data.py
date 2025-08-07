#!/usr/bin/env python3
"""
从SP8D备份文件中直接提取用户表数据
"""

import re

def extract_user_table_data():
    """提取用户表的结构和数据"""
    backup_file = "/Users/nijie/Documents/PMA/cloud_db_backups/pma_db_sp8d_backup_20250803_230106.sql"
    
    with open(backup_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 分析用户表结构和数据...")
    
    # 1. 查找用户表的CREATE语句
    print("\n" + "="*60)
    print("📋 用户表结构")
    print("="*60)
    
    # 查找CREATE TABLE users语句
    create_users_pattern = r"CREATE TABLE.*?users\s*\((.*?)\);"
    create_match = re.search(create_users_pattern, content, re.IGNORECASE | re.DOTALL)
    
    if create_match:
        table_definition = create_match.group(1)
        print("✅ 找到用户表结构:")
        
        # 解析字段
        fields = []
        for line in table_definition.split(','):
            line = line.strip()
            if line and not line.upper().startswith('CONSTRAINT') and not line.upper().startswith('PRIMARY') and not line.upper().startswith('UNIQUE'):
                # 提取字段名（第一个单词）
                parts = line.split()
                if parts:
                    field_name = parts[0].strip('"')
                    fields.append(field_name)
        
        print("字段列表:")
        for i, field in enumerate(fields, 1):
            print(f"  {i:2d}. {field}")
            
        # 检查是否有data_permission_level字段
        if any('data_permission_level' in field for field in fields):
            print("\n✅ 发现 data_permission_level 字段")
        else:
            print("\n❌ 未发现 data_permission_level 字段")
    else:
        print("❌ 未找到用户表结构")
    
    # 2. 查找用户数据的COPY语句
    print("\n" + "="*60)
    print("👤 用户数据")
    print("="*60)
    
    # 查找COPY users语句和数据
    copy_users_pattern = r"COPY.*?users.*?FROM stdin;(.*?)\\\\."
    copy_match = re.search(copy_users_pattern, content, re.IGNORECASE | re.DOTALL)
    
    if copy_match:
        user_data = copy_match.group(1).strip()
        user_lines = user_data.split('\n')
        user_lines = [line.strip() for line in user_lines if line.strip()]
        
        print(f"✅ 找到用户数据，共 {len(user_lines)} 行")
        
        # 查找zhouyj的数据
        zhouyj_line = None
        for line in user_lines:
            if 'zhouyj' in line.lower():
                zhouyj_line = line
                break
        
        if zhouyj_line:
            print(f"\n🎯 zhouyj用户数据:")
            print("原始数据:")
            print(zhouyj_line)
            
            # 尝试解析数据（简化版，实际可能需要处理转义字符等）
            data_parts = zhouyj_line.split('\t')
            print(f"\n解析后的字段 (共{len(data_parts)}个):")
            
            if create_match:
                # 使用之前提取的字段名
                for i, (field, value) in enumerate(zip(fields, data_parts)):
                    # 处理特殊值
                    if value == '\\N':
                        value = 'NULL'
                    elif value.startswith('scrypt:'):
                        value = 'scrypt:...密码哈希...'
                    print(f"  {i+1:2d}. {field:25} = {value}")
        else:
            print("❌ 未找到zhouyj用户数据")
    else:
        print("❌ 未找到COPY users语句")
        
        # 尝试其他方式查找
        print("\n🔄 尝试其他方式查找用户数据...")
        
        # 查找INSERT INTO users语句
        insert_pattern = r"INSERT INTO.*?users.*?VALUES.*?\(([^;]*)\);"
        insert_matches = re.findall(insert_pattern, content, re.IGNORECASE | re.DOTALL)
        
        if insert_matches:
            print(f"找到 {len(insert_matches)} 条INSERT用户记录")
            for i, match in enumerate(insert_matches[:3]):  # 只显示前3条
                if 'zhouyj' in match.lower():
                    print(f"zhouyj记录: {match[:200]}...")
                else:
                    print(f"记录 {i+1}: {match[:100]}...")
        
    # 3. 查找角色权限表数据
    print("\n" + "="*60)
    print("🔐 角色权限数据")
    print("="*60)
    
    # 查找role_permissions的COPY数据
    copy_role_perm_pattern = r"COPY.*?role_permissions.*?FROM stdin;(.*?)\\\\."
    role_perm_match = re.search(copy_role_perm_pattern, content, re.IGNORECASE | re.DOTALL)
    
    if role_perm_match:
        role_perm_data = role_perm_match.group(1).strip()
        role_perm_lines = role_perm_data.split('\n')
        role_perm_lines = [line.strip() for line in role_perm_lines if line.strip()]
        
        print(f"✅ 找到角色权限数据，共 {len(role_perm_lines)} 行")
        
        # 查找sales_manager的project权限
        sales_manager_project_line = None
        for line in role_perm_lines:
            if 'sales_manager' in line.lower() and 'project' in line.lower():
                sales_manager_project_line = line
                break
        
        if sales_manager_project_line:
            print(f"\n🎯 sales_manager项目权限:")
            print(sales_manager_project_line)
            
            # 解析权限数据
            perm_parts = sales_manager_project_line.split('\t')
            print(f"\n权限字段解析:")
            role_perm_fields = ['id', 'role', 'module', 'can_view', 'can_create', 'can_edit', 'can_delete', 'pricing_discount_limit', 'settlement_discount_limit', 'permission_level', 'permission_level_description']
            
            for i, (field, value) in enumerate(zip(role_perm_fields, perm_parts)):
                if value == '\\N':
                    value = 'NULL'
                print(f"  {field:25} = {value}")
        else:
            print("❌ 未找到sales_manager的project权限")
    else:
        print("❌ 未找到role_permissions COPY数据")
        
    # 4. 查找数据归属表数据
    print("\n" + "="*60)
    print("🔗 数据归属关系")
    print("="*60)
    
    # 查找affiliations的COPY数据
    copy_affiliations_pattern = r"COPY.*?affiliations.*?FROM stdin;(.*?)\\\\."
    affiliation_match = re.search(copy_affiliations_pattern, content, re.IGNORECASE | re.DOTALL)
    
    if affiliation_match:
        affiliation_data = affiliation_match.group(1).strip()
        affiliation_lines = affiliation_data.split('\n')
        affiliation_lines = [line.strip() for line in affiliation_lines if line.strip()]
        
        print(f"✅ 找到数据归属数据，共 {len(affiliation_lines)} 行")
        
        # 查找viewer_id=17的记录
        zhouyj_affiliations = []
        for line in affiliation_lines:
            parts = line.split('\t')
            if len(parts) >= 3 and parts[1] == '17':  # viewer_id字段通常是第2个
                zhouyj_affiliations.append(line)
        
        if zhouyj_affiliations:
            print(f"\n🎯 zhouyj的数据归属关系 ({len(zhouyj_affiliations)}条):")
            for i, line in enumerate(zhouyj_affiliations, 1):
                parts = line.split('\t')
                print(f"  {i}. owner_id={parts[2] if len(parts)>2 else '?'}, viewer_id={parts[1] if len(parts)>1 else '?'}")
        else:
            print("❌ zhouyj没有数据归属关系")
    else:
        print("❌ 未找到affiliations数据")

if __name__ == '__main__':
    extract_user_table_data()