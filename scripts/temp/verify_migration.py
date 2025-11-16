#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""验证数据库迁移结果"""
import sys
import os

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

# 避免导入有问题的模块
import importlib.util

def block_pdf_imports():
    """临时屏蔽PDF相关导入"""
    import sys
    from unittest.mock import MagicMock

    mock_weasyprint = MagicMock()
    mock_pdf_generator = MagicMock()

    sys.modules['weasyprint'] = mock_weasyprint
    sys.modules['app.services.pdf_generator'] = mock_pdf_generator

block_pdf_imports()

from app import create_app, db
from sqlalchemy import inspect

def main():
    """验证迁移结果"""
    print("=" * 70)
    print("🔍 验证数据库迁移结果")
    print("=" * 70)

    app = create_app()

    with app.app_context():
        inspector = inspect(db.engine)

        print("\n" + "=" * 70)
        print("1️⃣  验证新建表")
        print("=" * 70)

        tables = inspector.get_table_names()
        new_tables = ['product_specs', 'product_relations']

        for table in new_tables:
            if table in tables:
                columns = {col['name']: col for col in inspector.get_columns(table)}
                print(f"\n✅ 表 {table} 已创建 ({len(columns)} 个字段)")
                for col_name in sorted(columns.keys()):
                    col = columns[col_name]
                    print(f"   - {col_name}: {col['type']}")
            else:
                print(f"\n❌ 表 {table} 未创建")

        print("\n" + "=" * 70)
        print("2️⃣  验证表扩展")
        print("=" * 70)

        # 验证 products 表扩展
        if 'products' in tables:
            columns = {col['name']: col for col in inspector.get_columns('products')}
            new_columns = ['category_id', 'subcategory_id', 'region_id', 'source_type',
                          'source_dev_product_id', 'productized_at']

            print(f"\n✅ products 表扩展:")
            for col in new_columns:
                if col in columns:
                    print(f"   ✓ {col}: {columns[col]['type']}")
                else:
                    print(f"   ✗ {col}: 缺失")

        # 验证 quotation_details 表扩展
        if 'quotation_details' in tables:
            columns = {col['name']: col for col in inspector.get_columns('quotation_details')}
            new_columns = ['pending_specs', 'parent_item_id', 'is_accessory', 'is_editable']

            print(f"\n✅ quotation_details 表扩展:")
            for col in new_columns:
                if col in columns:
                    print(f"   ✓ {col}: {columns[col]['type']}")
                else:
                    print(f"   ✗ {col}: 缺失")

        print("\n" + "=" * 70)
        print("3️⃣  验证索引")
        print("=" * 70)

        # 验证 product_specs 索引
        if 'product_specs' in tables:
            indexes = inspector.get_indexes('product_specs')
            expected_indexes = ['idx_product_specs_product', 'idx_product_specs_field_name',
                              'idx_product_specs_field_value', 'idx_product_specs_name_value']
            actual_indexes = [idx['name'] for idx in indexes]

            print(f"\n✅ product_specs 表索引:")
            for idx_name in expected_indexes:
                if idx_name in actual_indexes:
                    print(f"   ✓ {idx_name}")
                else:
                    print(f"   ✗ {idx_name}")

        # 验证 product_relations 索引
        if 'product_relations' in tables:
            indexes = inspector.get_indexes('product_relations')
            expected_indexes = ['idx_product_relations_main', 'idx_product_relations_related']
            actual_indexes = [idx['name'] for idx in indexes]

            print(f"\n✅ product_relations 表索引:")
            for idx_name in expected_indexes:
                if idx_name in actual_indexes:
                    print(f"   ✓ {idx_name}")
                else:
                    print(f"   ✗ {idx_name}")

        # 验证 products 索引
        if 'products' in tables:
            indexes = inspector.get_indexes('products')
            expected_indexes = ['idx_products_category', 'idx_products_subcategory', 'idx_products_region']
            actual_indexes = [idx['name'] for idx in indexes]

            print(f"\n✅ products 表新增索引:")
            for idx_name in expected_indexes:
                if idx_name in actual_indexes:
                    print(f"   ✓ {idx_name}")
                else:
                    print(f"   ✗ {idx_name} (可能未创建或名称不同)")

        print("\n" + "=" * 70)
        print("4️⃣  验证外键约束")
        print("=" * 70)

        # 验证 product_specs 外键
        if 'product_specs' in tables:
            fks = inspector.get_foreign_keys('product_specs')
            print(f"\n✅ product_specs 表外键:")
            for fk in fks:
                print(f"   ✓ {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")

        # 验证 product_relations 外键
        if 'product_relations' in tables:
            fks = inspector.get_foreign_keys('product_relations')
            print(f"\n✅ product_relations 表外键:")
            for fk in fks:
                print(f"   ✓ {fk['constrained_columns']} -> {fk['referred_table']}.{fk['referred_columns']}")

        # 验证 products 外键
        if 'products' in tables:
            fks = inspector.get_foreign_keys('products')
            print(f"\n✅ products 表新增外键:")
            new_fk_names = ['fk_products_category', 'fk_products_subcategory',
                           'fk_products_region', 'fk_products_source_dev']
            fk_names = [fk.get('name') for fk in fks]
            for fk_name in new_fk_names:
                if fk_name in fk_names:
                    print(f"   ✓ {fk_name}")
                else:
                    print(f"   ✗ {fk_name} (可能未创建或名称不同)")

        print("\n" + "=" * 70)
        print("✅ 验证完成！")
        print("=" * 70)

if __name__ == '__main__':
    main()
