#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理直放站范围产品的孤儿规格（field_value 为空）+ 重建受影响产品快照。

一次性脚本，完成后可删除。
"""
import sys, os

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

app = create_app()

# 直放站范围 product_ids（仅 active 产品）
TARGET_IDS = [59, 60, 66, 67, 68, 74, 75, 76, 78, 79]

with app.app_context():
    # 查询孤儿规格：field_value 为空字符串或纯空白
    orphans = ProductSpec.query.filter(
        ProductSpec.product_id.in_(TARGET_IDS),
        db.or_(
            ProductSpec.field_value == '',
            ProductSpec.field_value == None,
            db.func.trim(ProductSpec.field_value) == ''
        )
    ).all()

    if not orphans:
        print("未发现孤儿规格，无需清理。")
        sys.exit(0)

    # 按 product_id 分组输出详情
    affected_product_ids = set()
    print(f"\n发现 {len(orphans)} 条孤儿规格：\n")
    for spec in orphans:
        print(f"  product_id={spec.product_id}  id={spec.id}  "
              f"field_name={spec.field_name!r}  field_value={spec.field_value!r}")
        affected_product_ids.add(spec.product_id)

    # 删除孤儿记录
    for spec in orphans:
        db.session.delete(spec)
    print(f"\n已删除 {len(orphans)} 条孤儿规格。")

    # 重建受影响产品的快照
    print(f"\n重建 {len(affected_product_ids)} 个产品的快照...\n")
    for pid in sorted(affected_product_ids):
        product = Product.query.get(pid)
        if product:
            snapshot = generate_product_snapshot(product)
            product.spec_snapshot = snapshot
            print(f"  product_id={pid} ({product.name}) 快照已重建")

    db.session.commit()
    print("\n清理完成。")
