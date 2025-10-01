#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断云端OVS系统所有进行中的报销单审批实例"""
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
from app.models.approval import ApprovalInstance, ApprovalStep, ApprovalStatus
from app.models.user import User
from sqlalchemy import text
import json

app = create_app()

def print_section(title):
    """打印分隔线和标题"""
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)

with app.app_context():
    # 确认数据库连接
    print_section("1. 数据库连接确认")
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if 'pqzviljbpfoqvyfulakl' in db_url:
        print("✅ 已连接到云端OVS数据库 (Supabase)")
    else:
        print(f"⚠️  当前数据库: {db_url[:100]}")
        print("请确认是否为OVS数据库")
        sys.exit(1)

    # 查询所有进行中的报销单审批实例
    print_section("2. 查询所有进行中的报销单审批实例")

    pending_approvals = ApprovalInstance.query.filter_by(
        object_type='expense',
        status=ApprovalStatus.PENDING
    ).all()

    print(f"找到 {len(pending_approvals)} 个进行中的报销单审批实例\n")

    if not pending_approvals:
        print("✅ 没有进行中的报销单审批实例")
        sys.exit(0)

    # 统计问题
    problems = []
    healthy_count = 0

    for approval in pending_approvals:
        # 获取报销单信息
        expense = Expense.query.get(approval.object_id)
        if not expense:
            problems.append({
                'approval_id': approval.id,
                'expense_id': approval.object_id,
                'issue': '报销单不存在',
                'severity': 'critical'
            })
            continue

        # 获取申请人
        owner = User.query.get(expense.owner_id) if expense.owner_id else None
        owner_name = f"{owner.username} ({owner.real_name})" if owner else "未知"

        # 检查1: current_step是否有效
        current_step_valid = False
        current_step_in_db = False
        current_step_in_snapshot = False
        step_id_mismatch = False

        # 从数据库检查
        step_obj = ApprovalStep.query.filter_by(id=approval.current_step).first()
        if step_obj:
            current_step_in_db = True
            current_step_valid = True

        # 从快照检查
        snapshot_step_info = None
        if approval.template_snapshot:
            try:
                snapshot = json.loads(approval.template_snapshot) if isinstance(approval.template_snapshot, str) else approval.template_snapshot
                steps = snapshot.get('steps', [])

                for step in steps:
                    # 检查是否能通过step_id匹配
                    if step.get('step_id') == approval.current_step:
                        current_step_in_snapshot = True
                        snapshot_step_info = step
                        current_step_valid = True
                        break
                    # 检查是否current_step存的是step_order
                    elif step.get('step_order') == approval.current_step:
                        step_id_mismatch = True
                        snapshot_step_info = step
                        break
            except Exception as e:
                problems.append({
                    'approval_id': approval.id,
                    'expense_number': expense.expense_number,
                    'owner': owner_name,
                    'issue': f'快照解析失败: {e}',
                    'severity': 'high'
                })
                continue

        # 检查2: get_current_step_info() 是否能返回有效信息
        try:
            current_step_info = approval.get_current_step_info()
        except Exception as e:
            current_step_info = None
            problems.append({
                'approval_id': approval.id,
                'expense_number': expense.expense_number,
                'owner': owner_name,
                'current_step': approval.current_step,
                'issue': f'get_current_step_info()执行失败: {e}',
                'severity': 'high'
            })
            continue

        # 检查3: 审批人是否能确定
        actual_approver = None
        if current_step_info:
            from app.helpers.approval_helpers import get_step_actual_approver
            try:
                actual_approver = get_step_actual_approver(current_step_info, approval)
            except Exception as e:
                problems.append({
                    'approval_id': approval.id,
                    'expense_number': expense.expense_number,
                    'owner': owner_name,
                    'current_step': approval.current_step,
                    'issue': f'无法确定审批人: {e}',
                    'severity': 'high'
                })

        # 问题汇总
        if step_id_mismatch:
            # 最严重：current_step存的是step_order而不是step_id
            problems.append({
                'approval_id': approval.id,
                'expense_number': expense.expense_number,
                'owner': owner_name,
                'current_step': approval.current_step,
                'correct_step_id': snapshot_step_info.get('step_id') if snapshot_step_info else None,
                'step_order': snapshot_step_info.get('step_order') if snapshot_step_info else None,
                'approver_id': snapshot_step_info.get('approver_user_id') if snapshot_step_info else None,
                'issue': f'current_step存储的是step_order({approval.current_step})，应为step_id({snapshot_step_info.get("step_id")})',
                'severity': 'critical'
            })
        elif not current_step_valid:
            # 严重：current_step无效
            problems.append({
                'approval_id': approval.id,
                'expense_number': expense.expense_number,
                'owner': owner_name,
                'current_step': approval.current_step,
                'issue': f'current_step={approval.current_step}既不在数据库也不在快照中',
                'severity': 'critical'
            })
        elif not current_step_info:
            # 严重：get_current_step_info()返回None
            problems.append({
                'approval_id': approval.id,
                'expense_number': expense.expense_number,
                'owner': owner_name,
                'current_step': approval.current_step,
                'issue': 'get_current_step_info()返回None，审批流程无法继续',
                'severity': 'critical'
            })
        elif not actual_approver:
            # 严重：无法确定审批人
            problems.append({
                'approval_id': approval.id,
                'expense_number': expense.expense_number,
                'owner': owner_name,
                'current_step': approval.current_step,
                'issue': '无法确定当前步骤的审批人',
                'severity': 'high'
            })
        else:
            # 健康实例
            healthy_count += 1

    # 输出结果
    print_section("3. 诊断结果汇总")

    print(f"\n总计: {len(pending_approvals)} 个进行中的审批实例")
    print(f"✅ 健康实例: {healthy_count} 个")
    print(f"❌ 问题实例: {len(problems)} 个\n")

    if not problems:
        print("🎉 所有审批实例都正常！")
    else:
        # 按严重程度分组
        critical_issues = [p for p in problems if p.get('severity') == 'critical']
        high_issues = [p for p in problems if p.get('severity') == 'high']

        if critical_issues:
            print_section("4. 严重问题 (Critical) - 需要立即修复")
            for i, problem in enumerate(critical_issues, 1):
                print(f"\n问题 #{i}:")
                print(f"  审批实例ID: {problem['approval_id']}")
                print(f"  报销单编号: {problem.get('expense_number', 'N/A')}")
                print(f"  申请人: {problem.get('owner', 'N/A')}")
                print(f"  current_step: {problem.get('current_step', 'N/A')}")
                print(f"  ❌ 问题: {problem['issue']}")

                if problem.get('correct_step_id'):
                    print(f"\n  🔧 修复SQL:")
                    print(f"     UPDATE approval_instance SET current_step = {problem['correct_step_id']} WHERE id = {problem['approval_id']};")

                    # 显示审批人信息
                    if problem.get('approver_id'):
                        approver = User.query.get(problem['approver_id'])
                        if approver:
                            print(f"     -- 修复后审批人: {approver.username} ({approver.real_name})")

        if high_issues:
            print_section("5. 高优先级问题 (High)")
            for i, problem in enumerate(high_issues, 1):
                print(f"\n问题 #{i}:")
                print(f"  审批实例ID: {problem['approval_id']}")
                print(f"  报销单编号: {problem.get('expense_number', 'N/A')}")
                print(f"  申请人: {problem.get('owner', 'N/A')}")
                print(f"  ⚠️  问题: {problem['issue']}")

        # 生成批量修复SQL
        if critical_issues and any(p.get('correct_step_id') for p in critical_issues):
            print_section("6. 批量修复SQL脚本")
            print("\n-- 在云端OVS数据库执行以下SQL修复所有问题:\n")
            print("BEGIN;")
            for problem in critical_issues:
                if problem.get('correct_step_id'):
                    print(f"UPDATE approval_instance SET current_step = {problem['correct_step_id']} WHERE id = {problem['approval_id']};")
            print("COMMIT;")
            print("\n-- 执行后所有审批流程将恢复正常")

    print("\n" + "=" * 100)
    print("  诊断完成")
    print("=" * 100)
