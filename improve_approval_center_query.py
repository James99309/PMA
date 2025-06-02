#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进审批中心查询逻辑
通过JOIN查询确保只显示关联业务对象存在的审批实例
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def generate_improved_query_functions():
    """生成改进的查询函数代码"""
    
    improved_code = '''
# 改进后的审批查询函数 - 替换 app/helpers/approval_helpers.py 中的函数

from sqlalchemy import and_, or_, desc, asc
from app.models.project import Project
from app.models.quotation import Quotation  
from app.models.customer import Company

def get_user_created_approvals(user_id=None, object_type=None, status=None, page=1, per_page=20):
    """获取指定用户发起的审批列表 - 改进版，只返回关联业务对象存在的审批
    
    Args:
        user_id: 用户ID，默认为当前登录用户
        object_type: 过滤特定类型的审批对象
        status: 过滤特定状态的审批
        page: 页码
        per_page: 每页数量
        
    Returns:
        分页对象，包含审批实例列表
    """
    if user_id is None:
        user_id = current_user.id
    
    # 基础查询
    query = ApprovalInstance.query.options(db.joinedload(ApprovalInstance.process)).filter(
        ApprovalInstance.created_by == user_id
    )
    
    # 根据业务对象类型添加JOIN条件，确保业务对象存在
    if object_type == 'project':
        query = query.join(Project, ApprovalInstance.object_id == Project.id).filter(
            ApprovalInstance.object_type == 'project'
        )
    elif object_type == 'quotation':
        query = query.join(Quotation, ApprovalInstance.object_id == Quotation.id).filter(
            ApprovalInstance.object_type == 'quotation'
        )
    elif object_type == 'customer':
        query = query.join(Company, ApprovalInstance.object_id == Company.id).filter(
            ApprovalInstance.object_type == 'customer'
        )
    else:
        # 如果没有指定类型，使用复杂的联合查询确保所有业务对象都存在
        project_subquery = db.session.query(ApprovalInstance.id).filter(
            ApprovalInstance.object_type == 'project'
        ).join(Project, ApprovalInstance.object_id == Project.id).subquery()
        
        quotation_subquery = db.session.query(ApprovalInstance.id).filter(
            ApprovalInstance.object_type == 'quotation'
        ).join(Quotation, ApprovalInstance.object_id == Quotation.id).subquery()
        
        customer_subquery = db.session.query(ApprovalInstance.id).filter(
            ApprovalInstance.object_type == 'customer'
        ).join(Company, ApprovalInstance.object_id == Company.id).subquery()
        
        # 只查询存在于任一子查询中的审批实例
        query = query.filter(
            or_(
                ApprovalInstance.id.in_(project_subquery),
                ApprovalInstance.id.in_(quotation_subquery),
                ApprovalInstance.id.in_(customer_subquery)
            )
        )
    
    if status:
        query = query.filter(ApprovalInstance.status == status)
    
    # 按创建时间倒序排列
    query = query.order_by(ApprovalInstance.started_at.desc())
    
    # 返回分页结果
    return query.paginate(page=page, per_page=per_page, error_out=False)


def get_user_pending_approvals(user_id=None, object_type=None, page=1, per_page=20):
    """获取待用户审批的列表 - 改进版，只返回关联业务对象存在的审批
    
    Args:
        user_id: 用户ID，默认为当前登录用户
        object_type: 过滤特定类型的审批对象
        page: 页码
        per_page: 每页数量
        
    Returns:
        分页对象，包含待该用户审批的审批实例列表
    """
    if user_id is None:
        user_id = current_user.id
    
    # 基础查询：找出当前用户是审批人且处于当前审批步骤的所有实例
    query = ApprovalInstance.query.options(db.joinedload(ApprovalInstance.process)).join(
        ApprovalStep, 
        and_(
            ApprovalStep.process_id == ApprovalInstance.process_id,
            ApprovalStep.step_order == ApprovalInstance.current_step
        )
    ).filter(
        ApprovalStep.approver_user_id == user_id,
        ApprovalInstance.status == ApprovalStatus.PENDING
    )
    
    # 根据业务对象类型添加JOIN条件，确保业务对象存在
    if object_type == 'project':
        query = query.join(Project, ApprovalInstance.object_id == Project.id).filter(
            ApprovalInstance.object_type == 'project'
        )
    elif object_type == 'quotation':
        query = query.join(Quotation, ApprovalInstance.object_id == Quotation.id).filter(
            ApprovalInstance.object_type == 'quotation'
        )
    elif object_type == 'customer':
        query = query.join(Company, ApprovalInstance.object_id == Company.id).filter(
            ApprovalInstance.object_type == 'customer'
        )
    else:
        # 如果没有指定类型，使用复杂的联合查询确保所有业务对象都存在
        project_subquery = db.session.query(ApprovalInstance.id).filter(
            ApprovalInstance.object_type == 'project'
        ).join(Project, ApprovalInstance.object_id == Project.id).subquery()
        
        quotation_subquery = db.session.query(ApprovalInstance.id).filter(
            ApprovalInstance.object_type == 'quotation'
        ).join(Quotation, ApprovalInstance.object_id == Quotation.id).subquery()
        
        customer_subquery = db.session.query(ApprovalInstance.id).filter(
            ApprovalInstance.object_type == 'customer'
        ).join(Company, ApprovalInstance.object_id == Company.id).subquery()
        
        # 只查询存在于任一子查询中的审批实例
        query = query.filter(
            or_(
                ApprovalInstance.id.in_(project_subquery),
                ApprovalInstance.id.in_(quotation_subquery),
                ApprovalInstance.id.in_(customer_subquery)
            )
        )
    
    # 按创建时间倒序排列
    query = query.order_by(ApprovalInstance.started_at.desc())
    
    # 返回分页结果
    return query.paginate(page=page, per_page=per_page, error_out=False)


def get_all_approvals(object_type=None, status=None, page=1, per_page=20):
    """获取所有审批记录（仅供admin使用）- 改进版，只返回关联业务对象存在的审批
    
    Args:
        object_type: 过滤特定类型的审批对象
        status: 过滤特定状态的审批
        page: 页码
        per_page: 每页数量
        
    Returns:
        分页对象，包含所有审批实例列表
    """
    query = ApprovalInstance.query.options(db.joinedload(ApprovalInstance.process))
    
    # 根据业务对象类型添加JOIN条件，确保业务对象存在
    if object_type == 'project':
        query = query.join(Project, ApprovalInstance.object_id == Project.id).filter(
            ApprovalInstance.object_type == 'project'
        )
    elif object_type == 'quotation':
        query = query.join(Quotation, ApprovalInstance.object_id == Quotation.id).filter(
            ApprovalInstance.object_type == 'quotation'
        )
    elif object_type == 'customer':
        query = query.join(Company, ApprovalInstance.object_id == Company.id).filter(
            ApprovalInstance.object_type == 'customer'
        )
    else:
        # 如果没有指定类型，使用复杂的联合查询确保所有业务对象都存在
        project_subquery = db.session.query(ApprovalInstance.id).filter(
            ApprovalInstance.object_type == 'project'
        ).join(Project, ApprovalInstance.object_id == Project.id).subquery()
        
        quotation_subquery = db.session.query(ApprovalInstance.id).filter(
            ApprovalInstance.object_type == 'quotation'
        ).join(Quotation, ApprovalInstance.object_id == Quotation.id).subquery()
        
        customer_subquery = db.session.query(ApprovalInstance.id).filter(
            ApprovalInstance.object_type == 'customer'
        ).join(Company, ApprovalInstance.object_id == Company.id).subquery()
        
        # 只查询存在于任一子查询中的审批实例
        query = query.filter(
            or_(
                ApprovalInstance.id.in_(project_subquery),
                ApprovalInstance.id.in_(quotation_subquery),
                ApprovalInstance.id.in_(customer_subquery)
            )
        )
        
    if status:
        query = query.filter(ApprovalInstance.status == status)
    
    # 按创建时间倒序排列
    query = query.order_by(ApprovalInstance.started_at.desc())
    
    # 返回分页结果
    return query.paginate(page=page, per_page=per_page, error_out=False)
'''
    
    # 将代码写入文件
    with open('improved_approval_queries.py', 'w', encoding='utf-8') as f:
        f.write(improved_code)
    
    print("✅ 改进的审批查询函数已生成到 improved_approval_queries.py")
    print("\n📋 使用说明:")
    print("1. 复制 improved_approval_queries.py 中的函数")
    print("2. 替换 app/helpers/approval_helpers.py 中对应的函数")
    print("3. 这将确保审批中心只显示关联业务对象存在的审批实例")
    print("\n🎯 改进要点:")
    print("- 使用 JOIN 查询确保业务对象存在")
    print("- 支持按业务类型过滤时的性能优化")
    print("- 防止显示孤立的审批实例")

if __name__ == "__main__":
    generate_improved_query_functions() 