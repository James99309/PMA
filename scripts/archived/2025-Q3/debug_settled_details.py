#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试已结算明细的显示问题
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.pricing_order import SettlementOrder, SettlementOrderDetail
from app.models.customer import Company
from config import LocalConfig
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_settled_details():
    """调试已结算明细的显示问题"""
    app = create_app(LocalConfig)
    
    with app.app_context():
        # 查找SO202506-020结算单
        settlement_order = SettlementOrder.query.filter_by(order_number='SO202506-020').first()
        
        if not settlement_order:
            print("❌ 未找到结算单 SO202506-020")
            return
        
        print(f"🔍 结算单: {settlement_order.order_number}")
        print(f"状态: {settlement_order.settlement_status}")
        print("-" * 80)
        
        # 检查每个明细
        for i, detail in enumerate(settlement_order.details, 1):
            print(f"明细 {i}: {detail.product_name}")
            print(f"  产品MN: {detail.product_mn}")
            print(f"  数量: {detail.quantity}")
            print(f"  状态: {detail.settlement_status}")
            print(f"  结算公司ID: {detail.settlement_company_id}")
            
            if detail.settlement_company_id:
                company = Company.query.get(detail.settlement_company_id)
                if company:
                    print(f"  结算公司: {company.company_name}")
                else:
                    print(f"  ❌ 结算公司ID {detail.settlement_company_id} 不存在")
            else:
                print(f"  ❌ 结算公司ID为空")
            
            if detail.settlement_company:
                print(f"  关系查询结果: {detail.settlement_company.company_name}")
            else:
                print(f"  ❌ 关系查询结果为空")
            
            print(f"  结算时间: {detail.settlement_date}")
            print(f"  结算备注: {detail.settlement_notes}")
            print()

if __name__ == '__main__':
    debug_settled_details()