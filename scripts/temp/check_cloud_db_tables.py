#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查云端数据库表状态"""
import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

try:
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    print("=" * 60)
    print("🔍 检查云端SP8D数据库状态")
    print("=" * 60)

    # 检查所有表
    cursor.execute("""
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
        AND table_type = 'BASE TABLE'
        ORDER BY table_schema, table_name
    """)
    tables = cursor.fetchall()

    print(f"\n找到 {len(tables)} 个表:\n")

    current_schema = None
    for table in tables:
        if current_schema != table['table_schema']:
            current_schema = table['table_schema']
            print(f"\n[Schema: {current_schema}]")

        # 获取行数
        try:
            cursor.execute(f"""
                SELECT COUNT(*) as count
                FROM "{table['table_schema']}"."{table['table_name']}"
            """)
            count = cursor.fetchone()['count']
            print(f"  ✅ {table['table_name']}: {count} 行")
        except Exception as e:
            print(f"  ❌ {table['table_name']}: 无法访问 - {str(e)}")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"\n❌ 错误: {str(e)}")
    import traceback
    traceback.print_exc()
