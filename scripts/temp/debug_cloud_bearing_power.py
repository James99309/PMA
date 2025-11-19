#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断云端SP8D数据库中"承载功率"指标数据

检查：
1. "承载功率"规格字段是否存在
2. 预定义选项值
3. DevProductSpec表中的数据
4. ProductSpec表中的数据
5. 为何API返回空列表
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

# 创建应用（使用云端数据库配置）
app = create_app()

with app.app_context():
    print("=" * 80)
    print("诊断：云端SP8D数据库 - 承载功率指标数据")
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
        print("  (无预定义选项)")

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

    # 5. 模拟API逻辑
    print(f"\n【步骤5】模拟API排除逻辑")
    print("=" * 80)

    # 合并所有产品值
    all_product_values = dev_values | product_values
    print(f"合并后的所有产品值: {all_product_values}")
    print(f"数量: {len(all_product_values)}")

    # 排除预定义值
    product_only_values = all_product_values - predefined_values
    print(f"\n排除预定义值后: {product_only_values}")
    print(f"数量: {len(product_only_values)}")

    # 6. 诊断结论
    print(f"\n【诊断结论】")
    print("=" * 80)

    if len(product_only_values) == 0:
        print("❌ 问题确认：API返回空列表")
        print("\n原因分析:")

        if len(all_product_values) == 0:
            print("  🔴 根本原因：数据库中没有任何产品使用'承载功率'规格")
            print("     → DevProductSpec表: 0条记录")
            print("     → ProductSpec表: 0条记录")
            print("\n  解决方案：")
            print("     1. 确认产品数据是否正确保存")
            print("     2. 检查保存产品时的规格数据写入逻辑")
            print("     3. 手动添加测试数据验证")
        elif len(all_product_values) > 0 and len(predefined_values) == 0:
            print("  🟡 原因：有产品数据，但没有预定义选项")
            print(f"     → 产品使用值: {all_product_values}")
            print("     → 预定义选项: 0个")
            print("\n  ⚠️ 这种情况不应该返回空列表！")
            print("     可能是代码逻辑问题")
        else:
            print("  🟠 原因：所有产品使用值都已在预定义选项池中")
            print(f"     → 产品使用值: {all_product_values}")
            print(f"     → 预定义选项: {predefined_values}")
            print(f"     → 差集: {product_only_values} (空)")
            print("\n  这是设计逻辑问题：")
            print("     当前逻辑：只显示'产品独有'的值（不在预定义中的）")
            print("     用户期望：显示'所有产品使用过'的值")
            print("\n  解决方案：")
            print("     方案A：修改API，添加参数显示所有产品值")
            print("     方案B：修改排除逻辑，允许显示预定义值")
            print("     方案C：前端显示时区分[预定义]和[产品值]")
    else:
        print("✅ API应该返回非空列表")
        print(f"\n预期返回值: {product_only_values}")
        print(f"数量: {len(product_only_values)}")
        print("\n如果前端仍然显示空列表，请检查：")
        print("  1. 前端JavaScript是否正确处理响应")
        print("  2. 浏览器Network标签中的实际API响应")
        print("  3. field_id参数是否正确传递")

    print("\n" + "=" * 80)
    print("诊断完成！")
    print("=" * 80)
