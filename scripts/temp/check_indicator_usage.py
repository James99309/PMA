#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查规格指标的使用情况
判断是否可以安全删除编码为A的指标
"""
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
from app.models.product import Product
from app.models.dev_product import DevProduct, DevProductSpec
from app.models.product_spec import ProductSpec

app = create_app()

print("=" * 80)
print("检查规格指标的使用情况")
print("=" * 80)

with app.app_context():
    # 查找所有编码为"A"的规格指标
    a_coded_options = ProductCodeFieldOption.query.filter_by(code='A').all()

    print(f"\n找到 {len(a_coded_options)} 个编码为'A'的规格指标\n")

    if not a_coded_options:
        print("✅ 没有编码为'A'的指标，无需处理")
        exit(0)

    total_used = 0
    total_unused = 0

    for option in a_coded_options:
        field = ProductCodeField.query.get(option.field_id)
        subcategory = ProductSubcategory.query.get(field.subcategory_id) if field else None
        product_name = subcategory.name if subcategory else '未分配'

        # 检查是否被标准产品使用
        used_in_products = ProductSpec.query.filter_by(
            field_name=field.name,
            field_value=option.value
        ).count() if field else 0

        # 检查是否被研发产品使用
        used_in_dev_products = DevProductSpec.query.filter_by(
            field_name=field.name,
            field_value=option.value
        ).count() if field else 0

        total_usage = used_in_products + used_in_dev_products

        if total_usage > 0:
            total_used += 1
            status = f"❌ 已被使用 ({total_usage}次)"
        else:
            total_unused += 1
            status = f"✅ 未被使用"

        print(f"指标ID {option.id}: {product_name} - {field.name if field else '?'}")
        print(f"  值: {option.value}")
        print(f"  编码: {option.code}")
        print(f"  状态: {status}")
        print()

    print("=" * 80)
    print("统计汇总")
    print("=" * 80)
    print(f"编码为'A'的指标总数: {len(a_coded_options)}")
    print(f"  已被使用: {total_used} 个 ❌")
    print(f"  未被使用: {total_unused} 个 ✅")

    print("\n" + "=" * 80)
    print("建议")
    print("=" * 80)

    if total_used > 0:
        print("⚠️  发现已被使用的指标！")
        print("\n推荐方案：")
        print("  1. 【保留现有指标】 - 不删除已有指标，避免影响现有产品")
        print("  2. 【新增指标自动优化】 - 修复后的代码会为新指标分配随机编码")
        print("  3. 【逐步优化】 - 未来新增产品会有更好的编码区分度")
        print("\n如果坚持要重新编码：")
        print("  1. 导出所有相关产品数据")
        print("  2. 删除指标并重新创建")
        print("  3. 手动更新所有产品的MN编码和规格记录")
        print("  4. 验证产品编码快照的一致性")
        print("  ⚠️  风险很高，不建议！")
    else:
        print("✅ 所有编码为'A'的指标都未被使用")
        print("\n可以安全执行以下操作：")
        print("  1. 删除这些未使用的指标")
        print("  2. 重新添加时会自动分配随机编码")
        print("  3. 获得更好的编码区分度")
        print("\n执行命令（需确认）：")
        print("  DELETE FROM product_code_field_options WHERE code='A' AND id IN (...);")

    print("\n" + "=" * 80)
    print("检查完成")
    print("=" * 80)
