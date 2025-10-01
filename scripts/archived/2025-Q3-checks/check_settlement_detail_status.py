#!/usr/bin/env python3
"""
检查结算明细的状态分布
"""

from app import create_app, db
from app.models.pricing_order import SettlementOrderDetail
from sqlalchemy import func

def check_settlement_detail_status():
    """检查结算明细状态分布"""
    
    # 查询所有结算明细的状态分布
    status_distribution = db.session.query(
        SettlementOrderDetail.settlement_status,
        func.count(SettlementOrderDetail.id).label('count')
    ).group_by(SettlementOrderDetail.settlement_status).all()
    
    print("=== 结算明细状态分布 ===")
    total_details = 0
    for status, count in status_distribution:
        print(f"状态 '{status}': {count} 条明细")
        total_details += count
    
    print(f"总明细数: {total_details}")
    print()
    
    # 查看一些具体的明细记录
    sample_details = SettlementOrderDetail.query.limit(10).all()
    print("=== 前10条明细记录状态 ===")
    for detail in sample_details:
        print(f"明细ID {detail.id}: 产品={detail.product_name}, 状态='{detail.settlement_status}'")
    
    print()
    
    # 查看有draft状态的明细
    draft_details = SettlementOrderDetail.query.filter_by(settlement_status='draft').limit(5).all()
    print("=== draft状态的明细记录（前5条）===")
    for detail in draft_details:
        print(f"明细ID {detail.id}: 产品={detail.product_name}, 状态='{detail.settlement_status}', 结算单={detail.settlement_order.order_number if detail.settlement_order else 'None'}")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        check_settlement_detail_status()