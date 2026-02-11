#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
阶段1: 清理产品分类的指标引用

操作流程：
1. 备份当前状态到 _backup 表
2. 将 ProductCodeFieldOption 引用的 SpecificationOption 值写回本地字段
3. 断开 spec_option_id 引用
4. 清空所有 SpecificationOption（字典指标全部清除）

产品编码功能不受影响：断开引用后 effective_value/effective_code 回退到本地 value/code

使用方法:
    python scripts/temp/cleanup_product_code_spec_options.py [--dry-run | --execute]
"""
import sys
import os
import argparse

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
from sqlalchemy import text


def cleanup(dry_run=True):
    """清理产品分类的指标引用"""
    print("=" * 60)
    print("阶段1: 清理产品分类的指标引用")
    print("=" * 60)

    if dry_run:
        print("【试运行模式】不会实际修改数据\n")
    else:
        print("【执行模式】将修改数据库\n")

    # Step 0: 检查当前状态
    result = db.session.execute(text("""
        SELECT COUNT(*) FROM product_code_field_options WHERE spec_option_id IS NOT NULL
    """))
    linked_count = result.scalar()

    result = db.session.execute(text("SELECT COUNT(*) FROM specification_options"))
    spec_option_count = result.scalar()

    result = db.session.execute(text("SELECT COUNT(*) FROM specification_dictionary"))
    spec_dict_count = result.scalar()

    print(f"当前状态:")
    print(f"  - ProductCodeFieldOption 引用 spec_option: {linked_count} 条")
    print(f"  - SpecificationOption 总数: {spec_option_count} 条")
    print(f"  - SpecificationDictionary 总数: {spec_dict_count} 条")
    print()

    if linked_count == 0 and spec_option_count == 0:
        print("已经是干净状态，无需清理")
        return

    # 显示将要写回的数据样本
    result = db.session.execute(text("""
        SELECT pcfo.id, pcfo.value AS local_value, pcfo.code AS local_code,
               so.value AS spec_value, so.code AS spec_code,
               sd.name AS spec_name
        FROM product_code_field_options pcfo
        JOIN specification_options so ON pcfo.spec_option_id = so.id
        JOIN specification_dictionary sd ON so.spec_id = sd.id
        LIMIT 10
    """))
    rows = result.fetchall()

    if rows:
        print("引用的指标样本（前10条）:")
        for row in rows:
            local_info = f"local=({row.local_value}, {row.local_code})"
            spec_info = f"spec=({row.spec_value}, {row.spec_code})"
            print(f"  ID {row.id}: {row.spec_name} | {local_info} | {spec_info}")
        print()

    if dry_run:
        print("--- 试运行结束，以下操作将在 --execute 模式执行 ---")
        print("  1. 创建 _backup_specification_options 备份表")
        print("  2. 创建 _backup_pcfo_spec_refs 备份表")
        print(f"  3. 将 {linked_count} 条引用的 value/code 写回本地字段")
        print(f"  4. 断开 {linked_count} 条 spec_option_id 引用")
        print(f"  5. 删除 {spec_option_count} 条 SpecificationOption 记录")
        return

    # === 执行模式 ===

    # Step 1: 备份
    print("Step 1: 创建备份表...")
    db.session.execute(text("DROP TABLE IF EXISTS _backup_specification_options"))
    db.session.execute(text(
        "CREATE TABLE _backup_specification_options AS SELECT * FROM specification_options"
    ))
    print(f"  已备份 specification_options ({spec_option_count} 条)")

    db.session.execute(text("DROP TABLE IF EXISTS _backup_pcfo_spec_refs"))
    db.session.execute(text("""
        CREATE TABLE _backup_pcfo_spec_refs AS
        SELECT id, spec_option_id, value, code
        FROM product_code_field_options
        WHERE spec_option_id IS NOT NULL
    """))
    print(f"  已备份 product_code_field_options 引用记录 ({linked_count} 条)")

    # Step 2: 将引用的 value/code 写回本地字段
    print("\nStep 2: 写回本地字段...")
    result = db.session.execute(text("""
        UPDATE product_code_field_options pcfo
        SET value = so.value, code = so.code
        FROM specification_options so
        WHERE pcfo.spec_option_id = so.id
          AND pcfo.spec_option_id IS NOT NULL
    """))
    print(f"  已更新 {result.rowcount} 条记录的本地 value/code")

    # Step 3: 断开引用
    print("\nStep 3: 断开 spec_option_id 引用...")
    result = db.session.execute(text("""
        UPDATE product_code_field_options
        SET spec_option_id = NULL
        WHERE spec_option_id IS NOT NULL
    """))
    print(f"  已清除 {result.rowcount} 条记录的 spec_option_id")

    # Step 4: 清空 SpecificationOption
    print("\nStep 4: 清空 specification_options...")
    result = db.session.execute(text("DELETE FROM specification_options"))
    print(f"  已删除 {result.rowcount} 条 SpecificationOption 记录")

    db.session.commit()
    print("\n提交成功!")

    # 验证
    print("\n=== 验证 ===")
    result = db.session.execute(text(
        "SELECT COUNT(*) FROM product_code_field_options WHERE spec_option_id IS NOT NULL"
    ))
    remaining_refs = result.scalar()
    print(f"  剩余引用数: {remaining_refs} (应为 0)")

    result = db.session.execute(text("SELECT COUNT(*) FROM specification_options"))
    remaining_opts = result.scalar()
    print(f"  剩余 SpecificationOption: {remaining_opts} (应为 0)")

    # 抽查本地字段是否有值
    result = db.session.execute(text("""
        SELECT COUNT(*) FROM product_code_field_options
        WHERE value IS NOT NULL AND value != ''
    """))
    with_value = result.scalar()
    result = db.session.execute(text("SELECT COUNT(*) FROM product_code_field_options"))
    total = result.scalar()
    print(f"  有本地 value 的记录: {with_value}/{total}")

    print("\n阶段1完成!")


def main():
    parser = argparse.ArgumentParser(description='清理产品分类的指标引用')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--dry-run', action='store_true', help='试运行（不修改数据）')
    group.add_argument('--execute', action='store_true', help='执行清理')
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        cleanup(dry_run=args.dry_run)


if __name__ == '__main__':
    main()
