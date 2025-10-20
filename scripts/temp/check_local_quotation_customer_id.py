#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查本地quotations表的customer_id字段约束"""
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
from sqlalchemy import text, inspect

app = create_app()

with app.app_context():
    inspector = inspect(db.engine)

    print("=" * 80)
    print("本地 quotations 表结构")
    print("=" * 80)

    cols = inspector.get_columns('quotations')

    print(f"\n{'字段名':<30} {'类型':<25} {'可空':<10} {'默认值':<20}")
    print("-" * 85)

    for col in cols:
        nullable_display = "YES" if col['nullable'] else "NO"
        default_display = str(col.get('default', '-'))
        print(f"{col['name']:<30} {str(col['type']):<25} {nullable_display:<10} {default_display:<20}")

    # 重点检查customer_id
    print("\n" + "=" * 80)
    print("customer_id 字段详细信息")
    print("=" * 80)

    customer_id_col = next((col for col in cols if col['name'] == 'customer_id'), None)

    if customer_id_col:
        print(f"字段名: customer_id")
        print(f"类型: {customer_id_col['type']}")
        print(f"可空: {'YES (可以为NULL)' if customer_id_col['nullable'] else 'NO (NOT NULL约束)'}")
        print(f"默认值: {customer_id_col.get('default', '无')}")
    else:
        print("⚠️ customer_id 字段不存在！")

    # 检查现有数据
    print("\n" + "=" * 80)
    print("现有数据检查")
    print("=" * 80)

    result = db.session.execute(text("""
        SELECT
            COUNT(*) as total,
            COUNT(customer_id) as with_customer,
            COUNT(*) FILTER (WHERE customer_id IS NULL) as null_count
        FROM quotations
    """))

    row = result.fetchone()
    print(f"总报价单数: {row[0]}")
    print(f"有customer_id的: {row[1]}")
    print(f"customer_id为NULL的: {row[2]}")
