#!/usr/bin/env python3
import psycopg2

DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

conn = psycopg2.connect(DB_URL)
cursor = conn.cursor()

print("=== tonglei和lihuawei的部门信息 ===")
cursor.execute("""
    SELECT id, username, real_name, department, company_name
    FROM users WHERE id IN (18, 15)
""")
for row in cursor.fetchall():
    print(f"ID={row[0]}, {row[2]}({row[1]}), 部门={row[3]}, 公司={row[4]}")

cursor.close()
conn.close()
