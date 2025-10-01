#!/usr/bin/env python3
"""
调试审批实例查询问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.approval import ApprovalInstance, ApprovalStatus

def debug_approval_instance():
    """调试审批实例查询问题"""
    
    app = create_app()
    
    with app.app_context():
        print("=== 调试审批实例查询问题 ===\n")
        
        # 1. 直接查询QU202505-006的所有审批实例
        print("1. 直接查询QU202505-006的所有审批实例:")
        all_instances = ApprovalInstance.query.filter_by(
            object_type='quotation',
            object_id=642
        ).order_by(ApprovalInstance.started_at.desc()).all()
        
        print(f"找到 {len(all_instances)} 个实例:")
        for instance in all_instances:
            print(f"  - 实例ID: {instance.id}")
            print(f"    状态: {instance.status}")
            print(f"    发起时间: {instance.started_at}")
            print(f"    结束时间: {instance.ended_at or '进行中'}")
        
        # 2. 测试get_object_approval_instance函数的逻辑
        print(f"\n2. 测试get_object_approval_instance函数的逻辑:")
        
        # 模拟函数逻辑
        instance = ApprovalInstance.query.filter_by(
            object_type='quotation',
            object_id=642
        ).first()
        
        if instance:
            print(f"查询到的第一个实例: ID={instance.id}, 状态={instance.status}")
            
            if instance.status == ApprovalStatus.PENDING:
                print("✅ 状态为PENDING，应该返回此实例")
            elif instance.status == ApprovalStatus.APPROVED:
                print("✅ 状态为APPROVED，应该返回此实例")
            else:
                print("❌ 状态为其他（可能是REJECTED），函数会返回None")
        else:
            print("❌ 没有查询到任何实例")
        
        # 3. 查找最新的PENDING实例
        print(f"\n3. 查找最新的PENDING实例:")
        pending_instance = ApprovalInstance.query.filter_by(
            object_type='quotation',
            object_id=642,
            status=ApprovalStatus.PENDING
        ).order_by(ApprovalInstance.started_at.desc()).first()
        
        if pending_instance:
            print(f"✅ 找到PENDING实例: ID={pending_instance.id}")
            print(f"   发起时间: {pending_instance.started_at}")
            print(f"   当前步骤: {pending_instance.current_step}")
        else:
            print("❌ 没有找到PENDING实例")
        
        # 4. 查找最新的实例（不限状态）
        print(f"\n4. 查找最新的实例（不限状态）:")
        latest_instance = ApprovalInstance.query.filter_by(
            object_type='quotation',
            object_id=642
        ).order_by(ApprovalInstance.started_at.desc()).first()
        
        if latest_instance:
            print(f"✅ 最新实例: ID={latest_instance.id}")
            print(f"   状态: {latest_instance.status}")
            print(f"   发起时间: {latest_instance.started_at}")
            print(f"   当前步骤: {latest_instance.current_step}")
        else:
            print("❌ 没有找到任何实例")

if __name__ == "__main__":
    debug_approval_instance() 