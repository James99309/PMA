#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Product表新旧字段统一迁移脚本
目标：将所有产品的category和product_name迁移到外键字段
确保所有产品都有category_id和subcategory_id
"""
import sys
import os
from datetime import datetime

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

# 直接使用config中的数据库连接
from config import Config
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

# 创建数据库连接
engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()

# 导入模型
from app.models.product import Product
from app.models.product_code import ProductCategory, ProductSubcategory

def main():
    print("=" * 80)
    print("Product表外键字段迁移脚本")
    print("=" * 80)
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    # 统计当前状态
    print("📊 当前数据状态：")
    total_products = session.query(Product).count()
    null_category_id = session.query(Product).filter(Product.category_id.is_(None)).count()
    null_subcategory_id = session.query(Product).filter(Product.subcategory_id.is_(None)).count()

    print(f"  总产品数: {total_products}")
    print(f"  category_id = NULL: {null_category_id}")
    print(f"  subcategory_id = NULL: {null_subcategory_id}")
    print()

    if null_category_id == 0 and null_subcategory_id == 0:
        print("✅ 所有产品已完成迁移，无需执行。")
        session.close()
        return

    # 确认执行
    print("⚠️  本脚本将修改以下数据：")
    print(f"  - 修复 {null_category_id} 个产品的 category_id")
    print(f"  - 修复 {null_subcategory_id} 个产品的 subcategory_id")
    print()

    confirm = input("是否继续执行？(yes/no): ").strip().lower()
    if confirm not in ['yes', 'y']:
        print("❌ 用户取消执行")
        session.close()
        return

    print("\n" + "=" * 80)
    print("开始迁移...")
    print("=" * 80 + "\n")

    # 迁移结果统计
    stats = {
        'category_exact': 0,
        'category_fuzzy': 0,
        'category_failed': 0,
        'subcategory_exact': 0,
        'subcategory_fuzzy': 0,
        'subcategory_failed': 0,
        'failed_products': []
    }

    # ==================== 第一步：修复 category_id ====================
    print("🔧 第一步：修复 category_id\n")

    products_without_category = session.query(Product).filter(
        Product.category_id.is_(None),
        Product.category.isnot(None)
    ).all()

    for product in products_without_category:
        category_name = product.category.strip()
        print(f"  处理产品 ID={product.id}, MN={product.product_mn}, category='{category_name}'")

        # 精确匹配
        category = session.query(ProductCategory).filter(
            func.lower(ProductCategory.name) == func.lower(category_name)
        ).first()

        if category:
            product.category_id = category.id
            stats['category_exact'] += 1
            print(f"    ✅ 精确匹配: {category.name} (ID={category.id})")
        else:
            # 模糊匹配
            category = session.query(ProductCategory).filter(
                func.lower(ProductCategory.name).like(f'%{category_name.lower()}%')
            ).first()

            if category:
                product.category_id = category.id
                stats['category_fuzzy'] += 1
                print(f"    ⚠️  模糊匹配: '{category_name}' → '{category.name}' (ID={category.id})")
            else:
                stats['category_failed'] += 1
                stats['failed_products'].append({
                    'id': product.id,
                    'mn': product.product_mn,
                    'field': 'category',
                    'value': category_name
                })
                print(f"    ❌ 无法匹配: '{category_name}'")

    print()

    # ==================== 第二步：修复 subcategory_id ====================
    print("🔧 第二步：修复 subcategory_id\n")

    products_without_subcategory = session.query(Product).filter(
        Product.subcategory_id.is_(None),
        Product.product_name.isnot(None)
    ).all()

    for product in products_without_subcategory:
        product_name = product.product_name.strip()
        print(f"  处理产品 ID={product.id}, MN={product.product_mn}, product_name='{product_name}'")

        # 精确匹配
        subcategory = session.query(ProductSubcategory).filter(
            func.lower(ProductSubcategory.name) == func.lower(product_name)
        ).first()

        if subcategory:
            product.subcategory_id = subcategory.id
            stats['subcategory_exact'] += 1
            print(f"    ✅ 精确匹配: {subcategory.name} (ID={subcategory.id})")
        else:
            # 模糊匹配
            subcategory = session.query(ProductSubcategory).filter(
                func.lower(ProductSubcategory.name).like(f'%{product_name.lower()}%')
            ).first()

            if subcategory:
                product.subcategory_id = subcategory.id
                stats['subcategory_fuzzy'] += 1
                print(f"    ⚠️  模糊匹配: '{product_name}' → '{subcategory.name}' (ID={subcategory.id})")
            else:
                stats['subcategory_failed'] += 1
                stats['failed_products'].append({
                    'id': product.id,
                    'mn': product.product_mn,
                    'field': 'subcategory',
                    'value': product_name
                })
                print(f"    ❌ 无法匹配: '{product_name}'")

    print()

    # ==================== 第三步：提交更改 ====================
    print("💾 提交数据库更改...")
    try:
        session.commit()
        print("  ✅ 数据库更改已提交\n")
    except Exception as e:
        session.rollback()
        print(f"  ❌ 提交失败: {e}\n")
        session.close()
        return

    # ==================== 第四步：验证结果 ====================
    print("=" * 80)
    print("验证迁移结果")
    print("=" * 80 + "\n")

    final_null_category = session.query(Product).filter(Product.category_id.is_(None)).count()
    final_null_subcategory = session.query(Product).filter(Product.subcategory_id.is_(None)).count()

    print("📊 迁移后状态：")
    print(f"  category_id = NULL: {null_category_id} → {final_null_category}")
    print(f"  subcategory_id = NULL: {null_subcategory_id} → {final_null_subcategory}")
    print()

    # ==================== 第五步：输出统计报告 ====================
    print("=" * 80)
    print("迁移统计报告")
    print("=" * 80 + "\n")

    print("Category字段迁移：")
    print(f"  ✅ 精确匹配: {stats['category_exact']}")
    print(f"  ⚠️  模糊匹配: {stats['category_fuzzy']}")
    print(f"  ❌ 匹配失败: {stats['category_failed']}")
    print()

    print("Subcategory字段迁移：")
    print(f"  ✅ 精确匹配: {stats['subcategory_exact']}")
    print(f"  ⚠️  模糊匹配: {stats['subcategory_fuzzy']}")
    print(f"  ❌ 匹配失败: {stats['subcategory_failed']}")
    print()

    # 如果有失败的产品，输出详细列表
    if stats['failed_products']:
        print("⚠️  以下产品需要人工处理：")
        print("-" * 80)
        for item in stats['failed_products']:
            print(f"  ID={item['id']}, MN={item['mn']}")
            print(f"    字段: {item['field']}")
            print(f"    值: '{item['value']}'")
            print()

    # 最终结论
    if final_null_category == 0 and final_null_subcategory == 0:
        print("=" * 80)
        print("🎉 迁移完成！所有产品已成功填充外键字段。")
        print("=" * 80)
    else:
        print("=" * 80)
        print("⚠️  迁移部分完成，仍有产品需要人工处理。")
        print("=" * 80)

    print(f"\n执行完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # 关闭session
    session.close()

if __name__ == '__main__':
    main()
