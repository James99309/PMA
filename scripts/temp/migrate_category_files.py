#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据迁移脚本：填充分类共享图片和PDF

为每个ProductCategory设置共享图片和PDF：
- 遍历每个分类下的产品（Product和DevProduct）
- 取第一个有文件的产品的文件路径设为分类共享文件
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
from app.models.product_code import ProductCategory
from app.models.product import Product
from app.models.dev_product import DevProduct


def migrate_category_files(dry_run=True):
    """
    迁移分类文件

    Args:
        dry_run: True=只显示将要执行的操作, False=实际执行
    """
    app = create_app()
    with app.app_context():
        categories = ProductCategory.query.all()
        print(f"\n找到 {len(categories)} 个产品分类")

        updated_count = 0
        for category in categories:
            print(f"\n处理分类: {category.name} (ID: {category.id})")

            # 检查是否已有共享文件
            has_image = bool(category.image_path)
            has_pdf = bool(category.pdf_path)

            if has_image and has_pdf:
                print(f"  - 已有共享文件，跳过")
                continue

            # 查找该分类下的产品（标准产品）
            products = Product.query.filter(
                Product.category_id == category.id
            ).all()

            # 查找该分类下的研发产品
            dev_products = DevProduct.query.filter(
                DevProduct.category_id == category.id
            ).all()

            # 合并产品列表
            all_products = list(products) + list(dev_products)
            print(f"  - 找到 {len(products)} 个标准产品, {len(dev_products)} 个研发产品")

            # 填充图片
            if not has_image:
                for product in all_products:
                    if product.image_path:
                        if dry_run:
                            print(f"  - [DRY RUN] 将设置共享图片: {product.image_path[:50]}...")
                        else:
                            category.image_path = product.image_path
                            print(f"  - 已设置共享图片: {product.image_path[:50]}...")
                        updated_count += 1
                        break
                else:
                    print(f"  - 没有找到带图片的产品")

            # 填充PDF
            if not has_pdf:
                for product in all_products:
                    pdf_path = getattr(product, 'pdf_path', None)
                    if pdf_path:
                        if dry_run:
                            print(f"  - [DRY RUN] 将设置共享PDF: {pdf_path[:50]}...")
                        else:
                            category.pdf_path = pdf_path
                            print(f"  - 已设置共享PDF: {pdf_path[:50]}...")
                        updated_count += 1
                        break
                else:
                    print(f"  - 没有找到带PDF的产品")

        if not dry_run:
            db.session.commit()
            print(f"\n迁移完成！共更新 {updated_count} 个分类文件")
        else:
            print(f"\n[DRY RUN] 将更新 {updated_count} 个分类文件")
            print("使用 --execute 参数实际执行迁移")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='迁移分类共享文件')
    parser.add_argument('--execute', action='store_true', help='实际执行迁移（默认为dry run）')
    args = parser.parse_args()

    migrate_category_files(dry_run=not args.execute)
