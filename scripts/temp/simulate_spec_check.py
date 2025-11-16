#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""模拟后端规格检查逻辑"""
import sys, os

# 路径修正
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
from config import Config

def simulate_check(product_mn, submitted_spec_names, submitted_spec_values):
    """
    模拟后端的规格检查逻辑

    Args:
        product_mn: 产品MN编码
        submitted_spec_names: 前端提交的spec_name[]数组
        submitted_spec_values: 前端提交的spec_value[]数组
    """
    conn = psycopg2.connect(Config.SQLALCHEMY_DATABASE_URI)
    cur = conn.cursor()

    # 查询产品
    cur.execute("""
        SELECT id, is_mn_locked
        FROM products
        WHERE product_mn = %s
    """, (product_mn,))

    product = cur.fetchone()
    if not product:
        print(f"错误：未找到产品 {product_mn}")
        return

    product_id, is_locked = product

    if not is_locked:
        print(f"✅ 产品未锁定，允许修改")
        return

    # 查询现有规格（按display_order排序）
    cur.execute("""
        SELECT field_name, field_value
        FROM product_specs
        WHERE product_id = %s
        ORDER BY display_order
    """, (product_id,))

    old_specs = cur.fetchall()

    print(f"\n=== 模拟后端检查：{product_mn} ===\n")
    print(f"产品ID: {product_id}")
    print(f"锁定状态: {'已锁定' if is_locked else '未锁定'}")
    print(f"\n数据库中的规格数量: {len(old_specs)}")
    print(f"前端提交的规格数量: {len(submitted_spec_names)}")

    # 模拟后端检查逻辑（来自product.py:1536-1550）
    blocked_changes = []

    if old_specs:
        # 原来有规格，检查是否有变化
        new_spec_count = len([n for n in submitted_spec_names if n.strip()])

        print(f"\n有效规格数量检查:")
        print(f"  数据库: {len(old_specs)}")
        print(f"  前端提交: {new_spec_count}")

        if new_spec_count != len(old_specs):
            blocked_changes.append('规格')
            print(f"  ❌ 规格数量不匹配！")
        else:
            print(f"  ✅ 规格数量匹配")

            # 简化检查：比较规格名称和值
            print(f"\n详细检查:")
            print("-" * 80)
            print(f"{'序号':<6} {'数据库名称':<20} {'提交名称':<20} {'匹配':<10}")
            print("-" * 80)

            for i, (db_name, db_value) in enumerate(old_specs):
                if i < len(submitted_spec_names):
                    submitted_name = submitted_spec_names[i]
                    match = "✅" if submitted_name == db_name else "❌"
                    print(f"{i:<6} {db_name:<20} {submitted_name:<20} {match:<10}")

                    if submitted_name != db_name:
                        blocked_changes.append('规格')
                        print(f"       规格名称不匹配: '{db_name}' vs '{submitted_name}'")
                        break

                    # 检查值
                    if i < len(submitted_spec_values):
                        submitted_value = submitted_spec_values[i]
                        if submitted_value != db_value:
                            blocked_changes.append('规格')
                            print(f"       规格值不匹配: '{db_value}' vs '{submitted_value}'")
                            break

            print("-" * 80)

    if blocked_changes:
        print(f"\n❌ 检查失败：该产品MN编码已锁定，不允许修改已有值的字段: {', '.join(blocked_changes)}")
    else:
        print(f"\n✅ 检查通过：允许保存")

    cur.close()
    conn.close()

if __name__ == '__main__':
    product_mn = 'BDABA1LQF6'

    # 场景1：完全匹配的规格（应该通过）
    print("=" * 80)
    print("场景1：完全匹配的规格数据")
    print("=" * 80)
    spec_names_match = [
        '频率范围', '带宽', '功率', '阻抗',
        '电源类型', '频率响应', '测试规格', '增益调节范围'
    ]
    spec_values_match = [
        '400-450MHz', '25MHz', '25', '50欧姆',
        '220V欧标', '150MHz', '个卡', '20dB'
    ]
    simulate_check(product_mn, spec_names_match, spec_values_match)

    # 场景2：规格数量不匹配（应该失败）
    print("\n" + "=" * 80)
    print("场景2：规格数量不匹配（只提交7个）")
    print("=" * 80)
    spec_names_less = spec_names_match[:7]
    spec_values_less = spec_values_match[:7]
    simulate_check(product_mn, spec_names_less, spec_values_less)

    # 场景3：空数组（应该失败）
    print("\n" + "=" * 80)
    print("场景3：前端未提交规格数据")
    print("=" * 80)
    simulate_check(product_mn, [], [])

    # 场景4：顺序错误（应该失败）
    print("\n" + "=" * 80)
    print("场景4：规格顺序错误")
    print("=" * 80)
    spec_names_wrong_order = [
        '带宽', '频率范围', '功率', '阻抗',  # 前两个顺序调换
        '电源类型', '频率响应', '测试规格', '增益调节范围'
    ]
    simulate_check(product_mn, spec_names_wrong_order, spec_values_match)
