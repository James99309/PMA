#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""为云端settlement_orders表添加currency字段"""
import psycopg2
from psycopg2.extras import RealDictCursor

CLOUD_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

try:
    conn = psycopg2.connect(CLOUD_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    print("=" * 60)
    print("为 settlement_orders 表添加 currency 字段")
    print("=" * 60)

    # 检查字段是否已存在
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'settlement_orders'
            AND column_name = 'currency'
        )
    """)

    exists = cursor.fetchone()['exists']

    if exists:
        print("\n⚠️  currency 字段已存在，无需添加")
    else:
        print("\n正在添加 currency 字段...")

        # 添加字段
        cursor.execute("""
            ALTER TABLE settlement_orders
            ADD COLUMN currency VARCHAR(10) DEFAULT 'CNY'
        """)

        # 添加注释
        cursor.execute("""
            COMMENT ON COLUMN settlement_orders.currency IS '货币类型'
        """)

        conn.commit()
        print("✅ currency 字段添加成功！")

        # 验证添加
        cursor.execute("""
            SELECT column_name, data_type, column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
            AND table_name = 'settlement_orders'
            AND column_name = 'currency'
        """)

        result = cursor.fetchone()
        if result:
            print(f"\n验证结果:")
            print(f"  字段名: {result['column_name']}")
            print(f"  类型: {result['data_type']}")
            print(f"  默认值: {result['column_default']}")

        # 检查现有记录数
        cursor.execute("SELECT COUNT(*) as count FROM settlement_orders")
        count = cursor.fetchone()['count']
        print(f"\n表中现有记录数: {count}")

        if count > 0:
            print(f"✅ 这些记录的 currency 字段将自动设置为默认值 'CNY'")

    cursor.close()
    conn.close()

    print("\n" + "=" * 60)
    print("操作完成！")
    print("=" * 60)

except Exception as e:
    print(f"\n❌ 错误: {str(e)}")
    import traceback
    traceback.print_exc()
    if conn:
        conn.rollback()
