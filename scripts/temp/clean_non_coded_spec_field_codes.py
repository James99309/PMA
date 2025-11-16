#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理研发产品中非编码规格的field_code值

问题：非编码规格(use_in_code=False)不应该有field_code值，但由于之前的bug，
这些非编码规格也被分配了编码值（如"A"）。

解决：找到所有非编码规格，将其field_code设为NULL。
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
from app.models.dev_product import DevProduct, DevProductSpec
from app.models.product_code import ProductCodeField

def clean_non_coded_specs():
    """清理非编码规格的field_code值"""
    app = create_app()

    with app.app_context():
        print("=" * 80)
        print("清理非编码规格的field_code值")
        print("=" * 80)

        # 查询所有有field_code的DevProductSpec
        specs_with_code = DevProductSpec.query.filter(
            DevProductSpec.field_code.isnot(None),
            DevProductSpec.field_code != ''
        ).all()

        print(f"\n找到 {len(specs_with_code)} 条有编码值的规格记录")

        cleaned_count = 0
        kept_count = 0

        for spec in specs_with_code:
            # 获取对应的研发产品
            dev_product = DevProduct.query.get(spec.dev_product_id)
            if not dev_product:
                print(f"⚠️  规格 ID {spec.id} 的产品不存在，跳过")
                continue

            # 查找对应的ProductCodeField
            code_field = ProductCodeField.query.filter_by(
                subcategory_id=dev_product.subcategory_id,
                name=spec.field_name
            ).first()

            if not code_field:
                print(f"⚠️  规格 '{spec.field_name}' 没有找到对应的ProductCodeField定义，保留编码")
                kept_count += 1
                continue

            # 检查是否参与编码
            if not code_field.use_in_code:
                # 非编码规格，清空field_code
                print(f"🔧 清理非编码规格: {spec.field_name} = {spec.field_value}, "
                      f"旧编码: {spec.field_code} → 新编码: NULL")
                spec.field_code = None
                cleaned_count += 1
            else:
                # 编码规格，保留field_code
                kept_count += 1

        print(f"\n" + "=" * 80)
        print(f"处理完成:")
        print(f"  - 清理非编码规格: {cleaned_count} 条")
        print(f"  - 保留编码规格: {kept_count} 条")
        print("=" * 80)

        # 确认是否提交
        if cleaned_count > 0:
            confirm = input(f"\n是否提交更改到数据库？(yes/no): ")
            if confirm.lower() == 'yes':
                db.session.commit()
                print("✅ 更改已提交到数据库")
            else:
                db.session.rollback()
                print("❌ 更改已回滚，数据库未修改")
        else:
            print("\n没有需要清理的数据")

if __name__ == '__main__':
    clean_non_coded_specs()
