#!/usr/bin/env python3
"""
检查批价单状态与结算明细状态的关系
"""

from app import create_app, db
from app.models.pricing_order import SettlementOrderDetail, SettlementOrder, PricingOrder
from sqlalchemy import func

def check_relationship():
    """检查批价单状态与结算明细状态的关系"""
    
    # 查询批价单状态与结算明细状态的分布
    relationship_query = db.session.query(
        PricingOrder.status.label('pricing_status'),
        SettlementOrderDetail.settlement_status.label('detail_status'),
        func.count(SettlementOrderDetail.id).label('count')
    ).join(
        SettlementOrder, SettlementOrder.pricing_order_id == PricingOrder.id
    ).join(
        SettlementOrderDetail, SettlementOrderDetail.settlement_order_id == SettlementOrder.id
    ).group_by(
        PricingOrder.status, SettlementOrderDetail.settlement_status
    ).all()
    
    print("=== 批价单状态 vs 结算明细状态分布 ===")
    print("批价单状态 | 明细状态 | 数量")
    print("-" * 40)
    
    for pricing_status, detail_status, count in relationship_query:
        print(f"{pricing_status:12} | {detail_status:8} | {count:4}")
    
    print()
    
    # 检查违反业务规则的数据
    print("=== 检查违反业务规则的数据 ===")
    
    # 1. 草稿/审批中/拒绝的批价单，但明细不是draft状态
    invalid_non_approved = db.session.query(
        PricingOrder.order_number,
        PricingOrder.status,
        SettlementOrderDetail.settlement_status,
        func.count(SettlementOrderDetail.id).label('count')
    ).join(
        SettlementOrder, SettlementOrder.pricing_order_id == PricingOrder.id
    ).join(
        SettlementOrderDetail, SettlementOrderDetail.settlement_order_id == SettlementOrder.id
    ).filter(
        PricingOrder.status.in_(['draft', 'pending', 'rejected']),
        SettlementOrderDetail.settlement_status != 'draft'
    ).group_by(
        PricingOrder.order_number, PricingOrder.status, SettlementOrderDetail.settlement_status
    ).all()
    
    if invalid_non_approved:
        print("❌ 发现违规数据：非已审批批价单但明细不是draft状态")
        for order_num, pricing_status, detail_status, count in invalid_non_approved[:5]:
            print(f"  批价单 {order_num}: 批价单状态={pricing_status}, 明细状态={detail_status}, 数量={count}")
    else:
        print("✅ 非已审批批价单的明细状态正确（都是draft）")
    
    print()
    
    # 2. 已审批的批价单，但明细是draft状态
    invalid_approved = db.session.query(
        PricingOrder.order_number,
        PricingOrder.status,
        SettlementOrderDetail.settlement_status,
        func.count(SettlementOrderDetail.id).label('count')
    ).join(
        SettlementOrder, SettlementOrder.pricing_order_id == PricingOrder.id
    ).join(
        SettlementOrderDetail, SettlementOrderDetail.settlement_order_id == SettlementOrder.id
    ).filter(
        PricingOrder.status == 'approved',
        SettlementOrderDetail.settlement_status == 'draft'
    ).group_by(
        PricingOrder.order_number, PricingOrder.status, SettlementOrderDetail.settlement_status
    ).all()
    
    if invalid_approved:
        print("❌ 发现违规数据：已审批批价单但明细还是draft状态")
        for order_num, pricing_status, detail_status, count in invalid_approved[:5]:
            print(f"  批价单 {order_num}: 批价单状态={pricing_status}, 明细状态={detail_status}, 数量={count}")
    else:
        print("✅ 已审批批价单的明细状态正确（不是draft）")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        check_relationship()