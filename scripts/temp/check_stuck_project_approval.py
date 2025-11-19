#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查和修复卡住的项目报备审批流程"""
import sys, os

# 设置云端SP8D数据库连接
os.environ['DATABASE_URL'] = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

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
from app.models.project import Project
from app.models.user import User
from app.models.approval import ApprovalInstance, ApprovalRecord
from sqlalchemy import and_

app = create_app()

with app.app_context():
    print("=" * 60)
    print("检查卡住的项目报备审批流程")
    print("=" * 60)

    # 查找lihuawei用户
    user = User.query.filter_by(username='lihuawei').first()
    if not user:
        print("❌ 未找到用户 lihuawei")
        sys.exit(1)

    print(f"\n✅ 找到用户: {user.username} (ID: {user.id})")

    # 查找上海证大广场改造项目
    project = Project.query.filter(
        and_(
            Project.name.like('%上海证大广场改造%'),
            Project.owner_id == user.id
        )
    ).first()

    if not project:
        # 尝试查找所有该用户的项目
        print(f"\n❌ 未找到名称包含'上海证大广场改造'的项目")
        print(f"\n该用户的所有项目：")
        user_projects = Project.query.filter_by(owner_id=user.id).all()
        for p in user_projects:
            print(f"  - {p.name} (ID: {p.id}, 状态: {p.status})")
        sys.exit(1)

    print(f"\n✅ 找到项目: {project.name} (ID: {project.id})")
    print(f"   状态: {project.status}")
    print(f"   创建时间: {project.created_at}")

    # 查找该项目的审批实例
    approval_instances = ApprovalInstance.query.filter_by(
        object_type='project',
        object_id=project.id
    ).order_by(ApprovalInstance.created_at.desc()).all()

    if not approval_instances:
        print("\n❌ 未找到该项目的审批实例")
        sys.exit(1)

    print(f"\n✅ 找到 {len(approval_instances)} 个审批实例：")

    for idx, instance in enumerate(approval_instances, 1):
        print(f"\n{'='*50}")
        print(f"审批实例 #{idx}")
        print(f"{'='*50}")
        print(f"  ID: {instance.id}")
        print(f"  状态: {instance.status.value if hasattr(instance.status, 'value') else instance.status}")
        print(f"  创建时间: {instance.started_at}")
        print(f"  当前步骤: {instance.current_step}")

        # 获取审批步骤信息
        steps = instance.get_steps()
        print(f"\n  审批步骤配置 ({len(steps) if steps else 0} 个):")
        if steps:
            for step in steps:
                if isinstance(step, dict):
                    approver_id = step.get('approver_user_id')
                    approver = User.query.get(approver_id) if approver_id else None
                    approver_name = approver.username if approver else "自动分配"
                    print(f"    步骤 {step.get('step_order')}: {step.get('step_name')} - 审批人: {approver_name}")
                else:
                    approver_name = step.approver.username if step.approver else "自动分配"
                    print(f"    步骤 {step.step_order}: {step.step_name} - 审批人: {approver_name}")

        # 查找审批记录
        records = ApprovalRecord.query.filter_by(
            instance_id=instance.id
        ).order_by(ApprovalRecord.timestamp).all()

        if records:
            print(f"\n  审批记录 ({len(records)} 条):")
            for record in records:
                approver_name = record.approver.username if record.approver else "未知"
                print(f"    {approver_name}: {record.action} - {record.timestamp}")
                if record.comment:
                    print(f"      意见: {record.comment}")
        else:
            print(f"\n  ⚠️  没有审批记录")

    # 询问是否需要重置
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)

    if approval_instances:
        latest = approval_instances[0]
        status_value = latest.status.value if hasattr(latest.status, 'value') else latest.status
        if status_value in ['pending', 'in_progress']:
            print(f"\n⚠️  最新的审批实例状态为: {status_value}")
            print("   可以执行以下操作：")
            print("   1. 删除该审批实例（让用户重新提交）")
            print("   2. 重置项目状态为草稿（draft）")

            response = input("\n是否执行操作？(1/2/n): ").strip()

            if response == '1':
                print(f"\n删除审批实例 {latest.id}...")
                # 先删除所有审批记录
                ApprovalRecord.query.filter_by(instance_id=latest.id).delete()
                # 删除审批实例
                db.session.delete(latest)
                # 重置项目状态为草稿
                project.status = 'draft'
                db.session.commit()
                print("✅ 已删除审批实例并重置项目状态为草稿")
                print("   用户现在可以重新提交项目报备")

            elif response == '2':
                print(f"\n重置项目状态为草稿...")
                project.status = 'draft'
                # 同时取消审批实例
                from app.models.approval import ApprovalStatus
                latest.status = ApprovalStatus.RECALLED
                db.session.commit()
                print("✅ 已重置项目状态为草稿，并召回审批流程")
                print("   用户现在可以重新提交项目报备")
            else:
                print("\n❌ 取消操作")
