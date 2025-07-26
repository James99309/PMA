#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
创建测试部分结算数据
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.pricing_order import SettlementOrder, SettlementOrderDetail
from config import LocalConfig
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_partial_settlement():
    """创建测试部分结算数据"""
    app = create_app(LocalConfig)
    
    with app.app_context():
        # 找一个有多个明细的待结算单
        settlement_order = SettlementOrder.query.filter(
            SettlementOrder.order_number.like('SO202507%')
        ).join(SettlementOrderDetail).filter(
            SettlementOrderDetail.settlement_status == 'draft'
        ).first()
        
        if not settlement_order:
            print("没有找到合适的结算单进行测试")
            return
        
        if len(settlement_order.details) < 2:
            print(f"结算单 {settlement_order.order_number} 明细太少，无法测试部分结算")
            return
        
        print(f"选择结算单: {settlement_order.order_number}")
        print(f"总明细数: {len(settlement_order.details)}")
        
        # 将一半明细设置为已结算
        half_count = len(settlement_order.details) // 2
        for i, detail in enumerate(settlement_order.details):
            if i < half_count:
                detail.settlement_status = 'settled'
                print(f"  明细 {i+1}: {detail.product_name} -> 已结算")
            else:
                print(f"  明细 {i+1}: {detail.product_name} -> 保持待结算")
        
        try:
            db.session.commit()
            print(f"\n✅ 成功创建部分结算测试数据")
            print(f"结算单 {settlement_order.order_number} 现在状态: {settlement_order.settlement_status}")
            
            # 验证状态
            total_details = len(settlement_order.details)
            settled_details = len([d for d in settlement_order.details if d.settlement_status == 'settled'])
            print(f"总明细: {total_details}, 已结算: {settled_details}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 创建测试数据失败: {str(e)}")

if __name__ == '__main__':
    create_test_partial_settlement()