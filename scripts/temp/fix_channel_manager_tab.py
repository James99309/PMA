#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复SP8D云端数据库中channel_manager角色的制表符问题

问题: 字典表和role_permissions表中的channel_manager包含制表符\t
导致: 前端发送'channel_manager'无法匹配'channel_manager\t',返回404错误
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

# 设置SP8D数据库连接
os.environ['DATABASE_URL'] = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

from app import create_app, db
from app.models.dictionary import Dictionary
from app.models.role_permissions import RolePermission

app = create_app()

with app.app_context():
    print("=" * 80)
    print("修复SP8D云端数据库中的channel_manager制表符问题")
    print("=" * 80)

    try:
        # 1. 检查并修复字典表
        print("\n【步骤1】检查字典表...")
        dict_with_tab = Dictionary.query.filter_by(type='role', key='channel_manager\t').first()

        if dict_with_tab:
            print(f"  找到脏数据: key={repr(dict_with_tab.key)} value={dict_with_tab.value}")
            dict_with_tab.key = 'channel_manager'
            print(f"  ✅ 已修复字典表: 'channel_manager\\t' → 'channel_manager'")
        else:
            print("  字典表中未找到包含制表符的channel_manager")

        # 2. 检查并修复role_permissions表
        print("\n【步骤2】检查role_permissions表...")
        role_perms_with_tab = RolePermission.query.filter_by(role='channel_manager\t').all()

        if role_perms_with_tab:
            print(f"  找到 {len(role_perms_with_tab)} 条脏数据记录")

            # 检查是否存在干净的channel_manager记录
            clean_perms = RolePermission.query.filter_by(role='channel_manager').all()
            if clean_perms:
                print(f"  ⚠️  发现 {len(clean_perms)} 条干净的'channel_manager'记录已存在")
                print(f"  策略: 直接删除带制表符的记录 (会导致唯一键冲突)")
                for perm in role_perms_with_tab:
                    db.session.delete(perm)
                print(f"  ✅ 已删除role_permissions表中的脏数据: {len(role_perms_with_tab)} 条记录")
            else:
                # 如果没有干净的记录,可以直接更新
                for perm in role_perms_with_tab:
                    perm.role = 'channel_manager'
                print(f"  ✅ 已修复role_permissions表: {len(role_perms_with_tab)} 条记录")
        else:
            print("  role_permissions表中未找到包含制表符的channel_manager")

        # 3. 提交更改
        print("\n【步骤3】提交更改...")
        db.session.commit()
        print("  ✅ 所有更改已成功提交到数据库")

        # 4. 验证修复结果
        print("\n【步骤4】验证修复结果...")
        clean_dict = Dictionary.query.filter_by(type='role', key='channel_manager').first()
        if clean_dict:
            print(f"  ✅ 字典表验证成功: key={repr(clean_dict.key)} value={clean_dict.value}")
        else:
            print("  ⚠️  字典表验证失败: 未找到'channel_manager'")

        clean_perms = RolePermission.query.filter_by(role='channel_manager').all()
        print(f"  ✅ role_permissions表验证成功: 找到 {len(clean_perms)} 条'channel_manager'记录")

        dirty_dict = Dictionary.query.filter_by(type='role', key='channel_manager\t').first()
        dirty_perms = RolePermission.query.filter_by(role='channel_manager\t').all()

        if dirty_dict or dirty_perms:
            print(f"  ⚠️  警告: 仍有脏数据存在 (dict:{dirty_dict is not None}, perms:{len(dirty_perms)})")
        else:
            print("  ✅ 确认: 数据库中已无包含制表符的channel_manager")

        print("\n" + "=" * 80)
        print("✅ 修复完成!")
        print("=" * 80)

    except Exception as e:
        db.session.rollback()
        print(f"\n❌ 修复失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
