from flask import current_app
from flask_login import current_user
from app import db
from app.models.approval import (
    ApprovalProcessTemplate, 
    ApprovalStep, 
    ApprovalInstance, 
    ApprovalRecord, 
    ApprovalStatus, 
    ApprovalAction
)
from app.models.user import User
from app.utils.dictionary_helpers import project_type_label
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime
from flask import url_for
from app.helpers.project_helpers import lock_project, unlock_project
from app.models.project import Project
from app.models.quotation import Quotation
from app.models.customer import Company

def get_user_created_approvals(user_id=None, object_type=None, status=None, page=1, per_page=20):
    """获取指定用户发起的审批列表 - 改进版，包含批价单审批，只返回关联业务对象存在的审批
    
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
    
    # 如果专门查询批价单，使用批价单的独立审批系统
    if object_type == 'pricing_order':
        from app.models.pricing_order import PricingOrder
        
        query = PricingOrder.query.filter(PricingOrder.created_by == user_id)
        
        # 状态映射 - 修复状态筛选逻辑
        if status:
            if status == ApprovalStatus.PENDING:
                query = query.filter(PricingOrder.status == 'pending')
            elif status == ApprovalStatus.APPROVED:
                query = query.filter(PricingOrder.status == 'approved')
            elif status == ApprovalStatus.REJECTED:
                query = query.filter(PricingOrder.status == 'rejected')
            # 如果传入的是字符串状态，直接匹配
            elif isinstance(status, str):
                if status.lower() == 'draft':
                    query = query.filter(PricingOrder.status == 'draft')
                elif status.lower() == 'pending':
                    query = query.filter(PricingOrder.status == 'pending')
                elif status.lower() == 'approved':
                    query = query.filter(PricingOrder.status == 'approved')
                elif status.lower() == 'rejected':
                    query = query.filter(PricingOrder.status == 'rejected')
        
        # 按创建时间倒序排列
        query = query.order_by(PricingOrder.created_at.desc())
        
        # 返回分页结果，需要包装成类似审批实例的格式
        try:
            pricing_orders = query.paginate(page=page, per_page=per_page, error_out=False)
        except Exception as e:
            # 如果分页出错，返回空结果
            try:
                from flask_sqlalchemy import Pagination
            except ImportError:
                from flask_sqlalchemy.pagination import Pagination
            pricing_orders = Pagination(query=query, page=page, per_page=per_page, total=0, items=[])
        
        # 创建虚拟审批实例对象，用于在审批中心显示
        class PricingOrderApprovalWrapper:
            def __init__(self, pricing_order):
                self.id = f"po_{pricing_order.id}"
                self.object_id = pricing_order.id
                self.object_type = 'pricing_order'
                self.started_at = pricing_order.created_at
                self.ended_at = pricing_order.approved_at if pricing_order.status == 'approved' else None
                self.created_by = pricing_order.created_by
                self.creator = pricing_order.creator
                self.pricing_order = pricing_order
                
                # 状态映射 - 确保所有状态都有对应的显示
                if pricing_order.status == 'pending':
                    self.status = type('Status', (), {'name': 'PENDING', 'value': 'pending'})()
                elif pricing_order.status == 'approved':
                    self.status = type('Status', (), {'name': 'APPROVED', 'value': 'approved'})()
                elif pricing_order.status == 'rejected':
                    self.status = type('Status', (), {'name': 'REJECTED', 'value': 'rejected'})()
                else:  # draft 或其他状态
                    self.status = type('Status', (), {'name': 'DRAFT', 'value': 'draft'})()
                
                # 虚拟流程对象
                flow_type_name = pricing_order.flow_type_label if hasattr(pricing_order, 'flow_type_label') else pricing_order.approval_flow_type
                self.process = type('Process', (), {
                    'name': f'批价单审批流程 - {flow_type_name}',
                    'id': f'pricing_{pricing_order.approval_flow_type}'
                })()
        
        # 包装分页对象
        wrapped_items = [PricingOrderApprovalWrapper(po) for po in pricing_orders.items]
        pricing_orders.items = wrapped_items
        
        return pricing_orders
        
    # 基础查询 - 通用审批系统
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
        ).join(Project, ApprovalInstance.object_id == Project.id)
        
        quotation_subquery = db.session.query(ApprovalInstance.id).filter(
            ApprovalInstance.object_type == 'quotation'
        ).join(Quotation, ApprovalInstance.object_id == Quotation.id)
        
        customer_subquery = db.session.query(ApprovalInstance.id).filter(
            ApprovalInstance.object_type == 'customer'
        ).join(Company, ApprovalInstance.object_id == Company.id)
        
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
    """获取待用户审批的列表 - 改进版，包含批价单审批，只返回关联业务对象存在的审批
    
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
    
    # 如果专门查询批价单，使用批价单的独立审批系统
    if object_type == 'pricing_order':
        from app.models.pricing_order import PricingOrder, PricingOrderApprovalRecord
        
        # 查询当前用户是审批人且处于当前审批步骤的批价单
        query = PricingOrder.query.join(
            PricingOrderApprovalRecord,
            and_(
                PricingOrderApprovalRecord.pricing_order_id == PricingOrder.id,
                PricingOrderApprovalRecord.step_order == PricingOrder.current_approval_step
            )
        ).filter(
            PricingOrderApprovalRecord.approver_id == user_id,
            PricingOrder.status == 'pending'
        )
        
        # 按创建时间倒序排列
        query = query.order_by(PricingOrder.created_at.desc())
        
        # 返回分页结果，需要包装成类似审批实例的格式
        try:
            pricing_orders = query.paginate(page=page, per_page=per_page, error_out=False)
        except Exception as e:
            # 如果分页出错，返回空结果
            try:
                from flask_sqlalchemy import Pagination
            except ImportError:
                from flask_sqlalchemy.pagination import Pagination
            pricing_orders = Pagination(query=query, page=page, per_page=per_page, total=0, items=[])
        
        # 创建虚拟审批实例对象，用于在审批中心显示
        class PricingOrderApprovalWrapper:
            def __init__(self, pricing_order):
                self.id = f"po_{pricing_order.id}"
                self.object_id = pricing_order.id
                self.object_type = 'pricing_order'
                self.started_at = pricing_order.created_at
                self.ended_at = pricing_order.approved_at if pricing_order.status == 'approved' else None
                self.created_by = pricing_order.created_by
                self.creator = pricing_order.creator
                self.pricing_order = pricing_order
                
                # 状态映射
                if pricing_order.status == 'pending':
                    self.status = type('Status', (), {'name': 'PENDING', 'value': 'pending'})()
                elif pricing_order.status == 'approved':
                    self.status = type('Status', (), {'name': 'APPROVED', 'value': 'approved'})()
                elif pricing_order.status == 'rejected':
                    self.status = type('Status', (), {'name': 'REJECTED', 'value': 'rejected'})()
                else:  # draft
                    self.status = type('Status', (), {'name': 'DRAFT', 'value': 'draft'})()
                
                # 虚拟流程对象
                flow_type_name = pricing_order.flow_type_label if hasattr(pricing_order, 'flow_type_label') else pricing_order.approval_flow_type
                self.process = type('Process', (), {
                    'name': f'批价单审批流程 - {flow_type_name}',
                    'id': f'pricing_{pricing_order.approval_flow_type}'
                })()
        
        # 包装分页对象
        wrapped_items = [PricingOrderApprovalWrapper(po) for po in pricing_orders.items]
        pricing_orders.items = wrapped_items
        
        return pricing_orders
    
    # 通用审批系统查询：找出当前用户是审批人且处于当前审批步骤的所有实例
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
        # 如果没有指定类型，需要合并通用审批系统和批价单系统的数据
        # 先处理通用审批系统
        project_subquery = db.session.query(ApprovalInstance.id).filter(
            ApprovalInstance.object_type == 'project'
        ).join(Project, ApprovalInstance.object_id == Project.id)
        
        quotation_subquery = db.session.query(ApprovalInstance.id).filter(
            ApprovalInstance.object_type == 'quotation'
        ).join(Quotation, ApprovalInstance.object_id == Quotation.id)
        
        customer_subquery = db.session.query(ApprovalInstance.id).filter(
            ApprovalInstance.object_type == 'customer'
        ).join(Company, ApprovalInstance.object_id == Company.id)
        
        # 只查询存在于任一子查询中的审批实例
        query = query.filter(
            or_(
                ApprovalInstance.id.in_(project_subquery),
                ApprovalInstance.id.in_(quotation_subquery),
                ApprovalInstance.id.in_(customer_subquery)
            )
        )
        
        # 获取通用审批系统的结果
        general_approvals = query.order_by(ApprovalInstance.started_at.desc()).paginate(
            page=1, per_page=1000, error_out=False  # 先获取所有数据，稍后合并分页
        )
        
        # 获取批价单待审批数据
        from app.models.pricing_order import PricingOrder, PricingOrderApprovalRecord
        
        po_query = PricingOrder.query.join(
            PricingOrderApprovalRecord,
            and_(
                PricingOrderApprovalRecord.pricing_order_id == PricingOrder.id,
                PricingOrderApprovalRecord.step_order == PricingOrder.current_approval_step
            )
        ).filter(
            PricingOrderApprovalRecord.approver_id == user_id,
            PricingOrder.status == 'pending'
        ).order_by(PricingOrder.created_at.desc())
        
        # 获取所有批价单（不分页，稍后合并时再分页）
        try:
            all_pricing_orders = po_query.all()
        except Exception as e:
            all_pricing_orders = []
        
        # 创建批价单包装对象
        class PricingOrderApprovalWrapper:
            def __init__(self, pricing_order):
                self.id = f"po_{pricing_order.id}"
                self.object_id = pricing_order.id
                self.object_type = 'pricing_order'
                self.started_at = pricing_order.created_at
                self.ended_at = pricing_order.approved_at if pricing_order.status == 'approved' else None
                self.created_by = pricing_order.created_by
                self.creator = pricing_order.creator
                self.pricing_order = pricing_order
                
                # 状态映射
                if pricing_order.status == 'pending':
                    self.status = type('Status', (), {'name': 'PENDING', 'value': 'pending'})()
                elif pricing_order.status == 'approved':
                    self.status = type('Status', (), {'name': 'APPROVED', 'value': 'approved'})()
                elif pricing_order.status == 'rejected':
                    self.status = type('Status', (), {'name': 'REJECTED', 'value': 'rejected'})()
                else:  # draft
                    self.status = type('Status', (), {'name': 'DRAFT', 'value': 'draft'})()
                
                # 虚拟流程对象
                flow_type_name = pricing_order.flow_type_label if hasattr(pricing_order, 'flow_type_label') else pricing_order.approval_flow_type
                self.process = type('Process', (), {
                    'name': f'批价单审批流程 - {flow_type_name}',
                    'id': f'pricing_{pricing_order.approval_flow_type}'
                })()
        
        # 包装批价单数据
        wrapped_pricing_orders = [PricingOrderApprovalWrapper(po) for po in all_pricing_orders]
        
        # 合并数据：将批价单数据添加到通用审批数据中
        combined_items = list(general_approvals.items) + wrapped_pricing_orders
        
        # 按创建时间排序
        combined_items.sort(key=lambda x: x.started_at, reverse=True)
        
        # 手动分页
        total = len(combined_items)
        start = (page - 1) * per_page
        end = start + per_page
        page_items = combined_items[start:end]
        
        # 创建合并的分页对象
        class CombinedPagination:
            def __init__(self, page, per_page, total, items):
                self.page = page
                self.per_page = per_page
                self.total = total
                self.items = items
                self.pages = (total + per_page - 1) // per_page
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1 if self.has_prev else None
                self.next_num = page + 1 if self.has_next else None
            
            def iter_pages(self, left_edge=2, right_edge=2, left_current=2, right_current=3):
                last = self.pages
                for num in range(1, last + 1):
                    if num <= left_edge or \
                       (self.page - left_current - 1 < num < self.page + right_current) or \
                       num > last - right_edge:
                        yield num
        
        return CombinedPagination(page, per_page, total, page_items)
    
    # 按创建时间倒序排列
    query = query.order_by(ApprovalInstance.started_at.desc())
    
    # 返回分页结果
    return query.paginate(page=page, per_page=per_page, error_out=False)


def get_all_approvals(object_type=None, status=None, page=1, per_page=20):
    """获取所有审批记录（仅供admin使用）- 改进版，支持批价单等独立审批系统
    
    Args:
        object_type: 过滤特定类型的审批对象
        status: 过滤特定状态的审批
        page: 页码
        per_page: 每页数量
        
    Returns:
        分页对象，包含所有审批实例列表
    """
    # 如果专门查询批价单，使用批价单的独立审批系统
    if object_type == 'pricing_order':
        from app.models.pricing_order import PricingOrder
        
        query = PricingOrder.query
        
        # 状态映射 - 修复状态筛选逻辑
        if status:
            if status == ApprovalStatus.PENDING:
                query = query.filter(PricingOrder.status == 'pending')
            elif status == ApprovalStatus.APPROVED:
                query = query.filter(PricingOrder.status == 'approved')
            elif status == ApprovalStatus.REJECTED:
                query = query.filter(PricingOrder.status == 'rejected')
            # 如果传入的是字符串状态，直接匹配
            elif isinstance(status, str):
                if status.lower() == 'draft':
                    query = query.filter(PricingOrder.status == 'draft')
                elif status.lower() == 'pending':
                    query = query.filter(PricingOrder.status == 'pending')
                elif status.lower() == 'approved':
                    query = query.filter(PricingOrder.status == 'approved')
                elif status.lower() == 'rejected':
                    query = query.filter(PricingOrder.status == 'rejected')
        
        # 按创建时间倒序排列
        query = query.order_by(PricingOrder.created_at.desc())
        
        # 返回分页结果，需要包装成类似审批实例的格式
        try:
            pricing_orders = query.paginate(page=page, per_page=per_page, error_out=False)
        except Exception as e:
            # 如果分页出错，返回空结果
            try:
                from flask_sqlalchemy import Pagination
            except ImportError:
                from flask_sqlalchemy.pagination import Pagination
            pricing_orders = Pagination(query=query, page=page, per_page=per_page, total=0, items=[])
        
        # 创建虚拟审批实例对象，用于在审批中心显示
        class PricingOrderApprovalWrapper:
            def __init__(self, pricing_order):
                self.id = f"po_{pricing_order.id}"
                self.object_id = pricing_order.id
                self.object_type = 'pricing_order'
                self.started_at = pricing_order.created_at
                self.ended_at = pricing_order.approved_at if pricing_order.status == 'approved' else None
                self.created_by = pricing_order.created_by
                self.creator = pricing_order.creator
                self.pricing_order = pricing_order
                
                # 状态映射 - 确保所有状态都有对应的显示
                if pricing_order.status == 'pending':
                    self.status = type('Status', (), {'name': 'PENDING', 'value': 'pending'})()
                elif pricing_order.status == 'approved':
                    self.status = type('Status', (), {'name': 'APPROVED', 'value': 'approved'})()
                elif pricing_order.status == 'rejected':
                    self.status = type('Status', (), {'name': 'REJECTED', 'value': 'rejected'})()
                else:  # draft 或其他状态
                    self.status = type('Status', (), {'name': 'DRAFT', 'value': 'draft'})()
                
                # 虚拟流程对象
                flow_type_name = pricing_order.flow_type_label if hasattr(pricing_order, 'flow_type_label') else pricing_order.approval_flow_type
                self.process = type('Process', (), {
                    'name': f'批价单审批流程 - {flow_type_name}',
                    'id': f'pricing_{pricing_order.approval_flow_type}'
                })()
        
        # 包装分页对象
        wrapped_items = [PricingOrderApprovalWrapper(po) for po in pricing_orders.items]
        pricing_orders.items = wrapped_items
        
        return pricing_orders
    
    # 通用审批系统
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
        # 如果没有指定类型，需要合并通用审批系统和批价单系统的数据
        # 先处理通用审批系统
        project_subquery = db.session.query(ApprovalInstance.id).filter(
            ApprovalInstance.object_type == 'project'
        ).join(Project, ApprovalInstance.object_id == Project.id)
        
        quotation_subquery = db.session.query(ApprovalInstance.id).filter(
            ApprovalInstance.object_type == 'quotation'
        ).join(Quotation, ApprovalInstance.object_id == Quotation.id)
        
        customer_subquery = db.session.query(ApprovalInstance.id).filter(
            ApprovalInstance.object_type == 'customer'
        ).join(Company, ApprovalInstance.object_id == Company.id)
        
        # 只查询存在于任一子查询中的审批实例
        query = query.filter(
            or_(
                ApprovalInstance.id.in_(project_subquery),
                ApprovalInstance.id.in_(quotation_subquery),
                ApprovalInstance.id.in_(customer_subquery)
            )
        )
        
        # 应用状态过滤器 - 对于通用审批系统，只过滤有效的枚举状态
        if status:
            # 如果是字符串状态且为草稿，跳过通用审批过滤（因为通用审批系统没有草稿状态）
            if not (isinstance(status, str) and status.lower() == 'draft'):
                query = query.filter(ApprovalInstance.status == status)
        
        # 按创建时间倒序排列
        query = query.order_by(ApprovalInstance.started_at.desc())
        
        # 获取通用审批系统的结果
        general_approvals = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 获取批价单数据并包装
        from app.models.pricing_order import PricingOrder
        po_query = PricingOrder.query
        
        # 状态过滤
        if status:
            if status == ApprovalStatus.PENDING:
                po_query = po_query.filter(PricingOrder.status == 'pending')
            elif status == ApprovalStatus.APPROVED:
                po_query = po_query.filter(PricingOrder.status == 'approved')
            elif status == ApprovalStatus.REJECTED:
                po_query = po_query.filter(PricingOrder.status == 'rejected')
            elif isinstance(status, str):
                if status.lower() == 'draft':
                    po_query = po_query.filter(PricingOrder.status == 'draft')
                elif status.lower() == 'pending':
                    po_query = po_query.filter(PricingOrder.status == 'pending')
                elif status.lower() == 'approved':
                    po_query = po_query.filter(PricingOrder.status == 'approved')
                elif status.lower() == 'rejected':
                    po_query = po_query.filter(PricingOrder.status == 'rejected')
        
        po_query = po_query.order_by(PricingOrder.created_at.desc())
        
        # 获取所有批价单（不分页，稍后合并时再分页）
        try:
            all_pricing_orders = po_query.all()
        except Exception as e:
            all_pricing_orders = []
        
        # 创建批价单包装对象
        class PricingOrderApprovalWrapper:
            def __init__(self, pricing_order):
                self.id = f"po_{pricing_order.id}"
                self.object_id = pricing_order.id
                self.object_type = 'pricing_order'
                self.started_at = pricing_order.created_at
                self.ended_at = pricing_order.approved_at if pricing_order.status == 'approved' else None
                self.created_by = pricing_order.created_by
                self.creator = pricing_order.creator
                self.pricing_order = pricing_order
                
                # 状态映射
                if pricing_order.status == 'pending':
                    self.status = type('Status', (), {'name': 'PENDING', 'value': 'pending'})()
                elif pricing_order.status == 'approved':
                    self.status = type('Status', (), {'name': 'APPROVED', 'value': 'approved'})()
                elif pricing_order.status == 'rejected':
                    self.status = type('Status', (), {'name': 'REJECTED', 'value': 'rejected'})()
                else:  # draft
                    self.status = type('Status', (), {'name': 'DRAFT', 'value': 'draft'})()
                
                # 虚拟流程对象
                flow_type_name = pricing_order.flow_type_label if hasattr(pricing_order, 'flow_type_label') else pricing_order.approval_flow_type
                self.process = type('Process', (), {
                    'name': f'批价单审批流程 - {flow_type_name}',
                    'id': f'pricing_{pricing_order.approval_flow_type}'
                })()
        
        # 包装批价单数据
        wrapped_pricing_orders = [PricingOrderApprovalWrapper(po) for po in all_pricing_orders]
        
        # 合并数据：将批价单数据添加到通用审批数据中
        combined_items = list(general_approvals.items) + wrapped_pricing_orders
        
        # 按时间重新排序
        combined_items.sort(key=lambda x: x.started_at, reverse=True)
        
        # 重新分页
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_items = combined_items[start_idx:end_idx]
        
        # 创建新的分页对象 - 手工构建，不使用Flask-SQLAlchemy的Pagination
        class CombinedPagination:
            def __init__(self, page, per_page, total, items):
                self.page = page
                self.per_page = per_page
                self.total = total
                self.items = items
                self.pages = (total + per_page - 1) // per_page  # 向上取整
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1 if self.has_prev else None
                self.next_num = page + 1 if self.has_next else None
            
            def iter_pages(self, left_edge=2, right_edge=2, left_current=2, right_current=3):
                """
                迭代页码，兼容Flask-SQLAlchemy的Pagination类
                """
                last = self.pages
                for num in range(1, last + 1):
                    if num <= left_edge or \
                       (self.page - left_current - 1 < num < self.page + right_current) or \
                       num > last - right_edge:
                        yield num
            
        total_count = general_approvals.total + len(all_pricing_orders)
        combined_pagination = CombinedPagination(
            page=page,
            per_page=per_page,
            total=total_count,
            items=paginated_items
        )
        
        return combined_pagination


def get_approval_details(instance_id):
    """获取审批流程详情
    
    Args:
        instance_id: 审批实例ID
        
    Returns:
        审批实例对象，包含流程模板、当前步骤等完整信息
    """
    return ApprovalInstance.query.filter_by(id=instance_id).first_or_404()


def get_approval_object_url(instance):
    """获取审批对象的详情页URL
    
    Args:
        instance: 审批实例对象
        
    Returns:
        业务对象详情页URL
    """
    if not instance:
        return url_for('main.index')
    
    object_type = instance.object_type
    object_id = instance.object_id
    
    if object_type == 'project':
        return url_for('project.view_project', project_id=object_id)
    elif object_type == 'quotation':
        return url_for('quotation.view_quotation', id=object_id)
    elif object_type == 'customer':
        return url_for('customer.view_company', company_id=object_id)
    elif object_type == 'pricing_order':
        return url_for('pricing_order.edit_pricing_order', order_id=object_id)
    else:
        return url_for('main.index')


def get_current_step_info(instance):
    """获取当前步骤信息
    
    Args:
        instance: 审批实例对象
        
    Returns:
        当前步骤对象，如果没有则返回None
    """
    # 处理批价单的特殊情况
    if hasattr(instance, 'object_type') and instance.object_type == 'pricing_order':
        if hasattr(instance, 'pricing_order'):
            pricing_order = instance.pricing_order
            if pricing_order.status == 'pending' and hasattr(pricing_order, 'current_approval_step') and pricing_order.current_approval_step:
                from app.models.pricing_order import PricingOrderApprovalRecord
                current_record = PricingOrderApprovalRecord.query.filter_by(
                    pricing_order_id=pricing_order.id,
                    step_order=pricing_order.current_approval_step
                ).first()
                
                if current_record and current_record.approver:
                    # 创建虚拟步骤对象
                    return type('Step', (), {
                        'step_name': current_record.step_name,
                        'approver': current_record.approver,
                        'approver_user_id': current_record.approver_id
                    })()
        return None
    
    # 处理通用审批系统
    if not instance or instance.status != ApprovalStatus.PENDING:
        return None
    
    # 获取当前步骤
    steps = ApprovalStep.query.filter_by(
        process_id=instance.process_id,
        step_order=instance.current_step
    ).first()
    
    return steps


def get_last_approver(instance):
    """获取最后一个审批人（用于已结束的审批流程）
    
    Args:
        instance: 审批实例对象
        
    Returns:
        最后一个审批人的用户对象，如果没有则返回None
    """
    # 处理批价单的特殊情况
    if hasattr(instance, 'object_type') and instance.object_type == 'pricing_order':
        if hasattr(instance, 'pricing_order'):
            pricing_order = instance.pricing_order
            if hasattr(pricing_order, 'approval_records'):
                from app.models.pricing_order import PricingOrderApprovalRecord
                last_record = PricingOrderApprovalRecord.query.filter_by(
                    pricing_order_id=pricing_order.id
                ).filter(
                    PricingOrderApprovalRecord.action.in_(['approve', 'reject'])
                ).order_by(
                    PricingOrderApprovalRecord.approved_at.desc()
                ).first()
                
                if last_record and last_record.approver:
                    return last_record.approver
        return None
    
    # 处理通用审批系统
    if not instance:
        return None
    
    # 获取最后一个审批记录
    last_record = ApprovalRecord.query.filter_by(
        instance_id=instance.id
    ).filter(
        ApprovalRecord.action.in_([ApprovalAction.APPROVE.value, ApprovalAction.REJECT.value])
    ).order_by(
        ApprovalRecord.timestamp.desc()
    ).first()
    
    if last_record and last_record.approver:
        return last_record.approver
    
    return None


def get_approval_records_by_instance(instance_id):
    """获取审批实例的所有审批记录
    
    Args:
        instance_id: 审批实例ID
        
    Returns:
        审批记录列表，按时间倒序排序
    """
    return ApprovalRecord.query.filter_by(
        instance_id=instance_id
    ).order_by(ApprovalRecord.timestamp.desc()).all()


def can_user_approve(instance_id, user_id=None):
    """检查用户是否可以审批当前步骤
    
    Args:
        instance_id: 审批实例ID
        user_id: 用户ID，默认为当前登录用户
        
    Returns:
        布尔值，表示用户是否可以审批
    """
    if user_id is None:
        user_id = current_user.id
    
    instance = ApprovalInstance.query.get(instance_id)
    if not instance or instance.status != ApprovalStatus.PENDING:
        return False
    
    # 获取当前步骤
    current_step = get_current_step_info(instance)
    if not current_step:
        return False
    
    return current_step.approver_user_id == user_id

# ----- 以下是审批流程配置模块需要的函数 ----- #

def get_approval_templates(page=1, per_page=10, object_type=None, is_active=None):
    """获取审批流程模板列表
    
    Args:
        page: 页码
        per_page: 每页数量
        object_type: 过滤特定类型的审批对象
        is_active: 是否只返回启用的模板
        
    Returns:
        分页对象，包含审批流程模板列表
    """
    query = ApprovalProcessTemplate.query
    
    if object_type:
        query = query.filter(ApprovalProcessTemplate.object_type == object_type)
        
    if is_active is not None:
        query = query.filter(ApprovalProcessTemplate.is_active == is_active)
    
    # 按创建时间倒序排列
    query = query.order_by(ApprovalProcessTemplate.created_at.desc())
    
    # 返回分页结果
    return query.paginate(page=page, per_page=per_page, error_out=False)


def get_template_details(template_id):
    """获取审批流程模板详情
    
    Args:
        template_id: 模板ID
        
    Returns:
        模板对象，包含所有步骤
    """
    return ApprovalProcessTemplate.query.filter_by(id=template_id).first_or_404()


def get_template_steps(template_id):
    """获取审批流程模板的所有步骤
    
    Args:
        template_id: 模板ID
        
    Returns:
        步骤列表，按step_order排序
    """
    return ApprovalStep.query.filter_by(
        process_id=template_id
    ).order_by(ApprovalStep.step_order.asc()).all()


def create_approval_template(name, object_type, creator_id=None, required_fields=None, lock_object_on_start=None, lock_reason=None):
    """创建审批流程模板
    
    Args:
        name: 模板名称
        object_type: 适用业务对象类型
        creator_id: 创建人ID
        required_fields: 发起审批必填字段列表
        lock_object_on_start: 是否在发起审批后锁定对象
        lock_reason: 锁定原因
        
    Returns:
        创建的模板对象
    """
    if creator_id is None:
        creator_id = current_user.id
        
    # 处理必填字段
    if isinstance(required_fields, str):
        # 如果是字符串，以逗号分隔，转换为列表
        field_list = [field.strip() for field in required_fields.split(',') if field.strip()]
    elif required_fields is None:
        field_list = []
    else:
        field_list = required_fields
    
    # 去重处理，保持顺序
    unique_fields = []
    for field in field_list:
        if field not in unique_fields:
            unique_fields.append(field)
        
    template = ApprovalProcessTemplate(
        name=name,
        object_type=object_type,
        created_by=creator_id,
        is_active=True,
        required_fields=unique_fields,
        lock_object_on_start=lock_object_on_start if lock_object_on_start is not None else True,
        lock_reason=lock_reason if lock_reason is not None else '审批流程进行中，暂时锁定编辑'
    )
    
    db.session.add(template)
    db.session.commit()
    
    current_app.logger.info(f"创建审批模板: {name}, ID: {template.id}")
    return template


def update_approval_template(template_id, name=None, object_type=None, is_active=None, required_fields=None, lock_object_on_start=None, lock_reason=None):
    """更新审批流程模板
    
    Args:
        template_id: 模板ID
        name: 新的模板名称
        object_type: 新的适用对象类型
        is_active: 是否启用
        required_fields: 发起审批必填字段列表
        lock_object_on_start: 是否在发起审批后锁定对象
        lock_reason: 锁定原因
        
    Returns:
        更新后的模板对象
    """
    template = ApprovalProcessTemplate.query.get(template_id)
    if not template:
        return None
    
    if name is not None:
        template.name = name
        
    if object_type is not None:
        template.object_type = object_type
        
    if is_active is not None:
        template.is_active = is_active
    
    if lock_object_on_start is not None:
        template.lock_object_on_start = lock_object_on_start
        
    if lock_reason is not None:
        template.lock_reason = lock_reason
    
    # 处理必填字段
    if required_fields is not None:
        if isinstance(required_fields, str):
            # 如果是字符串，以逗号分隔，转换为列表
            field_list = [field.strip() for field in required_fields.split(',') if field.strip()]
        else:
            field_list = required_fields if required_fields else []
        
        # 去重处理，保持顺序
        unique_fields = []
        for field in field_list:
            if field not in unique_fields:
                unique_fields.append(field)
        
        template.required_fields = unique_fields
    
    db.session.commit()
    
    current_app.logger.info(f"更新审批模板: {template.name}, ID: {template.id}")
    return template


def delete_approval_template(template_id):
    """删除审批流程模板
    
    Args:
        template_id: 模板ID
        
    Returns:
        字典，包含success、message和instances字段
    """
    template = ApprovalProcessTemplate.query.get(template_id)
    if not template:
        return {
            'success': False,
            'message': '审批流程模板不存在',
            'instances': []
        }
    
    # 检查是否有关联的审批实例
    instances = ApprovalInstance.query.filter_by(process_id=template_id).all()
    if instances:
        # 如果有关联实例，则只是将模板标记为禁用，并返回详细信息
        template.is_active = False
        db.session.commit()
        
        # 构建实例详情
        instance_details = []
        for instance in instances:
            instance_info = {
                'id': instance.id,
                'object_info': f"{get_object_type_display(instance.object_type)} ID: {instance.object_id}",
                'status': instance.status.value if hasattr(instance.status, 'value') else str(instance.status),
                'creator': instance.creator.username if instance.creator else '未知',
                'creator_real_name': instance.creator.real_name if instance.creator and instance.creator.real_name else '',
                'started_at': instance.started_at.strftime('%Y-%m-%d %H:%M') if instance.started_at else '未知'
            }
            instance_details.append(instance_info)
        
        return {
            'success': False,
            'message': f'无法删除模板"{template.name}"，因为存在 {len(instances)} 个关联的审批实例。模板已被禁用。',
            'instances': instance_details
        }
    
    try:
        # 否则，删除模板和所有关联的步骤
        ApprovalStep.query.filter_by(process_id=template_id).delete()
        db.session.delete(template)
        db.session.commit()
        
        return {
            'success': True,
            'message': f'审批流程模板"{template.name}"删除成功',
            'instances': []
        }
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除审批模板失败: {str(e)}")
        return {
            'success': False,
            'message': f'删除模板失败：{str(e)}',
            'instances': []
        }


def add_approval_step(template_id, step_name, approver_id, send_email=True, editable_fields=None, cc_users=None, cc_enabled=False):
    """添加审批步骤
    
    Args:
        template_id: 模板ID
        step_name: 步骤名称
        approver_id: 审批人ID
        send_email: 是否发送邮件通知
        editable_fields: 在此步骤可编辑的字段列表
        cc_users: 抄送用户ID列表
        cc_enabled: 是否启用抄送
        
    Returns:
        新创建的步骤对象，如果模板不存在则返回None
    """
    template = ApprovalProcessTemplate.query.get(template_id)
    if not template:
        return None
    
    # 获取最大步骤序号
    max_order = db.session.query(db.func.max(ApprovalStep.step_order)).filter(
        ApprovalStep.process_id == template_id
    ).scalar() or 0
    
    # 处理可编辑字段
    if editable_fields is None:
        editable_fields = []
    
    # 处理抄送用户
    if cc_users is None:
        cc_users = []
    
    # 添加新步骤
    step = ApprovalStep(
        process_id=template_id,
        step_order=max_order + 1,
        approver_user_id=approver_id,
        step_name=step_name,
        send_email=send_email,
        editable_fields=editable_fields,
        cc_users=cc_users,
        cc_enabled=cc_enabled
    )
    
    db.session.add(step)
    db.session.commit()
    
    return step


def update_approval_step(step_id, step_name=None, approver_id=None, send_email=None, editable_fields=None, cc_users=None, cc_enabled=None):
    """更新审批步骤
    
    Args:
        step_id: 步骤ID
        step_name: 步骤名称
        approver_id: 审批人ID
        send_email: 是否发送邮件通知
        editable_fields: 在此步骤可编辑的字段列表
        cc_users: 抄送用户ID列表
        cc_enabled: 是否启用抄送
        
    Returns:
        更新后的步骤对象，如果没有找到则返回None
    """
    step = ApprovalStep.query.get(step_id)
    if not step:
        return None
    
    if step_name is not None:
        step.step_name = step_name
        
    if approver_id is not None:
        step.approver_user_id = approver_id
        
    if send_email is not None:
        step.send_email = send_email
    
    if editable_fields is not None:
        step.editable_fields = editable_fields
        
    if cc_users is not None:
        step.cc_users = cc_users
        
    if cc_enabled is not None:
        step.cc_enabled = cc_enabled
    
    db.session.commit()
    
    return step


def delete_approval_step(step_id, force=False):
    """删除审批步骤
    
    Args:
        step_id: 步骤ID
        force: 是否强制删除（忽略进行中实例检查）
        
    Returns:
        布尔值，表示是否成功删除
    """
    step = ApprovalStep.query.get(step_id)
    if not step:
        return False
    
    template_id = step.process_id
    
    # 检查是否有进行中的审批实例
    if not force:
        pending_instances = ApprovalInstance.query.filter_by(
            process_id=template_id,
            status=ApprovalStatus.PENDING
        ).first()
        
        if pending_instances:
            current_app.logger.warning(f"无法删除步骤 {step_id}：存在进行中的审批实例")
            return False
    
    # 记录操作日志
    current_app.logger.info(f"删除审批步骤: {step.step_name} (ID: {step_id})")
    
    # 执行删除
    current_order = step.step_order
    db.session.delete(step)
    
    # 更新后续步骤的序号
    later_steps = ApprovalStep.query.filter(
        ApprovalStep.process_id == template_id,
        ApprovalStep.step_order > current_order
    ).all()
    
    for later_step in later_steps:
        later_step.step_order -= 1
    
    db.session.commit()
    return True


def reorder_approval_steps(template_id, step_order_map):
    """重新排序审批步骤
    
    Args:
        template_id: 模板ID
        step_order_map: 字典，键为步骤ID，值为新的step_order
        
    Returns:
        布尔值，表示是否成功重新排序
    """
    steps = ApprovalStep.query.filter_by(process_id=template_id).all()
    if not steps:
        return False
    
    # 创建一个临时映射存储原始顺序
    temp_order_map = {}
    
    # 更新步骤序号
    for step in steps:
        if step.id in step_order_map:
            # 使用负数作为临时序号，避免唯一性冲突
            temp_order_map[step.id] = step.step_order
            step.step_order = -step_order_map[step.id]
    
    db.session.commit()
    
    # 将负数序号转换为正数
    for step in steps:
        if step.step_order < 0:
            step.step_order = -step.step_order
    
    db.session.commit()
    
    return True


def get_all_users(active_only=True):
    """获取所有用户列表，用于选择审批人
    
    Args:
        active_only: 是否只返回激活状态的用户
    
    Returns:
        用户列表
    """
    # 初始查询
    query = User.query
    
    # 如果只需要活跃用户
    if active_only:
        # 管理员总是被视为活跃的，即使is_active字段为False
        # 使用OR条件查询：管理员或者is_active=True的用户
        query = query.filter(db.or_(
            User.role == 'admin',
            User._is_active == True
        ))
    
    # 执行查询并返回结果
    return query.order_by(User.username).all()


def get_object_types():
    """获取所有支持的业务对象类型
    
    Returns:
        对象类型列表，每项为(类型代码, 显示名称)
    """
    return [
        ('project', '项目'),
        ('quotation', '报价单'),
        ('customer', '客户')
    ]


# 辅助函数：获取对象类型的显示名称
def get_object_type_display(object_type):
    """获取对象类型的显示名称
    
    Args:
        object_type: 对象类型代码
        
    Returns:
        对象类型的中文显示名称
    """
    type_map = {
        'project': '项目',
        'quotation': '报价单',
        'customer': '客户',
    }
    
    return type_map.get(object_type, object_type)


def check_template_in_use(template_id, strict_mode=False):
    """检查审批流程模板是否正在使用
    
    Args:
        template_id: 模板ID
        strict_mode: 严格模式，True时仍然禁止修改已使用模板
        
    Returns:
        布尔值，表示模板是否有关联的审批实例
    """
    if strict_mode:
        # 严格模式：有任何关联实例就禁止修改
        return ApprovalInstance.query.filter_by(process_id=template_id).first() is not None
    else:
        # 宽松模式：只有进行中的实例才禁止修改
        return ApprovalInstance.query.filter_by(
            process_id=template_id,
            status=ApprovalStatus.PENDING
        ).first() is not None


def get_object_approval_instance(object_type, object_id):
    """获取业务对象的审批实例
    
    Args:
        object_type: 业务对象类型
        object_id: 业务对象ID
        
    Returns:
        对应的审批实例，如果没有则返回None
    """
    # 优先查找最新的PENDING实例
    pending_instance = ApprovalInstance.query.filter_by(
        object_type=object_type,
        object_id=object_id,
        status=ApprovalStatus.PENDING
    ).order_by(ApprovalInstance.started_at.desc()).first()
    
    if pending_instance:
        return pending_instance
    
    # 如果没有PENDING实例，查找最新的APPROVED实例（用于显示审批历史）
    approved_instance = ApprovalInstance.query.filter_by(
        object_type=object_type,
        object_id=object_id,
        status=ApprovalStatus.APPROVED
    ).order_by(ApprovalInstance.started_at.desc()).first()
    
    if approved_instance:
        return approved_instance
    
    # 被拒绝或其他情况，允许重新发起审批
    return None


def get_available_templates(object_type, object_id=None):
    """获取可用的审批流程模板列表
    
    Args:
        object_type: 业务对象类型
        object_id: 业务对象ID（可选），用于获取业务对象的特定属性以便更精确地筛选模板
        
    Returns:
        可用的审批流程模板列表
    """
    # 基本过滤：模板类型匹配且处于激活状态
    templates = ApprovalProcessTemplate.query.filter_by(
        object_type=object_type,
        is_active=True
    ).all()
    
    # 如果提供了业务对象ID，进行更精确的筛选
    if object_id and templates:
        # 根据业务对象类型获取额外属性
        business_type = None
        
        if object_type == 'project':
            project = Project.query.get(object_id)
            if project:
                business_type = project.project_type
                
                # 特殊筛选：已有授权编号的项目不能再申请授权编号
                if project.authorization_code:
                    current_app.logger.info(f"项目 {project.id} 已有授权编号 {project.authorization_code}，过滤授权模板")
                    
                    # 过滤掉包含授权步骤的模板
                    filtered_templates = []
                    for template in templates:
                        # 检查模板是否包含授权步骤
                        steps = ApprovalStep.query.filter_by(process_id=template.id).all()
                        has_auth_step = any(
                            hasattr(step, 'action_type') and step.action_type == 'authorization' 
                            for step in steps
                        )
                        
                        if not has_auth_step:
                            filtered_templates.append(template)
                        else:
                            current_app.logger.info(f"过滤授权模板: {template.name} (ID: {template.id})")
                    
                    templates = filtered_templates
        
        # 如果获取到了业务类型，进一步过滤模板
        if business_type and templates:
            # 检查模板名称是否包含业务类型关键词
            filtered_templates = []
            for template in templates:
                # 审批模板名称中包含业务类型关键词
                if business_type in template.name:
                    filtered_templates.append(template)
                # 或者检查模板id，可以添加特定规则
            
            # 如果过滤后没有模板，则返回原始列表
            if filtered_templates:
                templates = filtered_templates
    
    return templates


def start_approval_process(object_type, object_id, template_id, user_id=None):
    """发起审批流程
    
    Args:
        object_type: 业务对象类型
        object_id: 业务对象ID
        template_id: 审批流程模板ID
        user_id: 发起人ID，默认为当前登录用户
        
    Returns:
        新建的审批实例对象，如果失败则返回None
    """
    # 记录详细的诊断信息
    current_app.logger.info(f"开始发起审批流程: 对象类型={object_type}, 对象ID={object_id}, 模板ID={template_id}")
    
    # 检查是否已存在进行中的审批实例
    existing = get_object_approval_instance(object_type, object_id)
    if existing:
        status_str = str(existing.status) if hasattr(existing, 'status') else '未知状态'
        current_app.logger.warning(
            f"业务对象已存在审批实例: {object_type}:{object_id}, "
            f"实例ID: {existing.id}, 状态: {status_str}"
        )
        from flask import flash
        flash(f"发起审批失败，已存在审批流程 (状态: {status_str})", 'danger')
        return None
    
    # 查询历史审批实例，以便在日志中记录
    history_instance = ApprovalInstance.query.filter_by(
        object_type=object_type,
        object_id=object_id
    ).order_by(ApprovalInstance.ended_at.desc()).first()
    
    if history_instance and history_instance.status == ApprovalStatus.REJECTED:
        current_app.logger.info(f"该业务对象有被拒绝的审批历史: 实例ID={history_instance.id}, 拒绝时间={history_instance.ended_at}")
    
    # 获取模板
    template = ApprovalProcessTemplate.query.get(template_id)
    if not template:
        current_app.logger.warning(f"审批模板不存在: {template_id}")
        from flask import flash
        flash("发起审批失败，审批模板不存在或已被删除", 'danger')
        return None
        
    if not template.is_active:
        current_app.logger.warning(f"审批模板未启用: {template_id} ({template.name})")
        from flask import flash
        flash(f"发起审批失败，审批模板 \"{template.name}\" 未启用", 'danger')
        return None
    
    # 检查模板是否有步骤
    steps = ApprovalStep.query.filter_by(process_id=template_id).order_by(ApprovalStep.step_order.asc()).all()
    if not steps:
        current_app.logger.warning(f"审批模板没有配置审批步骤: {template_id} ({template.name})")
        from flask import flash
        flash(f"发起审批失败，审批模板 \"{template.name}\" 没有配置审批步骤", 'danger')
        return None
    
    current_app.logger.info(f"审批模板 {template.name} (ID: {template_id}) 有 {len(steps)} 个步骤")
    
    # 检查必填字段
    has_required_fields = hasattr(template, 'required_fields') and template.required_fields and len(template.required_fields) > 0
    
    if has_required_fields:
        current_app.logger.info(f"审批模板 {template.name} 设置了以下必填字段: {template.required_fields}")
        
        # 根据业务对象类型获取对象
        if object_type == 'project':
            obj = Project.query.get(object_id)
        elif object_type == 'quotation':
            from app.models.quotation import Quotation
            obj = Quotation.query.get(object_id)
        elif object_type == 'customer':
            from app.models.customer import Company
            obj = Company.query.get(object_id)
        else:
            obj = None
        
        if not obj:
            current_app.logger.warning(f"找不到业务对象: {object_type}:{object_id}")
            return None
        
        # 检查每个必填字段
        empty_fields = []
        field_values = {}  # 记录字段值用于日志
        
        for field in template.required_fields:
            if hasattr(obj, field):
                field_value = getattr(obj, field)
                # 记录字段值
                if isinstance(field_value, (str, int, float, bool)) or field_value is None:
                    field_values[field] = field_value
                elif isinstance(field_value, list):
                    field_values[field] = f"列表[长度={len(field_value)}]"
                elif field_value:
                    field_values[field] = f"对象类型: {type(field_value).__name__}"
                else:
                    field_values[field] = "空值"
                
                # 检查是否为空
                if field_value is None or field_value == '' or (isinstance(field_value, list) and len(field_value) == 0):
                    empty_fields.append(field)
            else:
                current_app.logger.warning(f"业务对象 {object_type} 没有字段 {field}")
                field_values[field] = "字段不存在"
                empty_fields.append(field)
        
                # 记录字段值日志
        current_app.logger.info(f"业务对象 {object_type}:{object_id} 字段值: {field_values}")
        
        if empty_fields:
            # 转换字段名为可读名称
            readable_fields = []
            for field in empty_fields:
                readable_fields.append(_get_field_display_name(field))
            
            error_msg = f"发起审批失败: 以下字段必填但未填写: {', '.join(readable_fields)}"
            current_app.logger.warning(error_msg)
            from flask import flash
            flash(error_msg, 'danger')
            return None
    
    if user_id is None:
        from flask_login import current_user
        user_id = current_user.id
    
    try:
        # 获取模板和步骤信息用于创建快照
        steps = ApprovalStep.query.filter_by(
            process_id=template_id
        ).order_by(ApprovalStep.step_order.asc()).all()
        
        # 创建模板快照
        template_snapshot = {
            'template_id': template.id,
            'template_name': template.name,
            'object_type': template.object_type,
            'required_fields': template.required_fields or [],
            'lock_object_on_start': template.lock_object_on_start,
            'lock_reason': template.lock_reason,
            'created_at': datetime.now().isoformat(),
            'steps': []
        }
        
        # 保存步骤快照
        for step in steps:
            step_data = {
                'id': step.id,
                'step_order': step.step_order,
                'step_name': step.step_name,
                'approver_user_id': step.approver_user_id,
                'approver_username': step.approver.username if step.approver else '',
                'approver_real_name': step.approver.real_name if step.approver else '',
                'send_email': step.send_email,
                'action_type': step.action_type,
                'action_params': step.action_params,
                'editable_fields': step.editable_fields or [],
                'cc_users': step.cc_users or [],
                'cc_enabled': step.cc_enabled
            }
            template_snapshot['steps'].append(step_data)
        
        # 创建审批实例
        instance = ApprovalInstance(
            process_id=template_id,
            object_id=object_id,
            object_type=object_type,
            current_step=1,  # 从第一步开始
            status=ApprovalStatus.PENDING,
            started_at=datetime.now(),
            created_by=user_id,
            template_snapshot=template_snapshot,
            template_version=f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        db.session.add(instance)
        db.session.flush()  # 获取实例ID但不提交
        
        current_app.logger.info(f"已为审批实例创建模板快照，版本: {instance.template_version}")
        
        # 如果模板配置了锁定对象，则锁定对象
        if template.lock_object_on_start:
            lock_success = False
            if object_type == 'quotation':
                from app.helpers.quotation_helpers import lock_quotation
                lock_success = lock_quotation(
                    quotation_id=object_id,
                    reason=template.lock_reason or '审批流程进行中，暂时锁定编辑',
                    user_id=user_id
                )
            elif object_type == 'project':
                # 先检查项目是否已被锁定，如果是，先解锁再锁定
                project = Project.query.get(object_id)
                if project and project.is_locked:
                    current_app.logger.info(f"项目已被锁定，尝试强制重新锁定: {object_id}, 原因: {project.locked_reason}")
                
                lock_success = lock_project(
                    project_id=object_id,
                    reason=f"授权编号审批锁定: {template.name}",
                    user_id=user_id,
                    force=True  # 强制锁定，即使已经锁定也更新锁定状态
                )
            elif object_type == 'customer':
                # 客户锁定逻辑可以在这里添加
                lock_success = True  # 暂时跳过客户锁定
            
            if not lock_success and object_type in ['quotation', 'project']:
                current_app.logger.warning(f"锁定{object_type}失败: {object_id}")
                # 锁定失败时回滚审批实例创建
                db.session.rollback()
                from flask import flash
                flash(f"发起审批失败: 无法锁定{get_object_type_display(object_type)}，请稍后再试", 'danger')
                return None
        
        db.session.commit()
        current_app.logger.info(f"成功发起审批流程: {object_type}:{object_id}, 模板ID: {template_id}, 实例ID: {instance.id}")
        return instance
    except Exception as e:
        current_app.logger.error(f"创建审批实例时发生异常: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        db.session.rollback()
        from flask import flash
        flash(f"发起审批失败: 系统错误 - {str(e)}", 'danger')
        return None


def _get_field_display_name(field_name):
    """获取字段的显示名称
    
    Args:
        field_name: 字段名
        
    Returns:
        字段的显示名称
    """
    field_map = {
        # 项目字段
        'authorization_code': '授权编号',
        'project_code': '项目编号',
        'project_name': '项目名称',
        'project_type': '项目类型',
        'report_time': '报备时间',
        'report_source': '报备来源',
        'end_user': '最终用户',
        'design_issues': '设计院/顾问',
        'contractor': '总承包单位',
        'system_integrator': '系统集成商',
        'product_situation': '品牌情况',
        'current_stage': '当前阶段',
        'delivery_forecast': '出货预测日期',
        'quotation_customer': '报价金额',
        
        # 报价单字段
        'quotation_code': '报价单编号',
        'customer_name': '客户名称',
        'valid_days': '有效期',
        'currency': '币种',
        'total_amount': '总金额',
        
        # 客户字段
        'company_name': '企业名称',
        'company_type': '企业类型',
        'industry': '行业',
        'country': '国家/地区',
        'region': '省份/州',
        'address': '地址',
        'contact_name': '联系人',
        # 报价单明细相关字段
        'product_name': '产品名称',
        'product_model': '产品型号',
        'product_spec': '产品规格',
        'product_brand': '产品品牌',
        'product_unit': '产品单位',
        'product_price': '产品单价',
        'discount_rate': '折扣率',
        'discounted_price': '折后单价',
        'quantity': '数量',
        'subtotal': '小计',
        'product_mn': '产品编码',
        'remark': '备注'
    }
    
    return field_map.get(field_name, field_name)


def process_approval_with_project_type(instance_id, action, project_type=None, comment=None, user_id=None):
    """处理审批操作，支持项目类型修改
    
    Args:
        instance_id: 审批实例ID
        action: 审批动作（ApprovalAction枚举值）
        project_type: 项目类型，用于授权步骤
        comment: 审批意见
        user_id: 操作人ID
        
    Returns:
        布尔值，表示操作是否成功
    """
    instance = ApprovalInstance.query.get(instance_id)
    if not instance or instance.status != ApprovalStatus.PENDING:
        return False
    
    if user_id is None:
        user_id = current_user.id
    
    # 获取当前步骤
    current_step = get_current_step_info(instance)
    if not current_step or current_step.approver_user_id != user_id:
        return False
    
    # 检查是否是授权编号步骤
    is_authorization_step = (
        hasattr(current_step, 'action_type') and 
        current_step.action_type == 'authorization'
    )
    
    # 确保action是枚举类型
    if not isinstance(action, ApprovalAction):
        if action == 'approve':
            action = ApprovalAction.APPROVE
        elif action == 'reject':
            action = ApprovalAction.REJECT
        else:
            current_app.logger.error(f"无效的审批动作: {action}")
            return False
    
    # 记录审批结果
    record = ApprovalRecord(
        instance_id=instance_id,
        step_id=current_step.id,
        approver_id=user_id,
        action=action.value,
        comment=comment,
        timestamp=datetime.now()
    )
    
    db.session.add(record)
    
    # 处理授权编号逻辑 - 只有通过且是授权步骤时才执行
    authorization_result = None
    if action == ApprovalAction.APPROVE and is_authorization_step and instance.object_type == 'project':
        authorization_result = _handle_project_authorization(instance, project_type)
    
    # 如果拒绝，直接结束流程
    if action == ApprovalAction.REJECT:
        instance.status = ApprovalStatus.REJECTED
        instance.ended_at = datetime.now()
        
        # 更新业务对象的审批状态
        _update_business_object_approval_status(instance, action, user_id, comment)
        
        # 解锁对象
        if instance.object_type == 'project':
            unlock_project(instance.object_id, user_id)
        elif instance.object_type == 'quotation':
            from app.helpers.quotation_helpers import unlock_quotation
            unlock_quotation(instance.object_id, user_id)
    else:
        # 获取下一步骤
        next_step_order = instance.current_step + 1
        next_step = ApprovalStep.query.filter_by(
            process_id=instance.process_id,
            step_order=next_step_order
        ).first()
        
        if next_step:
            # 更新到下一步
            instance.current_step = next_step_order
        else:
            # 所有步骤已完成，流程通过
            instance.status = ApprovalStatus.APPROVED
            instance.ended_at = datetime.now()
            
            # 更新业务对象的审批状态
            _update_business_object_approval_status(instance, action, user_id, comment)
            
            # 解锁对象
            if instance.object_type == 'project':
                unlock_project(instance.object_id, user_id)
            elif instance.object_type == 'quotation':
                from app.helpers.quotation_helpers import unlock_quotation
                unlock_quotation(instance.object_id, user_id)
    
    try:
        db.session.commit()
        
        # 如果设置了发送邮件，则发送邮件通知
        if current_step.send_email:
            try:
                _send_approval_notification(instance, current_step, action, comment)
            except Exception as e:
                # 记录日志但不影响主流程
                current_app.logger.error(f"发送审批邮件失败: {str(e)}")
        
        return True
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"处理审批失败: {str(e)}")
        return False


def _handle_project_authorization(instance, project_type):
    """处理项目授权编号逻辑
    
    Args:
        instance: 审批实例对象
        project_type: 用户选择的项目类型
        
    Returns:
        生成的授权编号或None
    """
    project = Project.query.get(instance.object_id)
    if not project:
        current_app.logger.error(f"找不到项目: {instance.object_id}")
        return None
    
    # 如果已经有授权编号，则不做处理
    if project.authorization_code:
        current_app.logger.warning(f"项目已有授权编号，不进行处理: {project.id} - {project.authorization_code}")
        return project.authorization_code
    
    try:
        # 如果提供了项目类型，则更新项目类型
        if project_type and project_type != project.project_type:
            current_app.logger.info(f"更新项目类型: {project.id}, 原类型: {project.project_type}, 新类型: {project_type}")
            project.project_type = project_type
        
        # 将英文类型映射为中文，用于生成授权编号
        project_type_for_code = project_type_label(project.project_type)
        
        # 生成授权编号
        authorization_code = Project.generate_authorization_code(project_type_for_code)
        if not authorization_code:
            current_app.logger.error(f"无法为项目生成授权编号: {project.id}, 类型: {project_type_for_code}")
            return None
        
        # 更新项目信息
        project.authorization_code = authorization_code
        project.authorization_status = None  # 清除pending状态
        project.report_time = datetime.now().date()  # 更新报备日期为当前日期
        
        # 同步更新所有关联报价单的project_stage和project_type
        quotations = Quotation.query.filter_by(project_id=project.id).all()
        for q in quotations:
            q.project_stage = project.current_stage
            q.project_type = project.project_type
        
        current_app.logger.info(f"项目授权成功: {project.id}, 授权编号: {authorization_code}, 项目类型: {project.project_type}")
        return authorization_code
    except Exception as e:
        current_app.logger.error(f"处理项目授权失败: {project.id}, 错误: {str(e)}")
        return None


def process_approval(instance_id, action, comment=None, user_id=None, project_type=None):
    """处理审批操作
    
    Args:
        instance_id: 审批实例ID
        action: 审批动作（ApprovalAction枚举值）
        comment: 审批意见
        user_id: 操作人ID，默认为当前登录用户
        project_type: 项目类型，用于授权步骤
        
    Returns:
        布尔值，表示操作是否成功
    """
    # 如果提供了项目类型，使用扩展的处理函数
    if project_type is not None:
        return process_approval_with_project_type(instance_id, action, project_type, comment, user_id)
    
    # 原始处理逻辑保持不变...
    instance = ApprovalInstance.query.get(instance_id)
    if not instance or instance.status != ApprovalStatus.PENDING:
        return False
    
    if user_id is None:
        user_id = current_user.id
    
    # 获取当前步骤
    current_step = get_current_step_info(instance)
    if not current_step or current_step.approver_user_id != user_id:
        return False
    
    # 确保action是枚举类型
    if not isinstance(action, ApprovalAction):
        if action == 'approve':
            action = ApprovalAction.APPROVE
        elif action == 'reject':
            action = ApprovalAction.REJECT
        else:
            current_app.logger.error(f"无效的审批动作: {action}")
            return False
    
    # 记录审批结果
    record = ApprovalRecord(
        instance_id=instance_id,
        step_id=current_step.id,
        approver_id=user_id,
        action=action.value,
        comment=comment,
        timestamp=datetime.now()
    )
    
    db.session.add(record)
    
    # 如果拒绝，直接结束流程
    if action == ApprovalAction.REJECT:
        instance.status = ApprovalStatus.REJECTED
        instance.ended_at = datetime.now()
        
        # 更新业务对象的审批状态
        _update_business_object_approval_status(instance, action, user_id, comment)
        
        # 解锁对象
        if instance.object_type == 'project':
            unlock_project(instance.object_id, user_id)
        elif instance.object_type == 'quotation':
            from app.helpers.quotation_helpers import unlock_quotation
            unlock_quotation(instance.object_id, user_id)
    else:
        # 获取下一步骤
        next_step_order = instance.current_step + 1
        next_step = ApprovalStep.query.filter_by(
            process_id=instance.process_id,
            step_order=next_step_order
        ).first()
        
        if next_step:
            # 更新到下一步
            instance.current_step = next_step_order
        else:
            # 所有步骤已完成，流程通过
            instance.status = ApprovalStatus.APPROVED
            instance.ended_at = datetime.now()
            
            # 更新业务对象的审批状态
            _update_business_object_approval_status(instance, action, user_id, comment)
            
            # 解锁对象
            if instance.object_type == 'project':
                unlock_project(instance.object_id, user_id)
            elif instance.object_type == 'quotation':
                from app.helpers.quotation_helpers import unlock_quotation
                unlock_quotation(instance.object_id, user_id)
    
    db.session.commit()
    
    # 如果设置了发送邮件，则发送邮件通知
    if current_step.send_email:
        try:
            _send_approval_notification(instance, current_step, action, comment)
        except Exception as e:
            # 记录日志但不影响主流程
            current_app.logger.error(f"发送审批邮件失败: {str(e)}")
    
    return True


def _send_approval_notification(instance, step, action, comment):
    """发送审批通知邮件（内部函数）
    
    Args:
        instance: 审批实例
        step: 当前步骤
        action: 审批动作
        comment: 审批意见
    """
    # 邮件发送逻辑，可根据项目实际需求实现
    # 这里仅添加占位，实际实现可在第五阶段通知系统中完成
    pass 


def delete_approval_instance(instance_id):
    """删除审批实例
    
    Args:
        instance_id: 审批实例ID
        
    Returns:
        布尔值，表示是否成功删除
    """
    instance = ApprovalInstance.query.get(instance_id)
    if not instance:
        return False
    
    # 删除相关记录和实例
    try:
        # 级联删除所有相关记录
        db.session.delete(instance)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除审批实例失败: {str(e)}")
        return False


def get_object_field_options(object_type=None):
    """获取业务对象的字段选项列表，用于必填字段下拉多选
    
    Args:
        object_type: 业务对象类型，如project、quotation、customer
        
    Returns:
        字段选项列表，每项为 (字段名, 显示名称)
    """
    # 所有业务对象类型通用字段
    common_fields = []
    
    # 各业务对象特有字段
    project_fields = [
        ('project_code', '项目编号'),
        ('project_name', '项目名称'),
        ('authorization_code', '授权编号'),
        ('project_type', '项目类型'),
        ('report_time', '报备时间'),
        ('report_source', '报备来源'),
        ('end_user', '最终用户'),
        ('design_issues', '设计院/顾问'),
        ('contractor', '总承包单位'),
        ('system_integrator', '系统集成商'),
        ('product_situation', '品牌情况'),
        ('current_stage', '当前阶段'),
        ('delivery_forecast', '出货预测日期')
    ]
    
    quotation_fields = [
        ('quotation_code', '报价单编号'),
        ('customer_name', '客户名称'),
        ('valid_days', '有效期'),
        ('currency', '币种'),
        ('total_amount', '总金额'),
        ('project_type', '项目类型'),
        # 报价单明细相关字段
        ('product_name', '产品名称'),
        ('product_model', '产品型号'),
        ('product_spec', '产品规格'),
        ('product_brand', '产品品牌'),
        ('product_unit', '产品单位'),
        ('product_price', '产品单价'),
        ('discount_rate', '折扣率'),
        ('discounted_price', '折后单价'),
        ('quantity', '数量'),
        ('subtotal', '小计'),
        ('product_mn', '产品编码'),
        ('remark', '备注')
    ]
    
    customer_fields = [
        ('company_name', '企业名称'),
        ('company_type', '企业类型'),
        ('industry', '行业'),
        ('country', '国家/地区'),
        ('region', '省份/州'),
        ('address', '地址'),
        ('contact_name', '联系人')
    ]
    
    # 根据业务对象类型返回对应的字段列表
    if object_type == 'project':
        return common_fields + project_fields
    elif object_type == 'quotation':
        return common_fields + quotation_fields
    elif object_type == 'customer':
        return common_fields + customer_fields
    else:
        # 如果没有指定业务对象类型，返回所有字段
        all_fields = set(common_fields + project_fields + quotation_fields + customer_fields)
        return sorted(list(all_fields), key=lambda x: x[1])  # 按显示名称排序 


def get_rejected_approval_history(object_type, object_id):
    """获取业务对象最近一条被拒绝的审批历史
    
    Args:
        object_type: 业务对象类型
        object_id: 业务对象ID
        
    Returns:
        最近一条被拒绝的审批实例，如果没有则返回None
    """
    return ApprovalInstance.query.filter_by(
        object_type=object_type,
        object_id=object_id,
        status=ApprovalStatus.REJECTED
    ).order_by(ApprovalInstance.ended_at.desc()).first() 


def get_pending_approval_count(user_id=None):
    """获取待用户审批的数量 - 包含批价单审批
    
    Args:
        user_id: 用户ID，默认为当前登录用户
        
    Returns:
        整数，表示待审批的数量
    """
    if user_id is None:
        # 检查用户是否已登录
        if not current_user.is_authenticated:
            return 0
        user_id = current_user.id
    
    # 查询当前用户是审批人且处于当前审批步骤的所有实例数量（通用审批系统）
    general_count = ApprovalInstance.query.join(
        ApprovalStep, 
        and_(
            ApprovalStep.process_id == ApprovalInstance.process_id,
            ApprovalStep.step_order == ApprovalInstance.current_step
        )
    ).filter(
        ApprovalStep.approver_user_id == user_id,
        ApprovalInstance.status == ApprovalStatus.PENDING
    ).count()
    
    # 查询批价单待审批数量
    pricing_order_count = 0
    try:
        from app.models.pricing_order import PricingOrder, PricingOrderApprovalRecord
        
        pricing_order_count = PricingOrder.query.join(
            PricingOrderApprovalRecord,
            and_(
                PricingOrderApprovalRecord.pricing_order_id == PricingOrder.id,
                PricingOrderApprovalRecord.step_order == PricingOrder.current_approval_step
            )
        ).filter(
            PricingOrderApprovalRecord.approver_id == user_id,
            PricingOrder.status == 'pending'
        ).count()
    except Exception as e:
        # 如果查询出错，忽略批价单数量
        pricing_order_count = 0
    
    return general_count + pricing_order_count 


def get_workflow_steps(approval_instance):
    """获取审批流程的步骤信息，用于在审批区域显示流程图
    
    Args:
        approval_instance: 审批实例对象
        
    Returns:
        包含步骤信息的列表，每个步骤包含：
        - order: 步骤顺序
        - name: 步骤名称
        - approver: 审批人姓名
        - is_current: 是否为当前步骤
        - is_completed: 是否已完成
        - action: 审批动作（approve/reject）
        - timestamp: 审批时间
        - comment: 审批意见
    """
    if not approval_instance or not approval_instance.process:
        return []
    
    # 获取流程模板的所有步骤
    template_steps = ApprovalStep.query.filter_by(
        process_id=approval_instance.process_id
    ).order_by(ApprovalStep.step_order.asc()).all()
    
    # 获取已完成的审批记录
    completed_records = ApprovalRecord.query.filter_by(
        instance_id=approval_instance.id
    ).order_by(ApprovalRecord.timestamp.asc()).all()
    
    # 构建步骤信息
    workflow_steps = []
    current_step_index = len(completed_records)
    
    for i, step in enumerate(template_steps):
        step_info = {
            'order': step.step_order,
            'name': step.step_name,
            'approver': step.approver.real_name or step.approver.username if step.approver else '未知',
            'is_current': i == current_step_index and approval_instance.status == ApprovalStatus.PENDING,
            'is_completed': i < len(completed_records),
            'action': None,
            'timestamp': None,
            'comment': None
        }
        
        # 如果步骤已完成，添加审批记录信息
        if i < len(completed_records):
            record = completed_records[i]
            step_info.update({
                'action': record.action,
                'timestamp': record.timestamp,
                'comment': record.comment
            })
        
        workflow_steps.append(step_info)
    
    return workflow_steps


def render_approval_code(instance_id):
    """渲染审批编号
    
    Args:
        instance_id: 审批实例ID
        
    Returns:
        格式化的审批编号HTML
    """
    return f'<span class="badge rounded-pill" style="background-color: #ff8c00; color: white; font-weight: 500;">APV-{instance_id:04d}</span>' 


def _update_business_object_approval_status(instance, action, user_id, comment):
    """更新业务对象的审批状态
    
    Args:
        instance: 审批实例对象
        action: 审批动作
        user_id: 操作人ID
        comment: 审批意见
    """
    try:
        from app.models.user import User
        user = User.query.get(user_id) if user_id else None
        
        if instance.object_type == 'quotation':
            # 更新报价单的审批状态
            from app.models.quotation import Quotation, QuotationApprovalStatus
            quotation = Quotation.query.get(instance.object_id)
            
            if quotation and quotation.project:
                # 根据项目当前阶段确定审批状态
                project_stage = quotation.project.current_stage
                target_approval_status = QuotationApprovalStatus.STAGE_TO_APPROVAL.get(project_stage)
                
                if target_approval_status and action == ApprovalAction.APPROVE:
                    # 更新审批状态
                    quotation.approval_status = target_approval_status
                    
                    # 添加到已审核阶段列表
                    if not quotation.approved_stages:
                        quotation.approved_stages = []
                    if target_approval_status not in quotation.approved_stages:
                        quotation.approved_stages.append(target_approval_status)
                    
                    # 添加审核历史
                    if not quotation.approval_history:
                        quotation.approval_history = []
                    quotation.approval_history.append({
                        'action': 'approve',
                        'stage': project_stage,
                        'approval_status': target_approval_status,
                        'approver_id': user_id,
                        'approver_name': user.username if user else '未知',
                        'comment': comment or '',
                        'timestamp': datetime.now().isoformat(),
                        'approval_instance_id': instance.id
                    })
                    
                    # 添加待确认徽章（新增逻辑）
                    quotation.set_pending_confirmation_badge()
                    
                    current_app.logger.info(f"报价单 {quotation.quotation_number} 审批状态已更新为: {target_approval_status}")
                    
                elif action == ApprovalAction.REJECT:
                    # 拒绝审批
                    quotation.approval_status = QuotationApprovalStatus.REJECTED
                    
                    # 添加审核历史
                    if not quotation.approval_history:
                        quotation.approval_history = []
                    quotation.approval_history.append({
                        'action': 'reject',
                        'stage': project_stage if quotation.project else None,
                        'approver_id': user_id,
                        'approver_name': user.username if user else '未知',
                        'comment': comment or '',
                        'timestamp': datetime.now().isoformat(),
                        'approval_instance_id': instance.id
                    })
                    
                    current_app.logger.info(f"报价单 {quotation.quotation_number} 审批被拒绝")
        
        elif instance.object_type == 'project':
            # 项目审批状态更新逻辑（如果需要的话）
            # 这里可以根据项目的具体需求来实现
            pass
            
        elif instance.object_type == 'customer':
            # 客户审批状态更新逻辑（如果需要的话）
            # 这里可以根据客户的具体需求来实现
            pass
            
    except Exception as e:
        current_app.logger.error(f"更新业务对象审批状态失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc()) 


# ----- 以下是审批列表模板需要的业务对象获取函数 ----- #

def get_quotation_by_id(quotation_id):
    """根据ID获取报价单对象
    
    Args:
        quotation_id: 报价单ID
        
    Returns:
        报价单对象，如果不存在则返回None
    """
    try:
        from app.models.quotation import Quotation
        return Quotation.query.get(quotation_id)
    except Exception as e:
        current_app.logger.error(f"获取报价单失败: {str(e)}")
        return None


def get_project_by_id(project_id):
    """根据ID获取项目对象
    
    Args:
        project_id: 项目ID
        
    Returns:
        项目对象，如果不存在则返回None
    """
    try:
        from app.models.project import Project
        return Project.query.get(project_id)
    except Exception as e:
        current_app.logger.error(f"获取项目失败: {str(e)}")
        return None


def get_customer_by_id(customer_id):
    """根据ID获取客户对象
    
    Args:
        customer_id: 客户ID
        
    Returns:
        客户对象，如果不存在则返回None
    """
    try:
        from app.models.customer import Company
        return Company.query.get(customer_id)
    except Exception as e:
        current_app.logger.error(f"获取客户失败: {str(e)}")
        return None


def get_pricing_order_by_id(pricing_order_id):
    """根据ID获取批价单对象
    
    Args:
        pricing_order_id: 批价单ID
        
    Returns:
        批价单对象，如果不存在则返回None
    """
    try:
        from app.models.pricing_order import PricingOrder
        return PricingOrder.query.get(pricing_order_id)
    except Exception as e:
        current_app.logger.error(f"获取批价单失败: {str(e)}")
        return None


def get_user_pricing_order_approvals(user_id, status=None, page=1, per_page=20):
    """获取用户相关的批价单审批记录
    
    包括：
    1. 用户创建的批价单
    2. 用户需要审批的批价单
    3. 用户已经审批过的批价单
    
    Args:
        user_id: 用户ID
        status: 状态筛选
        page: 页码
        per_page: 每页数量
        
    Returns:
        分页对象，包含批价单审批记录
    """
    from app.models.pricing_order import PricingOrder, PricingOrderApprovalRecord
    from sqlalchemy import or_, and_
    
    # 构建查询条件
    conditions = []
    
    # 1. 用户创建的批价单
    conditions.append(PricingOrder.created_by == user_id)
    
    # 2. 用户是审批人的批价单
    conditions.append(
        PricingOrder.approval_records.any(
            PricingOrderApprovalRecord.approver_id == user_id
        )
    )
    
    # 3. 用户是项目销售负责人的批价单
    conditions.append(
        and_(
            PricingOrder.project_id.isnot(None),
            PricingOrder.project.has(vendor_sales_manager_id=user_id)
        )
    )
    
    # 构建主查询
    query = PricingOrder.query.filter(or_(*conditions))
    
    # 状态筛选
    if status:
        if isinstance(status, str):
            query = query.filter(PricingOrder.status == status.lower())
        else:
            # 处理枚举类型状态
            status_map = {
                'PENDING': 'pending',
                'APPROVED': 'approved', 
                'REJECTED': 'rejected',
                'DRAFT': 'draft'
            }
            if hasattr(status, 'name') and status.name in status_map:
                query = query.filter(PricingOrder.status == status_map[status.name])
    
    # 按创建时间倒序排列
    query = query.order_by(PricingOrder.created_at.desc())
    
    # 分页
    try:
        pricing_orders = query.paginate(page=page, per_page=per_page, error_out=False)
    except Exception as e:
        current_app.logger.error(f"批价单审批分页查询失败: {str(e)}")
        # 返回空结果
        try:
            from flask_sqlalchemy import Pagination
        except ImportError:
            from flask_sqlalchemy.pagination import Pagination
        pricing_orders = Pagination(query=query, page=page, per_page=per_page, total=0, items=[])
    
    # 包装为审批实例格式
    class PricingOrderApprovalWrapper:
        def __init__(self, pricing_order):
            self.id = f"po_{pricing_order.id}"
            self.pricing_order = pricing_order
            self.object_type = 'pricing_order'
            self._object_id = pricing_order.id
            self.started_at = pricing_order.created_at
            self.ended_at = pricing_order.approved_at
            self.creator_id = pricing_order.created_by
            
            # 状态映射
            status_map = {
                'draft': type('Status', (), {'name': 'DRAFT', 'value': 'draft'})(),
                'pending': type('Status', (), {'name': 'PENDING', 'value': 'pending'})(),
                'approved': type('Status', (), {'name': 'APPROVED', 'value': 'approved'})(),
                'rejected': type('Status', (), {'name': 'REJECTED', 'value': 'rejected'})()
            }
            self.status = status_map.get(pricing_order.status, 
                                       type('Status', (), {'name': 'UNKNOWN', 'value': pricing_order.status})())
            
            # 创建人信息
            from app.models.user import User
            creator = User.query.get(pricing_order.created_by)
            self.creator = creator
            
            # 虚拟流程对象
            flow_type_labels = {
                'channel_follow': '渠道跟进类',
                'sales_key': '销售重点类',
                'sales_opportunity': '销售机会类'
            }
            flow_type_name = flow_type_labels.get(pricing_order.approval_flow_type, pricing_order.approval_flow_type)
            self.process = type('Process', (), {
                'name': f'批价单审批流程 - {flow_type_name}',
                'id': f'pricing_{pricing_order.approval_flow_type}'
            })()
            
            # 当前步骤信息
            self.current_step = pricing_order.current_approval_step
            
            # 业务对象信息
            self.business_object = pricing_order
            self.business_object_name = pricing_order.order_number
            
        def get_detail_url(self):
            """获取详情页URL"""
            from flask import url_for
            return url_for('pricing_order.edit_pricing_order', order_id=self.pricing_order.id)
        
        @property
        def object_id(self):
            """兼容性属性：返回批价单ID"""
            return self._object_id
    
    # 包装分页对象
    wrapped_items = [PricingOrderApprovalWrapper(po) for po in pricing_orders.items]
    pricing_orders.items = wrapped_items
    
    return pricing_orders