#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查 zhouzc 用户的客户模块权限配置"""
import sys, os

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
os.chdir(get_project_root())

from app import create_app, db
from app.models.user import User, Permission
from app.models.role_permissions import RolePermission

app = create_app()

with app.app_context():
    # 查找 zhouzc 用户
    user = User.query.filter_by(username='zhouzc').first()

    if not user:
        print("❌ 未找到用户 zhouzc")
        sys.exit(1)

    print(f"=" * 60)
    print(f"用户信息")
    print(f"=" * 60)
    print(f"用户名: {user.username}")
    print(f"真实姓名: {user.real_name}")
    print(f"角色: {user.role}")
    print(f"部门: {user.department}")
    print(f"公司: {user.company_name}")

    print(f"\n{'=' * 60}")
    print(f"角色权限 (RolePermission) - 基础权限")
    print(f"{'=' * 60}")

    # 查看角色在客户模块的权限
    role_perm = RolePermission.query.filter_by(role=user.role, module='customer').first()
    if role_perm:
        print(f"角色: {role_perm.role}")
        print(f"模块: {role_perm.module}")
        print(f"  - can_view: {role_perm.can_view}")
        print(f"  - can_create: {role_perm.can_create}")
        print(f"  - can_edit: {role_perm.can_edit}")
        print(f"  - can_delete: {role_perm.can_delete}")
        print(f"  - permission_level: {getattr(role_perm, 'permission_level', 'N/A')}")
    else:
        print(f"❌ 角色 '{user.role}' 没有 customer 模块的角色权限配置")

    print(f"\n{'=' * 60}")
    print(f"个人权限 (Permission) - 覆盖权限")
    print(f"{'=' * 60}")

    # 查看用户的个人权限
    personal_perm = Permission.query.filter_by(user_id=user.id, module='customer').first()
    if personal_perm:
        print(f"用户ID: {personal_perm.user_id}")
        print(f"模块: {personal_perm.module}")
        print(f"  - can_view: {personal_perm.can_view}")
        print(f"  - can_create: {personal_perm.can_create}  ← 新建按钮依赖此权限")
        print(f"  - can_edit: {personal_perm.can_edit}")
        print(f"  - can_delete: {personal_perm.can_delete}")
        print(f"  - permission_level: {getattr(personal_perm, 'permission_level', 'N/A')}")

        if not personal_perm.can_create:
            print(f"\n⚠️  问题发现: can_create = False，所以新建按钮不显示")
            print(f"\n💡 解决方案: 在权限管理中为该用户的客户模块启用「创建」权限")
    else:
        print(f"❌ 该用户没有 customer 模块的个人权限配置")
        print(f"   将使用角色权限")

    print(f"\n{'=' * 60}")
    print(f"最终权限检查结果")
    print(f"{'=' * 60}")

    # 使用 has_permission 方法检查实际权限
    can_view = user.has_permission('customer', 'view')
    can_create = user.has_permission('customer', 'create')
    can_edit = user.has_permission('customer', 'edit')
    can_delete = user.has_permission('customer', 'delete')

    print(f"customer.view: {can_view}")
    print(f"customer.create: {can_create}  ← 控制「新建」按钮")
    print(f"customer.edit: {can_edit}")
    print(f"customer.delete: {can_delete}")

    if not can_create:
        print(f"\n" + "=" * 60)
        print(f"❌ 确认问题: has_permission('customer', 'create') = False")
        print(f"   这就是为什么新建按钮不显示的原因")
        print(f"\n📋 修复方法:")
        print(f"   方法1: 在系统权限管理中，为 zhouzc 用户的客户模块勾选「创建」权限")
        print(f"   方法2: 运行以下代码修复:")
        print(f"""
# 修复代码
from app.models.user import Permission
from app import db

perm = Permission.query.filter_by(user_id={user.id}, module='customer').first()
if perm:
    perm.can_create = True
    db.session.commit()
    print("已启用创建权限")
""")
