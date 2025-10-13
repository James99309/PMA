#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清理RolePermission表中角色名的空白字符"""
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

def clean_role_whitespace():
    """清理角色名中的空白字符"""
    app = create_app()
    with app.app_context():
        print("=" * 80)
        print("清理RolePermission表中角色名的空白字符...")
        print("=" * 80)

        # 获取所有权限记录
        all_perms = RolePermission.query.all()

        # 按角色分组，找出需要清理的记录
        role_groups = {}
        for perm in all_perms:
            original_role = perm.role
            cleaned_role = original_role.strip()

            if cleaned_role not in role_groups:
                role_groups[cleaned_role] = {'clean': [], 'dirty': []}

            if original_role != cleaned_role:
                role_groups[cleaned_role]['dirty'].append(perm)
            else:
                role_groups[cleaned_role]['clean'].append(perm)

        # 显示发现的问题
        dirty_roles = [role for role, data in role_groups.items() if data['dirty']]

        if not dirty_roles:
            print("\n✓ 所有角色名都是干净的，无需清理")
            return True

        print(f"\n发现 {len(dirty_roles)} 个角色有空白字符问题:\n")

        for role in dirty_roles:
            data = role_groups[role]
            print(f"角色: '{role}'")
            print(f"  - 干净记录: {len(data['clean'])} 条")
            print(f"  - 脏记录: {len(data['dirty'])} 条")

            # 显示脏记录的详细信息
            for perm in data['dirty']:
                print(f"    → '{perm.role}' (repr: {repr(perm.role)}) - 模块: {perm.module}")

        # 询问用户确认
        print("\n" + "=" * 80)
        print("清理方案: 删除所有带空白字符的脏记录")
        print("=" * 80)
        response = input("\n是否继续清理? (yes/no): ")

        if response.lower() != 'yes':
            print("取消清理")
            return False

        # 执行清理
        deleted_count = 0
        for role in dirty_roles:
            data = role_groups[role]
            for perm in data['dirty']:
                db.session.delete(perm)
                deleted_count += 1
                print(f"删除: {repr(perm.role)} - {perm.module}")

        try:
            db.session.commit()
            print(f"\n✓ 成功删除 {deleted_count} 条脏记录")

            # 验证清理结果
            print("\n" + "=" * 80)
            print("验证清理结果...")
            print("=" * 80)

            remaining = RolePermission.query.all()
            dirty_remaining = [p for p in remaining if p.role != p.role.strip()]

            if dirty_remaining:
                print(f"⚠️ 仍有 {len(dirty_remaining)} 条脏记录")
                return False
            else:
                print("✓ 所有记录已清理完成")

                # 显示各角色的记录数
                print("\n当前角色权限记录统计:")
                from collections import Counter
                role_counts = Counter(p.role for p in remaining)
                for role, count in sorted(role_counts.items()):
                    print(f"  - {role}: {count} 条")

                return True

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 清理失败: {str(e)}")
            return False

if __name__ == '__main__':
    success = clean_role_whitespace()
    sys.exit(0 if success else 1)
