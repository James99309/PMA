#!/usr/bin/env python3
"""
修正结算明细状态：将draft状态改为pending状态
"""

from app import create_app, db
from app.models.pricing_order import SettlementOrderDetail, SettlementOrder

def fix_settlement_detail_status():
    """修正结算明细状态"""
    
    # 查询所有draft状态的明细
    draft_details = SettlementOrderDetail.query.filter_by(settlement_status='draft').all()
    
    print(f"=== 发现 {len(draft_details)} 条draft状态的明细需要修正 ===")
    
    updated_count = 0
    affected_orders = set()
    
    for detail in draft_details:
        # 将draft状态改为pending状态
        detail.settlement_status = 'pending'
        updated_count += 1
        
        # 记录受影响的结算单
        if detail.settlement_order:
            affected_orders.add(detail.settlement_order.id)
        
        if updated_count <= 5:
            print(f"修正明细 {detail.id}: {detail.product_name} draft -> pending")
    
    print(f"共修正 {updated_count} 条明细")
    print(f"影响 {len(affected_orders)} 个结算单")
    
    # 提交更改
    try:
        db.session.commit()
        print("✅ 明细状态修正完成")
        
        # 重新计算受影响结算单的状态
        print("\n=== 重新计算结算单状态 ===")
        for order_id in affected_orders:
            order = SettlementOrder.query.get(order_id)
            if order:
                old_status = order.settlement_status
                order.update_settlement_status()
                new_status = order.settlement_status
                print(f"结算单 {order.order_number}: {old_status} -> {new_status}")
        
        db.session.commit()
        print("✅ 结算单状态重新计算完成")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ 修正失败: {e}")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        fix_settlement_detail_status()