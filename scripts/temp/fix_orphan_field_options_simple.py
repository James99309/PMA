#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理 product_code_field_options 表中的孤儿记录
修复 field_id 为 NULL 的记录
"""
import os
import sys
import psycopg2
from psycopg2 import sql

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
    print("请设置数据库连接字符串，例如：")
    print("export DATABASE_URL='postgresql://user:password@localhost:5432/database'")
    exit(1)

print(f"连接到数据库...")

try:
    # 连接数据库
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    print("检查 product_code_field_options 表中的孤儿记录...")

    # 查询 field_id 为 NULL 的记录
    cur.execute("""
        SELECT id, value, code, description
        FROM product_code_field_options
        WHERE field_id IS NULL
    """)

    orphan_records = cur.fetchall()

    if orphan_records:
        print(f"\n发现 {len(orphan_records)} 条孤儿记录（field_id 为 NULL）：")
        print("-" * 80)
        for record in orphan_records:
            print(f"ID: {record[0]}, 值: {record[1]}, 编码: {record[2]}, 描述: {record[3]}")
        print("-" * 80)

        # 询问是否删除
        confirm = input(f"\n是否删除这 {len(orphan_records)} 条孤儿记录？(yes/no): ").strip().lower()

        if confirm == 'yes':
            # 删除孤儿记录
            cur.execute("DELETE FROM product_code_field_options WHERE field_id IS NULL")
            conn.commit()
            print(f"✅ 已删除 {cur.rowcount} 条孤儿记录")
        else:
            print("❌ 取消删除操作")
    else:
        print("✅ 未发现孤儿记录，数据库状态正常")

    cur.close()
    conn.close()

except Exception as e:
    print(f"❌ 错误: {e}")
    if 'conn' in locals():
        conn.rollback()
        conn.close()
