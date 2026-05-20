# -*- coding: utf-8 -*-
"""Wiki Scope 过滤服务

根据当前用户身份，过滤出可见的文章和原始文件。

可见性规则：
- system: 所有人可见
- company: 同公司成员可见（按 owner.company_name 比对 user.company_name）
- department: 同部门成员可见（部门经理看本部门所有）
- personal: 仅自己可见（部门经理额外看本部门成员的）
- 分享授权: KnowledgeShareGrant 扩展的可见范围
- admin/ceo: 所有内容可见
"""
from sqlalchemy import or_, and_

from app.models.knowledge import (
    KnowledgeRawFile,
    KnowledgeShareGrant,
    KnowledgeWikiArticle,
)
from app.models.user import User


def visible_articles_query(user):
    """返回当前用户可见的 KnowledgeWikiArticle 查询对象。"""
    # admin/ceo 看所有
    if user.role in ('admin', 'ceo'):
        return KnowledgeWikiArticle.query

    conditions = [
        KnowledgeWikiArticle.scope == 'system',
    ]

    # 同公司的 company 级文章（按 owner.company_name 比对 user.company_name）
    user_company = getattr(user, 'company_name', None)
    if user_company:
        same_company_user_ids = _get_company_user_ids(user_company)
        if same_company_user_ids:
            conditions.append(
                and_(
                    KnowledgeWikiArticle.scope == 'company',
                    KnowledgeWikiArticle.owner_id.in_(same_company_user_ids),
                )
            )

    # 同部门的 department 文章
    if user.department:
        conditions.append(
            and_(
                KnowledgeWikiArticle.scope == 'department',
                KnowledgeWikiArticle.owner_department == user.department,
            )
        )

    # 自己的 personal
    conditions.append(
        and_(
            KnowledgeWikiArticle.scope == 'personal',
            KnowledgeWikiArticle.owner_id == user.id,
        )
    )

    # 部门经理：本部门成员的 personal
    if user.is_department_manager and user.department:
        dept_user_ids = _get_department_user_ids(user.department)
        if dept_user_ids:
            conditions.append(
                and_(
                    KnowledgeWikiArticle.scope == 'personal',
                    KnowledgeWikiArticle.owner_id.in_(dept_user_ids),
                )
            )

    # 跨部门分享授权
    shared_ids = _get_shared_article_ids(user)
    if shared_ids:
        conditions.append(KnowledgeWikiArticle.id.in_(shared_ids))

    return KnowledgeWikiArticle.query.filter(or_(*conditions))


def visible_raw_files_query(user):
    """返回当前用户可见的 KnowledgeRawFile 查询对象。"""
    if user.role in ('admin', 'ceo'):
        return KnowledgeRawFile.query

    conditions = [
        KnowledgeRawFile.scope == 'system',
    ]

    # 同公司的 company 级原始文件
    user_company = getattr(user, 'company_name', None)
    if user_company:
        same_company_user_ids = _get_company_user_ids(user_company)
        if same_company_user_ids:
            conditions.append(
                and_(
                    KnowledgeRawFile.scope == 'company',
                    KnowledgeRawFile.owner_id.in_(same_company_user_ids),
                )
            )

    if user.department:
        conditions.append(
            and_(
                KnowledgeRawFile.scope == 'department',
                KnowledgeRawFile.owner_department == user.department,
            )
        )

    conditions.append(
        and_(
            KnowledgeRawFile.scope == 'personal',
            KnowledgeRawFile.owner_id == user.id,
        )
    )

    if user.is_department_manager and user.department:
        dept_user_ids = _get_department_user_ids(user.department)
        if dept_user_ids:
            conditions.append(
                and_(
                    KnowledgeRawFile.scope == 'personal',
                    KnowledgeRawFile.owner_id.in_(dept_user_ids),
                )
            )

    return KnowledgeRawFile.query.filter(or_(*conditions))


def can_write_scope(user, scope: str) -> bool:
    """检查用��是否有权限直接写入指定 scope。"""
    if user.role in ('admin', 'ceo'):
        return True
    if scope == 'personal':
        return True
    if scope == 'department':
        return bool(user.department)
    # company / system 需要 admin/ceo
    return False


def can_manage_article(user, article) -> bool:
    """检查用户是否能管理（编辑/删除/调整 scope）该文章。

    放行规则：
    - admin / ceo：任何文章
    - 文章所有者：任何 scope（含自己的 department 级文章）
    - 部门经理：同部门的 department 级文章
    注：升级到 company / system 另有审批门槛，由接口层控制。
    """
    if user.role in ('admin', 'ceo'):
        return True
    if article.owner_id == user.id:
        return True
    if article.scope == 'department' and user.is_department_manager \
            and user.department and article.owner_department == user.department:
        return True
    return False


def _get_department_user_ids(department: str) -> list[int]:
    """获取同部门所有用户 ID。"""
    users = User.query.filter_by(department=department).with_entities(User.id).all()
    return [u.id for u in users]


def _get_company_user_ids(company_name: str) -> list[int]:
    """获取同公司所有用户 ID。"""
    if not company_name:
        return []
    users = User.query.filter_by(company_name=company_name).with_entities(User.id).all()
    return [u.id for u in users]


def _get_shared_article_ids(user) -> list[int]:
    """获取通过分享授权对该用户可见的文章 ID。"""
    conditions = []

    # 直接分享给用户
    conditions.append(
        and_(
            KnowledgeShareGrant.grant_type == 'user',
            KnowledgeShareGrant.grant_target == str(user.id),
        )
    )

    # 分享给用户所在部门
    if user.department:
        conditions.append(
            and_(
                KnowledgeShareGrant.grant_type == 'department',
                KnowledgeShareGrant.grant_target == user.department,
            )
        )

    # 分享给用户所在企业
    if getattr(user, 'company_name', None):
        conditions.append(
            and_(
                KnowledgeShareGrant.grant_type == 'company',
                KnowledgeShareGrant.grant_target == user.company_name,
            )
        )

    grants = KnowledgeShareGrant.query.filter(or_(*conditions)).with_entities(
        KnowledgeShareGrant.article_id
    ).all()

    return [g.article_id for g in grants]
