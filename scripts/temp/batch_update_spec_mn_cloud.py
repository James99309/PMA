#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""批量更新云端产品库中现有产品的 spec_mn 字段

对于有规格定义的产品，根据规格数据计算 spec_mn。
使用云端数据库连接。
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

project_root = get_project_root()
sys.path.insert(0, project_root)

# 设置云端数据库环境变量
os.environ['DATABASE_URL'] = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

from app import create_app, db
from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.models.product_code import ProductCodeField, ProductCodeFieldOption


def generate_spec_mn_direct(product):
    """
    直接根据产品规格生成规格MN编码（不依赖辅助函数，避免日志问题）

    Args:
        product: Product对象

    Returns:
        str | None: 生成的规格MN编码
    """
    try:
        # 验证必要的分类信息
        if not product.category_obj or not product.subcategory_obj:
            return None

        # 获取区域编码
        region_code = ""
        if product.region_obj:
            region_code = product.region_obj.code or ""
            # 处理"?"情况
            if region_code == "?":
                option = ProductCodeFieldOption.query.filter_by(
                    field_id=product.region_obj.id
                ).first()
                region_code = option.code if option else "0"

        # 获取分类和子分类编码
        category_code = product.category_obj.code_letter or ""
        subcategory_code = product.subcategory_obj.code_letter or ""

        # 获取产品规格
        specs = ProductSpec.query.filter_by(
            product_id=product.id
        ).order_by(ProductSpec.display_order, ProductSpec.id).all()

        # 收集规格编码数据
        specs_data = []
        for spec in specs:
            # 查询字段定义，获取position
            field_def = ProductCodeField.query.filter_by(
                subcategory_id=product.subcategory_id,
                name=spec.field_name,
                field_type='spec'
            ).first()

            # 只处理有编码的规格
            if spec.field_code and spec.field_code.strip():
                position = field_def.position if field_def else 999
                specs_data.append({
                    'position': position,
                    'code': spec.field_code.strip()
                })

        # 按position排序
        specs_data.sort(key=lambda x: x.get('position', 999))

        # 提取前10个规格编码
        spec_codes = [s.get('code', '0') for s in specs_data[:10]]

        # 去掉末尾的'0'
        while spec_codes and spec_codes[-1] == '0':
            spec_codes.pop()

        # 生成规格MN
        spec_mn = f"{region_code}{category_code}{subcategory_code}{''.join(spec_codes)}"

        return spec_mn if spec_mn else None

    except Exception as e:
        print(f"生成规格MN失败: 产品ID={product.id}, 错误={str(e)}")
        return None


def batch_update_spec_mn(dry_run=True):
    """批量更新产品的 spec_mn 字段

    Args:
        dry_run: True=仅预览不实际更新，False=执行更新
    """
    app = create_app()

    with app.app_context():
        print(f"连接到云端数据库...")

        # 查询所有有规格数据的产品
        products_with_specs_ids = db.session.query(ProductSpec.product_id).distinct().subquery()

        products = Product.query.filter(
            Product.id.in_(db.session.query(products_with_specs_ids.c.product_id))
        ).all()

        print(f"\n找到 {len(products)} 个有规格数据的产品")
        print("=" * 80)

        updated_count = 0
        skipped_count = 0
        same_count = 0

        for product in products:
            # 生成规格MN
            spec_mn = generate_spec_mn_direct(product)

            if not spec_mn:
                print(f"跳过: ID={product.id}, MN={product.product_mn}, 型号={product.model} (无法生成规格MN)")
                skipped_count += 1
                continue

            # 检查是否需要更新
            if product.spec_mn == spec_mn:
                same_count += 1
                continue

            # 显示变更
            old_spec_mn = product.spec_mn or "(空)"
            if product.product_mn == spec_mn:
                print(f"更新: ID={product.id}, MN={product.product_mn}, 型号={product.model}")
                print(f"       spec_mn: {old_spec_mn} -> {spec_mn} (与MN一致)")
            else:
                print(f"更新: ID={product.id}, MN={product.product_mn}, 型号={product.model}")
                print(f"       spec_mn: {old_spec_mn} -> {spec_mn}")
                if product.product_mn:
                    print(f"       显示为: {product.product_mn} [{spec_mn}]")

            if not dry_run:
                product.spec_mn = spec_mn

            updated_count += 1

        if not dry_run:
            db.session.commit()
            print(f"\n已提交数据库更新")

        print("=" * 80)
        print(f"总结:")
        print(f"  - 有规格的产品: {len(products)}")
        print(f"  - 需要更新: {updated_count}")
        print(f"  - 已是最新: {same_count}")
        print(f"  - 跳过(无法生成): {skipped_count}")

        if dry_run:
            print(f"\n这是预览模式，未实际修改数据库。")
            print(f"若要执行更新，请运行: python3 {__file__} --execute")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='批量更新云端产品 spec_mn 字段')
    parser.add_argument('--execute', action='store_true', help='执行实际更新（默认仅预览）')
    args = parser.parse_args()

    batch_update_spec_mn(dry_run=not args.execute)
