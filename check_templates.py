#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查项目审批模板
"""

from app import create_app
from app.helpers.approval_helpers import get_available_templates
from app.models.approval import ApprovalProcessTemplate, ApprovalStep

def check_templates():
    app = create_app()
    with app.app_context():
        # 检查项目可用模板
        templates = get_available_templates('project')
        print(f'项目可用模板数量: {len(templates)}')
        for t in templates:
            print(f'模板: {t.id} - {t.name} (活跃: {t.is_active})')
            
            # 检查模板的审批步骤
            steps = ApprovalStep.query.filter_by(process_id=t.id).order_by(ApprovalStep.step_order).all()
            print(f'  步骤数量: {len(steps)}')
            for step in steps:
                print(f'  - 步骤 {step.step_order}: {step.step_name} (审批人ID: {step.approver_user_id})')
                
        # 检查所有模板
        all_templates = ApprovalProcessTemplate.query.all()
        print(f'\n所有模板数量: {len(all_templates)}')
        for t in all_templates:
            print(f'模板: {t.id} - {t.name} (活跃: {t.is_active}) (类型: {t.object_type})')
            
            # 检查模板的审批步骤
            steps = ApprovalStep.query.filter_by(process_id=t.id).order_by(ApprovalStep.step_order).all()
            print(f'  步骤数量: {len(steps)}')

if __name__ == "__main__":
    check_templates()
