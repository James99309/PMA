#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查 tonglei 账户的部门负责人标志
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

app = create_app()

with app.app_context():
    # 查询 tonglei 账户
    tonglei = User.query.filter_by(username='tonglei').first()

    if not tonglei:
        print("❌ 未找到 tonglei 账户")
        sys.exit(1)

    print("=" * 60)
    print(f"📋 tonglei 账户信息")
    print("=" * 60)
    print(f"用户ID: {tonglei.id}")
    print(f"用户名: {tonglei.username}")
    print(f"真实姓名: {tonglei.real_name}")
    print(f"角色: {tonglei.role}")
    print(f"公司: {tonglei.company_name}")
    print(f"部门: {tonglei.department}")
    print(f"🔍 is_department_manager: {tonglei.is_department_manager}")
    print("=" * 60)

    # 检查报销单权限配置
    from app.models.user import Permission
    expense_perm = Permission.query.filter_by(
        user_id=tonglei.id,
        module='expense'
    ).first()

    if expense_perm:
        print(f"\n💼 报销单权限配置:")
        print(f"  - 查看权限: {expense_perm.can_view}")
        print(f"  - 编辑权限: {expense_perm.can_edit}")
        print(f"  - 删除权限: {expense_perm.can_delete}")
        print(f"  - 权限级别: {expense_perm.permission_level}")
        print(f"  - 内容过滤: {expense_perm.content_filters}")
    else:
        print(f"\n❌ 未找到报销单权限配置")

    # 检查是否有归属关系
    from app.models.user import Affiliation
    affiliations = Affiliation.query.filter_by(viewer_id=tonglei.id).all()

    if affiliations:
        print(f"\n🔗 归属关系:")
        for aff in affiliations:
            owner = User.query.get(aff.owner_id)
            if owner:
                print(f"  - 可查看用户: {owner.username} ({owner.real_name})")
    else:
        print(f"\n✅ 无归属关系")

    print("\n" + "=" * 60)
