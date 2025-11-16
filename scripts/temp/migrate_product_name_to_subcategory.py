#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""产品名称字段数据迁移脚本

功能：
1. 将旧的 product_name 字符串字段迁移到新的 subcategory_id 外键字段
2. 尝试匹配ProductSubcategory表中的数据
3. 生成迁移报告，记录无法迁移的产品

策略：
- 能找到匹配的ProductSubcategory：设置subcategory_id
- 找不到匹配的：保留product_name，记录到报告
- 新建的产品：使用subcategory_id
"""
import sys
import os
import json
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

from app import create_app, db
from app.models.product import Product
from app.models.product_code import ProductSubcategory

def analyze_migration_status():
    """分析当前迁移状态"""
    app = create_app()
    with app.app_context():
        total_products = Product.query.count()
        with_subcategory = Product.query.filter(Product.subcategory_id != None).count()
        without_subcategory = Product.query.filter(Product.subcategory_id == None).count()

        with_product_name = Product.query.filter(
            Product.subcategory_id == None,
            Product.product_name != None,
            Product.product_name != ''
        ).count()

        print("\n" + "=" * 80)
        print("产品名称字段迁移状态分析".center(80))
        print("=" * 80)
        print(f"  总产品数：           {total_products:6d}")
        print(f"  已使用新字段：       {with_subcategory:6d} ({with_subcategory/total_products*100:.1f}%)" if total_products > 0 else "  已使用新字段：       0")
        print(f"  未使用新字段：       {without_subcategory:6d} ({without_subcategory/total_products*100:.1f}%)" if total_products > 0 else "  未使用新字段：       0")
        print(f"  有旧字段值可迁移：   {with_product_name:6d}")
        print("=" * 80 + "\n")

        return {
            'total': total_products,
            'with_subcategory': with_subcategory,
            'without_subcategory': without_subcategory,
            'with_product_name': with_product_name
        }

def migrate_product_names():
    """执行数据迁移"""
    app = create_app()
    with app.app_context():
        print("📋 开始迁移产品名称数据...")

        # 查找所有没有subcategory_id但有product_name的产品
        products_to_migrate = Product.query.filter(
            Product.subcategory_id == None,
            Product.product_name != None,
            Product.product_name != ''
        ).all()

        if not products_to_migrate:
            print("✅ 所有产品已经使用新字段或无需迁移")
            return

        print(f"\n找到 {len(products_to_migrate)} 个需要迁移的产品\n")

        migrated = []
        unmigrated = []

        for product in products_to_migrate:
            # 尝试通过product_name匹配ProductSubcategory
            subcategory = ProductSubcategory.query.filter_by(
                name=product.product_name.strip()
            ).first()

            if subcategory:
                product.subcategory_id = subcategory.id
                migrated.append({
                    'id': product.id,
                    'product_mn': product.product_mn or 'N/A',
                    'product_name': product.product_name,
                    'subcategory_id': subcategory.id,
                    'matched_name': subcategory.name
                })
                print(f"  ✅ 产品 ID={product.id:4d} MN={product.product_mn or 'N/A':20s} 名称='{product.product_name}' → subcategory_id={subcategory.id}")
            else:
                unmigrated.append({
                    'id': product.id,
                    'product_mn': product.product_mn or 'N/A',
                    'product_name': product.product_name,
                    'model': product.model or ''
                })
                print(f"  ⚠️  产品 ID={product.id:4d} MN={product.product_mn or 'N/A':20s} 名称='{product.product_name}' → 找不到匹配的ProductSubcategory")

        # 提交数据库更改
        if migrated:
            try:
                db.session.commit()
                print(f"\n✅ 成功迁移 {len(migrated)} 个产品")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ 迁移失败: {str(e)}")
                return

        if unmigrated:
            print(f"\n⚠️  {len(unmigrated)} 个产品无法迁移（将继续使用旧字段）")
            print("\n无法迁移的产品列表：")
            print("-" * 80)
            for item in unmigrated[:10]:  # 只显示前10个
                print(f"  ID: {item['id']:4d} | MN: {item['product_mn']:20s} | 名称: {item['product_name']}")
            if len(unmigrated) > 10:
                print(f"  ... 以及其他 {len(unmigrated) - 10} 个产品")
            print("-" * 80)

        # 生成详细报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'data/temp/product_name_migration_report_{timestamp}.json'

        os.makedirs('data/temp', exist_ok=True)

        report = {
            'timestamp': timestamp,
            'total_to_migrate': len(products_to_migrate),
            'migrated_count': len(migrated),
            'unmigrated_count': len(unmigrated),
            'migrated_products': migrated,
            'unmigrated_products': unmigrated
        }

        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n📄 详细迁移报告已保存到: {report_file}")

        return report

def list_all_subcategories():
    """列出所有可用的ProductSubcategory（调试用）"""
    app = create_app()
    with app.app_context():
        subcategories = ProductSubcategory.query.order_by(ProductSubcategory.id).all()

        print("\n" + "=" * 80)
        print("所有可用的ProductSubcategory".center(80))
        print("=" * 80)
        for sc in subcategories:
            print(f"  ID: {sc.id:3d} | 名称: {sc.name:30s} | 分类ID: {sc.category_id}")
        print("=" * 80 + "\n")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='产品名称字段数据迁移工具')
    parser.add_argument('--analyze', action='store_true', help='分析当前迁移状态')
    parser.add_argument('--migrate', action='store_true', help='执行数据迁移')
    parser.add_argument('--list-subcategories', action='store_true', help='列出所有ProductSubcategory')

    args = parser.parse_args()

    if args.analyze:
        analyze_migration_status()
    elif args.migrate:
        status = analyze_migration_status()
        if status['with_product_name'] > 0:
            confirm = input(f"\n是否确认迁移 {status['with_product_name']} 个产品？(yes/no): ").strip().lower()
            if confirm == 'yes':
                migrate_product_names()
            else:
                print("❌ 操作已取消")
        else:
            print("✅ 无需迁移")
    elif args.list_subcategories:
        list_all_subcategories()
    else:
        print("使用说明：")
        print("  分析状态：   python migrate_product_name_to_subcategory.py --analyze")
        print("  执行迁移：   python migrate_product_name_to_subcategory.py --migrate")
        print("  查看分类：   python migrate_product_name_to_subcategory.py --list-subcategories")
