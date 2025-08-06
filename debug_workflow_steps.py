#!/usr/bin/env python3
"""调试get_workflow_steps函数在BX2025080502上的实际执行情况"""

import sys
sys.path.append('/Users/nijie/Documents/PMA')

from app import create_app
from app.models.approval import ApprovalInstance, ApprovalStatus
from app.helpers.approval_helpers import get_workflow_steps, can_user_approve
from app.models.user import User

def debug_workflow_steps():
    """调试BX2025080502的workflow_steps函数"""
    
    app = create_app()
    
    with app.app_context():
        print("🔍 调试BX2025080502流程图显示问题")
        print("=" * 80)
        
        # 获取BX2025080502的审批实例
        approval_instance = ApprovalInstance.query.get(141)
        if not approval_instance:
            print("❌ 找不到审批实例141")
            return
        
        print(f"📋 审批实例信息:")
        print(f"  - ID: {approval_instance.id}")
        print(f"  - 当前步骤: {approval_instance.current_step}")
        print(f"  - 状态: {approval_instance.status}")
        print()
        
        # 获取gxh用户信息
        gxh_user = User.query.filter_by(username='gxh').first()
        vivian_user = User.query.filter_by(username='Vivian').first()
        
        if not gxh_user:
            print("❌ 找不到gxh用户")
            return
        if not vivian_user:
            print("❌ 找不到Vivian用户")
            return
            
        print(f"👤 用户信息:")
        print(f"  - gxh: ID={gxh_user.id}, 姓名={gxh_user.real_name}")
        print(f"  - Vivian: ID={vivian_user.id}, 姓名={vivian_user.real_name}")
        print()
        
        # 测试不同用户的can_user_approve结果
        print("🔐 权限检查:")
        gxh_can_approve = can_user_approve(approval_instance.id, gxh_user.id)
        vivian_can_approve = can_user_approve(approval_instance.id, vivian_user.id)
        
        print(f"  - gxh可以审批: {gxh_can_approve}")
        print(f"  - Vivian可以审批: {vivian_can_approve}")
        print()
        
        # 测试get_workflow_steps函数
        print("📊 流程步骤显示（gxh视角）:")
        gxh_workflow_steps = get_workflow_steps(approval_instance, gxh_user.id)
        
        for step in gxh_workflow_steps:
            status_info = []
            if step['is_completed']:
                status_info.append("✅ 已完成")
            if step['is_current']:
                status_info.append("🟡 当前步骤")
            if step['is_waiting']:
                status_info.append("🔵 等待中")
            if not any([step['is_completed'], step['is_current'], step['is_waiting']]):
                status_info.append("⚪ 未开始")
            
            status_str = " ".join(status_info)
            print(f"  步骤{step['order']}: {step['name']} ({step['approver']}) → {status_str}")
        
        print()
        print("📊 流程步骤显示（Vivian视角）:")
        vivian_workflow_steps = get_workflow_steps(approval_instance, vivian_user.id)
        
        for step in vivian_workflow_steps:
            status_info = []
            if step['is_completed']:
                status_info.append("✅ 已完成")
            if step['is_current']:
                status_info.append("🟡 当前步骤")
            if step['is_waiting']:
                status_info.append("🔵 等待中")
            if not any([step['is_completed'], step['is_current'], step['is_waiting']]):
                status_info.append("⚪ 未开始")
            
            status_str = " ".join(status_info)
            print(f"  步骤{step['order']}: {step['name']} ({step['approver']}) → {status_str}")
        
        print()
        
        # 深入分析步骤2的权限判断
        print("🔍 深入分析步骤2（财务审批）:")
        current_step_order = approval_instance.current_step
        print(f"  - 当前步骤序号: {current_step_order}")
        print(f"  - 审批实例状态: {approval_instance.status}")
        print(f"  - 步骤2是否为客观当前步骤: {2 == current_step_order and approval_instance.status == ApprovalStatus.PENDING}")
        
        return {
            'gxh_workflow_steps': gxh_workflow_steps,
            'vivian_workflow_steps': vivian_workflow_steps,
            'gxh_can_approve': gxh_can_approve,
            'vivian_can_approve': vivian_can_approve
        }

if __name__ == "__main__":
    results = debug_workflow_steps()
    
    print("\n" + "=" * 80)
    print("🎯 调试结果总结:")
    
    if results:
        print("如果gxh看到步骤2为黄色（当前步骤），说明权限检查有问题")
        print("预期结果：")
        print("  - gxh应该看到步骤2为蓝色（等待中）")
        print("  - Vivian应该看到步骤2为黄色（当前步骤）")
    else:
        print("调试过程中出现错误")
    
    print("=" * 80)