#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断云端OVS系统报销单BX2025091806审批流程问题"""
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

project_root = get_project_root()
sys.path.insert(0, project_root)

# 强制设置为云端OVS数据库
os.environ['DATABASE_URL'] = 'postgresql://postgres.pqzviljbpfoqvyfulakl:nyjrIc-gubcu4-rukhoc@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres'

from app import create_app, db
from app.models.expense import Expense
from app.models.approval import ApprovalInstance, ApprovalStep, ApprovalRecord, ApprovalStatus
from app.models.user import User
from sqlalchemy import text
import json

app = create_app()

def print_section(title):
    """打印分隔线和标题"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

with app.app_context():
    # 确认数据库连接
    print_section("1. 数据库连接信息")
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if 'ovs' in db_url.lower() or 'pqzviljbpfoqvyfulakl' in db_url:
        print("✅ 已连接到云端OVS数据库 (Supabase)")
    else:
        print(f"⚠️  当前数据库: {db_url[:100]}")
        print("请确认是否为OVS数据库")

    # 查询报销单基本信息
    print_section("2. 报销单BX2025091806基本信息")
    expense = Expense.query.filter_by(expense_number='BX2025091806').first()

    if not expense:
        print("❌ 未找到报销单BX2025091806")
        sys.exit(1)

    print(f"报销单ID: {expense.id}")
    print(f"报销单编号: {expense.expense_number}")
    print(f"标题: {expense.title}")
    print(f"状态: {expense.status}")
    print(f"总金额: {expense.total_amount:.2f} 元" if expense.total_amount else "总金额: 无")
    print(f"申请人ID (owner_id): {expense.owner_id}")
    print(f"创建时间: {expense.created_at}")

    # 查询申请人信息
    owner = User.query.get(expense.owner_id)
    if owner:
        print(f"申请人: {owner.username} (真实姓名: {owner.real_name}, 角色: {owner.role})")
    else:
        print(f"⚠️  申请人ID {expense.owner_id} 不存在")

    # 查询审批实例
    print_section("3. 审批实例信息")
    approval = ApprovalInstance.query.filter_by(
        object_type='expense',
        object_id=expense.id
    ).first()

    if not approval:
        print("❌ 未找到审批实例")
        sys.exit(1)

    print(f"审批实例ID: {approval.id}")
    print(f"审批状态: {approval.status}")
    print(f"当前步骤ID: {approval.current_step}")
    print(f"流程模板ID: {approval.process_id}")
    print(f"创建人ID: {approval.created_by}")

    # 解析模板快照
    template_snapshot = None
    if approval.template_snapshot:
        try:
            if isinstance(approval.template_snapshot, str):
                template_snapshot = json.loads(approval.template_snapshot)
            else:
                template_snapshot = approval.template_snapshot
            print(f"✅ 模板快照: 包含 {len(template_snapshot.get('steps', []))} 个步骤")
        except Exception as e:
            print(f"⚠️  模板快照解析失败: {e}")

    # 查询所有审批步骤（从快照或数据库）
    print_section("4. 审批步骤详细信息")

    if template_snapshot and 'steps' in template_snapshot:
        print("📋 从模板快照获取步骤信息:")
        steps = template_snapshot['steps']
        current_step_order = approval.current_step_order if hasattr(approval, 'current_step_order') else 1

        for i, step in enumerate(steps, 1):
            is_current = (i == current_step_order)
            marker = "👉 [当前步骤]" if is_current else ""
            print(f"\n步骤 {i}: {step.get('step_name')} {marker}")
            print(f"  - 审批人类型: {step.get('approver_type', 'user')}")
            print(f"  - 审批人用户ID: {step.get('approver_user_id', '无')}")
            print(f"  - 审批人用户名: {step.get('approver_username', '无')}")
            print(f"  - 审批人真实姓名: {step.get('approver_real_name', '无')}")
            print(f"  - 操作类型: {step.get('action_type', '审批')}")

            if is_current and i == 2:
                print("\n  🔍 [重点分析] 这是第二步，问题步骤")
                print(f"  - 配置的审批人ID: {step.get('approver_user_id')}")
                print(f"  - 配置的审批人类型: {step.get('approver_type')}")
    else:
        print("📋 从数据库获取步骤信息:")
        # 查询数据库中的步骤
        db_steps = ApprovalStep.query.filter_by(
            approval_instance_id=approval.id
        ).order_by(ApprovalStep.step_order).all()

        if not db_steps:
            # 尝试从模板获取步骤
            from app.models.approval import ApprovalProcessTemplate
            template = ApprovalProcessTemplate.query.get(approval.process_id)
            if template:
                db_steps = ApprovalStep.query.filter_by(
                    process_id=template.id
                ).order_by(ApprovalStep.step_order).all()
                print(f"从模板获取到 {len(db_steps)} 个步骤")

        for step in db_steps:
            is_current = (step.id == approval.current_step)
            marker = "👉 [当前步骤]" if is_current else ""
            print(f"\n步骤ID {step.id}: {step.step_name} {marker}")
            print(f"  - 步骤顺序: {step.step_order}")
            print(f"  - 审批人类型: {step.approver_type or 'user'}")
            print(f"  - 审批人用户ID: {step.approver_user_id or '无'}")
            print(f"  - 操作类型: {step.action_type or '审批'}")

            if step.approver_user_id:
                approver = User.query.get(step.approver_user_id)
                if approver:
                    print(f"  - 审批人: {approver.username} (真实姓名: {approver.real_name})")
                else:
                    print(f"  ⚠️  审批人用户ID {step.approver_user_id} 不存在")

    # 查询审批记录
    print_section("5. 审批记录")
    try:
        records = ApprovalRecord.query.filter_by(
            instance_id=approval.id
        ).all()

        if records:
            for record in records:
                approver = User.query.get(record.approver_id) if record.approver_id else None
                approver_name = f"{approver.username} ({approver.real_name})" if approver else "未知"
                print(f"• {record.action} - {approver_name}")
                if hasattr(record, 'comment') and record.comment:
                    print(f"  备注: {record.comment}")
        else:
            print("暂无审批记录")
    except Exception as e:
        print(f"⚠️  查询审批记录失败: {e}")

    # 查询admin用户信息
    print_section("6. Admin用户信息对比")
    admin_user = User.query.filter_by(username='admin').first()

    if admin_user:
        print(f"Admin用户:")
        print(f"  - ID: {admin_user.id}")
        print(f"  - 用户名: {admin_user.username}")
        print(f"  - 真实姓名: {admin_user.real_name}")
        print(f"  - 角色: {admin_user.role}")
    else:
        print("⚠️  未找到admin用户")

    # 查找所有真实姓名包含james.ni的用户
    print("\n查找真实姓名包含'james'或'ni'的用户:")
    james_users = User.query.filter(
        db.or_(
            User.real_name.ilike('%james%'),
            User.real_name.ilike('%ni%'),
            User.username.ilike('%james%'),
            User.username.ilike('%ni%')
        )
    ).all()

    for user in james_users:
        print(f"  - ID: {user.id}, 用户名: {user.username}, 真实姓名: {user.real_name}, 角色: {user.role}")

    # 分析权限问题
    print_section("7. 审批权限诊断")

    if approval.current_step:
        # 获取当前步骤信息
        current_step_info = approval.get_current_step_info()

        if current_step_info:
            print("当前步骤信息 (从get_current_step_info获取):")
            if isinstance(current_step_info, dict):
                print(f"  - 步骤ID: {current_step_info.get('id')}")
                print(f"  - 步骤名称: {current_step_info.get('step_name')}")
                print(f"  - 审批人类型: {current_step_info.get('approver_type')}")
                print(f"  - 审批人用户ID: {current_step_info.get('approver_user_id')}")
            else:
                print(f"  - 步骤ID: {current_step_info.id}")
                print(f"  - 步骤名称: {current_step_info.step_name}")
                print(f"  - 审批人类型: {getattr(current_step_info, 'approver_type', 'user')}")
                print(f"  - 审批人用户ID: {getattr(current_step_info, 'approver_user_id', None)}")

            # 使用系统的审批权限判断函数
            from app.helpers.approval_helpers import get_step_actual_approver, can_user_approve

            actual_approver = get_step_actual_approver(current_step_info, approval)

            print(f"\n通过get_step_actual_approver计算的实际审批人:")
            if actual_approver:
                print(f"  - ID: {actual_approver.id}")
                print(f"  - 用户名: {actual_approver.username}")
                print(f"  - 真实姓名: {actual_approver.real_name}")
                print(f"  - 角色: {actual_approver.role}")
            else:
                print("  ⚠️  无法确定实际审批人")

            # 检查admin用户是否可以审批
            if admin_user:
                can_approve = can_user_approve(approval.id, admin_user.id)
                print(f"\nAdmin用户权限检查:")
                print(f"  - Admin用户ID: {admin_user.id}")
                print(f"  - 实际审批人ID: {actual_approver.id if actual_approver else '无'}")
                print(f"  - ID匹配: {'✅ 是' if actual_approver and actual_approver.id == admin_user.id else '❌ 否'}")
                print(f"  - can_user_approve结果: {'✅ 可以审批' if can_approve else '❌ 不能审批'}")
        else:
            print("⚠️  无法获取当前步骤信息")

    # 输出诊断结论
    print_section("8. 诊断结论")

    if admin_user and actual_approver:
        if admin_user.id == actual_approver.id:
            print("✅ 用户ID匹配正常")
            print("   Admin用户ID和实际审批人ID一致，理论上应该可以审批")
            print("\n可能的原因:")
            print("   1. 前端页面缓存问题，需要刷新页面")
            print("   2. 审批实例状态不是PENDING")
            print("   3. 前端权限判断逻辑有问题")
        else:
            print("❌ 发现问题: 用户ID不匹配")
            print(f"   Admin用户ID: {admin_user.id}")
            print(f"   实际审批人ID: {actual_approver.id}")
            print(f"   实际审批人: {actual_approver.username} ({actual_approver.real_name})")
            print("\n根本原因:")
            print("   审批步骤配置的审批人不是admin用户，而是另一个用户")
            print("\n修复建议:")
            print(f"   1. 如果应该由admin审批，需要更新审批实例快照中第二步的审批人ID为 {admin_user.id}")
            print(f"   2. 或者使用实际审批人账户 {actual_approver.username} 登录进行审批")
    else:
        print("⚠️  无法完成完整诊断，缺少关键信息")

    print("\n" + "=" * 80)
