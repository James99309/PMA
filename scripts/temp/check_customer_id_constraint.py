#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查quotations.customer_id字段的约束"""

from sqlalchemy import create_engine, text

DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'
engine = create_engine(DB_URL)

with engine.connect() as conn:
    print("=" * 70)
    print("检查 quotations.customer_id 字段约束")
    print("=" * 70)

    # 检查字段是否可空
    result = conn.execute(text("""
        SELECT
            column_name,
            is_nullable,
            column_default,
            data_type
        FROM information_schema.columns
        WHERE table_name = 'quotations'
        AND column_name = 'customer_id'
    """))

    row = result.fetchone()
    if row:
        print(f"\n字段名: {row[0]}")
        print(f"是否可空: {row[1]} ({'可以为NULL' if row[1] == 'YES' else '不允许NULL ❌'})")
        print(f"默认值: {row[2]}")
        print(f"数据类型: {row[3]}")

    # 检查外键约束
    print("\n外键约束:")
    result = conn.execute(text("""
        SELECT
            tc.constraint_name,
            kcu.column_name,
            ccu.table_name AS foreign_table,
            ccu.column_name AS foreign_column
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage ccu
            ON ccu.constraint_name = tc.constraint_name
        WHERE tc.table_name = 'quotations'
        AND tc.constraint_type = 'FOREIGN KEY'
        AND kcu.column_name = 'customer_id'
    """))

    rows = result.fetchall()
    if rows:
        for row in rows:
            print(f"  约束名: {row[0]}")
            print(f"  关联: {row[1]} -> {row[2]}.{row[3]}")
    else:
        print("  无外键约束")
