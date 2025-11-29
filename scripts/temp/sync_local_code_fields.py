#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步 ProductCodeFieldOption 本地字段

功能：
将有 spec_option_id 的记录的本地 code 和 value 同步为 spec_option 的值

使用方法：
    python3 scripts/temp/sync_local_code_fields.py          # 预览模式
    python3 scripts/temp/sync_local_code_fields.py --execute # 执行模式
"""
import sys
import os
from datetime import datetime

# 路径修正 - 支持从任何位置运行
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

PROJECT_ROOT = get_project_root()
sys.path.insert(0, PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from app import create_app, db
from app.models.product_code import ProductCodeFieldOption, SpecificationOption


def sync_local_fields(dry_run=True):
    """
    同步本地字段

    Args:
        dry_run: True=只显示变更，不实际执行；False=执行变更
    """
    print("=" * 60)
    print(f"同步 ProductCodeFieldOption 本地字段 {'(预览模式)' if dry_run else '(执行模式)'}")
    print("=" * 60)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 统计
    stats = {
        'total': 0,
        'with_spec_option': 0,
        'without_spec_option': 0,
        'code_changed': 0,
        'value_changed': 0,
        'unchanged': 0
    }

    # 获取所有 ProductCodeFieldOption
    options = ProductCodeFieldOption.query.all()
    stats['total'] = len(options)

    print(f"总记录数: {stats['total']}")
    print()

    changes = []  # [(id, field_name, old_code, new_code, old_value, new_value)]

    for option in options:
        if option.spec_option_id and option.spec_option:
            stats['with_spec_option'] += 1

            old_code = option.code
            new_code = option.spec_option.code
            old_value = option.value
            new_value = option.spec_option.value

            code_changed = old_code != new_code
            value_changed = old_value != new_value

            if code_changed or value_changed:
                # 获取字段名称
                field_name = option.field.name if option.field else f"Field#{option.field_id}"
                changes.append((option.id, field_name, old_code, new_code, old_value, new_value))

                if code_changed:
                    stats['code_changed'] += 1
                if value_changed:
                    stats['value_changed'] += 1

                if not dry_run:
                    option.code = new_code
                    option.value = new_value
            else:
                stats['unchanged'] += 1
        else:
            stats['without_spec_option'] += 1

    # 显示变更详情
    if changes:
        print("变更详情:")
        print("-" * 60)
        for opt_id, field_name, old_code, new_code, old_value, new_value in changes:
            code_status = f"{old_code} → {new_code}" if old_code != new_code else f"{old_code} (不变)"
            value_status = f"{old_value} → {new_value}" if old_value != new_value else "(不变)"
            print(f"  [{field_name}] ID={opt_id}: code={code_status}, value={value_status}")
        print()

    # 提交事务
    if not dry_run and changes:
        db.session.commit()
        print("✅ 事务已提交")
        print()

    # 汇总
    print("=" * 60)
    print("统计汇总")
    print("=" * 60)
    print(f"总记录数: {stats['total']}")
    print(f"有 spec_option_id: {stats['with_spec_option']}")
    print(f"无 spec_option_id: {stats['without_spec_option']} (保留本地值)")
    print(f"code 变更: {stats['code_changed']}")
    print(f"value 变更: {stats['value_changed']}")
    print(f"无变更: {stats['unchanged']}")
    print()

    if dry_run:
        print("=" * 60)
        print("这是预览模式，未执行任何变更")
        print("确认无误后，请使用 --execute 参数执行")
        print("=" * 60)
    else:
        print("=" * 60)
        print("✅ 同步完成！")
        print("=" * 60)

    return stats, changes


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='同步 ProductCodeFieldOption 本地字段')
    parser.add_argument('--execute', action='store_true', help='执行同步（默认为预览模式）')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        dry_run = not args.execute
        sync_local_fields(dry_run=dry_run)
