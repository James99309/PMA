#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""详细检查审批实例的模板快照数据"""
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
from app.models.approval import ApprovalInstance
import json

def main():
    app = create_app()

    with app.app_context():
        print("\n=== 检查模板快照详情 ===\n")

        # 检查最近一个实例
        instance = ApprovalInstance.query.filter(
            ApprovalInstance.object_type == 'pricing_order'
        ).order_by(ApprovalInstance.started_at.desc()).first()

        if not instance:
            print("❌ 未找到批价单审批实例！")
            return

        print(f"实例 {instance.id} (批价单ID: {instance.object_id})")
        print(f"  - status: {instance.status.value if instance.status else 'None'}")
        print(f"  - current_step: {instance.current_step}")
        print(f"  - template_version: {instance.template_version}")

        print(f"\n=== Template Snapshot 内容 ===")
        if instance.template_snapshot:
            print(json.dumps(instance.template_snapshot, ensure_ascii=False, indent=2))
        else:
            print("⚠️ template_snapshot 为空或None!")

        print("\n=== 使用get_steps()方法获取步骤 ===")
        steps = instance.get_steps()
        print(f"步骤类型: {type(steps)}")
        print(f"步骤数量: {len(steps) if steps else 0}")

        if steps:
            for i, step in enumerate(steps):
                print(f"\n步骤 {i+1}:")
                if isinstance(step, dict):
                    print(json.dumps(step, ensure_ascii=False, indent=2))
                else:
                    print(f"  - 对象类型: {type(step)}")
                    print(f"  - step_id: {step.id}")
                    print(f"  - step_name: {step.step_name}")
                    print(f"  - action_type: {step.action_type}")

        print("\n=== 检查完成 ===\n")

if __name__ == '__main__':
    main()
