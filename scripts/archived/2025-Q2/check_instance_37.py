#!/usr/bin/env python3
"""
检查实例ID 37的详细信息
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.approval import ApprovalInstance, ApprovalStep, ApprovalRecord
from app.helpers.approval_helpers import (
    get_current_step_info,
    get_workflow_steps,
    can_user_approve
)

def check_instance_37():
    """检查实例ID 37的详细信息"""
    
    app = create_app()
    
    with app.app_context():
        print("=== 实例ID 37 详细检查 ===\n")
        
        # 1. 获取审批实例
        instance = ApprovalInstance.query.get(37)
        if not instance:
            print("❌ 未找到实例ID 37")
            return
        
        print(f"✅ 找到审批实例:")
        print(f"   实例ID: {instance.id}")
        print(f"   对象类型: {instance.object_type}")
        print(f"   对象ID: {instance.object_id}")
        print(f"   流程模板ID: {instance.process_id}")
        print(f"   流程名称: {instance.process.name if instance.process else '未知'}")
        print(f"   发起人: {instance.creator.username if instance.creator else '未知'}")
        print(f"   发起时间: {instance.started_at}")
        print(f"   当前状态: {instance.status}")
        print(f"   当前步骤: {instance.current_step}")
        
        # 2. 检查模板快照
        if hasattr(instance, 'template_snapshot') and instance.template_snapshot:
            print(f"\n✅ 模板快照信息:")
            snapshot = instance.template_snapshot
            print(f"   模板名称: {snapshot.get('template_name', '未知')}")
            print(f"   模板版本: {instance.template_version or '未设置'}")
            print(f"   快照步骤数: {len(snapshot.get('steps', []))}")
            
            # 显示快照中的步骤
            steps = snapshot.get('steps', [])
            if steps:
                print(f"\n   快照步骤详情:")
                for i, step in enumerate(steps, 1):
                    print(f"     步骤{step.get('step_order', i)}: {step.get('step_name', '未知')}")
                    print(f"       审批人ID: {step.get('approver_user_id', '未知')}")
                    print(f"       审批人用户名: {step.get('approver_username', '未知')}")
                    print(f"       审批人姓名: {step.get('approver_real_name', '未设置')}")
        else:
            print(f"\n⚠️  无模板快照，使用当前模板配置")
        
        # 3. 检查当前步骤信息
        current_step = get_current_step_info(instance)
        if current_step:
            print(f"\n✅ 当前步骤信息:")
            print(f"   步骤ID: {current_step.id}")
            print(f"   步骤名称: {current_step.step_name}")
            print(f"   步骤顺序: {current_step.step_order}")
            print(f"   审批人ID: {current_step.approver_user_id}")
            print(f"   审批人: {current_step.approver.username if current_step.approver else '未知'}")
            print(f"   审批人姓名: {current_step.approver.real_name if current_step.approver and current_step.approver.real_name else '未设置'}")
        else:
            print(f"\n❌ 未找到当前步骤信息")
        
        # 4. 检查审批流程步骤
        workflow_steps = get_workflow_steps(instance)
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
            print(f"\n❌ 未找到审批流程步骤")
        
        # 5. 检查审批记录
        records = ApprovalRecord.query.filter_by(instance_id=instance.id).all()
        if records:
            print(f"\n✅ 审批记录 (共{len(records)}条):")
            for record in records:
                print(f"   - 审批人: {record.approver.username if record.approver else '未知'}")
                print(f"     审批动作: {record.action}")
                print(f"     审批时间: {record.timestamp}")
                print(f"     审批意见: {record.comment or '无'}")
        else:
            print(f"\n⚠️  暂无审批记录")
        
        # 6. 检查NIJIE用户的审批权限
        from app.models.user import User
        nijie_user = User.query.filter_by(username='nijie').first()
        if nijie_user:
            can_approve = can_user_approve(instance.id, nijie_user.id)
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
            print(f"\n❌ 未找到NIJIE用户")

if __name__ == "__main__":
    check_instance_37() 