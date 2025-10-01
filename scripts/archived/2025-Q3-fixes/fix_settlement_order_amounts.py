#!/usr/bin/env python3
"""
修复结算单总金额与明细不匹配的问题
"""

from app import create_app, db
from app.models.pricing_order import SettlementOrder

def fix_settlement_order_amounts():
    """修复结算单总金额"""
    
    print("=== 修复结算单总金额 ===")
    
    # 获取所有结算单
    settlement_orders = SettlementOrder.query.all()
    
    print(f"检查 {len(settlement_orders)} 个结算单")
    
    fixed_count = 0
    
    for order in settlement_orders:
        # 计算明细总金额
        details = order.details
        calculated_total = sum(detail.total_price for detail in details) if details else 0.0
        
        # 检查是否需要修复
        if abs(calculated_total - (order.total_amount or 0.0)) > 0.01:  # 允许小数精度误差
            old_amount = order.total_amount
            print(f"修复结算单 {order.order_number}:")
            print(f"  原金额: {old_amount}")
            print(f"  计算金额: {calculated_total}")
            print(f"  明细数量: {len(details)}")
            
            # 更新总金额
            order.total_amount = calculated_total
            
            # 重新计算总折扣率
            if details:
                total_market_amount = sum(detail.market_price * detail.quantity for detail in details)
                if total_market_amount > 0:
                    order.total_discount_rate = calculated_total / total_market_amount
                    print(f"  更新折扣率: {order.total_discount_rate:.4f}")
            
            fixed_count += 1
    
    print(f"\n共修复 {fixed_count} 个结算单")
    
    if fixed_count > 0:
        try:
            db.session.commit()
            print("✅ 结算单金额修复完成")
            
            # 验证修复结果
            print("\n=== 验证修复结果 ===")
            
            # 重新检查前面有问题的结算单
            test_orders = ['SO202507-003', 'SO202507-004', 'SO202507-005', 'SO202507-006', 'SO202507-007']
            
            for order_number in test_orders:
                order = SettlementOrder.query.filter_by(order_number=order_number).first()
                if order:
                    details = order.details
                    calculated_total = sum(detail.total_price for detail in details) if details else 0.0
                    print(f"结算单 {order_number}: 总金额={order.total_amount}, 计算金额={calculated_total}")
                    
                    if abs(calculated_total - (order.total_amount or 0.0)) > 0.01:
                        print(f"  ❌ 仍然不匹配")
                    else:
                        print(f"  ✅ 金额正确")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 修复失败: {e}")
    else:
        print("ℹ️ 没有需要修复的结算单")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        fix_settlement_order_amounts()