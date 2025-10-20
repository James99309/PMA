#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查批价单 PO202510-003 和对应项目的状态"""
import sys
import os

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
from app.models.pricing_order import PricingOrder
from app.models.project import Project

app = create_app()

with app.app_context():
    # 查询批价单
    pricing_order = PricingOrder.query.filter_by(order_number='PO202510-003').first()

    if not pricing_order:
        print("❌ 未找到批价单 PO202510-003")
        sys.exit(1)

    print(f"\n📋 批价单信息: {pricing_order.order_number}")
    print(f"ID: {pricing_order.id}")
    print(f"状态: {pricing_order.status}")
    print(f"审批通过时间: {pricing_order.approved_at}")
    print(f"审批人ID: {pricing_order.approved_by}")

    # 查询关联项目
    project = pricing_order.project
    if project:
        print(f"\n🎯 关联项目信息:")
        print(f"项目名称: {project.project_name}")
        print(f"项目ID: {project.id}")
        print(f"当前阶段: {project.current_stage}")
        print(f"是否锁定: {project.is_locked}")
        print(f"锁定原因: {project.locked_reason}")

        # 检查是否应该推进
        if pricing_order.status == 'approved' and project.current_stage == 'quoted':
            print(f"\n⚠️  问题发现:")
            print(f"  - 批价单状态: {pricing_order.status} (已批准)")
            print(f"  - 项目阶段: {project.current_stage} (批价)")
            print(f"  - 预期行为: 项目应该从 'quoted' 推进到 'signed'")
            print(f"  - 实际情况: 项目仍然停留在 'quoted' 阶段")
        elif pricing_order.status == 'approved' and project.current_stage == 'signed':
            print(f"\n✅ 状态正确:")
            print(f"  - 批价单已批准，项目已推进到签约阶段")
        else:
            print(f"\n📊 当前状态:")
            print(f"  - 批价单状态: {pricing_order.status}")
            print(f"  - 项目阶段: {project.current_stage}")
    else:
        print(f"\n❌ 批价单没有关联项目")
