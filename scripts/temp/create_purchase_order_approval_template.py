#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建采购订单审批模板

使用方法：
    python scripts/temp/create_purchase_order_approval_template.py

说明：
    此脚本在审批配置中创建一个默认的采购订单审批模板。
    模板包含一个审批步骤，审批人需要在创建后通过审批配置页面进行配置。
"""
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
from app.models.approval import ApprovalProcessTemplate, ApprovalStep
from app.models.user import User


def create_template():
    """创建采购订单审批模板"""
    app = create_app()

    with app.app_context():
        # 检查是否已存在
        existing = ApprovalProcessTemplate.query.filter_by(
            object_type='purchase_order',
            is_active=True
        ).first()

        if existing:
            print(f"✅ 采购订单审批模板已存在: {existing.name} (ID: {existing.id})")
            print("   如需创建新模板，请先在审批配置页面禁用现有模板")
            return

        # 获取管理员用户作为创建者
        admin = User.query.filter_by(role='admin').first()
        if not admin:
            admin = User.query.first()

        if not admin:
            print("❌ 无法找到用户，请先创建用户")
            return

        # 创建模板
        template = ApprovalProcessTemplate(
            name="采购订单审批流程",
            object_type="purchase_order",
            is_active=True,
            created_by=admin.id,
            lock_object_on_start=True,
            required_fields=['company_id']  # 必须选择供应商
        )
        db.session.add(template)
        db.session.flush()  # 获取ID

        # 查找供应链部门负责人
        supply_chain_manager = User.query.filter(
            User.is_department_manager == True,
            User.department == '供应链'
        ).first()

        # 创建审批步骤
        step = ApprovalStep(
            process_id=template.id,
            step_order=1,
            step_name="供应链负责人审批",
            approver_user_id=supply_chain_manager.id if supply_chain_manager else None,
            approver_type='user' if supply_chain_manager else 'auto',
            action_type='authorization',
            send_email=True
        )
        db.session.add(step)

        db.session.commit()

        print(f"✅ 采购订单审批模板创建成功!")
        print(f"   模板ID: {template.id}")
        print(f"   模板名称: {template.name}")

        if supply_chain_manager:
            print(f"   审批人: {supply_chain_manager.real_name or supply_chain_manager.username}")
        else:
            print(f"   ⚠️ 未找到供应链部门负责人，请在审批配置页面配置审批人")
            print(f"   访问 /approval/config/ 进行配置")


if __name__ == '__main__':
    create_template()
