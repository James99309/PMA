#!/usr/bin/env python3
"""
检查gxh用户的审批问题
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
from app.models.project import Project

def main():
    app = create_app()
    
    with app.app_context():
        print("=== 检查gxh用户的审批问题 ===")
        
        gxh = User.query.filter_by(username='gxh').first()
        if not gxh:
            print("❌ 未找到gxh用户")
            return
        
        print(f"用户: {gxh.username} ({gxh.real_name}) - 角色: {gxh.role}")
        
        # 查找应该由gxh审批的所有记录
        pending_instances = ApprovalInstance.query.filter_by(status=ApprovalStatus.PENDING).all()
        print(f"总共的待审批实例数量: {len(pending_instances)}")
        
        gxh_should_approve = []
        for instance in pending_instances:
            current_step_info = instance.get_current_step_info()
            if current_step_info:
                current_approver_id = None
                
                if isinstance(current_step_info, dict):  # 快照数据
                    current_approver_id = current_step_info.get('approver_user_id')
                else:  # 模板步骤对象
                    current_approver_id = current_step_info.approver_user_id
                
                if current_approver_id == gxh.id:
                    gxh_should_approve.append(instance)
        
        print(f"应该由gxh审批的实例数量: {len(gxh_should_approve)}")
        
        # 分析这些项目的类型
        project_types = {}
        for instance in gxh_should_approve:
            if instance.object_type == 'project':
                project = Project.query.get(instance.object_id)
                if project:
                    project_type = project.project_type
                    if project_type not in project_types:
                        project_types[project_type] = []
                    project_types[project_type].append(instance.id)
        
        print(f"\n项目类型分布:")
        for project_type, instance_ids in project_types.items():
            print(f"  {project_type}: {len(instance_ids)}个 - {instance_ids}")
        
        # sales_director应该能看到的项目类型
        allowed_types = ['销售重点', 'sales_key', 'sales_focus', '渠道跟进', 'channel_follow']
        print(f"\nsales_director角色允许的项目类型: {allowed_types}")
        
        allowed_count = 0
        not_allowed_count = 0
        
        for project_type, instance_ids in project_types.items():
            if project_type in allowed_types:
                allowed_count += len(instance_ids)
                print(f"  ✅ {project_type}: {len(instance_ids)}个（允许）")
            else:
                not_allowed_count += len(instance_ids)
                print(f"  ❌ {project_type}: {len(instance_ids)}个（不允许）")
        
        print(f"\n总结:")
        print(f"  应该审批的总数: {len(gxh_should_approve)}")
        print(f"  权限允许的数量: {allowed_count}")
        print(f"  权限不允许的数量: {not_allowed_count}")
        
        if not_allowed_count > 0:
            print(f"\n🎯 问题发现: gxh有{not_allowed_count}个不符合sales_director权限的审批记录被过滤掉了")

if __name__ == '__main__':
    main() 