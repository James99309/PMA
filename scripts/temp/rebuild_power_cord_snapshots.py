#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""重建电源线类型更新后的产品快照和描述"""
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
from app.services.spec_service import SpecService

app = create_app()
with app.app_context():
    # 查找有"电源线类型"规格的产品
    product_ids = db.session.query(ProductSpec.product_id).filter(
        ProductSpec.field_name == '电源线类型'
    ).distinct().all()
    product_ids = [pid[0] for pid in product_ids]

    print(f"需要重建快照的产品: {len(product_ids)} 个")

    count = 0
    for pid in product_ids:
        product = Product.query.get(pid)
        if not product or product.is_deleted:
            continue
        snap = generate_product_snapshot(product, source='batch_regenerate')
        if snap:
            product.code_definition_snapshot = snap
        product.specification = SpecService.generate_description(SpecService.TYPE_PRODUCT, pid)
        count += 1

    db.session.commit()
    print(f"完成: {count} 个产品快照+描述已重建")
