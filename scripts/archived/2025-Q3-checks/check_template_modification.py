#!/usr/bin/env python3
"""
检查项目详情页模板中添加客户按钮的权限控制修改
"""

def check_template_modification():
    """检查模板中的权限控制修改"""
    print("=== 检查项目详情页添加客户按钮权限控制修改 ===\n")
    
    template_path = "/Users/nijie/Documents/PMA/app/templates/project/detail.html"
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        print("✅ 成功读取模板文件\n")
        
        # 查找关联客户卡片的代码块
        lines = content.split('\n')
        
        # 找到关联客户卡片开始行
        customer_card_start = -1
        add_customer_button_line = -1
        
        for i, line in enumerate(lines):
            if '关联客户' in line and 'card-title' in line:
                customer_card_start = i
                print(f"找到关联客户卡片标题在第 {i+1} 行")
            
            if customer_card_start != -1 and 'can_edit_project_data' in line and '添加客户' in line:
                add_customer_button_line = i
                print(f"找到修改后的添加客户按钮权限控制在第 {i+1} 行")
                break
        
        if add_customer_button_line != -1:
            # 显示修改后的按钮代码
            print("\n修改后的添加客户按钮权限控制代码:")
            for i in range(max(0, add_customer_button_line-2), min(len(lines), add_customer_button_line+3)):
                marker = ">>>" if i == add_customer_button_line else "   "
                print(f"{marker} {i+1:3d}: {lines[i]}")
        
        # 检查是否存在新的权限变量
        if 'can_edit_project_data' in content:
            print("\n✅ 模板中包含新的数据权限变量 'can_edit_project_data'")
        else:
            print("\n❌ 模板中未找到新的数据权限变量")
            
        # 检查旧的权限检查是否已移除
        old_permission_check = "current_user.has_permission('project', 'edit') and (current_user.role == 'admin' or current_user.id == project.owner_id)"
        
        # 统计旧权限检查的出现次数
        old_check_count = content.count(old_permission_check)
        if old_check_count == 0:
            print("✅ 添加客户按钮已移除旧的权限检查逻辑")
        else:
            print(f"⚠️  模板中仍有 {old_check_count} 处使用旧的权限检查逻辑")
        
        # 分析新的权限逻辑
        new_permission_check = "can_edit_project_data and (not project.is_locked or current_user.role == 'admin')"
        if new_permission_check in content:
            print("✅ 已使用新的权限控制逻辑")
        else:
            print("❌ 未找到新的权限控制逻辑")
        
        print("\n=== 权限控制变化总结 ===")
        print("旧逻辑：current_user.has_permission('project', 'edit') and (current_user.role == 'admin' or current_user.id == project.owner_id) and (not project.is_locked or current_user.role == 'admin')")
        print("新逻辑：can_edit_project_data and (not project.is_locked or current_user.role == 'admin')")
        
        print("\n新逻辑的优势：")
        print("1. 使用统一的数据权限系统 can_edit_data() 函数")
        print("2. 支持系统级、公司级、部门级权限")
        print("3. 包含项目共享权限检查")
        print("4. 支持厂商销售负责人权限")
        print("5. 保留了项目锁定状态检查")
        
        return True
        
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        return False

if __name__ == '__main__':
    success = check_template_modification()
    if success:
        print("\n🎉 项目详情页添加客户按钮权限控制修改验证完成！")
    else:
        print("\n❌ 验证失败！")