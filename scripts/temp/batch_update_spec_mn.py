#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量更新产品库中现有产品的 spec_mn 字段

对于有规格定义的产品，根据规格数据计算 spec_mn。
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

from app import create_app, db
from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.utils.product_helpers import generate_spec_mn


def batch_update_spec_mn(dry_run=True):
    """批量更新产品的 spec_mn 字段

    Args:
        dry_run: True=仅预览不实际更新，False=执行更新
    """
    app = create_app()

    with app.app_context():
        # 查询所有有规格数据的产品
        # 通过子查询找到有规格的产品ID
        products_with_specs_ids = db.session.query(ProductSpec.product_id).distinct().subquery()

        products = Product.query.filter(
            Product.id.in_(db.session.query(products_with_specs_ids.c.product_id))
        ).all()

        print(f"\n找到 {len(products)} 个有规格数据的产品")
        print("=" * 80)

        updated_count = 0
        skipped_count = 0
        same_count = 0

        for product in products:
            # 生成规格MN
            spec_mn = generate_spec_mn(product)

            if not spec_mn:
                print(f"跳过: ID={product.id}, MN={product.product_mn}, 型号={product.model} (无法生成规格MN)")
                skipped_count += 1
                continue

            # 检查是否需要更新
            if product.spec_mn == spec_mn:
                same_count += 1
                continue

            # 显示变更
            old_spec_mn = product.spec_mn or "(空)"
            if product.product_mn == spec_mn:
                print(f"更新: ID={product.id}, MN={product.product_mn}, 型号={product.model}")
                print(f"       spec_mn: {old_spec_mn} -> {spec_mn} (与MN一致)")
            else:
                print(f"更新: ID={product.id}, MN={product.product_mn}, 型号={product.model}")
                print(f"       spec_mn: {old_spec_mn} -> {spec_mn}")
                if product.product_mn:
                    print(f"       显示为: {product.product_mn} [{spec_mn}]")

            if not dry_run:
                product.spec_mn = spec_mn

            updated_count += 1

        if not dry_run:
            db.session.commit()
            print(f"\n已提交数据库更新")

        print("=" * 80)
        print(f"总结:")
        print(f"  - 有规格的产品: {len(products)}")
        print(f"  - 需要更新: {updated_count}")
        print(f"  - 已是最新: {same_count}")
        print(f"  - 跳过(无法生成): {skipped_count}")

        if dry_run:
            print(f"\n这是预览模式，未实际修改数据库。")
            print(f"若要执行更新，请运行: python3 {__file__} --execute")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='批量更新产品 spec_mn 字段')
    parser.add_argument('--execute', action='store_true', help='执行实际更新（默认仅预览）')
    args = parser.parse_args()

    batch_update_spec_mn(dry_run=not args.execute)
