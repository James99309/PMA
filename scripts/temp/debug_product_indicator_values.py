#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试产品指标值采集问题

检查：
1. API参数传递情况
2. 数据库中的实际数据
3. 查询逻辑是否正确
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
from app.models.product_code import ProductCodeField
from app.models.dev_product import DevProductSpec
from app.models.product_spec import ProductSpec

app = create_app()

with app.app_context():
    print("=" * 80)
    print("调试：产品指标值采集问题")
    print("=" * 80)

    # 1. 查找所有规格字段
    print("\n【步骤1】查找所有规格字段（前10个）：")
    print("-" * 80)
    fields = ProductCodeField.query.filter_by(field_type='spec').limit(10).all()

    for field in fields:
        print(f"\n字段ID: {field.id}")
        print(f"  名称: '{field.name}'")
        print(f"  产品名称: {field.subcategory.name if field.subcategory else 'N/A'}")
        print(f"  预定义选项数: {field.options.count()}")

        # 查询该规格在DevProductSpec中的使用情况
        dev_count = DevProductSpec.query.filter_by(field_name=field.name).count()
        print(f"  DevProductSpec使用次数: {dev_count}")

        # 查询该规格在ProductSpec中的使用情况
        prod_count = ProductSpec.query.filter_by(field_name=field.name).count()
        print(f"  ProductSpec使用次数: {prod_count}")

        # 如果有产品使用值，显示前5个不同的值
        if dev_count > 0 or prod_count > 0:
            print(f"  ✅ 该规格有产品使用值")

            # 从DevProductSpec提取
            dev_values = db.session.query(DevProductSpec.field_value)\
                .filter_by(field_name=field.name)\
                .distinct()\
                .limit(5)\
                .all()

            if dev_values:
                print(f"  DevProductSpec中的值（前5个）：")
                for (value,) in dev_values:
                    print(f"    - '{value}'")

            # 从ProductSpec提取
            prod_values = db.session.query(ProductSpec.field_value)\
                .filter_by(field_name=field.name)\
                .distinct()\
                .limit(5)\
                .all()

            if prod_values:
                print(f"  ProductSpec中的值（前5个）：")
                for (value,) in prod_values:
                    print(f"    - '{value}'")

            # 模拟API逻辑：排除预定义值
            existing_values = set()
            for opt in field.options.all():
                if opt.value and opt.value.strip():
                    existing_values.add(opt.value.strip())

            all_product_values = set()
            for (value,) in dev_values:
                if value and value.strip():
                    all_product_values.add(value.strip())
            for (value,) in prod_values:
                if value and value.strip():
                    all_product_values.add(value.strip())

            product_only_values = all_product_values - existing_values

            print(f"  预定义值: {existing_values}")
            print(f"  产品使用值: {all_product_values}")
            print(f"  排除后应显示: {product_only_values}")

    # 2. 模拟API调用
    print("\n" + "=" * 80)
    print("【步骤2】模拟API调用（选择第一个有产品使用值的规格）：")
    print("=" * 80)

    # 找一个有产品使用值的规格字段
    test_field = None
    for field in ProductCodeField.query.filter_by(field_type='spec').all():
        dev_count = DevProductSpec.query.filter_by(field_name=field.name).count()
        prod_count = ProductSpec.query.filter_by(field_name=field.name).count()

        if dev_count > 0 or prod_count > 0:
            test_field = field
            break

    if not test_field:
        print("❌ 未找到任何有产品使用值的规格字段")
    else:
        print(f"\n测试规格：'{test_field.name}' (ID: {test_field.id})")
        print(f"产品名称：{test_field.subcategory.name if test_field.subcategory else 'N/A'}")

        # 模拟API参数
        field_id = test_field.id
        spec_name = test_field.name
        subcategory_id = test_field.subcategory_id

        print(f"\nAPI参数：")
        print(f"  field_id: {field_id}")
        print(f"  spec_name: '{spec_name}'")
        print(f"  subcategory_id: {subcategory_id}")
        print(f"  include_product_values: true")

        # 执行查询逻辑（复制API代码）
        print(f"\n执行查询逻辑：")

        # 1. 获取预定义选项的值
        existing_option_values = set()
        for option in test_field.options.all():
            if option.value and option.value.strip():
                existing_option_values.add(option.value.strip())

        print(f"  预定义选项值: {existing_option_values}")

        # 2. 查询产品使用值
        dev_values = db.session.query(DevProductSpec.field_value)\
            .filter(DevProductSpec.field_name == spec_name)\
            .distinct()\
            .all()

        prod_values = db.session.query(ProductSpec.field_value)\
            .filter(ProductSpec.field_name == spec_name)\
            .distinct()\
            .all()

        print(f"  DevProductSpec查询结果: {len(dev_values)}个不同值")
        print(f"  ProductSpec查询结果: {len(prod_values)}个不同值")

        # 3. 合并并去重
        all_product_values = set()
        for (value,) in dev_values:
            if value and value.strip():
                all_product_values.add(value.strip())
        for (value,) in prod_values:
            if value and value.strip():
                all_product_values.add(value.strip())

        print(f"  合并后的产品值: {all_product_values}")

        # 4. 排除预定义值
        product_only_values = all_product_values - existing_option_values

        print(f"  排除预定义后: {product_only_values}")

        # 5. 组装返回数据
        options_data = []
        for value in sorted(product_only_values):
            options_data.append({
                'id': None,
                'value': value,
                'code': '',
                'description': '',
                'is_active': True,
                'source': 'product'
            })

        print(f"\n最终返回的options数量: {len(options_data)}")
        if options_data:
            print(f"返回的数据（前5个）：")
            for opt in options_data[:5]:
                print(f"  - {opt['value']}")
        else:
            print("⚠️ 返回的数据为空！")
            print("\n可能原因：")
            print("  1. 所有产品使用值都已在预定义选项池中")
            print("  2. 数据库中没有该规格的产品数据")
            print("  3. field_name不匹配")

    # 3. 检查API端点的实际行为
    print("\n" + "=" * 80)
    print("【步骤3】诊断建议：")
    print("=" * 80)

    # 统计
    total_fields = ProductCodeField.query.filter_by(field_type='spec').count()
    fields_with_dev_data = 0
    fields_with_prod_data = 0

    for field in ProductCodeField.query.filter_by(field_type='spec').all():
        if DevProductSpec.query.filter_by(field_name=field.name).count() > 0:
            fields_with_dev_data += 1
        if ProductSpec.query.filter_by(field_name=field.name).count() > 0:
            fields_with_prod_data += 1

    print(f"\n统计信息：")
    print(f"  规格字段总数: {total_fields}")
    print(f"  有DevProductSpec数据的字段: {fields_with_dev_data}")
    print(f"  有ProductSpec数据的字段: {fields_with_prod_data}")

    if fields_with_dev_data == 0 and fields_with_prod_data == 0:
        print("\n❌ 问题：数据库中没有任何产品规格数据")
        print("   解决方案：需要先创建产品并填写规格值")
    else:
        print("\n✅ 数据库中有产品规格数据")
        print("   如果前端仍然不显示，请检查：")
        print("   1. 浏览器控制台Network标签中的API请求")
        print("   2. 请求URL是否包含 include_product_values=true")
        print("   3. 响应数据是否包含产品值")

    print("\n" + "=" * 80)
    print("调试完成！")
    print("=" * 80)
