#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""修复 SO202510-001 结算单的孤儿明细"""
import sys
import os

# 路径修正 - 支持从任何位置运行
def get_project_root():
    current = os.path.dirname(os.path.abspath(__file__))
    while current != '/':
        if os.path.exists(os.path.join(current, 'app')) and \
           os.path.exists(os.path.join(current, 'run.py')):
            return current
        current = os.path.dirname(current)
    raise RuntimeError("无法找到项目根目录")

sys.path.insert(0, get_project_root())

from app import create_app, db
from app.models.pricing_order import SettlementOrder, SettlementOrderDetail

app = create_app()
with app.app_context():
    print("=" * 60)
    print("修复 SO202510-001 结算单孤儿明细")
    print("=" * 60)

    # 查询结算单
    settlement = SettlementOrder.query.filter_by(order_number='SO202510-001').first()
    if not settlement:
        print("❌ 未找到 SO202510-001 结算单")
        sys.exit(1)

    print(f"✅ 找到结算单: ID={settlement.id}, 订单号={settlement.order_number}")
    print(f"   关联批价单ID: {settlement.pricing_order_id}")
    print(f"   分销商ID: {settlement.distributor_id}")
    print(f"   总金额: {settlement.total_amount}")

    # 查询孤儿明细
    orphan_details = SettlementOrderDetail.query.filter_by(
        pricing_order_id=settlement.pricing_order_id,
        settlement_order_id=None
    ).all()

    if not orphan_details:
        print(f"\n✅ 没有找到孤儿明细，结算单数据正常")
        print(f"   当前 settlement.details 包含 {len(settlement.details)} 条明细")
        sys.exit(0)

    print(f"\n📊 找到 {len(orphan_details)} 条孤儿明细:")
    print(f"{'ID':<8} {'产品名称':<30} {'数量':<8} {'单价':<12} {'小计':<12}")
    print("-" * 80)
    for detail in orphan_details:
        print(f"{detail.id:<8} {detail.product_name:<30} {detail.quantity:<8} {detail.unit_price:<12.2f} {detail.total_price:<12.2f}")

    total_amount = sum(d.total_price for d in orphan_details)
    print("-" * 80)
    print(f"{'合计':<38} {len(orphan_details):<8} {'':12} {total_amount:<12.2f}")

    # 自动确认修复（脚本模式）
    print(f"\n⚠️  将这 {len(orphan_details)} 条明细关联到结算单 SO202510-001 (ID={settlement.id})")
    print("🔧 自动执行修复...")

    # 执行修复
    try:
        print(f"\n🔧 正在修复...")

        for detail in orphan_details:
            detail.settlement_order_id = settlement.id

        db.session.commit()

        print(f"✅ 成功关联 {len(orphan_details)} 条明细到结算单")

        # 验证修复结果
        db.session.expire_all()  # 刷新缓存
        settlement = SettlementOrder.query.filter_by(order_number='SO202510-001').first()
        settlement_details_count = len(settlement.details)

        print(f"\n📊 验证结果:")
        print(f"   settlement.details 现在包含: {settlement_details_count} 条明细")

        if settlement_details_count == len(orphan_details):
            print(f"   ✅ 修复成功！设备数量从 0 恢复到 {settlement_details_count}")
        else:
            print(f"   ⚠️  预期 {len(orphan_details)} 条，实际 {settlement_details_count} 条")

    except Exception as e:
        db.session.rollback()
        print(f"\n❌ 修复失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    print("\n" + "=" * 60)
    print("✅ 修复完成！")
    print("   请刷新结算单管理页面查看结果")
    print("=" * 60)
