#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 tonglei 可见的报销单的真实owner
"""
import sys
import os

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
from app.models.user import User
from app.models.expense import Expense
from sqlalchemy import text

app = create_app()

with app.app_context():
    # 查询 tonglei
    tonglei = User.query.filter_by(username='tonglei').first()
    if not tonglei:
        print("❌ 未找到 tonglei 账户")
        sys.exit(1)

    print("=" * 80)
    print("检查报销单的真实 owner")
    print("=" * 80)
    print(f"\n当前用户: {tonglei.username} ({tonglei.real_name}) - {tonglei.role}")
    print(f"部门: {tonglei.department}")
    print(f"公司: {tonglei.company_name}")

    # 查询所有未删除的报销单
    expenses = Expense.query.filter_by(is_deleted=False).order_by(Expense.created_at.desc()).limit(100).all()

    print(f"\n找到 {len(expenses)} 条报销单")
    print("\n报销单列表 (按创建时间倒序):")
    print("-" * 80)
    print(f"{'编号':<20} {'申请人ID':<10} {'申请人':<15} {'角色':<15} {'部门':<10}")
    print("-" * 80)

    # 统计
    owner_stats = {}
    department_stats = {}

    for exp in expenses:
        owner = User.query.get(exp.owner_id)
        if owner:
            owner_name = f"{owner.real_name or owner.username}"
            owner_role = owner.role
            owner_dept = owner.department or '无'

            print(f"{exp.expense_number:<20} {exp.owner_id:<10} {owner_name:<15} {owner_role:<15} {owner_dept:<10}")

            # 统计
            if owner_name not in owner_stats:
                owner_stats[owner_name] = 0
            owner_stats[owner_name] += 1

            if owner_dept not in department_stats:
                department_stats[owner_dept] = 0
            department_stats[owner_dept] += 1

    # tonglei 的归属关系用户
    print("\n" + "=" * 80)
    print("Tonglei 的归属关系用户:")
    print("=" * 80)
    from app.models.user import Affiliation
    affiliations = Affiliation.query.filter_by(viewer_id=tonglei.id).all()

    affiliation_user_ids = []
    for aff in affiliations:
        owner = User.query.get(aff.owner_id)
        if owner:
            affiliation_user_ids.append(aff.owner_id)
            print(f"  - {owner.username} ({owner.real_name}) - ID: {aff.owner_id}")

    # 检查可见的报销单的owner是否在归属关系中
    print("\n" + "=" * 80)
    print("检查截图中可见的用户:")
    print("=" * 80)

    visible_users = ['郭小金', '李华伟', '周慧锦']

    for visible_user_name in visible_users:
        user = User.query.filter(
            (User.real_name == visible_user_name) | (User.username == visible_user_name)
        ).first()

        if user:
            is_affiliation = "✅ 是" if user.id in affiliation_user_ids else "❌ 否"
            print(f"\n{visible_user_name}:")
            print(f"  - ID: {user.id}")
            print(f"  - 用户名: {user.username}")
            print(f"  - 角色: {user.role}")
            print(f"  - 部门: {user.department}")
            print(f"  - 是否在归属关系中: {is_affiliation}")

            # 检查该用户的报销单
            user_expenses = Expense.query.filter_by(
                owner_id=user.id,
                is_deleted=False
            ).all()

            print(f"  - 报销单数量: {len(user_expenses)}")
            if user_expenses:
                print(f"  - 最近的报销单:")
                for exp in user_expenses[:3]:
                    print(f"      {exp.expense_number} - {exp.title}")
        else:
            print(f"\n{visible_user_name}: ❌ 未找到该用户")

    # 按部门统计
    print("\n" + "=" * 80)
    print("按部门统计报销单数量:")
    print("=" * 80)
    for dept, count in sorted(department_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {dept}: {count} 条")

    print("\n" + "=" * 80)
    print("分析完成")
    print("=" * 80)
