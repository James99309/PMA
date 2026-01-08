#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看客户ID 4 和 382 的信息"""

from sqlalchemy import create_engine, text

DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'
engine = create_engine(DB_URL)

with engine.connect() as conn:
    print("=" * 70)
    print("客户信息对比")
    print("=" * 70)

    for cid in [4, 382]:
        result = conn.execute(text("""
            SELECT id, company_name, company_code, country, region, industry
            FROM companies WHERE id = :cid
        """), {"cid": cid})
        row = result.fetchone()
        if row:
            print(f"\n客户ID: {row[0]}")
            print(f"  公司名称: {row[1]}")
            print(f"  公司代码: {row[2]}")
            print(f"  国家: {row[3]}")
            print(f"  地区: {row[4]}")
            print(f"  行业: {row[5]}")

    print("\n" + "=" * 70)

    # 统计备份表中的数据
    print("\n备份表 quotations_customer_backup_20251025_214040 统计：")
    result = conn.execute(text("""
        SELECT customer_id, COUNT(*) as cnt
        FROM quotations_customer_backup_20251025_214040
        GROUP BY customer_id
        ORDER BY cnt DESC
        LIMIT 10
    """))
    for row in result:
        print(f"  customer_id={row[0]}: {row[1]} 条记录")

    # 统计当前quotations表中的数据
    print("\n当前 quotations 表统计：")
    result = conn.execute(text("""
        SELECT customer_id, COUNT(*) as cnt
        FROM quotations
        GROUP BY customer_id
        ORDER BY cnt DESC
        LIMIT 10
    """))
    for row in result:
        print(f"  customer_id={row[0]}: {row[1]} 条记录")
