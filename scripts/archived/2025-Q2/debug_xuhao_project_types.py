#!/usr/bin/env python3
"""
检查需要xuhao审批的项目的具体类型
"""

import os
import sys

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from flask import Flask
from app import create_app, db
from app.models.user import User
from app.models.approval import ApprovalInstance, ApprovalStatus
from app.models.project import Project

def main():
    """主函数"""
    print("=== 检查需要xuhao审批的项目类型 ===")
    
    app = create_app()
    
    with app.app_context():
        # 找到xuhao用户
        xuhao = User.query.filter_by(username='xuhao').first()
        if not xuhao:
            print("❌ 未找到xuhao用户")
            return
        
        xuhao_id = xuhao.id
        print(f"xuhao用户ID: {xuhao_id}")
        
        # 查找所有状态为pending的审批实例
        pending_instances = ApprovalInstance.query.filter_by(status=ApprovalStatus.PENDING).all()
        print(f"总共的待审批实例数量: {len(pending_instances)}")
        
        xuhao_should_approve = []
        
        for instance in pending_instances:
            current_step_info = instance.get_current_step_info()
            if current_step_info:
                current_approver_id = None
                
                if isinstance(current_step_info, dict):  # 快照数据
                    current_approver_id = current_step_info.get('approver_user_id')
                else:  # 模板步骤对象
                    current_approver_id = current_step_info.approver_user_id
                
                if current_approver_id == xuhao_id:
                    xuhao_should_approve.append(instance)
        
        print(f"应该由xuhao审批的实例数量: {len(xuhao_should_approve)}")
        
        if xuhao_should_approve:
            print("\n需要xuhao审批的记录详情:")
            for instance in xuhao_should_approve:
                print(f"  审批ID: {instance.id} (APV-{instance.id:04d})")
                print(f"    对象类型: {instance.object_type}")
                print(f"    对象ID: {instance.object_id}")
                print(f"    状态: {instance.status}")
                print(f"    当前步骤: {instance.current_step}")
                
                # 获取关联的业务对象信息
                if instance.object_type == 'project':
                    project = Project.query.get(instance.object_id)
                    if project:
                        # 使用正确的属性名
                        project_name = getattr(project, 'project_name', getattr(project, 'name', '未知'))
                        print(f"    项目名称: {project_name}")
                        print(f"    项目类型: {project.project_type}")
                        print(f"    创建者ID: {project.created_by}")
                        if hasattr(project, 'creator') and project.creator:
                            print(f"    创建者: {project.creator.real_name}")
                        
                        # 检查项目类型是否在允许的范围内
                        allowed_types = ['销售机会', 'sales_opportunity']
                        if project.project_type in allowed_types:
                            print(f"    ✅ 项目类型匹配service_manager权限")
                        else:
                            print(f"    ❌ 项目类型不匹配service_manager权限 (仅允许: {allowed_types})")
                    else:
                        print(f"    ⚠️ 关联项目不存在")
                print()
        
        # 检查系统中所有项目类型
        print("\n=== 系统中所有项目类型统计 ===")
        all_project_types = db.session.query(Project.project_type).distinct().all()
        for project_type_tuple in all_project_types:
            project_type = project_type_tuple[0]
            count = Project.query.filter_by(project_type=project_type).count()
            print(f"  {project_type}: {count}个项目")

if __name__ == '__main__':
    main() 