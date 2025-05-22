#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
检查审批流程模板
此脚本用于查询数据库中的审批流程模板
"""

from app import create_app
from app.models.approval import ApprovalProcessTemplate

app = create_app()

with app.app_context():
    print("===== 审批流程模板列表 =====")
    templates = ApprovalProcessTemplate.query.all()
    
    if not templates:
        print("数据库中没有审批流程模板记录，需要先创建一些模板！")
    else:
        for template in templates:
            print(f"ID: {template.id}, 名称: {template.name}, 类型: {template.object_type}, 状态: {'启用' if template.is_active else '禁用'}")

    print("\n===== 按业务类型分组 =====")
    for obj_type in ['project', 'quotation', 'customer']:
        type_templates = ApprovalProcessTemplate.query.filter_by(object_type=obj_type, is_active=True).all()
        print(f"类型 '{obj_type}' 的可用模板数量: {len(type_templates)}")
        for t in type_templates:
            print(f"  - {t.name}") 