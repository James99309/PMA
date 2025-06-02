#!/usr/bin/env python3
"""
检查报价单审批徽章状态
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.models.quotation import Quotation
from app.helpers.approval_helpers import get_object_approval_instance

def check_quotation_approval_badge():
    """检查报价单审批徽章状态"""
    
    app = create_app()
    
    with app.app_context():
        print("=== 检查报价单QU202505-006审批徽章状态 ===\n")
        
        # 1. 获取报价单
        quotation = Quotation.query.get(642)
        
        if not quotation:
            print("❌ 未找到报价单")
            return
        
        print(f"✅ 找到报价单: ID={quotation.id}, 编号={quotation.quotation_number}")
        
        # 2. 检查报价单的审批相关字段
        print(f"\n2. 报价单审批字段检查:")
        print(f"   approval_status: {quotation.approval_status}")
        print(f"   approved_stages: {quotation.approved_stages}")
        print(f"   approval_history: {quotation.approval_history}")
        
        # 3. 检查审批实例状态
        print(f"\n3. 审批实例状态:")
        approval_instance = get_object_approval_instance('quotation', 642)
        
        if approval_instance:
            print(f"   实例ID: {approval_instance.id}")
            print(f"   状态: {approval_instance.status}")
            print(f"   当前步骤: {approval_instance.current_step}")
            print(f"   开始时间: {approval_instance.started_at}")
            print(f"   结束时间: {approval_instance.ended_at}")
        else:
            print("   ❌ 未找到审批实例")
        
        # 4. 测试徽章HTML生成
        print(f"\n4. 审批徽章HTML:")
        try:
            badge_html = quotation.approval_badge_html
            print(f"   徽章HTML: {badge_html}")
            
            if badge_html and '通过' in badge_html:
                print("   ✅ 徽章显示审批通过")
            elif badge_html:
                print(f"   ⚠️ 徽章存在但内容可能不正确: {badge_html}")
            else:
                print("   ❌ 徽章为空")
        except Exception as e:
            print(f"   ❌ 生成徽章时出错: {e}")
        
        # 5. 检查项目当前阶段
        if quotation.project:
            print(f"\n5. 项目信息:")
            print(f"   项目ID: {quotation.project.id}")
            print(f"   当前阶段: {quotation.project.current_stage}")
            
            # 根据项目阶段检查应该的审批状态
            from app.models.quotation import QuotationApprovalStatus
            target_status = QuotationApprovalStatus.STAGE_TO_APPROVAL.get(quotation.project.current_stage)
            print(f"   期望审批状态: {target_status}")
            
            if quotation.approval_status == target_status:
                print("   ✅ 审批状态与项目阶段匹配")
            else:
                print(f"   ❌ 审批状态不匹配 (当前: {quotation.approval_status}, 期望: {target_status})")
        else:
            print("\n5. ❌ 报价单没有关联项目")

if __name__ == "__main__":
    check_quotation_approval_badge() 