#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为所有现有产品的code_definition_snapshot添加单位信息

为现有快照中的code_parts添加unit字段
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
from app.routes.product_code import get_field_unit


def add_units_to_existing_snapshots(dry_run=False):
    """
    为现有产品快照添加单位信息

    Args:
        dry_run: 如果为True，只显示预览不实际更新数据库
    """
    app = create_app()

    with app.app_context():
        print("=" * 70)
        print("为产品编码快照添加单位信息")
        print("=" * 70)
        print()

        # 查询所有有快照的产品
        products = Product.query.filter(
            Product.code_definition_snapshot.isnot(None)
        ).order_by(Product.id).all()

        total_count = len(products)
        print(f"📊 找到 {total_count} 个产品有快照")
        print()

        if total_count == 0:
            print("✅ 没有产品需要处理")
            return

        # 统计信息
        updated_count = 0
        skipped_count = 0
        failed_count = 0

        # 显示前10个示例
        if total_count > 0:
            print("示例产品（前10个）：")
            for i, product in enumerate(products[:10], 1):
                print(f"  {i}. ID={product.id}, MN={product.product_mn}, "
                      f"名称={product.subcategory.name if product.subcategory else 'N/A'}")
            if total_count > 10:
                print(f"  ... 还有 {total_count - 10} 个产品")
            print()

        # 确认执行
        if dry_run:
            print("⚠️  预览模式：不会实际更新数据库")
        else:
            confirmation = input(f"是否继续处理这 {total_count} 个产品？(yes/no): ").strip().lower()
            if confirmation not in ['yes', 'y']:
                print("❌ 操作已取消")
                return

        print()
        print("开始处理...")
        print("-" * 70)

        # 处理每个产品
        for i, product in enumerate(products, 1):
            try:
                snapshot = product.code_definition_snapshot

                if not snapshot or 'code_parts' not in snapshot:
                    skipped_count += 1
                    print(f"[{i}/{total_count}] ⚠️  跳过 - "
                          f"ID={product.id}, MN={product.product_mn} (快照格式不正确)")
                    continue

                # 检查是否需要添加单位
                modified = False
                parts_updated = 0

                for part in snapshot['code_parts']:
                    if 'unit' not in part and 'field_name' in part:
                        # 查询单位
                        unit = get_field_unit(part['field_name'])
                        part['unit'] = unit
                        modified = True
                        parts_updated += 1

                if modified:
                    if not dry_run:
                        # 更新快照
                        product.code_definition_snapshot = snapshot
                        db.session.flush()

                    updated_count += 1
                    status = "✅ 成功"
                    detail = f"更新了{parts_updated}个规格字段的单位"
                else:
                    skipped_count += 1
                    status = "⚠️  跳过"
                    detail = "快照已包含单位信息"

                print(f"[{i}/{total_count}] {status} - "
                      f"ID={product.id}, MN={product.product_mn}, {detail}")

            except Exception as e:
                failed_count += 1
                print(f"[{i}/{total_count}] ❌ 失败 - "
                      f"ID={product.id}, MN={product.product_mn}, 错误: {str(e)}")

        # 提交更改
        if not dry_run and updated_count > 0:
            try:
                db.session.commit()
                print()
                print("-" * 70)
                print("✅ 数据库已更新")
            except Exception as e:
                db.session.rollback()
                print()
                print("-" * 70)
                print(f"❌ 数据库提交失败: {str(e)}")
                return

        # 显示统计结果
        print()
        print("=" * 70)
        print("处理完成 - 统计结果")
        print("=" * 70)
        print(f"  总数: {total_count}")
        print(f"  ✅ 成功更新: {updated_count}")
        print(f"  ⚠️  跳过: {skipped_count}")
        print(f"  ❌ 失败: {failed_count}")
        print("=" * 70)

        if dry_run:
            print()
            print("这是预览模式，数据库未被修改。")
            print("要实际执行更新，请运行: python3 scripts/temp/add_units_to_snapshots.py")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='为产品快照添加单位信息')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='预览模式，不实际更新数据库'
    )

    args = parser.parse_args()

    try:
        add_units_to_existing_snapshots(dry_run=args.dry_run)
    except KeyboardInterrupt:
        print("\n\n⚠️  操作已取消")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
