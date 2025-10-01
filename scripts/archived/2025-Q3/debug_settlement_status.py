#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试结算单状态计算问题
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

def debug_settlement_status():
    """调试结算单状态计算"""
    app = create_app(LocalConfig)
    
    with app.app_context():
        # 获取所有结算单
        settlement_orders = SettlementOrder.query.order_by(SettlementOrder.created_at.desc()).all()
        
        print(f"总结算单数量: {len(settlement_orders)}")
        print("-" * 80)
        
        fully_settled_count = 0
        partially_settled_count = 0
        pending_count = 0
        
        for order in settlement_orders:
            # 统计明细结算状态
            total_details = len(order.details)
            settled_details = len([d for d in order.details if d.settlement_status == 'settled'])
            
            # 计算状态
            if settled_details == 0:
                status = 'pending'
                pending_count += 1
            elif settled_details == total_details:
                status = 'fully_settled'
                fully_settled_count += 1
            else:
                status = 'partially_settled'
                partially_settled_count += 1
            
            # 设置到order对象中
            order.settlement_status = status
            
            print(f"结算单: {order.order_number}")
            print(f"  总明细: {total_details}, 已结算: {settled_details}")
            print(f"  计算状态: {status}")
            
            # 显示明细状态分布
            if order.details:
                status_counts = {}
                for detail in order.details:
                    status_counts[detail.settlement_status] = status_counts.get(detail.settlement_status, 0) + 1
                print(f"  明细状态分布: {status_counts}")
            print()
        
        print("-" * 80)
        print(f"统计结果:")
        print(f"  完全结算: {fully_settled_count}")
        print(f"  部分结算: {partially_settled_count}")
        print(f"  待结算: {pending_count}")

if __name__ == '__main__':
    debug_settlement_status()