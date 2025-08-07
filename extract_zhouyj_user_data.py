#!/usr/bin/env python3
"""
从SP8D备份中提取zhouyj的具体用户数据和权限信息
"""

import re

def extract_user_data():
    """提取用户数据"""
    backup_file = "/Users/nijie/Documents/PMA/cloud_db_backups/pma_db_sp8d_backup_20250803_230106.sql"
    
    with open(backup_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 从备份中提取zhouyj相关数据...")
    
    # 1. 从最后一行提取用户ID信息
    # 行21430显示: 17	zhouyj	scrypt:32768:8:1$iQRQ5prniTjHlSwT...
    # 这表明zhouyj的用户ID是17
    
    print("👤 用户基本信息:")
    print("用户ID: 17")
    print("用户名: zhouyj")
    
    # 2. 查找包含用户ID 17的具体用户记录
    # 搜索INSERT INTO users语句
    users_insert_pattern = r"INSERT INTO users.*?VALUES\s*\([^;]*17[^;]*'zhouyj'[^;]*\);"
    user_match = re.search(users_insert_pattern, content, re.IGNORECASE | re.DOTALL)
    
    if user_match:
        print(f"\n🎯 找到完整用户记录:")
        user_record = user_match.group(0)
        print(user_record[:500] + "..." if len(user_record) > 500 else user_record)
    else:
        print("\n❌ 未找到完整用户记录")
        # 尝试其他方式查找
        print("尝试查找包含17和zhouyj的行...")
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if '17' in line and 'zhouyj' in line.lower() and 'INSERT INTO users' in line:
                print(f"行 {i+1}: {line[:200]}...")
    
    # 3. 分析操作日志中的权限相关信息
    print("\n" + "="*60)
    print("📊 从操作日志分析用户权限和项目访问情况")  
    print("="*60)
    
    # 从日志中统计zhouyj操作的项目
    project_operations = []
    quotation_operations = []
    customer_operations = []
    
    lines = content.split('\n')
    for line in lines:
        if 'zhouyj' in line.lower() and '17' in line:
            if 'project' in line and 'projects' in line:
                # 提取项目操作信息
                if 'CREATE' in line:
                    project_operations.append(('CREATE', line))
                elif 'UPDATE' in line:
                    project_operations.append(('UPDATE', line))
                elif 'DELETE' in line:
                    project_operations.append(('DELETE', line))
            elif 'quotation' in line and 'quotations' in line:
                if 'CREATE' in line:
                    quotation_operations.append(('CREATE', line))
                elif 'UPDATE' in line:
                    quotation_operations.append(('UPDATE', line))
            elif 'customer' in line and ('companies' in line or 'contacts' in line):
                if 'CREATE' in line:
                    customer_operations.append(('CREATE', line))
                elif 'UPDATE' in line:
                    customer_operations.append(('UPDATE', line))
    
    print(f"📋 项目操作统计:")
    create_projects = len([op for op in project_operations if op[0] == 'CREATE'])
    update_projects = len([op for op in project_operations if op[0] == 'UPDATE'])
    delete_projects = len([op for op in project_operations if op[0] == 'DELETE'])
    
    print(f"  - 创建项目: {create_projects} 次")
    print(f"  - 更新项目: {update_projects} 次")
    print(f"  - 删除项目: {delete_projects} 次")
    print(f"  - 项目操作总计: {len(project_operations)} 次")
    
    print(f"\n📋 报价单操作统计:")
    create_quotations = len([op for op in quotation_operations if op[0] == 'CREATE'])
    update_quotations = len([op for op in quotation_operations if op[0] == 'UPDATE'])
    print(f"  - 创建报价单: {create_quotations} 次")
    print(f"  - 更新报价单: {update_quotations} 次")
    print(f"  - 报价单操作总计: {len(quotation_operations)} 次")
    
    print(f"\n📋 客户操作统计:")
    create_customers = len([op for op in customer_operations if op[0] == 'CREATE'])
    update_customers = len([op for op in customer_operations if op[0] == 'UPDATE'])
    print(f"  - 创建客户: {create_customers} 次")
    print(f"  - 更新客户: {update_customers} 次")
    print(f"  - 客户操作总计: {len(customer_operations)} 次")
    
    # 4. 分析具体的项目ID
    print("\n" + "="*60)
    print("🎯 分析zhouyj操作的具体项目")
    print("="*60)
    
    project_ids = set()
    for operation, line in project_operations:
        # 尝试提取项目ID（通常在第三个字段）
        parts = line.split('\t')
        if len(parts) >= 4:
            try:
                table = parts[1]
                projects_table = parts[2]
                project_id = parts[3]
                if table == 'project' and projects_table == 'projects':
                    project_ids.add(project_id)
            except:
                pass
    
    print(f"zhouyj操作过的项目ID数量: {len(project_ids)}")
    if len(project_ids) > 0:
        print("项目ID列表:", sorted(list(project_ids))[:20])  # 显示前20个
        if len(project_ids) > 20:
            print(f"... 还有 {len(project_ids) - 20} 个项目")
    
    # 5. 查找角色权限信息
    print("\n" + "="*60)
    print("🔐 查找角色权限配置")
    print("="*60)
    
    # 查找sales_manager角色的权限配置
    role_perm_lines = []
    for line in lines:
        if 'sales_manager' in line.lower() and ('role_permissions' in line.lower() or 'INSERT INTO' in line):
            role_perm_lines.append(line)
    
    print(f"找到 {len(role_perm_lines)} 行包含sales_manager权限配置:")
    for i, line in enumerate(role_perm_lines[:5]):  # 显示前5行
        print(f"  {i+1}. {line[:150]}{'...' if len(line) > 150 else ''}")
    
    # 6. 查找数据归属关系
    print("\n" + "="*60)
    print("🔗 查找数据归属关系")
    print("="*60)
    
    affiliation_lines = []
    for line in lines:
        if ('affiliation' in line.lower() and '17' in line) or ('viewer_id' in line.lower() and '17' in line):
            affiliation_lines.append(line)
    
    print(f"找到 {len(affiliation_lines)} 行可能包含归属关系:")
    for i, line in enumerate(affiliation_lines[:3]):  # 显示前3行
        print(f"  {i+1}. {line[:150]}{'...' if len(line) > 150 else ''}")
    
    # 7. 分析结论
    print("\n" + "="*60)  
    print("📊 分析结论")
    print("="*60)
    
    print("基于备份文件分析的发现:")
    print(f"✅ zhouyj用户ID: 17")
    print(f"✅ 大量项目操作记录: {len(project_operations)}次，涉及{len(project_ids)}个不同项目")
    print(f"✅ 报价单操作记录: {len(quotation_operations)}次")
    print(f"✅ 客户操作记录: {len(customer_operations)}次")
    print(f"✅ 权限配置行数: {len(role_perm_lines)}行")
    print(f"✅ 可能的归属关系: {len(affiliation_lines)}行")
    
    print("\n🔍 权限异常可能原因:")
    print("1. zhouyj作为厂商销售经理 - 从操作日志看，他设置了多个项目的厂商负责人")  
    print("2. 大量项目创建和更新操作表明他有广泛的项目访问权限")
    print("3. 需要进一步检查他是否被设置为其他项目的vendor_sales_manager_id")
    
    return {
        'user_id': 17,
        'project_operations': len(project_operations),
        'project_ids': list(project_ids),
        'quotation_operations': len(quotation_operations),
        'customer_operations': len(customer_operations),
        'role_permission_lines': len(role_perm_lines),
        'affiliation_lines': len(affiliation_lines)
    }

if __name__ == '__main__':
    result = extract_user_data()
    
    print("\n" + "="*60)
    print("🎯 关键发现汇总")
    print("="*60)
    print(f"用户ID: {result['user_id']}")
    print(f"项目操作次数: {result['project_operations']}")
    print(f"涉及项目数量: {len(result['project_ids'])}")
    print(f"报价单操作次数: {result['quotation_operations']}")
    print(f"客户操作次数: {result['customer_operations']}")
    
    print("\n💡 建议检查项")
    print("1. 查询projects表中vendor_sales_manager_id=17的记录数量")
    print("2. 查询role_permissions表中sales_manager+project的permission_level")
    print("3. 查询affiliations表中viewer_id=17的记录")
    print("4. 确认zhouyj的实际角色权限配置是否正确")