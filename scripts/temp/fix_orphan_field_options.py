#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理 product_code_field_options 表中的孤儿记录
修复 field_id 为 NULL 的记录
"""
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
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("检查 product_code_field_options 表中的孤儿记录...")

    # 查询 field_id 为 NULL 的记录
    orphan_records = db.session.execute(
        text("""
            SELECT id, value, code, description
            FROM product_code_field_options
            WHERE field_id IS NULL
        """)
    ).fetchall()

    if orphan_records:
        print(f"\n发现 {len(orphan_records)} 条孤儿记录（field_id 为 NULL）：")
        print("-" * 80)
        for record in orphan_records:
            print(f"ID: {record[0]}, 值: {record[1]}, 编码: {record[2]}, 描述: {record[3]}")
        print("-" * 80)

        # 询问是否删除
        confirm = input(f"\n是否删除这 {len(orphan_records)} 条孤儿记录？(yes/no): ").strip().lower()

        if confirm == 'yes':
            # 删除孤儿记录
            result = db.session.execute(
                text("DELETE FROM product_code_field_options WHERE field_id IS NULL")
            )
            db.session.commit()
            print(f"✅ 已删除 {result.rowcount} 条孤儿记录")
        else:
            print("❌ 取消删除操作")
    else:
        print("✅ 未发现孤儿记录，数据库状态正常")
