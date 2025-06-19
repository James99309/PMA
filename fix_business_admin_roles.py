#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
修复商务助理角色配置脚本
用于确保云端商务助理用户能够正确显示部门审批页面
"""

import os
import sys
import time

# 确保能导入应用模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_business_admin_roles():
    """修复商务助理角色配置"""
    try:
        from app import create_app
        from app.models.user import User
        from app.models.dictionary import Dictionary
        from app import db
        
        app = create_app()
        with app.app_context():
            print("=" * 60)
            print("🔧 修复商务助理角色配置")
            print("=" * 60)
            
            # 步骤1: 检查当前状态
            print("\n📊 步骤1: 检查当前状态")
            print("-" * 30)
            
            # 检查商务助理用户
            business_admin_users = User.query.filter_by(role='business_admin').all()
            print(f"当前商务助理用户数量: {len(business_admin_users)}")
            
            for user in business_admin_users:
                print(f"  ✅ {user.username} (ID: {user.id}, 真实姓名: {user.real_name})")
            
            # 检查特定用户的角色
            target_users = ['jing', 'tonglei']
            users_need_fix = []
            
            for username in target_users:
                user = User.query.filter_by(username=username).first()
                if user:
                    print(f"\n用户 {username}:")
                    print(f"  当前角色: '{user.role}'")
                    print(f"  是否为business_admin: {user.role == 'business_admin'}")
                    print(f"  是否激活: {user.is_active}")
                    
                    if user.role != 'business_admin':
                        users_need_fix.append(user)
                        print(f"  ⚠️ 需要修复角色")
                    else:
                        print(f"  ✅ 角色正确")
                else:
                    print(f"\n❌ 用户 {username} 不存在")
            
            # 检查角色字典
            print(f"\n📚 检查角色字典:")
            role_dict = Dictionary.query.filter_by(type='role', key='business_admin').first()
            if role_dict:
                print(f"  ✅ business_admin 字典存在")
                print(f"     键: {role_dict.key}")
                print(f"     值: {role_dict.value}")
                print(f"     激活状态: {role_dict.is_active}")
                print(f"     排序: {role_dict.sort_order}")
            else:
                print(f"  ⚠️ business_admin 角色字典缺失")
            
            # 步骤2: 执行修复
            print(f"\n🔧 步骤2: 执行修复")
            print("-" * 30)
            
            changes_made = False
            
            # 修复用户角色
            if users_need_fix:
                print(f"修复 {len(users_need_fix)} 个用户的角色:")
                for user in users_need_fix:
                    old_role = user.role
                    user.role = 'business_admin'
                    print(f"  ✅ {user.username}: {old_role} -> business_admin")
                    changes_made = True
            else:
                print("所有目标用户角色都正确，无需修复")
            
            # 修复角色字典
            if not role_dict:
                # 获取最大排序号
                max_sort_order = db.session.query(db.func.max(Dictionary.sort_order)).filter_by(type='role').scalar() or 100
                
                role_dict = Dictionary(
                    type='role',
                    key='business_admin',
                    value='商务助理',
                    is_active=True,
                    sort_order=max_sort_order + 10,
                    created_at=time.time(),
                    updated_at=time.time()
                )
                db.session.add(role_dict)
                print(f"  ✅ 添加business_admin角色字典")
                changes_made = True
                
            elif not role_dict.is_active:
                role_dict.is_active = True
                role_dict.updated_at = time.time()
                print(f"  ✅ 激活business_admin角色字典")
                changes_made = True
                
            else:
                print("角色字典状态正确，无需修复")
            
            # 提交更改
            if changes_made:
                db.session.commit()
                print(f"\n✅ 所有修复已提交到数据库")
            else:
                print(f"\n✅ 无需修复，所有配置都正确")
            
            # 步骤3: 验证修复结果
            print(f"\n🔍 步骤3: 验证修复结果")
            print("-" * 30)
            
            # 重新检查商务助理用户
            business_admin_users = User.query.filter_by(role='business_admin').all()
            print(f"修复后商务助理用户数量: {len(business_admin_users)}")
            
            all_correct = True
            for username in target_users:
                user = User.query.filter_by(username=username).first()
                if user:
                    is_correct = user.role == 'business_admin' and user.is_active
                    status = "✅ 正确" if is_correct else "❌ 仍有问题"
                    print(f"  用户 {username}: {user.role} - {status}")
                    if not is_correct:
                        all_correct = False
                else:
                    print(f"  用户 {username}: ❌ 不存在")
                    all_correct = False
            
            # 重新检查角色字典
            role_dict = Dictionary.query.filter_by(type='role', key='business_admin').first()
            if role_dict and role_dict.is_active:
                print(f"  角色字典: ✅ 正确")
            else:
                print(f"  角色字典: ❌ 仍有问题")
                all_correct = False
            
            print(f"\n{'='*60}")
            if all_correct:
                print("🎉 修复完成！商务助理用户现在应该能看到部门审批页面了")
            else:
                print("⚠️ 修复后仍有问题，需要进一步检查")
            print("="*60)
            
            return all_correct
            
    except Exception as e:
        print(f"❌ 修复过程中出现错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_template_logic():
    """检查模板逻辑是否正确"""
    try:
        print(f"\n📄 检查模板逻辑")
        print("-" * 30)
        
        template_path = "app/templates/approval/center.html"
        if os.path.exists(template_path):
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 检查部门审批相关代码
            if "current_user.role == 'business_admin'" in content:
                print("✅ 模板包含正确的角色检查逻辑")
            else:
                print("❌ 模板缺少角色检查逻辑")
                
            if "'department'" in content and "'部门审批'" in content:
                print("✅ 模板包含部门审批标签页配置")
            else:
                print("❌ 模板缺少部门审批标签页配置")
                
        else:
            print(f"❌ 模板文件不存在: {template_path}")
            
    except Exception as e:
        print(f"❌ 检查模板逻辑失败: {str(e)}")

if __name__ == '__main__':
    print("开始修复商务助理角色配置...")
    
    # 检查模板逻辑
    check_template_logic()
    
    # 执行修复
    success = fix_business_admin_roles()
    
    if success:
        print("\n🎯 下一步操作:")
        print("1. 请商务助理用户重新登录系统")
        print("2. 访问审批中心页面")
        print("3. 确认是否显示'部门审批'标签页")
        print("4. 如果仍有问题，请检查代码版本是否为最新")
    else:
        print("\n❌ 修复失败，请检查错误信息并手动修复")
    
    print(f"\n修复脚本执行完成") 