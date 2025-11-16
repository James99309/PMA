#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查字段关系问题
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
print("检查问题选项 (ID: 1, 2, 5, 68) 关联的字段")
print("=" * 100)

# 查询这些选项及其关联的字段
cur.execute("""
    SELECT
        o.id as option_id,
        o.value as option_value,
        o.code as option_code,
        o.field_id,
        f.id as field_actual_id,
        f.name as field_name,
        f.field_type,
        f.subcategory_id,
        s.name as subcategory_name,
        c.id as category_id,
        c.name as category_name
    FROM product_code_field_options o
    LEFT JOIN product_code_fields f ON o.field_id = f.id
    LEFT JOIN product_subcategories s ON f.subcategory_id = s.id
    LEFT JOIN product_categories c ON s.category_id = c.id
    WHERE o.id IN (1, 2, 5, 68)
    ORDER BY o.id
""")

records = cur.fetchall()
print("\n问题选项的详细信息：")
print("-" * 100)
for r in records:
    print(f"选项ID: {r[0]}")
    print(f"  选项值: {r[1]}")
    print(f"  选项编码: {r[2]}")
    print(f"  field_id: {r[3]}")
    print(f"  字段ID: {r[4]}")
    print(f"  字段名称: {r[5]}")
    print(f"  字段类型: {r[6]}")
    print(f"  子分类ID: {r[7]}")
    print(f"  子分类名称: {r[8]}")
    print(f"  分类ID: {r[9]}")
    print(f"  分类名称: {r[10]}")
    print("-" * 100)

# 检查基站分类（ID=1）的所有子分类和字段
print("\n\n基站分类（ID=1）的所有子分类：")
print("=" * 100)
cur.execute("""
    SELECT
        s.id,
        s.name,
        s.code_letter,
        COUNT(f.id) as field_count
    FROM product_subcategories s
    LEFT JOIN product_code_fields f ON s.id = f.subcategory_id AND f.field_type = 'spec'
    WHERE s.category_id = 1
    GROUP BY s.id, s.name, s.code_letter
    ORDER BY s.display_order
""")

subcategories = cur.fetchall()
for sub in subcategories:
    print(f"子分类ID: {sub[0]:3d} | 名称: {sub[1]:20s} | 标识符: {sub[2]} | 规格字段数: {sub[3]}")

# 检查这些字段是否属于基站分类的子分类
print("\n\n检查问题字段 (5, 6, 9, 73) 的归属：")
print("=" * 100)
cur.execute("""
    SELECT
        f.id,
        f.name,
        f.field_type,
        f.subcategory_id,
        s.name as subcategory_name,
        c.id as category_id,
        c.name as category_name,
        (SELECT COUNT(*) FROM product_code_field_options WHERE field_id = f.id) as option_count
    FROM product_code_fields f
    LEFT JOIN product_subcategories s ON f.subcategory_id = s.id
    LEFT JOIN product_categories c ON s.category_id = c.id
    WHERE f.id IN (5, 6, 9, 73)
    ORDER BY f.id
""")

fields = cur.fetchall()
for f in fields:
    print(f"字段ID: {f[0]:3d} | 名称: {f[1]:20s} | 类型: {f[2]:15s} | 子分类: {f[4]:20s} | 分类: {f[6]:10s} | 选项数: {f[7]}")

cur.close()
conn.close()
