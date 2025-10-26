#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查PO202510-004的完整信息"""
import psycopg2

CLOUD_DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

def main():
    conn = psycopg2.connect(CLOUD_DB_URL)
    cursor = conn.cursor()

    print("\n=== PO202510-004 完整信息 ===\n")

    # 1. 批价单基本信息
    cursor.execute("""
        SELECT id, order_number, status, created_at,
               pricing_total_discount_rate, settlement_total_discount_rate
        FROM pricing_orders
        WHERE order_number = 'PO202510-004'
    """)

    po = cursor.fetchone()
    if not po:
        print("❌ 未找到批价单")
        return

    print(f"批价单ID: {po[0]}")
    print(f"订单号: {po[1]}")
    print(f"状态: {po[2]}")
    print(f"创建时间: {po[3]}")
    print(f"批价折扣率: {po[4]}")
    print(f"结算折扣率: {po[5]}")

    # 2. 所有审批实例（包括召回的）
    print(f"\n=== 所有审批实例 ===\n")

    cursor.execute("""
        SELECT ai.id, ai.status, ai.current_step, ai.started_at, ai.ended_at,
               u.real_name as submitter
        FROM approval_instance ai
        JOIN users u ON ai.created_by = u.id
        WHERE ai.object_type = 'pricing_order' AND ai.object_id = %s
        ORDER BY ai.started_at DESC
    """, (po[0],))

    instances = cursor.fetchall()
    print(f"总共 {len(instances)} 个审批实例:\n")

    for inst in instances:
        print(f"  实例{inst[0]}: {inst[1]}")
        print(f"    提交人: {inst[5]}")
        print(f"    当前步骤: {inst[2]}")
        print(f"    开始: {inst[3]}")
        print(f"    结束: {inst[4]}")

        # 查找这个实例的审批记录
        cursor.execute("""
            SELECT ar.id, u.real_name, ar.action, ar.step_id, ar.timestamp
            FROM approval_record ar
            JOIN users u ON ar.approver_id = u.id
            WHERE ar.instance_id = %s
            ORDER BY ar.timestamp
        """, (inst[0],))

        records = cursor.fetchall()
        if records:
            print(f"    审批记录:")
            for rec in records:
                print(f"      - {rec[1]:10} {rec[2]:10} step{rec[3]:3} {rec[4]}")
        print()

    # 3. 查找所有用户，看是否有郭小会
    print(f"=== 查找郭小会用户 ===\n")

    cursor.execute("""
        SELECT id, username, real_name, role
        FROM users
        WHERE real_name LIKE '%郭%' OR username LIKE '%gxh%'
    """)

    users = cursor.fetchall()
    if users:
        for user in users:
            print(f"  用户{user[0]}: {user[2]} (username: {user[1]}, role: {user[3]})")
    else:
        print("  ⚠️ 未找到郭小会用户")

    cursor.close()
    conn.close()

    print("\n=== 完成 ===\n")

if __name__ == '__main__':
    main()
