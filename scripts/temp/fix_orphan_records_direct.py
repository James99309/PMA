#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接删除 product_code_field_options 表中的孤儿记录
"""
import os
import sys
import psycopg2

# 路径修正
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

project_root = get_project_root()

# 加载 .env 文件
from dotenv import load_dotenv
env_file = os.path.join(project_root, '.env')
if os.path.exists(env_file):
    load_dotenv(env_file)
    print(f"✅ 已加载 .env 文件")

# 从环境变量获取数据库连接信息
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ 未找到 DATABASE_URL 环境变量")
    exit(1)

print(f"连接到数据库...")

try:
    # 连接数据库
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    print("\n检查 product_code_field_options 表中的孤儿记录...")

    # 先禁用触发器以避免级联问题
    cur.execute("SET session_replication_role = 'replica';")

    # 查询 field_id 为 NULL 的记录
    cur.execute("""
        SELECT id, value, code, description, field_id
        FROM product_code_field_options
        WHERE field_id IS NULL
        ORDER BY id
    """)

    orphan_records = cur.fetchall()

    if orphan_records:
        print(f"发现 {len(orphan_records)} 条孤儿记录：")
        print("-" * 100)
        for record in orphan_records:
            print(f"ID: {record[0]:4d} | 值: {record[1]:20s} | 编码: {record[2]:5s} | field_id: {record[4]}")
        print("-" * 100)

        print(f"\n正在删除 {len(orphan_records)} 条孤儿记录...")

        # 删除孤儿记录
        cur.execute("DELETE FROM product_code_field_options WHERE field_id IS NULL")
        deleted_count = cur.rowcount

        # 恢复触发器
        cur.execute("SET session_replication_role = 'origin';")

        conn.commit()
        print(f"✅ 已删除 {deleted_count} 条孤儿记录")
    else:
        print("✅ 未发现孤儿记录")
        # 恢复触发器
        cur.execute("SET session_replication_role = 'origin';")
        conn.commit()

    cur.close()
    conn.close()

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    if 'conn' in locals():
        conn.rollback()
        conn.close()
