#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查HYCCN34Y产品的库存状态
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.inventory import Inventory, InventoryTransaction
from app.models.product import Product
from app.models.customer import Company
from app.models.pricing_order import SettlementOrder, SettlementOrderDetail
from config import LocalConfig
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_HYCCN34Y_inventory():
    """检查HYCCN34Y产品的库存状态"""
    app = create_app(LocalConfig)
    
    with app.app_context():
        # 查找HYCCN34Y产品
        product = Product.query.filter_by(product_mn='HYCCN34Y').first()
        
        if not product:
            print("❌ 未找到产品MN: HYCCN34Y")
            return
        
        print(f"🔍 产品信息: {product.product_name} (MN: {product.product_mn})")
        print("-" * 80)
        
        # 查找所有公司的该产品库存
        inventories = Inventory.query.filter_by(product_id=product.id).all()
        
        print("📦 所有公司库存情况:")
        total_inventory = 0
        for inventory in inventories:
            company = inventory.company
            print(f"  {company.company_name}: {inventory.quantity} 件")
            total_inventory += inventory.quantity
        
        print(f"  总库存: {total_inventory} 件")
        print()
        
        # 查找相关的结算明细
        settlement_details = SettlementOrderDetail.query.filter_by(product_mn='HYCCN34Y').all()
        
        print("📋 结算明细记录:")
        total_settled = 0
        for detail in settlement_details:
            if detail.settlement_order:
                print(f"  结算单: {detail.settlement_order.order_number}")
            else:
                print(f"  结算单: 未关联")
            print(f"    数量: {detail.quantity}")
            print(f"    状态: {detail.settlement_status}")
            if detail.settlement_company:
                print(f"    结算公司: {detail.settlement_company.company_name}")
            if detail.settlement_date:
                print(f"    结算时间: {detail.settlement_date}")
            
            if detail.settlement_status == 'settled':
                total_settled += detail.quantity
            print()
        
        print(f"  总已结算数量: {total_settled} 件")
        print()
        
        # 查找相关的库存变动记录
        transactions = InventoryTransaction.query.join(Inventory).filter(
            Inventory.product_id == product.id,
            InventoryTransaction.reference_type == 'settlement'
        ).order_by(InventoryTransaction.created_at.desc()).all()
        
        print("📊 结算相关的库存变动记录:")
        if transactions:
            for trans in transactions:
                print(f"  {trans.created_at}: {trans.transaction_type} {trans.quantity} 件")
                print(f"    公司: {trans.inventory.company.company_name}")
                print(f"    描述: {trans.description}")
                print()
        else:
            print("  无相关库存变动记录")
        
        # 分析潜在问题
        print("🔎 问题分析:")
        if total_settled > total_inventory:
            print(f"  ⚠️  已结算数量 ({total_settled}) 超过当前总库存 ({total_inventory})")
            print("  这可能表明:")
            print("    1. 结算时有足够库存，但后来被其他操作减少")
            print("    2. 存在数据不一致性")
            print("    3. 结算逻辑存在漏洞")

if __name__ == '__main__':
    check_HYCCN34Y_inventory()