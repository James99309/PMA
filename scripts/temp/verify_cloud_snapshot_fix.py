#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证云端SP8D数据库产品快照修复效果

检查：
1. 随机抽样产品的快照数据
2. 确认非编码规格已移除
3. 确认 use_in_code 字段已添加
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
import json

# 创建Flask应用并使用云端数据库配置
app = Flask(__name__)

# 云端SP8D数据库连接信息（Supabase）
cloud_db_url = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

app.config['SQLALCHEMY_DATABASE_URI'] = cloud_db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


def verify_cloud_snapshot_fix():
    with app.app_context():
        print("=" * 80)
        print("验证云端SP8D数据库产品快照修复效果")
        print("=" * 80)

        # 显示数据库信息
        from urllib.parse import urlparse
        parsed = urlparse(cloud_db_url)
        print(f"\n🗄️  数据库连接信息:")
        print(f"   主机: {parsed.hostname}")
        print(f"   端口: {parsed.port}")
        print(f"   数据库: {parsed.path.lstrip('/')}")
        print(f"   用户: {parsed.username}")

        # 1. 查询有快照的产品
        products = Product.query.filter(
            Product.code_definition_snapshot != None
        ).limit(10).all()

        if not products:
            print("\n❌ 未找到有快照的产品")
            return

        print(f"\n📦 抽样检查 {len(products)} 个产品:")

        total_specs = 0
        total_with_use_in_code = 0
        products_checked = 0

        for product in products:
            snapshot = product.code_definition_snapshot
            if not snapshot or 'code_parts' not in snapshot:
                continue

            products_checked += 1
            code_parts = snapshot['code_parts']
            total_specs += len(code_parts)

            # 统计有 use_in_code 字段的规格
            with_use_in_code = sum(1 for part in code_parts if 'use_in_code' in part)
            total_with_use_in_code += with_use_in_code

            print(f"\n   产品 {product.product_mn}:")
            print(f"      规格数量: {len(code_parts)}")
            print(f"      包含 use_in_code: {with_use_in_code}/{len(code_parts)}")

            # 检查是否还有非编码规格
            for part in code_parts:
                field_name = part.get('field_name')
                if not field_name:
                    continue

                # 查询字段定义
                field_def = ProductCodeField.query.filter_by(
                    subcategory_id=product.subcategory_id,
                    name=field_name,
                    field_type='spec'
                ).first()

                if field_def and not field_def.use_in_code:
                    print(f"      ⚠️  仍包含非编码规格: {field_name}")

        print(f"\n" + "=" * 80)
        print("验证结果总结:")
        print(f"  - 检查产品: {products_checked} 个")
        print(f"  - 总规格数: {total_specs} 个")
        print(f"  - 包含 use_in_code 字段: {total_with_use_in_code}/{total_specs}")

        if total_with_use_in_code == total_specs:
            print(f"\n  ✅ 所有规格都已添加 use_in_code 字段")
        else:
            print(f"\n  ⚠️  还有 {total_specs - total_with_use_in_code} 个规格缺少 use_in_code 字段")

        print("=" * 80)


if __name__ == '__main__':
    verify_cloud_snapshot_fix()
