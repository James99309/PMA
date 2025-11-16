#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断产品规格排序问题"""
import sys, os

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

# 仅用于诊断，不导入Flask应用
import psycopg2
from config import Config

def main():
    # 直接连接数据库
    conn = psycopg2.connect(Config.SQLALCHEMY_DATABASE_URI)
    cur = conn.cursor()

    product_mn = 'BDABA1LQF6'

    print(f"\n=== 诊断产品 {product_mn} 的规格排序 ===\n")

    # 查询产品ID
    cur.execute("""
        SELECT id, product_mn, is_mn_locked
        FROM products
        WHERE product_mn = %s
    """, (product_mn,))

    product = cur.fetchone()
    if not product:
        print(f"错误：未找到产品 {product_mn}")
        return

    product_id, mn, is_locked = product
    print(f"产品ID: {product_id}")
    print(f"MN编码: {mn}")
    print(f"锁定状态: {'已锁定' if is_locked else '未锁定'}")

    # 查询规格（按display_order排序）
    cur.execute("""
        SELECT
            id,
            field_name,
            field_value,
            display_order
        FROM product_specs
        WHERE product_id = %s
        ORDER BY display_order
    """, (product_id,))

    specs = cur.fetchall()

    print(f"\n规格数量: {len(specs)}")
    print("\n按 display_order 排序的规格:")
    print("-" * 80)
    print(f"{'序号':<6} {'display_order':<15} {'field_name':<20} {'field_value':<20}")
    print("-" * 80)

    for i, (spec_id, field_name, field_value, display_order) in enumerate(specs):
        print(f"{i:<6} {display_order:<15} {field_name:<20} {field_value:<20}")

    print("-" * 80)

    # 检查display_order是否连续且唯一
    display_orders = [spec[3] for spec in specs]
    expected_orders = list(range(len(specs)))

    if display_orders == expected_orders:
        print("\n✅ display_order 正确（从0开始连续递增）")
    else:
        print(f"\n❌ display_order 不正确")
        print(f"   当前: {display_orders}")
        print(f"   期望: {expected_orders}")

    # 检查是否有重复的display_order
    if len(display_orders) != len(set(display_orders)):
        print("❌ 存在重复的 display_order 值！")
        from collections import Counter
        counts = Counter(display_orders)
        duplicates = {k: v for k, v in counts.items() if v > 1}
        print(f"   重复值: {duplicates}")
    else:
        print("✅ display_order 值唯一")

    cur.close()
    conn.close()

if __name__ == '__main__':
    main()
