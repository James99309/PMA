#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查报价单 QU202408-022 的历史数据和变更记录"""
import psycopg2

# SP8D 云端数据库连接
DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

def main():
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()

    print("=== 1. 报价单完整时间戳信息 ===")
    cursor.execute("""
        SELECT id, quotation_number, customer_id, project_id, owner_id,
               created_at, updated_at
        FROM quotations
        WHERE LOWER(quotation_number) = 'qu202408-022'
    """)
    q = cursor.fetchone()
    if q:
        print(f"报价单ID: {q[0]}")
        print(f"报价单号: {q[1]}")
        print(f"customer_id: {q[2]}")
        print(f"project_id: {q[3]}")
        print(f"owner_id: {q[4]}")
        print(f"created_at: {q[5]} (类型: {type(q[5])})")
        print(f"updated_at: {q[6]} (类型: {type(q[6])})")

    # 查看变更日志
    print("\n=== 2. 变更日志 (change_logs 表) ===")
    cursor.execute("""
        SELECT id, table_name, record_id, field_name, old_value, new_value,
               changed_by, changed_at, change_type
        FROM change_logs
        WHERE (table_name = 'quotations' AND record_id = 564)
           OR (table_name = 'quotation' AND record_id = 564)
        ORDER BY changed_at DESC
        LIMIT 20
    """)
    logs = cursor.fetchall()
    if logs:
        for log in logs:
            print(f"\n变更ID: {log[0]}")
            print(f"  表名: {log[1]}, 记录ID: {log[2]}")
            print(f"  字段: {log[3]}")
            print(f"  旧值: {log[4]}")
            print(f"  新值: {log[5]}")
            print(f"  变更人ID: {log[6]}")
            print(f"  变更时间: {log[7]}")
            print(f"  变更类型: {log[8]}")
    else:
        print("未找到相关变更日志")

    # 查看所有类似时间创建的报价单
    print("\n=== 3. 2024年8月创建的报价单 ===")
    cursor.execute("""
        SELECT q.quotation_number, q.owner_id, u.real_name, q.created_at, q.updated_at
        FROM quotations q
        LEFT JOIN users u ON q.owner_id = u.id
        WHERE q.quotation_number LIKE 'QU202408%'
        ORDER BY q.quotation_number
    """)
    quotations = cursor.fetchall()
    for qt in quotations:
        print(f"{qt[0]} | 所有者: {qt[2]}(ID={qt[1]}) | 创建: {qt[3]} | 更新: {qt[4]}")

    # 检查项目48的报价单
    print("\n=== 4. 项目48(哔哩哔哩)的所有报价单 ===")
    cursor.execute("""
        SELECT q.quotation_number, q.owner_id, u.real_name,
               q.customer_id, c.company_name,
               q.created_at
        FROM quotations q
        LEFT JOIN users u ON q.owner_id = u.id
        LEFT JOIN companies c ON q.customer_id = c.id
        WHERE q.project_id = 48
        ORDER BY q.created_at
    """)
    project_quotations = cursor.fetchall()
    for pq in project_quotations:
        print(f"{pq[0]} | 所有者: {pq[2]}(ID={pq[1]}) | 客户: {pq[4]}(ID={pq[3]}) | 创建: {pq[5]}")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
