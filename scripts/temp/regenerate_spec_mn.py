#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新生成 SP8D 云端数据库所有产品的 spec_mn

修复问题：
1. 之前生成时 region_id 为空，缺少区域编码
2. 之前的批量脚本没有正确检查 use_in_code 字段
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
os.chdir(get_project_root())

# 设置云端数据库连接
os.environ['DATABASE_URL'] = 'postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require'

from app import create_app, db
from app.models.product import Product
from app.models.product_spec import ProductSpec
from app.utils.product_helpers import generate_spec_mn

def verify_database():
    """验证数据库身份"""
    from app.models.product_code import ProductCategory
    category = ProductCategory.query.filter_by(name='基站').first()
    if category:
        return 'SP8D'
    category = ProductCategory.query.filter_by(name='Basestation').first()
    if category:
        return 'OVS'
    return 'UNKNOWN'

def regenerate_all_spec_mn():
    """重新生成所有产品的 spec_mn"""
    app = create_app()

    with app.app_context():
        # 验证数据库
        db_identity = verify_database()
        print(f"数据库身份: {db_identity}")

        if db_identity != 'SP8D':
            print(f"错误: 期望 SP8D，但连接到 {db_identity}")
            return

        # 获取所有有规格数据的产品ID
        product_ids_with_specs = db.session.query(ProductSpec.product_id).distinct().all()
        product_ids = [pid[0] for pid in product_ids_with_specs]

        # 根据ID获取产品
        products_with_specs = Product.query.filter(Product.id.in_(product_ids)).all()

        print(f"\n找到 {len(products_with_specs)} 个有规格数据的产品")
        print("-" * 80)

        updated_count = 0
        unchanged_count = 0
        failed_count = 0

        results = []

        for product in products_with_specs:
            old_spec_mn = product.spec_mn

            # 使用正确的函数重新生成
            new_spec_mn = generate_spec_mn(product)

            if new_spec_mn != old_spec_mn:
                results.append({
                    'id': product.id,
                    'model': product.model,
                    'product_mn': product.product_mn,
                    'old': old_spec_mn,
                    'new': new_spec_mn,
                    'changed': True
                })

                # 更新数据库
                product.spec_mn = new_spec_mn
                updated_count += 1
            else:
                results.append({
                    'id': product.id,
                    'model': product.model,
                    'product_mn': product.product_mn,
                    'old': old_spec_mn,
                    'new': new_spec_mn,
                    'changed': False
                })
                unchanged_count += 1

        # 打印变更详情
        print("\n变更详情:")
        print("-" * 80)
        for r in results:
            if r['changed']:
                print(f"[更新] ID={r['id']:3d} | {r['model'][:20]:20s} | {r['product_mn']:15s}")
                print(f"        旧: {r['old']}")
                print(f"        新: {r['new']}")
                print()

        print("-" * 80)
        print(f"统计: 更新 {updated_count} 个, 未变 {unchanged_count} 个, 失败 {failed_count} 个")

        # 提交更改
        if updated_count > 0:
            if '--auto-confirm' in sys.argv:
                db.session.commit()
                print(f"\n✅ 已提交 {updated_count} 个产品的 spec_mn 更新")
            else:
                try:
                    confirm = input("\n确认提交更改? (yes/no): ")
                    if confirm.lower() == 'yes':
                        db.session.commit()
                        print(f"\n✅ 已提交 {updated_count} 个产品的 spec_mn 更新")
                    else:
                        db.session.rollback()
                        print("\n❌ 已取消，未提交更改")
                except EOFError:
                    print("\n提示: 使用 --auto-confirm 参数自动确认提交")
                    db.session.rollback()
        else:
            print("\n没有需要更新的产品")

if __name__ == '__main__':
    regenerate_all_spec_mn()
