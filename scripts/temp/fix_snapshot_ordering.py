#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复快照 code_parts 排序不一致问题

问题：generate_code_definition_snapshot() 按 ProductSpec.id 排序，
      而 ProductCode.generate_snapshot() 按字典 position 排序，
      导致同子分类下不同产品的 code_parts 顺序不一致，前端错位。

修复：重新生成所有产品的 code_definition_snapshot，使用字典 position 排序。
"""
import sys
import os
from datetime import datetime

# 路径修正
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

app = create_app()

def fix_snapshots():
    """批量重新生成快照"""
    with app.app_context():
        # 查询所有有快照的产品
        products = Product.query.filter(
            Product.code_definition_snapshot.isnot(None),
            Product.is_deleted == False
        ).all()

        print(f"找到 {len(products)} 个有快照的产品")
        print("=" * 70)

        changed = 0
        unchanged = 0
        errors = 0

        for product in products:
            old_snapshot = product.code_definition_snapshot
            old_source = old_snapshot.get("source", "unknown") if old_snapshot else "unknown"

            # 提取旧的 use_in_code=true 的字段顺序
            old_code_fields = []
            if old_snapshot and "code_parts" in old_snapshot:
                old_code_fields = [
                    p["field_name"] for p in old_snapshot["code_parts"]
                    if p.get("use_in_code")
                ]

            # 重新生成快照（使用修复后的排序逻辑）
            new_snapshot = generate_product_snapshot(product, source=old_source)

            if not new_snapshot:
                print(f"  [ERROR] 产品 {product.id} ({product.product_mn}) 快照生成失败")
                errors += 1
                continue

            # 添加重排序时间戳
            new_snapshot["reordered_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")

            # 提取新的 use_in_code=true 的字段顺序
            new_code_fields = [
                p["field_name"] for p in new_snapshot["code_parts"]
                if p.get("use_in_code")
            ]

            # 比较顺序是否变化
            if old_code_fields != new_code_fields:
                print(f"  [CHANGED] 产品 {product.id} ({product.product_mn}) "
                      f"子分类={product.subcategory_id}")
                print(f"    旧顺序: {old_code_fields}")
                print(f"    新顺序: {new_code_fields}")
                changed += 1
            else:
                unchanged += 1

            # 更新快照
            product.code_definition_snapshot = new_snapshot

        db.session.commit()

        print("=" * 70)
        print(f"完成: {changed} 个顺序变化, {unchanged} 个无变化, {errors} 个错误")
        print(f"共更新 {changed + unchanged} 个快照")


if __name__ == "__main__":
    fix_snapshots()
