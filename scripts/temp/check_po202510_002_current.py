#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查批价单 PO202510-002 的当前状态"""
import sys, os

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
from app.models.pricing_order import PricingOrder, SettlementOrder
from app.models.customer import Company
from sqlalchemy import text

def check_status():
    """检查状态"""
    app = create_app()
    with app.app_context():
        print("=" * 80)
        print("检查批价单 PO202510-002 的当前状态")
        print("=" * 80)

        # 查询批价单
        pricing_order = PricingOrder.query.filter_by(order_number='PO202510-002').first()

        if not pricing_order:
            print("\n❌ 未找到批价单 PO202510-002")
            return False

        print(f"\n📋 批价单信息:")
        print(f"  ID: {pricing_order.id}")
        print(f"  订单号: {pricing_order.order_number}")
        print(f"  状态: {pricing_order.status}")
        print(f"  创建时间: {pricing_order.created_at}")
        print(f"  更新时间: {pricing_order.updated_at}")
        print(f"  当前审批步骤: {pricing_order.current_approval_step}")

        print(f"\n🏢 业务类型标记:")
        print(f"  is_direct_contract (厂商直签): {pricing_order.is_direct_contract}")
        print(f"  is_factory_pickup (厂家提货): {pricing_order.is_factory_pickup}")

        print(f"\n👥 客户信息:")
        print(f"  dealer_id (经销商ID): {pricing_order.dealer_id}")
        if pricing_order.dealer_id:
            dealer = Company.query.get(pricing_order.dealer_id)
            if dealer:
                print(f"    └─ 名称: {dealer.company_name}")
                print(f"    └─ 类型: {dealer.company_type}")

        print(f"  distributor_id (分销商ID): {pricing_order.distributor_id}")
        if pricing_order.distributor_id:
            distributor = Company.query.get(pricing_order.distributor_id)
            if distributor:
                print(f"    └─ 名称: {distributor.company_name}")
                print(f"    └─ 类型: {distributor.company_type}")

        # 业务规则验证
        print(f"\n✅ 批价单业务规则验证:")
        pricing_ok = True
        if pricing_order.is_direct_contract:
            if pricing_order.dealer_id is None and pricing_order.distributor_id is None:
                print(f"  ✓ 厂商直签规则正确")
            else:
                print(f"  ❌ 厂商直签规则违规")
                pricing_ok = False
        elif pricing_order.is_factory_pickup:
            if pricing_order.dealer_id is not None and pricing_order.distributor_id is None:
                print(f"  ✓ 厂家提货规则正确")
            else:
                print(f"  ❌ 厂家提货规则违规")
                pricing_ok = False
        else:
            print(f"  常规渠道")

        # 查询结算单
        settlement_orders = SettlementOrder.query.filter_by(
            pricing_order_id=pricing_order.id
        ).all()

        print(f"\n📄 关联的结算单（{len(settlement_orders)}个）:")

        all_ok = pricing_ok
        for i, so in enumerate(settlement_orders, 1):
            print(f"\n  结算单 #{i}:")
            print(f"    订单号: {so.order_number}")
            print(f"    状态: {so.status}")
            print(f"    创建时间: {so.created_at}")
            print(f"    更新时间: {so.updated_at}")
            print(f"    is_direct_contract: {so.is_direct_contract}")
            print(f"    is_factory_pickup: {so.is_factory_pickup}")
            print(f"    dealer_id: {so.dealer_id}")
            print(f"    distributor_id: {so.distributor_id}")

            # 验证一致性
            print(f"\n    一致性验证:")
            if so.is_direct_contract == pricing_order.is_direct_contract:
                print(f"      ✓ is_direct_contract 与批价单一致")
            else:
                print(f"      ❌ is_direct_contract 不一致 (批价单:{pricing_order.is_direct_contract}, 结算单:{so.is_direct_contract})")
                all_ok = False

            if so.is_factory_pickup == pricing_order.is_factory_pickup:
                print(f"      ✓ is_factory_pickup 与批价单一致")
            else:
                print(f"      ❌ is_factory_pickup 不一致 (批价单:{pricing_order.is_factory_pickup}, 结算单:{so.is_factory_pickup})")
                all_ok = False

            # 验证业务规则
            if so.is_direct_contract:
                if so.dealer_id is None and so.distributor_id is None:
                    print(f"      ✓ 结算单厂商直签规则正确")
                else:
                    print(f"      ❌ 结算单厂商直签规则违规")
                    all_ok = False
            elif so.is_factory_pickup:
                if so.distributor_id is None:
                    print(f"      ✓ 结算单厂家提货规则正确")
                else:
                    print(f"      ❌ 结算单厂家提货规则违规")
                    all_ok = False

        print("\n" + "=" * 80)
        if all_ok:
            print("✅ 所有字段配置正确，数据一致！")
        else:
            print("❌ 发现数据不一致，需要修复！")
        print("=" * 80)

        return all_ok

if __name__ == '__main__':
    try:
        success = check_status()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
