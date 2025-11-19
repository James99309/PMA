#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查settlement_orders表结构"""
import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

try:
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    print("=" * 60)
    print("检查 settlement_orders 表结构")
    print("=" * 60)

    # 查询表结构
    cursor.execute("""
        SELECT
            column_name,
            data_type,
            is_nullable,
            column_default
        FROM information_schema.columns
        WHERE table_schema = 'public'
        AND table_name = 'settlement_orders'
        ORDER BY ordinal_position
    """)

    columns = cursor.fetchall()

    print(f"\n找到 {len(columns)} 个字段:\n")

    has_currency = False
    for col in columns:
        nullable = "NULL" if col['is_nullable'] == 'YES' else "NOT NULL"
        default = f" DEFAULT {col['column_default']}" if col['column_default'] else ""
        print(f"  {col['column_name']:30} {col['data_type']:20} {nullable}{default}")

        if col['column_name'] == 'currency':
            has_currency = True

    print("\n" + "=" * 60)
    if has_currency:
        print("✅ currency 字段存在")
    else:
        print("❌ currency 字段不存在！")
        print("\n需要添加 currency 字段到 settlement_orders 表")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"\n❌ 错误: {str(e)}")
    import traceback
    traceback.print_exc()
