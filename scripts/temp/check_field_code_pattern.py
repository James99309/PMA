#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查字段的code属性和选项编码模式"""
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
from app.models.product_code import ProductCodeField, ProductCodeFieldOption, ProductSubcategory

app = create_app()

print("=" * 80)
print("检查字段的 code 属性和选项编码模式")
print("=" * 80)

with app.app_context():
    # 查找频率范围字段
    freq_fields = ProductCodeField.query.filter_by(
        name='频率范围',
        field_type='spec'
    ).limit(5).all()

    print(f'\n找到 {len(freq_fields)} 个频率范围字段\n')

    for f in freq_fields:
        subcategory = ProductSubcategory.query.get(f.subcategory_id)
        product_name = subcategory.name if subcategory else '未分配'

        print(f'产品: {product_name}')
        print(f'  字段ID: {f.id}')
        print(f'  字段code: "{f.code}"')
        print(f'  use_in_code: {f.use_in_code}')
        print(f'  max_length: {f.max_length}')

        # 查看该字段的选项编码
        options = f.options.limit(10).all()
        if options:
            print(f'  选项编码示例 ({len(options)} 个):')
            for opt in options:
                print(f'    "{opt.value}" → code="{opt.code}"')
        else:
            print(f'  （该字段没有预定义选项）')
        print()

    # 查看其他类型的字段
    print("\n" + "=" * 80)
    print("检查其他规格字段的编码模式")
    print("=" * 80)

    other_fields = ProductCodeField.query.filter_by(
        field_type='spec',
        use_in_code=True
    ).limit(5).all()

    for f in other_fields:
        subcategory = ProductSubcategory.query.get(f.subcategory_id)
        product_name = subcategory.name if subcategory else '未分配'

        options = f.options.limit(3).all()
        if options:
            print(f'\n产品: {product_name} | 规格: {f.name}')
            print(f'  字段code: "{f.code}" | max_length: {f.max_length}')
            print(f'  选项编码:')
            for opt in options:
                print(f'    "{opt.value}" → "{opt.code}"')

print("\n" + "=" * 80)
print("完成")
print("=" * 80)
