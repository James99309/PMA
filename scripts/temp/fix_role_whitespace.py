#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复Dictionary表中角色key的空白字符问题"""
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
from app.models.dictionary import Dictionary
from app.models.role_permissions import RolePermission

def fix_role_whitespace():
    """修复角色key中的空白字符"""
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("检查Dictionary表中角色key的空白字符...")
        print("=" * 60)

        # 获取所有角色字典项
        roles = Dictionary.query.filter_by(type='role').all()

        fixed_count = 0
        for role in roles:
            original_key = role.key
            # 去除首尾空白字符
            cleaned_key = original_key.strip()

            if original_key != cleaned_key:
                print(f"\n发现包含空白字符的角色key:")
                print(f"  原始key: '{original_key}' (repr: {repr(original_key)})")
                print(f"  清理后: '{cleaned_key}' (repr: {repr(cleaned_key)})")

                # 检查清理后的key是否已存在
                existing = Dictionary.query.filter_by(type='role', key=cleaned_key).first()
                if existing and existing.id != role.id:
                    print(f"  ⚠️  警告: 清理后的key '{cleaned_key}' 已存在，跳过")
                    continue

                # 更新role_permissions表中的引用
                permissions = RolePermission.query.filter_by(role=original_key).all()
                if permissions:
                    print(f"  更新 {len(permissions)} 条权限记录...")
                    for perm in permissions:
                        perm.role = cleaned_key

                # 更新Dictionary表
                role.key = cleaned_key
                fixed_count += 1
                print(f"  ✓ 已修复")

        if fixed_count > 0:
            try:
                db.session.commit()
                print(f"\n{'=' * 60}")
                print(f"✓ 成功修复 {fixed_count} 个角色key")
                print(f"{'=' * 60}")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ 提交失败: {str(e)}")
                return False
        else:
            print(f"\n{'=' * 60}")
            print("✓ 所有角色key正常，无需修复")
            print(f"{'=' * 60}")

        # 验证修复结果
        print("\n" + "=" * 60)
        print("当前所有角色key:")
        print("=" * 60)
        roles = Dictionary.query.filter_by(type='role').order_by(Dictionary.sort_order).all()
        for role in roles:
            status = "✓" if role.is_active else "✗"
            print(f"  {status} {role.key:20s} -> {role.value}")

        return True

if __name__ == '__main__':
    success = fix_role_whitespace()
    sys.exit(0 if success else 1)
