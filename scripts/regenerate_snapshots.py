#!/usr/bin/env python3
"""批量重新生成所有产品的 code_definition_snapshot"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.product import Product
from app.utils.product_helpers import generate_product_snapshot

app = create_app()

with app.app_context():
    products = Product.query.filter(Product.status != 'deleted').all()
    total = len(products)
    updated = 0
    failed = 0

    for i, product in enumerate(products):
        try:
            snapshot = generate_product_snapshot(product, source="batch_regenerate")
            if snapshot:
                product.code_definition_snapshot = snapshot
                updated += 1
            else:
                failed += 1
        except Exception as e:
            print(f"  [ERROR] 产品 {product.id} ({product.model}): {e}")
            failed += 1

        if (i + 1) % 50 == 0:
            db.session.commit()
            print(f"  进度: {i+1}/{total} (已更新 {updated}, 失败 {failed})")

    db.session.commit()
    print(f"\n完成: {total} 个产品, 更新 {updated}, 失败 {failed}")
