#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查product_manager角色对product模块的权限配置
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
from app.models.role_permissions import RolePermission

def check_permissions():
    """检查product_manager的product模块权限"""
    app = create_app()

    with app.app_context():
        print("=" * 80)
        print("检查 product_manager 角色的 product 模块权限")
        print("=" * 80)

        # 查询product_manager角色的product模块权限
        perm = RolePermission.query.filter_by(
            role='product_manager',
            module='product'
        ).first()

        if not perm:
            print("\n❌ 未找到 product_manager 角色的 product 模块权限配置！")
            print("\n建议创建权限配置:")
            print("  - can_view: True")
            print("  - can_create: True")
            print("  - can_edit: True")
            print("  - can_delete: True")

            create = input("\n是否创建权限配置？(yes/no): ")
            if create.lower() == 'yes':
                new_perm = RolePermission(
                    role='product_manager',
                    module='product',
                    can_view=True,
                    can_create=True,
                    can_edit=True,
                    can_delete=True
                )
                db.session.add(new_perm)
                db.session.commit()
                print("✅ 权限配置已创建")
            else:
                print("❌ 已取消创建")
        else:
            print(f"\n找到权限配置:")
            print(f"  - can_view: {perm.can_view}")
            print(f"  - can_create: {perm.can_create}")
            print(f"  - can_edit: {perm.can_edit}")
            print(f"  - can_delete: {perm.can_delete}")

            if not perm.can_delete:
                print("\n⚠️  product_manager 角色没有 delete 权限！")
                fix = input("\n是否添加 delete 权限？(yes/no): ")
                if fix.lower() == 'yes':
                    perm.can_delete = True
                    db.session.commit()
                    print("✅ 已添加 delete 权限")
                else:
                    print("❌ 已取消修改")
            else:
                print("\n✅ product_manager 拥有完整的 product 模块权限（包括删除）")

if __name__ == '__main__':
    check_permissions()
