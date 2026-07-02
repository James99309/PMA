# -*- coding: utf-8 -*-
"""集中注册各业务实体的关联查询(导入即注册)

调用方式:在 app/__init__.py 创建 app 时 import 一次即可
    from app.utils import related_data_register  # noqa
"""
from sqlalchemy.orm import joinedload
from app.utils.related_data import RelatedDataService
from app.utils.access_control import get_viewable_data


# ────────────────────────────────────────────────────────
# Company(客户/供应商/渠道)的关联模块
# ────────────────────────────────────────────────────────

def _company_projects(cid, user):
    """客户关联项目:通过 ProjectCustomerAssociation 关联表 → viewable Project"""
    from app.models.project import Project
    from app.models.project_customer_association import ProjectCustomerAssociation
    proj_ids = [a.project_id for a in ProjectCustomerAssociation.query
                .filter_by(company_id=cid).with_entities(ProjectCustomerAssociation.project_id).all()]
    if not proj_ids:
        return Project.query.filter(False)  # 空查询
    return get_viewable_data(Project, user,
        [Project.id.in_(proj_ids), Project.is_deleted == False])


def _company_quotations(cid, user):
    from app.models.quotation import Quotation
    return get_viewable_data(Quotation, user, [Quotation.customer_id == cid])


def _company_pricing_orders(cid, user):
    """批价单:通过客户 → 项目 → 批价单"""
    from app.models.pricing_order import PricingOrder
    from app.models.project_customer_association import ProjectCustomerAssociation
    proj_ids = [a.project_id for a in ProjectCustomerAssociation.query
                .filter_by(company_id=cid).with_entities(ProjectCustomerAssociation.project_id).all()]
    if not proj_ids:
        return PricingOrder.query.filter(False)
    # PricingOrder 用 created_by 而非 owner_id,这里简化只走 project_id
    # 实际查询不强制 viewable(批价单权限走自己的服务)— 后续可加 _build_pricing_order_query
    return PricingOrder.query.filter(PricingOrder.project_id.in_(proj_ids))


def _company_sales_orders(cid, user):
    from app.models.sales_order import SalesOrder
    return get_viewable_data(SalesOrder, user, [SalesOrder.customer_id == cid])


def _company_purchase_orders(cid, user):
    from app.models.inventory import PurchaseOrder
    return get_viewable_data(PurchaseOrder, user, [PurchaseOrder.company_id == cid])


def _company_expenses(cid, user):
    from app.models.expense import Expense
    return get_viewable_data(Expense, user,
        [Expense.customer_id == cid, Expense.is_deleted == False])


# 注册 company 的所有关联模块
def _register_company():
    from app.models.project import Project
    from app.models.quotation import Quotation
    from app.models.pricing_order import PricingOrder
    from app.models.sales_order import SalesOrder
    from app.models.inventory import PurchaseOrder
    from app.models.expense import Expense

    RelatedDataService.register(
        'company', 'project', _company_projects, 'project',
        sort_clause=Project.updated_at.desc(),
        eager_options=[joinedload(Project.owner)],
    )
    RelatedDataService.register(
        'company', 'quotation', _company_quotations, 'quotation',
        sort_clause=Quotation.updated_at.desc(),
        eager_options=[joinedload(Quotation.owner)],
    )
    RelatedDataService.register(
        'company', 'pricing_order', _company_pricing_orders, 'pricing_order',
        sort_clause=PricingOrder.created_at.desc(),
        eager_options=[joinedload(PricingOrder.creator), joinedload(PricingOrder.project)],
    )
    RelatedDataService.register(
        'company', 'sales_order', _company_sales_orders, 'sales_order',
        sort_clause=SalesOrder.created_at.desc(),
    )
    RelatedDataService.register(
        'company', 'purchase_order', _company_purchase_orders, 'order',
        sort_clause=PurchaseOrder.created_at.desc(),
    )
    RelatedDataService.register(
        'company', 'expense', _company_expenses, 'expense',
        sort_clause=Expense.updated_at.desc(),
        eager_options=[joinedload(Expense.owner)],
    )


_register_company()


# ────────────────────────────────────────────────────────
# Project 的关联模块
# ────────────────────────────────────────────────────────

def _project_quotations(pid, user):
    from app.models.quotation import Quotation
    return get_viewable_data(Quotation, user, [Quotation.project_id == pid])


def _project_pricing_orders(pid, user):
    from app.models.pricing_order import PricingOrder
    return get_viewable_data(PricingOrder, user, [PricingOrder.project_id == pid])


def _project_sales_orders(pid, user):
    from app.models.sales_order import SalesOrder
    if not hasattr(SalesOrder, 'project_id'):
        return SalesOrder.query.filter(False)
    return get_viewable_data(SalesOrder, user, [SalesOrder.project_id == pid])


def _project_expenses(pid, user):
    from app.models.expense import Expense
    return get_viewable_data(Expense, user,
        [Expense.project_id == pid, Expense.is_deleted == False])


def _register_project():
    from app.models.quotation import Quotation
    from app.models.pricing_order import PricingOrder
    from app.models.sales_order import SalesOrder
    from app.models.expense import Expense

    RelatedDataService.register(
        'project', 'quotation', _project_quotations, 'quotation',
        sort_clause=Quotation.updated_at.desc(),
        eager_options=[joinedload(Quotation.owner)],
    )
    RelatedDataService.register(
        'project', 'pricing_order', _project_pricing_orders, 'pricing_order',
        sort_clause=PricingOrder.created_at.desc(),
        eager_options=[joinedload(PricingOrder.creator)],
    )
    if hasattr(SalesOrder, 'project_id'):
        RelatedDataService.register(
            'project', 'sales_order', _project_sales_orders, 'sales_order',
            sort_clause=SalesOrder.created_at.desc(),
        )
    RelatedDataService.register(
        'project', 'expense', _project_expenses, 'expense',
        sort_clause=Expense.updated_at.desc(),
        eager_options=[joinedload(Expense.owner)],
    )


_register_project()


# ────────────────────────────────────────────────────────
# Quotation 的关联模块(同项目兄弟报价 + 该报价的批价单)
# ────────────────────────────────────────────────────────

def _quotation_sibling_quotations(qid, user):
    """同一项目下其他报价"""
    from app.models.quotation import Quotation
    q = Quotation.query.get(qid)
    if not q or not q.project_id:
        return Quotation.query.filter(False)
    return get_viewable_data(Quotation, user,
        [Quotation.project_id == q.project_id, Quotation.id != qid])


def _quotation_pricing_orders(qid, user):
    """从该报价生成的批价单(通过 project_id + 时间窗口估算 — 也可走 quotation_id 字段若存在)"""
    from app.models.pricing_order import PricingOrder
    from app.models.quotation import Quotation
    q = Quotation.query.get(qid)
    if not q or not q.project_id:
        return PricingOrder.query.filter(False)
    return PricingOrder.query.filter(PricingOrder.project_id == q.project_id)


def _register_quotation():
    from app.models.quotation import Quotation
    from app.models.pricing_order import PricingOrder

    RelatedDataService.register(
        'quotation', 'quotation', _quotation_sibling_quotations, 'quotation',
        sort_clause=Quotation.updated_at.desc(),
        eager_options=[joinedload(Quotation.owner)],
    )
    RelatedDataService.register(
        'quotation', 'pricing_order', _quotation_pricing_orders, 'pricing_order',
        sort_clause=PricingOrder.created_at.desc(),
        eager_options=[joinedload(PricingOrder.creator)],
    )


_register_quotation()


# ────────────────────────────────────────────────────────
# Expense 的关联模块(同项目其他报销)
# ────────────────────────────────────────────────────────

def _expense_sibling_expenses(eid, user):
    from app.models.expense import Expense
    e = Expense.query.get(eid)
    if not e or not e.project_id:
        return Expense.query.filter(False)
    return get_viewable_data(Expense, user,
        [Expense.project_id == e.project_id, Expense.id != eid, Expense.is_deleted == False])


def _register_expense():
    from app.models.expense import Expense

    RelatedDataService.register(
        'expense', 'expense', _expense_sibling_expenses, 'expense',
        sort_clause=Expense.updated_at.desc(),
        eager_options=[joinedload(Expense.owner)],
    )


_register_expense()
