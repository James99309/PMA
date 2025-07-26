#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
为测试添加库存
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.customer import Company
from config import LocalConfig
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_test_inventory():
    """为测试添加库存"""
    app = create_app(LocalConfig)
    
    with app.app_context():
        # 查找HYTD4MA产品
        product = Product.query.filter_by(product_mn='HYTD4MA').first()
        
        if not product:
            print("❌ 未找到产品 HYTD4MA")
            return
        
        print(f"🔍 产品: {product.product_name} (MN: {product.product_mn})")
        
        # 查找一个公司（使用上海瑞康通信科技有限公司）
        company = Company.query.filter_by(company_name='上海瑞康通信科技有限公司').first()
        
        if not company:
            print("❌ 未找到测试公司")
            return
        
        print(f"🏢 公司: {company.company_name}")
        
        # 检查是否已有库存记录
        existing_inventory = Inventory.query.filter_by(
            product_id=product.id,
            company_id=company.id
        ).first()
        
        if existing_inventory:
            print(f"当前库存: {existing_inventory.quantity}")
            # 增加库存到50
            existing_inventory.quantity = 50
            print(f"更新库存为: {existing_inventory.quantity}")
        else:
            # 获取一个用户ID（使用第一个用户）
            from app.models.user import User
            user = User.query.first()
            if not user:
                print("❌ 未找到用户")
                return
            
            # 创建新的库存记录
            new_inventory = Inventory(
                product_id=product.id,
                company_id=company.id,
                quantity=50,
                min_stock=10,
                location='测试仓库',
                created_by_id=user.id
            )
            db.session.add(new_inventory)
            print(f"创建新库存记录: {50} 件")
        
        try:
            db.session.commit()
            print("✅ 库存更新成功！")
            
            # 验证结果
            inventory = Inventory.query.filter_by(
                product_id=product.id,
                company_id=company.id
            ).first()
            
            print(f"验证结果: {company.company_name} 现有 {inventory.quantity} 件 {product.product_name}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 库存更新失败: {str(e)}")

if __name__ == '__main__':
    add_test_inventory()