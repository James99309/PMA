#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量锁定产品MN编码脚本

功能：
1. 锁定所有现有产品的MN编码（is_mn_locked=True）
2. 防止已有产品被意外修改MN编码
3. 支持按条件筛选锁定（可选）

使用场景：
- 初次部署MN锁定功能时，批量锁定已有产品
- 手动保护特定产品不被修改
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

def lock_all_products():
    """锁定所有未锁定的产品"""
    app = create_app()
    with app.app_context():
        try:
            # 查询所有未锁定的产品
            unlocked_products = Product.query.filter(
                (Product.is_mn_locked == False) | (Product.is_mn_locked == None)
            ).all()

            if not unlocked_products:
                print("✅ 所有产品已经处于锁定状态")
                return

            print(f"📋 找到 {len(unlocked_products)} 个未锁定的产品")
            print("\n即将锁定以下产品：")
            print("-" * 80)

            for product in unlocked_products[:10]:  # 只显示前10个作为示例
                print(f"  ID: {product.id:4d} | MN: {product.product_mn or 'N/A':20s} | 型号: {product.model or 'N/A'}")

            if len(unlocked_products) > 10:
                print(f"  ... 以及其他 {len(unlocked_products) - 10} 个产品")

            print("-" * 80)

            # 确认操作
            confirm = input(f"\n是否确认锁定这 {len(unlocked_products)} 个产品？(yes/no): ").strip().lower()

            if confirm != 'yes':
                print("❌ 操作已取消")
                return

            # 批量锁定
            locked_count = 0
            for product in unlocked_products:
                product.is_mn_locked = True
                locked_count += 1

            db.session.commit()
            print(f"\n✅ 成功锁定 {locked_count} 个产品")

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 批量锁定失败: {str(e)}")
            import traceback
            traceback.print_exc()

def lock_products_by_ids(product_ids):
    """按产品ID列表锁定指定产品"""
    app = create_app()
    with app.app_context():
        try:
            products = Product.query.filter(Product.id.in_(product_ids)).all()

            if not products:
                print("❌ 未找到指定的产品")
                return

            print(f"📋 找到 {len(products)} 个产品")

            for product in products:
                print(f"  ID: {product.id:4d} | MN: {product.product_mn or 'N/A':20s} | 锁定状态: {product.is_mn_locked}")
                product.is_mn_locked = True

            db.session.commit()
            print(f"\n✅ 成功锁定 {len(products)} 个产品")

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 锁定失败: {str(e)}")

def unlock_products_by_ids(product_ids):
    """按产品ID列表解锁指定产品（仅管理员使用）"""
    app = create_app()
    with app.app_context():
        try:
            products = Product.query.filter(Product.id.in_(product_ids)).all()

            if not products:
                print("❌ 未找到指定的产品")
                return

            print(f"📋 找到 {len(products)} 个产品")

            for product in products:
                print(f"  ID: {product.id:4d} | MN: {product.product_mn or 'N/A':20s} | 锁定状态: {product.is_mn_locked}")
                product.is_mn_locked = False

            db.session.commit()
            print(f"\n✅ 成功解锁 {len(products)} 个产品")

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ 解锁失败: {str(e)}")

def show_lock_status():
    """显示产品锁定状态统计"""
    app = create_app()
    with app.app_context():
        total = Product.query.count()
        locked = Product.query.filter(Product.is_mn_locked == True).count()
        unlocked = total - locked

        print("\n" + "=" * 80)
        print("产品MN锁定状态统计".center(80))
        print("=" * 80)
        print(f"  总产品数：   {total:6d}")
        print(f"  已锁定：     {locked:6d} ({locked/total*100:.1f}%)" if total > 0 else "  已锁定：     0")
        print(f"  未锁定：     {unlocked:6d} ({unlocked/total*100:.1f}%)" if total > 0 else "  未锁定：     0")
        print("=" * 80 + "\n")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='产品MN编码批量锁定工具')
    parser.add_argument('--lock-all', action='store_true', help='锁定所有未锁定的产品')
    parser.add_argument('--lock-ids', type=str, help='锁定指定ID的产品（逗号分隔，如：1,2,3）')
    parser.add_argument('--unlock-ids', type=str, help='解锁指定ID的产品（逗号分隔）')
    parser.add_argument('--status', action='store_true', help='显示锁定状态统计')

    args = parser.parse_args()

    if args.status:
        show_lock_status()
    elif args.lock_all:
        lock_all_products()
    elif args.lock_ids:
        ids = [int(id.strip()) for id in args.lock_ids.split(',')]
        lock_products_by_ids(ids)
    elif args.unlock_ids:
        ids = [int(id.strip()) for id in args.unlock_ids.split(',')]
        unlock_products_by_ids(ids)
    else:
        print("使用说明：")
        print("  显示状态：   python lock_existing_products.py --status")
        print("  锁定所有：   python lock_existing_products.py --lock-all")
        print("  锁定指定：   python lock_existing_products.py --lock-ids 1,2,3")
        print("  解锁指定：   python lock_existing_products.py --unlock-ids 1,2,3")
