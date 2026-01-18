#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步 product_subcategories 英文名称到云端 SP8D 数据库

此脚本从本地数据库读取英文名称，然后更新到云端数据库。
按 category_id 和 name (中文名) 匹配。
"""
import sys
import os

# 路径修正 - 支持从任何位置运行
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

import psycopg2
from psycopg2.extras import DictCursor

# 本地数据库配置
LOCAL_DB_URL = "postgresql://nijie@localhost:5432/pma_local"

# 云端 SP8D 数据库配置
CLOUD_DB_URL = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"


def get_local_english_names():
    """从本地数据库获取所有有英文名称的子分类"""
    conn = psycopg2.connect(LOCAL_DB_URL)
    try:
        with conn.cursor(cursor_factory=DictCursor) as cur:
            cur.execute("""
                SELECT category_id, name, name_en, code_letter
                FROM product_subcategories
                WHERE name_en IS NOT NULL AND name_en != ''
                ORDER BY category_id, id
            """)
            return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def sync_to_cloud(subcategories):
    """同步英文名称到云端数据库"""
    conn = psycopg2.connect(CLOUD_DB_URL)
    try:
        with conn.cursor() as cur:
            updated = 0
            not_found = []

            for sub in subcategories:
                cur.execute("""
                    UPDATE product_subcategories
                    SET name_en = %s
                    WHERE category_id = %s AND name = %s
                    AND (name_en IS NULL OR name_en = '')
                """, (sub['name_en'], sub['category_id'], sub['name']))

                if cur.rowcount > 0:
                    updated += 1
                    print(f"  ✅ 更新: {sub['name']} -> {sub['name_en']}")
                else:
                    # 检查是否因为已有英文名而跳过
                    cur.execute("""
                        SELECT name_en FROM product_subcategories
                        WHERE category_id = %s AND name = %s
                    """, (sub['category_id'], sub['name']))
                    result = cur.fetchone()
                    if result:
                        if result[0]:
                            print(f"  ⏭️ 已有: {sub['name']} = {result[0]}")
                        else:
                            not_found.append(sub['name'])
                    else:
                        not_found.append(sub['name'])

            conn.commit()

            print(f"\n============================================================")
            print(f"同步完成：更新了 {updated} 条记录")
            if not_found:
                print(f"未找到 {len(not_found)} 条记录: {', '.join(not_found[:5])}...")
            print(f"============================================================")

            return updated
    finally:
        conn.close()


def verify_sync():
    """验证同步结果"""
    conn = psycopg2.connect(CLOUD_DB_URL)
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) as total,
                       SUM(CASE WHEN name_en IS NOT NULL AND name_en != '' THEN 1 ELSE 0 END) as with_en
                FROM product_subcategories
            """)
            result = cur.fetchone()
            print(f"\n云端 product_subcategories 状态:")
            print(f"  总记录数: {result[0]}")
            print(f"  有英文名: {result[1]}")
            print(f"  缺英文名: {result[0] - result[1]}")
    finally:
        conn.close()


if __name__ == '__main__':
    print("============================================================")
    print("同步 product_subcategories 英文名称到云端 SP8D")
    print("============================================================\n")

    print("1. 从本地数据库获取英文名称...")
    subcategories = get_local_english_names()
    print(f"   获取到 {len(subcategories)} 条记录\n")

    print("2. 同步到云端数据库...")
    sync_to_cloud(subcategories)

    print("\n3. 验证同步结果...")
    verify_sync()
