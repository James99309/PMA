#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查approvalstatus枚举类型的有效值"""
import psycopg2
from psycopg2.extras import RealDictCursor

DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

try:
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # 查询enum类型的值
    cursor.execute("""
        SELECT enumlabel
        FROM pg_enum
        WHERE enumtypid = (
            SELECT oid FROM pg_type WHERE typname = 'approvalstatus'
        )
        ORDER BY enumsortorder
    """)

    values = cursor.fetchall()
    print("approvalstatus 枚举类型的有效值：")
    for v in values:
        print(f"  - {v['enumlabel']}")

    cursor.close()
    conn.close()

except Exception as e:
    print(f"错误: {str(e)}")
