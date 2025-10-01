#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查订单审批流程配置
此脚本用于诊断为什么订单审批流程可能没有正确配置
"""

import os
import sys

# 添加项目路径到Python路径
sys.path.insert(0, '/Users/nijie/Documents/PMA')

# 设置环境变量
os.environ['FLASK_APP'] = 'run.py'
os.environ['FLASK_ENV'] = 'development'

try:
    from app import create_app, db
    from app.models.approval import ApprovalProcessTemplate, ApprovalStep
    from app.models.user import User
    from app.helpers.approval_helpers import get_available_templates
    from sqlalchemy import func
    
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("订单审批流程配置诊断报告")
        print("=" * 60)
        
        # 1. 检查所有审批模板
        print("\n1. 所有审批模板概览：")
        all_templates = ApprovalProcessTemplate.query.all()
        if not all_templates:
            print("   ❌ 数据库中没有任何审批模板！")
        else:
            print(f"   ✅ 找到 {len(all_templates)} 个审批模板:")
            for template in all_templates:
                status = "✅ 激活" if template.is_active else "❌ 禁用"
                print(f"      - ID: {template.id}, 名称: {template.name}, 对象类型: {template.object_type}, 状态: {status}")
        
        # 2. 检查order类型的模板
        print("\n2. 针对 'order' 类型的审批模板：")
        order_templates = ApprovalProcessTemplate.query.filter_by(object_type='order').all()
        if not order_templates:
            print("   ❌ 没有找到针对 'order' 类型的审批模板！")
        else:
            print(f"   ✅ 找到 {len(order_templates)} 个order类型模板:")
            for template in order_templates:
                status = "✅ 激活" if template.is_active else "❌ 禁用"
                print(f"      - ID: {template.id}, 名称: {template.name}, 状态: {status}")
                
                # 检查步骤
                steps = ApprovalStep.query.filter_by(process_id=template.id).order_by(ApprovalStep.step_order).all()
                if steps:
                    print(f"        审批步骤 ({len(steps)}个):")
                    for step in steps:
                        approver = User.query.get(step.approver_user_id) if step.approver_user_id else None
                        approver_info = f"{approver.username}({approver.role})" if approver else "未指定"
                        print(f"          步骤{step.step_order}: {step.step_name} - 审批人: {approver_info}")
                else:
                    print("        ❌ 该模板没有配置审批步骤！")
        
        # 3. 检查purchase_order类型的模板
        print("\n3. 针对 'purchase_order' 类型的审批模板：")
        po_templates = ApprovalProcessTemplate.query.filter_by(object_type='purchase_order').all()
        if not po_templates:
            print("   ❌ 没有找到针对 'purchase_order' 类型的审批模板！")
        else:
            print(f"   ✅ 找到 {len(po_templates)} 个purchase_order类型模板:")
            for template in po_templates:
                status = "✅ 激活" if template.is_active else "❌ 禁用"
                print(f"      - ID: {template.id}, 名称: {template.name}, 状态: {status}")
                
                # 检查步骤
                steps = ApprovalStep.query.filter_by(process_id=template.id).order_by(ApprovalStep.step_order).all()
                if steps:
                    print(f"        审批步骤 ({len(steps)}个):")
                    for step in steps:
                        approver = User.query.get(step.approver_user_id) if step.approver_user_id else None
                        approver_info = f"{approver.username}({approver.role})" if approver else "未指定"
                        print(f"          步骤{step.step_order}: {step.step_name} - 审批人: {approver_info}")
                else:
                    print("        ❌ 该模板没有配置审批步骤！")
        
        # 4. 测试get_available_templates函数
        print("\n4. 测试get_available_templates函数：")
        try:
            print("   测试 get_available_templates('order'):")
            order_templates_func = get_available_templates('order')
            if order_templates_func:
                print(f"      ✅ 返回 {len(order_templates_func)} 个模板:")
                for template in order_templates_func:
                    print(f"         - {template.name} (ID: {template.id})")
            else:
                print("      ❌ 函数返回空列表")
            
            print("   测试 get_available_templates('purchase_order'):")
            po_templates_func = get_available_templates('purchase_order')
            if po_templates_func:
                print(f"      ✅ 返回 {len(po_templates_func)} 个模板:")
                for template in po_templates_func:
                    print(f"         - {template.name} (ID: {template.id})")
            else:
                print("      ❌ 函数返回空列表")
                
        except Exception as e:
            print(f"      ❌ 调用函数时出错: {str(e)}")
        
        # 5. 按对象类型统计模板
        print("\n5. 按对象类型统计审批模板：")
        stats = db.session.query(
            ApprovalProcessTemplate.object_type,
            func.count(ApprovalProcessTemplate.id).label('total'),
            func.sum(ApprovalProcessTemplate.is_active.cast(db.Integer)).label('active')
        ).group_by(ApprovalProcessTemplate.object_type).all()
        
        if stats:
            for stat in stats:
                print(f"   对象类型: {stat.object_type:15} | 总数: {stat.total:2} | 激活: {stat.active:2}")
        else:
            print("   ❌ 没有找到任何审批模板统计数据")
        
        # 6. 检查用户角色情况
        print("\n6. 检查系统用户角色：")
        users = User.query.all()
        role_count = {}
        for user in users:
            role = user.role or 'None'
            role_count[role] = role_count.get(role, 0) + 1
        
        print("   用户角色分布:")
        for role, count in role_count.items():
            print(f"      {role}: {count} 人")
        
        # 7. 提供修复建议
        print("\n" + "=" * 60)
        print("修复建议：")
        print("=" * 60)
        
        if not order_templates and not po_templates:
            print("❌ 问题：没有为订单配置审批模板")
            print("✅ 解决方案：")
            print("   1. 创建针对 'order' 或 'purchase_order' 类型的审批模板")
            print("   2. 为模板配置适当的审批步骤")
            print("   3. 指定具有相应权限的审批人")
            print()
            print("🔧 可以运行以下命令创建示例模板：")
            print("   python create_order_approval_template.py")
        
        elif order_templates or po_templates:
            inactive_templates = [t for t in (order_templates + po_templates) if not t.is_active]
            if inactive_templates:
                print("⚠️  问题：存在审批模板但被禁用")
                print("✅ 解决方案：激活相关模板")
                for template in inactive_templates:
                    print(f"   - 激活模板 '{template.name}' (ID: {template.id})")
            
            templates_without_steps = []
            for template in (order_templates + po_templates):
                steps = ApprovalStep.query.filter_by(process_id=template.id).count()
                if steps == 0:
                    templates_without_steps.append(template)
            
            if templates_without_steps:
                print("⚠️  问题：审批模板存在但没有配置审批步骤")
                print("✅ 解决方案：为以下模板添加审批步骤：")
                for template in templates_without_steps:
                    print(f"   - 模板 '{template.name}' (ID: {template.id})")

except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保在正确的Python环境中运行此脚本")
except Exception as e:
    print(f"运行时错误: {e}")
    import traceback
    traceback.print_exc()