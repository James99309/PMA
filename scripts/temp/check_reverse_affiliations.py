#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查是否有人把 tonglei 设为 viewer (反向归属)
或者检查 tonglei 是否通过其他机制能看到部门数据
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
from app.models.user import User, Affiliation
from sqlalchemy import or_

app = create_app()

with app.app_context():
    # 查询 tonglei
    tonglei = User.query.filter_by(username='tonglei').first()
    if not tonglei:
        print("❌ 未找到 tonglei 账户")
        sys.exit(1)

    print("=" * 80)
    print("检查 Tonglei 的所有归属关系 (正向和反向)")
    print("=" * 80)
    print(f"\nTonglei ID: {tonglei.id}")
    print(f"角色: {tonglei.role}")
    print(f"部门: {tonglei.department}")

    # 1. 正向归属: tonglei 作为 viewer,可以查看哪些人的数据
    print("\n" + "=" * 80)
    print("1️⃣  正向归属 (tonglei 可以查看谁的数据)")
    print("=" * 80)

    forward_affiliations = Affiliation.query.filter_by(viewer_id=tonglei.id).all()

    if forward_affiliations:
        print(f"✅ Tonglei 有 {len(forward_affiliations)} 个正向归属:")
        for aff in forward_affiliations:
            owner = User.query.get(aff.owner_id)
            if owner:
                print(f"  - 可查看: {owner.username} ({owner.real_name}) - {owner.role} - {owner.department}")
    else:
        print("ℹ️  无正向归属")

    # 2. 反向归属: 谁把 tonglei 设为 viewer (这会让 tonglei 能看到他们的数据吗?)
    print("\n" + "=" * 80)
    print("2️⃣  反向归属 (谁把 tonglei 设为 viewer)")
    print("=" * 80)

    reverse_affiliations = Affiliation.query.filter_by(owner_id=tonglei.id).all()

    if reverse_affiliations:
        print(f"⚠️  有 {len(reverse_affiliations)} 个用户把 tonglei 设为 viewer:")
        for aff in reverse_affiliations:
            viewer = User.query.get(aff.viewer_id)
            if viewer:
                print(f"  - {viewer.username} ({viewer.real_name}) - {viewer.role} - {viewer.department}")
                print(f"    说明: {viewer.username} 可以查看 tonglei 的数据")
    else:
        print("ℹ️  无反向归属")

    # 3. 检查部门销售人员
    print("\n" + "=" * 80)
    print("3️⃣  销售部门所有成员")
    print("=" * 80)

    dept_users = User.query.filter_by(
        department=tonglei.department,
        company_name=tonglei.company_name
    ).all()

    print(f"销售部共 {len(dept_users)} 人:")
    for user in dept_users:
        marker = "👤" if user.id == tonglei.id else "  "
        dept_mgr_flag = "🔑" if getattr(user, 'is_department_manager', False) else ""
        print(f"{marker} {user.username} ({user.real_name}) - {user.role} {dept_mgr_flag}")

    # 4. 检查截图中的用户
    print("\n" + "=" * 80)
    print("4️⃣  截图中可见的用户归属关系")
    print("=" * 80)

    visible_users = ['郭小金', '李华伟', '周慧锦']
    forward_owner_ids = [aff.owner_id for aff in forward_affiliations]

    for name in visible_users:
        user = User.query.filter(
            or_(User.real_name == name, User.username == name)
        ).first()

        if user:
            # 检查是否在 tonglei 的正向归属中
            in_forward = "✅" if user.id in forward_owner_ids else "❌"

            # 检查该用户是否把 tonglei 设为 viewer
            reverse_aff = Affiliation.query.filter_by(
                owner_id=user.id,
                viewer_id=tonglei.id
            ).first()

            has_reverse = "✅" if reverse_aff else "❌"

            print(f"\n{name} ({user.username}):")
            print(f"  - 角色: {user.role}")
            print(f"  - 部门: {user.department}")
            print(f"  - 在 tonglei 正向归属中: {in_forward}")
            print(f"  - {name} 把 tonglei 设为 viewer: {has_reverse}")

            # 检查该用户的所有归属关系
            user_affiliations = Affiliation.query.filter_by(owner_id=user.id).all()
            if user_affiliations:
                print(f"  - {name} 的归属关系 ({len(user_affiliations)} 个):")
                for aff in user_affiliations:
                    viewer = User.query.get(aff.viewer_id)
                    if viewer:
                        print(f"      → {viewer.username} ({viewer.real_name}) 可查看 {name} 的数据")

    print("\n" + "=" * 80)
    print("分析完成")
    print("=" * 80)
