#!/usr/bin/env python3
"""
检查实例ID 37的详细信息（修复版）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.approval import ApprovalInstance
from app.helpers.approval_helpers import (
    get_object_approval_instance,
    get_current_step_info,
    get_workflow_steps,
    can_user_approve
)

def check_quotation_approval_fixed():
    """检查QU202505-006报价单的审批状态（修复版）"""
    
    app = create_app()
    
    with app.app_context():
        print("=== QU202505-006 报价单审批状态检查（修复版） ===\n")
        
        # 1. 使用正确的方式获取审批实例
        approval_instance = get_object_approval_instance('quotation', 642)
        if not approval_instance:
            print("❌ 未找到审批实例")
            return
        
        print(f"✅ 找到审批实例:")
        print(f"   实例ID: {approval_instance.id}")
        print(f"   流程名称: {approval_instance.process.name if approval_instance.process else '未知'}")
        print(f"   发起人: {approval_instance.creator.username if approval_instance.creator else '未知'}")
        print(f"   发起时间: {approval_instance.started_at}")
        print(f"   当前状态: {approval_instance.status}")
        print(f"   当前步骤: {approval_instance.current_step}")
        
        # 2. 检查当前步骤信息
        current_step = get_current_step_info(approval_instance)
        if current_step:
            print(f"\n✅ 当前步骤信息:")
            print(f"   步骤名称: {current_step.step_name}")
            print(f"   审批人: {current_step.approver.username if current_step.approver else '未知'}")
            print(f"   审批人姓名: {current_step.approver.real_name if current_step.approver and current_step.approver.real_name else '未设置'}")
            print(f"   步骤顺序: {current_step.step_order}")
        else:
            print("\n❌ 未找到当前步骤信息")
        
        # 3. 检查审批流程步骤
        workflow_steps = get_workflow_steps(approval_instance)
        if workflow_steps:
            print(f"\n✅ 审批流程步骤 (共{len(workflow_steps)}步):")
            for step in workflow_steps:
                status_icon = "✅" if step['is_completed'] else ("⏳" if step['is_current'] else "⭕")
                print(f"   {status_icon} 步骤{step['order']}: {step['name']}")
                print(f"      审批人: {step['approver']}")
                if step['is_completed']:
                    print(f"      审批结果: {step['action']}")
                    print(f"      审批时间: {step['timestamp']}")
                    if step['comment']:
                        print(f"      审批意见: {step['comment']}")
                elif step['is_current']:
                    print(f"      状态: 待审批")
        else:
            print("\n❌ 未找到审批流程步骤")
        
        # 4. 检查NIJIE用户的审批权限（使用正确的用户名）
        from app.models.user import User
        nijie_user = User.query.filter_by(username='NIJIE').first()  # 使用大写的NIJIE
        if nijie_user:
            can_approve = can_user_approve(approval_instance.id, nijie_user.id)
            print(f"\n✅ NIJIE用户审批权限检查:")
            print(f"   用户ID: {nijie_user.id}")
            print(f"   用户名: {nijie_user.username}")
            print(f"   真实姓名: {nijie_user.real_name or '未设置'}")
            print(f"   角色: {nijie_user.role}")
            print(f"   可以审批: {'是' if can_approve else '否'}")
            
            if current_step and current_step.approver:
                is_current_approver = current_step.approver.id == nijie_user.id
                print(f"   是当前审批人: {'是' if is_current_approver else '否'}")
        else:
            print("\n❌ 未找到NIJIE用户")
        
        # 5. 检查模板快照中的步骤信息
        if hasattr(approval_instance, 'template_snapshot') and approval_instance.template_snapshot:
            print(f"\n✅ 模板快照步骤信息:")
            snapshot = approval_instance.template_snapshot
            steps = snapshot.get('steps', [])
            for step in steps:
                print(f"   步骤{step.get('step_order')}: {step.get('step_name')}")
                print(f"     审批人ID: {step.get('approver_user_id')}")
                print(f"     审批人用户名: {step.get('approver_username')}")
                print(f"     审批人姓名: {step.get('approver_real_name')}")

if __name__ == "__main__":
    check_quotation_approval_fixed() 