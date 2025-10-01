#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试特定结算单 SO202506-020 的状态
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

def debug_settlement_order_SO202506_020():
    """调试结算单 SO202506-020"""
    app = create_app(LocalConfig)
    
    with app.app_context():
        # 查找特定结算单
        settlement_order = SettlementOrder.query.filter_by(order_number='SO202506-020').first()
        
        if not settlement_order:
            print("❌ 未找到结算单 SO202506-020")
            return
        
        print(f"🔍 结算单详情: {settlement_order.order_number}")
        print(f"计算的状态: {settlement_order.settlement_status}")
        print(f"总明细数量: {len(settlement_order.details)}")
        print("-" * 80)
        
        # 统计明细状态
        status_count = {}
        settled_count = 0
        draft_count = 0
        
        print("📋 明细状态详情:")
        for i, detail in enumerate(settlement_order.details, 1):
            status = detail.settlement_status
            status_count[status] = status_count.get(status, 0) + 1
            
            if status == 'settled':
                settled_count += 1
            elif status == 'draft':
                draft_count += 1
            
            print(f"  {i:2d}. {detail.product_name}")
            print(f"      产品MN: {detail.product_mn or '无'}")
            print(f"      数量: {detail.quantity}")
            print(f"      状态: {status}")
            
            # 如果是HYCCN34Y，特别标注
            if detail.product_mn and 'HYCCN34Y' in detail.product_mn:
                print(f"      ⚠️  这是用户提到的HYCCN34Y产品!")
            print()
        
        print("-" * 80)
        print(f"📊 状态统计:")
        print(f"  总明细: {len(settlement_order.details)}")
        print(f"  已结算 (settled): {settled_count}")
        print(f"  待结算 (draft): {draft_count}")
        print(f"  状态分布: {status_count}")
        print()
        
        # 验证计算逻辑
        print("🧮 状态计算验证:")
        if settled_count == 0:
            expected_status = 'pending'
        elif settled_count == len(settlement_order.details):
            expected_status = 'fully_settled'
        else:
            expected_status = 'partially_settled'
        
        print(f"  期望状态: {expected_status}")
        print(f"  实际状态: {settlement_order.settlement_status}")
        
        if expected_status != settlement_order.settlement_status:
            print("  ❌ 状态计算错误!")
        else:
            print("  ✅ 状态计算正确")
        
        # 如果有未结算明细但被标记为完全结算，这是错误的
        if draft_count > 0 and settlement_order.settlement_status == 'fully_settled':
            print(f"\n🚨 严重错误: 结算单有 {draft_count} 个未结算明细，但被错误地标记为完全结算!")
            print("   这个结算单应该在 '部分结算' 或 '待结算' 列表中，而不是 '已结算' 列表中!")

if __name__ == '__main__':
    debug_settlement_order_SO202506_020()