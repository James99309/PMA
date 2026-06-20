#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
为现有发货单补 SN 数据（一次性数据补丁）

背景：
  SN 写入逻辑（shipment_routes.api_create_from_po）上线前已存在的 8 张发货单
  shipment_details.serial_numbers 全空，product_serial_numbers 表 0 行。
  本脚本按产品 model + 全局递增序号生成 SN，回填两处。

规则：
  - 仅处理 product.has_serial_number=True
  - 备货型明细（po_detail.sales_order_detail_id is None）的 SN 绑到厂商仓库 inventory_id
  - 销售型明细（直发客户）的 SN 不绑 inventory_id（未入厂商库存）
  - 同产品跨 shipment 序号连续递增（按 ship_date asc 排序）
"""
import sys, os, json
from datetime import datetime


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
from app.models.shipment import Shipment
from app.models.product_serial_number import ProductSerialNumber
from app.models.inventory import Inventory, PurchaseOrderDetail
from app.models.customer import Company


def main(dry_run=True):
    app = create_app()
    with app.app_context():
        vendor = Company.query.filter_by(
            company_type='vendor', is_deleted=False
        ).order_by(Company.id).first()
        if not vendor:
            print("❌ 未找到厂商公司 (company_type='vendor')")
            return
        print(f"厂商仓库公司: {vendor.company_name} (id={vendor.id})")

        # 按 ship_date asc, id asc 排序，确保跨 shipment 序号稳定
        shipments = Shipment.query.order_by(
            Shipment.ship_date.asc().nullsfirst(), Shipment.id.asc()
        ).all()

        seq_by_product = {}     # product_id -> next seq
        plan_rows = []          # (shp_no, detail_id, product_model, qty, sn_list, inv_id, kind)
        skipped = 0

        for shp in shipments:
            for d in shp.details:
                product = d.product
                if not product:
                    continue
                if not getattr(product, 'has_serial_number', True):
                    skipped += d.quantity
                    continue
                if not product.model:
                    print(f"  ⚠️ 产品 {product.name} 无 model，跳过")
                    continue

                qty = d.quantity
                seq_start = seq_by_product.get(product.id, 1)
                sn_list = [f'{product.model}-{str(seq_start + i).zfill(3)}'
                           for i in range(qty)]
                seq_by_product[product.id] = seq_start + qty

                # 备货 vs 销售
                po_detail = PurchaseOrderDetail.query.get(d.purchase_order_detail_id)
                is_stock = po_detail and not po_detail.sales_order_detail_id
                kind = '备货' if is_stock else '销售'

                inv_id = None
                if is_stock:
                    inv = Inventory.query.filter_by(
                        company_id=vendor.id, product_id=product.id
                    ).first()
                    inv_id = inv.id if inv else None

                plan_rows.append({
                    'shipment': shp,
                    'detail': d,
                    'po_detail': po_detail,
                    'product': product,
                    'sn_list': sn_list,
                    'inv_id': inv_id,
                    'kind': kind,
                })

        # 打印计划
        print(f"\n=== 计划摘要 ===")
        print(f"产品累计序号: {seq_by_product}")
        print(f"明细数: {len(plan_rows)}, 总 SN 数: {sum(len(r['sn_list']) for r in plan_rows)}, 跳过(无SN产品): {skipped}")
        print(f"\n=== 明细预览 ===")
        for r in plan_rows:
            sns = r['sn_list']
            preview = ', '.join(sns[:3]) + (f' … (+{len(sns)-3})' if len(sns) > 3 else '')
            print(f"  {r['shipment'].shipment_number} [{r['kind']}] {r['product'].model} x{len(sns)} "
                  f"inv={r['inv_id']}: {preview}")

        if dry_run:
            print("\n[DRY RUN] 未提交。重新运行带 --apply 执行。")
            return

        # 执行
        inserted, updated = 0, 0
        for r in plan_rows:
            shp = r['shipment']
            d = r['detail']
            po_detail = r['po_detail']

            # 1. 写 shipment_details.serial_numbers
            d.serial_numbers = json.dumps(r['sn_list'])
            updated += 1

            # 2. 插 ProductSerialNumber
            customer_id = shp.sales_order.customer_id if shp.sales_order else None
            for sn_str in r['sn_list']:
                existing = ProductSerialNumber.query.filter_by(serial_number=sn_str).first()
                if existing:
                    print(f"  ⚠️ {sn_str} 已存在,跳过")
                    continue
                rec = ProductSerialNumber(
                    serial_number=sn_str,
                    product_id=r['product'].id,
                    purchase_order_id=po_detail.order_id if po_detail else None,
                    purchase_detail_id=po_detail.id if po_detail else None,
                    sales_order_id=shp.sales_order_id,
                    shipment_id=shp.id,
                    customer_id=customer_id,
                    inventory_id=r['inv_id'],
                    status='in_stock',
                    warehouse_in_date=shp.ship_date or datetime.now(),
                    created_by_id=shp.created_by_id,
                )
                db.session.add(rec)
                inserted += 1

        db.session.commit()
        print(f"\n✅ 完成: 更新 {updated} 条发货明细, 插入 {inserted} 个 SN")


if __name__ == '__main__':
    apply_mode = '--apply' in sys.argv
    main(dry_run=not apply_mode)
