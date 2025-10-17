#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复权限数据不一致问题

问题：当permission_level='none'时，权限字段(can_view/can_edit等)应该全部为False
但由于前端只隐藏复选框未清空值，导致数据库中存在矛盾数据

解决方案：
1. 查找所有level='none'但权限字段为True的记录
2. 将这些记录的所有权限字段设为False
3. 同时处理Permission表和RolePermission表

创建时间：2025-10-17
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
from app.models.user import Permission
from app.models.role_permissions import RolePermission

def find_inconsistent_permissions():
    """查找所有不一致的权限记录"""
    print("=" * 80)
    print("查找数据不一致的权限记录")
    print("=" * 80)

    # 1. 查找Permission表中的不一致记录
    print("\n1. 检查Permission表（个人权限）...")
    personal_permissions = Permission.query.filter_by(permission_level='none').all()

    inconsistent_personal = []
    for perm in personal_permissions:
        has_any_permission = (perm.can_view or perm.can_edit or
                             perm.can_create or perm.can_delete or
                             getattr(perm, 'can_change_owner', False))
        if has_any_permission:
            inconsistent_personal.append(perm)
            print(f"   ❌ 用户ID {perm.user_id}, 模块 {perm.module}:")
            print(f"      level='none' 但权限为: view={perm.can_view}, edit={perm.can_edit}, "
                  f"create={perm.can_create}, delete={perm.can_delete}")

    if not inconsistent_personal:
        print("   ✅ 未发现不一致记录")
    else:
        print(f"\n   共发现 {len(inconsistent_personal)} 条不一致记录")

    # 2. 查找RolePermission表中的不一致记录
    print("\n2. 检查RolePermission表（角色权限）...")
    role_permissions = RolePermission.query.filter_by(permission_level='none').all()

    inconsistent_role = []
    for perm in role_permissions:
        has_any_permission = (perm.can_view or perm.can_edit or
                             perm.can_create or perm.can_delete or
                             getattr(perm, 'can_change_owner', False))
        if has_any_permission:
            inconsistent_role.append(perm)
            print(f"   ❌ 角色 {perm.role}, 模块 {perm.module}:")
            print(f"      level='none' 但权限为: view={perm.can_view}, edit={perm.can_edit}, "
                  f"create={perm.can_create}, delete={perm.can_delete}")

    if not inconsistent_role:
        print("   ✅ 未发现不一致记录")
    else:
        print(f"\n   共发现 {len(inconsistent_role)} 条不一致记录")

    return inconsistent_personal, inconsistent_role


def fix_inconsistent_permissions(inconsistent_personal, inconsistent_role, dry_run=True):
    """修复不一致的权限记录"""

    if not inconsistent_personal and not inconsistent_role:
        print("\n✅ 没有需要修复的记录")
        return

    mode_text = "【模拟模式】" if dry_run else "【执行模式】"
    print(f"\n{mode_text} 开始修复不一致记录...")
    print("=" * 80)

    fixed_count = 0

    # 1. 修复Permission表
    if inconsistent_personal:
        print(f"\n1. 修复Permission表 ({len(inconsistent_personal)}条记录)...")
        for perm in inconsistent_personal:
            print(f"   修复: 用户ID {perm.user_id}, 模块 {perm.module}")
            if not dry_run:
                perm.can_view = False
                perm.can_edit = False
                perm.can_create = False
                perm.can_delete = False
                if hasattr(perm, 'can_change_owner'):
                    perm.can_change_owner = False
                fixed_count += 1

    # 2. 修复RolePermission表
    if inconsistent_role:
        print(f"\n2. 修复RolePermission表 ({len(inconsistent_role)}条记录)...")
        for perm in inconsistent_role:
            print(f"   修复: 角色 {perm.role}, 模块 {perm.module}")
            if not dry_run:
                perm.can_view = False
                perm.can_edit = False
                perm.can_create = False
                perm.can_delete = False
                if hasattr(perm, 'can_change_owner'):
                    perm.can_change_owner = False
                fixed_count += 1

    # 3. 提交更改
    if not dry_run:
        try:
            db.session.commit()
            print(f"\n✅ 成功修复 {fixed_count} 条记录")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 修复失败: {str(e)}")
            raise
    else:
        print(f"\n💡 模拟模式：将修复 {len(inconsistent_personal) + len(inconsistent_role)} 条记录")
        print("   使用 --fix 参数执行实际修复")


def verify_fix():
    """验证修复结果"""
    print("\n" + "=" * 80)
    print("验证修复结果")
    print("=" * 80)

    # 验证Permission表
    personal_none = Permission.query.filter_by(permission_level='none').all()
    personal_issues = []
    for perm in personal_none:
        if (perm.can_view or perm.can_edit or perm.can_create or
            perm.can_delete or getattr(perm, 'can_change_owner', False)):
            personal_issues.append(perm)

    # 验证RolePermission表
    role_none = RolePermission.query.filter_by(permission_level='none').all()
    role_issues = []
    for perm in role_none:
        if (perm.can_view or perm.can_edit or perm.can_create or
            perm.can_delete or getattr(perm, 'can_change_owner', False)):
            role_issues.append(perm)

    if not personal_issues and not role_issues:
        print("\n✅ 验证通过！所有level='none'的记录权限字段均为False")
        return True
    else:
        print(f"\n❌ 验证失败！仍有{len(personal_issues) + len(role_issues)}条不一致记录")
        return False


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='修复permission_level=none时的权限数据不一致问题')
    parser.add_argument('--fix', action='store_true',
                       help='执行实际修复（默认为模拟模式）')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        # 1. 查找不一致记录
        inconsistent_personal, inconsistent_role = find_inconsistent_permissions()

        # 2. 修复不一致记录
        if args.fix:
            fix_inconsistent_permissions(inconsistent_personal, inconsistent_role, dry_run=False)

            # 3. 验证修复结果
            verify_fix()
        else:
            fix_inconsistent_permissions(inconsistent_personal, inconsistent_role, dry_run=True)
            print("\n" + "=" * 80)
            print("提示：这是模拟模式，未做任何修改")
            print("使用 python3 scripts/temp/fix_none_level_permission_data.py --fix 执行实际修复")
            print("=" * 80)


if __name__ == '__main__':
    main()
