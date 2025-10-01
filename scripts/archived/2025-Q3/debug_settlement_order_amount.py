#!/usr/bin/env python3
"""
调试结算单金额为0的问题
"""

from app import create_app, db
from app.models.pricing_order import SettlementOrder, SettlementOrderDetail, PricingOrder

def debug_settlement_order_amount():
    """调试结算单金额问题"""
    
    print("=== 调试结算单金额为0的问题 ===")
    
    # 查找金额为0的结算单
    zero_amount_orders = SettlementOrder.query.filter(
        SettlementOrder.total_amount == 0.0
    ).all()
    
    print(f"发现 {len(zero_amount_orders)} 个总金额为0的结算单")
    
    for order in zero_amount_orders[:5]:  # 只检查前5个
        print(f"\n=== 结算单 {order.order_number} ===")
        print(f"总金额: {order.total_amount}")
        print(f"结算状态: {order.settlement_status}")
        print(f"审批状态: {order.status}")
        
        # 检查关联的批价单
        pricing_order = order.pricing_order_ref
        if pricing_order:
            print(f"关联批价单: {pricing_order.order_number}")
            print(f"批价单状态: {pricing_order.status}")
            print(f"批价单结算总金额: {pricing_order.settlement_total_amount}")
        else:
            print("❌ 未找到关联的批价单")
        
        # 检查结算单明细
        details = order.details
        print(f"结算单明细数量: {len(details)}")
        
        if details:
            detail_total = sum(detail.total_price for detail in details)
            print(f"明细金额总计: {detail_total}")
            
            print("前3条明细:")
            for detail in details[:3]:
                print(f"  - 产品: {detail.product_name}")
                print(f"    数量: {detail.quantity}, 单价: {detail.unit_price}, 小计: {detail.total_price}")
                print(f"    明细状态: {detail.settlement_status}")
        else:
            print("❌ 该结算单没有明细记录")
        
        # 检查是否需要重新计算总金额
        if details:
            calculated_total = sum(detail.total_price for detail in details)
            if calculated_total != order.total_amount:
                print(f"⚠️ 金额不匹配！结算单总金额: {order.total_amount}, 计算总金额: {calculated_total}")
                print("建议重新计算总金额")
            else:
                print("✅ 金额匹配")
    
    # 检查特定的结算单 SO202507-005
    print(f"\n=== 特别检查 SO202507-005 ===")
    specific_order = SettlementOrder.query.filter_by(order_number='SO202507-005').first()
    
    if specific_order:
        print(f"结算单状态: {specific_order.status}")
        print(f"结算状态: {specific_order.settlement_status}")
        print(f"总金额: {specific_order.total_amount}")
        print(f"总折扣率: {specific_order.total_discount_rate}")
        
        # 检查明细
        details = specific_order.details
        print(f"明细数量: {len(details)}")
        
        if details:
            for i, detail in enumerate(details):
                print(f"明细 {i+1}:")
                print(f"  产品: {detail.product_name}")
                print(f"  市场价: {detail.market_price}")
                print(f"  单价: {detail.unit_price}")
                print(f"  数量: {detail.quantity}")
                print(f"  折扣率: {detail.discount_rate}")
                print(f"  小计: {detail.total_price}")
                print(f"  状态: {detail.settlement_status}")
        
        # 检查关联的批价单明细
        pricing_order = specific_order.pricing_order_ref
        if pricing_order:
            print(f"\n关联批价单: {pricing_order.order_number}")
            print(f"批价单结算总金额: {pricing_order.settlement_total_amount}")
            
            settlement_details = pricing_order.settlement_details
            print(f"批价单结算明细数量: {len(settlement_details)}")
            
            # 检查结算明细是否有金额
            for i, detail in enumerate(settlement_details[:3]):
                print(f"批价单结算明细 {i+1}:")
                print(f"  产品: {detail.product_name}")
                print(f"  数量: {detail.quantity}")
                print(f"  单价: {detail.unit_price}")
                print(f"  小计: {detail.total_price}")
                print(f"  状态: {detail.settlement_status}")
    else:
        print("❌ 未找到结算单 SO202507-005")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        debug_settlement_order_amount()