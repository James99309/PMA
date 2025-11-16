#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查YEABV编码的产品详情"""
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

# 延迟导入，避免加载不必要的模块
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

# 创建最小化Flask应用
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://nijie@localhost:5432/pma_local')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# 定义需要的模型（最小化版本）
class DevProduct(db.Model):
    __tablename__ = 'dev_products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200))
    mn_code = db.Column(db.String(50))
    category_id = db.Column(db.Integer, db.ForeignKey('product_categories.id'))
    subcategory_id = db.Column(db.Integer, db.ForeignKey('product_subcategories.id'))
    region_id = db.Column(db.Integer, db.ForeignKey('product_code_fields.id'))

class ProductCategory(db.Model):
    __tablename__ = 'product_categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    code_letter = db.Column(db.String(1))

class ProductSubcategory(db.Model):
    __tablename__ = 'product_subcategories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    code_letter = db.Column(db.String(1))

class ProductCodeField(db.Model):
    __tablename__ = 'product_code_fields'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    code = db.Column(db.String(10))
    field_type = db.Column(db.String(50))

class DevProductSpec(db.Model):
    __tablename__ = 'dev_product_specs'
    id = db.Column(db.Integer, primary_key=True)
    dev_product_id = db.Column(db.Integer, db.ForeignKey('dev_products.id'))
    field_name = db.Column(db.String(100))
    field_value = db.Column(db.Text)
    field_code = db.Column(db.String(10))
    display_order = db.Column(db.Integer)

with app.app_context():
    # 查找MN编码为YEABV的产品
    product = DevProduct.query.filter_by(mn_code='YEABV').first()

    if product:
        print('=== 产品基本信息 ===')
        print(f'产品ID: {product.id}')
        print(f'产品名称: {product.name}')
        print(f'MN编码: {product.mn_code}')

        # 查询分类
        category = ProductCategory.query.get(product.category_id) if product.category_id else None
        print(f'分类: {category.name if category else "未设置"} (编码: {category.code_letter if category else ""})')

        # 查询子分类
        subcategory = ProductSubcategory.query.get(product.subcategory_id) if product.subcategory_id else None
        print(f'子分类: {subcategory.name if subcategory else "未设置"} (编码: {subcategory.code_letter if subcategory else ""})')

        # 查询区域
        region = ProductCodeField.query.get(product.region_id) if product.region_id else None
        print(f'区域: {region.name if region else "未设置"} (编码: {region.code if region else ""})')

        print('\n=== 规格编码分析 ===')
        print(f'固定前缀: {category.code_letter if category else "?"}{subcategory.code_letter if subcategory else "?"}{region.code if region else "?"}')
        print(f'规格编码: {product.mn_code[3:] if len(product.mn_code) > 3 else "无"}')

        print('\n=== 规格详情 ===')
        specs = DevProductSpec.query.filter_by(
            dev_product_id=product.id
        ).order_by(DevProductSpec.display_order).all()

        if specs:
            for spec in specs:
                print(f'顺序 {spec.display_order}: {spec.field_name} = {spec.field_value} (编码: {spec.field_code})')
        else:
            print('该产品没有规格数据')

        # 重新生成编码验证
        print('\n=== 编码验证 ===')
        expected_code = ''
        if category:
            expected_code += category.code_letter
        if subcategory:
            expected_code += subcategory.code_letter
        if region:
            expected_code += region.code

        spec_codes = [spec.field_code for spec in specs if spec.field_code]
        expected_code += ''.join(spec_codes)

        print(f'预期编码: {expected_code}')
        print(f'实际编码: {product.mn_code}')
        print(f'是否匹配: {"✅ 是" if expected_code == product.mn_code else "❌ 否"}')

    else:
        print('未找到MN编码为YEABV的产品')

        # 列出所有类似的编码
        print('\n=== YE开头的产品 ===')
        similar = DevProduct.query.filter(
            DevProduct.mn_code.like('YE%')
        ).limit(10).all()

        if similar:
            for p in similar:
                print(f'{p.mn_code}: {p.name}')
        else:
            print('未找到YE开头的产品')
