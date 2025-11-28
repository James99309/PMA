#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量更新产品快照脚本

重新生成所有标准产品的 code_definition_snapshot，
使其包含所有规格（编码规格 + 非编码规格）。

使用方法:
    python scripts/temp/update_product_snapshots.py
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
from app.utils.product_helpers import generate_product_snapshot


def update_all_snapshots():
    """批量更新所有标准产品的快照"""
    app = create_app()

    with app.app_context():
        # 查询所有产品（排除空类型和project类型）
        products = Product.query.filter(
            Product.type.in_(['channel', 'third party', 'standard'])
        ).all()

        print(f"找到 {len(products)} 个标准产品")

        updated = 0
        failed = 0
        skipped = 0

        for product in products:
            try:
                # 生成新快照
                snapshot = generate_product_snapshot(
                    product=product,
                    source="batch_update"
                )

                if snapshot:
                    old_count = 0
                    if product.code_definition_snapshot:
                        old_parts = product.code_definition_snapshot.get('code_parts', [])
                        old_count = len(old_parts)

                    new_count = len(snapshot.get('code_parts', []))

                    product.code_definition_snapshot = snapshot
                    updated += 1
                    print(f"✓ [{product.id}] {product.model}: {old_count} → {new_count} 项规格")
                else:
                    skipped += 1
                    print(f"- [{product.id}] {product.model}: 跳过（无规格数据）")

            except Exception as e:
                failed += 1
                print(f"✗ [{product.id}] {product.model}: 失败 - {str(e)}")

        # 提交更改
        if updated > 0:
            db.session.commit()
            print(f"\n完成！更新: {updated}, 跳过: {skipped}, 失败: {failed}")
        else:
            print(f"\n无需更新。跳过: {skipped}, 失败: {failed}")


if __name__ == '__main__':
    update_all_snapshots()
