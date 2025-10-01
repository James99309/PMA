#!/usr/bin/env python3
"""
检查所有service_manager用户的审批问题
"""

import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from flask import Flask
from app import create_app
from app.models.user import User
from app.models.approval import ApprovalInstance, ApprovalStatus
from app.helpers.approval_helpers import get_user_pending_approvals, get_pending_approval_count

def main():
    app = create_app()
    
    with app.app_context():
        print("=== 检查所有service_manager用户的审批问题 ===")
        
        # 查找所有service_manager角色的用户
        service_managers = User.query.filter_by(role='service_manager').all()
        print(f"找到 {len(service_managers)} 个service_manager用户:")
        
        for user in service_managers:
            print(f"\n用户: {user.username} ({user.real_name}) - 部门: {user.department}")
            
            # 检查待审批数量
            try:
                pending_count = get_pending_approval_count(user_id=user.id)
                pending_approvals = get_user_pending_approvals(user_id=user.id)
                approval_count = pending_approvals.total if hasattr(pending_approvals, 'total') else 0
                
                print(f"  get_pending_approval_count: {pending_count}")
                print(f"  get_user_pending_approvals: {approval_count}")
                
                if pending_count != approval_count:
                    print(f"  ❌ 数量不一致，可能有问题")
                elif pending_count > 0:
                    print(f"  ✅ 有{pending_count}个待审批，正常")
                else:
                    print(f"  ℹ️  无待审批记录")
                    
            except Exception as e:
                print(f"  ⚠️ 检查时出错: {str(e)}")
        
        # 检查所有其他角色的用户
        print("\n=== 检查其他角色用户（抽样检查）===")
        other_roles = ['admin', 'business_admin', 'channel_manager', 'sales_director']
        
        for role in other_roles:
            users = User.query.filter_by(role=role).limit(2).all()  # 每个角色检查前2个用户
            
            if users:
                print(f"\n{role}角色用户:")
                for user in users:
                    try:
                        pending_count = get_pending_approval_count(user_id=user.id)
                        pending_approvals = get_user_pending_approvals(user_id=user.id)
                        approval_count = pending_approvals.total if hasattr(pending_approvals, 'total') else 0
                        
                        print(f"  {user.username}: count={pending_count}, approvals={approval_count}", end="")
                        if pending_count != approval_count:
                            print(" ❌ 不一致")
                        else:
                            print(" ✅")
                    except Exception as e:
                        print(f"  {user.username}: ⚠️ 出错: {str(e)}")

if __name__ == '__main__':
    main() 