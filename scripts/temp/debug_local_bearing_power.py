#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断本地数据库中"承载功率"指标数据

检查：
1. "承载功率"规格字段是否存在
2. 预定义选项值
3. DevProductSpec表中的数据
4. ProductSpec表中的数据
5. 为何界面不显示预定义指标
"""
import sys
import os

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
from app.models.product_code import ProductCodeField, ProductCodeFieldOption
from app.models.dev_product import DevProduct, DevProductSpec
from app.models.product import Product
from app.models.product_spec import ProductSpec

# 创建应用（使用本地数据库配置）
app = create_app()

with app.app_context():
    print("=" * 80)
    print("诊断：本地数据库 - 承载功率指标数据")
    print("=" * 80)
    print(f"数据库URI: {app.config.get('SQLALCHEMY_DATABASE_URI', 'N/A')[:50]}...")
    print()

    # 1. 查找"承载功率"字段配置
    print("【步骤1】查找'承载功率'规格字段配置")
    print("-" * 80)

    field = ProductCodeField.query.filter_by(
        name='承载功率',
        field_type='spec',
        is_deleted=False
    ).first()

    if not field:
        print("❌ 未找到'承载功率'字段配置")
        print("\n尝试模糊搜索包含'功率'的字段：")
        similar_fields = ProductCodeField.query.filter(
            ProductCodeField.name.like('%功率%'),
            ProductCodeField.field_type == 'spec',
            ProductCodeField.is_deleted == False
        ).all()

        if similar_fields:
            for f in similar_fields:
                print(f"  - ID: {f.id}, 名称: '{f.name}', 产品: {f.subcategory.name if f.subcategory else 'N/A'}")
        else:
            print("  未找到任何包含'功率'的规格字段")

        sys.exit(1)

    print(f"✅ 找到字段配置:")
    print(f"  字段ID: {field.id}")
    print(f"  字段名称: '{field.name}'")
    print(f"  所属产品: {field.subcategory.name if field.subcategory else 'N/A'}")
    print(f"  产品ID: {field.subcategory_id}")

    # 2. 查找预定义选项
    print(f"\n【步骤2】查找预定义选项值")
    print("-" * 80)

    predefined_options = ProductCodeFieldOption.query.filter_by(
        field_id=field.id,
        is_deleted=False
    ).order_by(ProductCodeFieldOption.position).all()

    predefined_values = set()
    print(f"预定义选项数量: {len(predefined_options)}")
    if predefined_options:
        print("预定义选项列表:")
        for opt in predefined_options:
            if opt.value and opt.value.strip():
                predefined_values.add(opt.value.strip())
                active_mark = "✓" if opt.is_active else "✗"
                print(f"  [{active_mark}] {opt.value} (编码: {opt.code}, ID: {opt.id})")
    else:
        print("  ⚠️ (无预定义选项) - 这可能是问题所在！")

    print(f"\n预定义值集合: {predefined_values}")

    # 3. 查找DevProductSpec中的数据
    print(f"\n【步骤3】查找DevProductSpec表中的'承载功率'数据")
    print("-" * 80)

    dev_specs = DevProductSpec.query.filter_by(
        field_name=field.name
    ).all()

    print(f"DevProductSpec记录数: {len(dev_specs)}")

    dev_values = set()
    dev_products_map = {}

    if dev_specs:
        print("\nDevProductSpec数据详情:")
        for spec in dev_specs:
            dev_product = DevProduct.query.get(spec.dev_product_id)
            product_name = dev_product.name if dev_product else '未知产品'

            if spec.field_value and spec.field_value.strip():
                dev_values.add(spec.field_value.strip())

                if product_name not in dev_products_map:
                    dev_products_map[product_name] = set()
                dev_products_map[product_name].add(spec.field_value.strip())

                print(f"  产品: {product_name}")
                print(f"    值: {spec.field_value}")
                print(f"    产品ID: {spec.dev_product_id}")
                print()
    else:
        print("  (无数据)")

    print(f"DevProductSpec值集合: {dev_values}")
    print(f"涉及产品数量: {len(dev_products_map)}")
    if dev_products_map:
        print("按产品分组:")
        for product_name, values in dev_products_map.items():
            print(f"  - {product_name}: {values}")

    # 4. 查找ProductSpec中的数据
    print(f"\n【步骤4】查找ProductSpec表中的'承载功率'数据")
    print("-" * 80)

    product_specs = ProductSpec.query.filter_by(
        field_name=field.name
    ).all()

    print(f"ProductSpec记录数: {len(product_specs)}")

    product_values = set()
    products_map = {}

    if product_specs:
        print("\nProductSpec数据详情:")
        for spec in product_specs:
            product = Product.query.get(spec.product_id)
            product_name = product.name if product else '未知产品'

            if spec.field_value and spec.field_value.strip():
                product_values.add(spec.field_value.strip())

                if product_name not in products_map:
                    products_map[product_name] = set()
                products_map[product_name].add(spec.field_value.strip())

                print(f"  产品: {product_name}")
                print(f"    值: {spec.field_value}")
                print(f"    产品ID: {spec.product_id}")
                print()
    else:
        print("  (无数据)")

    print(f"ProductSpec值集合: {product_values}")
    print(f"涉及产品数量: {len(products_map)}")
    if products_map:
        print("按产品分组:")
        for product_name, values in products_map.items():
            print(f"  - {product_name}: {values}")

    # 5. 诊断结论
    print(f"\n【诊断结论】")
    print("=" * 80)

    if len(predefined_options) == 0:
        print("❌ 问题确认：本地数据库没有预定义指标选项！")
        print("\n原因分析:")
        print("  🔴 根本原因：ProductCodeFieldOption表中没有'承载功率'的预定义选项")
        print(f"     → 字段ID: {field.id}")
        print(f"     → 预定义选项数量: 0")
        print("\n解决方案：")
        print("  1. 在规格管理页面为'承载功率'字段添加预定义指标选项")
        print("  2. 或者从云端数据库同步预定义选项数据")
        print("  3. 添加预定义选项后，前端应该能正常显示")
    else:
        print("✅ 预定义选项存在")
        print(f"\n预定义选项: {predefined_values}")
        print(f"数量: {len(predefined_options)}")

        # 检查是否有不活跃的选项
        inactive_count = sum(1 for opt in predefined_options if not opt.is_active)
        if inactive_count > 0:
            print(f"\n⚠️ 注意：有 {inactive_count} 个不活跃的选项")
            print("   如果API设置了 include_inactive=false，这些选项不会显示")

        print("\n如果前端仍然不显示，请检查：")
        print("  1. API参数是否正确传递（field_id、include_inactive等）")
        print("  2. 浏览器Network标签中的实际API响应")
        print("  3. JavaScript控制台是否有错误")
        print("  4. fields.html 第408-409行是否注释了 include_product_values 参数")

    # 6. 对比云端和本地差异
    print(f"\n【云端vs本地对比】")
    print("-" * 80)
    print("云端SP8D数据库：")
    print("  - 预定义选项: 50 (A), 100 (B) - 2个选项")
    print(f"\n本地数据库：")
    print(f"  - 预定义选项: {len(predefined_options)}个")
    if predefined_options:
        print(f"  - 选项值: {', '.join(sorted(predefined_values))}")
    else:
        print("  - ⚠️ 本地没有预定义选项，需要添加！")

    print("\n" + "=" * 80)
    print("诊断完成！")
    print("=" * 80)
