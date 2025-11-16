#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复研发产品的region_id字段
根据MN编码中的区域编码（第3位）来填充region_id
"""
import sys
import os

# 添加项目根目录到sys.path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

# 设置环境变量使用本地数据库
os.environ['FLASK_ENV'] = 'local'

from app import db
from app.models.dev_product import DevProduct
from app.models.product_code import ProductCodeField
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 直接连接数据库
DATABASE_URL = "postgresql://nijie@localhost:5432/pma_local"
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

print("=" * 80)
print("修复研发产品的region_id字段")
print("=" * 80)

# 获取所有区域字段（origin_location类型）
region_fields = session.query(ProductCodeField).filter_by(
    field_type='origin_location'
).all()

print("\n可用的区域字段：")
region_code_map = {}
for field in region_fields:
    code = field.code
    if code and code != "?":
        region_code_map[code] = field.id
        print(f"  - ID: {field.id}, 名称: {field.name}, 编码: {code}")

# 查找所有需要修复的研发产品（有MN编码但region_id为空）
dev_products = session.query(DevProduct).filter(
    DevProduct.mn_code.isnot(None),
    DevProduct.mn_code != '',
    DevProduct.region_id.is_(None)
).all()

print(f"\n找到 {len(dev_products)} 个需要修复的研发产品")
print("-" * 80)

fixed_count = 0
error_count = 0

for product in dev_products:
    mn_code = product.mn_code

    # MN编码第3位是区域编码（索引2）
    if len(mn_code) >= 3:
        region_code = mn_code[2]

        if region_code in region_code_map:
            region_id = region_code_map[region_code]

            print(f"\n产品ID: {product.id}")
            print(f"  名称: {product.name}")
            print(f"  型号: {product.model}")
            print(f"  MN编码: {mn_code}")
            print(f"  区域编码: {region_code}")
            print(f"  设置region_id: {region_id}")

            product.region_id = region_id
            fixed_count += 1
        else:
            print(f"\n⚠️  产品ID: {product.id} - 未找到区域编码'{region_code}'")
            print(f"  名称: {product.name}")
            print(f"  MN编码: {mn_code}")
            error_count += 1
    else:
        print(f"\n⚠️  产品ID: {product.id} - MN编码太短: {mn_code}")
        error_count += 1

print("\n" + "=" * 80)
print(f"修复完成！")
print(f"  成功修复: {fixed_count} 个产品")
print(f"  无法修复: {error_count} 个产品")
print("=" * 80)

if fixed_count > 0:
    # 自动提交更改
    session.commit()
    print("\n✅ 更改已自动提交到数据库")
else:
    print("\n没有需要修复的产品")

session.close()
