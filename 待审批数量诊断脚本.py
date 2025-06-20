#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
待审批数量诊断脚本
用于检查审批中心提示数字的逻辑错误
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.approval import ApprovalInstance, ApprovalStatus, ApprovalStep
from app.models.pricing_order import PricingOrder, PricingOrderApprovalRecord
from app.models.inventory import PurchaseOrder
from app.models.user import User
from app.helpers.approval_helpers import get_current_step_info
from sqlalchemy import and_, or_

def analyze_pending_approvals(user_id):
    """分析用户的待审批数量，检查逻辑错误"""
    
    print(f"\n🔍 分析用户 {user_id} 的待审批数量...")
    
    user = User.query.get(user_id)
    if not user:
        print(f"❌ 用户 {user_id} 不存在")
        return
    
    print(f"👤 用户信息: {user.username} ({user.real_name}) - 角色: {user.role}")
    
    # 方法1: 旧版实现 (第678行)
    print("\n📊 方法1: 旧版实现 (逐个检查)")
    
    # 通用审批系统 - 旧方法
    general_query = ApprovalInstance.query.filter(
        ApprovalInstance.status == ApprovalStatus.PENDING
    )
    
    pending_instance_ids = []
    print(f"   🔄 检查 {general_query.count()} 个待审批实例...")
    
    for instance in general_query.all():
        current_step = get_current_step_info(instance)
        if current_step and current_step.approver_user_id == user_id:
            pending_instance_ids.append(instance.id)
            print(f"      ✅ 实例 {instance.id}: {instance.object_type}_{instance.object_id}")
    
    old_general_count = len(pending_instance_ids)
    print(f"   📈 旧方法通用审批数量: {old_general_count}")
    
    # 批价单审批 - 共同方法
    pricing_order_query = PricingOrderApprovalRecord.query.join(
        PricingOrder,
        PricingOrderApprovalRecord.pricing_order_id == PricingOrder.id
    ).filter(
        PricingOrderApprovalRecord.approver_id == user_id,
        PricingOrderApprovalRecord.action.is_(None),
        PricingOrder.status == 'pending'
    )
    
    pricing_order_count = pricing_order_query.count()
    print(f"   📈 批价单审批数量: {pricing_order_count}")
    
    if pricing_order_count > 0:
        print("      批价单详情:")
        for record in pricing_order_query.all():
            po = record.pricing_order
            print(f"         • 批价单 {po.id}: {po.order_number} (步骤 {record.step_order})")
    
    old_total = old_general_count + pricing_order_count
    print(f"   🔢 旧方法总计: {old_total}")
    
    # 方法2: 新版实现 (第3085行)
    print("\n📊 方法2: 新版实现 (连接查询)")
    
    # 通用审批系统 - 新方法
    new_general_count = ApprovalInstance.query.join(
        ApprovalStep, 
        and_(
            ApprovalStep.process_id == ApprovalInstance.process_id,
            ApprovalStep.step_order == ApprovalInstance.current_step
        )
    ).filter(
        ApprovalStep.approver_user_id == user_id,
        ApprovalInstance.status == ApprovalStatus.PENDING
    ).count()
    
    print(f"   📈 新方法通用审批数量: {new_general_count}")
    
    # 批价单审批 - 新方法（相同）
    new_pricing_count = PricingOrder.query.join(
        PricingOrderApprovalRecord,
        and_(
            PricingOrderApprovalRecord.pricing_order_id == PricingOrder.id,
            PricingOrderApprovalRecord.step_order == PricingOrder.current_approval_step
        )
    ).filter(
        PricingOrderApprovalRecord.approver_id == user_id,
        PricingOrder.status == 'pending'
    ).count()
    
    print(f"   📈 新方法批价单数量: {new_pricing_count}")
    
    # 订单审批数量
    order_count = PurchaseOrder.query.join(
        ApprovalInstance,
        and_(
            ApprovalInstance.object_type == 'purchase_order',
            ApprovalInstance.object_id == PurchaseOrder.id,
            ApprovalInstance.status == ApprovalStatus.PENDING
        )
    ).join(
        ApprovalStep,
        and_(
            ApprovalStep.process_id == ApprovalInstance.process_id,
            ApprovalStep.step_order == ApprovalInstance.current_step
        )
    ).filter(
        ApprovalStep.approver_user_id == user_id
    ).count()
    
    print(f"   📈 订单审批数量: {order_count}")
    
    new_total = new_general_count + new_pricing_count + order_count
    print(f"   🔢 新方法总计: {new_total}")
    
    # 比较结果
    print("\n🔍 结果比较:")
    print(f"   通用审批: 旧方法 {old_general_count} vs 新方法 {new_general_count}")
    print(f"   批价单: 旧方法 {pricing_order_count} vs 新方法 {new_pricing_count}")
    print(f"   总数: 旧方法 {old_total} vs 新方法 {new_total}")
    
    if old_total != new_total:
        print(f"   ⚠️ 发现差异! 相差 {abs(old_total - new_total)} 个")
        
        # 详细分析差异
        if old_general_count != new_general_count:
            print("\n🔍 通用审批差异分析:")
            
            # 找出新方法能查到但旧方法查不到的
            new_general_instances = ApprovalInstance.query.join(
                ApprovalStep, 
                and_(
                    ApprovalStep.process_id == ApprovalInstance.process_id,
                    ApprovalStep.step_order == ApprovalInstance.current_step
                )
            ).filter(
                ApprovalStep.approver_user_id == user_id,
                ApprovalInstance.status == ApprovalStatus.PENDING
            ).all()
            
            new_instance_ids = [instance.id for instance in new_general_instances]
            
            print(f"   新方法查到的实例: {new_instance_ids}")
            print(f"   旧方法查到的实例: {pending_instance_ids}")
            
            # 找出差异
            only_in_new = set(new_instance_ids) - set(pending_instance_ids)
            only_in_old = set(pending_instance_ids) - set(new_instance_ids)
            
            if only_in_new:
                print(f"   ⚠️ 只有新方法查到的实例: {list(only_in_new)}")
                for instance_id in only_in_new:
                    instance = ApprovalInstance.query.get(instance_id)
                    current_step = get_current_step_info(instance)
                    print(f"      实例 {instance_id}: {instance.object_type}_{instance.object_id}")
                    print(f"         当前步骤: {instance.current_step}")
                    print(f"         步骤信息: {current_step}")
            
            if only_in_old:
                print(f"   ⚠️ 只有旧方法查到的实例: {list(only_in_old)}")
        
        if pricing_order_count != new_pricing_count:
            print(f"\n🔍 批价单差异分析:")
            print(f"   旧方法查询条件: action IS NULL")
            print(f"   新方法查询条件: step_order = current_approval_step")
            
            # 检查是否有步骤不匹配的情况
            mismatched_records = PricingOrderApprovalRecord.query.join(
                PricingOrder,
                PricingOrderApprovalRecord.pricing_order_id == PricingOrder.id
            ).filter(
                PricingOrderApprovalRecord.approver_id == user_id,
                PricingOrder.status == 'pending'
            ).all()
            
            for record in mismatched_records:
                po = record.pricing_order
                is_current_step = record.step_order == po.current_approval_step
                has_no_action = record.action is None
                
                if is_current_step != has_no_action:
                    print(f"      ⚠️ 不匹配记录: 批价单 {po.id}, 记录步骤 {record.step_order}, 当前步骤 {po.current_approval_step}, action: {record.action}")
    
    else:
        print("   ✅ 两种方法结果一致")
    
    return {
        'old_total': old_total,
        'new_total': new_total,
        'old_general': old_general_count,
        'new_general': new_general_count,
        'pricing_order': pricing_order_count,
        'new_pricing': new_pricing_count,
        'order': order_count
    }

def check_all_users():
    """检查所有用户的待审批数量"""
    print("\n🔍 检查所有用户的待审批数量...")
    
    users = User.query.filter(User.is_active == True).all()
    issues_found = []
    
    for user in users:
        try:
            result = analyze_pending_approvals(user.id)
            if result['old_total'] != result['new_total']:
                issues_found.append({
                    'user': user,
                    'result': result
                })
        except Exception as e:
            print(f"❌ 检查用户 {user.username} 时出错: {e}")
    
    if issues_found:
        print(f"\n⚠️ 发现 {len(issues_found)} 个用户存在差异:")
        for issue in issues_found:
            user = issue['user']
            result = issue['result']
            print(f"   {user.username}: 旧方法 {result['old_total']} vs 新方法 {result['new_total']}")
    else:
        print("\n✅ 所有用户的数量统计都一致")

def check_specific_user(username):
    """检查特定用户的待审批数量"""
    user = User.query.filter_by(username=username).first()
    if not user:
        print(f"❌ 用户 {username} 不存在")
        return
    
    analyze_pending_approvals(user.id)

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        print("🔍 待审批数量诊断脚本")
        print("=" * 50)
        
        if len(sys.argv) > 1:
            username = sys.argv[1]
            check_specific_user(username)
        else:
            print("请提供用户名作为参数，例如:")
            print("python 待审批数量诊断脚本.py linwengguan")
            print("\n或者检查所有用户:")
            print("python 待审批数量诊断脚本.py --all")
            
            if len(sys.argv) > 1 and sys.argv[1] == '--all':
                check_all_users() 