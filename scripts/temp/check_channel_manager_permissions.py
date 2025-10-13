#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查channel_manager角色的权限记录"""
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

from app import create_app, db
from app.models.role_permissions import RolePermission

def check_permissions():
    """检查channel_manager角色的权限记录"""
    app = create_app()
    with app.app_context():
        print("=" * 80)
        print("检查RolePermission表中channel_manager相关的记录...")
        print("=" * 80)

        # 查询所有包含channel_manager的记录（包括可能的空白字符变体）
        all_perms = RolePermission.query.filter(
            RolePermission.role.like('%channel_manager%')
        ).all()

        print(f"\n找到 {len(all_perms)} 条包含 'channel_manager' 的记录:\n")

        role_variants = {}
        for perm in all_perms:
            role_key = repr(perm.role)  # 使用repr显示隐藏字符
            if role_key not in role_variants:
                role_variants[role_key] = []
            role_variants[role_key].append(perm)

        for role_repr, perms in role_variants.items():
            print(f"角色: {role_repr} (长度: {len(eval(role_repr))})")
            print(f"  记录数: {len(perms)}")
            print(f"  模块: {[p.module for p in perms]}")
            print()

        # 检查是否有多个变体
        if len(role_variants) > 1:
            print("⚠️ 发现多个角色名变体！这会导致权限保存问题。")
            print("\n需要清理重复记录。")
        else:
            print("✓ 只有一个角色名版本")

        # 尝试精确查询
        print("\n" + "=" * 80)
        print("尝试精确查询 'channel_manager' (无空白字符):")
        print("=" * 80)
        exact_perms = RolePermission.query.filter_by(role='channel_manager').all()
        print(f"找到 {len(exact_perms)} 条记录")

        if exact_perms:
            print("\n权限详情:")
            for perm in exact_perms:
                print(f"  - {perm.module}: level={perm.permission_level}, "
                      f"view={perm.can_view}, create={perm.can_create}, "
                      f"edit={perm.can_edit}, delete={perm.can_delete}")

        return True

if __name__ == '__main__':
    success = check_permissions()
    sys.exit(0 if success else 1)
