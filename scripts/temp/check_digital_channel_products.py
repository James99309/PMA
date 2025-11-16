#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试脚本：检查"数字智能信道机"产品数据
"""
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

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import json

# 直接连接数据库
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://nijie:nijie@localhost:5432/pma_local')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

def check_products():
    """检查数字智能信道机产品"""
    session = Session()

    try:
        print("=" * 80)
        print("查询：数字智能信道机产品详细信息")
        print("=" * 80)

        # 直接SQL查询
        sql = """
        SELECT
            id,
            product_mn,
            product_name,
            category,
            subcategory_id,
            model,
            product_model,
            status,
            code_definition_snapshot
        FROM products
        WHERE product_name LIKE '%数字智能信道机%'
           OR category LIKE '%数字智能信道机%'
        ORDER BY id
        """

        result = session.execute(sql)
        products = result.fetchall()

        print(f"\n找到 {len(products)} 个相关产品:\n")

        for p in products:
            print(f"{'='*80}")
            print(f"ID: {p[0]}")
            print(f"产品MN编码: {p[1]}")
            print(f"产品名称: {p[2]}")
            print(f"分类: {p[3]}")
            print(f"子分类ID: {p[4]}")
            print(f"model字段: {p[5]}")
            print(f"product_model字段: {p[6]}")
            print(f"状态 (status): {p[7]}")

            # 解析code_definition_snapshot
            if p[8]:
                try:
                    snapshot = json.loads(p[8])
                    print(f"编码快照字段数: {len(snapshot)}")
                    if snapshot:
                        print("  前3个字段:")
                        for field in snapshot[:3]:
                            print(f"    - {field.get('name')}: {field.get('value')} (code: {field.get('code')})")
                except:
                    print("编码快照: (解析失败)")
            else:
                print("编码快照: 无")
            print()

        # 测试API过滤逻辑
        print("=" * 80)
        print("模拟API过滤逻辑测试")
        print("=" * 80)

        # 子分类查询
        sql_subcategory = """
        SELECT id, name, category_id
        FROM product_subcategories
        WHERE name LIKE '%数字智能信道机%'
        """
        result = session.execute(sql_subcategory)
        subcategories = result.fetchall()

        if subcategories:
            for subcat in subcategories:
                print(f"\n子分类: {subcat[1]} (ID: {subcat[0]}, Category ID: {subcat[2]})")

                # 查询该子分类下的产品（模拟API逻辑）
                sql_filtered = """
                SELECT
                    id,
                    product_mn,
                    product_name,
                    model,
                    product_model,
                    status
                FROM products
                WHERE subcategory_id = :subcategory_id
                  AND status = 'active'
                """
                result = session.execute(sql_filtered, {'subcategory_id': subcat[0]})
                filtered_products = result.fetchall()

                print(f"  → status='active'过滤后: {len(filtered_products)} 个产品")
                for fp in filtered_products:
                    print(f"      {fp[1]:20} | model={fp[3]:20} | product_model={fp[4]}")

                # 查询所有状态的产品
                sql_all = """
                SELECT
                    id,
                    product_mn,
                    product_name,
                    model,
                    product_model,
                    status
                FROM products
                WHERE subcategory_id = :subcategory_id
                """
                result = session.execute(sql_all, {'subcategory_id': subcat[0]})
                all_products = result.fetchall()

                print(f"  → 无状态过滤: {len(all_products)} 个产品")
                for ap in all_products:
                    print(f"      {ap[1]:20} | status={ap[5]:15} | model={ap[3]:20} | product_model={ap[4]}")

        # 分组测试
        print("\n" + "=" * 80)
        print("型号分组测试（模拟后端分组逻辑）")
        print("=" * 80)

        if subcategories:
            for subcat in subcategories:
                sql_all = """
                SELECT
                    id,
                    product_mn,
                    product_name,
                    model,
                    product_model,
                    status
                FROM products
                WHERE subcategory_id = :subcategory_id
                  AND status = 'active'
                """
                result = session.execute(sql_all, {'subcategory_id': subcat[0]})
                products_to_group = result.fetchall()

                print(f"\n子分类: {subcat[1]}")
                print(f"共 {len(products_to_group)} 个active产品需要分组\n")

                # 模拟当前后端逻辑: model = product.model or product.product_name
                groups_current = {}
                for p in products_to_group:
                    model_key = p[3] or p[2] or '未知型号'  # model or product_name
                    if model_key not in groups_current:
                        groups_current[model_key] = []
                    groups_current[model_key].append(p)

                print("【当前逻辑】使用 model 字段分组:")
                for model_key, prods in groups_current.items():
                    print(f"  型号 '{model_key}': {len(prods)} 个产品")
                    for p in prods:
                        print(f"    - {p[1]} (product_model={p[4]})")

                # 模拟修复后逻辑: product_model > model > product_name
                groups_fixed = {}
                for p in products_to_group:
                    if p[4] and p[4] != p[2]:  # product_model 存在且不等于 product_name
                        model_key = p[4]
                    elif p[3] and p[3] != p[2]:  # model 存在且不等于 product_name
                        model_key = p[3]
                    else:
                        model_key = p[2] or '未知型号'

                    if model_key not in groups_fixed:
                        groups_fixed[model_key] = []
                    groups_fixed[model_key].append(p)

                print("\n【修复后逻辑】优先使用 product_model 字段分组:")
                for model_key, prods in groups_fixed.items():
                    print(f"  型号 '{model_key}': {len(prods)} 个产品")
                    for p in prods:
                        print(f"    - {p[1]} (model={p[3]}, product_model={p[4]})")

    finally:
        session.close()

if __name__ == '__main__':
    check_products()
