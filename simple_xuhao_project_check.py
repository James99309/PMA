#!/usr/bin/env python3
"""
简化检查xuhao审批项目类型
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
        xuhao = User.query.filter_by(username='xuhao').first()
        if not xuhao:
            print("❌ 未找到xuhao用户")
            return
        
        print(f"xuhao用户ID: {xuhao.id}, 角色: {xuhao.role}")
        
        # 查找待审批实例
        pending_instances = ApprovalInstance.query.filter_by(status=ApprovalStatus.PENDING).all()
        print(f"总待审批实例: {len(pending_instances)}")
        
        xuhao_approvals = []
        for instance in pending_instances:
            current_step = instance.get_current_step_info()
            if current_step:
                approver_id = current_step.get('approver_user_id') if isinstance(current_step, dict) else current_step.approver_user_id
                if approver_id == xuhao.id:
                    xuhao_approvals.append(instance)
        
        print(f"xuhao需要审批的数量: {len(xuhao_approvals)}")
        
        for instance in xuhao_approvals:
            if instance.object_type == 'project':
                project = Project.query.get(instance.object_id)
                if project:
                    print(f"项目ID: {project.id}, 名称: {project.project_name}, 类型: {project.project_type}")
        
        # 检查系统中的项目类型
        print("\n所有项目类型:")
        project_types = Project.query.with_entities(Project.project_type).distinct().all()
        for pt in project_types:
            if pt[0]:  # 过滤None值
                count = Project.query.filter_by(project_type=pt[0]).count()
                print(f"  {pt[0]}: {count}个")

if __name__ == '__main__':
    main() 