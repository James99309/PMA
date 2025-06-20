#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复批价单数据不一致脚本
解决审批记录与当前步骤不匹配的问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.pricing_order import PricingOrder, PricingOrderApprovalRecord
from app.models.user import User

def fix_pricing_order_inconsistency():
    """修复批价单审批记录的数据不一致"""
    
    print("🔧 检查并修复批价单审批记录的数据不一致...")
    
    # 查找所有有问题的批价单
    inconsistent_orders = []
    
    # 检查所有批价单
    all_pricing_orders = PricingOrder.query.all()
    
    for po in all_pricing_orders:
        # 查找该批价单的所有审批记录
        records = PricingOrderApprovalRecord.query.filter_by(
            pricing_order_id=po.id
        ).order_by(PricingOrderApprovalRecord.step_order).all()
        
        if not records:
            continue
            
        # 检查是否有待审批记录与当前步骤不匹配的情况
        pending_records = [r for r in records if r.action is None]
        
        for record in pending_records:
            if record.step_order != po.current_approval_step:
                inconsistent_orders.append({
                    'po': po,
                    'record': record,
                    'issue': f'待审批记录步骤{record.step_order}与当前步骤{po.current_approval_step}不匹配'
                })
    
    print(f"发现 {len(inconsistent_orders)} 个数据不一致的批价单:")
    
    for item in inconsistent_orders:
        po = item['po']
        record = item['record']
        issue = item['issue']
        
        print(f"\n批价单 {po.id}: {po.order_number}")
        print(f"  问题: {issue}")
        print(f"  当前状态: {po.status}")
        print(f"  当前审批步骤: {po.current_approval_step}")
        print(f"  审批人: {record.approver.username}")
        print(f"  记录步骤: {record.step_order}")
        
        # 分析并建议修复方案
        all_records = PricingOrderApprovalRecord.query.filter_by(
            pricing_order_id=po.id
        ).order_by(PricingOrderApprovalRecord.step_order).all()
        
        print("  所有审批记录:")
        for r in all_records:
            status = r.action if r.action else '待审批'
            print(f"    步骤{r.step_order}: {r.approver.username} - {status}")
        
        # 提供修复建议
        if po.status == 'approved':
            print("  🔧 建议: 批价单已通过，应清理待审批记录")
            # 清理待审批记录
            record.action = 'approve'
            print(f"  ✅ 已修复: 将步骤{record.step_order}的记录标记为已通过")
            
        elif po.status == 'rejected':
            print("  🔧 建议: 批价单已拒绝，应清理待审批记录")
            record.action = 'reject'
            print(f"  ✅ 已修复: 将步骤{record.step_order}的记录标记为已拒绝")
            
        elif po.status == 'pending':
            # 检查是否应该更新当前步骤
            approved_steps = [r.step_order for r in all_records if r.action == 'approve']
            max_approved_step = max(approved_steps) if approved_steps else 0
            expected_current_step = max_approved_step + 1
            
            if po.current_approval_step == 0 and expected_current_step > 0:
                print(f"  🔧 建议: 更新当前审批步骤从 {po.current_approval_step} 到 {expected_current_step}")
                po.current_approval_step = expected_current_step
                print(f"  ✅ 已修复: 当前审批步骤更新为 {expected_current_step}")
                
            elif record.step_order < po.current_approval_step:
                # 记录步骤小于当前步骤，应该已经处理了
                print(f"  🔧 建议: 步骤{record.step_order}应该已经通过")
                record.action = 'approve'
                print(f"  ✅ 已修复: 将步骤{record.step_order}的记录标记为已通过")
        
        else:
            print(f"  ⚠️ 未知状态: {po.status}")
    
    if inconsistent_orders:
        print(f"\n💾 提交修复...")
        try:
            db.session.commit()
            print("✅ 数据修复完成!")
            
            # 验证修复效果
            print("\n🔍 验证修复效果...")
            verify_fix()
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 修复失败: {e}")
    else:
        print("\n✅ 没有发现数据不一致问题")

def verify_fix():
    """验证修复效果"""
    
    # 重新检查林文冠用户的待审批数量
    user = User.query.filter_by(username='linwengguan').first()
    if not user:
        print("❌ 用户不存在")
        return
    
    # 检查该用户的待审批记录
    user_pending_records = PricingOrderApprovalRecord.query.filter_by(
        approver_id=user.id,
        action=None
    ).all()
    
    print(f"修复后林文冠用户的待审批记录数: {len(user_pending_records)}")
    
    for record in user_pending_records:
        po = record.pricing_order
        print(f"  批价单 {po.id}: 步骤{record.step_order} (当前步骤: {po.current_approval_step})")
        
        if record.step_order == po.current_approval_step:
            print("    ✅ 记录与当前步骤匹配")
        else:
            print("    ❌ 记录与当前步骤仍不匹配")
    
    # 重新计算待审批数量
    from app.helpers.approval_helpers import get_pending_approval_count
    count = get_pending_approval_count(user.id)
    print(f"\n修复后的待审批数量: {count}")

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        print("🔧 批价单数据不一致修复脚本")
        print("=" * 50)
        
        fix_pricing_order_inconsistency() 