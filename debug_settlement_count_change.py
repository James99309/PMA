#!/usr/bin/env python3
"""
调试结算单数量变化的原因
"""

from app import create_app, db
from app.models.pricing_order import SettlementOrder, PricingOrder

def debug_settlement_count():
    """调试结算单数量变化"""
    
    print("=== 调试结算单数量变化 ===")
    
    # 1. 查看所有结算单
    all_orders = SettlementOrder.query.all()
    print(f"数据库中总结算单数量: {len(all_orders)}")
    
    # 2. 查看已审批批价单的结算单（新逻辑）
    approved_orders = SettlementOrder.query.join(
        PricingOrder, SettlementOrder.pricing_order_id == PricingOrder.id
    ).filter(
        PricingOrder.status == 'approved'
    ).all()
    print(f"已审批批价单的结算单数量: {len(approved_orders)}")
    
    # 3. 查看不同批价单状态的结算单分布
    status_distribution = {}
    for order in all_orders:
        pricing_order = order.pricing_order_ref
        if pricing_order:
            status = pricing_order.status
            if status not in status_distribution:
                status_distribution[status] = []
            status_distribution[status].append(order.order_number)
        else:
            if 'no_pricing_order' not in status_distribution:
                status_distribution['no_pricing_order'] = []
            status_distribution['no_pricing_order'].append(order.order_number)
    
    print(f"\n=== 按批价单状态分布的结算单 ===")
    for status, orders in status_distribution.items():
        print(f"批价单状态 '{status}': {len(orders)} 个结算单")
        if len(orders) <= 5:
            print(f"  结算单: {', '.join(orders)}")
        else:
            print(f"  结算单: {', '.join(orders[:5])} ... (共{len(orders)}个)")
    
    # 4. 查看被过滤掉的结算单
    print(f"\n=== 被过滤掉的结算单 (非已审批批价单) ===")
    filtered_out_orders = SettlementOrder.query.join(
        PricingOrder, SettlementOrder.pricing_order_id == PricingOrder.id
    ).filter(
        PricingOrder.status != 'approved'
    ).all()
    
    print(f"被过滤掉的结算单数量: {len(filtered_out_orders)}")
    for order in filtered_out_orders:
        pricing_order = order.pricing_order_ref
        print(f"  {order.order_number}: 批价单状态={pricing_order.status if pricing_order else 'None'}")
    
    # 5. 验证数学关系
    total_check = len(approved_orders) + len(filtered_out_orders)
    orders_with_pricing = SettlementOrder.query.filter(
        SettlementOrder.pricing_order_id.isnot(None)
    ).count()
    
    print(f"\n=== 数量验证 ===")
    print(f"已审批结算单 + 非已审批结算单 = {len(approved_orders)} + {len(filtered_out_orders)} = {total_check}")
    print(f"有关联批价单的结算单总数: {orders_with_pricing}")
    print(f"数据库中总结算单数: {len(all_orders)}")
    
    if total_check == orders_with_pricing:
        print("✅ 数量关系正确")
    else:
        print("❌ 数量关系有问题，可能有结算单没有关联批价单")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        debug_settlement_count()