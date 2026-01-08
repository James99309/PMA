#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查客户ID=4和ID=382的信息"""
import psycopg2

DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

def main():
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()

    print("=== 客户 ID=4 的信息 ===")
    cursor.execute("""
        SELECT c.id, c.company_name, c.company_code, c.owner_id, u.real_name
        FROM companies c
        LEFT JOIN users u ON c.owner_id = u.id
        WHERE c.id = 4
    """)
    customer4 = cursor.fetchone()
    if customer4:
        print(f"客户ID: {customer4[0]}")
        print(f"客户名称: {customer4[1]}")
        print(f"客户代码: {customer4[2]}")
        print(f"所有者: {customer4[4]} (ID={customer4[3]})")
    else:
        print("客户ID=4不存在")

    print("\n=== 客户 ID=382 的信息 ===")
    cursor.execute("""
        SELECT c.id, c.company_name, c.company_code, c.owner_id, u.real_name
        FROM companies c
        LEFT JOIN users u ON c.owner_id = u.id
        WHERE c.id = 382
    """)
    customer382 = cursor.fetchone()
    if customer382:
        print(f"客户ID: {customer382[0]}")
        print(f"客户名称: {customer382[1]}")
        print(f"客户代码: {customer382[2]}")
        print(f"所有者: {customer382[4]} (ID={customer382[3]})")

    print("\n=== 客户 ID=381 的信息 (总公司) ===")
    cursor.execute("""
        SELECT c.id, c.company_name, c.company_code, c.owner_id, u.real_name
        FROM companies c
        LEFT JOIN users u ON c.owner_id = u.id
        WHERE c.id = 381
    """)
    customer381 = cursor.fetchone()
    if customer381:
        print(f"客户ID: {customer381[0]}")
        print(f"客户名称: {customer381[1]}")
        print(f"客户代码: {customer381[2]}")
        print(f"所有者: {customer381[4]} (ID={customer381[3]})")

    # 检查是否有数据迁移把 customer_id=4 批量改成了其他值
    print("\n=== 备份表中 customer_id=4 的报价单数量 ===")
    cursor.execute("""
        SELECT COUNT(*) FROM quotations_customer_backup_20251025_214040
        WHERE customer_id = 4
    """)
    count = cursor.fetchone()[0]
    print(f"备份中 customer_id=4 的报价单数量: {count}")

    # 检查这些报价单现在的 customer_id
    print("\n=== 备份中 customer_id=4 的报价单，现在的状态 ===")
    cursor.execute("""
        SELECT b.id, b.quotation_number, b.customer_id as old_customer_id,
               q.customer_id as new_customer_id,
               c.company_name as new_customer_name
        FROM quotations_customer_backup_20251025_214040 b
        JOIN quotations q ON b.id = q.id
        LEFT JOIN companies c ON q.customer_id = c.id
        WHERE b.customer_id = 4
        ORDER BY b.id
    """)
    changed = cursor.fetchall()
    for row in changed:
        print(f"报价单 {row[1]} (ID={row[0]}): 旧customer_id=4 -> 新customer_id={row[3]} ({row[4]})")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
