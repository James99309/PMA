#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复厂商产品标记 - 将3个数字智能信道机标记为厂商产品"""
import sys, os

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

# 直接使用数据库，避免导入PDF生成等依赖
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# 获取数据库URL
database_url = os.getenv('DATABASE_URL')
if not database_url:
    print('❌ 未找到DATABASE_URL环境变量')
    print('请使用以下命令设置：')
    print('export DATABASE_URL="postgresql://用户名:密码@localhost:5432/数据库名"')
    sys.exit(1)

# 创建数据库连接
engine = create_engine(database_url)
Session = sessionmaker(bind=engine)
session = Session()

# 导入Product模型（使用base导入避免循环依赖）
from app.models.product import Product

if True:  # 替代 with app.app_context()
    print('='*80)
    print('修复厂商产品标记')
    print('='*80)

    # 需要修复的产品MN编号
    product_mns = [
        'BDACB1L1F6',  # 数字智能信道机
        'BDACA1L2H6',  # 数字智能信道机
        'BDABA1LQF6'   # 数字智能信道机
    ]

    print(f'\n📋 需要修复的产品MN编号：')
    for mn in product_mns:
        print(f'   - {mn}')

    print(f'\n🔍 查询产品信息...')

    # 查询产品
    products = session.query(Product).filter(Product.product_mn.in_(product_mns)).all()

    if not products:
        print('❌ 未找到任何产品，请检查MN编号')
        sys.exit(1)

    print(f'\n✅ 找到 {len(products)} 个产品：\n')
    print(f'{"MN编号":<15} {"产品名称":<25} {"品牌":<15} {"当前标记":<12}')
    print('-' * 80)

    for product in products:
        vendor_status = '✅ 厂商' if product.is_vendor_product else '❌ 非厂商'
        print(f'{product.product_mn:<15} {product.name:<25} {product.brand or "无":<15} {vendor_status:<12}')

    # 询问确认
    print('\n' + '='*80)
    confirm = input('是否将上述产品标记为厂商产品？(yes/no): ').strip().lower()

    if confirm not in ['yes', 'y']:
        print('❌ 操作已取消')
        sys.exit(0)

    # 执行更新
    print('\n🔧 开始更新产品标记...')
    updated_count = 0

    for product in products:
        if not product.is_vendor_product:
            print(f'   ✓ 更新 {product.product_mn} - {product.name}')
            product.is_vendor_product = True
            updated_count += 1
        else:
            print(f'   ○ 跳过 {product.product_mn} - {product.name} (已是厂商产品)')

    # 提交更改
    if updated_count > 0:
        try:
            session.commit()
            print(f'\n✅ 成功更新 {updated_count} 个产品')
            print('\n📊 后续影响：')
            print('   - 使用这些产品的报价单将自动重新计算植入金额')
            print('   - 建议重新查看相关报价单的植入合计金额')
        except Exception as e:
            session.rollback()
            print(f'\n❌ 更新失败：{e}')
            sys.exit(1)
        finally:
            session.close()
    else:
        print('\n✓ 所有产品已正确标记，无需更新')
        session.close()

    print('\n' + '='*80)
    print('修复完成')
    print('='*80)
