#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理不再使用的 origin_location 类型字段
这些字段已被规格字典系统替代
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

DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)
cur = conn.cursor()

print("=" * 100)
print("检查 origin_location 类型的字段")
print("=" * 100)

# 查询所有 origin_location 类型的字段
cur.execute("""
    SELECT
        f.id,
        f.name,
        f.field_type,
        f.subcategory_id,
        s.name as subcategory_name,
        c.name as category_name,
        (SELECT COUNT(*) FROM product_code_field_options WHERE field_id = f.id) as option_count
    FROM product_code_fields f
    LEFT JOIN product_subcategories s ON f.subcategory_id = s.id
    LEFT JOIN product_categories c ON s.category_id = c.id
    WHERE f.field_type = 'origin_location'
    ORDER BY f.id
""")

origin_fields = cur.fetchall()

if origin_fields:
    print(f"\n发现 {len(origin_fields)} 个 origin_location 类型字段：")
    print("-" * 100)
    for f in origin_fields:
        print(f"字段ID: {f[0]:3d} | 名称: {f[1]:20s} | 子分类: {f[4]:25s} | 分类: {f[5]:10s} | 选项数: {f[6]}")
    print("-" * 100)

    print("\n这些字段已被规格字典系统替代，建议删除。")
    print("删除这些字段会同时删除它们的所有选项。")

    confirm = input("\n是否删除这些 origin_location 字段？(yes/no): ").strip().lower()

    if confirm == 'yes':
        # 开始删除
        print("\n开始删除...")

        # 先删除关联的选项
        for f in origin_fields:
            field_id = f[0]
            option_count = f[6]

            if option_count > 0:
                cur.execute(
                    "DELETE FROM product_code_field_options WHERE field_id = %s",
                    (field_id,)
                )
                print(f"  删除字段 {field_id} ({f[1]}) 的 {cur.rowcount} 个选项")

        # 再删除字段
        cur.execute("DELETE FROM product_code_fields WHERE field_type = 'origin_location'")
        print(f"\n✅ 已删除 {cur.rowcount} 个 origin_location 字段")

        conn.commit()
        print("✅ 操作完成")
    else:
        print("❌ 取消删除操作")
else:
    print("✅ 未发现 origin_location 类型字段")

cur.close()
conn.close()
