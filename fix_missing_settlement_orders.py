#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复缺失的结算单 - 为已审批的批价单生成结算单
"""

import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.pricing_order import PricingOrder, SettlementOrder, SettlementOrderDetail
from app.services.pricing_order_service import PricingOrderService
from config import LocalConfig
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_missing_settlement_orders():
    """为缺失结算单的已审批批价单生成结算单"""
    app = create_app(LocalConfig)
    
    with app.app_context():
        try:
            # 查找已审批但没有结算单的批价单
            missing_settlement_pricing_orders = db.session.query(PricingOrder).outerjoin(
                SettlementOrder, PricingOrder.id == SettlementOrder.pricing_order_id
            ).filter(
                PricingOrder.status == 'approved',
                SettlementOrder.id.is_(None)
            ).all()
            
            logger.info(f"发现 {len(missing_settlement_pricing_orders)} 个已审批但缺少结算单的批价单")
            
            created_count = 0
            for pricing_order in missing_settlement_pricing_orders:
                try:
                    logger.info(f"为批价单 {pricing_order.order_number} 创建结算单...")
                    
                    # 创建结算单
                    settlement_order = PricingOrderService.create_settlement_order(
                        pricing_order, 
                        pricing_order.created_by
                    )
                    
                    # 创建结算单明细
                    PricingOrderService.create_settlement_details(pricing_order, settlement_order)
                    
                    db.session.commit()
                    created_count += 1
                    logger.info(f"✅ 成功为批价单 {pricing_order.order_number} 创建结算单 {settlement_order.order_number}")
                    
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"❌ 为批价单 {pricing_order.order_number} 创建结算单失败: {str(e)}")
                    continue
            
            logger.info(f"✅ 修复完成！成功创建了 {created_count} 个结算单")
            
            # 验证修复结果
            remaining_missing = db.session.query(PricingOrder).outerjoin(
                SettlementOrder, PricingOrder.id == SettlementOrder.pricing_order_id
            ).filter(
                PricingOrder.status == 'approved',
                SettlementOrder.id.is_(None)
            ).count()
            
            logger.info(f"剩余缺少结算单的已审批批价单数量: {remaining_missing}")
            
        except Exception as e:
            logger.error(f"修复过程中发生错误: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    fix_missing_settlement_orders()