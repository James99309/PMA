#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查研发产品MN编码与region_id字段不匹配的问题
"""
import sys, os

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
from app.models.dev_product import DevProduct
from app.models.product_code import ProductCodeField, ProductCodeFieldOption

app = create_app()

with app.app_context():
    print("=" * 80)
    print("检查研发产品MN编码与region_id不匹配的问题")
    print("=" * 80)

    # 获取所有region字段（origin_location类型）
    region_fields = ProductCodeField.query.filter_by(
        field_type='origin_location'
    ).order_by(ProductCodeField.position).all()

    print("\n可用的区域字段：")
    region_code_map = {}
    for field in region_fields:
        # 检查字段是否有直接的code
        code = field.code
        if not code or code == "?":
            # 如果字段本身没有code，检查其选项
            option = ProductCodeFieldOption.query.filter_by(field_id=field.id).first()
            code = option.code if option else None

        if code:
            region_code_map[code] = field
            print(f"  - ID: {field.id}, 名称: {field.name}, 编码: {code}")

    # 查找所有研发产品
    dev_products = DevProduct.query.filter(
        DevProduct.mn_code.isnot(None),
        DevProduct.mn_code != ''
    ).all()

    print(f"\n找到 {len(dev_products)} 个有MN编码的研发产品")
    print("-" * 80)

    mismatched_products = []

    for product in dev_products:
        mn_code = product.mn_code
        region_id = product.region_id

        # 解析MN编码获取区域编码（第5位，0-indexed为4）
        if len(mn_code) >= 5:
            region_code_in_mn = mn_code[4]

            # 检查是否匹配
            if region_id is None:
                mismatched_products.append({
                    'id': product.id,
                    'name': product.name,
                    'model': product.model,
                    'mn_code': mn_code,
                    'region_code_in_mn': region_code_in_mn,
                    'region_id': None,
                    'issue': 'region_id为空'
                })
            else:
                # 检查region_id对应的字段
                region_field = ProductCodeField.query.get(region_id)
                if region_field:
                    # 获取字段的编码
                    field_code = region_field.code
                    if not field_code or field_code == "?":
                        option = ProductCodeFieldOption.query.filter_by(
                            field_id=region_field.id
                        ).first()
                        field_code = option.code if option else None

                    if field_code != region_code_in_mn:
                        mismatched_products.append({
                            'id': product.id,
                            'name': product.name,
                            'model': product.model,
                            'mn_code': mn_code,
                            'region_code_in_mn': region_code_in_mn,
                            'region_id': region_id,
                            'region_name': region_field.name,
                            'region_code': field_code,
                            'issue': f'MN编码中区域为"{region_code_in_mn}"，但region_id指向"{region_field.name}"(编码:{field_code})'
                        })

    if mismatched_products:
        print(f"\n发现 {len(mismatched_products)} 个不匹配的产品：\n")
        for p in mismatched_products:
            print(f"产品ID: {p['id']}")
            print(f"  名称: {p['name']}")
            print(f"  型号: {p['model']}")
            print(f"  MN编码: {p['mn_code']}")
            print(f"  MN中区域编码: {p['region_code_in_mn']}")
            print(f"  region_id: {p['region_id']}")
            if p['region_id']:
                print(f"  region名称: {p['region_name']}")
                print(f"  region编码: {p['region_code']}")
            print(f"  问题: {p['issue']}")

            # 尝试找到正确的region_id
            if p['region_code_in_mn'] in region_code_map:
                correct_field = region_code_map[p['region_code_in_mn']]
                print(f"  建议修复: region_id应为 {correct_field.id} ({correct_field.name})")
            else:
                print(f"  建议修复: 未找到编码为'{p['region_code_in_mn']}'的区域，需要创建或MN编码有误")
            print("-" * 80)
    else:
        print("\n✅ 所有研发产品的MN编码与region_id字段匹配！")

    print("\n检查完成！")
