#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
待审批详细检查脚本
分析待审批数量差异的具体原因
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from app.models.approval import ApprovalInstance, ApprovalStatus, ApprovalStep
from app.models.pricing_order import PricingOrder, PricingOrderApprovalRecord
from app.models.user import User
from app.helpers.approval_helpers import get_current_step_info
from sqlalchemy import and_, or_

def detailed_check(username):
    """详细检查待审批数量差异"""
    
    print(f"\n🔍 详细检查用户 {username} 的待审批情况...")
    
    user = User.query.filter_by(username=username).first()
    if not user:
        print(f"❌ 用户 {username} 不存在")
        return
    
    print(f"👤 用户: {user.username} ({user.real_name}) - 角色: {user.role}")
    
    # 1. 检查通用审批系统中的待审批实例
    print("\n📋 1. 通用审批系统检查:")
    
    pending_instances = ApprovalInstance.query.filter_by(status=ApprovalStatus.PENDING).all()
    print(f"   系统中待审批实例总数: {len(pending_instances)}")
    
    user_pending_instances = []
    for instance in pending_instances:
        current_step = get_current_step_info(instance)
        print(f"   实例 {instance.id}: {instance.object_type}_{instance.object_id}")
        print(f"      当前步骤: {instance.current_step}")
        print(f"      流程ID: {instance.process_id}")
        
        if current_step:
            print(f"      当前审批人: {current_step.approver_user_id} ({current_step.approver.username if current_step.approver else '未知'})")
            if current_step.approver_user_id == user.id:
                user_pending_instances.append(instance)
                print(f"      ✅ 该用户是当前步骤审批人")
            else:
                print(f"      ❌ 该用户不是当前步骤审批人")
        else:
            print(f"      ⚠️ 无法获取当前步骤信息")
    
    print(f"   该用户的待审批实例数: {len(user_pending_instances)}")
    
    # 2. 检查批价单审批
    print("\n💰 2. 批价单审批检查:")
    
    pending_pricing_orders = PricingOrder.query.filter_by(status='pending').all()
    print(f"   系统中待审批批价单总数: {len(pending_pricing_orders)}")
    
    user_pending_pricing = []
    for po in pending_pricing_orders:
        print(f"   批价单 {po.id}: {po.order_number}")
        print(f"      当前审批步骤: {po.current_approval_step}")
        print(f"      审批流程类型: {po.approval_flow_type}")
        
        # 检查该用户是否是当前步骤的审批人
        current_step_record = PricingOrderApprovalRecord.query.filter_by(
            pricing_order_id=po.id,
            step_order=po.current_approval_step
        ).first()
        
        if current_step_record:
            print(f"      当前步骤审批人: {current_step_record.approver_id} ({current_step_record.approver.username if current_step_record.approver else '未知'})")
            print(f"      当前步骤状态: {current_step_record.action if current_step_record.action else '待审批'}")
            
            if current_step_record.approver_id == user.id and current_step_record.action is None:
                user_pending_pricing.append(po)
                print(f"      ✅ 该用户是当前步骤审批人且待审批")
            else:
                print(f"      ❌ 该用户不是当前步骤审批人或已处理")
        else:
            print(f"      ⚠️ 找不到当前步骤的审批记录")
            
        # 检查该批价单的所有审批记录
        all_records = PricingOrderApprovalRecord.query.filter_by(
            pricing_order_id=po.id
        ).order_by(PricingOrderApprovalRecord.step_order).all()
        
        print(f"      审批记录详情:")
        for record in all_records:
            status = record.action if record.action else '待审批'
            is_current = "👉" if record.step_order == po.current_approval_step else "  "
            is_user = "🔵" if record.approver_id == user.id else "  "
            print(f"        {is_current}{is_user} 步骤{record.step_order}: {record.approver.username} - {status}")
    
    print(f"   该用户的待审批批价单数: {len(user_pending_pricing)}")
    
    # 3. 检查用户的所有批价单审批记录
    print("\n📊 3. 用户批价单审批记录统计:")
    
    user_all_records = PricingOrderApprovalRecord.query.filter_by(
        approver_id=user.id
    ).all()
    
    pending_records = [r for r in user_all_records if r.action is None]
    approved_records = [r for r in user_all_records if r.action == 'approve']
    rejected_records = [r for r in user_all_records if r.action == 'reject']
    
    print(f"   该用户的审批记录总数: {len(user_all_records)}")
    print(f"   其中待审批: {len(pending_records)}")
    print(f"   其中已通过: {len(approved_records)}")
    print(f"   其中已拒绝: {len(rejected_records)}")
    
    if pending_records:
        print(f"   待审批记录详情:")
        for record in pending_records:
            po = record.pricing_order
            is_current = "👉" if record.step_order == po.current_approval_step else "❌"
            print(f"     {is_current} 批价单 {po.id}: 步骤{record.step_order} (当前步骤: {po.current_approval_step})")
    
    # 4. 角色权限检查
    print(f"\n🔐 4. 角色权限检查 (角色: {user.role}):")
    
    if user.role == 'channel_manager':
        print("   渠道经理权限范围:")
        print("   - 渠道跟进项目")
        print("   - 有经销商的销售重点/销售机会项目")
        
        # 检查权限过滤后的批价单数量
        from app.models.project import Project
        
        filtered_query = PricingOrder.query.join(
            PricingOrderApprovalRecord,
            and_(
                PricingOrderApprovalRecord.pricing_order_id == PricingOrder.id,
                PricingOrderApprovalRecord.step_order == PricingOrder.current_approval_step
            )
        ).filter(
            PricingOrderApprovalRecord.approver_id == user.id,
            PricingOrder.status == 'pending'
        ).join(Project, PricingOrder.project_id == Project.id).filter(
            or_(
                Project.project_type.in_(['渠道跟进', 'channel_follow']),
                and_(
                    Project.project_type.in_(['销售重点', 'sales_key', '销售机会', 'sales_opportunity']),
                    PricingOrder.dealer_id.isnot(None)
                )
            )
        )
        
        filtered_count = filtered_query.count()
        print(f"   权限过滤后的待审批批价单数: {filtered_count}")
        
        if filtered_count > 0:
            print("   符合权限的批价单:")
            for po in filtered_query.all():
                project = po.project
                print(f"     批价单 {po.id}: 项目类型 {project.project_type}, 经销商 {'有' if po.dealer_id else '无'}")
    
    # 5. 最终计算
    print(f"\n🔢 5. 最终计算结果:")
    
    from app.helpers.approval_helpers import get_pending_approval_count
    final_count = get_pending_approval_count(user.id)
    
    expected_count = len(user_pending_instances) + len(user_pending_pricing)
    
    print(f"   函数返回的待审批数量: {final_count}")
    print(f"   手动计算的预期数量: {expected_count}")
    print(f"   其中通用审批: {len(user_pending_instances)}")
    print(f"   其中批价单审批: {len(user_pending_pricing)}")
    
    if final_count != expected_count:
        print(f"   ⚠️ 存在差异! 差额: {abs(final_count - expected_count)}")
    else:
        print(f"   ✅ 计算结果一致")
    
    # 6. 可能的问题分析
    print(f"\n🔍 6. 可能的问题分析:")
    
    if len(pending_instances) > 0 and len(user_pending_instances) == 0:
        print("   ⚠️ 系统中有待审批实例，但该用户不是审批人")
        print("   可能原因: 审批流程配置问题或权限设置错误")
    
    if len(pending_pricing_orders) > 0 and len(user_pending_pricing) == 0:
        print("   ⚠️ 系统中有待审批批价单，但该用户不是当前步骤审批人")
        print("   可能原因: 审批步骤不匹配或角色权限限制")
    
    if len(pending_records) > len(user_pending_pricing):
        print("   ⚠️ 该用户有未处理的审批记录，但不在当前审批步骤")
        print("   可能原因: 批价单当前步骤与记录不匹配")
    
    return {
        'user': user,
        'general_pending': len(user_pending_instances),
        'pricing_pending': len(user_pending_pricing),
        'total': final_count,
        'expected': expected_count
    }

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        print("🔍 待审批数量详细检查脚本")
        print("=" * 60)
        
        if len(sys.argv) > 1:
            username = sys.argv[1]
            detailed_check(username)
        else:
            print("请提供用户名作为参数，例如:")
            print("python 待审批详细检查.py linwengguan") 