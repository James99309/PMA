#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
创建审批流程模板
此脚本用于向数据库中添加示例审批流程模板
"""

from app import create_app
from app.models.approval import ApprovalProcessTemplate
from app.models.user import User
from app import db
from datetime import datetime

app = create_app()

with app.app_context():
    # 获取管理员用户ID
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        print("找不到管理员用户，无法创建模板")
        exit(1)
    
    creator_id = admin.id
    
    # 添加报价单审批模板
    quotation_template = ApprovalProcessTemplate(
        name="报价单审批流程",
        object_type="quotation",
        is_active=True,
        created_by=creator_id,
        created_at=datetime.now()
    )
    
    # 添加客户信息审批模板
    customer_template = ApprovalProcessTemplate(
        name="客户信息审批流程",
        object_type="customer",
        is_active=True,
        created_by=creator_id,
        created_at=datetime.now()
    )
    
    # 添加项目变更审批模板（另一个项目审批模板）
    project_change_template = ApprovalProcessTemplate(
        name="项目变更审批流程",
        object_type="project",
        is_active=True,
        created_by=creator_id,
        created_at=datetime.now()
    )
    
    # 保存到数据库
    try:
        db.session.add(quotation_template)
        db.session.add(customer_template)
        db.session.add(project_change_template)
        db.session.commit()
        print("成功创建3个审批流程模板！")
    except Exception as e:
        db.session.rollback()
        print(f"创建模板失败: {str(e)}") 