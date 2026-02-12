#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量生成缺失的产品编码定义快照

为所有 code_definition_snapshot 为 NULL 或 code_parts 为空的产品重新生成快照数据。
使用与产品创建/编辑相同的通用快照生成函数，确保格式统一。
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
from app.utils.product_helpers import generate_product_snapshot
from sqlalchemy import or_, text


def generate_missing_snapshots(dry_run=False, force=False):
    """
    批量生成缺失的产品快照

    Args:
        dry_run: 如果为True，只显示预览不实际更新数据库
        force: 如果为True，跳过交互确认直接执行
    """
    app = create_app()

    with app.app_context():
        print("=" * 70)
        print("批量生成产品编码定义快照")
        print("=" * 70)
        print()

        # 查询所有快照为NULL或code_parts为空的产品
        # 注意: code_definition_snapshot 是 JSON 类型，需要 cast 到 jsonb 进行操作
        products_without_snapshot = Product.query.filter(
            or_(
                Product.code_definition_snapshot.is_(None),
                text("code_definition_snapshot::text = '{}'"),
                text("code_definition_snapshot::jsonb->'code_parts' = '[]'::jsonb"),
                text("NOT (code_definition_snapshot::jsonb ? 'code_parts')")
            )
        ).order_by(Product.id).all()

        # 过滤：只保留有 ProductSpec 数据的产品（否则生成快照也是空的）
        products_with_specs = []
        products_no_specs = []
        for p in products_without_snapshot:
            spec_count = ProductSpec.query.filter_by(product_id=p.id).count()
            if spec_count > 0:
                products_with_specs.append((p, spec_count))
            else:
                products_no_specs.append(p)

        print(f"📊 找到 {len(products_without_snapshot)} 个产品缺少有效快照")
        print(f"   其中 {len(products_with_specs)} 个有规格数据（可生成快照）")
        print(f"   其中 {len(products_no_specs)} 个无规格数据（跳过）")
        print()

        products_without_snapshot = [p for p, _ in products_with_specs]

        total_count = len(products_without_snapshot)
        print(f"📊 找到 {total_count} 个产品缺少快照")
        print()

        if total_count == 0:
            print("✅ 所有产品都已有快照，无需处理")
            return

        # 统计信息
        success_count = 0
        skip_count = 0
        failed_count = 0

        # 显示前10个示例
        if total_count > 0:
            print("示例产品（前10个）：")
            for i, product in enumerate(products_without_snapshot[:10], 1):
                name = product.product_name or (product.subcategory_obj.name if product.subcategory_obj else 'N/A')
                print(f"  {i}. ID={product.id}, MN={product.product_mn}, 名称={name}")
            if total_count > 10:
                print(f"  ... 还有 {total_count - 10} 个产品")
            print()

        # 确认执行
        if dry_run:
            print("⚠️  预览模式：不会实际更新数据库")
        elif not force:
            confirmation = input(f"是否继续处理这 {total_count} 个产品？(yes/no): ").strip().lower()
            if confirmation not in ['yes', 'y']:
                print("❌ 操作已取消")
                return

        print()
        print("开始处理...")
        print("-" * 70)

        # 处理每个产品
        for i, product in enumerate(products_without_snapshot, 1):
            try:
                # 生成快照
                snapshot = generate_product_snapshot(
                    product=product,
                    source="batch_generate"  # 标记为批量生成
                )

                if snapshot:
                    if not dry_run:
                        product.code_definition_snapshot = snapshot
                        db.session.flush()

                    success_count += 1
                    status = "✅ 成功"
                    code_parts_count = len(snapshot.get('code_parts', []))
                    detail = f"{code_parts_count}个规格字段"
                else:
                    skip_count += 1
                    status = "⚠️  跳过"
                    detail = "规格数据不完整（无field_code）"

                print(f"[{i}/{total_count}] {status} - "
                      f"ID={product.id}, MN={product.product_mn}, {detail}")

            except Exception as e:
                failed_count += 1
                print(f"[{i}/{total_count}] ❌ 失败 - "
                      f"ID={product.id}, MN={product.product_mn}, 错误: {str(e)}")

        # 提交更改
        if not dry_run and success_count > 0:
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
        print(f"  ✅ 成功生成: {success_count}")
        print(f"  ⚠️  跳过: {skip_count}")
        print(f"  ❌ 失败: {failed_count}")
        print("=" * 70)

        if skip_count > 0:
            print()
            print("跳过原因：产品规格中没有 field_code（编码字段），无法生成快照")
            print("这些产品需要先完善规格数据后再重新运行此脚本")

        if products_no_specs:
            print()
            print(f"⚠️  另有 {len(products_no_specs)} 个产品无规格数据，未处理：")
            for p in products_no_specs[:10]:
                print(f"    ID={p.id}, MN={p.product_mn}, 名称={p.product_name}")
            if len(products_no_specs) > 10:
                print(f"    ... 还有 {len(products_no_specs) - 10} 个")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='批量生成缺失的产品编码定义快照')
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='预览模式，不实际更新数据库'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='跳过交互确认直接执行'
    )

    args = parser.parse_args()

    try:
        generate_missing_snapshots(dry_run=args.dry_run, force=args.force)
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
