#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查报价单的变更日志"""
import psycopg2

DB_URL = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

def main():
    conn = psycopg2.connect(DB_URL)
    cursor = conn.cursor()

    print("=== 报价单 564 (QU202408-022) 的变更日志 ===")
    cursor.execute("""
        SELECT id, module_name, table_name, record_id, operation_type,
               field_name, old_value, new_value, user_id, user_name,
               created_at, description
        FROM change_logs
        WHERE record_id = 564
          AND (table_name ILIKE '%quotation%' OR module_name ILIKE '%quotation%')
        ORDER BY created_at DESC
    """)
    logs = cursor.fetchall()

    if logs:
        for log in logs:
            print(f"\n变更ID: {log[0]}")
            print(f"  模块: {log[1]}, 表: {log[2]}, 记录ID: {log[3]}")
            print(f"  操作: {log[4]}")
            print(f"  字段: {log[5]}")
            print(f"  旧值: {log[6]}")
            print(f"  新值: {log[7]}")
            print(f"  操作人: {log[9]} (ID={log[8]})")
            print(f"  时间: {log[10]}")
            print(f"  描述: {log[11]}")
    else:
        print("未找到相关变更日志")

    # 搜索所有包含 customer_id 变更的日志
    print("\n\n=== 所有 customer_id 相关的变更日志 ===")
    cursor.execute("""
        SELECT id, table_name, record_id, field_name, old_value, new_value,
               user_name, created_at
        FROM change_logs
        WHERE field_name ILIKE '%customer%'
        ORDER BY created_at DESC
        LIMIT 20
    """)
    customer_logs = cursor.fetchall()

    if customer_logs:
        for log in customer_logs:
            print(f"ID:{log[0]} | 表:{log[1]} | 记录:{log[2]} | 字段:{log[3]}")
            print(f"  旧值:{log[4]} -> 新值:{log[5]} | 操作人:{log[6]} | 时间:{log[7]}")
    else:
        print("未找到 customer_id 相关变更日志")

    # 检查最近的备份时间
    print("\n\n=== 检查数据库中是否有备份记录表 ===")
    cursor.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name LIKE '%backup%'
    """)
    backup_tables = cursor.fetchall()
    print(f"备份相关表: {backup_tables}")

    cursor.close()
    conn.close()

if __name__ == '__main__':
    main()
