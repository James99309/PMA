#!/usr/bin/env python3
"""
修复报价单QU202505-006的审批状态
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.quotation import Quotation, QuotationApprovalStatus
from app.models.approval import ApprovalInstance, ApprovalStatus
from app.helpers.approval_helpers import get_object_approval_instance
from datetime import datetime

def fix_quotation_approval_status():
    """修复报价单审批状态"""
    
    app = create_app()
    
    with app.app_context():
        print("=== 修复报价单QU202505-006审批状态 ===\n")
        
        # 1. 获取报价单
        quotation = Quotation.query.get(642)
        
        if not quotation:
            print("❌ 未找到报价单")
            return
        
        print(f"✅ 找到报价单: ID={quotation.id}, 编号={quotation.quotation_number}")
        
        # 2. 获取审批实例
        approval_instance = get_object_approval_instance('quotation', 642)
        
        if not approval_instance:
            print("❌ 未找到审批实例")
            return
        
        print(f"✅ 找到审批实例: ID={approval_instance.id}, 状态={approval_instance.status}")
        
        # 3. 检查审批实例是否已完成
        if approval_instance.status != ApprovalStatus.APPROVED:
            print(f"❌ 审批实例状态不是APPROVED: {approval_instance.status}")
            return
        
        # 4. 获取项目阶段信息
        if not quotation.project:
            print("❌ 报价单没有关联项目")
            return
        
        project_stage = quotation.project.current_stage
        target_approval_status = QuotationApprovalStatus.STAGE_TO_APPROVAL.get(project_stage)
        
        print(f"✅ 项目阶段: {project_stage}")
        print(f"✅ 目标审批状态: {target_approval_status}")
        
        # 5. 更新报价单审批状态
        try:
            # 更新审批状态
            quotation.approval_status = target_approval_status
            
            # 添加到已审核阶段列表
            if not quotation.approved_stages:
                quotation.approved_stages = []
            if target_approval_status not in quotation.approved_stages:
                quotation.approved_stages.append(target_approval_status)
            
            # 添加审核历史
            if not quotation.approval_history:
                quotation.approval_history = []
            
            # 从审批记录中获取审批人信息
            from app.models.approval import ApprovalRecord
            from app.models.user import User
            
            approval_records = ApprovalRecord.query.filter_by(instance_id=approval_instance.id).all()
            approver_name = '未知'
            approval_comment = ''
            
            if approval_records:
                last_record = approval_records[-1]  # 最后一条记录
                approver = User.query.get(last_record.approver_id) if last_record.approver_id else None
                approver_name = approver.username if approver else '未知'
                approval_comment = last_record.comment or ''
            
            quotation.approval_history.append({
                'action': 'approve',
                'stage': project_stage,
                'approval_status': target_approval_status,
                'approver_id': approval_records[-1].approver_id if approval_records else None,
                'approver_name': approver_name,
                'comment': approval_comment,
                'timestamp': approval_instance.ended_at.isoformat() if approval_instance.ended_at else datetime.now().isoformat(),
                'approval_instance_id': approval_instance.id
            })
            
            # 保存更改
            db.session.commit()
            
            print("✅ 报价单审批状态已成功更新!")
            print(f"   新的审批状态: {quotation.approval_status}")
            print(f"   已审核阶段: {quotation.approved_stages}")
            print(f"   审核历史记录数: {len(quotation.approval_history)}")
            
            # 6. 验证徽章
            print(f"\n6. 验证审批徽章:")
            badge_html = quotation.approval_badge_html
            print(f"   徽章HTML: {badge_html}")
            
            if badge_html and '通过' in badge_html:
                print("   ✅ 徽章显示正常")
            else:
                print("   ⚠️ 徽章可能有问题")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ 更新报价单审批状态失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    fix_quotation_approval_status() 