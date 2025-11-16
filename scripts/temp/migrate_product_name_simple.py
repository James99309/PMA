#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""产品名称字段数据迁移脚本（简化版，直接使用数据库）

不依赖Flask应用，直接连接数据库执行迁移
"""
import os
import sys
import json
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 从环境变量获取数据库URL
database_url = os.getenv('DATABASE_URL', 'postgresql://nijie@localhost:5432/pma_local')

print(f"📊 连接数据库: {database_url}")

# 创建数据库引擎
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)

def analyze_migration_status():
    """分析当前迁移状态"""
    session = Session()
    try:
        # 统计产品数量
        result = session.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(subcategory_id) as with_subcategory,
                COUNT(*) - COUNT(subcategory_id) as without_subcategory,
                COUNT(CASE WHEN subcategory_id IS NULL AND product_name IS NOT NULL AND product_name != '' THEN 1 END) as with_product_name
            FROM products
        """))
        stats = result.fetchone()

        print("\n" + "=" * 80)
        print("产品名称字段迁移状态分析".center(80))
        print("=" * 80)
        print(f"  总产品数：           {stats[0]:6d}")
        print(f"  已使用新字段：       {stats[1]:6d} ({stats[1]/stats[0]*100:.1f}%)" if stats[0] > 0 else "  已使用新字段：       0")
        print(f"  未使用新字段：       {stats[2]:6d} ({stats[2]/stats[0]*100:.1f}%)" if stats[0] > 0 else "  未使用新字段：       0")
        print(f"  有旧字段值可迁移：   {stats[3]:6d}")
        print("=" * 80 + "\n")

        return {
            'total': stats[0],
            'with_subcategory': stats[1],
            'without_subcategory': stats[2],
            'with_product_name': stats[3]
        }
    finally:
        session.close()

def list_all_subcategories():
    """列出所有可用的ProductSubcategory"""
    session = Session()
    try:
        result = session.execute(text("""
            SELECT id, name, category_id
            FROM product_subcategories
            ORDER BY id
        """))
        subcategories = result.fetchall()

        print("\n" + "=" * 80)
        print("所有可用的ProductSubcategory".center(80))
        print("=" * 80)
        for sc in subcategories:
            print(f"  ID: {sc[0]:3d} | 名称: {sc[1]:30s} | 分类ID: {sc[2]}")
        print("=" * 80 + "\n")

        return subcategories
    finally:
        session.close()

def migrate_product_names():
    """执行数据迁移"""
    session = Session()
    try:
        print("📋 开始迁移产品名称数据...")

        # 查找所有没有subcategory_id但有product_name的产品
        result = session.execute(text("""
            SELECT id, product_mn, product_name, model
            FROM products
            WHERE subcategory_id IS NULL
              AND product_name IS NOT NULL
              AND product_name != ''
        """))
        products_to_migrate = result.fetchall()

        if not products_to_migrate:
            print("✅ 所有产品已经使用新字段或无需迁移")
            return

        print(f"\n找到 {len(products_to_migrate)} 个需要迁移的产品\n")

        migrated = []
        unmigrated = []

        for product in products_to_migrate:
            product_id, product_mn, product_name, model = product

            # 尝试通过product_name匹配ProductSubcategory
            result = session.execute(text("""
                SELECT id, name
                FROM product_subcategories
                WHERE TRIM(name) = :product_name
            """), {'product_name': product_name.strip()})
            subcategory = result.fetchone()

            if subcategory:
                # 找到匹配，更新subcategory_id
                session.execute(text("""
                    UPDATE products
                    SET subcategory_id = :subcategory_id
                    WHERE id = :product_id
                """), {
                    'subcategory_id': subcategory[0],
                    'product_id': product_id
                })

                migrated.append({
                    'id': product_id,
                    'product_mn': product_mn or 'N/A',
                    'product_name': product_name,
                    'subcategory_id': subcategory[0],
                    'matched_name': subcategory[1]
                })
                print(f"  ✅ 产品 ID={product_id:4d} MN={product_mn or 'N/A':20s} 名称='{product_name}' → subcategory_id={subcategory[0]}")
            else:
                unmigrated.append({
                    'id': product_id,
                    'product_mn': product_mn or 'N/A',
                    'product_name': product_name,
                    'model': model or ''
                })
                print(f"  ⚠️  产品 ID={product_id:4d} MN={product_mn or 'N/A':20s} 名称='{product_name}' → 找不到匹配的ProductSubcategory")

        # 提交事务
        if migrated:
            session.commit()
            print(f"\n✅ 成功迁移 {len(migrated)} 个产品")

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

    except Exception as e:
        session.rollback()
        print(f"\n❌ 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='产品名称字段数据迁移工具（简化版）')
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
        print("  分析状态：   python migrate_product_name_simple.py --analyze")
        print("  执行迁移：   python migrate_product_name_simple.py --migrate")
        print("  查看分类：   python migrate_product_name_simple.py --list-subcategories")
