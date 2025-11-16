#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查规格字段的field_type定义"""
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
from app.models.product_code import ProductCodeField, ProductSubcategory  # 正确的类名

app = create_app()
with app.app_context():
    print("=" * 80)
    print("检查'常规数字基站'子分类的规格字段配置")
    print("=" * 80)
    
    # 查找子分类
    subcategory = ProductSubcategory.query.filter(
        ProductSubcategory.name.ilike('%常规数字基站%')
    ).first()
    
    if not subcategory:
        print("❌ 未找到'常规数字基站'子分类")
        print("\n所有子分类列表:")
        all_subs = ProductSubcategory.query.all()
        for sub in all_subs[:10]:  # 只显示前10个
            print(f"  - ID: {sub.id}, 名称: {sub.name}")
        sys.exit(1)
    
    print(f"\n✅ 子分类信息:")
    print(f"   ID: {subcategory.id}")
    print(f"   名称: {subcategory.name}")
    
    print(f"\n{'='*80}")
    print(f"查询该子分类下的所有规格字段（ProductCodeField）")
    print(f"{'='*80}\n")
    
    # 查询所有字段
    all_fields = ProductCodeField.query.filter_by(
        subcategory_id=subcategory.id
    ).order_by(ProductCodeField.position).all()
    
    print(f"总共找到 {len(all_fields)} 个字段:")
    print(f"{'-'*80}")
    
    if len(all_fields) == 0:
        print("\n❌ 没有找到任何字段！这说明数据库中没有规格定义。")
        sys.exit(1)
    
    # 统计field_type分布
    from collections import Counter
    type_counter = Counter([f.field_type for f in all_fields])
    
    print(f"\nfield_type分布统计:")
    for field_type, count in type_counter.items():
        print(f"  '{field_type}': {count}个")
    
    # 详细列出每个字段
    print(f"\n{'='*80}")
    print(f"详细字段信息:")
    print(f"{'='*80}\n")
    
    for field in all_fields:
        print(f"字段ID: {field.id}")
        print(f"  名称: {field.name}")
        print(f"  field_type: '{field.field_type}'  ← 关键字段！")
        print(f"  position: {field.position}")
        print(f"  use_in_code: {field.use_in_code}")
        print(f"  is_required: {field.is_required}")
        print()
    
    # 检查API查询条件
    print(f"{'='*80}")
    print(f"检查API查询条件（模拟spec-structure端点）")
    print(f"{'='*80}\n")
    
    # 模拟API查询条件
    spec_fields = ProductCodeField.query.filter(
        ProductCodeField.subcategory_id == subcategory.id,
        ProductCodeField.field_type == 'spec',  # ← 这是关键条件！
        (ProductCodeField.use_in_code == True) | (ProductCodeField.use_in_code.is_(None))
    ).order_by(ProductCodeField.position).all()
    
    print(f"查询条件:")
    print(f"  - subcategory_id = {subcategory.id}")
    print(f"  - field_type = 'spec'")
    print(f"  - use_in_code = True 或 None")
    print(f"\n查询结果: 找到 {len(spec_fields)} 个字段")
    
    if len(spec_fields) == 0 and len(all_fields) > 0:
        print("\n❌❌❌ 问题确认：field_type不是'spec'！ ❌❌❌")
        print("\n实际的field_type值是：")
        for ft in type_counter.keys():
            print(f"  - '{ft}'")
        print("\n✅ 解决方案：")
        print("  修改API查询条件，将 field_type == 'spec' 改为实际的field_type值")
    else:
        print("\n✅ 查询成功，这些字段应该能被加载")
        for field in spec_fields:
            print(f"  - {field.name} (position: {field.position})")

