#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
为审批流程模板添加步骤
用法: python create_approval_step.py <template_id> <step_name> <approver_id>
"""

import sys
from app import create_app
from app.models.approval import ApprovalStep
from app import db

def add_step(template_id, step_name, approver_id):
    """添加审批步骤到模板"""
    
    # 获取最大步骤序号
    max_order = db.session.query(db.func.max(ApprovalStep.step_order)).filter(
        ApprovalStep.process_id == template_id
    ).scalar() or 0
    
    # 创建新步骤
    step = ApprovalStep(
        process_id=template_id,
        step_order=max_order + 1,
        approver_user_id=approver_id,
        step_name=step_name,
        send_email=True
    )
    
    db.session.add(step)
    db.session.commit()
    
    print(f"成功添加步骤: {step_name} 到模板ID: {template_id}")
    return step

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("用法: python create_approval_step.py <template_id> <step_name> <approver_id>")
        sys.exit(1)
    
    template_id = int(sys.argv[1])
    step_name = sys.argv[2]
    approver_id = int(sys.argv[3])
    
    app = create_app()
    
    with app.app_context():
        try:
            add_step(template_id, step_name, approver_id)
            print("添加步骤成功!")
        except Exception as e:
            print(f"添加步骤失败: {str(e)}")
            sys.exit(1) 