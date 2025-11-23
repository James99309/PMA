#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查云端SP8D数据库中的产品快照是否包含非编码规格

检查内容：
1. 统计有快照的产品数量
2. 分析快照中是否包含 use_in_code=False 的规格
3. 对比字段定义表中的 use_in_code 值
"""
import sys
import os

def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

from app import db
from app.models.product import Product
from app.models.product_code import ProductCodeField
from flask import Flask
import os
import json

# 创建Flask应用并使用云端数据库配置
app = Flask(__name__)

# 云端SP8D数据库连接信息（Supabase）
cloud_db_url = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

app.config['SQLALCHEMY_DATABASE_URI'] = cloud_db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


def check_cloud_snapshots():
    with app.app_context():
        print("=" * 80)
        print("检查云端SP8D数据库中的产品快照")
        print("=" * 80)

        # 显示数据库信息
        from urllib.parse import urlparse
        parsed = urlparse(cloud_db_url)
        print(f"\n🗄️  数据库连接信息:")
        print(f"   主机: {parsed.hostname}")
        print(f"   端口: {parsed.port}")
        print(f"   数据库: {parsed.path.lstrip('/')}")
        print(f"   用户: {parsed.username}")

        # 1. 统计产品总数
        total_products = Product.query.count()
        products_with_snapshot = Product.query.filter(
            Product.code_definition_snapshot != None
        ).count()

        print(f"\n📊 产品统计:")
        print(f"   总产品数: {total_products}")
        print(f"   有快照的产品: {products_with_snapshot}")

        # 2. 检查快照数据
        print(f"\n🔍 检查快照中的非编码规格...")

        products = Product.query.filter(
            Product.code_definition_snapshot != None
        ).limit(100).all()  # 先检查前100个产品

        issues = []
        for product in products:
            try:
                snapshot = product.code_definition_snapshot
                if not snapshot or 'code_parts' not in snapshot:
                    continue

                # 检查每个规格字段
                for part in snapshot['code_parts']:
                    field_name = part.get('field_name')
                    if not field_name:
                        continue

                    # 查询字段定义
                    field_def = ProductCodeField.query.filter_by(
                        subcategory_id=product.subcategory_id,
                        name=field_name,
                        field_type='spec'
                    ).first()

                    # 检查是否为非编码规格
                    if field_def and not field_def.use_in_code:
                        issues.append({
                            'product_mn': product.product_mn,
                            'field_name': field_name,
                            'snapshot_use_in_code': part.get('use_in_code', 'undefined'),
                            'db_use_in_code': field_def.use_in_code
                        })

            except Exception as e:
                print(f"   ⚠️  检查产品 {product.product_mn} 时出错: {e}")
                continue

        # 3. 输出检查结果
        if issues:
            print(f"\n⚠️  发现 {len(issues)} 个快照包含非编码规格:")

            # 按产品分组显示
            by_product = {}
            for issue in issues:
                product_mn = issue['product_mn']
                if product_mn not in by_product:
                    by_product[product_mn] = []
                by_product[product_mn].append(issue['field_name'])

            for product_mn, fields in by_product.items():
                print(f"\n   产品 {product_mn}:")
                for field in fields:
                    print(f"      - {field}")

            print(f"\n❌ 云端数据库需要运行迁移脚本")
            print(f"   影响的产品: {len(by_product)} 个")
            print(f"   需要移除的非编码规格: {len(issues)} 个字段实例")

        else:
            print(f"\n✅ 前{len(products)}个产品的快照数据正确，不包含非编码规格")

        # 4. 检查是否有 use_in_code 字段
        print(f"\n🔍 检查快照是否包含 use_in_code 字段...")

        sample_count = 0
        with_use_in_code = 0
        without_use_in_code = 0

        for product in products[:10]:  # 抽样检查前10个
            snapshot = product.code_definition_snapshot
            if snapshot and 'code_parts' in snapshot and len(snapshot['code_parts']) > 0:
                sample_count += 1
                first_part = snapshot['code_parts'][0]
                if 'use_in_code' in first_part:
                    with_use_in_code += 1
                else:
                    without_use_in_code += 1

        print(f"   抽样检查: {sample_count} 个产品")
        print(f"   包含 use_in_code 字段: {with_use_in_code} 个")
        print(f"   缺少 use_in_code 字段: {without_use_in_code} 个")

        if without_use_in_code > 0:
            print(f"\n⚠️  部分快照缺少 use_in_code 字段，需要运行迁移脚本")

        print("\n" + "=" * 80)
        print("检查完成")
        print("=" * 80)


if __name__ == '__main__':
    check_cloud_snapshots()
