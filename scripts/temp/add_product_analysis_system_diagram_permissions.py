#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
添加 product_analysis（植入分析）和 system_diagram（系统设计）权限模块

植入分析：仅查看权限，数据范围跟随各角色设置
系统设计：完整 CRUD 权限，继承原 product 模块的权限配置
"""
import sys, os

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
from app.models.permission_module import PermissionModule
from app.models.role_permissions import RolePermission


def run():
    app = create_app()
    with app.app_context():
        # ── 1. 修正序列（防止主键冲突） ──
        max_id = db.session.execute(db.text("SELECT MAX(id) FROM permission_modules")).scalar() or 0
        db.session.execute(db.text(f"SELECT setval('permission_modules_id_seq', {max_id})"))
        db.session.commit()

        # ── 2. 添加 permission_modules 记录 ──
        new_modules = [
            {
                'module_id': 'product_analysis',
                'name': '植入分析',
                'name_en': 'Product Analysis',
                'icon': 'analytics',
                'description': '产品植入分析数据查看（仅查看权限）',
                'description_en': 'Product implantation analysis (view only)',
                'group_name': '产品管理',
                'group_name_en': 'Product Management',
                'sort_order': 24,
            },
            {
                'module_id': 'system_diagram',
                'name': '系统设计',
                'name_en': 'System Diagram',
                'icon': 'draw',
                'description': '系统设计图管理',
                'description_en': 'System diagram management',
                'group_name': '产品管理',
                'group_name_en': 'Product Management',
                'sort_order': 25,
            },
        ]

        for mod_def in new_modules:
            existing = PermissionModule.query.filter_by(module_id=mod_def['module_id']).first()
            if existing:
                print(f"  ⏭️  模块 {mod_def['module_id']} 已存在，跳过")
            else:
                m = PermissionModule(**mod_def)
                db.session.add(m)
                print(f"  ✅ 添加模块: {mod_def['module_id']} ({mod_def['name']})")

        db.session.flush()

        # ── 2. 为所有角色添加 role_permissions 记录 ──

        # 获取所有已有角色
        existing_roles = set(
            r.role for r in RolePermission.query.with_entities(RolePermission.role).distinct().all()
        )
        print(f"\n  角色列表: {sorted(existing_roles)}")

        # --- product_analysis: 从 quotation 继承 can_view + permission_level，其余 False ---
        print("\n  === product_analysis (植入分析 - 仅查看) ===")
        for role in sorted(existing_roles):
            if RolePermission.query.filter_by(role=role, module='product_analysis').first():
                print(f"    ⏭️  {role}: 已存在")
                continue

            # 从 quotation 模块继承查看权限和数据范围
            quotation_perm = RolePermission.query.filter_by(role=role, module='quotation').first()
            if quotation_perm:
                can_view = quotation_perm.can_view
                level = quotation_perm.permission_level
            else:
                can_view = False
                level = 'personal'

            rp = RolePermission(
                role=role,
                module='product_analysis',
                can_view=can_view,
                can_create=False,
                can_edit=False,
                can_delete=False,
                permission_level=level,
            )
            db.session.add(rp)
            print(f"    ✅ {role}: view={can_view}, level={level}")

        # --- system_diagram: 从 product 继承完整 CRUD ---
        print("\n  === system_diagram (系统设计 - 完整 CRUD) ===")
        for role in sorted(existing_roles):
            if RolePermission.query.filter_by(role=role, module='system_diagram').first():
                print(f"    ⏭️  {role}: 已存在")
                continue

            # 从 product 模块继承权限
            product_perm = RolePermission.query.filter_by(role=role, module='product').first()
            if product_perm:
                rp = RolePermission(
                    role=role,
                    module='system_diagram',
                    can_view=product_perm.can_view,
                    can_create=product_perm.can_create,
                    can_edit=product_perm.can_edit,
                    can_delete=product_perm.can_delete,
                    permission_level=product_perm.permission_level,
                )
            else:
                rp = RolePermission(
                    role=role,
                    module='system_diagram',
                    can_view=True,
                    can_create=False,
                    can_edit=False,
                    can_delete=False,
                    permission_level='system',
                )
            db.session.add(rp)
            print(f"    ✅ {role}: view={rp.can_view} create={rp.can_create} edit={rp.can_edit} delete={rp.can_delete} level={rp.permission_level}")

        db.session.commit()
        print("\n✅ 权限模块初始化完成")


if __name__ == '__main__':
    run()
