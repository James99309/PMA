#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断研发产品规格字段加载问题"""
import sys, os

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
from app.models.product_code import ProductCodeField, ProductFieldValue
from app.models.product import ProductCategory, ProductSubCategory

app = create_app()
with app.app_context():
    print("=" * 80)
    print("1. 查找'常规数字基站'子分类")
    print("=" * 80)
    
    # 查找子分类
    subcategory = ProductSubCategory.query.filter(
        ProductSubCategory.name.ilike('%常规数字基站%')
    ).first()
    
    if not subcategory:
        print("❌ 未找到'常规数字基站'子分类")
        print("\n所有子分类列表：")
        all_subs = ProductSubCategory.query.all()
        for sub in all_subs:
            print(f"  - ID: {sub.id}, 名称: {sub.name}, 分类ID: {sub.category_id}")
        sys.exit(1)
    
    print(f"✅ 找到子分类:")
    print(f"   ID: {subcategory.id}")
    print(f"   名称: {subcategory.name}")
    print(f"   分类ID: {subcategory.category_id}")
    print(f"   分类名称: {subcategory.category.name if subcategory.category else 'N/A'}")
    
    print("\n" + "=" * 80)
    print("2. 查询该子分类下的规格字段定义")
    print("=" * 80)
    
    fields = ProductCodeField.query.filter_by(
        subcategory_id=subcategory.id
    ).order_by(ProductCodeField.display_order).all()
    
    print(f"\n找到 {len(fields)} 个规格字段:")
    print("-" * 80)
    
    for field in fields:
        print(f"\n字段 #{field.id}:")
        print(f"  字段名: {field.field_name}")
        print(f"  字段类型: {field.field_type}")
        print(f"  是否必填: {field.is_required}")
        print(f"  用于编码: {field.use_in_code}")
        print(f"  显示顺序: {field.display_order}")
        print(f"  分组: {field.group_name or 'N/A'}")
        
        # 如果是选项类型，显示选项
        if field.field_type in ['select', 'radio']:
            if field.options:
                print(f"  选项: {field.options}")
        
        # 检查是否有实际使用记录
        usage_count = ProductFieldValue.query.filter_by(field_id=field.id).count()
        print(f"  使用次数: {usage_count}")
    
    print("\n" + "=" * 80)
    print("3. 检查字段的关键配置")
    print("=" * 80)
    
    # 统计字段类型分布
    from collections import Counter
    type_counter = Counter([f.field_type for f in fields])
    print(f"\n字段类型分布:")
    for field_type, count in type_counter.items():
        print(f"  {field_type}: {count}个")
    
    # 检查用于编码的字段
    code_fields = [f for f in fields if f.use_in_code]
    print(f"\n用于编码的字段: {len(code_fields)}个")
    for f in code_fields:
        print(f"  - {f.field_name} ({f.field_type})")
    
    # 检查必填字段
    required_fields = [f for f in fields if f.is_required]
    print(f"\n必填字段: {len(required_fields)}个")
    for f in required_fields:
        print(f"  - {f.field_name} ({f.field_type})")

