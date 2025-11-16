#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""同时迁移产品名称和产品分类字段

将旧字段迁移到新的外键关联字段：
- product_name (String) → subcategory_id (FK)
- category (String) → category_id (FK)
"""
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

from app import db
from app.models.product import Product
from app.models.product_code import ProductCategory, ProductSubcategory
from sqlalchemy import or_

def migrate_product_fields():
    """同时迁移产品名称和产品分类字段"""

    print("\n" + "="*60)
    print("开始迁移产品字段...")
    print("="*60)

    # 统计当前状态
    total_products = Product.query.count()
    need_name_migration = Product.query.filter(
        Product.subcategory_id.is_(None),
        Product.product_name.isnot(None)
    ).count()
    need_category_migration = Product.query.filter(
        Product.category_id.is_(None),
        Product.category.isnot(None)
    ).count()

    print(f"\n📊 迁移前统计:")
    print(f"  总产品数: {total_products}")
    print(f"  需迁移产品名称: {need_name_migration}")
    print(f"  需迁移产品分类: {need_category_migration}")

    # 获取所有需要迁移的产品
    products_to_migrate = Product.query.filter(
        or_(
            Product.subcategory_id.is_(None),
            Product.category_id.is_(None)
        )
    ).all()

    migrated_names = 0
    migrated_categories = 0
    failed_names = []
    failed_categories = []

    print(f"\n🔄 开始处理 {len(products_to_migrate)} 个产品...")

    for product in products_to_migrate:
        modified = False

        # 迁移产品名称
        if not product.subcategory_id and product.product_name:
            subcategory = ProductSubcategory.query.filter_by(
                name=product.product_name
            ).first()

            if subcategory:
                product.subcategory_id = subcategory.id
                migrated_names += 1
                modified = True
                print(f"  ✅ 产品 #{product.id}: 名称 '{product.product_name}' → subcategory_id={subcategory.id}")
            else:
                failed_names.append({
                    'id': product.id,
                    'name': product.product_name,
                    'mn': product.product_mn
                })

        # 迁移产品分类
        if not product.category_id and product.category:
            category = ProductCategory.query.filter_by(
                name=product.category
            ).first()

            if category:
                product.category_id = category.id
                migrated_categories += 1
                modified = True
                print(f"  ✅ 产品 #{product.id}: 分类 '{product.category}' → category_id={category.id}")
            else:
                failed_categories.append({
                    'id': product.id,
                    'category': product.category,
                    'mn': product.product_mn
                })

    # 提交更改
    try:
        db.session.commit()
        print("\n✅ 数据库更改已提交")
    except Exception as e:
        db.session.rollback()
        print(f"\n❌ 数据库提交失败: {e}")
        return

    # 显示结果统计
    print("\n" + "="*60)
    print("📊 迁移结果统计")
    print("="*60)

    print(f"\n✅ 成功迁移:")
    print(f"  产品名称: {migrated_names}/{need_name_migration} ({migrated_names*100//need_name_migration if need_name_migration else 0}%)")
    print(f"  产品分类: {migrated_categories}/{need_category_migration} ({migrated_categories*100//need_category_migration if need_category_migration else 0}%)")

    if failed_names:
        print(f"\n⚠️  未能迁移产品名称 ({len(failed_names)} 个):")
        for item in failed_names[:10]:  # 只显示前10个
            print(f"  - ID {item['id']}: '{item['name']}' (MN: {item['mn']})")
        if len(failed_names) > 10:
            print(f"  ... 还有 {len(failed_names) - 10} 个")
        print(f"  原因: 在 ProductSubcategory 表中找不到匹配的名称")

    if failed_categories:
        print(f"\n⚠️  未能迁移产品分类 ({len(failed_categories)} 个):")
        unique_categories = {}
        for item in failed_categories:
            cat = item['category']
            if cat not in unique_categories:
                unique_categories[cat] = []
            unique_categories[cat].append(item['id'])

        for cat, ids in unique_categories.items():
            print(f"  - '{cat}': {len(ids)} 个产品 (IDs: {ids[:5]}{'...' if len(ids) > 5 else ''})")
        print(f"  原因: 在 ProductCategory 表中找不到匹配的分类名称")
        print(f"\n  💡 建议: 先在 ProductCategory 表中创建缺失的分类，然后重新运行脚本")

    # 最终统计
    final_with_subcategory = Product.query.filter(Product.subcategory_id.isnot(None)).count()
    final_with_category = Product.query.filter(Product.category_id.isnot(None)).count()

    print(f"\n📊 迁移后统计:")
    print(f"  使用 subcategory_id: {final_with_subcategory}/{total_products} ({final_with_subcategory*100//total_products}%)")
    print(f"  使用 category_id: {final_with_category}/{total_products} ({final_with_category*100//total_products}%)")

    print("\n" + "="*60)
    print("✅ 迁移完成")
    print("="*60)

if __name__ == '__main__':
    from app import create_app

    app = create_app()
    with app.app_context():
        migrate_product_fields()
