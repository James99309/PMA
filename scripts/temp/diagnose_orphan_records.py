#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断 product_code_field_options 表中的数据
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
    print(f"✅ 已加载 .env 文件: {env_file}")

# 从环境变量获取数据库连接信息
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    print("❌ 未找到 DATABASE_URL 环境变量")
    exit(1)

# 解析数据库URL显示连接信息
import re
match = re.search(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', DATABASE_URL)
if match:
    user, password, host, port, dbname = match.groups()
    print(f"数据库连接信息:")
    print(f"  主机: {host}")
    print(f"  端口: {port}")
    print(f"  数据库: {dbname}")
    print(f"  用户: {user}")
else:
    print(f"DATABASE_URL: {DATABASE_URL}")

print(f"\n连接到数据库...")

try:
    # 连接数据库
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    # 1. 检查表是否存在
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'product_code_field_options'
        )
    """)
    table_exists = cur.fetchone()[0]
    print(f"\n表 product_code_field_options 存在: {table_exists}")

    if not table_exists:
        print("❌ 表不存在")
        exit(1)

    # 2. 查询总记录数
    cur.execute("SELECT COUNT(*) FROM product_code_field_options")
    total_count = cur.fetchone()[0]
    print(f"总记录数: {total_count}")

    # 3. 查询 field_id 为 NULL 的记录
    cur.execute("""
        SELECT id, value, code, description, field_id
        FROM product_code_field_options
        WHERE field_id IS NULL
        ORDER BY id
    """)
    orphan_records = cur.fetchall()
    print(f"field_id 为 NULL 的记录数: {len(orphan_records)}")

    if orphan_records:
        print("\nfield_id 为 NULL 的记录：")
        print("-" * 100)
        for record in orphan_records:
            print(f"ID: {record[0]:4d} | 值: {record[1]:20s} | 编码: {record[2]:5s} | field_id: {record[4]}")
        print("-" * 100)

    # 4. 查询特定ID的记录 (1, 2, 5, 68)
    print("\n查询特定ID (1, 2, 5, 68) 的记录：")
    cur.execute("""
        SELECT id, value, code, description, field_id
        FROM product_code_field_options
        WHERE id IN (1, 2, 5, 68)
        ORDER BY id
    """)
    specific_records = cur.fetchall()
    if specific_records:
        print("-" * 100)
        for record in specific_records:
            print(f"ID: {record[0]:4d} | 值: {record[1]:20s} | 编码: {record[2]:5s} | field_id: {record[4]}")
        print("-" * 100)
    else:
        print("未找到这些记录")

    # 5. 查询所有记录的 field_id 分布
    cur.execute("""
        SELECT
            CASE WHEN field_id IS NULL THEN 'NULL' ELSE 'NOT NULL' END as field_id_status,
            COUNT(*) as count
        FROM product_code_field_options
        GROUP BY CASE WHEN field_id IS NULL THEN 'NULL' ELSE 'NOT NULL' END
    """)
    distribution = cur.fetchall()
    print("\nfield_id 分布：")
    for row in distribution:
        print(f"  {row[0]}: {row[1]} 条记录")

    cur.close()
    conn.close()

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    if 'conn' in locals():
        conn.close()
