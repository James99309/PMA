#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复无效的结算数据 - 将无库存支持的已结算产品改为待结算状态
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.pricing_order import SettlementOrder, SettlementOrderDetail
from config import LocalConfig
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_invalid_settlement_data():
    """修复无效的结算数据"""
    app = create_app(LocalConfig)
    
    with app.app_context():
        print("🔍 开始分析已结算明细中的无效数据...")
        print("=" * 80)
        
        # 获取所有已结算的明细
        settled_details = SettlementOrderDetail.query.filter_by(settlement_status='settled').all()
        
        print(f"总计已结算明细数量: {len(settled_details)}")
        print()
        
        invalid_settlements = []
        
        for detail in settled_details:
            # 检查产品是否存在
            if not detail.product_mn:
                continue
                
            product = Product.query.filter_by(product_mn=detail.product_mn).first()
            if not product:
                print(f"⚠️  产品 {detail.product_mn} 不存在，明细ID: {detail.id}")
                continue
            
            # 获取所有公司的该产品总库存
            total_inventory = db.session.query(db.func.sum(Inventory.quantity)).filter_by(product_id=product.id).scalar() or 0
            
            # 获取该产品的所有已结算数量
            total_settled = db.session.query(db.func.sum(SettlementOrderDetail.quantity)).filter(
                SettlementOrderDetail.product_mn == detail.product_mn,
                SettlementOrderDetail.settlement_status == 'settled'
            ).scalar() or 0
            
            # 如果已结算数量超过当前总库存很多，则认为有问题
            if total_settled > total_inventory + 100:  # 给100的容错空间
                invalid_settlements.append({
                    'detail': detail,
                    'product': product,
                    'total_inventory': total_inventory,
                    'total_settled': total_settled,
                    'excess': total_settled - total_inventory
                })
        
        print(f"发现 {len(invalid_settlements)} 个产品存在明显的库存不足问题:")
        print("-" * 80)
        
        # 按超出数量排序，最严重的在前面
        invalid_settlements.sort(key=lambda x: x['excess'], reverse=True)
        
        products_to_fix = {}
        
        for item in invalid_settlements:
            product_mn = item['product'].product_mn
            if product_mn not in products_to_fix:
                products_to_fix[product_mn] = {
                    'product_name': item['product'].product_name,
                    'total_inventory': item['total_inventory'],
                    'total_settled': item['total_settled'],
                    'excess': item['excess'],
                    'settlement_details': []
                }
            
            products_to_fix[product_mn]['settlement_details'].append(item['detail'])
        
        # 显示问题产品
        for product_mn, info in products_to_fix.items():
            print(f"产品: {info['product_name']} (MN: {product_mn})")
            print(f"  当前总库存: {info['total_inventory']}")
            print(f"  已结算总数: {info['total_settled']}")
            print(f"  超出数量: {info['excess']}")
            print(f"  涉及明细数: {len(info['settlement_details'])}")
            print()
        
        # 自动进行修复
        if not products_to_fix:
            print("✅ 没有发现明显的数据不一致问题")
            return
        
        print("=" * 80)
        print("⚠️  发现严重的数据不一致问题，自动进行修复...")
        
        print("\n🔧 开始修复数据...")
        fixed_count = 0
        
        for product_mn, info in products_to_fix.items():
            # 按时间倒序，优先保留最近的结算记录
            details_to_revert = sorted(info['settlement_details'], 
                                     key=lambda d: d.settlement_date or d.id, 
                                     reverse=True)
            
            # 计算需要保留多少已结算记录
            keep_settled = min(info['total_inventory'], info['total_settled'])
            revert_count = len(details_to_revert) - keep_settled if keep_settled > 0 else len(details_to_revert)
            
            print(f"处理 {info['product_name']} (MN: {product_mn}):")
            print(f"  保留 {keep_settled} 个已结算记录")
            print(f"  回退 {revert_count} 个记录为待结算状态")
            
            # 回退多余的已结算记录
            for i, detail in enumerate(details_to_revert):
                if i < revert_count:
                    detail.settlement_status = 'draft'
                    detail.settlement_company_id = None
                    detail.settlement_date = None
                    detail.settlement_notes = None
                    fixed_count += 1
                    print(f"    回退明细 {detail.id}: {detail.quantity} 件")
        
        try:
            db.session.commit()
            print(f"\n✅ 修复完成！共修复 {fixed_count} 个明细记录")
            
            # 验证修复结果
            print("\n🔍 验证修复结果...")
            for product_mn, info in products_to_fix.items():
                new_settled_count = db.session.query(db.func.sum(SettlementOrderDetail.quantity)).filter(
                    SettlementOrderDetail.product_mn == product_mn,
                    SettlementOrderDetail.settlement_status == 'settled'
                ).scalar() or 0
                
                print(f"{info['product_name']}: {info['total_settled']} → {new_settled_count} 件已结算")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ 修复失败: {str(e)}")

if __name__ == '__main__':
    fix_invalid_settlement_data()