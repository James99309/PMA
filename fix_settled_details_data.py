#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复已结算明细的数据问题
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.pricing_order import SettlementOrder, SettlementOrderDetail
from app.models.customer import Company
from config import LocalConfig
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_settled_details_data():
    """修复已结算明细的数据问题"""
    app = create_app(LocalConfig)
    
    with app.app_context():
        print("🔍 开始修复已结算明细的数据问题...")
        print("=" * 80)
        
        # 查找所有状态为settled但缺少结算信息的明细
        problematic_details = SettlementOrderDetail.query.filter(
            SettlementOrderDetail.settlement_status == 'settled',
            SettlementOrderDetail.settlement_company_id.is_(None)
        ).all()
        
        print(f"发现 {len(problematic_details)} 个已结算但缺少结算信息的明细")
        
        if not problematic_details:
            print("✅ 没有发现需要修复的数据")
            return
        
        # 按结算单分组处理
        orders_to_fix = {}
        for detail in problematic_details:
            order_number = detail.settlement_order.order_number
            if order_number not in orders_to_fix:
                orders_to_fix[order_number] = []
            orders_to_fix[order_number].append(detail)
        
        print(f"涉及 {len(orders_to_fix)} 个结算单")
        print("-" * 80)
        
        fixed_count = 0
        
        for order_number, details in orders_to_fix.items():
            settlement_order = details[0].settlement_order
            print(f"处理结算单: {order_number}")
            
            # 确定默认结算公司（优先选择distributor，然后dealer）
            default_company = None
            if settlement_order.distributor_id:
                default_company = Company.query.get(settlement_order.distributor_id)
                print(f"  使用分销商作为默认结算公司: {default_company.company_name}")
            elif settlement_order.dealer_id:
                default_company = Company.query.get(settlement_order.dealer_id)
                print(f"  使用经销商作为默认结算公司: {default_company.company_name}")
            else:
                # 如果都没有，使用第一个公司
                default_company = Company.query.first()
                print(f"  使用第一个公司作为默认结算公司: {default_company.company_name}")
            
            if not default_company:
                print(f"  ❌ 无法找到默认公司，跳过此结算单")
                continue
            
            # 修复每个明细
            for detail in details:
                detail.settlement_company_id = default_company.id
                detail.settlement_date = detail.settlement_order.created_at or datetime.now()
                detail.settlement_notes = f'历史数据修复 - 结算到 {default_company.company_name}'
                fixed_count += 1
                print(f"    修复明细: {detail.product_name} (数量: {detail.quantity})")
        
        try:
            db.session.commit()
            print(f"\n✅ 修复完成！共修复 {fixed_count} 个明细记录")
            
            # 验证修复结果
            print("\n🔍 验证修复结果...")
            remaining_problematic = SettlementOrderDetail.query.filter(
                SettlementOrderDetail.settlement_status == 'settled',
                SettlementOrderDetail.settlement_company_id.is_(None)
            ).count()
            
            print(f"剩余有问题的明细数量: {remaining_problematic}")
            
            if remaining_problematic == 0:
                print("✅ 所有问题都已修复！")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 修复失败: {str(e)}")

if __name__ == '__main__':
    fix_settled_details_data()