#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查批价单的关联关系和分支条件评估"""
import sys, os

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

from app import create_app, db
from app.models.pricing_order import PricingOrder
from app.models.approval import ApprovalInstance, ApprovalStep
import json

def main():
    app = create_app()

    with app.app_context():
        print("\n=== 检查批价单关联关系和分支条件 ===\n")

        # 查找最近的审批实例
        instance = ApprovalInstance.query.filter(
            ApprovalInstance.object_type == 'pricing_order'
        ).order_by(ApprovalInstance.started_at.desc()).first()

        if not instance:
            print("❌ 未找到审批实例！")
            return

        print(f"实例 {instance.id}")
        print(f"  批价单ID: {instance.object_id}")

        # 获取批价单
        pricing_order = PricingOrder.query.get(instance.object_id)
        if not pricing_order:
            print("❌ 未找到批价单！")
            return

        print(f"  批价单编号: {pricing_order.order_number}")

        # 检查关联关系
        print(f"\n=== 关联关系检查 ===")

        # 检查是否有quotation属性
        has_quotation = hasattr(pricing_order, 'quotation')
        print(f"✓ 是否有quotation属性: {has_quotation}")

        if has_quotation:
            quotation = pricing_order.quotation
            print(f"  - quotation存在: {quotation is not None}")
            if quotation:
                print(f"  - quotation.id: {quotation.id}")
                has_project_type = hasattr(quotation, 'project_type')
                print(f"  - quotation有project_type字段: {has_project_type}")
                if has_project_type:
                    print(f"  - quotation.project_type: {quotation.project_type}")

        # 检查是否有project属性
        has_project = hasattr(pricing_order, 'project')
        print(f"\n✓ 是否有project属性: {has_project}")

        if has_project:
            project = pricing_order.project
            print(f"  - project存在: {project is not None}")
            if project:
                print(f"  - project.id: {project.id}")
                has_project_type = hasattr(project, 'project_type')
                print(f"  - project有project_type字段: {has_project_type}")
                if has_project_type:
                    print(f"  - project.project_type: {project.project_type}")

        # 模拟分支条件评估
        print(f"\n=== 模拟分支条件评估 ===")

        # 获取步骤1（分支步骤）
        steps = instance.get_steps()
        if steps:
            step1 = steps[0] if isinstance(steps[0], dict) else None

            if step1:
                print(f"步骤1配置:")
                print(f"  - step_name: {step1.get('step_name')}")
                print(f"  - action_type: {step1.get('action_type')}")

                branch_condition = step1.get('branch_condition')
                if branch_condition:
                    field = branch_condition.get('field')
                    print(f"  - 分支字段: {field}")

                    # 尝试获取字段值（模拟_get_object_field_value逻辑）
                    field_value = None

                    if field == 'project_type':
                        if hasattr(pricing_order, 'quotation') and pricing_order.quotation:
                            if hasattr(pricing_order.quotation, 'project_type'):
                                field_value = pricing_order.quotation.project_type
                                print(f"  - 从quotation获取到project_type: {field_value}")

                        if field_value is None:
                            if hasattr(pricing_order, 'project') and pricing_order.project:
                                if hasattr(pricing_order.project, 'project_type'):
                                    field_value = pricing_order.project.project_type
                                    print(f"  - 从project获取到project_type: {field_value}")

                    if field_value is None:
                        print(f"  ⚠️ 无法获取字段值！")
                        print(f"  → 会走默认分支（default_branch）")
                        default_branch = branch_condition.get('default_branch', {})
                        print(f"  → 默认分支action: '{default_branch.get('action', '')}'")
                        if not default_branch.get('action'):
                            print(f"  ❌ 默认分支action为空，不会执行pricing_settlement_approval！")
                            print(f"  ❌ 这就是数据未保存的原因！")
                    else:
                        print(f"  ✓ 字段值: {field_value}")

                        # 匹配条件
                        conditions = branch_condition.get('conditions', [])
                        matched = False
                        for i, cond in enumerate(conditions):
                            if cond.get('operator') == 'equals' and cond.get('value') == field_value:
                                matched = True
                                print(f"  ✓ 匹配条件 {i+1}: {cond.get('value')}")
                                print(f"  ✓ 审批人ID: {cond.get('approver_id')}")
                                print(f"  ✓ 动作: {cond.get('action')}")
                                break

                        if not matched:
                            print(f"  ⚠️ 没有匹配的条件，会走默认分支")
                            default_branch = branch_condition.get('default_branch', {})
                            print(f"  → 默认分支action: '{default_branch.get('action', '')}'")

        # 检查数据库表结构
        print(f"\n=== 数据库表结构检查 ===")
        from sqlalchemy import inspect

        inspector = inspect(db.engine)

        # 检查pricing_order表的列
        pricing_columns = [col['name'] for col in inspector.get_columns('pricing_order')]
        print(f"pricing_order表字段: {pricing_columns}")

        # 检查是否有project_id或quotation_id外键
        has_project_id = 'project_id' in pricing_columns
        has_quotation_id = 'quotation_id' in pricing_columns

        print(f"  - 是否有project_id字段: {has_project_id}")
        print(f"  - 是否有quotation_id字段: {has_quotation_id}")

        if has_project_id:
            print(f"  - pricing_order.project_id值: {getattr(pricing_order, 'project_id', None)}")
        if has_quotation_id:
            print(f"  - pricing_order.quotation_id值: {getattr(pricing_order, 'quotation_id', None)}")

        print("\n=== 检查完成 ===\n")

if __name__ == '__main__':
    main()
