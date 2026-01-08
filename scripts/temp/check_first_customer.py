#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查SP8D数据库第一个客户ID"""

from sqlalchemy import create_engine, text

DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'
engine = create_engine(DB_URL)

with engine.connect() as conn:
    print("=" * 70)
    print("SP8D数据库 companies 表前10个客户")
    print("=" * 70)

    result = conn.execute(text("""
        SELECT id, company_name, company_code, is_deleted
        FROM companies
        ORDER BY id
        LIMIT 10
    """))

    for row in result:
        status = "已删除" if row[3] else "有效"
        print(f"ID: {row[0]:<5} | {status:<6} | {row[2]:<15} | {row[1]}")

    print("\n" + "=" * 70)
    print("第一个未删除的客户")
    print("=" * 70)

    result = conn.execute(text("""
        SELECT id, company_name, company_code
        FROM companies
        WHERE is_deleted = false
        ORDER BY id
        LIMIT 1
    """))

    row = result.fetchone()
    if row:
        print(f"ID: {row[0]}")
        print(f"名称: {row[1]}")
        print(f"代码: {row[2]}")

    print("\n" + "=" * 70)
    print("查找customer_id=382的创建时间和其他信息")
    print("=" * 70)

    result = conn.execute(text("""
        SELECT id, company_name, company_code, created_at, owner_id
        FROM companies
        WHERE id = 382
    """))

    row = result.fetchone()
    if row:
        print(f"ID: {row[0]}")
        print(f"名称: {row[1]}")
        print(f"代码: {row[2]}")
        print(f"创建时间: {row[3]}")
        print(f"所有者ID: {row[4]}")
