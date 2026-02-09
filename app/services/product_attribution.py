# -*- coding: utf-8 -*-
"""
产品经理归属和角色视角服务

归属逻辑:
  Product.owner_id 是 PM 角色? → 用它
  否则 → ProductCategory.manager_id (跳过 admin 和非 PM)
"""
from app import db
from app.models.user import User
from app.models.product import Product
from app.models.product_code import ProductCategory
from app.models.relation import ProjectMember
from app.models.worklog import WorkItem
from app.models.action import Action
from sqlalchemy import func


def get_product_manager(product):
    """获取产品的负责产品经理

    Product.owner_id(PM) → fallback ProductCategory.manager_id → None
    """
    if product.owner_id:
        owner = User.query.get(product.owner_id)
        if owner and owner.role == 'product_manager':
            return owner

    if product.category_id:
        category = ProductCategory.query.get(product.category_id)
        if category and category.manager_id:
            manager = User.query.get(category.manager_id)
            if manager and manager.role == 'product_manager':
                return manager

    return None


def get_analysis_view_scope(user):
    """返回用户的分析视角范围

    Returns:
        dict: {
            level: 'admin' | 'se' | 'pm' | 'sales',
            associated_project_ids: list[int],  # SE 关联的项目
            managed_category_ids: list[int],     # PM 管理的类别
        }
    """
    from app.permissions import is_admin_or_ceo

    if is_admin_or_ceo():
        return {'level': 'admin', 'associated_project_ids': [], 'managed_category_ids': []}

    if user.role == 'solution_manager':
        project_ids = [m.project_id for m in ProjectMember.query.filter(
            ProjectMember.user_id == user.id,
            ProjectMember.role == 'solution_engineer'
        ).all()]
        return {'level': 'se', 'associated_project_ids': project_ids, 'managed_category_ids': []}

    if user.role == 'product_manager':
        category_ids = [c.id for c in ProductCategory.query.filter_by(manager_id=user.id).all()]
        return {
            'level': 'pm',
            'associated_project_ids': [],
            'managed_category_ids': category_ids
        }

    return {'level': 'sales', 'associated_project_ids': [], 'managed_category_ids': []}


def get_participation_metrics(user_id, project_ids=None):
    """获取用户的参与度指标

    Returns:
        dict: {project_count, workitem_count, action_count}
    """
    wi_q = WorkItem.query.filter(WorkItem.owner_id == user_id, WorkItem.project_id.isnot(None))
    act_q = Action.query.filter(Action.owner_id == user_id, Action.project_id.isnot(None))

    if project_ids:
        wi_q = wi_q.filter(WorkItem.project_id.in_(project_ids))
        act_q = act_q.filter(Action.project_id.in_(project_ids))

    wi_count = wi_q.count()
    act_count = act_q.count()

    # 计算涉及的项目数
    wi_projects = db.session.query(WorkItem.project_id).filter(
        WorkItem.owner_id == user_id, WorkItem.project_id.isnot(None)
    )
    act_projects = db.session.query(Action.project_id).filter(
        Action.owner_id == user_id, Action.project_id.isnot(None)
    )
    if project_ids:
        wi_projects = wi_projects.filter(WorkItem.project_id.in_(project_ids))
        act_projects = act_projects.filter(Action.project_id.in_(project_ids))

    all_pids = wi_projects.union(act_projects).distinct()
    project_count = all_pids.count()

    return {
        'project_count': project_count,
        'workitem_count': wi_count,
        'action_count': act_count
    }
