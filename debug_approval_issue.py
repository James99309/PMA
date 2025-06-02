#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
审批流程问题诊断脚本
检查项目审批流程无法发起的具体原因
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models.project import Project
from app.models.approval import ApprovalInstance, ApprovalProcessTemplate, ApprovalStatus
from app.helpers.approval_helpers import get_object_approval_instance, start_approval_process
from flask_login import login_user
from app.models.user import User

app = create_app()

def check_approval_issue():
    """检查审批流程问题"""
    with app.app_context():
        print("=== 审批流程问题诊断 ===\n")
        
        # 1. 检查项目
        projects = Project.query.order_by(Project.id.desc()).limit(5).all()
        print(f"最近的5个项目:")
        for project in projects:
            print(f"  ID: {project.id}, 名称: {project.project_name}, 创建时间: {project.created_at}")
        
        if not projects:
            print("  没有找到任何项目")
            return
        
        # 选择第一个项目进行测试
        test_project = projects[0]
        print(f"\n使用项目进行测试: ID={test_project.id}, 名称='{test_project.project_name}'")
        
        # 2. 检查该项目是否有现有的审批实例
        print(f"\n=== 检查项目 {test_project.id} 的审批实例 ===")
        existing_instances = ApprovalInstance.query.filter_by(
            object_type='project',
            object_id=test_project.id
        ).all()
        
        if existing_instances:
            print(f"发现 {len(existing_instances)} 个审批实例:")
            for instance in existing_instances:
                status_text = {
                    ApprovalStatus.PENDING: "审批中",
                    ApprovalStatus.APPROVED: "已通过", 
                    ApprovalStatus.REJECTED: "已拒绝"
                }.get(instance.status, str(instance.status))
                
                template_name = instance.process.name if instance.process else "未知模板"
                
                print(f"  实例ID: {instance.id}")
                print(f"  状态: {status_text}")
                print(f"  模板: {template_name}")
                print(f"  发起时间: {instance.started_at}")
                if instance.ended_at:
                    print(f"  结束时间: {instance.ended_at}")
                print()
        else:
            print("该项目没有审批实例")
        
        # 3. 检查审批模板
        print(f"\n=== 检查项目类型的审批模板 ===")
        templates = ApprovalProcessTemplate.query.filter_by(
            object_type='project',
            is_active=True
        ).all()
        
        if templates:
            print(f"找到 {len(templates)} 个有效的项目审批模板:")
            for template in templates:
                print(f"  ID: {template.id}, 名称: {template.name}")
                print(f"  必填字段: {template.required_fields}")
                print(f"  创建人: {template.created_by}")
                print()
        else:
            print("没有找到有效的项目审批模板")
            return
        
        # 4. 使用 get_object_approval_instance 函数检查
        print(f"\n=== 使用 get_object_approval_instance 检查 ===")
        approval_instance = get_object_approval_instance('project', test_project.id)
        if approval_instance:
            status_text = {
                ApprovalStatus.PENDING: "审批中",
                ApprovalStatus.APPROVED: "已通过", 
                ApprovalStatus.REJECTED: "已拒绝"
            }.get(approval_instance.status, str(approval_instance.status))
            
            print(f"函数返回实例: ID={approval_instance.id}, 状态={status_text}")
            print("这解释了为什么无法发起新的审批流程")
        else:
            print("函数返回 None，理论上可以发起新的审批流程")
        
        # 5. 测试发起审批流程（如果没有现有实例）
        if not approval_instance and templates:
            print(f"\n=== 测试发起审批流程 ===")
            
            # 模拟登录用户
            user = User.query.filter_by(username='admin').first()
            if not user:
                print("找不到admin用户，无法测试")
                return
            
            print(f"使用用户: {user.username} (ID: {user.id})")
            
            template = templates[0]
            print(f"使用模板: {template.name} (ID: {template.id})")
            
            try:
                instance = start_approval_process(
                    object_type='project',
                    object_id=test_project.id,
                    template_id=template.id,
                    user_id=user.id
                )
                
                if instance:
                    print(f"成功创建审批实例: ID={instance.id}")
                    # 立即删除测试实例
                    db.session.delete(instance)
                    db.session.commit()
                    print("测试实例已删除")
                else:
                    print("创建审批实例失败")
            except Exception as e:
                print(f"发起审批流程时出错: {str(e)}")
                import traceback
                traceback.print_exc()
        
        print(f"\n=== 诊断完成 ===")

if __name__ == '__main__':
    check_approval_issue() 