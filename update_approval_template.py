#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
更新审批流程模板状态
用法: python update_approval_template.py <template_id> <is_active>
"""

import sys
from app import create_app
from app.models.approval import ApprovalProcessTemplate
from app import db

def update_template(template_id, is_active):
    """更新审批模板启用状态"""
    template = ApprovalProcessTemplate.query.get(template_id)
    if not template:
        print(f"模板ID:{template_id}不存在")
        return False
    
    template.is_active = is_active
    db.session.commit()
    
    status = "启用" if is_active else "禁用"
    print(f"模板 '{template.name}' 状态已更新为: {status}")
    return True

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python update_approval_template.py <template_id> <is_active>")
        print("示例: python update_approval_template.py 1 true")
        sys.exit(1)
    
    template_id = int(sys.argv[1])
    is_active = sys.argv[2].lower() in ('true', 'yes', '1', 'y', 't')
    
    app = create_app()
    
    with app.app_context():
        try:
            update_template(template_id, is_active)
        except Exception as e:
            print(f"更新模板失败: {str(e)}")
            sys.exit(1) 