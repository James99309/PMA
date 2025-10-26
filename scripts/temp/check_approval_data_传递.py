#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查云端审批记录中是否接收到了pricing_order_data"""
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
from app.models.approval import ApprovalInstance, ApprovalRecord
from app.models.user import User
from app.models.pricing_order import PricingOrder
from sqlalchemy import text
import json

def main():
    app = create_app()

    with app.app_context():
        print("\n=== 检查云端数据库审批数据传递情况 ===\n")

        # 1. 查找gxh用户
        gxh_user = User.query.filter(
            (User.username == 'gxh') | (User.real_name == 'gxh')
        ).first()

        if not gxh_user:
            print("❌ 未找到gxh用户！")
            return

        print(f"✓ 找到用户: {gxh_user.real_name} (id: {gxh_user.id})")

        # 2. 查找最近的审批实例
        print("\n查找最近的批价单审批实例...")
        instance = ApprovalInstance.query.filter(
            ApprovalInstance.object_type == 'pricing_order'
        ).order_by(ApprovalInstance.started_at.desc()).first()

        if not instance:
            print("❌ 未找到审批实例！")
            return

        print(f"✓ 实例 {instance.id} (批价单ID: {instance.object_id})")

        # 3. 查找批价单
        pricing_order = PricingOrder.query.get(instance.object_id)
        if pricing_order:
            print(f"  批价单编号: {pricing_order.order_number}")
            print(f"  当前批价折扣率: {pricing_order.pricing_total_discount_rate}")
            print(f"  当前结算折扣率: {pricing_order.settlement_total_discount_rate}")

        # 4. 查找gxh的审批记录
        print(f"\n查找gxh的审批记录...")
        gxh_record = ApprovalRecord.query.filter(
            ApprovalRecord.instance_id == instance.id,
            ApprovalRecord.approver_id == gxh_user.id
        ).first()

        if not gxh_record:
            print("❌ 未找到gxh的审批记录！")
            return

        print(f"✓ 记录 {gxh_record.id}:")
        print(f"  - step_id: {gxh_record.step_id}")
        print(f"  - action: {gxh_record.action}")
        print(f"  - timestamp: {gxh_record.timestamp}")
        print(f"  - comment: {gxh_record.comment}")

        # 5. 检查是否有frontend_data字段（如果存在）
        if hasattr(gxh_record, 'frontend_data'):
            print(f"  - frontend_data: {gxh_record.frontend_data}")

        # 6. 检查应用日志中是否有相关记录
        print("\n\n=== 重要提示 ===")
        print("请检查云端应用日志（pma.log或app.log）中的以下关键字：")
        print("  1. '批价单审批 - 开始收集页面数据'")
        print("  2. '批价单审批 - 成功解析数据'")
        print("  3. '批价单审批 - 未收到pricing_order_data字段'")
        print("  4. '批结算审批 - 接收到的数据'")
        print("  5. '批结算审批 - 没有外部页面数据传递，跳过数据保存'")
        print(f"\n搜索命令示例：")
        print(f"  grep '批价单审批' logs/pma.log | grep '{instance.id}'")
        print(f"  grep '批结算审批' logs/pma.log | grep '{pricing_order.id}'")

        print("\n=== 检查完成 ===\n")

if __name__ == '__main__':
    main()
