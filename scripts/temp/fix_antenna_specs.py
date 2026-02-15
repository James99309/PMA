#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复「天线」分类 9个活跃产品规格编码
产品ID: 104-111, 113
重建快照 + specification文本

Usage:
  export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib
  python3 scripts/temp/fix_antenna_specs.py [--dry-run]
"""
import sys
import os
import json

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
from app.utils.product_helpers import generate_product_snapshot, generate_spec_mn

PRODUCT_IDS = [104, 105, 106, 107, 108, 109, 110, 111, 113]

def rebuild_snapshots(dry_run=False):
    """重建所有天线产品的快照和specification文本"""
    app = create_app()
    with app.app_context():
        from app.routes.product_code import get_field_unit

        for pid in PRODUCT_IDS:
            product = Product.query.get(pid)
            if not product:
                print(f"  [SKIP] 产品 {pid} 不存在")
                continue

            specs = ProductSpec.query.filter_by(product_id=pid)\
                .order_by(ProductSpec.display_order).all()

            # 1. 重建 specification 文本
            is_ovs = app.config.get('IS_OVS', False)
            description_parts = []
            for spec in specs:
                if spec.include_in_description and spec.field_value:
                    unit = get_field_unit(spec.field_name) or ''
                    unit_str = f" {unit}" if unit else ""
                    if is_ovs and spec.field_name_en:
                        field_display_name = spec.field_name_en
                    else:
                        field_display_name = spec.field_name
                    description_parts.append(f"{field_display_name}: {spec.field_value}{unit_str}")
            new_description = ", ".join(description_parts) if description_parts else ""

            # 2. 重新生成 MN 编码
            new_mn = generate_spec_mn(product)

            # 3. 重建快照
            snapshot = generate_product_snapshot(product, source="manual_update")

            print(f"  [{'DRY' if dry_run else 'OK'}] 产品 {pid} ({product.product_name})")
            print(f"       规格数: {len(specs)}")
            print(f"       specification: {new_description[:80]}...")
            print(f"       MN: {product.product_mn} → {new_mn}")
            print(f"       快照: {'生成成功' if snapshot else '生成失败'}")

            if not dry_run:
                product.specification = new_description
                if new_mn and not product.is_mn_locked:
                    product.product_mn = new_mn
                if snapshot:
                    product.code_definition_snapshot = json.dumps(snapshot, ensure_ascii=False)

        if not dry_run:
            db.session.commit()
            print(f"\n✅ 已更新 {len(PRODUCT_IDS)} 个产品的快照和specification")
        else:
            print(f"\n[DRY RUN] 未做任何修改")


def verify_codes():
    """验证所有code是否与字典匹配"""
    app = create_app()
    with app.app_context():
        from app.models.product_code import SpecificationDictionary, SpecificationOption

        errors = []
        for pid in PRODUCT_IDS:
            specs = ProductSpec.query.filter_by(product_id=pid)\
                .order_by(ProductSpec.display_order).all()
            for spec in specs:
                dict_entry = SpecificationDictionary.query.filter_by(name=spec.field_name).first()
                if not dict_entry:
                    errors.append(f"  产品{pid} {spec.field_name}={spec.field_value} → 无字典条目")
                    continue
                option = SpecificationOption.query.filter_by(
                    spec_id=dict_entry.id, value=spec.field_value).first()
                if not option:
                    errors.append(f"  产品{pid} {spec.field_name}={spec.field_value} → 无字典选项")
                    continue
                if spec.field_code != option.code:
                    errors.append(f"  产品{pid} {spec.field_name}={spec.field_value} code={spec.field_code} 应为={option.code}")

        if errors:
            print(f"\n❌ 发现 {len(errors)} 个code不匹配:")
            for e in errors:
                print(e)
        else:
            print(f"\n✅ 所有 {len(PRODUCT_IDS)} 个产品的code全部匹配字典")


if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv

    print("=" * 60)
    print("修复「天线」分类 9个产品 - 重建快照")
    print("=" * 60)

    rebuild_snapshots(dry_run=dry_run)
    verify_codes()
