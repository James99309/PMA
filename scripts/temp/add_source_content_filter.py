#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为现有 customer 模块权限记录添加 source 内容筛选字段

背景：客户模块新增 source（来源）内容筛选维度后，
现有权限记录若缺少 source 字段，会导致用户无法看到任何客户数据。
本脚本为所有已有 content_filters 的 customer 权限记录补充 source 字段，
设为所有来源 key 的完整列表（保持现有行为不变）。
"""
import sys
import os


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
from app.models.dictionary import Dictionary


def get_all_report_source_keys():
    """从数据库获取所有 report_source 字典的 key 值"""
    items = Dictionary.query.filter_by(type='report_source', is_active=True)\
        .order_by(Dictionary.sort_order).all()
    keys = [d.key for d in items]
    return keys


def migrate_permissions():
    app = create_app()
    with app.app_context():
        source_keys = get_all_report_source_keys()
        if not source_keys:
            print("警告: 未找到任何 report_source 字典数据，请检查数据库")
            return

        print(f"报备来源 key 列表: {source_keys}")
        print()

        updated_count = 0

        # 1. 处理角色权限 (RolePermission)
        role_perms = RolePermission.query.filter_by(module='customer').all()
        print(f"找到 {len(role_perms)} 条 customer 角色权限记录")

        for rp in role_perms:
            if rp.content_filters and isinstance(rp.content_filters, dict):
                if 'source' not in rp.content_filters:
                    new_filters = dict(rp.content_filters)
                    new_filters['source'] = source_keys
                    rp.content_filters = new_filters
                    updated_count += 1
                    print(f"  [角色] {rp.role} - 已添加 source: {source_keys}")
                else:
                    print(f"  [角色] {rp.role} - 已有 source 配置，跳过")
            else:
                print(f"  [角色] {rp.role} - 无 content_filters，跳过")

        print()

        # 2. 处理用户个人权限 (Permission)
        user_perms = Permission.query.filter_by(module='customer').all()
        print(f"找到 {len(user_perms)} 条 customer 用户权限记录")

        for up in user_perms:
            if up.content_filters and isinstance(up.content_filters, dict):
                if 'source' not in up.content_filters:
                    new_filters = dict(up.content_filters)
                    new_filters['source'] = source_keys
                    up.content_filters = new_filters
                    updated_count += 1
                    print(f"  [用户] user_id={up.user_id} - 已添加 source: {source_keys}")
                else:
                    print(f"  [用户] user_id={up.user_id} - 已有 source 配置，跳过")
            else:
                print(f"  [用户] user_id={up.user_id} - 无 content_filters，跳过")

        print()
        print(f"共更新 {updated_count} 条记录")

        if updated_count > 0:
            confirm = input("确认提交更改？(y/n): ").strip().lower()
            if confirm == 'y':
                db.session.commit()
                print("已提交更改")
            else:
                db.session.rollback()
                print("已回滚更改")
        else:
            print("无需更新")


if __name__ == '__main__':
    migrate_permissions()
