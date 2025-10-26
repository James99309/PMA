#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查云端sp8d数据库中gxh的批价单审批流程配置"""
import sys, os

# 路径修正 - 支持从任何位置运行
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
from app.models.user import User
from app.models.approval import ApprovalProcessTemplate, ApprovalStep, ApprovalInstance, ApprovalRecord
from app.models.pricing_order import PricingOrder
import json

def main():
    # 创建应用上下文（会自动使用 .env.sp8d.prod 配置连接云端数据库）
    app = create_app()

    with app.app_context():
        print("\n=== 检查云端sp8d数据库 - gxh审批流程配置 ===\n")

        # 1. 查找gxh用户
        print("1. 查找gxh用户...")
        gxh_user = User.query.filter(
            (User.username == 'gxh') | (User.real_name == 'gxh')
        ).first()

        if not gxh_user:
            print("❌ 未找到gxh用户！")
            return

        print(f"✓ 找到用户: {gxh_user.real_name} (username: {gxh_user.username}, id: {gxh_user.id})")

        # 2. 查找批价单的审批流程模板
        print("\n2. 查找批价单审批流程模板...")
        templates = ApprovalProcessTemplate.query.filter(
            ApprovalProcessTemplate.object_type == 'pricing_order',
            ApprovalProcessTemplate.is_active == True
        ).all()

        if not templates:
            print("❌ 未找到激活的批价单审批流程模板！")
            return

        print(f"✓ 找到 {len(templates)} 个激活的批价单审批流程模板")

        # 3. 查找gxh作为审批人的步骤
        print("\n3. 查找gxh作为审批人的步骤...")
        for template in templates:
            print(f"\n流程模板: {template.name} (id: {template.id})")
            print(f"  - object_type: {template.object_type}")
            print(f"  - is_active: {template.is_active}")
            print(f"  - lock_object_on_start: {template.lock_object_on_start}")

            steps = ApprovalStep.query.filter(
                ApprovalStep.process_id == template.id
            ).order_by(ApprovalStep.step_order).all()

            print(f"  - 总步骤数: {len(steps)}")

            for step in steps:
                # 检查是否是gxh的步骤
                is_gxh_step = (step.approver_user_id == gxh_user.id)
                marker = "👉 [GXH步骤]" if is_gxh_step else "  "

                print(f"\n  {marker} 步骤 {step.step_order}: {step.step_name} (id: {step.id})")
                print(f"       - step_type: {step.step_type}")
                print(f"       - approver_type: {step.approver_type}")

                if step.approver_user_id:
                    approver = User.query.get(step.approver_user_id)
                    if approver:
                        print(f"       - approver: {approver.real_name} (id: {step.approver_user_id})")
                    else:
                        print(f"       - approver_user_id: {step.approver_user_id} [用户不存在]")

                print(f"       - action_type: {step.action_type}")
                print(f"       - editable_fields: {step.editable_fields}")

                if step.action_params:
                    print(f"       - action_params: {json.dumps(step.action_params, ensure_ascii=False, indent=10)}")

                if step.branch_condition:
                    print(f"       - branch_condition: {json.dumps(step.branch_condition, ensure_ascii=False, indent=10)}")

                if is_gxh_step:
                    print(f"\n       ⚠️ 关键检查点:")
                    print(f"          1. action_type是否为 'pricing_settlement_approval': {step.action_type == 'pricing_settlement_approval'}")
                    print(f"          2. editable_fields是否包含批价相关字段: {step.editable_fields}")

        # 4. 检查最近的批价单审批实例
        print("\n\n4. 检查最近的批价单审批实例...")
        instances = ApprovalInstance.query.filter(
            ApprovalInstance.object_type == 'pricing_order'
        ).order_by(ApprovalInstance.started_at.desc()).limit(5).all()

        print(f"✓ 找到最近 {len(instances)} 个批价单审批实例")

        for instance in instances:
            print(f"\n实例 {instance.id}:")
            print(f"  - object_type: {instance.object_type}")
            print(f"  - object_id: {instance.object_id}")
            print(f"  - status: {instance.status.value if instance.status else 'None'}")
            print(f"  - current_step: {instance.current_step}")
            print(f"  - started_at: {instance.started_at}")
            print(f"  - ended_at: {instance.ended_at}")

            # 查找这个实例对应的批价单
            pricing_order = PricingOrder.query.get(instance.object_id)
            if pricing_order:
                print(f"  - 批价单编号: {pricing_order.order_number}")

            # 查找gxh的审批记录
            gxh_records = ApprovalRecord.query.filter(
                ApprovalRecord.instance_id == instance.id,
                ApprovalRecord.approver_id == gxh_user.id
            ).all()

            if gxh_records:
                print(f"  - gxh的审批记录数: {len(gxh_records)}")
                for record in gxh_records:
                    print(f"    * 记录 {record.id}:")
                    print(f"      - step_id: {record.step_id}")
                    print(f"      - action: {record.action}")
                    print(f"      - timestamp: {record.timestamp}")
                    print(f"      - comment: {record.comment}")

            # 检查模板快照
            if instance.template_snapshot:
                print(f"\n  - 模板快照中的步骤:")
                steps_snapshot = instance.template_snapshot.get('steps', [])
                for step_snap in steps_snapshot:
                    if step_snap.get('approver_user_id') == gxh_user.id:
                        print(f"    * GXH步骤 {step_snap.get('step_order')}:")
                        print(f"      - step_name: {step_snap.get('step_name')}")
                        print(f"      - action_type: {step_snap.get('action_type')}")
                        print(f"      - editable_fields: {step_snap.get('editable_fields')}")

        print("\n=== 检查完成 ===\n")

if __name__ == '__main__':
    main()
