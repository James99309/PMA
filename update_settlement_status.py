#!/usr/bin/env python3
"""
更新结算单的settlement_status字段
根据现有的明细状态来设置正确的结算状态
"""

from app import create_app, db
from app.models.pricing_order import SettlementOrder

def update_all_settlement_status():
    """更新所有结算单的settlement_status字段"""
    
    # 获取所有结算单
    settlement_orders = SettlementOrder.query.all()
    
    print(f"=== 开始更新 {len(settlement_orders)} 个结算单的状态 ===")
    
    updated_count = 0
    status_summary = {
        'pending': 0,
        'partially_settled': 0, 
        'fully_settled': 0
    }
    
    for order in settlement_orders:
        # 记录原状态
        old_status = getattr(order, 'settlement_status', None)
        
        # 更新状态
        order.update_settlement_status()
        new_status = order.settlement_status
        
        # 统计新状态
        if new_status in status_summary:
            status_summary[new_status] += 1
        
        print(f"结算单 {order.order_number}: {old_status} -> {new_status} (明细数: {len(order.details)})")
        
        # 如果是前3个，显示明细状态
        if updated_count < 3:
            for i, detail in enumerate(order.details):
                print(f"  明细{i+1}: settlement_status='{detail.settlement_status}'")
        
        updated_count += 1
    
    # 提交更改
    try:
        db.session.commit()
        print(f"\n=== 更新完成，共更新 {updated_count} 个结算单 ===")
        print("状态分布:")
        for status, count in status_summary.items():
            print(f"  {status}: {count} 单")
        
    except Exception as e:
        db.session.rollback()
        print(f"更新失败，已回滚: {e}")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        update_all_settlement_status()