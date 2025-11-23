#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证产品快照修复效果

检查：
1. 产品 BDABA1LQF6 的快照数据
2. "测试规格"和"增益调节范围"字段的 use_in_code 值
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
from config import Config
import json

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


def verify_snapshot_fix():
    with app.app_context():
        print("=" * 60)
        print("验证产品快照修复效果")
        print("=" * 60)

        # 1. 查询产品快照
        product = Product.query.filter_by(product_mn='BDABA1LQF6').first()
        if not product:
            print("❌ 未找到产品 BDABA1LQF6")
            return

        print(f"\n📦 产品: {product.product_mn}")
        print(f"   ID: {product.id}")
        print(f"   子类ID: {product.subcategory_id}")

        snapshot = product.code_definition_snapshot
        if not snapshot:
            print("❌ 快照数据为空")
            return

        print(f"\n📋 快照数据中的规格（共 {len(snapshot['code_parts'])} 个）:")
        for i, part in enumerate(snapshot['code_parts'], 1):
            use_in_code = part.get('use_in_code', 'undefined')
            print(f"   {i}. {part['field_name']:20} | use_in_code={use_in_code}")

        # 2. 查询字段定义
        print(f"\n🔍 字段定义表中的 use_in_code 值:")

        test_fields = ['测试规格', '增益调节范围', '防护等级', '频率范围']
        for field_name in test_fields:
            field_def = ProductCodeField.query.filter_by(
                subcategory_id=product.subcategory_id,
                name=field_name,
                field_type='spec'
            ).first()

            if field_def:
                print(f"   {field_name:20} | use_in_code={field_def.use_in_code}")
            else:
                print(f"   {field_name:20} | ❌ 未找到定义")

        print("\n" + "=" * 60)


if __name__ == '__main__':
    verify_snapshot_fix()
