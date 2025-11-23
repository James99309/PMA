#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复云端SP8D数据库产品快照数据：添加 use_in_code 字段并过滤非编码规格

功能：
1. 连接到云端Supabase数据库
2. 遍历所有产品的 code_definition_snapshot
3. 查询每个规格字段的 use_in_code 值
4. 移除 use_in_code=False 的非编码规格
5. 为所有规格添加 use_in_code 字段

使用方法：
    python3 scripts/temp/fix_cloud_product_snapshots.py

创建日期：2025-11-23
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

from app import db
from app.models.product import Product
from app.models.product_code import ProductCodeField
from flask import Flask
from sqlalchemy.orm.attributes import flag_modified
import json

# 创建Flask应用并使用云端数据库配置
app = Flask(__name__)

# 云端SP8D数据库连接信息（Supabase）
cloud_db_url = "postgresql://postgres.iqcyimnjtnmomvfuwjzw:towsys-coGdoq-6gofdi@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres?sslmode=require"

app.config['SQLALCHEMY_DATABASE_URI'] = cloud_db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


def fix_cloud_product_snapshots():
    """修复云端数据库所有产品的快照数据"""
    with app.app_context():
        print("=" * 80)
        print("开始修复云端SP8D数据库产品快照数据")
        print("=" * 80)

        # 显示数据库信息
        from urllib.parse import urlparse
        parsed = urlparse(cloud_db_url)
        print(f"\n🗄️  数据库连接信息:")
        print(f"   主机: {parsed.hostname}")
        print(f"   端口: {parsed.port}")
        print(f"   数据库: {parsed.path.lstrip('/')}")
        print(f"   用户: {parsed.username}")

        # 查询所有有快照数据的产品
        products = Product.query.filter(
            Product.code_definition_snapshot != None
        ).all()

        print(f'\n找到 {len(products)} 个产品需要检查...\n')

        fixed_count = 0
        skipped_count = 0
        error_count = 0

        for product in products:
            try:
                snapshot = product.code_definition_snapshot

                # 检查快照格式
                if not snapshot:
                    skipped_count += 1
                    continue

                if isinstance(snapshot, str):
                    snapshot = json.loads(snapshot)

                if 'code_parts' not in snapshot:
                    print(f"⚠️  产品 {product.product_mn}: 快照格式不匹配（缺少code_parts）")
                    skipped_count += 1
                    continue

                # 处理每个规格字段
                new_code_parts = []
                removed_specs = []

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

                    # 检查 use_in_code 值
                    if field_def:
                        use_in_code = field_def.use_in_code
                    else:
                        # 字段定义不存在，默认为编码规格
                        use_in_code = True

                    # 跳过非编码规格
                    if not use_in_code:
                        removed_specs.append(field_name)
                        continue

                    # 添加 use_in_code 字段
                    part['use_in_code'] = use_in_code
                    new_code_parts.append(part)

                # 如果有变化，更新快照
                if len(new_code_parts) != len(snapshot['code_parts']) or removed_specs:
                    snapshot['code_parts'] = new_code_parts
                    product.code_definition_snapshot = snapshot
                    # 标记字段已修改（SQLAlchemy JSON字段修改检测）
                    flag_modified(product, 'code_definition_snapshot')
                    db.session.add(product)
                    fixed_count += 1

                    print(f"✅ 修复产品 {product.product_mn}:")
                    print(f"   规格数量: {len(snapshot['code_parts'])} → {len(new_code_parts)}")
                    if removed_specs:
                        print(f"   移除非编码规格: {', '.join(removed_specs)}")

            except Exception as e:
                print(f"❌ 修复产品 {product.product_mn} 失败: {e}")
                error_count += 1
                continue

        # 提交更改
        if fixed_count > 0:
            print(f'\n准备提交更改：将修复 {fixed_count} 个产品')
            print("⚠️  警告：即将修改云端生产数据库！")

            # 自动提交（CLI脚本模式）
            db.session.commit()
            print(f'\n✅ 成功修复 {fixed_count} 个产品的快照数据')
        else:
            print('\n✅ 所有产品快照数据已经正确，无需修复')

        print("\n" + "=" * 80)
        print("修复完成统计:")
        print(f"  - 修复: {fixed_count} 个产品")
        print(f"  - 跳过: {skipped_count} 个产品")
        print(f"  - 错误: {error_count} 个产品")
        print("=" * 80)


if __name__ == '__main__':
    fix_cloud_product_snapshots()
