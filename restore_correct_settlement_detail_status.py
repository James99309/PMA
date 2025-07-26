#!/usr/bin/env python3
"""
恢复正确的结算明细状态
- 将非已审批批价单的明细恢复为draft状态  
- 只有已审批批价单的明细保持pending/settled状态
"""

from app import create_app, db
from app.models.pricing_order import SettlementOrderDetail, SettlementOrder, PricingOrder
from sqlalchemy import func

def restore_correct_settlement_detail_status():
    """恢复正确的结算明细状态"""
    
    print("=== 开始恢复正确的结算明细状态 ===")
    
    # 查询当前状态分布
    print("=== 当前状态分布 ===")
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
    
    for pricing_status, detail_status, count in relationship_query:
        print(f"批价单状态={pricing_status}, 明细状态={detail_status}: {count}条")
    
    print()
    
    # 1. 将非已审批批价单的明细恢复为draft状态
    print("=== 第一步：恢复非已审批批价单的明细为draft状态 ===")
    
    # 查找违规数据：非已审批但明细不是draft状态
    invalid_details = db.session.query(SettlementOrderDetail).join(
        SettlementOrder, SettlementOrder.id == SettlementOrderDetail.settlement_order_id
    ).join(
        PricingOrder, PricingOrder.id == SettlementOrder.pricing_order_id
    ).filter(
        PricingOrder.status.in_(['draft', 'pending', 'rejected']),
        SettlementOrderDetail.settlement_status != 'draft'
    ).all()
    
    print(f"发现 {len(invalid_details)} 条需要恢复为draft状态的明细")
    
    updated_count = 0
    affected_orders = set()
    
    for detail in invalid_details:
        old_status = detail.settlement_status
        detail.settlement_status = 'draft'
        updated_count += 1
        
        # 记录受影响的结算单
        if detail.settlement_order:
            affected_orders.add(detail.settlement_order.id)
        
        if updated_count <= 10:
            pricing_order = detail.settlement_order.pricing_order_ref if detail.settlement_order else None
            pricing_status = pricing_order.status if pricing_order else 'unknown'
            print(f"  明细 {detail.id}: {detail.product_name} ({pricing_status}批价单) {old_status} -> draft")
    
    print(f"共恢复 {updated_count} 条明细为draft状态")
    print(f"影响 {len(affected_orders)} 个结算单")
    
    # 2. 检查已审批批价单的明细状态
    print("\n=== 第二步：检查已审批批价单的明细状态 ===")
    
    approved_draft_details = db.session.query(SettlementOrderDetail).join(
        SettlementOrder, SettlementOrder.id == SettlementOrderDetail.settlement_order_id
    ).join(
        PricingOrder, PricingOrder.id == SettlementOrder.pricing_order_id
    ).filter(
        PricingOrder.status == 'approved',
        SettlementOrderDetail.settlement_status == 'draft'
    ).all()
    
    print(f"发现 {len(approved_draft_details)} 条已审批批价单但还是draft状态的明细")
    
    # 将已审批批价单的draft明细改为pending状态
    for detail in approved_draft_details:
        detail.settlement_status = 'pending'
        updated_count += 1
        
        if detail.settlement_order:
            affected_orders.add(detail.settlement_order.id)
        
        if len(approved_draft_details) <= 10:
            print(f"  明细 {detail.id}: {detail.product_name} (approved批价单) draft -> pending")
    
    print(f"共修正 {len(approved_draft_details)} 条已审批批价单的明细为pending状态")
    
    # 提交更改
    try:
        db.session.commit()
        print(f"\n✅ 明细状态恢复完成，共修正 {updated_count} 条明细")
        
        # 重新计算受影响结算单的状态
        print("\n=== 第三步：重新计算结算单状态 ===")
        for order_id in affected_orders:
            order = SettlementOrder.query.get(order_id)
            if order:
                old_status = order.settlement_status
                order.update_settlement_status()
                new_status = order.settlement_status
                if old_status != new_status:
                    print(f"结算单 {order.order_number}: {old_status} -> {new_status}")
        
        db.session.commit()
        print("✅ 结算单状态重新计算完成")
        
        # 验证修复结果
        print("\n=== 修复后状态分布 ===")
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
        
        for pricing_status, detail_status, count in relationship_query:
            print(f"批价单状态={pricing_status}, 明细状态={detail_status}: {count}条")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 恢复失败: {e}")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        restore_correct_settlement_detail_status()