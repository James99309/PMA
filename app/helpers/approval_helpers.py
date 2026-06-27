from flask import current_app
from flask_login import current_user
from config import Config
from app import db
from app.models.approval import (
    ApprovalProcessTemplate, 
    ApprovalStep, 
    ApprovalInstance, 
    ApprovalRecord, 
    ApprovalStatus, 
    ApprovalAction
)
from app.models.approval_branch_condition import ApprovalBranchCondition
from app.models.user import User
from app.utils.dictionary_helpers import project_type_label
from sqlalchemy import and_, or_, desc, asc
from datetime import datetime
from flask import url_for


def safe_strftime(dt_value, format_str):
    """安全的日期格式化函数"""
    if not dt_value:
        return ''
    
    try:
        if isinstance(dt_value, str):
            # 如果是字符串，尝试解析
            dt = datetime.fromisoformat(dt_value.replace('Z', '+00:00'))
            return dt.strftime(format_str)
        else:
            # 如果是datetime对象
            return dt_value.strftime(format_str)
    except (ValueError, AttributeError) as e:
        current_app.logger.warning(f"日期格式化失败: {dt_value}, 错误: {e}")
        return str(dt_value) if dt_value else ''
from app.helpers.project_helpers import lock_project, unlock_project
from app.models.project import Project
from app.models.quotation import Quotation
from app.models.customer import Company


# ============================================================================
# 审批包装器类 - 将业务对象包装为统一的审批实例接口
# ============================================================================
# 这些类用于将不同的业务对象（报销单、批价单、订单）包装成统一的接口
# 使其可以在审批中心以一致的方式显示和处理
# ============================================================================

class ExpenseApprovalWrapper:
    """报销单审批包装器 - 将Expense对象包装为类似ApprovalInstance的接口"""

    def __init__(self, expense):
        # 🔥 修复：只有已发起审批的报销单才应该显示在审批中心
        # 草稿状态的报销单不应该显示审批编号
        self.real_approval_instance_id = None
        self.should_display = False  # 标记是否应该在审批中心显示

        if expense.status in ['pending', 'approved', 'rejected', 'recalled']:
            from app.models.approval import ApprovalInstance
            approval_instance = ApprovalInstance.query.filter_by(
                object_type='expense',
                object_id=expense.id
            ).order_by(ApprovalInstance.id.desc()).first()
            if approval_instance:
                self.real_approval_instance_id = approval_instance.id
                # 🔥 修改显示逻辑：无论什么状态，只要有审批实例就可以显示
                # 具体的状态过滤由调用方的查询条件控制
                self.should_display = True
                # 使用真实审批实例ID作为主ID
                self.id = approval_instance.id
                # 设置审批流程的开始时间为审批实例的开始时间
                self.started_at = approval_instance.started_at
                # 设置结束时间
                if approval_instance.ended_at:
                    self.ended_at = approval_instance.ended_at
                elif expense.status == 'approved':
                    self.ended_at = expense.approved_at
                else:
                    self.ended_at = None
            else:
                # 状态不是draft但没有审批实例，可能是数据不一致
                self.should_display = False
                self.id = f"expense_{expense.id}"
                self.started_at = expense.created_at
                self.ended_at = None
        else:
            # draft状态，不应该在审批中心显示
            self.should_display = False
            self.id = f"expense_{expense.id}"
            self.started_at = expense.created_at
            self.ended_at = None

        self.object_id = expense.id
        self.object_type = 'expense'
        self.wrapper_type = 'expense'  # 用于 convert_approval_item 识别
        self.created_by = expense.owner_id
        self.creator = expense.owner
        self.owner = expense.owner  # 用于 convert_approval_item
        self.created_at = expense.created_at  # 用于 convert_approval_item
        self.approval_status = expense.status  # 字符串状态，用于 convert_approval_item
        self.expense = expense

        # 🔥 添加审批编号 - 使用报销单编号
        self.approval_number = expense.expense_number

        # 🔥 添加关联项目名称
        self.project_name = expense.project.project_name if expense.project else None

        # 状态映射 - 确保所有状态都有对应的显示
        if expense.status == 'pending':
            self.status = type('Status', (), {'name': 'PENDING', 'value': 'pending'})()
        elif expense.status == 'approved':
            self.status = type('Status', (), {'name': 'APPROVED', 'value': 'approved'})()
        elif expense.status == 'rejected':
            self.status = type('Status', (), {'name': 'REJECTED', 'value': 'rejected'})()
        elif expense.status == 'recalled':
            self.status = type('Status', (), {'name': 'RECALLED', 'value': 'recalled'})()
        else:  # draft 或其他状态
            self.status = type('Status', (), {'name': 'DRAFT', 'value': 'draft'})()

        # 虚拟流程对象
        self.process = type('Process', (), {
            'name': '报销单审批流程',
            'id': 'expense_approval'
        })()

    def get_current_step_info(self):
        """获取当前审批步骤信息 - 修复"待分配"显示问题的关键方法"""
        if self.real_approval_instance_id:
            from app.models.approval import ApprovalInstance
            approval = ApprovalInstance.query.get(self.real_approval_instance_id)
            if approval:
                return approval.get_current_step_info()
        return None


class PricingOrderApprovalWrapper:
    """批价单审批包装器 - 将PricingOrder对象包装为类似ApprovalInstance的接口"""

    def __init__(self, pricing_order):
        self.id = pricing_order.id  # 使用原始ID，不加前缀
        self.pricing_order = pricing_order
        self.object_type = 'pricing_order'
        self.wrapper_type = 'pricing_order'  # 用于 convert_approval_item 识别
        self._object_id = pricing_order.id
        self.started_at = pricing_order.created_at
        self.created_at = pricing_order.created_at  # 用于 convert_approval_item
        self.ended_at = pricing_order.approved_at
        self.creator_id = pricing_order.created_by
        self.approval_status = pricing_order.status  # 用于 convert_approval_item

        # 关联项目名称
        self.project_name = pricing_order.project.project_name if pricing_order.project else None

        # 🔥 添加审批编号 - 使用批价单号
        self.approval_number = pricing_order.order_number

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
        self.created_by = creator  # 保存 User 对象用于 convert_approval_item

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
        return url_for('pricing_order.at_edit_pricing_order', order_id=self.pricing_order.id)

    @property
    def object_id(self):
        """兼容性属性：返回批价单ID"""
        return self._object_id

    def get_current_step_info(self):
        """获取当前审批步骤信息 - 修复"待分配"显示问题的关键方法"""
        # 批价单使用独立的审批流程，需要通过ApprovalInstance查询
        from app.models.approval import ApprovalInstance
        approval = ApprovalInstance.query.filter_by(
            object_type='pricing_order',
            object_id=self.pricing_order.id
        ).order_by(ApprovalInstance.id.desc()).first()
        if approval:
            return approval.get_current_step_info()
        return None


class OrderApprovalWrapper:
    """订单审批包装器 - 将Order对象包装为类似ApprovalInstance的接口"""

    def __init__(self, order):
        self.id = order.id  # 使用原始ID，不加前缀
        self.object_id = order.id
        self.object_type = 'purchase_order'
        self.wrapper_type = 'order'  # 用于 convert_approval_item 识别
        self.started_at = order.created_at
        self.created_at = order.created_at  # 用于 convert_approval_item
        self.ended_at = order.approved_at if order.status == 'approved' else None
        self.creator = order.created_by  # User 对象
        self.created_by = order.created_by  # User 对象，用于 convert_approval_item
        self.approval_status = order.status  # 用于 convert_approval_item
        self.order = order

        # 🔥 添加审批编号 - 使用订单号
        self.approval_number = order.order_number

        # 状态映射
        if order.status == 'pending':
            self.status = type('Status', (), {'name': 'PENDING', 'value': 'pending'})()
        elif order.status == 'approved':
            self.status = type('Status', (), {'name': 'APPROVED', 'value': 'approved'})()
        elif order.status == 'rejected':
            self.status = type('Status', (), {'name': 'REJECTED', 'value': 'rejected'})()
        else:  # draft 或其他状态
            self.status = type('Status', (), {'name': 'DRAFT', 'value': order.status})()

        # 虚拟流程对象
        self.process = type('Process', (), {
            'name': '订单审批流程',
            'id': 'purchase_order_approval'
        })()

    def get_current_step_info(self):
        """获取当前审批步骤信息 - 修复"待分配"显示问题的关键方法"""
        # 订单使用独立的审批流程，需要通过ApprovalInstance查询
        from app.models.approval import ApprovalInstance
        approval = ApprovalInstance.query.filter_by(
            object_type='purchase_order',
            object_id=self.order.id
        ).order_by(ApprovalInstance.id.desc()).first()
        if approval:
            return approval.get_current_step_info()
        return None


# 项目类型到角色的映射 - 用于授权审批工作流
# 注：此映射用于确定授权审批的默认审批人，是工作流配置而非权限检查
# 未来可迁移到数据库配置表，以便动态调整工作流
PROJECT_TYPE_ROLE_MAPPING = {
    'channel_follow': 'channel_manager',      # 渠道跟进 -> 渠道经理
    'sales_focus': 'sales_director',          # 销售重点 -> 营销总监
    'sales_key': 'sales_director',            # 向sales_focus统一
    'business_opportunity': 'service_manager' # 客户服务 -> 服务经理
}

def get_authorization_approver_by_project_type(project_type):
    """根据项目类型获取授权审批人
    
    Args:
        project_type: 项目类型
        
    Returns:
        User对象或None
    """
    from app.models.user import User
    
    # 获取目标角色
    target_role = PROJECT_TYPE_ROLE_MAPPING.get(project_type)
    if not target_role:
        # 如果没有找到对应角色，默认使用总经理
        target_role = 'ceo'
    
    # 查找第一个具有该角色的用户
    approver = User.query.filter_by(role=target_role).first()

    # 如果没找到对应角色的用户，使用总经理角色(不再回退到 admin —— admin 不参与审批)
    if not approver:
        approver = User.query.filter_by(role='ceo').first()

    return approver


def get_next_level_approver(user):
    """获取指定用户的上一级领导
    
    上一级领导逻辑：
    1. 部门成员 -> 部门负责人 -> 总经理（管理员）
    2. 如果没有部门的直接到总经理（管理员）
    3. 如果不在同一个企业中的，没有上一级就直接到管理员
    
    Args:
        user: User对象，为其查找上一级领导
        
    Returns:
        User对象或None，上一级领导
    """
    from app.models.user import User
    
    if not user:
        return None
    
    current_app.logger.debug(f"查找用户 {user.username} 的上一级领导")
    
    # 管理员发起 → 交由总经理审批(admin 不参与审批流程);无总经理则无上级(跳过)
    if user.role == 'admin':
        ceo = User.query.filter_by(role='ceo').filter(User.id != user.id).first()
        current_app.logger.debug(f"管理员 {user.username} 发起,上级={ceo.username if ceo else '无(跳过)'}")
        return ceo

    # 总经理是组织最高层，无上级 → 返回 None(上级审批步将被自动跳过，不再回退到 admin)
    if user.role == 'ceo':
        current_app.logger.debug(f"用户 {user.username} 是总经理，无上级，上级审批步将跳过")
        return None

    # 如果用户有部门且不是部门负责人，上一级是同企业同部门的部门负责人
    if user.department and user.company_name and not user.is_department_manager:
        # 方式1：查找 is_department_manager=True 的用户（主归属该部门的负责人）
        dept_manager = User.query.filter_by(
            department=user.department,
            company_name=user.company_name,
            is_department_manager=True
        ).filter(User.id != user.id).first()

        if dept_manager:
            current_app.logger.debug(f"找到部门负责人: {dept_manager.username}")
            return dept_manager

        # 方式2：查找 Department 表中该部门的 manager_id（分管人）
        # 适用于：用户主归属一个部门，但分管其他部门的情况
        from app.models.expense import Department
        dept = Department.query.filter_by(
            name=user.department,
            company_name=user.company_name
        ).first()

        if dept and dept.manager_id:
            manager = User.query.get(dept.manager_id)
            if manager and manager.id != user.id:
                current_app.logger.debug(f"找到部门分管人: {manager.username}")
                return manager

    # 如果用户是部门负责人，查找该部门的分管领导（通过 Department.manager_id）
    if user.department and user.company_name and user.is_department_manager:
        from app.models.expense import Department
        dept = Department.query.filter_by(
            name=user.department,
            company_name=user.company_name
        ).first()
        if dept and dept.manager_id:
            manager = User.query.get(dept.manager_id)
            if manager and manager.id != user.id:
                current_app.logger.debug(f"找到部门负责人的分管领导: {manager.username}")
                return manager

    # 如果是部门负责人或没有找到部门负责人，上一级是总经理
    # 优先查找同企业的总经理
    if user.company_name:
        ceo = User.query.filter_by(
            company_name=user.company_name,
            role='ceo'
        ).filter(User.id != user.id).first()
        
        if ceo:
            current_app.logger.debug(f"找到同企业总经理: {ceo.username}")
            return ceo
    
    # 如果没有同企业的总经理，查找任意总经理
    ceo = User.query.filter_by(role='ceo').filter(User.id != user.id).first()
    if ceo:
        current_app.logger.debug(f"找到总经理: {ceo.username}")
        return ceo

    # 查无总经理 → 无上级(上级审批步将跳过);不再回退到 admin —— admin 不参与审批流程
    current_app.logger.debug(f"未找到用户 {user.username} 的上一级领导(无总经理),上级审批将跳过")
    return None


def get_approver_by_type(approver_type, approver_user_id, context_user=None, project_type=None):
    """根据审批人类型获取审批人
    
    Args:
        approver_type: 审批人类型 ('user', 'auto', 'next_level')
        approver_user_id: 固定审批人ID（当approver_type='user'时使用）
        context_user: 上下文用户（用于next_level类型）
        project_type: 项目类型（用于authorization动作类型）
        
    Returns:
        User对象或None
    """
    from app.models.user import User
    
    if approver_type == 'user' and approver_user_id:
        # 固定用户
        return User.query.get(approver_user_id)
    elif approver_type == 'next_level' and context_user:
        # 上一级领导
        return get_next_level_approver(context_user)
    elif approver_type == 'auto' and project_type:
        # 根据项目类型自动选择（主要用于authorization动作）
        return get_authorization_approver_by_project_type(project_type)
    
    return None


def _expense_next_level_bump(approver, approval_instance):
    """CN 报销专属规则: 上级审批若落到营销总监(sales_director),上提到总经理(CEO)。

    覆盖用户需求(2026-06-24「郭小会下面的人的报销也走ceo,郭小会也走ceo」):
      - 销售部下属提交报销 → next_level 算出的上级是营销总监 → 本规则上提到 CEO
      - 营销总监本人提交报销 → next_level 本就回退到 CEO(此处不触发,结果已是 CEO)

    仅 object_type=='expense' 且 CN(PMA_DB_TYPE=sp8d) 生效:
      - 不影响项目/报价等其它审批(它们 object_type 不同) → 「其它不变」
      - 不影响 SG(SG 亦有 sales_director,但这是 CN 专属策略,故按区域限定)
    """
    import os
    if not approver or getattr(approver, 'role', None) != 'sales_director':
        return approver
    if not approval_instance or getattr(approval_instance, 'object_type', None) != 'expense':
        return approver
    db_type = (os.environ.get('PMA_DB_TYPE') or os.environ.get('SUPABASE_DB_TYPE') or 'sp8d').lower()
    if db_type != 'sp8d':
        return approver
    ceo = (User.query.filter_by(company_name=approver.company_name, role='ceo')
                     .filter(User.id != approver.id).first()
           or User.query.filter_by(role='ceo').filter(User.id != approver.id).first())
    if ceo:
        current_app.logger.info(
            f"[CN报销] 上级审批人为营销总监 {approver.username}, 按规则上提到总经理 {ceo.username}")
        return ceo
    return approver


def get_step_actual_approver(step, approval_instance):
    """获取审批步骤的实际审批人

    根据步骤配置和审批实例上下文，动态确定实际的审批人。

    Args:
        step: ApprovalStep对象或步骤字典（来自模板快照）
        approval_instance: ApprovalInstance对象

    Returns:
        User对象或None
    """
    from app.models.user import User

    # 转交检查: 当前实例当前步骤被代理时, 返回 delegated_to 用户(优先级最高)
    # 注意: 流程推进到下一步时 process_approval 会清空这 3 个字段, 所以代理只对当前步骤生效
    if approval_instance is not None and getattr(approval_instance, 'delegated_to_id', None):
        delegated = User.query.get(approval_instance.delegated_to_id)
        if delegated:
            return delegated
    
    # 获取步骤信息
    if isinstance(step, dict):
        # 从模板快照中获取
        approver_type = step.get('approver_type', 'user')
        approver_user_id = step.get('approver_user_id')
        approver_role = step.get('approver_role')  # 角色类型审批人
        action_type = step.get('action_type')
        # 模板快照里 step 的真实 ID key 是 'step_id'(不是 'id')— 召回快照写入时统一用 step_id
        step_id = step.get('step_id', step.get('id', 'unknown'))
        step_name = step.get('step_name', 'unknown')
    else:
        # 从ApprovalStep对象获取
        approver_type = step.approver_type or 'user'
        approver_user_id = step.approver_user_id
        approver_role = getattr(step, 'approver_role', None)  # 角色类型审批人
        action_type = step.action_type
        step_id = step.id
        step_name = step.step_name
    
    
    # 获取审批发起人作为上下文用户
    context_user = User.query.get(approval_instance.created_by)

    # 🔥 检查是否有特殊的上下文用户ID（用于归属人上级审批等场景）
    # 如果步骤数据中包含 context_user_id，则使用该用户作为上级计算的基础
    step_context_user_id = None
    if isinstance(step, dict):
        step_context_user_id = step.get('context_user_id')

    # 如果是项目相关的审批，获取项目类型
    project_type = None
    if approval_instance.object_type == 'project':
        project = Project.query.get(approval_instance.object_id)
        if project:
            project_type = project.project_type

    # 根据审批人类型确定实际审批人
    if approver_type == 'next_level':
        # 上一级领导
        # 如果步骤有 context_user_id（如归属人上级审批），则基于该用户计算上级
        # 否则基于审批发起人计算上级
        if step_context_user_id:
            context_user_for_next_level = User.query.get(step_context_user_id)
            if context_user_for_next_level:
                current_app.logger.info(f"使用归属人 {context_user_for_next_level.username} 计算上级审批人")
                result = get_next_level_approver(context_user_for_next_level)
                return _expense_next_level_bump(result, approval_instance)
            else:
                current_app.logger.warning(f"步骤 context_user_id={step_context_user_id} 对应的用户不存在，回退到发起人")
        result = get_next_level_approver(context_user)
        return _expense_next_level_bump(result, approval_instance)
    elif approver_type == 'auto' or action_type == 'authorization':
        # 自动选择：基于项目类型确定（主要用于授权）
        if project_type:
            result = get_authorization_approver_by_project_type(project_type)
            return result
    elif approver_type == 'user' and approver_user_id:
        # 固定用户
        result = User.query.get(approver_user_id)
        return result
    elif approver_type == 'role' and approver_role:
        # 按角色确定审批人（查找第一个具有该角色且活跃的用户）
        result = User.query.filter_by(role=approver_role, is_active=True).first()
        return result
    elif approver_type == 'branch':
        # 分支决策：根据条件确定审批人
        result = get_branch_approver(step, approval_instance)
        return result
    elif approver_type == 'submitter_designate':
        # 提交时由提交者指定 — 从 approval_instance.designated_approvers 取
        # designated_approvers JSON 格式: {str(step_id): user_id, ...}
        designated = getattr(approval_instance, 'designated_approvers', None) or {}
        # step_id 在 step dict / Step 对象上都叫 'step_id' 或 'id'
        key = str(step_id) if step_id != 'unknown' else None
        user_id = designated.get(key) if key else None
        if not user_id and isinstance(step, dict):
            # 兼容快照里用 step_order 当 key 的情况
            order_key = str(step.get('step_order') or '')
            if order_key:
                user_id = designated.get(order_key)
        if user_id:
            result = User.query.get(int(user_id))
            if result:
                return result
        current_app.logger.warning(
            f"submitter_designate 步骤未找到指定审批人: step_id={step_id} designated={designated}"
        )
        return None

    current_app.logger.warning(f"无法确定步骤审批人: approver_type={approver_type}, approver_user_id={approver_user_id}, approver_role={approver_role}")
    return None

# 对象类型到模型类的映射配置
BRANCH_OBJECT_TYPE_MAPPING = {
    'project': 'app.models.project.Project',
    'pricing_order': 'app.models.pricing_order.PricingOrder',
    'quotation': 'app.models.quotation.Quotation',
    'customer': 'app.models.company.Company',
    'expense': 'app.models.expense.Expense',
}

# 字段映射配置 - 处理不同对象类型的字段差异
BRANCH_FIELD_MAPPING = {
    'pricing_order': {
        # 移除错误映射，批价单分支条件将直接查询关联项目的真实project_type
        # 'project_type': 'approval_flow_type'  # 已废弃：错误的V1兼容映射
    },
    # 其他类型可以在这里添加字段映射
}

def get_branch_business_object(approval_instance):
    """通用的业务对象获取函数
    
    Args:
        approval_instance: 审批实例对象
        
    Returns:
        业务对象或None
    """
    object_type = approval_instance.object_type
    object_id = approval_instance.object_id
    
    # 获取模型类路径
    model_path = BRANCH_OBJECT_TYPE_MAPPING.get(object_type)
    if not model_path:
        current_app.logger.error(f"不支持的对象类型用于分支决策: {object_type}")
        return None
    
    try:
        # 动态导入模型类
        module_path, class_name = model_path.rsplit('.', 1)
        module = __import__(module_path, fromlist=[class_name])
        model_class = getattr(module, class_name)
        
        # 查询业务对象
        business_object = model_class.query.get(object_id)
        if not business_object:
            current_app.logger.error(f"找不到{object_type}对象: {object_id}")
            return None
            
        return business_object
        
    except Exception as e:
        current_app.logger.error(f"获取{object_type}对象失败: {e}")
        return None

def get_field_value_with_mapping(business_object, field_name, object_type):
    """支持字段映射的字段取值函数
    
    Args:
        business_object: 业务对象
        field_name: 字段名称
        object_type: 对象类型
        
    Returns:
        字段值或None
    """
    
    # 特殊处理：批价单的project_type字段从关联项目获取真实类型
    if object_type == 'pricing_order' and field_name == 'project_type':
        if hasattr(business_object, 'project') and business_object.project:
            field_value = business_object.project.project_type
            return field_value
        else:
            current_app.logger.warning(f"[调试] 批价单没有关联项目，无法获取project_type")
            return None
    
    # 检查是否有字段映射
    field_mappings = BRANCH_FIELD_MAPPING.get(object_type, {})
    actual_field_name = field_mappings.get(field_name, field_name)
    
    
    # 获取字段值
    field_value = getattr(business_object, actual_field_name, None)
    
    # 检查业务对象是否有该字段
    if not hasattr(business_object, actual_field_name):
        current_app.logger.warning(f"[调试] 业务对象没有字段 '{actual_field_name}'")
    
    return field_value

def match_branch_conditions(field_value, branch_condition, object_type):
    """通用的条件匹配函数
    
    Args:
        field_value: 字段值
        branch_condition: 分支条件配置
        object_type: 对象类型（用于日志）
        
    Returns:
        匹配的审批人ID或None
    """
    
    conditions = branch_condition.get('conditions', [])
    
    # 遍历条件列表寻找匹配项
    for i, condition in enumerate(conditions):
        operator = condition.get('operator')
        expected_value = condition.get('value')
        approver_id = condition.get('approver_id')
        condition_id = condition.get('id', f'cond_{i}')
        
        
        match_found = False
        if operator == 'equals' and field_value == expected_value:
            match_found = True
        elif operator == 'in' and field_value == expected_value:
            match_found = True
        elif operator == 'contains' and expected_value in str(field_value):
            match_found = True

        if match_found:
            return approver_id
    
    # 没有匹配条件时检查默认分支
    default_branch = branch_condition.get('default_branch')
    if default_branch:
        default_approver_id = default_branch.get('approver_id')
        default_approver_type = default_branch.get('approver_type')
        
        
        if default_approver_id:
            return default_approver_id
        elif default_approver_type == 'next_branch':
            return None  # 让系统继续到下一个步骤

    current_app.logger.warning(f"[调试] {object_type}未找到匹配的分支条件, 字段值: '{field_value}'")
    return None

def get_branch_approver(step, approval_instance):
    """根据分支条件确定审批人 - 重构版，支持所有对象类型
    
    Args:
        step: 审批步骤对象或字典
        approval_instance: 审批实例对象
        
    Returns:
        User对象或None
    """
    from app.models.user import User
    import json
    
    step_id = step.get('id') if isinstance(step, dict) else getattr(step, 'id', None)
    step_name = step.get('step_name') if isinstance(step, dict) else getattr(step, 'step_name', None)
    
    # 1. 获取分支条件配置
    if isinstance(step, dict):
        branch_condition = step.get('branch_condition')
    else:
        branch_condition = step.branch_condition
    
    
    if not branch_condition:
        object_type = approval_instance.object_type if approval_instance else 'unknown'
        
        current_app.logger.warning(f"分支步骤缺少条件配置 - 步骤ID: {step_id}, 步骤名称: {step_name}, 对象类型: {object_type}")
        return None
    
    # 如果是字符串，解析为JSON
    if isinstance(branch_condition, str):
        try:
            branch_condition = json.loads(branch_condition)
        except json.JSONDecodeError as e:
            current_app.logger.error(f"分支条件JSON解析失败: {e}")
            return None
    
    # 2. 获取业务对象（支持所有对象类型）
    business_object = get_branch_business_object(approval_instance)
    if not business_object:
        current_app.logger.error(f"[调试] 无法获取业务对象: 对象类型={approval_instance.object_type}, 对象ID={approval_instance.object_id}")
        return None
    
    
    # 3. 获取条件字段值（支持字段映射）
    field_name = branch_condition.get('field')
    if not field_name:
        current_app.logger.error(f"分支条件缺少field配置")
        return None
    
    field_value = get_field_value_with_mapping(business_object, field_name, approval_instance.object_type)
    
    # 4. 执行条件匹配
    approver_id = match_branch_conditions(field_value, branch_condition, approval_instance.object_type)
    
    # 5. 返回审批人
    if approver_id:
        result = User.query.get(approver_id)
        return result
    
    current_app.logger.warning(f"[调试] 分支条件匹配未找到审批人")
    return None

def create_or_get_unified_authorization_template():
    """创建或获取统一的动态授权审批模板
    
    此模板名称固定，但审批人根据项目类型动态分配
    
    Returns:
        ApprovalProcessTemplate对象或None
    """
    from app.models.approval import ApprovalProcessTemplate, ApprovalStep
    from app.models.user import User
    
    # 使用固定的模板名称
    template_name = "智能授权审批流程"
    
    # 查找已存在的统一模板
    existing_template = ApprovalProcessTemplate.query.filter_by(
        name=template_name,
        object_type='project'
    ).first()
    
    if existing_template:
        # 如果模板存在但被禁用，重新激活它
        if not existing_template.is_active:
            existing_template.is_active = True
            db.session.commit()
            current_app.logger.info(f"重新激活统一授权审批模板: {template_name}")
        
        return existing_template
    
    try:
        # 获取一个有效的用户ID作为创建者
        admin_user = User.query.filter_by(role='admin').first()
        ceo_user = User.query.filter_by(role='ceo').first()
        creator_id = admin_user.id if admin_user else (ceo_user.id if ceo_user else 1)
        
        # 创建统一的审批流程模板
        template = ApprovalProcessTemplate(
            name=template_name,
            object_type='project',
            created_by=creator_id,
            is_active=True,
            lock_object_on_start=True,
            lock_reason="项目授权编号审批锁定"
        )
        db.session.add(template)
        db.session.flush()  # 获取模板ID
        
        # 创建智能步骤（审批人将在运行时动态分配）
        # 不设置固定的审批人，使用特殊标记表示自动选择
        step = ApprovalStep(
            process_id=template.id,
            step_name="智能授权审批",
            step_order=1,
            approver_user_id=None,  # 不设置固定审批人
            approver_type='auto',   # 标记为自动选择类型
            action_type='authorization',
            send_email=True,
            description="根据项目类型自动分配审批人：渠道跟进→渠道经理，销售重点→营销总监，销售机会→服务经理"
        )
        db.session.add(step)
        db.session.commit()
        
        current_app.logger.info(f"创建统一的智能授权审批流程模板: {template.name}")
        return template
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建统一授权审批流程失败: {str(e)}")
        return None

def get_user_created_approvals(user_id=None, object_type=None, status=None, page=1, per_page=20):
    """获取指定用户发起的审批列表 - 改进版，包含批价单审批，只返回关联业务对象存在的审批

    Args:
        user_id: 用户ID，默认为当前登录用户
        object_type: 过滤特定类型的审批对象
        status: 过滤特定状态的审批，默认为'pending'（只显示审批中的记录）
        page: 页码
        per_page: 每页数量

    Returns:
        分页对象，包含审批实例列表
    """
    if user_id is None:
        user_id = current_user.id

    # 🔥 默认只显示审批中的记录（pending状态），除非明确指定其他状态
    if status is None:
        status = 'pending'

    # 获取当前查询用户的信息，检查是否为商务助理
    from app.models.user import User
    query_user = User.query.get(user_id)
    if not query_user:
        return None

    # "我发起的"页签：只查看自己发起的审批（保持原有功能）
    user_ids_to_query = [user_id]

    # 如果专门查询批价单，使用批价单的独立审批系统
    if object_type == 'pricing_order':
        from app.models.pricing_order import PricingOrder

        query = PricingOrder.query.filter(PricingOrder.created_by.in_(user_ids_to_query))

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

        # 包装分页对象（使用顶部定义的统一PricingOrderApprovalWrapper类）
        wrapped_items = [PricingOrderApprovalWrapper(po) for po in pricing_orders.items]
        pricing_orders.items = wrapped_items

        return pricing_orders

    # 如果专门查询报销单，使用报销单的独立审批系统
    if object_type == 'expense':
        from app.models.expense import Expense

        query = Expense.query.filter(Expense.owner_id.in_(user_ids_to_query))

        # 状态映射 - 修复状态筛选逻辑，优先处理字符串状态
        if status:
            # 如果传入的是字符串状态，直接匹配
            if isinstance(status, str):
                if status.lower() == 'draft':
                    query = query.filter(Expense.status == 'draft')
                elif status.lower() == 'pending':
                    query = query.filter(Expense.status == 'pending')
                elif status.lower() == 'approved':
                    query = query.filter(Expense.status == 'approved')
                elif status.lower() == 'rejected':
                    query = query.filter(Expense.status == 'rejected')
            # 处理ApprovalStatus枚举
            elif status == ApprovalStatus.PENDING:
                query = query.filter(Expense.status == 'pending')
            elif status == ApprovalStatus.APPROVED:
                query = query.filter(Expense.status == 'approved')
            elif status == ApprovalStatus.REJECTED:
                query = query.filter(Expense.status == 'rejected')

        # 按创建时间倒序排列
        query = query.order_by(Expense.created_at.desc())

        # 返回分页结果，需要包装成类似审批实例的格式
        try:
            expenses = query.paginate(page=page, per_page=per_page, error_out=False)
        except Exception as e:
            # 如果分页出错，返回空结果
            try:
                from flask_sqlalchemy import Pagination
            except ImportError:
                from flask_sqlalchemy.pagination import Pagination
            expenses = Pagination(query=query, page=page, per_page=per_page, total=0, items=[])

        # 包装分页对象，只包含应该显示的项目（使用顶部定义的统一ExpenseApprovalWrapper类）
        wrapped_items = []
        for expense in expenses.items:
            wrapper = ExpenseApprovalWrapper(expense)
            if wrapper.should_display:
                wrapped_items.append(wrapper)
        
        # 重新计算分页信息，因为过滤后数量可能改变
        # 获取应该显示的总数 - 使用与分页查询相同的基础查询
        base_query = Expense.query.filter(Expense.owner_id.in_(user_ids_to_query))
        
        # 应用相同的状态过滤逻辑
        if status:
            # 如果传入的是字符串状态，直接匹配
            if isinstance(status, str):
                if status.lower() == 'draft':
                    base_query = base_query.filter(Expense.status == 'draft')
                elif status.lower() == 'pending':
                    base_query = base_query.filter(Expense.status == 'pending')
                elif status.lower() == 'approved':
                    base_query = base_query.filter(Expense.status == 'approved')
                elif status.lower() == 'rejected':
                    base_query = base_query.filter(Expense.status == 'rejected')
            # 处理ApprovalStatus枚举
            elif status == ApprovalStatus.PENDING:
                base_query = base_query.filter(Expense.status == 'pending')
            elif status == ApprovalStatus.APPROVED:
                base_query = base_query.filter(Expense.status == 'approved')
            elif status == ApprovalStatus.REJECTED:
                base_query = base_query.filter(Expense.status == 'rejected')
        
        total_display_count = 0
        for expense in base_query.all():
            wrapper = ExpenseApprovalWrapper(expense)
            if wrapper.should_display:
                total_display_count += 1
        
        # 创建新的分页对象，因为QueryPagination的属性是只读的
        try:
            from flask_sqlalchemy import Pagination
        except ImportError:
            from flask_sqlalchemy.pagination import Pagination
        
        # 创建自定义分页对象
        class CustomPagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = (total + per_page - 1) // per_page if per_page > 0 else 0
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1 if self.has_prev else None
                self.next_num = page + 1 if self.has_next else None
        
        expenses = CustomPagination(wrapped_items, page, per_page, total_display_count)
        
        return expenses
        
    # 基础查询 - 通用审批系统
    query = ApprovalInstance.query.options(db.joinedload(ApprovalInstance.process)).filter(
        ApprovalInstance.created_by.in_(user_ids_to_query)
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
        # 如果没有指定类型，需要合并通用审批和批价单审批
        # 先获取通用审批系统的数据
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
    
    # 状态过滤 - 需要处理字符串状态转换为枚举
    if status:
        if isinstance(status, str):
            # 如果是字符串，尝试转换为枚举
            try:
                from app.models.approval import ApprovalStatus
                if status.lower() == 'pending':
                    query = query.filter(ApprovalInstance.status == ApprovalStatus.PENDING)
                elif status.lower() == 'approved':
                    query = query.filter(ApprovalInstance.status == ApprovalStatus.APPROVED)
                elif status.lower() == 'rejected':
                    query = query.filter(ApprovalInstance.status == ApprovalStatus.REJECTED)
                # 如果不是有效的状态字符串，跳过过滤
            except:
                pass
        else:
            # 如果已经是枚举值，直接使用
            query = query.filter(ApprovalInstance.status == status)
    
    # 按创建时间倒序排列
    query = query.order_by(ApprovalInstance.started_at.desc())
    
    # 如果没有指定object_type，需要合并批价单审批数据
    if not object_type:
        # 获取通用审批系统的分页结果
        general_approvals = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 获取批价单审批数据
        from app.models.pricing_order import PricingOrder
        pricing_query = PricingOrder.query.filter(PricingOrder.created_by.in_(user_ids_to_query))
        
        # 状态过滤
        if status:
            if status == ApprovalStatus.PENDING:
                pricing_query = pricing_query.filter(PricingOrder.status == 'pending')
            elif status == ApprovalStatus.APPROVED:
                pricing_query = pricing_query.filter(PricingOrder.status == 'approved')
            elif status == ApprovalStatus.REJECTED:
                pricing_query = pricing_query.filter(PricingOrder.status == 'rejected')
            elif isinstance(status, str):
                if status.lower() == 'draft':
                    pricing_query = pricing_query.filter(PricingOrder.status == 'draft')
                elif status.lower() == 'pending':
                    pricing_query = pricing_query.filter(PricingOrder.status == 'pending')
                elif status.lower() == 'approved':
                    pricing_query = pricing_query.filter(PricingOrder.status == 'approved')
                elif status.lower() == 'rejected':
                    pricing_query = pricing_query.filter(PricingOrder.status == 'rejected')
        
        # 获取所有批价单，不分页
        all_pricing_orders = pricing_query.order_by(PricingOrder.created_at.desc()).all()
        
        # 创建批价单包装器
        # 包装批价单为审批实例
        wrapped_pricing_orders = [PricingOrderApprovalWrapper(po) for po in all_pricing_orders]
        
        # 获取订单审批数据
        from app.models.inventory import PurchaseOrder
        order_query = PurchaseOrder.query.filter(PurchaseOrder.created_by_id.in_(user_ids_to_query))
        
        # 订单状态过滤
        if status:
            if status == ApprovalStatus.PENDING:
                order_query = order_query.filter(PurchaseOrder.status == 'pending')
            elif status == ApprovalStatus.APPROVED:
                order_query = order_query.filter(PurchaseOrder.status == 'approved')
            elif status == ApprovalStatus.REJECTED:
                order_query = order_query.filter(PurchaseOrder.status == 'rejected')
            elif isinstance(status, str):
                if status.lower() == 'pending':
                    order_query = order_query.filter(PurchaseOrder.status == 'pending')
                elif status.lower() == 'approved':
                    order_query = order_query.filter(PurchaseOrder.status == 'approved')
                elif status.lower() == 'rejected':
                    order_query = order_query.filter(PurchaseOrder.status == 'rejected')
        
        # 获取所有订单，不分页
        all_orders = order_query.order_by(PurchaseOrder.created_at.desc()).all()
        
        # 创建订单包装器
        # 包装订单为审批实例
        wrapped_orders = [OrderApprovalWrapper(order) for order in all_orders]
        
        # 获取报销单审批数据
        from app.models.expense import Expense
        expense_query = Expense.query.filter(Expense.owner_id.in_(user_ids_to_query))
        
        # 报销单状态过滤 - 与其他地方保持一致的逻辑
        if status:
            # 如果传入的是字符串状态，直接匹配
            if isinstance(status, str):
                if status.lower() == 'draft':
                    expense_query = expense_query.filter(Expense.status == 'draft')
                elif status.lower() == 'pending':
                    expense_query = expense_query.filter(Expense.status == 'pending')
                elif status.lower() == 'approved':
                    expense_query = expense_query.filter(Expense.status == 'approved')
                elif status.lower() == 'rejected':
                    expense_query = expense_query.filter(Expense.status == 'rejected')
            # 处理ApprovalStatus枚举
            elif status == ApprovalStatus.PENDING:
                expense_query = expense_query.filter(Expense.status == 'pending')
            elif status == ApprovalStatus.APPROVED:
                expense_query = expense_query.filter(Expense.status == 'approved')
            elif status == ApprovalStatus.REJECTED:
                expense_query = expense_query.filter(Expense.status == 'rejected')
        
        # 获取所有报销单，不分页
        all_expenses = expense_query.order_by(Expense.created_at.desc()).all()
        
        # 创建报销单包装器
        # 包装报销单为审批实例，只包含应该显示的项目
        wrapped_expenses = []
        for expense in all_expenses:
            wrapper = ExpenseApprovalWrapper(expense)  
            if wrapper.should_display:
                wrapped_expenses.append(wrapper)
        
        # 合并四种审批数据并按时间排序
        all_approvals = list(general_approvals.items) + wrapped_pricing_orders + wrapped_orders + wrapped_expenses
        all_approvals.sort(key=lambda x: x.started_at, reverse=True)
        
        # 计算总数
        total_count = general_approvals.total + len(wrapped_pricing_orders) + len(wrapped_orders) + len(wrapped_expenses)
        
        # 手动分页
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_items = all_approvals[start_idx:end_idx]
        
        # 创建自定义分页对象
        class CombinedPagination:
            def __init__(self, page, per_page, total, items):
                self.page = page
                self.per_page = per_page
                self.total = total
                self.items = items
                self.pages = (total + per_page - 1) // per_page if per_page > 0 else 0
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
        
        return CombinedPagination(page, per_page, total_count, paginated_items)
    
    # 返回通用审批系统的分页结果
    return query.paginate(page=page, per_page=per_page, error_out=False)


def get_user_department_approvals(user_id=None, object_type=None, status=None, page=1, per_page=20):
    """获取用户部门内所有审批列表 - 专门为商务助理等角色提供
    
    商务助理可以查看部门内（同公司）所有用户发起的审批流程
    
    Args:
        user_id: 用户ID，默认为当前登录用户
        object_type: 过滤特定类型的审批对象
        status: 过滤特定状态
        page: 页码
        per_page: 每页数量
        
    Returns:
        分页对象，包含部门内所有审批实例列表
    """
    if user_id is None:
        user_id = current_user.id
    
    # 获取当前查询用户的信息，检查是否为商务助理
    from app.models.user import User
    query_user = User.query.get(user_id)
    if not query_user:
        return None
    
    # 只有商务助理等特定角色才能查看部门审批
    if not (query_user.role and query_user.role.strip() == 'business_admin'):
        # 非商务助理返回空结果 - 创建一个简单的空分页对象
        class EmptyPagination:
            def __init__(self):
                self.page = page
                self.per_page = per_page
                self.total = 0
                self.items = []
                self.pages = 1
                self.has_prev = False
                self.has_next = False
                self.prev_num = None
                self.next_num = None
            def iter_pages(self, left_edge=2, right_edge=2, left_current=2, right_current=3):
                return []
        return EmptyPagination()
    
    # 商务助理：查看部门内所有用户发起的审批
    # 如果有部门信息，按部门查询；否则按公司查询
    if query_user.department:
        department_users = User.query.filter_by(department=query_user.department).all()
    elif query_user.company_name:
        department_users = User.query.filter_by(company_name=query_user.company_name).all()
    else:
        # 如果既没有部门也没有公司信息，只能查看自己的
        department_users = [query_user]
    
    user_ids_to_query = [u.id for u in department_users]
    current_app.logger.info(f"商务助理 {query_user.username} 可查看 {len(user_ids_to_query)} 个用户的审批 (部门: {query_user.department}, 公司: {query_user.company_name})")
    
    # 如果专门查询批价单，使用批价单的独立审批系统
    if object_type == 'pricing_order':
        from app.models.pricing_order import PricingOrder
        
        query = PricingOrder.query.filter(PricingOrder.created_by.in_(user_ids_to_query))
        
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
        # 包装分页对象
        wrapped_items = [PricingOrderApprovalWrapper(po) for po in pricing_orders.items]
        pricing_orders.items = wrapped_items
        
        return pricing_orders
        
    # 如果专门查询报销单，使用报销单的独立审批系统
    if object_type == 'expense':
        from app.models.expense import Expense
        
        query = Expense.query.filter(Expense.owner_id.in_(user_ids_to_query))
        
        # 状态映射 - 修复状态筛选逻辑，优先处理字符串状态
        if status:
            # 如果传入的是字符串状态，直接匹配
            if isinstance(status, str):
                if status.lower() == 'draft':
                    query = query.filter(Expense.status == 'draft')
                elif status.lower() == 'pending':
                    query = query.filter(Expense.status == 'pending')
                elif status.lower() == 'approved':
                    query = query.filter(Expense.status == 'approved')
                elif status.lower() == 'rejected':
                    query = query.filter(Expense.status == 'rejected')
            # 处理ApprovalStatus枚举
            elif status == ApprovalStatus.PENDING:
                query = query.filter(Expense.status == 'pending')
            elif status == ApprovalStatus.APPROVED:
                query = query.filter(Expense.status == 'approved')
            elif status == ApprovalStatus.REJECTED:
                query = query.filter(Expense.status == 'rejected')
        
        # 按创建时间倒序排列
        query = query.order_by(Expense.created_at.desc())
        
        # 返回分页结果，需要包装成类似审批实例的格式
        try:
            expenses = query.paginate(page=page, per_page=per_page, error_out=False)
        except Exception as e:
            # 如果分页出错，返回空结果
            try:
                from flask_sqlalchemy import Pagination
            except ImportError:
                from flask_sqlalchemy.pagination import Pagination
            expenses = Pagination(query=query, page=page, per_page=per_page, total=0, items=[])
        
        # 创建虚拟审批实例对象，用于在审批中心显示
        # 包装分页对象，只包含应该显示的项目
        wrapped_items = []
        for expense in expenses.items:
            wrapper = ExpenseApprovalWrapper(expense)
            if wrapper.should_display:
                wrapped_items.append(wrapper)
        
        # 重新计算分页信息，因为过滤后数量可能改变
        # 获取应该显示的总数 - 使用与分页查询相同的基础查询
        base_query = Expense.query.filter(Expense.owner_id.in_(user_ids_to_query))
        
        # 应用相同的状态过滤逻辑
        if status:
            # 如果传入的是字符串状态，直接匹配
            if isinstance(status, str):
                if status.lower() == 'draft':
                    base_query = base_query.filter(Expense.status == 'draft')
                elif status.lower() == 'pending':
                    base_query = base_query.filter(Expense.status == 'pending')
                elif status.lower() == 'approved':
                    base_query = base_query.filter(Expense.status == 'approved')
                elif status.lower() == 'rejected':
                    base_query = base_query.filter(Expense.status == 'rejected')
            # 处理ApprovalStatus枚举
            elif status == ApprovalStatus.PENDING:
                base_query = base_query.filter(Expense.status == 'pending')
            elif status == ApprovalStatus.APPROVED:
                base_query = base_query.filter(Expense.status == 'approved')
            elif status == ApprovalStatus.REJECTED:
                base_query = base_query.filter(Expense.status == 'rejected')
        
        total_display_count = 0
        for expense in base_query.all():
            wrapper = ExpenseApprovalWrapper(expense)
            if wrapper.should_display:
                total_display_count += 1
        
        # 创建新的分页对象，因为QueryPagination的属性是只读的
        try:
            from flask_sqlalchemy import Pagination
        except ImportError:
            from flask_sqlalchemy.pagination import Pagination
        
        # 创建自定义分页对象
        class CustomPagination:
            def __init__(self, items, page, per_page, total):
                self.items = items
                self.page = page
                self.per_page = per_page
                self.total = total
                self.pages = (total + per_page - 1) // per_page if per_page > 0 else 0
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1 if self.has_prev else None
                self.next_num = page + 1 if self.has_next else None
        
        expenses = CustomPagination(wrapped_items, page, per_page, total_display_count)
        
        return expenses
        
    # 基础查询 - 通用审批系统
    query = ApprovalInstance.query.options(db.joinedload(ApprovalInstance.process)).filter(
        ApprovalInstance.created_by.in_(user_ids_to_query)
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
        # 如果没有指定类型，需要合并通用审批和批价单审批
        # 先获取通用审批系统的数据
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
    
    # 状态过滤 - 需要处理字符串状态转换为枚举
    if status:
        if isinstance(status, str):
            # 如果是字符串，尝试转换为枚举
            try:
                if status.lower() == 'pending':
                    query = query.filter(ApprovalInstance.status == ApprovalStatus.PENDING)
                elif status.lower() == 'approved':
                    query = query.filter(ApprovalInstance.status == ApprovalStatus.APPROVED)
                elif status.lower() == 'rejected':
                    query = query.filter(ApprovalInstance.status == ApprovalStatus.REJECTED)
                # 如果不是有效的状态字符串，跳过过滤
            except:
                pass
        else:
            # 如果已经是枚举值，直接使用
            query = query.filter(ApprovalInstance.status == status)
    
    # 按创建时间倒序排列
    query = query.order_by(ApprovalInstance.started_at.desc())
    
    # 如果没有指定object_type，需要合并批价单审批数据
    if not object_type:
        # 获取通用审批系统的分页结果
        general_approvals = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # 获取批价单审批数据
        from app.models.pricing_order import PricingOrder
        pricing_query = PricingOrder.query.filter(PricingOrder.created_by.in_(user_ids_to_query))
        
        # 状态过滤
        if status:
            if status == ApprovalStatus.PENDING:
                pricing_query = pricing_query.filter(PricingOrder.status == 'pending')
            elif status == ApprovalStatus.APPROVED:
                pricing_query = pricing_query.filter(PricingOrder.status == 'approved')
            elif status == ApprovalStatus.REJECTED:
                pricing_query = pricing_query.filter(PricingOrder.status == 'rejected')
            elif isinstance(status, str):
                if status.lower() == 'draft':
                    pricing_query = pricing_query.filter(PricingOrder.status == 'draft')
                elif status.lower() == 'pending':
                    pricing_query = pricing_query.filter(PricingOrder.status == 'pending')
                elif status.lower() == 'approved':
                    pricing_query = pricing_query.filter(PricingOrder.status == 'approved')
                elif status.lower() == 'rejected':
                    pricing_query = pricing_query.filter(PricingOrder.status == 'rejected')
        
        # 获取所有批价单，不分页
        all_pricing_orders = pricing_query.order_by(PricingOrder.created_at.desc()).all()
        
        # 创建批价单包装器
        # 包装批价单为审批实例
        wrapped_pricing_orders = [PricingOrderApprovalWrapper(po) for po in all_pricing_orders]
        
        # 获取订单审批数据
        from app.models.inventory import PurchaseOrder
        order_query = PurchaseOrder.query.filter(PurchaseOrder.created_by_id.in_(user_ids_to_query))
        
        # 订单状态过滤
        if status:
            if status == ApprovalStatus.PENDING:
                order_query = order_query.filter(PurchaseOrder.status == 'pending')
            elif status == ApprovalStatus.APPROVED:
                order_query = order_query.filter(PurchaseOrder.status == 'approved')
            elif status == ApprovalStatus.REJECTED:
                order_query = order_query.filter(PurchaseOrder.status == 'rejected')
            elif isinstance(status, str):
                if status.lower() == 'pending':
                    order_query = order_query.filter(PurchaseOrder.status == 'pending')
                elif status.lower() == 'approved':
                    order_query = order_query.filter(PurchaseOrder.status == 'approved')
                elif status.lower() == 'rejected':
                    order_query = order_query.filter(PurchaseOrder.status == 'rejected')
        
        # 获取所有订单，不分页
        all_orders = order_query.order_by(PurchaseOrder.created_at.desc()).all()
        
        # 创建订单包装器
        # 包装订单为审批实例
        wrapped_orders = [OrderApprovalWrapper(order) for order in all_orders]
        
        # 合并两种审批数据并按时间排序
        all_approvals = list(general_approvals.items) + wrapped_pricing_orders + wrapped_orders
        all_approvals.sort(key=lambda x: x.started_at, reverse=True)
        
        # 计算总数
        total_count = general_approvals.total + len(wrapped_pricing_orders) + len(wrapped_orders)
        
        # 手动分页
        start_index = (page - 1) * per_page
        end_index = start_index + per_page
        paginated_items = all_approvals[start_index:end_index]
        
        # 创建合并的分页对象
        class CombinedPagination:
            def __init__(self, page, per_page, total, items):
                self.page = page
                self.per_page = per_page
                self.total = total
                self.items = items
                self.pages = (total + per_page - 1) // per_page if per_page > 0 else 1
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
        
        return CombinedPagination(page, per_page, total_count, paginated_items)
    
    # 返回通用审批系统的分页结果
    return query.paginate(page=page, per_page=per_page, error_out=False)


# 删除了重复的get_pending_approval_count函数定义
# 保留第3085行的更高效的实现

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
    
    # 获取指定用户的信息
    from app.models.user import User
    target_user = User.query.get(user_id)
    if not target_user:
        # 如果用户不存在，返回空结果
        try:
            from flask_sqlalchemy import Pagination
        except ImportError:
            from flask_sqlalchemy.pagination import Pagination
        return Pagination(None, page=page, per_page=per_page, total=0, items=[])
    
    # 批价单现在使用V2统一审批系统，不再需要专用逻辑
    
    # 通用审批系统查询：找出当前用户是审批人且处于当前审批步骤的所有实例
    # 需要考虑模板快照和当前模板两种情况
    
    # 先获取所有待审批的实例
    base_instances = ApprovalInstance.query.filter(
        ApprovalInstance.status == ApprovalStatus.PENDING
    ).all()
    
    # 筛选出当前用户是当前步骤审批人的实例
    valid_instance_ids = []
    for instance in base_instances:
        current_step_info = instance.get_current_step_info()
        if current_step_info:
            # 使用新的动态审批人确定函数
            actual_approver = get_step_actual_approver(current_step_info, instance)
            
            if actual_approver and actual_approver.id == user_id:
                valid_instance_ids.append(instance.id)
    
    # 基于筛选出的实例ID构建查询
    if valid_instance_ids:
        query = ApprovalInstance.query.options(db.joinedload(ApprovalInstance.process)).filter(
            ApprovalInstance.id.in_(valid_instance_ids)
        )
    else:
        # 如果没有有效实例，返回空查询
        query = ApprovalInstance.query.filter(ApprovalInstance.id.in_([]))
    
    # 根据业务对象类型添加JOIN条件，确保业务对象存在
    if object_type == 'project':
        query = query.join(Project, ApprovalInstance.object_id == Project.id).filter(
            ApprovalInstance.object_type == 'project'
        )
        
        # 基于部门权限控制，不再使用项目类型过滤
        # 所有用户都可以看到其权限范围内的项目审批，权限由access_control.py统一管理
    elif object_type == 'project_hold':
        # 项目失败/搁置审核(object_id 关联 Project)
        query = query.join(Project, ApprovalInstance.object_id == Project.id).filter(
            ApprovalInstance.object_type == 'project_hold'
        )
    elif object_type == 'project_win_lock':
        # 项目成功锁定审核(object_id 关联 Project)
        query = query.join(Project, ApprovalInstance.object_id == Project.id).filter(
            ApprovalInstance.object_type == 'project_win_lock'
        )
    elif object_type == 'quotation':
        query = query.join(Quotation, ApprovalInstance.object_id == Quotation.id).filter(
            ApprovalInstance.object_type == 'quotation'
        )
    elif object_type == 'customer':
        query = query.join(Company, ApprovalInstance.object_id == Company.id).filter(
            ApprovalInstance.object_type == 'customer'
        )
    elif object_type == 'expense':
        from app.models.expense import Expense
        query = query.join(Expense, ApprovalInstance.object_id == Expense.id).filter(
            ApprovalInstance.object_type == 'expense'
        )
    elif object_type == 'pricing_order':
        from app.models.pricing_order import PricingOrder
        query = query.join(PricingOrder, ApprovalInstance.object_id == PricingOrder.id).filter(
            ApprovalInstance.object_type == 'pricing_order'
        )
    elif object_type == 'rd_product':
        from app.models.dev_product import DevProduct
        query = query.join(DevProduct, ApprovalInstance.object_id == DevProduct.id).filter(
            ApprovalInstance.object_type == 'rd_product'
        )
    # 不指定类型时:通用 —— 直接用 valid_instance_ids(已保证 PENDING + 当前用户是当前步骤审批人)。
    # 不再按 object_type 白名单 JOIN 过滤:旧白名单每加一种审批类型都要手动登记,漏了就静默
    # 从代办消失(project_hold 即如此);且计数 _calculate_pending_approval_count / 移动端
    # _get_pending_instances_for_user 本就是通用的,这里对齐,任何现有/未来类型都不会再漏。
    # (硬删除业务对象的孤儿实例极少,且渲染层会兜底跳过取不到对象的项。)

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
        # 包装分页对象
        wrapped_items = [PricingOrderApprovalWrapper(po) for po in pricing_orders.items]
        pricing_orders.items = wrapped_items
        
        return pricing_orders
    
    # 如果专门查询订单，使用订单的审批系统
    if object_type == 'purchase_order':
        from app.models.inventory import PurchaseOrder
        
        query = PurchaseOrder.query
        
        # 状态映射 - 修复状态筛选逻辑
        if status:
            if status == ApprovalStatus.PENDING:
                query = query.filter(PurchaseOrder.status == 'pending')
            elif status == ApprovalStatus.APPROVED:
                query = query.filter(PurchaseOrder.status == 'approved')
            elif status == ApprovalStatus.REJECTED:
                query = query.filter(PurchaseOrder.status == 'rejected')
            # 如果传入的是字符串状态，直接匹配
            elif isinstance(status, str):
                if status.lower() == 'draft':
                    query = query.filter(PurchaseOrder.status == 'draft')
                elif status.lower() == 'pending':
                    query = query.filter(PurchaseOrder.status == 'pending')
                elif status.lower() == 'approved':
                    query = query.filter(PurchaseOrder.status == 'approved')
                elif status.lower() == 'rejected':
                    query = query.filter(PurchaseOrder.status == 'rejected')
        
        # 按创建时间倒序排列
        query = query.order_by(PurchaseOrder.created_at.desc())
        
        # 返回分页结果，需要包装成类似审批实例的格式
        try:
            orders = query.paginate(page=page, per_page=per_page, error_out=False)
        except Exception as e:
            # 如果分页出错，返回空结果
            try:
                from flask_sqlalchemy import Pagination
            except ImportError:
                from flask_sqlalchemy.pagination import Pagination
            orders = Pagination(query=query, page=page, per_page=per_page, total=0, items=[])
        
        # 使用已定义的OrderApprovalWrapper类
        
        # 包装分页对象
        wrapped_items = [OrderApprovalWrapper(order) for order in orders.items]
        orders.items = wrapped_items
        
        return orders
    
    # 通用审批系统
    query = ApprovalInstance.query.options(db.joinedload(ApprovalInstance.process))
    
    # 根据业务对象类型添加JOIN条件，确保业务对象存在
    if object_type == 'project':
        query = query.join(Project, ApprovalInstance.object_id == Project.id).filter(
            ApprovalInstance.object_type == 'project'
        )
        
        # 应用状态过滤器
        if status:
            query = query.filter(ApprovalInstance.status == status)
        
        # 按创建时间倒序排列并返回分页结果
        query = query.order_by(ApprovalInstance.started_at.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)
        
    elif object_type == 'quotation':
        query = query.join(Quotation, ApprovalInstance.object_id == Quotation.id).filter(
            ApprovalInstance.object_type == 'quotation'
        )
        
        # 应用状态过滤器
        if status:
            query = query.filter(ApprovalInstance.status == status)
        
        # 按创建时间倒序排列并返回分页结果
        query = query.order_by(ApprovalInstance.started_at.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)
        
    elif object_type == 'customer':
        query = query.join(Company, ApprovalInstance.object_id == Company.id).filter(
            ApprovalInstance.object_type == 'customer'
        )

        # 应用状态过滤器
        if status:
            query = query.filter(ApprovalInstance.status == status)

        # 按创建时间倒序排列并返回分页结果
        query = query.order_by(ApprovalInstance.started_at.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)
    elif object_type == 'rd_product':
        from app.models.dev_product import DevProduct
        query = query.join(DevProduct, ApprovalInstance.object_id == DevProduct.id).filter(
            ApprovalInstance.object_type == 'rd_product'
        )

        # 应用状态过滤器
        if status:
            query = query.filter(ApprovalInstance.status == status)

        # 按创建时间倒序排列并返回分页结果
        query = query.order_by(ApprovalInstance.started_at.desc())
        return query.paginate(page=page, per_page=per_page, error_out=False)
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

        from app.models.dev_product import DevProduct
        rd_product_subquery = db.session.query(ApprovalInstance.id).filter(
            ApprovalInstance.object_type == 'rd_product'
        ).join(DevProduct, ApprovalInstance.object_id == DevProduct.id)

        # 只查询存在于任一子查询中的审批实例
        query = query.filter(
            or_(
                ApprovalInstance.id.in_(project_subquery),
                ApprovalInstance.id.in_(quotation_subquery),
                ApprovalInstance.id.in_(customer_subquery),
                ApprovalInstance.id.in_(rd_product_subquery)
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
        # 包装批价单数据
        wrapped_pricing_orders = [PricingOrderApprovalWrapper(po) for po in all_pricing_orders]
        
        # 获取订单数据并包装
        from app.models.inventory import PurchaseOrder
        order_query = PurchaseOrder.query
        
        # 状态过滤
        if status:
            if status == ApprovalStatus.PENDING:
                order_query = order_query.filter(PurchaseOrder.status == 'pending')
            elif status == ApprovalStatus.APPROVED:
                order_query = order_query.filter(PurchaseOrder.status == 'approved')
            elif status == ApprovalStatus.REJECTED:
                order_query = order_query.filter(PurchaseOrder.status == 'rejected')
            elif isinstance(status, str):
                if status.lower() == 'draft':
                    order_query = order_query.filter(PurchaseOrder.status == 'draft')
                elif status.lower() == 'pending':
                    order_query = order_query.filter(PurchaseOrder.status == 'pending')
                elif status.lower() == 'approved':
                    order_query = order_query.filter(PurchaseOrder.status == 'approved')
                elif status.lower() == 'rejected':
                    order_query = order_query.filter(PurchaseOrder.status == 'rejected')
        
        order_query = order_query.order_by(PurchaseOrder.created_at.desc())
        
        # 获取所有订单（不分页，稍后合并时再分页）
        try:
            all_orders = order_query.all()
        except Exception as e:
            all_orders = []
        
        # 创建订单包装对象
        # 包装订单数据
        wrapped_orders = [OrderApprovalWrapper(order) for order in all_orders]
        
        # 合并数据：将批价单数据和订单数据添加到通用审批数据中
        combined_items = list(general_approvals.items) + wrapped_pricing_orders + wrapped_orders
        
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
            
        total_count = general_approvals.total + len(all_pricing_orders) + len(all_orders)
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
    # 检查是否为订单包装对象的字符串ID
    if isinstance(instance_id, str) and instance_id.startswith('order_'):
        # 订单包装对象，抛出404错误（订单审批详情需要通过订单详情页查看）
        from flask import abort
        abort(404)
    
    # 检查是否为合法的整数ID
    if not isinstance(instance_id, int):
        from flask import abort
        abort(404)
    
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
        return url_for('pricing_order.at_edit_pricing_order', order_id=object_id)
    elif object_type == 'purchase_order':
        return url_for('purchase_order.at_detail_view', order_id=object_id)
    elif object_type == 'expense':
        return url_for('expense.expense_detail', id=object_id, from_approval='true')
    elif object_type == 'rd_product':
        # 研发产品蓝图已停用，返回首页
        return url_for('main.index')
    else:
        return url_for('main.index')


def get_current_step_info(instance):
    """获取当前步骤信息
    
    Args:
        instance: 审批实例对象
        
    Returns:
        当前步骤对象，如果没有则返回None
    """
    # 处理订单包装对象的特殊情况
    if hasattr(instance, 'id') and isinstance(instance.id, str) and instance.id.startswith('order_'):
        # OrderApprovalWrapper对象，查找对应的审批实例
        if hasattr(instance, 'order'):
            order = instance.order
            if order.status == 'pending':
                # 查找对应的审批实例
                approval_instance = ApprovalInstance.query.filter_by(
                    object_type='purchase_order',
                    object_id=order.id,
                    status=ApprovalStatus.PENDING
                ).first()
                
                if approval_instance:
                    # 获取当前步骤
                    return ApprovalStep.query.filter_by(
                        id=approval_instance.current_step
                    ).first()
        return None
    
    # 🔥 修复：处理报销单包装对象的特殊情况
    if hasattr(instance, 'expense') and hasattr(instance, 'real_approval_instance_id'):
        # ExpenseApprovalWrapper对象，如果有真实的审批实例ID，则使用它
        if instance.real_approval_instance_id:
            approval_instance = ApprovalInstance.query.get(instance.real_approval_instance_id)
            if approval_instance:
                # 递归调用获取当前步骤信息（使用真实的审批实例）
                return approval_instance.get_current_step_info()
        return None
    
    # 批价单现在使用V2统一审批系统，不需要特殊处理
    
    # 处理通用审批系统
    if not instance or instance.status != ApprovalStatus.PENDING:
        return None
    
    # 🔥 关键修复：优先使用模板快照中的步骤信息，并处理类型问题
    if instance.template_snapshot:
        # 处理template_snapshot可能是字符串的情况
        snapshot_data = instance.template_snapshot
        if isinstance(snapshot_data, str):
            try:
                import json
                snapshot_data = json.loads(snapshot_data)
                current_app.logger.warning(f"审批实例 {instance.id} 的template_snapshot是字符串，已转换为字典")
            except (json.JSONDecodeError, TypeError) as e:
                current_app.logger.error(f"审批实例 {instance.id} 的template_snapshot字符串解析失败: {e}")
                snapshot_data = None
        
        if snapshot_data and isinstance(snapshot_data, dict) and 'steps' in snapshot_data:
            # 从模板快照中获取当前步骤信息
            steps_data = snapshot_data['steps']
            current_step_data = None

            # 🔥 修复：current_step 可能是 step_order 或 step_id，需要智能匹配
            # 优先 step_order 匹配，失败则用 step_id 匹配
            for step_data in steps_data:
                if step_data.get('step_order') == instance.current_step:
                    current_step_data = step_data
                    break
            # 如果 step_order 匹配不到，尝试用 step_id 匹配（兼容历史数据）
            if not current_step_data:
                for step_data in steps_data:
                    if step_data.get('step_id') == instance.current_step:
                        current_step_data = step_data
                        break
        
        if current_step_data:
            # 创建虚拟步骤对象，包含快照中的正确信息
            from app.models.user import User
            approver = User.query.get(current_step_data.get('approver_user_id'))
            
            # 🔥 修复：如果审批人未分配（ID为None），尝试重新计算审批人
            if not current_step_data.get('approver_user_id') and current_step_data.get('approver_type'):
                approver_type = current_step_data.get('approver_type')
                if approver_type in ['next_level', 'branch']:
                    # 尝试重新计算审批人
                    try:
                        actual_approver = get_step_actual_approver(current_step_data, instance)
                        if actual_approver:
                            approver = actual_approver
                            current_app.logger.info(f"重新计算审批人成功：{approver.username} (类型: {approver_type})")
                        else:
                            current_app.logger.warning(f"重新计算审批人失败，审批实例 {instance.id}，步骤 {current_step_data.get('step_order')}，类型: {approver_type}")
                    except Exception as e:
                        current_app.logger.error(f"重新计算审批人时出错：{e}")
                        import traceback
                        current_app.logger.error(traceback.format_exc())
            
            # 如果无法从数据库获取审批人，创建虚拟审批人对象
            if not approver and current_step_data.get('approver_user_id'):
                approver = type('VirtualUser', (), {
                    'id': current_step_data.get('approver_user_id'),
                    'username': current_step_data.get('approver_username', '未知用户'),
                    'real_name': current_step_data.get('approver_real_name', ''),
                    'role': current_step_data.get('approver_role', ''),
                })()
                current_app.logger.warning(f"审批人ID {current_step_data.get('approver_user_id')} 在数据库中不存在，创建虚拟审批人对象")
            
            virtual_step = type('Step', (), {
                'id': f"snapshot_step_{instance.id}_{current_step_data['step_order']}",
                'step_name': current_step_data.get('step_name', '未知步骤'),
                'step_order': current_step_data.get('step_order'),
                'approver_user_id': approver.id if approver else current_step_data.get('approver_user_id'),
                'approver_type': current_step_data.get('approver_type', 'user'),  # 🔥 修复：添加缺失的属性
                'approver': approver,
                'action_type': current_step_data.get('action_type'),
                'send_email': current_step_data.get('send_email', True),
                'description': current_step_data.get('description', ''),
                'process_id': instance.process_id,
                'branch_condition': current_step_data.get('branch_condition'),  # 🔥 修复：添加分支条件属性
                'step_type': current_step_data.get('step_type', 'normal'),  # 🔥 修复：添加步骤类型属性
                # 添加额外的快照信息
                'approver_username': approver.username if approver else current_step_data.get('approver_username'),
                'approver_real_name': approver.real_name if approver and hasattr(approver, 'real_name') else current_step_data.get('approver_real_name')
            })()
            
            current_app.logger.info(f"使用模板快照获取步骤信息 - 审批实例 {instance.id}，步骤 {instance.current_step}，审批人: {current_step_data.get('approver_username')} (ID: {current_step_data.get('approver_user_id')})")
            return virtual_step
    
    # 回退：如果没有快照或快照中没有步骤信息，使用数据库中的模板步骤（兼容旧数据）
    current_app.logger.warning(f"模板快照不可用，回退到数据库模板 - 审批实例 {instance.id}")
    steps = ApprovalStep.query.filter_by(
        id=instance.current_step
    ).first()
    
    return steps


def get_last_approver(instance):
    """获取最后一个审批人（用于已结束的审批流程）
    
    Args:
        instance: 审批实例对象
        
    Returns:
        最后一个审批人的用户对象，如果没有则返回None
    """
    # 处理订单包装对象的特殊情况
    if hasattr(instance, 'id') and isinstance(instance.id, str) and instance.id.startswith('order_'):
        # OrderApprovalWrapper对象，暂时返回None（订单审批人从订单记录获取）
        if hasattr(instance, 'order') and hasattr(instance.order, 'approved_by'):
            return instance.order.approved_by
        return None
    
    # 处理批价单的特殊情况 - 现在使用V2统一审批系统
    if hasattr(instance, 'object_type') and instance.object_type == 'pricing_order':
        # V2系统：批价单审批记录存储在通用ApprovalRecord表中
        if hasattr(instance, 'id') and isinstance(instance.id, int):
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
    
    # 处理通用审批系统
    if not instance:
        return None
    
    # 检查instance.id是否为合法的整数
    if not isinstance(instance.id, int):
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
    # 检查是否为订单包装对象的字符串ID
    if isinstance(instance_id, str) and instance_id.startswith('order_'):
        # 订单包装对象，返回空列表（订单审批记录在ApprovalRecord表中按真实实例ID存储）
        return []
    
    # 检查是否为合法的整数ID
    if not isinstance(instance_id, int):
        return []
    
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
    
    # 检查是否为订单包装对象的字符串ID
    if isinstance(instance_id, str) and instance_id.startswith('order_'):
        # 订单包装对象，需要查找真实的审批实例
        try:
            order_id = int(instance_id.replace('order_', ''))
            instance = ApprovalInstance.query.filter_by(
                object_type='purchase_order',
                object_id=order_id,
                status=ApprovalStatus.PENDING
            ).first()
        except ValueError:
            return False
    else:
        # 检查是否为合法的整数ID
        if not isinstance(instance_id, int):
            return False
        instance = ApprovalInstance.query.get(instance_id)
    
    if not instance or instance.status != ApprovalStatus.PENDING:
        return False
    
    # 获取当前步骤 - 修复：使用模板快照
    current_step = instance.get_current_step_info()
    if not current_step:
        return False
    
    # 使用新的动态审批人确定函数
    actual_approver = get_step_actual_approver(current_step, instance)
    return actual_approver and actual_approver.id == user_id

# ----- 以下是审批流程配置模块需要的函数 ----- #

def get_designate_steps_info(template_id):
    """返回模板中 approver_type='submitter_designate' 的步骤 + 候选审批人列表。

    用途:提交审批前,前端拿到这个列表展示「选择审批人」对话框,
         用户为每个 submitter_designate 步骤选定 user_id。

    Returns:
        list[dict]: [{step_id, step_name, step_order, pool, candidates: [{id, name, role}]}]
    """
    from app.models.approval import ApprovalStep
    from app.models.user import User
    out = []
    steps = ApprovalStep.query.filter_by(
        process_id=template_id, approver_type='submitter_designate'
    ).order_by(ApprovalStep.step_order.asc()).all()
    for s in steps:
        pool = s.designate_pool or {}
        roles = pool.get('roles') or []
        companies = pool.get('companies') or []
        # 兼容旧字段名(早期版本叫 departments,现已改为 companies)
        if not companies:
            companies = pool.get('departments') or []
        # 注意:User.is_active 是 hybrid property,filter 必须用底层列 User._is_active
        # 参见 memory feedback_systematic_patterns
        q = User.query.filter(User._is_active == True)  # noqa: E712
        if roles:
            q = q.filter(User.role.in_(roles))
        if companies:
            q = q.filter(User.company_name.in_(companies))
        candidates = [{
            'id': u.id,
            'name': u.real_name or u.username,
            'role': u.role or '',
            'company': u.company_name or '',
        } for u in q.order_by(User.real_name.asc()).limit(200).all()]
        out.append({
            'step_id': s.id,
            'step_name': s.step_name,
            'step_order': s.step_order,
            'pool': pool,
            'candidates': candidates,
        })
    return out


def get_approval_templates(page=1, per_page=10, object_type=None, is_active=None, search=None, creator_id=None):
    """获取审批流程模板列表

    Args:
        page: 页码
        per_page: 每页数量
        object_type: 过滤特定类型的审批对象
        is_active: 是否只返回启用的模板
        search: 搜索关键字（模板名称）
        creator_id: 过滤特定创建人的模板

    Returns:
        分页对象，包含审批流程模板列表
    """
    query = ApprovalProcessTemplate.query

    if object_type:
        query = query.filter(ApprovalProcessTemplate.object_type == object_type)

    if is_active is not None:
        query = query.filter(ApprovalProcessTemplate.is_active == is_active)

    if search:
        query = query.filter(ApprovalProcessTemplate.name.ilike(f'%{search}%'))

    if creator_id:
        query = query.filter(ApprovalProcessTemplate.created_by == creator_id)

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
                'started_at': safe_strftime(instance.started_at, '%Y-%m-%d %H:%M') if instance.started_at else '未知'
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


def add_approval_step(template_id, step_name, approver_id, send_email=True, editable_fields=None, cc_users=None, cc_enabled=False, approver_type='user', step_type='normal', branch_condition=None, parent_step_id=None, is_parallel=False, branch_group_id=None, branch_level=0, branch_path=None, merge_step_id=None, execution_condition=None):
    """添加审批步骤

    Args:
        template_id: 模板ID
        step_name: 步骤名称
        approver_id: 审批人ID
        send_email: 是否发送邮件通知
        editable_fields: 在此步骤可编辑的字段列表
        cc_users: 抄送用户ID列表
        cc_enabled: 是否启用抄送
        approver_type: 审批人类型 ('user', 'next_level', 'auto')
        step_type: 步骤类型 ('normal', 'branch')
        branch_condition: 分支条件配置
        parent_step_id: 上级步骤ID（用于并行分支）
        is_parallel: 是否为并行分支
        execution_condition: 步骤执行条件（JSON），满足条件时才执行此步骤

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
        approver_type=approver_type,
        step_name=step_name,
        send_email=send_email,
        editable_fields=editable_fields,
        cc_users=cc_users,
        cc_enabled=cc_enabled,
        step_type=step_type,
        branch_condition=branch_condition,
        parent_step_id=parent_step_id,
        is_parallel=is_parallel,
        branch_group_id=branch_group_id,
        branch_level=branch_level,
        branch_path=branch_path,
        merge_step_id=merge_step_id,
        execution_condition=execution_condition
    )
    
    db.session.add(step)
    db.session.commit()
    
    return step


_UNSET = object()  # 哨兵值：区分"不更新"和"设为None"

def update_approval_step(step_id, step_name=None, approver_id=None, send_email=None, editable_fields=None, cc_users=None, cc_enabled=None, update_approver=False, approver_type=None, execution_condition=_UNSET):
    """更新审批步骤

    Args:
        step_id: 步骤ID
        step_name: 步骤名称
        approver_id: 审批人ID（可以为None）
        send_email: 是否发送邮件通知
        editable_fields: 在此步骤可编辑的字段列表
        cc_users: 抄送用户ID列表
        cc_enabled: 是否启用抄送
        update_approver: 是否更新审批人（用于区分None值和不更新）
        approver_type: 审批人类型 ('user', 'next_level', 'auto')
        execution_condition: 执行条件（dict或None表示清空，_UNSET表示不更新）

    Returns:
        更新后的步骤对象，如果没有找到则返回None
    """
    step = ApprovalStep.query.get(step_id)
    if not step:
        return None

    if step_name is not None:
        step.step_name = step_name

    # 只有在明确指定更新审批人时才更新，允许设置为None
    if update_approver:
        step.approver_user_id = approver_id

    if approver_type is not None:
        step.approver_type = approver_type

    if send_email is not None:
        step.send_email = send_email

    if editable_fields is not None:
        step.editable_fields = editable_fields

    if cc_users is not None:
        step.cc_users = cc_users

    if cc_enabled is not None:
        step.cc_enabled = cc_enabled

    # execution_condition: _UNSET=不更新, None=清空条件, dict=设置条件
    if execution_condition is not _UNSET:
        step.execution_condition = execution_condition

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
    if force:
        current_app.logger.info(f"强制删除审批步骤 (快照机制保护运行中流程): {step.step_name} (ID: {step_id})")
    else:
        current_app.logger.info(f"删除审批步骤: {step.step_name} (ID: {step_id})")
    
    # 执行删除
    current_order = step.step_order
    
    # 先删除相关的分支条件记录（避免外键约束错误）
    from app.models.approval_branch_condition import ApprovalBranchCondition
    branch_conditions = ApprovalBranchCondition.query.filter_by(step_id=step_id).all()
    if branch_conditions:
        current_app.logger.info(f"删除步骤 {step_id} 的 {len(branch_conditions)} 个分支条件记录")
        for condition in branch_conditions:
            db.session.delete(condition)
    
    # 删除审批步骤
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
        ('customer', '客户'),
        ('purchase_order', '订单'),
        ('expense', '报销单'),
        ('settlement', '结算单'),
        ('pricing_order', '批价单'),
        ('standard_product', '标准产品'),
        ('rd_product', '研发产品'),
        ('product_analysis', '产品分析'),
        ('inventory_stock', '库存'),
        ('performance_target', '绩效目标'),
        ('user', '用户'),
        ('department', '部门')
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
        'purchase_order': '订单',
        'expense': '报销单',
        'settlement': '结算单',
        'pricing_order': '批价单',
        'standard_product': '标准产品',
        'rd_product': '研发产品',
        'product_analysis': '产品分析',
        'inventory_stock': '库存',
        'performance_target': '绩效目标',
        'perf_settlement': '绩效结算',
        'salary_run': '月度薪资审批',
        'dealer_apply': '客户渠道身份',
        'project_hold': '项目失败/搁置',
        'project_win_lock': '项目成功锁定',
        'user': '用户',
        'department': '部门'
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


def check_template_has_instances(template_id):
    """检查审批流程模板是否有任何相关联的审批实例（用于模板列表显示）
    
    Args:
        template_id: 模板ID
        
    Returns:
        布尔值，表示模板是否有任何关联的审批实例
    """
    return ApprovalInstance.query.filter_by(process_id=template_id).first() is not None


def get_object_approval_instance(object_type, object_id, include_rejected=False):
    """获取业务对象的审批实例
    
    Args:
        object_type: 业务对象类型
        object_id: 业务对象ID
        include_rejected: 是否包含被拒绝的实例
        
    Returns:
        对应的审批实例，如果没有则返回None
    """
    try:
        # 强制确保数据库连接正常，多次尝试回滚
        for i in range(3):  # 尝试3次
            try:
                db.session.rollback()
                break
            except Exception as e:
                if i == 2:  # 最后一次尝试失败
                    current_app.logger.error(f"数据库回滚失败: {e}")
                continue
    except Exception:
        pass
    
    try:
        # 优先查找最新的PENDING实例
        pending_instance = ApprovalInstance.query.filter_by(
            object_type=object_type,
            object_id=object_id,
            status=ApprovalStatus.PENDING
        ).order_by(ApprovalInstance.started_at.desc()).first()
        
        if pending_instance:
            return pending_instance
        
        # 如果没有PENDING实例，查找最新的APPROVED实例（已通过的实例应优先显示）
        approved_instance = ApprovalInstance.query.filter_by(
            object_type=object_type,
            object_id=object_id,
            status=ApprovalStatus.APPROVED
        ).order_by(ApprovalInstance.started_at.desc()).first()
        
        if approved_instance:
            return approved_instance
        
        # 如果没有APPROVED实例，查找最新的REJECTED实例（拒绝状态优先于召回）
        rejected_instance = ApprovalInstance.query.filter_by(
            object_type=object_type,
            object_id=object_id,
            status=ApprovalStatus.REJECTED
        ).order_by(ApprovalInstance.started_at.desc()).first()
        
        if rejected_instance:
            return rejected_instance
        
        # 最后查找最新的RECALLED实例（已召回的实例优先级最低）
        recalled_instance = ApprovalInstance.query.filter_by(
            object_type=object_type,
            object_id=object_id,
            status=ApprovalStatus.RECALLED
        ).order_by(ApprovalInstance.started_at.desc()).first()
        
        if recalled_instance:
            return recalled_instance
        
        # include_rejected参数现在不再需要，因为REJECTED实例总是被优先返回
        
        # 没有找到任何实例，允许重新发起审批
        return None
        
    except Exception as e:
        # 数据库查询失败时，回滚事务并返回None
        current_app.logger.error(f"获取审批实例失败: {e}")
        try:
            db.session.rollback()
        except Exception:
            pass
        return None


def get_object_approval_instances_batch(object_type, object_ids):
    """批量获取多个业务对象的审批实例

    用一次 IN 查询获取所有相关审批实例，然后按状态优先级选出最优实例。
    状态优先级：PENDING > APPROVED > REJECTED > RECALLED
    与 get_object_approval_instance() 保持完全一致的选择逻辑。

    Args:
        object_type: 业务对象类型（如 'expense'）
        object_ids: 业务对象ID列表

    Returns:
        dict: { object_id: ApprovalInstance 或 None }
    """
    if not object_ids:
        return {}

    result = {oid: None for oid in object_ids}

    try:
        # 一次查询获取所有相关审批实例
        all_instances = ApprovalInstance.query.filter(
            ApprovalInstance.object_type == object_type,
            ApprovalInstance.object_id.in_(object_ids)
        ).order_by(ApprovalInstance.started_at.desc()).all()

        # 按 object_id 分组
        from collections import defaultdict
        instances_by_id = defaultdict(list)
        for inst in all_instances:
            instances_by_id[inst.object_id].append(inst)

        # 状态优先级映射（值越小优先级越高）
        status_priority = {
            ApprovalStatus.PENDING: 0,
            ApprovalStatus.APPROVED: 1,
            ApprovalStatus.REJECTED: 2,
            ApprovalStatus.RECALLED: 3,
        }

        # 为每个对象选择最优实例
        for oid, instances in instances_by_id.items():
            if not instances:
                continue
            # 按状态优先级排序，同状态按 started_at 倒序（已由查询保证）
            best = min(instances, key=lambda i: status_priority.get(i.status, 99))
            result[oid] = best

    except Exception as e:
        current_app.logger.error(f"批量获取审批实例失败: {e}")
        try:
            db.session.rollback()
        except Exception:
            pass

    return result


def cleanup_duplicate_dynamic_templates():
    """清理重复的动态审批模板
    
    只保留每种项目类型-角色组合的最新模板，将多余的模板标记为不活跃
    """
    try:
        # 查找所有动态创建的模板
        dynamic_templates = ApprovalProcessTemplate.query.filter(
            ApprovalProcessTemplate.name.like('动态授权审批-%')
        ).order_by(ApprovalProcessTemplate.created_at.desc()).all()
        
        # 按模板名称分组
        template_groups = {}
        for template in dynamic_templates:
            if template.name not in template_groups:
                template_groups[template.name] = []
            template_groups[template.name].append(template)
        
        # 清理重复模板
        cleaned_count = 0
        for template_name, templates in template_groups.items():
            if len(templates) > 1:
                # 保留最新的（第一个），禁用其他的
                latest_template = templates[0]
                for duplicate_template in templates[1:]:
                    # 检查是否有正在使用的实例
                    has_pending_instances = ApprovalInstance.query.filter_by(
                        process_id=duplicate_template.id,
                        status=ApprovalStatus.PENDING
                    ).first() is not None
                    
                    if not has_pending_instances:
                        duplicate_template.is_active = False
                        cleaned_count += 1
                        current_app.logger.info(f"已禁用重复的动态模板: {duplicate_template.name} (ID: {duplicate_template.id})")
        
        if cleaned_count > 0:
            db.session.commit()
            current_app.logger.info(f"清理完成，共禁用 {cleaned_count} 个重复的动态模板")
        
        return cleaned_count
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"清理动态模板失败: {str(e)}")
        return 0


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
                            current_app.logger.info(f"保留非授权模板: {template.name} (ID: {template.id})")
                        else:
                            current_app.logger.info(f"过滤授权模板: {template.name} (ID: {template.id})")
                    
                    templates = filtered_templates
        
        # 注释掉按业务类型过滤模板的逻辑，保持所有可用模板对用户可见
        # 智能路由将在审批发起时自动处理，用户界面不需要预先过滤
        # if business_type and templates:
        #     # 检查模板名称是否包含业务类型关键词
        #     filtered_templates = []
        #     for template in templates:
        #         # 审批模板名称中包含业务类型关键词
        #         if business_type in template.name:
        #             filtered_templates.append(template)
        #         # 或者检查模板id，可以添加特定规则
        #     
        #     # 如果过滤后没有模板，则返回原始列表
        #     if filtered_templates:
        #         templates = filtered_templates
    
    return templates


def restart_rejected_approval(object_type, object_id, template_id, user_id=None):
    """重新发起被拒绝的审批流程
    
    Args:
        object_type: 业务对象类型
        object_id: 业务对象ID  
        template_id: 审批流程模板ID
        user_id: 发起人ID，默认为当前登录用户
        
    Returns:
        重新启动的审批实例对象，如果失败则返回None
    """
    # 🔥 关键修复：召回后重新发起时，完全按照新的项目状态重新创建审批实例
    # 不再重用旧实例，避免审批人不更新的问题
    
    # 查找最新的被拒绝实例
    rejected_instance = ApprovalInstance.query.filter_by(
        object_type=object_type,
        object_id=object_id,
        status=ApprovalStatus.REJECTED
    ).order_by(ApprovalInstance.started_at.desc()).first()
    
    if rejected_instance:
        current_app.logger.info(f"发现被拒绝的审批实例 {rejected_instance.id}，将创建新实例而非重用")
        
        # 🔥 修复：删除旧的被拒绝实例，创建全新的实例
        # 这样可以确保重新评估项目类型和审批人
        try:
            # 保留历史记录，但删除实例本身
            old_instance_id = rejected_instance.id
            db.session.delete(rejected_instance)
            db.session.commit()
            
            current_app.logger.info(f"已删除旧的被拒绝实例 {old_instance_id}，将创建新实例")
            
            # 🔥 调用标准的发起流程函数，确保重新评估所有逻辑
            new_instance = start_approval_process(object_type, object_id, template_id, user_id)
            
            if new_instance:
                current_app.logger.info(f"成功创建新的审批实例 {new_instance.id} 替代被拒绝的实例 {old_instance_id}")
                return new_instance
            else:
                current_app.logger.error(f"创建新审批实例失败，尝试恢复旧实例")
                return None
                
        except Exception as e:
            current_app.logger.error(f"重新发起被拒绝的审批失败: {str(e)}")
            db.session.rollback()
            return None
    
    return None


def _get_complete_branch_condition(step):
    """获取完整的分支条件数据
    
    对于分支步骤，从新表获取完整条件数据；
    对于非分支步骤，使用原始数据。
    """
    
    if step.step_type == 'branch' or step.action_type == 'branch_decision':
        
        # 对分支步骤，从新表获取完整条件
        conditions = step.get_branch_conditions()
        
        # 处理每个条件
        for i, cond in enumerate(conditions):
            pass  # 这里原本有调试代码，现在先用pass占位
        
        branch_field = step.get_branch_field() or 'project_type'
        default_branch = step.get_default_branch()
        
        
        legacy_conditions = [cond.to_legacy_format() for cond in conditions]
        
        result = {
            'field': branch_field,
            'conditions': legacy_conditions,
            'default_branch': default_branch
        }
        
        return result
    else:
        # 非分支步骤，使用原始数据
        return step.branch_condition


def start_approval_process(object_type, object_id, template_id, user_id=None,
                            auto_commit=True, designated_approvers=None):
    """发起审批流程

    Args:
        object_type: 业务对象类型
        object_id: 业务对象ID
        template_id: 审批流程模板ID
        user_id: 发起人ID,默认为当前登录用户
        auto_commit: 是否自动提交事务,默认True。
                     设为False时只flush不commit,由调用者统一提交,
                     确保审批实例创建和业务对象状态更新在同一事务中。
        designated_approvers: 提交时指定的审批人 dict {step_id_str: user_id},
                             用于 approver_type='submitter_designate' 的步骤。

    Returns:
        新建的审批实例对象,如果失败则返回None
    """
    # 记录详细的诊断信息
    current_app.logger.info(f"开始发起审批流程: 对象类型={object_type}, 对象ID={object_id}, 模板ID={template_id}")
    
    # 检查是否已存在进行中的审批实例（不包括被拒绝的和已召回的）
    existing = get_object_approval_instance(object_type, object_id, include_rejected=False)
    
    if existing and existing.status not in [ApprovalStatus.RECALLED, ApprovalStatus.REJECTED]:
        status_str = str(existing.status) if hasattr(existing, 'status') else '未知状态'
        current_app.logger.warning(
            f"业务对象已存在审批实例: {object_type}:{object_id}, "
            f"实例ID: {existing.id}, 状态: {status_str}"
        )
        try:
            from flask import flash
            flash(f"发起审批失败，已存在审批流程 (状态: {status_str})", 'danger')
        except RuntimeError:
            # 在非请求上下文中，不使用flash
            current_app.logger.warning(f"无法使用flash消息: 非请求上下文")
        return None
    
    # 如果存在RECALLED或REJECTED状态的实例，记录日志但允许重新发起
    if existing and existing.status in [ApprovalStatus.RECALLED, ApprovalStatus.REJECTED]:
        current_app.logger.info(f"发现已{'召回' if existing.status == ApprovalStatus.RECALLED else '拒绝'}的审批实例: {existing.id}, 允许重新发起审批")
    
    # 检查是否有被拒绝的实例，如果有则删除后重新创建
    rejected_instance = get_object_approval_instance(object_type, object_id, include_rejected=True)
    if rejected_instance and rejected_instance.status == ApprovalStatus.REJECTED:
        current_app.logger.info(f"发现被拒绝的审批实例，将删除并重新创建: 实例ID={rejected_instance.id}")
        
        # 🔥 修复：直接删除被拒绝的实例，确保重新创建
        try:
            old_instance_id = rejected_instance.id
            db.session.delete(rejected_instance)
            db.session.commit()
            current_app.logger.info(f"已删除被拒绝的实例 {old_instance_id}，继续创建新实例")
        except Exception as e:
            current_app.logger.error(f"删除被拒绝实例失败: {str(e)}")
            db.session.rollback()
            from flask import flash
            flash(f"无法删除旧的审批记录: {str(e)}", 'danger')
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
        current_app.logger.warning(f"审批模板已禁用: {template_id}")
        from flask import flash
        flash("发起审批失败，审批模板已被禁用", 'danger')
        return None
    
    if user_id is None:
        user_id = current_user.id
    
    try:
        # 获取模板步骤
        steps = ApprovalStep.query.filter_by(process_id=template_id).order_by(ApprovalStep.step_order).all()
        if not steps:
            current_app.logger.warning(f"审批模板没有配置步骤: {template_id}")
            from flask import flash
            flash("发起审批失败，审批模板未配置审批步骤", 'danger')
            return None
        
        # 🔥 关键修复：创建模板快照，但不修改原模板
        # 只在快照中进行动态调整，避免影响其他实例
        template_snapshot = {
            'template_id': template.id,
            'template_name': template.name,
            'object_type': template.object_type,
            'created_at': datetime.now().isoformat(),
            'steps': []
        }
        
        # 复制所有步骤到快照中
        
        for step in steps:
            
            # 获取分支条件（这里会调用我们刚刚添加调试的函数）
            branch_condition = _get_complete_branch_condition(step)
            
            step_data = {
                'step_id': step.id,
                'step_order': step.step_order,
                'step_name': step.step_name,
                'approver_type': step.approver_type,  # 🔥 关键修复：添加 approver_type 字段
                'approver_user_id': step.approver_user_id,
                'approver_username': step.approver.username if step.approver else None,
                'approver_real_name': step.approver.real_name if step.approver and step.approver.real_name else (step.approver.username if step.approver else None),
                'send_email': step.send_email,
                'action_type': step.action_type,
                'action_params': step.action_params,
                'editable_fields': step.editable_fields or [],
                'cc_users': step.cc_users or [],
                'cc_enabled': step.cc_enabled,
                'branch_condition': branch_condition,  # 🔥 关键修复：使用完整的分支条件数据
                'execution_condition': step.execution_condition  # 步骤执行条件
            }
            
            template_snapshot['steps'].append(step_data)
        
        
        # 获取目标对象的详细信息用于调试
        if object_type == 'pricing_order':
            from app.models.pricing_order import PricingOrder
            pricing_order = PricingOrder.query.get(object_id)
            if pricing_order and pricing_order.project:
                pass  # 原调试代码已移除
            else:
                pass  # 这里原本有调试代码，现在用pass占位
        
        # 🔥 关键修复：只在快照中进行动态调整，不修改数据库中的模板步骤
        # 检查是否有授权编号动作的步骤或智能授权流程，动态调整审批人
        if object_type == 'project':
            project = Project.query.get(object_id)
            if project:
                approver = get_authorization_approver_by_project_type(project.project_type)
                if approver:
                    # 处理智能授权流程 - 只更新快照，不修改数据库
                    if template.name == "智能授权审批流程":
                        # 更新模板快照中的审批人信息（第一步）
                        for step_data in template_snapshot['steps']:
                            if step_data['step_order'] == 1:
                                step_data['approver_user_id'] = approver.id
                                step_data['approver_username'] = approver.username
                                step_data['approver_real_name'] = approver.real_name or approver.username
                                step_data['step_name'] = f"{approver.role.replace('_', '').title()}授权审批"
                                current_app.logger.info(f"智能授权流程快照更新：项目类型 {project.project_type}，动态分配审批人：{approver.username} ({approver.role})")
                                break
                    
                    # 处理任何模板中的授权编号动作步骤 - 只更新快照
                    for step_data in template_snapshot['steps']:
                        # 如果步骤的动作类型是授权编号，动态分配审批人
                        if step_data.get('action_type') == 'authorization':
                            # 更新模板快照中的审批人信息
                            step_data['approver_user_id'] = approver.id
                            step_data['approver_username'] = approver.username
                            step_data['approver_real_name'] = approver.real_name or approver.username
                            original_step_name = step_data['step_name']
                            if '授权' not in original_step_name:
                                step_data['step_name'] = f"{original_step_name} - {approver.role.replace('_', '').title()}授权"
                            else:
                                step_data['step_name'] = f"{approver.role.replace('_', '').title()}授权审批"
                            
                            current_app.logger.info(f"授权编号步骤快照更新：项目类型 {project.project_type}，步骤 {step_data['step_order']}，分配给：{approver.username} ({approver.role})")
                else:
                    current_app.logger.warning(f"无法为项目类型 {project.project_type} 找到合适的授权审批人")

        # 🔥 报销单费用归属审批流程调整
        # 如果报销单指定了归属人（且不是申请人自己），需要动态插入两个步骤：
        # 1. 归属人审批（确认接受费用归属）
        # 2. 归属人上级审批
        if object_type == 'expense':
            from app.models.expense import Expense
            expense = Expense.query.get(object_id)
            if expense and expense.attributed_to_id and expense.attributed_to_id != expense.owner_id:
                current_app.logger.info(f"报销单 {expense.expense_number} 指定了归属人: {expense.attributed_to_id}，需要调整审批流程")

                # 获取归属人信息
                attributed_to_user = User.query.get(expense.attributed_to_id)
                if attributed_to_user:
                    # 在快照中找到第一个 approver_type='next_level' 的步骤
                    next_level_step_index = None
                    for i, step_data in enumerate(template_snapshot['steps']):
                        if step_data.get('approver_type') == 'next_level':
                            next_level_step_index = i
                            break

                    if next_level_step_index is not None:
                        current_app.logger.info(f"找到上级审批步骤（索引 {next_level_step_index}），将替换为归属人审批流程")

                        # 获取原步骤信息
                        original_step = template_snapshot['steps'][next_level_step_index]
                        original_order = original_step['step_order']

                        # 创建归属人审批步骤
                        attribution_step = {
                            'step_id': f"attr_{expense.id}_1",  # 动态生成的步骤ID
                            'step_order': original_order,
                            'step_name': f'归属人审批（{attributed_to_user.real_name or attributed_to_user.username}）',
                            'approver_type': 'user',  # 固定用户审批
                            'approver_user_id': attributed_to_user.id,
                            'approver_username': attributed_to_user.username,
                            'approver_real_name': attributed_to_user.real_name or attributed_to_user.username,
                            'send_email': original_step.get('send_email', True),
                            'action_type': original_step.get('action_type'),
                            'action_params': original_step.get('action_params'),
                            'editable_fields': original_step.get('editable_fields', []),
                            'cc_users': [],
                            'cc_enabled': False,
                            'branch_condition': None
                        }

                        # 创建归属人上级审批步骤
                        attribution_superior_step = {
                            'step_id': f"attr_{expense.id}_2",  # 动态生成的步骤ID
                            'step_order': original_order + 1,
                            'step_name': '归属人上级审批',
                            'approver_type': 'next_level',  # 上级审批
                            'approver_user_id': None,  # 动态计算
                            'approver_username': None,
                            'approver_real_name': None,
                            'send_email': original_step.get('send_email', True),
                            'action_type': original_step.get('action_type'),
                            'action_params': original_step.get('action_params'),
                            'editable_fields': original_step.get('editable_fields', []),
                            'cc_users': [],
                            'cc_enabled': False,
                            'branch_condition': None,
                            # 🔥 关键：标记这个步骤基于归属人计算上级
                            'context_user_id': attributed_to_user.id
                        }

                        # 替换原步骤为两个新步骤
                        template_snapshot['steps'] = (
                            template_snapshot['steps'][:next_level_step_index] +
                            [attribution_step, attribution_superior_step] +
                            template_snapshot['steps'][next_level_step_index + 1:]
                        )

                        # 重新调整后续步骤的 step_order
                        for j, step_data in enumerate(template_snapshot['steps']):
                            step_data['step_order'] = j + 1

                        current_app.logger.info(f"已插入归属人审批步骤，新的步骤顺序: {[s['step_name'] for s in template_snapshot['steps']]}")
                    else:
                        current_app.logger.warning(f"报销单 {expense.expense_number} 的审批模板中没有找到上级审批步骤")
                else:
                    current_app.logger.warning(f"报销单 {expense.expense_number} 的归属人 {expense.attributed_to_id} 不存在")

        # 🔥 重要：不再提交模板步骤的更新，因为我们只修改快照
        # db.session.commit()  # 删除这行，避免修改数据库中的模板

        # 🔥 修复：使用 step_order 而不是 step_id
        # current_step 是 Integer 类型，存储步骤顺序号（1, 2, 3...）
        # 这样无论是原始步骤还是动态插入的归属人步骤，都能正确匹配
        first_step_order = 1  # 第一步的 step_order 始终为 1
        current_app.logger.info(f"使用 step_order 作为 current_step: {first_step_order}")

        # 标准化 designated_approvers:key 转 str(兼容前端发 int key 的情况)
        _designated_norm = None
        if designated_approvers and isinstance(designated_approvers, dict):
            _designated_norm = {str(k): int(v) for k, v in designated_approvers.items() if v}

        # 创建审批实例
        instance = ApprovalInstance(
            process_id=template_id,
            object_id=object_id,
            object_type=object_type,
            current_step=first_step_order,  # 🔥 使用 step_order 而不是 step_id
            status=ApprovalStatus.PENDING,
            started_at=datetime.now(),
            created_by=user_id,
            template_snapshot=template_snapshot,
            template_version=f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            designated_approvers=_designated_norm,
        )
        db.session.add(instance)
        db.session.flush()  # 获取实例ID但不提交
        
        
        # 特别调试分支步骤的快照内容
        for step_data in template_snapshot['steps']:
            if step_data.get('action_type') == 'branch_decision':
                if step_data['branch_condition']:
                    conditions = step_data['branch_condition'].get('conditions', [])
                    for i, cond in enumerate(conditions):
                        pass  # 原有调试代码已清理
        
        current_app.logger.info(f"已为审批实例创建模板快照，版本: {instance.template_version}")
        
        # 🔧 关键调试：审批实例创建后检查批价单状态
        if object_type == 'pricing_order':
            from app.models.pricing_order import PricingOrder
            pricing_order_after = PricingOrder.query.get(object_id)
        
        # 如果模板配置了锁定对象，则锁定对象（统一调度,详见 app/utils/lockable.py）
        if template.lock_object_on_start:
            from app.utils.lockable import lock_object, get_registry
            _reason = template.lock_reason or '审批流程进行中，暂时锁定编辑'
            if object_type == 'project':
                # 项目特殊:锁定原因包含模板名(沿用旧行为)
                _reason = f"授权编号审批锁定: {template.name}"
            lock_success = lock_object(object_type, object_id, reason=_reason, user_id=user_id)

            # 已注册的对象类型如果锁定失败,回滚整个审批实例
            if not lock_success and object_type in get_registry():
                current_app.logger.warning(f"锁定{object_type}失败: {object_id}")
                db.session.rollback()
                from flask import flash
                flash(f"发起审批失败: 无法锁定{get_object_type_display(object_type)}，请稍后再试", 'danger')
                return None
        
        # 🔧 关键调试：数据库提交前最后检查批价单状态
        if object_type == 'pricing_order':
            from app.models.pricing_order import PricingOrder
            pricing_order_before_commit = PricingOrder.query.get(object_id)

        # 根据 auto_commit 参数决定是否提交事务
        if auto_commit:
            db.session.commit()
            current_app.logger.info(f"审批实例已提交: auto_commit=True")
        else:
            db.session.flush()  # 只flush不commit，由调用者统一提交
            current_app.logger.info(f"审批实例已flush，等待调用者提交: auto_commit=False")

        # 🔧 关键调试：数据库提交后最终检查批价单状态
        if object_type == 'pricing_order':
            from app.models.pricing_order import PricingOrder
            pricing_order_after_commit = PricingOrder.query.get(object_id)

        current_app.logger.info(f"成功发起审批流程: {object_type}:{object_id}, 模板ID: {template_id}, 实例ID: {instance.id}")

        # 检查第一步的执行条件，如果不满足则跳过到下一个可执行步骤
        all_steps = instance.get_steps()
        first_step = all_steps[0] if all_steps else None
        if first_step:
            target_object = _get_target_object_by_type(instance)
            should_execute = _check_step_execution_condition(first_step, target_object, instance)
            if should_execute is False:
                # 第一步条件不满足/自审 → 跳过并寻找下一个可执行步骤
                _create_skip_record(instance, first_step,
                    "发起人本人，审核步自动跳过" if _is_self_review_auto_skip(first_step, instance)
                    else "无上级审批人(发起人为最高层)，自动跳过" if _is_next_level_no_approver(first_step, instance)
                    else "条件不满足，自动跳过")
                # 从首步序号(而非写死0)之后找下一可执行步, 否则 advance 会从 order=1
                # 重新评估并二次记录同一首步 → skipped 记录重复 (引擎原有 quirk, 修正为单条)
                _fs_order = first_step.get('step_order') if isinstance(first_step, dict) else first_step.step_order
                next_executable = _advance_to_next_executable_step(instance, _fs_order, all_steps, target_object)
                if next_executable:
                    next_order = next_executable.get('step_order') if isinstance(next_executable, dict) else next_executable.step_order
                    instance.current_step = next_order
                    first_step = next_executable  # 更新 first_step 为实际通知的步骤
                    current_app.logger.info(f"第一步执行条件不满足，跳过到步骤 {next_order}")
                else:
                    # 所有步骤都不满足条件，直接完成
                    instance.status = ApprovalStatus.APPROVED
                    instance.ended_at = datetime.now()
                    current_app.logger.info(f"所有步骤执行条件均不满足，审批流程自动完成")
                    first_step = None  # 不需要通知
                db.session.flush()

        # 通知第一步审批人（站内消息）
        if first_step:
            from app.services.approval_message_service import ApprovalMessageService
            ApprovalMessageService.send_approval_notification(instance, first_step, actual_approver=get_step_actual_approver(first_step, instance))

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
        'remark': '备注',
        # 订单字段
        'order_number': '订单号',
        'company_id': '目标公司',
        'order_date': '订单日期',
        'expected_date': '预期交付日期',
        'total_amount': '订单总金额',
        'total_quantity': '订单总数量',
        'payment_terms': '付款条件',
        'delivery_address': '交付地址'
    }
    
    return field_map.get(field_name, field_name)


def process_auto_step(instance_id, user_id=None):
    """自动处理自动执行步骤
    
    Args:
        instance_id: 审批实例ID
        user_id: 操作人ID（用于记录）
        
    Returns:
        布尔值，表示操作是否成功
    """
    instance = ApprovalInstance.query.get(instance_id)
    if not instance or instance.status != ApprovalStatus.PENDING:
        return False
    
    if user_id is None:
        user_id = current_user.id
    
    # 获取当前步骤
    current_step = instance.get_current_step_info()
    if not current_step:
        return False
    
    # 检查是否为自动步骤
    if isinstance(current_step, dict):
        approver_type = current_step.get('approver_type', 'user')
        action_type = current_step.get('action_type')
    else:
        approver_type = getattr(current_step, 'approver_type', 'user')
        action_type = getattr(current_step, 'action_type', None)
    
    if approver_type != 'auto':
        return False
    
    
    # 自动批准处理
    return process_approval_with_project_type(instance_id, 'approve', None, '自动执行', user_id, None)


def process_approval_with_project_type(instance_id, action, project_type=None, comment=None, user_id=None, pricing_order_data=None):
    """处理审批操作，支持项目类型修改 - 修复版：支付步骤保持PENDING状态

    Args:
        instance_id: 审批实例ID
        action: 审批动作（ApprovalAction枚举值）
        project_type: 项目类型，用于授权步骤
        comment: 审批意见
        user_id: 操作人ID
        pricing_order_data: 批价单数据，用于批结算步骤

    Returns:
        布尔值，表示操作是否成功
    """
    instance = ApprovalInstance.query.get(instance_id)
    if not instance or instance.status != ApprovalStatus.PENDING:
        return False
    
    if user_id is None:
        user_id = current_user.id

    # 🔧 预检查：验证current_step是否能在快照中找到（数据完整性检查）
    # 🔥 修复：current_step 可能是 step_order 或 step_id，需要智能匹配
    instance_steps = instance.get_steps()
    current_step_found = False
    if isinstance(instance_steps, list):
        # 先尝试用 step_order 匹配
        for step in instance_steps:
            step_order = step.get('step_order') if isinstance(step, dict) else getattr(step, 'step_order', None)
            if step_order == instance.current_step:
                current_step_found = True
                break
        # 如果 step_order 匹配不到，尝试用 step_id 匹配（兼容历史数据）
        if not current_step_found:
            for step in instance_steps:
                step_id = step.get('step_id') if isinstance(step, dict) else getattr(step, 'id', None)
                if step_id == instance.current_step:
                    current_step_found = True
                    break

    if not current_step_found:
        current_app.logger.error(
            f"数据完整性错误: current_step={instance.current_step}在快照中找不到对应的step_order或step_id。"
        )
        current_app.logger.warning(f"继续尝试处理，但可能会失败")

    # 获取当前步骤 - 修复：使用模板快照
    current_step = instance.get_current_step_info()
    if not current_step:
        return False
    
    # 检查步骤类型
    if isinstance(current_step, dict):
        approver_type = current_step.get('approver_type', 'user')
    else:
        approver_type = getattr(current_step, 'approver_type', 'user')
    
    # 对于自动步骤，跳过权限检查并自动执行
    if approver_type == 'auto':
        # 自动步骤使用系统用户ID进行记录
        if user_id is None:
            user_id = current_user.id
    else:
        # 使用新的动态审批人确定函数检查权限
        actual_approver = get_step_actual_approver(current_step, instance)
        if not actual_approver or actual_approver.id != user_id:
            return False
    
    # 检查是否是授权编号步骤
    is_authorization_step = False
    
    # 获取action_type
    if isinstance(current_step, dict):
        action_type = current_step.get('action_type')
        branch_condition = current_step.get('branch_condition')
    else:
        action_type = getattr(current_step, 'action_type', None)
        branch_condition = getattr(current_step, 'branch_condition', None)
    
    # 判断是否为授权步骤，同时获取分支授权动作
    branch_action = None
    # 直接授权类步骤（非分支）
    if action_type in ['authorization', 'project_authorization', 'channel_authorization', 'business_authorization', 'customer_service_authorization']:
        is_authorization_step = True
        # 非通用authorization时，明确指定分支动作类型，供授权处理函数选择对应编码生成器
        if action_type != 'authorization':
            branch_action = action_type
    # 分支决策步骤中包含授权动作
    elif action_type == 'branch_decision' and branch_condition:
        # 对于分支步骤，检查匹配的分支action是否为授权类型
        # 简化版本：检查当前项目类型匹配的分支action是否包含'authorization'
        try:
            import json
            if isinstance(branch_condition, str):
                branch_condition = json.loads(branch_condition)
            
            if instance.object_type == 'project':
                project = Project.query.get(instance.object_id)
                if project:
                    field_name = branch_condition.get('field')
                    if field_name:
                        field_value = getattr(project, field_name, None)
                        conditions = branch_condition.get('conditions', [])
                        for condition in conditions:
                            if ((condition.get('operator') == 'equals' and field_value == condition.get('value')) or
                                (condition.get('operator') == 'in' and field_value == condition.get('value')) or
                                (condition.get('operator') == 'contains' and condition.get('value') in str(field_value))):
                                action_type_found = condition.get('action', '')
                                # 分支动作包含 authorization 时认为是授权步骤
                                is_authorization_step = 'authorization' in action_type_found
                                if is_authorization_step:
                                    branch_action = action_type_found
                                    break
        except Exception as e:
            current_app.logger.error(f"检查分支授权步骤失败: {e}")
            is_authorization_step = False
    
    # 确保action是枚举类型
    if not isinstance(action, ApprovalAction):
        if action == 'approve':
            action = ApprovalAction.APPROVE
        elif action == 'reject':
            action = ApprovalAction.REJECT
        else:
            current_app.logger.error(f"无效的审批动作: {action}")
            return False
    
    # 记录审批结果 - 处理模板快照的step_id类型问题
    # 对于模板快照，current_step.id可能是字符串，需要特殊处理
    if isinstance(current_step, dict):
        step_id_value = current_step.get('step_id')
    else:
        step_id_value = current_step.id
    if isinstance(step_id_value, str) and step_id_value.startswith('snapshot_step_'):
        # 模板快照情况：使用None作为step_id，因为step_id字段是整数外键
        # 我们将在未来版本中考虑为快照记录添加专门的字段
        step_id_value = None
        step_id_for_log = current_step.get('step_id') if isinstance(current_step, dict) else current_step.id
        current_app.logger.info(f"模板快照审批记录 - 实例 {instance_id}，步骤ID: {step_id_for_log}，使用NULL作为step_id")
    
    record = ApprovalRecord(
        instance_id=instance_id,
        step_id=step_id_value,
        approver_id=user_id,
        action=action.value,
        comment=comment,
        timestamp=datetime.now()
    )
    
    db.session.add(record)

    # 🔥 修复：从快照创建临时ApprovalStep对象用于execute_action调用
    # 在10月1日重构中，从数据库查询改为模板快照，但忘记创建current_step_obj
    from app.models.approval import ApprovalStep
    current_step_obj = ApprovalStep.from_snapshot(current_step, instance.process_id)

    # 【已移除】处理授权编号逻辑 - 授权逻辑已移至分支决策动作中执行
    # authorization_result = None
    #
    # if action == ApprovalAction.APPROVE and is_authorization_step and instance.object_type == 'project':
    #     authorization_result = _handle_project_authorization(instance, project_type, preview_only=False, branch_action=branch_action)
    # else:
    #     pass  # 其他情况暂不处理

    # 如果拒绝，直接结束流程
    if action == ApprovalAction.REJECT:
        instance.status = ApprovalStatus.REJECTED
        instance.ended_at = datetime.now()

        # 通知提交人审批被拒绝
        try:
            from app.services.approval_message_service import ApprovalMessageService
            ApprovalMessageService.send_approval_notification(
                instance, current_step, action, comment,
                custom_context=None, notify_submitter=True
            )
        except Exception as e:
            current_app.logger.error(f"发送提交人通知失败: {str(e)}", exc_info=True)

        # 更新业务对象的审批状态
        _update_business_object_approval_status(instance, action, user_id, comment)

        # 解锁对象(统一调度,详见 app/utils/lockable.py)
        from app.utils.lockable import unlock_object
        unlock_object(instance.object_type, instance.object_id, user_id)
    else:
        # 🔥 修复：检查是否刚完成了支付步骤
        current_step_action_type = None
        if isinstance(current_step, dict):
            current_step_action_type = current_step.get('action_type')
        elif hasattr(current_step, 'action_type'):
            current_step_action_type = current_step.action_type
            
        is_payment_step_completed = (
            current_step_action_type == 'payment_processing' and 
            instance.object_type == 'expense'
        )
        
        if is_payment_step_completed:
            # 支付步骤完成，流程结束
            instance.status = ApprovalStatus.APPROVED
            instance.ended_at = datetime.now()

            # 获取报销单信息并构建自定义上下文
            from app.models.expense import Expense
            expense = Expense.query.get(instance.object_id)
            custom_context = None
            if expense:
                custom_context = {
                    'business_number': expense.expense_number,
                    'object_title': expense.title,
                    'total_amount': f'{Config.CURRENCY_SYMBOL}{expense.total_amount:.2f}'
                }

            # 通知提交人流程已完成
            try:
                from app.services.approval_message_service import ApprovalMessageService
                ApprovalMessageService.send_approval_notification(
                    instance, current_step, action, comment,
                    custom_context=custom_context, notify_submitter=True
                )
            except Exception as e:
                current_app.logger.error(f"发送提交人通知失败: {str(e)}", exc_info=True)

            # 设置报销单状态
            if expense:
                expense.status = 'paid'
                expense.payment_status = 'paid'
                expense.payment_date = datetime.now()
                expense.paid_by = user_id
                # 🔥 修复：支付完成后保持锁定状态，确保已支付报销单不被修改
                expense.is_locked = True
                current_app.logger.info(f"报销单 {expense.expense_number} 支付完成，状态更新为: paid，保持锁定状态")
            
            # 🔥 注释掉：支付完成的报销单应该保持锁定，不应该解锁
            # unlock_expense(instance.object_id, user_id)
        else:
            # 🔥 修复：从快照中直接获取当前步骤的step_order，避免查询数据库导致的跨流程混淆
            current_step_order = None
            if isinstance(current_step, dict):
                current_step_order = current_step.get('step_order')
            else:
                current_step_order = getattr(current_step, 'step_order', None)

            if current_step_order is None:
                current_app.logger.error(f"无法从当前步骤获取step_order，审批失败")
                return False

            # 从模板快照中查找下一步骤（支持执行条件跳过）
            steps = instance.get_steps()
            target_object = _get_target_object_by_type(instance)
            next_step = _advance_to_next_executable_step(instance, current_step_order, steps, target_object)


            # ============================================================
            # 阶段1：执行当前步骤的动作（统一处理，无论是否有下一步）
            # ============================================================
            _execute_current_step_action(
                instance, current_step, current_step_obj, current_step_action_type,
                record, user_id, pricing_order_data, action
            )

            # ============================================================
            # 阶段2：更新流程状态（根据是否有下一步决定继续或完成）
            # ============================================================
            if next_step:
                # 有下一步：移动到下一步
                # 🔥 修复：使用 step_order 而不是 step_id
                next_step_order = next_step.get('step_order') if isinstance(next_step, dict) else next_step.step_order
                instance.current_step = next_step_order

                # 特殊处理：如果下一步是支付步骤，需要更新业务对象状态
                next_step_action_type = next_step.get('action_type') if isinstance(next_step, dict) else getattr(next_step, 'action_type', None)
                if next_step_action_type == 'payment_processing' and instance.object_type == 'expense':
                    _update_expense_status_for_payment_stage(instance, user_id, comment)

                # 通知下一步审批人
                from app.services.approval_message_service import ApprovalMessageService
                ApprovalMessageService.send_approval_notification(instance, next_step, actual_approver=get_step_actual_approver(next_step, instance))
            else:
                # 无下一步：流程完成
                instance.status = ApprovalStatus.APPROVED
                instance.ended_at = datetime.now()

                # 通知提交人流程已完成
                try:
                    from app.services.approval_message_service import ApprovalMessageService
                    ApprovalMessageService.send_approval_notification(
                        instance, current_step, action, comment,
                        custom_context=None, notify_submitter=True
                    )
                except Exception as e:
                    current_app.logger.error(f"发送提交人通知失败: {str(e)}", exc_info=True)

                # 更新业务对象的审批状态
                _update_business_object_approval_status(instance, action, user_id, comment)

                # 解锁对象(统一调度,详见 app/utils/lockable.py)
                from app.utils.lockable import unlock_object
                unlock_object(instance.object_type, instance.object_id, user_id)
    
    try:
        db.session.commit()
        current_app.logger.info(f"审批操作成功提交: 实例{instance_id}, 当前步骤{instance.current_step}")

        # 发送站内消息通知
        try:
            from app.services.approval_message_service import ApprovalMessageService
            ApprovalMessageService.send_approval_notification(
                instance, current_step, action, comment, custom_context=None
            )
        except Exception as e:
            # 记录日志但不影响主流程
            current_app.logger.error(f"发送审批通知失败: {str(e)}", exc_info=True)

        return True
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"处理审批失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return False



def _handle_project_authorization(instance, project_type, preview_only=False, branch_action=None):
    """处理项目授权编号逻辑
    
    Args:
        instance: 审批实例对象
        project_type: 用户选择的项目类型
        preview_only: 仅预览模式，不实际修改数据库
        branch_action: 分支授权动作类型 (如 'channel_authorization', 'business_authorization')
        
    Returns:
        生成的授权编号或None
    """
    
    project = Project.query.get(instance.object_id)
    if not project:
        current_app.logger.error(f"找不到项目: {instance.object_id}")
        return None
    
    
    # 如果已经有授权编号，则不做处理
    if project.authorization_code and not preview_only:
        current_app.logger.warning(f"项目已有授权编号，不进行处理: {project.id} - {project.authorization_code}")
        return project.authorization_code
    
    try:
        # 确定要使用的项目类型
        effective_project_type = project_type if project_type else project.project_type
        
        # 根据分支授权动作类型选择对应的生成函数
        if branch_action:
            # 在预览模式下，使用默认的审批人ID (0)
            approver_id = getattr(instance, 'processed_by', 0) if not preview_only else 0
            
            if branch_action == 'channel_authorization':
                from app.utils.authorization import generate_channel_authorization_code
                authorization_code = generate_channel_authorization_code(effective_project_type, project.id, approver_id)
            elif branch_action == 'business_authorization':
                from app.utils.authorization import generate_business_authorization_code
                authorization_code = generate_business_authorization_code(effective_project_type, project.id, approver_id)
            elif branch_action == 'project_authorization':
                from app.utils.authorization import generate_project_authorization_code
                authorization_code = generate_project_authorization_code(effective_project_type, project.id, approver_id)
            else:
                # 默认使用通用授权编码生成
                from app.utils.authorization import generate_authorization_code
                authorization_code = generate_authorization_code(effective_project_type)
        else:
            # 使用原有的生成方式
            project_type_for_code = project_type_label(effective_project_type)
            authorization_code = Project.generate_authorization_code(project_type_for_code)
        
        if not authorization_code:
            current_app.logger.error(f"无法为项目生成授权编号: {project.id}, 类型: {effective_project_type}, 动作: {branch_action}")
            return None
        
        # 预览模式不修改数据库
        if preview_only:
            return authorization_code
        
        # 如果提供了项目类型，则更新项目类型
        if project_type and project_type != project.project_type:
            current_app.logger.info(f"更新项目类型: {project.id}, 原类型: {project.project_type}, 新类型: {project_type}")
            project.project_type = project_type
        
        # 更新项目信息
        project.authorization_code = authorization_code
        project.authorization_status = None  # 清除pending状态
        project.report_time = datetime.now().date()  # 更新报备日期为当前日期
        
        # 同步更新所有关联报价单的project_stage和project_type
        quotations = Quotation.query.filter_by(project_id=project.id).all()
        for q in quotations:
            q.project_stage = project.current_stage
            q.project_type = project.project_type

        # 提交数据库事务
        db.session.commit()

        current_app.logger.info(f"项目授权成功: {project.id}, 授权编号: {authorization_code}, 项目类型: {project.project_type}")
        return authorization_code
    except Exception as e:
        current_app.logger.error(f"处理项目授权失败: {project.id}, 错误: {str(e)}")
        return None


def _is_self_review_auto_skip(step, instance):
    """是否应"自审自动跳过": 纯审核步(无 action_type 且非分支) 且 该步实际审批人
    == 审批发起人。 发起人提交即认可, 自己审自己无意义 → 跳过。

    白名单语义: 仅无 action_type 的纯审核步适用; 带 action_type 的步骤
    (付款 payment_processing / 各类授权 authorization / 分支决策 branch_decision
    / 入库 product_warehousing / 批价结算 pricing_settlement_approval / 表单确认
    form_confirm 等执行或控制动作) 一律不适用 —— 新增动作类型默认不跳, 安全。
    """
    if instance is None:
        return False
    if isinstance(step, dict):
        _act = step.get('action_type')
        _stype = step.get('step_type')
    else:
        _act = getattr(step, 'action_type', None)
        _stype = getattr(step, 'step_type', None)
    if _act or _stype == 'branch':
        return False
    try:
        _actual = get_step_actual_approver(step, instance)
        return _actual is not None and getattr(_actual, 'id', None) == instance.created_by
    except Exception:
        return False  # 解析审批人失败 → 不跳, 不影响原有逻辑


def _is_next_level_no_approver(step, instance):
    """next_level(上级审批)步是否解析不到上级 → 应跳过。
    用于:发起人本身是总经理(无上级)等场景,避免回退到 admin 或卡死。
    仅对 next_level 类型生效;user/auto 类型缺审批人属配置问题,不在此自动跳过。"""
    if instance is None:
        return False
    atype = step.get('approver_type') if isinstance(step, dict) else getattr(step, 'approver_type', None)
    if atype != 'next_level':
        return False
    try:
        return get_step_actual_approver(step, instance) is None
    except Exception:
        return False  # 解析失败 → 不跳,不影响原有逻辑


def _check_step_execution_condition(step, target_object, instance=None):
    """检查步骤的执行条件

    Args:
        step: 步骤对象（ApprovalStep对象或快照字典）
        target_object: 目标业务对象
        instance: 审批实例 (用于自审跳过判定; None 时退回原有纯条件逻辑)

    Returns:
        True  → 条件满足，执行此步骤
        False → 条件不满足/自审应跳过，跳过此步骤
        None  → 无条件（未设置条件），正常执行
    """
    # 发起人审自己的纯审核步 → 自动跳过 (详见 _is_self_review_auto_skip)
    if _is_self_review_auto_skip(step, instance):
        return False

    # next_level(上级审批)步解析不到上级(如发起人为总经理/无上级)→ 跳过该步,继续后续流程
    if _is_next_level_no_approver(step, instance):
        return False

    if isinstance(step, dict):
        condition = step.get('execution_condition')
    else:
        condition = getattr(step, 'execution_condition', None)

    if not condition or not isinstance(condition, dict):
        return None  # 无条件

    # 创建临时 ApprovalStep 对象以复用评估逻辑
    temp_step = ApprovalStep.from_snapshot(step) if isinstance(step, dict) else step
    if temp_step is None:
        return None
    return temp_step.evaluate_execution_condition(target_object)


def _create_skip_record(instance, step, reason="条件不满足，自动跳过"):
    """为跳过的步骤创建审批记录

    Args:
        instance: 审批实例对象
        step: 步骤对象（ApprovalStep对象或快照字典）
        reason: 跳过原因

    注意：ApprovalRecord.approver_id 是 NOT NULL，
    跳过记录使用审批实例的创建人（发起人）作为记录关联用户。
    """
    step_id = step.get('step_id') if isinstance(step, dict) else step.id

    record = ApprovalRecord(
        instance_id=instance.id,
        step_id=step_id if isinstance(step_id, int) else None,
        approver_id=instance.created_by,  # 使用发起人ID，因为approver_id不可为空
        action='skipped',
        comment=reason,
        timestamp=datetime.now()
    )
    db.session.add(record)
    current_app.logger.info(
        f"步骤跳过记录已创建: instance_id={instance.id}, "
        f"step_id={step_id}, reason={reason}"
    )


def _find_step_by_order(steps, step_order):
    """从步骤列表中按step_order查找步骤

    Args:
        steps: 步骤列表（字典列表或对象列表）
        step_order: 目标步骤序号

    Returns:
        匹配的步骤对象/字典，如果没有则返回None
    """
    if not isinstance(steps, list) or len(steps) == 0:
        return None

    if isinstance(steps[0], dict):
        for step in steps:
            if step.get('step_order') == step_order:
                return step
    else:
        for step in steps:
            if step.step_order == step_order:
                return step
    return None


def _advance_to_next_executable_step(instance, current_step_order, steps, target_object):
    """从当前步骤开始，寻找下一个可执行的步骤（跳过不满足执行条件的步骤）

    Args:
        instance: 审批实例
        current_step_order: 当前步骤序号
        steps: 全部步骤列表
        target_object: 目标业务对象

    Returns:
        下一个可执行的步骤（字典或对象），如果所有后续步骤都不满足条件则返回None
    """
    next_order = current_step_order + 1
    next_step = _find_step_by_order(steps, next_order)

    while next_step:
        should_execute = _check_step_execution_condition(next_step, target_object, instance)
        if should_execute is not False:
            # 条件满足或无条件 → 执行此步骤
            return next_step
        # 条件不满足/自审 → 创建跳过记录，继续找下一步
        _create_skip_record(instance, next_step,
            "无上级审批人(发起人为最高层)，自动跳过" if _is_next_level_no_approver(next_step, instance)
            else "发起人本人，审核步自动跳过" if _is_self_review_auto_skip(next_step, instance)
            else "条件不满足，自动跳过")
        next_order += 1
        next_step = _find_step_by_order(steps, next_order)

    return None  # 没有可执行的后续步骤


def _get_target_object_by_type(instance):
    """根据对象类型获取目标对象

    Args:
        instance: ApprovalInstance对象

    Returns:
        目标业务对象，如果不存在则返回None
    """
    target_object = None

    if instance.object_type == 'project':
        from app.models.project import Project
        target_object = Project.query.get(instance.object_id)
    elif instance.object_type == 'expense':
        from app.models.expense import Expense
        target_object = Expense.query.get(instance.object_id)
    elif instance.object_type == 'pricing_order':
        from app.models.pricing_order import PricingOrder
        target_object = PricingOrder.query.get(instance.object_id)
    elif instance.object_type == 'rd_product':
        from app.models.dev_product import DevProduct
        target_object = DevProduct.query.get(instance.object_id)

    return target_object


def _execute_current_step_action(instance, current_step, current_step_obj, current_step_action_type,
                                  record, user_id, pricing_order_data, action):
    """执行当前步骤的动作（统一处理）

    Args:
        instance: ApprovalInstance对象
        current_step: 当前步骤信息（字典格式）
        current_step_obj: 当前步骤对象（ApprovalStep临时对象）
        current_step_action_type: 当前步骤动作类型
        record: ApprovalRecord对象
        user_id: 操作人ID
        pricing_order_data: 批价单数据（可选）
        action: 审批动作（ApprovalAction枚举值）

    Returns:
        布尔值，表示动作执行是否成功
    """
    # 只有批准操作才执行动作
    if action != ApprovalAction.APPROVE:
        return True

    # 如果没有动作类型，直接返回
    if not current_step_action_type:
        return True

    # 如果是分支决策步骤，使用专门的分支决策处理函数
    if current_step_action_type == 'branch_decision':
        from app.helpers.approval_helpers import _execute_branch_decision_action
        _execute_branch_decision_action(instance, current_step, current_step_obj, record, user_id, pricing_order_data)
        return True

    # 其他动作类型，通过execute_action执行
    if not current_step_obj:
        return True

    try:
        # 获取目标业务对象
        target_object = _get_target_object_by_type(instance)

        if not target_object:
            current_app.logger.warning(f"目标对象不存在: {instance.object_type} #{instance.object_id}")
            return False

        # 执行动作
        if instance.object_type == 'pricing_order' and pricing_order_data:
            # 批价单审批传递数据
            result = current_step_obj.execute_action(record, target_object, pricing_order_data)
        else:
            # 其他类型审批
            result = current_step_obj.execute_action(record, target_object)

        return result
    except Exception as e:
        current_app.logger.error(f"执行步骤动作失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def process_approval(instance_id, action, comment=None, user_id=None, project_type=None, pricing_order_data=None):
    """处理审批操作
    
    Args:
        instance_id: 审批实例ID
        action: 审批动作（ApprovalAction枚举值）
        comment: 审批意见
        user_id: 操作人ID，默认为当前登录用户
        project_type: 项目类型，用于授权步骤
        pricing_order_data: 批价单数据，用于批结算步骤
        
    Returns:
        布尔值，表示操作是否成功
    """
    
    # 🔍 添加函数入口调试信息
    if pricing_order_data:
        pass

    # 导入所需的模型
    from app.models.approval import ApprovalStep
    
    # 如果提供了项目类型，使用扩展的处理函数
    if project_type is not None:
        return process_approval_with_project_type(instance_id, action, project_type, comment, user_id, pricing_order_data)
    
    # 原始处理逻辑保持不变...
    instance = ApprovalInstance.query.get(instance_id)
    if instance:
        pass

    if not instance or instance.status != ApprovalStatus.PENDING:
        current_app.logger.warning(f"🔍 [INSTANCE_DEBUG] 审批实例无效或状态不是PENDING，函数返回False")
        return False
    
    if user_id is None:
        user_id = current_user.id
    
    # 🔧 预检查：验证current_step是否能在快照中找到（数据完整性检查）
    # 🔥 修复：current_step 可能是 step_order 或 step_id，需要智能匹配
    instance_steps = instance.get_steps()
    current_step_found = False
    if isinstance(instance_steps, list):
        # 先尝试用 step_order 匹配
        for step in instance_steps:
            step_order = step.get('step_order') if isinstance(step, dict) else getattr(step, 'step_order', None)
            if step_order == instance.current_step:
                current_step_found = True
                break
        # 如果 step_order 匹配不到，尝试用 step_id 匹配（兼容历史数据）
        if not current_step_found:
            for step in instance_steps:
                step_id = step.get('step_id') if isinstance(step, dict) else getattr(step, 'id', None)
                if step_id == instance.current_step:
                    current_step_found = True
                    break

    if not current_step_found:
        current_app.logger.error(
            f"数据完整性错误: current_step={instance.current_step}在快照中找不到对应的step_order或step_id。"
        )
        # 不直接返回False，让后续代码继续尝试处理
        current_app.logger.warning(f"继续尝试处理，但可能会失败")
    
    # 获取当前步骤 - 修复：使用模板快照
    current_step = instance.get_current_step_info()
    if current_step:
        if isinstance(current_step, dict):
            pass
        else:
            pass

    if not current_step:
        current_app.logger.warning(f"🔍 [STEP_DEBUG] 无法获取当前步骤信息，函数返回False")
        return False
    
    # 使用新的动态审批人确定函数检查权限
    actual_approver = get_step_actual_approver(current_step, instance)
    
    # 调试信息
    current_app.logger.info(f"  instance_id: {instance_id}")
    current_app.logger.info(f"  user_id: {user_id}")
    current_app.logger.info(f"  current_step: {current_step}")
    current_app.logger.info(f"  actual_approver: {actual_approver}")
    current_app.logger.info(f"  actual_approver.id: {actual_approver.id if actual_approver else None}")
    current_app.logger.info(f"  权限检查结果: {actual_approver and actual_approver.id == user_id}")
    
    if not actual_approver or actual_approver.id != user_id:
        current_app.logger.warning(f"审批权限检查失败: actual_approver={actual_approver}, user_id={user_id}")
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
    
    # 记录审批结果 - 获取正确的step_id
    # current_step是字典，应该使用step_id字段
    step_id_value = None
    if isinstance(current_step, dict):
        step_id_value = current_step.get('step_id')
    elif hasattr(current_step, 'step_id'):
        step_id_value = current_step.step_id
    elif hasattr(current_step, 'id'):
        # 兼容旧的数据结构
        step_id_value = current_step.id
        
    # 🔧 关键修复：对V2快照系统，检查步骤ID是否在数据库中存在
    # 如果不存在，说明这是快照步骤，使用NULL避免外键约束冲突

    # 🔥 修复：先检查 step_id_value 是否为字符串类型（动态步骤如 "attr_93_1"）
    # 字符串类型的 step_id 是动态生成的，不在数据库中，直接设为 None
    if isinstance(step_id_value, str):
        current_app.logger.info(f"🔧 动态步骤：step_id={step_id_value} 是字符串类型，使用NULL避免外键约束")
        step_id_value = None
    elif step_id_value is not None:
        # 只有整数类型的 step_id 才去数据库查询验证
        existing_step = ApprovalStep.query.get(step_id_value)
        if existing_step is None:
            current_app.logger.info(f"🔧 快照步骤修复：步骤ID {step_id_value} 在数据库中不存在，使用NULL避免外键约束")
            step_id_value = None
        else:
            current_app.logger.info(f"🔧 常规步骤：步骤ID {step_id_value} 在数据库中存在，保持原值")
    
    
    record = ApprovalRecord(
        instance_id=instance_id,
        step_id=step_id_value,
        approver_id=user_id,
        action=action.value,
        comment=comment,
        timestamp=datetime.now()
    )
    
    db.session.add(record)

    # 🔥 修复：从快照创建临时ApprovalStep对象用于execute_action调用
    # 在10月1日重构中，从数据库查询改为模板快照，但忘记创建current_step_obj
    current_step_obj = ApprovalStep.from_snapshot(current_step, instance.process_id)

    # 如果拒绝，直接结束流程
    if action == ApprovalAction.REJECT:
        instance.status = ApprovalStatus.REJECTED
        instance.ended_at = datetime.now()

        # 通知提交人审批被拒绝
        try:
            from app.services.approval_message_service import ApprovalMessageService
            ApprovalMessageService.send_approval_notification(
                instance, current_step, action, comment,
                custom_context=None, notify_submitter=True
            )
        except Exception as e:
            current_app.logger.error(f"发送提交人通知失败: {str(e)}", exc_info=True)

        # 更新业务对象的审批状态
        _update_business_object_approval_status(instance, action, user_id, comment)

        # 解锁对象(统一调度,详见 app/utils/lockable.py)
        from app.utils.lockable import unlock_object
        unlock_object(instance.object_type, instance.object_id, user_id)
    else:
        # 🔥 修复：检查是否刚完成了支付步骤
        current_step_action_type = None
        if isinstance(current_step, dict):
            current_step_action_type = current_step.get('action_type')
        elif hasattr(current_step, 'action_type'):
            current_step_action_type = current_step.action_type
            
        is_payment_step_completed = (
            current_step_action_type == 'payment_processing' and 
            instance.object_type == 'expense'
        )
        
        if is_payment_step_completed:
            # 支付步骤完成，流程结束
            instance.status = ApprovalStatus.APPROVED
            instance.ended_at = datetime.now()

            # 获取报销单信息并构建自定义上下文
            from app.models.expense import Expense
            expense = Expense.query.get(instance.object_id)
            custom_context = None
            if expense:
                custom_context = {
                    'business_number': expense.expense_number,
                    'object_title': expense.title,
                    'total_amount': f'{Config.CURRENCY_SYMBOL}{expense.total_amount:.2f}'
                }

            # 通知提交人流程已完成
            try:
                from app.services.approval_message_service import ApprovalMessageService
                ApprovalMessageService.send_approval_notification(
                    instance, current_step, action, comment,
                    custom_context=custom_context, notify_submitter=True
                )
            except Exception as e:
                current_app.logger.error(f"发送提交人通知失败: {str(e)}", exc_info=True)

            # 设置报销单状态
            if expense:
                expense.status = 'paid'
                expense.payment_status = 'paid'
                expense.payment_date = datetime.now()
                expense.paid_by = user_id
                # 🔥 修复：支付完成后保持锁定状态，确保已支付报销单不被修改
                expense.is_locked = True
                current_app.logger.info(f"报销单 {expense.expense_number} 支付完成，状态更新为: paid，保持锁定状态")
            
            # 🔥 注释掉：支付完成的报销单应该保持锁定，不应该解锁
            # unlock_expense(instance.object_id, user_id)
        else:
            # 🔥 修复：从快照中直接获取当前步骤的step_order，避免查询数据库导致的跨流程混淆
            current_step_order = None
            if isinstance(current_step, dict):
                current_step_order = current_step.get('step_order')
            else:
                current_step_order = getattr(current_step, 'step_order', None)

            if current_step_order is None:
                current_app.logger.error(f"无法从当前步骤获取step_order，审批失败")
                return False

            # 从模板快照中查找下一步骤（支持执行条件跳过）
            steps = instance.get_steps()
            target_object = _get_target_object_by_type(instance)
            next_step = _advance_to_next_executable_step(instance, current_step_order, steps, target_object)


            # ============================================================
            # 阶段1：执行当前步骤的动作（统一处理，无论是否有下一步）
            # ============================================================
            _execute_current_step_action(
                instance, current_step, current_step_obj, current_step_action_type,
                record, user_id, pricing_order_data, action
            )

            # ============================================================
            # 阶段2：更新流程状态（根据是否有下一步决定继续或完成）
            # ============================================================
            if next_step:
                # 有下一步：移动到下一步
                # 🔥 修复：使用 step_order 而不是 step_id
                next_step_order = next_step.get('step_order') if isinstance(next_step, dict) else next_step.step_order
                instance.current_step = next_step_order

                # 特殊处理：如果下一步是支付步骤，需要更新业务对象状态
                next_step_action_type = next_step.get('action_type') if isinstance(next_step, dict) else getattr(next_step, 'action_type', None)
                if next_step_action_type == 'payment_processing' and instance.object_type == 'expense':
                    _update_expense_status_for_payment_stage(instance, user_id, comment)

                # 通知下一步审批人
                from app.services.approval_message_service import ApprovalMessageService
                ApprovalMessageService.send_approval_notification(instance, next_step, actual_approver=get_step_actual_approver(next_step, instance))
            else:
                # 无下一步：流程完成
                instance.status = ApprovalStatus.APPROVED
                instance.ended_at = datetime.now()

                # 通知提交人流程已完成
                try:
                    from app.services.approval_message_service import ApprovalMessageService
                    ApprovalMessageService.send_approval_notification(
                        instance, current_step, action, comment,
                        custom_context=None, notify_submitter=True
                    )
                except Exception as e:
                    current_app.logger.error(f"发送提交人通知失败: {str(e)}", exc_info=True)

                # 更新业务对象的审批状态
                _update_business_object_approval_status(instance, action, user_id, comment)

                # 解锁对象(统一调度,详见 app/utils/lockable.py)
                from app.utils.lockable import unlock_object
                unlock_object(instance.object_type, instance.object_id, user_id)

    # 步骤推进/拒绝/通过 — 转交失效, 清空代理字段
    # 转交是 per-step 级别: 当前步骤处理完(approve/reject)后下一步骤须按原配置审批人
    if hasattr(instance, 'delegated_to_id') and instance.delegated_to_id is not None:
        instance.delegated_to_id = None
        instance.delegated_at = None
        instance.delegated_by_id = None

    db.session.commit()
    return True




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
    """获取对象的可编辑字段选项，包括主表和明细表字段
    
    Args:
        object_type: 对象类型 ('quotation', 'pricing_order', 'settlement_order', 'expense')
    
    Returns:
        dict: 字段选项字典，按分组组织，格式为:
        {
            'master': [(field_name, field_label)],  # 主表字段
            'detail': [(field_name, field_label)]   # 明细表字段
        }
        对于不支持明细的对象类型，返回传统格式的列表
    """
    
    # 支持明细字段的新格式对象类型
    if object_type in ['quotation', 'pricing_order', 'settlement_order', 'expense']:
        field_options = {'master': [], 'detail': []}
        
        if object_type == 'quotation':
            # 报价单主表字段
            field_options['master'] = [
                ('quotation_number', '报价单号'),
                ('amount', '报价金额'),
                ('project_stage', '项目阶段'),
                ('project_type', '项目类型'),
                ('approval_status', '审核状态'),
                ('currency', '货币类型'),
                ('implant_total_amount', '植入总额合计'),
                ('confirmation_badge_status', '确认徽章状态'),
                ('is_locked', '锁定状态'),
                ('lock_reason', '锁定原因'),
                ('created_at', '创建时间'),
                ('updated_at', '更新时间')
            ]
            # 报价单明细字段
            field_options['detail'] = [
                ('product_name', '产品名称'),
                ('product_model', '产品型号'),
                ('product_desc', '产品描述'),
                ('brand', '品牌'),
                ('unit', '单位'),
                ('quantity', '数量'),
                ('discount', '折扣率'),
                ('market_price', '市场价'),
                ('unit_price', '单价'),
                ('total_price', '总价'),
                ('product_mn', '产品料号'),
                ('implant_subtotal', '植入小计'),
                ('currency', '货币类型')
            ]
        elif object_type == 'pricing_order':
            # 批价单主表字段
            field_options['master'] = [
                ('order_number', '批价单号'),
                ('approval_flow_type', '审批流程类型'),
                ('status', '批价单状态'),
                ('current_approval_step', '当前审批步骤'),
                ('pricing_total_amount', '批价单总金额'),
                ('pricing_total_discount_rate', '批价单总折扣率'),
                ('settlement_total_amount', '结算单总金额'),
                ('settlement_total_discount_rate', '结算单总折扣率'),
                ('is_direct_contract', '厂商直签'),
                ('is_factory_pickup', '厂家提货'),
                ('project_type', '项目类型'),
                ('currency', '货币类型'),
                ('created_at', '创建时间'),
                ('updated_at', '更新时间')
            ]
            # 批价单明细字段
            field_options['detail'] = [
                ('product_name', '产品名称'),
                ('product_model', '产品型号'),
                ('product_desc', '产品描述'),
                ('brand', '品牌'),
                ('unit', '单位'),
                ('product_mn', '产品MN编码'),
                ('market_price', '市场价'),
                ('unit_price', '单价'),
                ('quantity', '数量'),
                ('discount_rate', '折扣率'),
                ('total_price', '小计金额'),
                ('currency', '货币类型'),
                ('source_type', '数据来源')
            ]
        elif object_type == 'settlement_order':
            # 结算单主表字段
            field_options['master'] = [
                ('order_number', '结算单号'),
                ('total_amount', '结算总金额'),
                ('total_discount_rate', '结算总折扣率'),
                ('status', '结算单审批状态'),
                ('settlement_status', '结算状态'),
                ('created_at', '创建时间'),
                ('updated_at', '更新时间')
            ]
            # 结算单明细字段
            field_options['detail'] = [
                ('product_name', '产品名称'),
                ('product_model', '产品型号'),
                ('product_desc', '产品描述'),
                ('brand', '品牌'),
                ('unit', '单位'),
                ('product_mn', '产品MN编码'),
                ('market_price', '市场价'),
                ('unit_price', '单价'),
                ('quantity', '数量'),
                ('discount_rate', '折扣率'),
                ('total_price', '小计金额'),
                ('currency', '货币类型'),
                ('settlement_status', '结算状态'),
                ('settlement_date', '结算完成时间'),
                ('settlement_notes', '结算备注')
            ]
        elif object_type == 'expense':
            # 报销单主表字段
            field_options['master'] = [
                ('expense_number', '报销单编号'),
                ('title', '报销主题'),
                ('description', '报销说明'),
                ('currency', '货币类型'),
                ('total_amount', '报销总金额'),
                ('status', '审批状态'),
                ('is_locked', '锁定状态'),
                ('approval_notes', '审批备注'),
                ('created_at', '创建时间'),
                ('updated_at', '更新时间')
            ]
            # 报销单明细字段
            field_options['detail'] = [
                ('expense_date', '发生日期'),
                ('expense_category', '报销科目'),
                ('description', '明细描述'),
                ('document_count', '单据数量'),
                ('currency', '发票货币类型'),
                ('invoice_amount', '发票金额'),
                ('current_amount', '当前金额'),
                ('exchange_rate', '汇率'),
                ('amount', '金额'),
                ('invoice_images', '发票图片'),
                ('status', '明细状态')
            ]
        
        return field_options
    
    # 以下是传统格式的字段定义，保持向后兼容
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
    
    customer_fields = [
        ('company_name', '企业名称'),
        ('company_type', '企业类型'),
        ('industry', '行业'),
        ('country', '国家/地区'),
        ('region', '省份/州'),
        ('address', '地址'),
        ('contact_name', '联系人')
    ]
    
    purchase_order_fields = [
        ('order_number', '订单号'),
        ('company_id', '目标公司'),
        ('order_date', '订单日期'),
        ('expected_date', '预期交付日期'),
        ('total_amount', '订单总金额'),
        ('total_quantity', '订单总数量'),
        ('currency', '币种'),
        ('payment_terms', '付款条件'),
        ('delivery_address', '交付地址'),
        ('description', '订单说明')
    ]
    
    settlement_fields = [
        ('settlement_number', '结算单号'),
        ('customer_id', '客户'),
        ('total_amount', '结算总金额'),
        ('currency', '币种'),
        ('settlement_date', '结算日期'),
        ('payment_terms', '付款条件'),
        ('description', '结算说明')
    ]
    
    standard_product_fields = [
        ('product_code', '产品编码'),
        ('product_name', '产品名称'),
        ('product_model', '产品型号'),
        ('product_spec', '产品规格'),
        ('product_brand', '产品品牌'),
        ('product_unit', '产品单位'),
        ('standard_price', '标准价格'),
        ('category', '产品分类')
    ]
    
    rd_product_fields = [
        ('mn_code', 'MN编号'),
        ('model', '产品型号'),
        ('name', '产品名称'),
        ('status', '产品状态'),
        ('unit', '单位'),
        ('retail_price', '零售价'),
        ('currency', '货币类型'),
        ('description', '产品描述'),
        ('category_id', '产品分类'),
        ('subcategory_id', '产品子分类'),
        ('region_id', '地区'),
        ('planned_duration_days', '计划工期(天)'),
        ('actual_duration_days', '实际工期(天)'),
        ('risk_level', '风险等级')
    ]
    
    product_analysis_fields = [
        ('analysis_id', '分析编号'),
        ('product_id', '关联产品'),
        ('analysis_type', '分析类型'),
        ('analysis_date', '分析日期'),
        ('cost_analysis', '成本分析'),
        ('market_analysis', '市场分析'),
        ('conclusion', '分析结论')
    ]
    
    inventory_stock_fields = [
        ('stock_id', '库存编号'),
        ('product_id', '产品'),
        ('warehouse', '仓库'),
        ('current_quantity', '当前库存'),
        ('reserved_quantity', '预留数量'),
        ('available_quantity', '可用数量'),
        ('last_update', '最后更新时间')
    ]
    
    performance_target_fields = [
        ('target_id', '目标编号'),
        ('user_id', '目标用户'),
        ('target_type', '目标类型'),
        ('target_value', '目标值'),
        ('current_value', '当前值'),
        ('achievement_rate', '完成率'),
        ('period', '考核期间')
    ]
    
    user_fields = [
        ('username', '用户名'),
        ('email', '邮箱'),
        ('full_name', '姓名'),
        ('phone', '电话'),
        ('department_id', '所属部门'),
        ('position', '职位'),
        ('is_active', '状态')
    ]
    
    department_fields = [
        ('department_name', '部门名称'),
        ('department_code', '部门编码'),
        ('parent_id', '上级部门'),
        ('manager_id', '部门经理'),
        ('description', '部门描述')
    ]
    
    # 根据业务对象类型返回对应的字段列表（传统格式）
    if object_type == 'project':
        return common_fields + project_fields
    elif object_type == 'customer':
        return common_fields + customer_fields
    elif object_type == 'purchase_order':
        return common_fields + purchase_order_fields
    elif object_type == 'settlement':
        return common_fields + settlement_fields
    elif object_type == 'standard_product':
        return common_fields + standard_product_fields
    elif object_type == 'rd_product' or object_type == 'dev_product':
        return common_fields + rd_product_fields
    elif object_type == 'product_analysis':
        return common_fields + product_analysis_fields
    elif object_type == 'inventory_stock':
        return common_fields + inventory_stock_fields
    elif object_type == 'performance_target':
        return common_fields + performance_target_fields
    elif object_type == 'user':
        return common_fields + user_fields
    elif object_type == 'department':
        return common_fields + department_fields
    else:
        # 如果没有指定业务对象类型，返回所有字段
        all_fields = set(common_fields + project_fields + customer_fields + purchase_order_fields + 
                        settlement_fields + standard_product_fields + rd_product_fields + product_analysis_fields + inventory_stock_fields +
                        performance_target_fields + user_fields + department_fields)
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


def get_pending_approval_count(user_id=None, force_refresh=False):
    """获取待用户审批的数量 - 优化版本使用缓存

    Args:
        user_id: 用户ID，默认为当前登录用户
        force_refresh: 是否强制刷新缓存，默认False

    Returns:
        整数，表示待审批的数量
    """
    try:
        if user_id is None:
            # 检查用户是否已登录
            if not current_user.is_authenticated:
                return 0
            user_id = current_user.id

        # 🔥 优化1: 使用session缓存，避免每次页面切换都重新计算
        from flask import session
        cache_key = f'pending_approval_count_{user_id}'

        # 如果不强制刷新且缓存存在，直接返回缓存值
        if not force_refresh and cache_key in session:
            cached_count = session[cache_key]
            if isinstance(cached_count, int):
                return cached_count

        # 🔥 优化2: 计算待审批数量（保持原有逻辑，但优化异常处理）
        general_count = _calculate_pending_approval_count(user_id)

        # 🔥 优化3: 缓存结果到session中
        session[cache_key] = general_count

        return general_count

    except Exception as e:
        # 最外层异常捕获，确保函数不会抛出错误导致模板渲染失败
        current_app.logger.error(f"get_pending_approval_count: 完全失败: {e}")
        return 0  # 返回默认值


def _calculate_pending_approval_count(user_id):
    """内部函数：实际计算待审批数量

    Args:
        user_id: 用户ID

    Returns:
        整数，表示待审批的数量
    """
    try:
        # 确保数据库事务状态干净
        try:
            db.session.rollback()
        except Exception:
            pass

        # 先获取所有待审批的实例
        base_instances = ApprovalInstance.query.filter(
            ApprovalInstance.status == ApprovalStatus.PENDING
        ).all()

        # 筛选出当前用户是当前步骤审批人的实例
        general_count = 0
        for instance in base_instances:
            try:
                current_step_info = instance.get_current_step_info()
                if current_step_info:
                    # 使用动态审批人确定函数
                    actual_approver = get_step_actual_approver(current_step_info, instance)

                    if actual_approver and actual_approver.id == user_id:
                        general_count += 1
            except Exception as e:
                current_app.logger.error(f"_calculate_pending_approval_count: 处理审批实例 {instance.id} 失败: {e}")
                continue  # 跳过有问题的实例

        return general_count

    except Exception as e:
        current_app.logger.error(f"_calculate_pending_approval_count: 计算失败: {e}")
        return 0


def clear_pending_approval_count_cache(user_id=None):
    """清除待审批数量缓存

    Args:
        user_id: 用户ID，默认为当前用户。如果为None，清除所有缓存
    """
    try:
        from flask import session

        if user_id is None:
            # 清除当前用户缓存
            if current_user.is_authenticated:
                user_id = current_user.id
            else:
                return

        cache_key = f'pending_approval_count_{user_id}'
        if cache_key in session:
            del session[cache_key]
            current_app.logger.info(f"已清除用户 {user_id} 的待审批数量缓存")

    except Exception as e:
        current_app.logger.error(f"清除待审批数量缓存失败: {e}")


def clear_all_pending_approval_count_cache():
    """清除所有用户的待审批数量缓存"""
    try:
        from flask import session

        # 查找并删除所有相关缓存key
        keys_to_delete = []
        for key in session.keys():
            if key.startswith('pending_approval_count_'):
                keys_to_delete.append(key)

        for key in keys_to_delete:
            del session[key]

        if keys_to_delete:
            current_app.logger.info(f"已清除 {len(keys_to_delete)} 个待审批数量缓存")

    except Exception as e:
        current_app.logger.error(f"清除所有待审批数量缓存失败: {e}")


def clear_approval_cache_after_operation(operation_name, user_id=None, object_type=None, object_id=None):
    """审批操作后清理缓存的通用函数

    Args:
        operation_name: 操作名称（用于日志）
        user_id: 操作用户ID，可选
        object_type: 业务对象类型，可选
        object_id: 业务对象ID，可选
    """
    try:
        # 清除所有用户的待审批数量缓存
        clear_all_pending_approval_count_cache()

        log_msg = f"{operation_name}操作后已清除待审批数量缓存"
        if object_type and object_id:
            log_msg += f" (涉及{object_type}#{object_id})"
        if user_id:
            log_msg += f" (操作用户: {user_id})"

        current_app.logger.info(log_msg)

    except Exception as e:
        current_app.logger.error(f"{operation_name}操作后清除缓存失败: {e}")


def setup_approval_cache_hooks():
    """设置审批缓存清理钩子函数

    这个函数可以用来批量设置各种审批操作的缓存清理
    """
    # 这里可以添加更多的钩子设置，比如信号处理等
    pass


def get_workflow_steps(approval_instance, current_user_id=None):
    """获取审批流程的步骤信息，用于在审批区域显示流程图
    
    Args:
        approval_instance: 审批实例对象
        current_user_id: 当前用户ID，用于权限判断
        
    Returns:
        包含步骤信息的列表，每个步骤包含：
        - order: 步骤顺序
        - name: 步骤名称
        - approver: 审批人姓名
        - is_current: 是否为当前步骤且当前用户有权限
        - is_waiting: 是否为当前步骤但当前用户无权限
        - is_completed: 是否已完成
        - action: 审批动作（approve/reject）
        - timestamp: 审批时间
        - comment: 审批意见
    """
    if not approval_instance:
        return []
    
    # 优先使用模板快照，如果没有快照则回退到当前模板
    template_steps = approval_instance.get_steps()
    if not template_steps:
        return []
    
    # 获取已完成的审批记录
    completed_records = ApprovalRecord.query.filter_by(
        instance_id=approval_instance.id
    ).order_by(ApprovalRecord.timestamp.asc()).all()
    
    # 构建步骤信息
    workflow_steps = []
    
    # 确定当前步骤：需要从step_id转换为step_order
    current_step_obj = ApprovalStep.query.filter_by(id=approval_instance.current_step).first()
    current_step_order = current_step_obj.step_order if current_step_obj else 1
    
    for i, step in enumerate(template_steps):
        # 处理快照数据（字典）和模型对象两种情况
        if isinstance(step, dict):
            step_order = step.get('step_order')
            step_name = step.get('step_name', '未知步骤')
            approver_real_name = step.get('approver_real_name')
            approver_username = step.get('approver_username')
            approver_type = step.get('approver_type', 'user')
        else:
            step_order = step.step_order
            step_name = step.step_name
            approver_real_name = step.approver.real_name if step.approver else None
            approver_username = step.approver.username if step.approver else None
            approver_type = step.approver_type or 'user'
        
        # 确定审批人显示名称
        if approver_type == 'next_level':
            # 对于next_level类型，尝试获取实际审批人
            try:
                actual_approver = get_step_actual_approver(step, approval_instance)
                approver_display = actual_approver.real_name or actual_approver.username if actual_approver else '待确定'
            except:
                approver_display = '上级领导'
        else:
            approver_display = approver_real_name or approver_username or '未知'
        
        # 🔥 修复：确定步骤状态 - 考虑用户权限
        is_objective_current = (step_order == current_step_order) and (approval_instance.status == ApprovalStatus.PENDING)
        is_completed = step_order < current_step_order
        
        # 判断当前用户是否有权限审批此步骤
        user_can_approve = False
        if current_user_id and is_objective_current:
            try:
                from flask import current_app
                user_can_approve = can_user_approve(approval_instance.id, current_user_id)
                current_app.logger.debug(f"步骤{step_order}权限检查: user_id={current_user_id}, can_approve={user_can_approve}")
            except:
                user_can_approve = False
        
        # 🔥 关键修复：只有当前用户有权限时才显示为current，否则显示为waiting
        is_current = is_objective_current and user_can_approve
        is_waiting = is_objective_current and not user_can_approve
        
        # 检查是否有跳过记录
        is_skipped = False
        skip_comment = None
        step_id_value = step.get('step_id') if isinstance(step, dict) else step.id
        for record in completed_records:
            if record.action == 'skipped' and record.step_id == step_id_value:
                is_skipped = True
                skip_comment = record.comment
                break

        step_info = {
            'order': step_order,
            'name': step_name,
            'approver': approver_display,
            'is_current': is_current,
            'is_waiting': is_waiting,  # 新增：等待状态
            'is_completed': is_completed,
            'is_skipped': is_skipped,  # 新增：跳过状态
            'action': None,
            'timestamp': None,
            'comment': None
        }

        # 如果步骤被跳过，设置对应信息
        if is_skipped:
            step_info.update({
                'action': 'skipped',
                'comment': skip_comment or '条件不满足，自动跳过'
            })
            # 从记录列表中移除已匹配的跳过记录
            for record in completed_records:
                if record.action == 'skipped' and record.step_id == step_id_value:
                    completed_records.remove(record)
                    break
        # 如果步骤已完成，查找对应的审批记录
        elif is_completed:
            # 查找匹配这个步骤的审批记录
            matching_record = None
            for record in completed_records:
                # 可以通过时间顺序或其他方式匹配
                # 这里简化处理：按顺序匹配（假设审批记录按时间顺序对应步骤顺序）
                if not matching_record:  # 取第一个还没有被使用的记录
                    matching_record = record
                    break

            if matching_record:
                step_info.update({
                    'action': matching_record.action,
                    'timestamp': matching_record.timestamp,
                    'comment': matching_record.comment
                })
                completed_records.remove(matching_record)  # 避免重复使用
        
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


def _update_generic_object_status(instance, action, user_id, comment):
    """通用的对象状态更新逻辑 - 重用现有映射机制
    
    支持所有在BRANCH_OBJECT_TYPE_MAPPING中配置的对象类型
    
    Args:
        instance: 审批实例对象
        action: 审批动作
        user_id: 操作人ID
        comment: 审批意见
    """
    try:
        # 重用现有的对象获取机制
        business_object = get_branch_business_object(instance)
        if not business_object:
            current_app.logger.error(f"找不到{instance.object_type}对象: {instance.object_id}")
            return
        
        # 通用状态更新逻辑
        if action == ApprovalAction.APPROVE:
            if instance.status == ApprovalStatus.APPROVED:
                # 流程完全通过
                business_object.status = 'approved'

                # 动态设置时间戳字段
                if hasattr(business_object, 'approved_at'):
                    business_object.approved_at = datetime.now()
                if hasattr(business_object, 'approved_by'):
                    business_object.approved_by = user_id

                # 针对批价单，执行审批完成后的额外操作（推进项目状态等）
                if instance.object_type == 'pricing_order':
                    from app.services.pricing_order_service import PricingOrderService
                    PricingOrderService.complete_approval(business_object)
            else:
                # 还在审批中
                business_object.status = 'pending'
                
        elif action == ApprovalAction.REJECT:
            # 审批拒绝
            business_object.status = 'rejected'
            if hasattr(business_object, 'approved_at'):
                business_object.approved_at = datetime.now()  
            if hasattr(business_object, 'approved_by'):
                business_object.approved_by = user_id
        
        # 记录日志
        object_identifier = getattr(business_object, 'order_number', None) or \
                           getattr(business_object, 'project_name', None) or \
                           getattr(business_object, 'quotation_number', None) or \
                           getattr(business_object, 'expense_number', None) or \
                           getattr(business_object, 'company_name', None) or \
                           getattr(business_object, 'id', 'unknown')
        
        current_app.logger.info(f"{instance.object_type} {object_identifier} 状态已更新为: {business_object.status}")
        
    except Exception as e:
        current_app.logger.error(f"通用对象状态更新失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())

def _log_quotation_confirmation(quotation_id, new_value, user_id, user=None):
    """技术确认动作记入变更历史(field_name='confirmation';报价单详情卡按可读动作显示)。"""
    try:
        from app.models.change_log import ChangeLog
        ChangeLog.log_update(
            module_name='quotation', table_name='quotations',
            record_id=quotation_id, field_name='confirmation',
            old_value='', new_value=new_value,
            user_id=user_id,
            user_name=(user.real_name or user.username) if user else None,
            description='confirm_' + str(new_value))
    except Exception:
        pass


def _update_business_object_approval_status(instance, action, user_id, comment):
    """更新业务对象的审批状态 - 重构版，支持所有对象类型
    
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
                # 技术确认徽章 = 审批结果的显示(单一来源):通过→点亮绿徽章 / 驳回→清除
                try:
                    if action == ApprovalAction.APPROVE:
                        quotation.set_confirmation_badge('#28a745', user_id)
                        _log_quotation_confirmation(quotation.id, 'confirmed', user_id, user)
                    elif action == ApprovalAction.REJECT:
                        quotation.clear_confirmation_badge()
                except Exception as _badge_err:
                    current_app.logger.warning(f"同步报价单确认徽章失败: {_badge_err}")

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

                    # 驳回后解锁 — 让创建人 / 有编辑权限的人(如方案经理)能修正后重新提交
                    try:
                        if hasattr(quotation, 'unlock'):
                            quotation.unlock(user_id)
                        else:
                            quotation.is_locked = False
                            quotation.lock_reason = None
                            quotation.locked_by = None
                            quotation.locked_at = None
                        current_app.logger.info(f"报价单 {quotation.quotation_number} 驳回后已解锁")
                    except Exception as _unlock_err:
                        current_app.logger.warning(f"驳回后解锁报价单失败: {_unlock_err}")

                    current_app.logger.info(f"报价单 {quotation.quotation_number} 审批被拒绝")
        
        elif instance.object_type == 'project':
            # 更新项目的状态
            from app.models.project import Project
            project = Project.query.get(instance.object_id)
            
            if project:
                if action == ApprovalAction.APPROVE:
                    # 审批通过
                    if instance.status == ApprovalStatus.APPROVED:
                        # 流程完全通过
                        project.status = 'approved'
                        # 业务线路由流程:授权编号按项目类型自动生成
                        # (channel_follow→CPJ / sales_focus→SPJ / business_opportunity→APJ);
                        # 旧 branch 流程在 branch 步骤已生成,_handle 对已有编号幂等直接返回
                        if (instance.template_snapshot or {}).get('biz_line_route'):
                            _BRANCH_BY_TYPE = {
                                'channel_follow': 'channel_authorization',
                                'sales_focus': 'project_authorization',
                                'business_opportunity': 'business_authorization',
                            }
                            _ba = _BRANCH_BY_TYPE.get(project.project_type)
                            try:
                                _handle_project_authorization(instance, None, branch_action=_ba)
                            except Exception as _auth_err:
                                current_app.logger.error(f"自动生成授权编号失败: {_auth_err}", exc_info=True)
                    else:
                        # 还在审批中
                        project.status = 'pending'
                elif action == ApprovalAction.REJECT:
                    # 审批拒绝
                    project.status = 'rejected'
                
                current_app.logger.info(f"项目 {project.project_name} 状态已更新为: {project.status}")

        elif instance.object_type == 'project_hold':
            # 项目失败/搁置审核(gated):仅当整条流程通过(instance.status==APPROVED)时,
            # 才把 current_stage 改为目标(lost/paused);驳回则什么都不改(维持正常)。
            from app.models.project import Project
            project = Project.query.get(instance.object_id)
            if project:
                if action == ApprovalAction.APPROVE and instance.status == ApprovalStatus.APPROVED:
                    snap = instance.template_snapshot or {}
                    target_stage = snap.get('hold_target')
                    if target_stage in ('lost', 'paused'):
                        old_stage = project.current_stage
                        project.current_stage = target_stage
                        try:
                            from app.models.projectpm_stage_history import ProjectStageHistory
                            ProjectStageHistory.add_history_record(
                                project_id=project.id,
                                from_stage=old_stage,
                                to_stage=target_stage,
                                remarks=f"失败/搁置审核通过：{snap.get('hold_reason') or ''}".strip(),
                                account_id=user_id,
                                commit=False,
                            )
                        except Exception as _hist_err:
                            current_app.logger.warning(f"记录失败/搁置阶段历史失败: {_hist_err}")
                        current_app.logger.info(
                            f"项目 {project.project_name} 失败/搁置审核通过: {old_stage} → {target_stage}")
                elif action == ApprovalAction.REJECT:
                    current_app.logger.info(
                        f"项目 {project.project_name} 失败/搁置审核被驳回，维持原阶段")

        elif instance.object_type == 'project_win_lock':
            # 成功锁定审核(gated):整条通过才真正 win_locked(打金额/报价/交期快照);驳回不锁。
            from app.models.project import Project
            project = Project.query.get(instance.object_id)
            if project:
                if action == ApprovalAction.APPROVE and instance.status == ApprovalStatus.APPROVED:
                    snap = instance.template_snapshot or {}
                    from app.models.quotation import Quotation
                    qid = snap.get('wl_quotation_id')
                    lock_q = Quotation.query.get(qid) if qid else None
                    project.win_locked = True
                    project.win_lock_reason = snap.get('wl_reason')
                    project.win_locked_by = snap.get('wl_initiator_id') or user_id
                    project.win_locked_at = datetime.now()
                    if lock_q:
                        project.win_locked_quotation_id = lock_q.id
                        project.win_locked_amount = float(lock_q.amount or 0)
                    dlv = snap.get('wl_delivery')
                    if dlv:
                        try:
                            from datetime import date as _date
                            project.delivery_forecast = _date.fromisoformat(dlv)
                        except Exception:
                            pass
                    current_app.logger.info(f"项目 {project.project_name} 成功锁定审核通过 → 已锁定")
                elif action == ApprovalAction.REJECT:
                    current_app.logger.info(f"项目 {project.project_name} 成功锁定审核被驳回，不锁定")

        elif instance.object_type == 'dealer_apply':
            # 客户渠道身份审批:整条流程通过 → company_type=目标身份;驳回 → 仅清 pending
            from app.models.customer import Company
            comp = Company.query.get(instance.object_id)
            if comp:
                if action == ApprovalAction.APPROVE and instance.status == ApprovalStatus.APPROVED:
                    snap = instance.template_snapshot or {}
                    target = snap.get('dealer_target')
                    if target in ('dealer', 'distributor'):
                        comp.company_type = target
                        comp.pending_company_type = None
                        current_app.logger.info(
                            f"客户 {comp.company_name} 渠道身份审批通过: company_type={target}")
                elif action == ApprovalAction.REJECT:
                    comp.pending_company_type = None
                    current_app.logger.info(
                        f"客户 {comp.company_name} 渠道身份审批被驳回,身份维持原状")

        elif instance.object_type == 'perf_settlement':
            # 季度绩效结算:整条通过 → 折算金额写入薪资绩效项该季末月 + 锁定;驳回 → 标记
            from app.models.performance_settlement import PerformanceSettlement
            st = PerformanceSettlement.query.get(instance.object_id)
            if st:
                if action == ApprovalAction.APPROVE and instance.status == ApprovalStatus.APPROVED:
                    from datetime import datetime as _dt
                    from app.models.salary_structure import UserSalaryItem
                    _Q_END = {1: 3, 2: 6, 3: 9, 4: 12}
                    end_m = str(_Q_END[st.quarter])
                    row = UserSalaryItem.query.filter_by(
                        user_id=st.user_id, year=st.year,
                        item_code='performance_salary', is_personal=False).first()
                    if not row:
                        row = UserSalaryItem(user_id=st.user_id, year=st.year,
                                             item_code='performance_salary', is_personal=False,
                                             created_by=user_id)
                        db.session.add(row)
                    m = dict(row.monthly_amounts or {})
                    m[end_m] = float(st.settled_amount or 0)
                    row.monthly_amounts = m
                    from sqlalchemy.orm.attributes import flag_modified as _fm
                    _fm(row, 'monthly_amounts')
                    st.status = 'approved'
                    st.is_locked = True
                    st.settled_at = _dt.utcnow()
                    current_app.logger.info(
                        f"绩效结算通过: user={st.user_id} {st.year}Q{st.quarter} "
                        f"得分={st.score} 折算={st.settled_amount} → 薪资{end_m}月")
                elif action == ApprovalAction.REJECT:
                    st.status = 'rejected'
                    st.is_locked = False
                    current_app.logger.info(
                        f"绩效结算被驳回: user={st.user_id} {st.year}Q{st.quarter}")

        elif instance.object_type == 'salary_run':
            # 月度薪资审批:终审通过 → 永久锁定(已在提交时锁);驳回 → 解锁可改后重提
            from app.models.salary_structure import SalaryRun
            run = SalaryRun.query.get(instance.object_id)
            if run:
                if action == ApprovalAction.APPROVE and instance.status == ApprovalStatus.APPROVED:
                    from datetime import datetime as _dt
                    run.status = 'approved'
                    run.is_locked = True
                    run.settled_at = _dt.utcnow()
                    current_app.logger.info(
                        f"月度薪资审批通过并固化: {run.company_name} {run.year}-{run.month} "
                        f"人数={run.headcount} 合计={run.total_amount}")
                elif action == ApprovalAction.REJECT:
                    run.status = 'rejected'
                    run.is_locked = False
                    current_app.logger.info(
                        f"月度薪资审批被驳回,解锁: {run.company_name} {run.year}-{run.month}")

        elif instance.object_type == 'customer':
            # 客户审批状态更新逻辑（如果需要的话）
            # 这里可以根据客户的具体需求来实现
            pass

        elif instance.object_type == 'purchase_order':
            # 更新订单的状态（订单审批状态通过通用审批系统管理，不在订单表中存储）
            from app.models.inventory import PurchaseOrder
            order = PurchaseOrder.query.get(instance.object_id)
            
            if order:
                if action == ApprovalAction.APPROVE:
                    # 审批通过
                    if instance.status == ApprovalStatus.APPROVED:
                        # 流程完全通过
                        order.status = 'approved'

                        # 自动生成序列号
                        try:
                            from app.services.serial_number_service import generate_serial_numbers_for_order
                            result = generate_serial_numbers_for_order(order, user_id)
                            if result['success']:
                                current_app.logger.info(f"订单 {order.order_number} 自动生成 {len(result['serial_numbers'])} 个序列号")
                            else:
                                current_app.logger.warning(f"订单 {order.order_number} 序列号生成失败: {result['message']}")
                                # 记录详细错误但不阻断审批流程
                                for error in result.get('errors', []):
                                    current_app.logger.warning(f"  - {error}")
                        except Exception as e:
                            current_app.logger.error(f"序列号生成异常: {str(e)}")
                            # 不抛出异常，避免影响审批流程
                    else:
                        # 还在审批中
                        order.status = 'pending'
                elif action == ApprovalAction.REJECT:
                    # 审批拒绝
                    order.status = 'rejected'

                current_app.logger.info(f"订单 {order.order_number} 状态已更新为: {order.status}")
                
        elif instance.object_type == 'expense':
            # 更新报销单的状态
            from app.models.expense import Expense
            expense = Expense.query.get(instance.object_id)
            
            if expense:
                if action == ApprovalAction.APPROVE:
                    # 审批通过
                    if instance.status == ApprovalStatus.APPROVED:
                        # 流程完全通过 - 检查刚完成的步骤类型
                        current_step_info = instance.get_current_step_info() or {}
                        last_step_action_type = current_step_info.get('action_type')
                        
                        if last_step_action_type == 'payment_processing':
                            # 刚完成的是支付步骤，更新为已支付状态
                            expense.status = 'paid'
                            if hasattr(expense, 'payment_status'):
                                expense.payment_status = 'paid'
                            if hasattr(expense, 'payment_date') and not expense.payment_date:
                                expense.payment_date = datetime.now()
                            if hasattr(expense, 'paid_by') and not expense.paid_by:
                                expense.paid_by = user_id
                            current_app.logger.info(f"报销单 {expense.expense_number} 支付审批完成，状态更新为已支付: paid")
                        else:
                            # 其他步骤完成，检查是否有支付步骤
                            has_payment_steps = _has_payment_steps_in_process(instance)
                            
                            if has_payment_steps:
                                # 如果有支付步骤，状态应为待支付
                                expense.status = 'awaiting_payment'
                                if hasattr(expense, 'payment_status'):
                                    expense.payment_status = 'awaiting'
                                current_app.logger.info(f"报销单 {expense.expense_number} 审批完成，状态更新为待支付: awaiting_payment")
                            else:
                                # 如果没有支付步骤，直接审批通过
                                expense.status = 'approved'
                            expense.approved_at = datetime.now()
                            expense.approved_by = user_id
                            current_app.logger.info(f"报销单 {expense.expense_number} 审批完成，状态更新为: approved")
                    else:
                        # 还在审批中
                        expense.status = 'pending'
                        current_app.logger.info(f"报销单 {expense.expense_number} 审批中，状态保持为: pending")
                elif action == ApprovalAction.REJECT:
                    # 审批拒绝
                    expense.status = 'rejected'
                    # 注意：报销单模型没有rejected_at和rejected_by字段，只更新状态
                    current_app.logger.info(f"报销单 {expense.expense_number} 审批被拒绝，状态更新为: rejected")
        
        else:
            # 通用处理逻辑 - 支持所有在BRANCH_OBJECT_TYPE_MAPPING中配置的对象类型
            # 包括: pricing_order, project, customer等
            current_app.logger.info(f"使用通用状态更新逻辑处理 {instance.object_type} 类型对象")
            _update_generic_object_status(instance, action, user_id, comment)
            
    except Exception as e:
        current_app.logger.error(f"更新业务对象审批状态失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc()) 


def _has_payment_steps_in_process(instance):
    """检查审批流程中是否包含支付步骤
    
    Args:
        instance: 审批实例对象
        
    Returns:
        bool: 如果包含支付步骤返回True，否则返回False
    """
    try:
        # 获取流程中的所有步骤
        steps = instance.get_steps()
        
        if not steps:
            return False
            
        # 检查步骤类型 - 支持快照和模型对象两种情况
        for step in steps:
            if isinstance(step, dict):
                # 快照数据（字典格式）
                action_type = step.get('action_type', '')
            else:
                # 模型对象
                action_type = getattr(step, 'action_type', '')
            
            # 检查是否为支付处理动作
            if action_type == 'payment_processing':
                current_app.logger.info(f"流程 {instance.id} 包含支付步骤")
                return True
                
        current_app.logger.info(f"流程 {instance.id} 不包含支付步骤")
        return False
        
    except Exception as e:
        current_app.logger.error(f"检查支付步骤失败: {str(e)}")
        return False


def _update_expense_status_for_payment_stage(instance, user_id, comment):
    """当审批流程进入支付阶段时更新报销单状态
    
    Args:
        instance: 审批实例对象
        user_id: 操作人ID
        comment: 审批意见
    """
    try:
        from app.models.expense import Expense
        expense = Expense.query.get(instance.object_id)
        
        if expense:
            # 更新为待支付状态
            expense.status = 'awaiting_payment'
            if hasattr(expense, 'payment_status'):
                expense.payment_status = 'awaiting'
            current_app.logger.info(f"报销单 {expense.expense_number} 进入支付阶段，状态更新为: awaiting_payment")
            
    except Exception as e:
        current_app.logger.error(f"更新报销单支付阶段状态失败: {str(e)}")


def lock_expense(expense_id, user_id=None):
    """锁定报销单，防止编辑
    
    Args:
        expense_id: 报销单ID
        user_id: 锁定人ID，默认为当前登录用户
        
    Returns:
        布尔值，表示是否成功锁定
    """
    from app.models.expense import Expense
    
    expense = Expense.query.get(expense_id)
    if not expense:
        current_app.logger.error(f"报销单不存在: {expense_id}")
        return False
    
    # 如果报销单已经被锁定，返回True
    if expense.is_locked:
        current_app.logger.info(f"报销单已被锁定: {expense_id}")
        return True
    
    try:
        expense.is_locked = True
        db.session.commit()
        current_app.logger.info(f"报销单已锁定: {expense_id}, 锁定人: {user_id}")
        return True
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"锁定报销单失败: {expense_id}, 错误: {str(e)}")
        return False


def unlock_expense(expense_id, user_id=None):
    """解锁报销单
    
    Args:
        expense_id: 报销单ID
        user_id: 解锁人ID，默认为当前登录用户
        
    Returns:
        布尔值，表示是否成功解锁
    """
    from app.models.expense import Expense
    
    expense = Expense.query.get(expense_id)
    if not expense:
        current_app.logger.error(f"报销单不存在: {expense_id}")
        return False
    
    # 如果报销单未被锁定，返回True
    if not expense.is_locked:
        current_app.logger.info(f"报销单未被锁定: {expense_id}")
        return True
    
    try:
        expense.is_locked = False
        db.session.commit()
        current_app.logger.info(f"报销单已解锁: {expense_id}, 解锁人: {user_id}")
        return True
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"解锁报销单失败: {expense_id}, 错误: {str(e)}")
        return False


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


def get_purchase_order_by_id(order_id):
    """根据ID获取订单对象
    
    Args:
        order_id: 订单ID
        
    Returns:
        订单对象，如果不存在则返回None
    """
    try:
        from app.models.inventory import PurchaseOrder
        return PurchaseOrder.query.get(order_id)
    except Exception as e:
        current_app.logger.error(f"获取订单失败: {str(e)}")
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
    from app.models.pricing_order import PricingOrder
    from sqlalchemy import or_, and_
    
    # 获取用户信息，检查是否为商务助理
    from app.models.user import User
    target_user = User.query.get(user_id)
    if not target_user:
        # 如果用户不存在，返回空结果
        try:
            from flask_sqlalchemy import Pagination
        except ImportError:
            from flask_sqlalchemy.pagination import Pagination
        return Pagination(None, page=page, per_page=per_page, total=0, items=[])
    
    # 确定查询范围：商务助理可以查看部门内（同公司）所有用户的批价单
    if target_user.role and target_user.role.strip() == 'business_admin':
        # 商务助理：查看同公司所有用户的批价单
        department_users = User.query.filter_by(company_name=target_user.company_name).all()
        user_ids_to_query = [u.id for u in department_users]
    else:
        # 其他用户：只查看与自己相关的批价单
        user_ids_to_query = [user_id]
    
    # 构建查询条件
    conditions = []
    
    # 1. 用户或部门内用户创建的批价单
    conditions.append(PricingOrder.created_by.in_(user_ids_to_query))
    
    # 2. 用户是审批人的批价单 - 使用V2统一审批系统
    # 查询ApprovalInstance表，找到用户作为审批人的批价单
    pricing_order_instances = ApprovalInstance.query.filter(
        ApprovalInstance.object_type == 'pricing_order'
    ).all()
    
    # 通过动态审批人匹配找到用户相关的批价单ID
    user_approved_pricing_order_ids = []
    for instance in pricing_order_instances:
        try:
            current_step_info = instance.get_current_step_info()
            if current_step_info:
                actual_approver = get_step_actual_approver(current_step_info, instance)
                if actual_approver and actual_approver.id == user_id:
                    user_approved_pricing_order_ids.append(instance.object_id)
        except Exception:
            continue
    
    if user_approved_pricing_order_ids:
        conditions.append(PricingOrder.id.in_(user_approved_pricing_order_ids))
    
    # 3. 用户是项目销售负责人的批价单
    conditions.append(
        and_(
            PricingOrder.project_id.isnot(None),
            PricingOrder.project.has(vendor_sales_manager_id=user_id)
        )
    )
    
    # 构建主查询
    query = PricingOrder.query.filter(or_(*conditions))
    
    # 添加基于用户角色的项目类型权限过滤
    # 获取指定用户的信息
    from app.models.user import User
    target_user = User.query.get(user_id)
    if target_user and target_user.role != 'admin':
        # 根据权限配置过滤项目类型
        # 注：各角色可见的项目类型通过权限配置系统控制
        # - pricing_order 模块的 content_filters 字段配置可见的 project_type
        # 例如：渠道经理配置 content_filters = {"project_type": ["channel_follow"]}

        # 添加项目关联
        query = query.join(Project, PricingOrder.project_id == Project.id)

        # 获取用户权限配置中的 content_filters
        permission = target_user.get_permission_config('pricing_order')
        if permission and hasattr(permission, 'content_filters') and permission.content_filters:
            content_filters = permission.content_filters
            if isinstance(content_filters, dict) and 'project_type' in content_filters:
                allowed_types = content_filters.get('project_type', [])
                if allowed_types:
                    query = query.filter(Project.project_type.in_(allowed_types))
        # 无 content_filters 限制时，不添加额外过滤（按权限级别控制）
    
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
    else:
        # 默认排除已完成的审批（approved/rejected），审批中心只显示待处理项
        query = query.filter(PricingOrder.status.notin_(['approved', 'rejected']))

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
    
    # 包装为审批实例格式（使用顶部定义的统一 PricingOrderApprovalWrapper 类）
    # 包装分页对象
    wrapped_items = [PricingOrderApprovalWrapper(po) for po in pricing_orders.items]
    pricing_orders.items = wrapped_items
    
    return pricing_orders


def get_user_order_approvals(user_id, status_filter=None, page=1, per_page=20):
    """获取用户相关的订单审批
    
    Args:
        user_id: 用户ID
        status_filter: 状态筛选
        page: 页码
        per_page: 每页数量
        
    Returns:
        分页对象，包含OrderApprovalWrapper对象列表
    """
    from app.models.inventory import PurchaseOrder
    from app.models.approval import ApprovalInstance
    from sqlalchemy import or_, and_
    
    # 获取用户信息，检查是否为商务助理
    from app.models.user import User
    target_user = User.query.get(user_id)
    if not target_user:
        # 如果用户不存在，返回空结果
        try:
            from flask_sqlalchemy import Pagination
        except ImportError:
            from flask_sqlalchemy.pagination import Pagination
        return Pagination(None, page=page, per_page=per_page, total=0, items=[])
    
    # 确定查询范围：商务助理可以查看部门内（同公司）所有用户的订单
    if target_user.role and target_user.role.strip() == 'business_admin':
        # 商务助理：查看同公司所有用户的订单
        department_users = User.query.filter_by(company_name=target_user.company_name).all()
        user_ids_to_query = [u.id for u in department_users]
    else:
        # 其他用户：只查看与自己相关的订单
        user_ids_to_query = [user_id]
    
    # 构建基础查询
    query = PurchaseOrder.query
    
    # 获取用户作为审批人的审批实例的订单ID
    approval_subquery = db.session.query(ApprovalInstance.object_id).filter(
        ApprovalInstance.object_type == 'purchase_order',
        ApprovalInstance.current_step.in_(
            db.session.query(ApprovalStep.step_order).filter(
                ApprovalStep.process_id == ApprovalInstance.process_id,
                ApprovalStep.approver_user_id == user_id
            )
        )
    ).subquery().select()
    
    # 获取用户是当前待审批人的订单ID
    current_approver_subquery = db.session.query(ApprovalInstance.object_id).filter(
        ApprovalInstance.object_type == 'purchase_order',
        ApprovalInstance.status == ApprovalStatus.PENDING,
        ApprovalInstance.current_step.in_(
            db.session.query(ApprovalStep.step_order).filter(
                ApprovalStep.process_id == ApprovalInstance.process_id,
                ApprovalStep.approver_user_id == user_id
            )
        )
    ).subquery().select()
    
    # 组合查询条件
    conditions = [
        PurchaseOrder.created_by_id.in_(user_ids_to_query),  # 用户或部门内用户创建的订单
        PurchaseOrder.id.in_(approval_subquery),  # 用户需要审批的订单
        PurchaseOrder.id.in_(current_approver_subquery)  # 用户是当前待审批人的订单
    ]
    
    query = query.filter(or_(*conditions))
    
    # 状态筛选
    if status_filter:
        query = query.filter(PurchaseOrder.status == status_filter)
    
    # 排序
    query = query.order_by(PurchaseOrder.created_at.desc())
    
    # 分页
    pagination = query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )
    
    # 使用顶部定义的统一 OrderApprovalWrapper 类
    # 包装为审批对象
    wrapped_items = []
    for order in pagination.items:
        wrapped_items.append(OrderApprovalWrapper(order))
    
    # 创建新的分页对象
    try:
        from flask_sqlalchemy import Pagination
    except ImportError:
        # 如果无法导入Pagination，创建一个简单的分页对象
        class Pagination:
            def __init__(self, query, page, per_page, total, items):
                self.query = query
                self.page = page
                self.per_page = per_page
                self.total = total
                self.items = items
                self.pages = (total + per_page - 1) // per_page if per_page > 0 else 1
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
    
    wrapped_pagination = Pagination(
        query=query,
        page=page,
        per_page=per_page,
        total=pagination.total,
        items=wrapped_items
    )
    
    return wrapped_pagination


def rollback_order_approval(order_id, admin_user_id, reason=None):
    """
    管理员将已通过的订单审批退回到初始状态
    
    Args:
        order_id: 订单ID
        admin_user_id: 管理员用户ID
        reason: 退回原因
        
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        from app.models.inventory import PurchaseOrder
        from app.models.user import User
        
        # 验证管理员权限
        admin_user = User.query.get(admin_user_id)
        if not admin_user or admin_user.role != 'admin':
            return False, "只有管理员可以执行退回操作"
        
        # 获取订单
        order = PurchaseOrder.query.get(order_id)
        if not order:
            return False, "订单不存在"
        
        # 检查订单状态 - 只能退回已通过的订单
        if order.status != 'approved':
            return False, f"只能退回已通过的订单，当前状态：{order.status}"
        
        # 开始数据库事务
        from app import db
        
        # 1. 查找并删除相关的审批实例
        approval_instances = ApprovalInstance.query.filter_by(
            object_type='purchase_order',
            object_id=order_id
        ).all()
        
        for instance in approval_instances:
            # 删除审批记录
            ApprovalRecord.query.filter_by(instance_id=instance.id).delete()
            # 删除审批实例
            db.session.delete(instance)
        
        # 2. 重置订单状态为草稿
        order.status = 'draft'
        order.approved_by_id = None
        order.approved_at = None
        
        # 3. 记录操作日志（如果有审计系统）
        current_app.logger.info(
            f"管理员 {admin_user.username} (ID: {admin_user_id}) "
            f"将订单 {order.order_number} (ID: {order_id}) 的审批状态退回到草稿状态。"
            f"原因：{reason or '未提供'}"
        )
        
        # 提交事务
        db.session.commit()
        
        return True, "订单审批已成功退回到草稿状态"
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"订单审批退回失败: {str(e)}")
        return False, f"退回失败：{str(e)}"


def can_rollback_order_approval(order_id, user_id):
    """
    检查用户是否可以退回订单审批
    
    Args:
        order_id: 订单ID
        user_id: 用户ID
        
    Returns:
        bool: 是否可以退回
    """
    try:
        from app.models.inventory import PurchaseOrder
        from app.models.user import User
        
        # 检查用户权限
        user = User.query.get(user_id)
        if not user or user.role != 'admin':
            return False
        
        # 检查订单状态
        order = PurchaseOrder.query.get(order_id)
        if not order or order.status != 'approved':
            return False
        
        return True
        
    except Exception:
        return False


def get_pending_created_count(user_id=None):
    """获取用户发起的未结束流程数量（用于我发起的页签数字标记）
    
    Args:
        user_id: 用户ID，默认为当前登录用户
        
    Returns:
        未结束流程数量
    """
    if user_id is None:
        user_id = current_user.id
    
    try:
        # 统计通用审批系统中的未结束流程
        general_pending = ApprovalInstance.query.filter(
            ApprovalInstance.created_by == user_id,
            ApprovalInstance.status == ApprovalStatus.PENDING
        ).count()
        
        # 统计批价单中的未结束流程
        from app.models.pricing_order import PricingOrder
        pricing_pending = PricingOrder.query.filter(
            PricingOrder.created_by == user_id,
            PricingOrder.status.in_(['draft', 'pending'])
        ).count()
        
        # 统计订单中的未结束流程  
        from app.models.inventory import PurchaseOrder
        order_pending = PurchaseOrder.query.filter(
            PurchaseOrder.created_by_id == user_id,
            PurchaseOrder.status.in_(['draft', 'pending'])
        ).count()
        
        return general_pending + pricing_pending + order_pending
        
    except Exception as e:
        from app import current_app
        current_app.logger.error(f"获取用户发起的未结束流程数量失败: {str(e)}")
        return 0

def check_step_discount_violations(pricing_order, step_order, user_id):
    """
    检查指定审批步骤中是否存在折扣权限违规
    
    Args:
        pricing_order: 批价单对象
        step_order: 审批步骤顺序
        user_id: 用户ID
        
    Returns:
        dict: {
            'has_violation': bool,  # 是否存在违规
            'violations': list,     # 违规详情列表
            'user_limits': dict     # 用户权限限制
        }
    """
    from app.models.user import User
    from app.services.discount_permission_service import DiscountPermissionService
    
    try:
        # 获取用户信息
        user = User.query.get(user_id)
        if not user:
            return {'has_violation': False, 'violations': [], 'user_limits': {}}
        
        # 获取用户的折扣权限限制
        user_limits = DiscountPermissionService.get_user_discount_limits(user)
        
        violations = []
        
        # 检查批价单明细的折扣率
        if user_limits['pricing_discount_limit'] is not None:
            for detail in pricing_order.pricing_details:
                # 将折扣率转换为百分比进行比较
                detail_discount_pct = detail.discount_rate * 100 if detail.discount_rate else 0
                if detail_discount_pct < user_limits['pricing_discount_limit']:
                    violations.append({
                        'type': 'pricing_detail',
                        'product_name': detail.product_name,
                        'model': detail.product_model,
                        'discount_rate': detail.discount_rate,
                        'limit': user_limits['pricing_discount_limit'],
                        'step_order': step_order
                    })
        
        # 检查批价单总折扣率
        if (user_limits['pricing_discount_limit'] is not None and 
            pricing_order.pricing_discount_percentage and 
            pricing_order.pricing_discount_percentage < user_limits['pricing_discount_limit']):
            violations.append({
                'type': 'pricing_total',
                'discount_rate': pricing_order.pricing_discount_percentage,
                'limit': user_limits['pricing_discount_limit'],
                'step_order': step_order
            })
        
        # 检查结算单明细的折扣率
        if user_limits['settlement_discount_limit'] is not None:
            for detail in pricing_order.settlement_details:
                if detail.discount_rate and detail.discount_rate < user_limits['settlement_discount_limit']:
                    violations.append({
                        'type': 'settlement_detail',
                        'product_name': detail.product_name,
                        'model': detail.product_model,
                        'discount_rate': detail.discount_rate,
                        'limit': user_limits['settlement_discount_limit'],
                        'step_order': step_order
                    })
        
        # 检查结算单总折扣率
        if (user_limits['settlement_discount_limit'] is not None and 
            pricing_order.settlement_discount_percentage and 
            pricing_order.settlement_discount_percentage < user_limits['settlement_discount_limit']):
            violations.append({
                'type': 'settlement_total',
                'discount_rate': pricing_order.settlement_discount_percentage,
                'limit': user_limits['settlement_discount_limit'],
                'step_order': step_order
            })
        
        return {
            'has_violation': len(violations) > 0,
            'violations': violations,
            'user_limits': user_limits
        }
        
    except Exception as e:
        current_app.logger.error(f"检查折扣权限违规失败: {str(e)}")
        return {'has_violation': False, 'violations': [], 'user_limits': {}}


def get_approval_step_discount_status(pricing_order):
    """
    获取批价单审批流程中各步骤的折扣权限状态
    
    注意：快速审批功能已取消，但保留权限提示徽章功能
    当审批人超出权限范围时，在其所在的审批环节显示权限徽章
    
    Args:
        pricing_order: 批价单对象
        
    Returns:
        dict: 步骤顺序 -> 权限状态的映射
    """
    try:
        step_statuses = {}
        
        # 检查流程发起人（创建者）的权限
        if pricing_order.created_by:
            creator_status = check_step_discount_violations(
                pricing_order, 0, pricing_order.created_by
            )
            if creator_status['has_violation']:
                from app.models.user import User
                creator = User.query.get(pricing_order.created_by)
                step_statuses[0] = {
                    'has_violation': True,
                    'violations': creator_status['violations'],
                    'user_role': creator.role if creator else 'unknown',
                    'user_name': creator.username if creator else '未知用户'
                }
        
        # 检查已完成的审批记录（只检查已审批通过或提交的步骤）
        for record in pricing_order.approval_records:
            if record.action and record.approver_id:  # 只检查已审批的步骤
                record_status = check_step_discount_violations(
                    pricing_order, record.step_order, record.approver_id
                )
                if record_status['has_violation']:
                    step_statuses[record.step_order] = {
                        'has_violation': True,
                        'violations': record_status['violations'],
                        'user_role': record.approver_role,
                        'user_name': record.approver.username if record.approver else '未知用户'
                    }
        
        # 注意：不检查当前待审批步骤的权限，只在审批提交后才显示权限徽章
        # 这样确保权限徽章只在审批人已经做出决策后才显示
        
        return step_statuses
        
    except Exception as e:
        current_app.logger.error(f"获取审批步骤权限状态失败: {str(e)}")
        return {}

def process_approval_stage(stage_id, action, comment=None, processed_by_id=None):
    """处理审批阶段操作 - 标准化API版本
    
    Args:
        stage_id: 审批阶段/步骤ID
        action: 审批动作 ('approve', 'reject')
        comment: 审批意见
        processed_by_id: 操作人ID
        
    Returns:
        dict: {
            'success': bool,
            'message': str,
            'approval_completed': bool,
            'final_status': str
        }
    """
    try:
        from app.models.approval import ApprovalInstance, ApprovalRecord, ApprovalAction, ApprovalStatus
        from app import db
        
        # 注意：这个函数现在主要作为备用，实际的订单审批已经在路由中直接处理
        # 保留此函数以支持其他可能的调用
        return {
            'success': False,
            'message': '此函数已废弃，请使用路由中的直接审批处理',
            'approval_completed': False,
            'final_status': None
        }
        
        # 转换action为枚举
        if action == 'approve':
            approval_action = ApprovalAction.APPROVE
        elif action == 'reject':
            approval_action = ApprovalAction.REJECT  
        else:
            return {
                'success': False,
                'message': f'无效的审批动作: {action}',
                'approval_completed': False,
                'final_status': None
            }
        
        # 调用现有的审批处理函数
        success = process_approval(
            instance_id=target_instance.id,
            action=approval_action,
            comment=comment,
            user_id=processed_by_id
        )
        
        if not success:
            return {
                'success': False,
                'message': '审批处理失败',
                'approval_completed': False,
                'final_status': None
            }
        
        # 重新查询实例状态
        db.session.refresh(target_instance)
        
        # 检查审批是否完成
        approval_completed = target_instance.status != ApprovalStatus.PENDING
        final_status = None
        
        if approval_completed:
            if target_instance.status == ApprovalStatus.APPROVED:
                final_status = 'approved'
            elif target_instance.status == ApprovalStatus.REJECTED:
                final_status = 'rejected'
        
        return {
            'success': True,
            'message': '审批处理成功',
            'approval_completed': approval_completed,
            'final_status': final_status
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'message': f'处理失败：{str(e)}',
            'approval_completed': False,
            'final_status': None
        }


def can_recall_approval(object_type, object_id, user_id):
    """
    检查用户是否可以召回审批流程
    
    Args:
        object_type: 对象类型
        object_id: 对象ID
        user_id: 用户ID
        
    Returns:
        布尔值，表示是否可以召回
    """
    try:
        # 获取审批实例
        approval_instance = get_object_approval_instance(object_type, object_id)
        if not approval_instance:
            return False
        
        # 只有在待审批状态下才能召回
        if approval_instance.status != ApprovalStatus.PENDING:
            return False
        
        # 获取用户信息检查权限
        from app.models.user import User
        user = User.query.get(user_id)
        if not user:
            return False
            
        # 发起人可以召回，或者管理员可以召回任何审批
        if approval_instance.created_by == user_id or user.role == 'admin':
            return True
        
        return False
        
    except Exception as e:
        current_app.logger.error(f"检查召回权限失败: {str(e)}")
        return False


def recall_approval(object_type, object_id, user_id, reason=None):
    """
    召回审批流程
    
    Args:
        object_type: 对象类型
        object_id: 对象ID  
        user_id: 召回人ID
        reason: 召回原因
        
    Returns:
        字典，包含操作结果
    """
    try:
        # 检查召回权限
        if not can_recall_approval(object_type, object_id, user_id):
            return {
                'success': False,
                'message': '无权限召回或审批流程已无法召回'
            }
        
        # 获取审批实例
        approval_instance = get_object_approval_instance(object_type, object_id)
        
        # 更新审批实例状态为召回（使用REJECTED状态，通过action字段区分）
        approval_instance.status = ApprovalStatus.REJECTED
        approval_instance.ended_at = datetime.now()
        
        # 添加召回记录
        recall_record = ApprovalRecord(
            instance_id=approval_instance.id,
            step_id=None,  # 召回不属于特定步骤
            approver_id=user_id,
            action='recall',
            comment=reason or '流程召回',
            timestamp=datetime.now()
        )
        
        db.session.add(recall_record)
        
        # 更新业务对象状态为草稿
        update_business_object_status(object_type, object_id, 'draft')

        # 客户渠道身份审批召回 → 清 pending(身份不变)
        if object_type == 'dealer_apply':
            try:
                from app.models.customer import Company as _C
                _comp = _C.query.get(object_id)
                if _comp:
                    _comp.pending_company_type = None
            except Exception:
                pass

        # 绩效结算召回 → 标记为草稿,解锁(尚未结算)
        if object_type == 'perf_settlement':
            try:
                from app.models.performance_settlement import PerformanceSettlement as _PS
                _st = _PS.query.get(object_id)
                if _st:
                    _st.status = 'draft'
                    _st.is_locked = False
            except Exception:
                pass

        # 月度薪资审批召回 → 草稿,解锁该公司该月个人薪资
        if object_type == 'salary_run':
            try:
                from app.models.salary_structure import SalaryRun as _SR
                _run = _SR.query.get(object_id)
                if _run:
                    _run.status = 'draft'
                    _run.is_locked = False
            except Exception:
                pass

        # 项目失败审核召回 → 清除已打的失败归因标(流程作废)
        if object_type == 'project_hold':
            try:
                from app.models.project import Project as _P
                _proj = _P.query.get(object_id)
                if _proj:
                    _proj.fail_owner_fault = False
                    _proj.fail_mgmt_fault = False
            except Exception:
                pass

        db.session.commit()
        
        current_app.logger.info(f"审批流程召回成功: {object_type}#{object_id}, 召回人: {user_id}")
        
        return {
            'success': True,
            'message': '审批流程召回成功'
        }
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"召回审批流程失败: {str(e)}")
        return {
            'success': False,
            'message': f'召回失败：{str(e)}'
        }


def can_resubmit_approval(object_type, object_id, user_id):
    """
    检查用户是否可以重新提交审批
    
    Args:
        object_type: 对象类型
        object_id: 对象ID
        user_id: 用户ID
        
    Returns:
        布尔值，表示是否可以重新提交
    """
    try:
        # 获取审批实例（包含被拒绝的实例）
        approval_instance = get_object_approval_instance(object_type, object_id, include_rejected=True)
        if not approval_instance:
            return True  # 没有审批实例，可以提交
        
        # 只有在被拒绝或召回状态下才能重新提交
        if approval_instance.status != ApprovalStatus.REJECTED:
            return False
            
        # 检查是否是召回状态（通过最后一个记录的action判断）
        last_record = ApprovalRecord.query.filter_by(
            instance_id=approval_instance.id
        ).order_by(ApprovalRecord.timestamp.desc()).first()
        
        # 如果最后一个记录是召回或拒绝，才能重新提交
        if not last_record or last_record.action not in ['recall', 'reject']:
            return False
            
        # 只有提交人可以重新提交
        if approval_instance.created_by != user_id:
            return False
            
        return True
        
    except Exception as e:
        current_app.logger.error(f"检查重新提交权限失败: {str(e)}")
        return False


def resubmit_approval(object_type, object_id, user_id):
    """
    重新提交审批流程

    重新提交时删除旧实例，使用最新的审批模板配置创建全新实例。
    这样可以确保：
    - 模板快照使用最新配置（包括步骤、执行条件等）
    - 动态调整逻辑（授权审批人、归属人等）重新执行
    - 执行条件基于当前业务数据重新评估

    Args:
        object_type: 对象类型
        object_id: 对象ID
        user_id: 提交人ID

    Returns:
        字典，包含操作结果
    """
    try:
        # 检查重新提交权限
        if not can_resubmit_approval(object_type, object_id, user_id):
            return {
                'success': False,
                'message': '无权限重新提交或审批流程状态不允许重新提交'
            }

        # 获取现有审批实例，如果存在则删除（级联删除审批记录）
        approval_instance = get_object_approval_instance(object_type, object_id)
        template_id = None
        if approval_instance:
            template_id = approval_instance.process_id
            old_instance_id = approval_instance.id
            db.session.delete(approval_instance)
            db.session.flush()
            current_app.logger.info(f"重新提交: 已删除旧审批实例 {old_instance_id}")

        # 确定使用的审批模板
        if not template_id:
            templates = get_available_templates(object_type)
            if not templates:
                return {
                    'success': False,
                    'message': '未找到适用的审批流程模板'
                }
            template_id = templates[0].id

        # 使用最新模板配置创建全新审批实例
        new_instance = start_approval_process(
            object_type, object_id, template_id, user_id, auto_commit=False
        )

        if not new_instance:
            return {
                'success': False,
                'message': '创建审批实例失败'
            }

        # 更新业务对象状态为待审批
        update_business_object_status(object_type, object_id, 'pending')
        db.session.commit()

        current_app.logger.info(f"重新提交审批成功: {object_type}#{object_id}, 提交人: {user_id}, 新实例: {new_instance.id}")

        return {
            'success': True,
            'message': '重新提交审批成功'
        }

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"重新提交审批失败: {str(e)}")
        return {
            'success': False,
            'message': f'重新提交失败：{str(e)}'
        }


def update_business_object_status(object_type, object_id, status):
    """
    更新业务对象状态
    
    Args:
        object_type: 对象类型
        object_id: 对象ID
        status: 新状态
    """
    try:
        if object_type == 'project':
            from app.models.project import Project
            obj = Project.query.get(object_id)
            if obj:
                obj.status = status
                
        elif object_type == 'quotation':
            from app.models.quotation import Quotation
            obj = Quotation.query.get(object_id)
            if obj:
                obj.status = status
                
        elif object_type == 'customer':
            from app.models.customer import Company
            obj = Company.query.get(object_id)
            if obj:
                obj.status = status
                
        elif object_type == 'purchase_order':
            from app.models.inventory import PurchaseOrder
            obj = PurchaseOrder.query.get(object_id)
            if obj:
                obj.status = status
                
        current_app.logger.info(f"业务对象状态更新: {object_type}#{object_id} -> {status}")
        
    except Exception as e:
        current_app.logger.error(f"更新业务对象状态失败: {str(e)}")


def get_pricing_order_pending_count(user_id=None):
    """获取批价单待审批数量（使用V2统一审批系统）
    
    Args:
        user_id: 用户ID，默认为当前登录用户
        
    Returns:
        批价单待审批数量
    """
    if user_id is None:
        user_id = current_user.id
    
    try:
        from app.models.user import User
        
        # 获取用户信息
        user = User.query.get(user_id)
        if not user:
            return 0
        
        # 批价单审批数量统计（使用V2统一审批系统）
        pricing_count = 0
        
        # 查询用户作为审批人的批价单实例
        instances = ApprovalInstance.query.filter(
            ApprovalInstance.object_type == 'pricing_order',
            ApprovalInstance.status == ApprovalStatus.PENDING
        ).all()
        
        for instance in instances:
            # 检查用户是否为当前步骤的审批人（支持分支步骤）
            if can_user_approve(instance.id, user_id):
                # 验证业务对象是否存在
                from app.models.pricing_order import PricingOrder
                pricing_order = PricingOrder.query.get(instance.object_id)
                if pricing_order and pricing_order.status == 'pending':
                    pricing_count += 1
        
        return pricing_count
        
    except Exception as e:
        current_app.logger.error(f"获取批价单待审批数量失败: {str(e)}")
        return 0


def get_order_pending_count(user_id=None):
    """获取订单待审批数量
    
    Args:
        user_id: 用户ID，默认为当前登录用户
        
    Returns:
        订单待审批数量
    """
    if user_id is None:
        user_id = current_user.id
    
    try:
        from app.models.user import User
        
        # 获取用户信息
        user = User.query.get(user_id)
        if not user:
            return 0
        
        # 订单审批数量统计（使用通用审批系统）
        order_count = 0
        
        # 查询用户作为审批人的订单实例
        instances = ApprovalInstance.query.filter(
            ApprovalInstance.object_type == 'purchase_order',
            ApprovalInstance.status == ApprovalStatus.PENDING
        ).all()
        
        for instance in instances:
            # 检查用户是否为当前步骤的审批人
            if can_user_approve(user_id, instance.id):
                # 验证业务对象是否存在
                from app.models.inventory import PurchaseOrder
                order = PurchaseOrder.query.get(instance.object_id)
                if order and order.status == 'pending':
                    order_count += 1
        
        # 注意：待审批计数只包含分配给用户本人的审批，不包含部门权限扩展
        # 部门内审批查看功能由单独的get_user_department_approvals函数提供
        
        return order_count
        
    except Exception as e:
        current_app.logger.error(f"获取订单待审批数量失败: {str(e)}")
        return 0


def get_expense_pending_count(user_id=None):
    """获取报销单待审批数量
    
    Args:
        user_id: 用户ID，默认为当前登录用户
        
    Returns:
        int: 待审批的报销单数量
    """
    if user_id is None:
        from flask_login import current_user
        user_id = current_user.id
    
    try:
        from app.models.user import User
        from app.models.approval import ApprovalInstance, ApprovalStatus
        
        user = User.query.get(user_id)
        if not user:
            return 0
        
        expense_count = 0
        
        # 查询用户作为审批人的报销单实例
        instances = ApprovalInstance.query.filter(
            ApprovalInstance.object_type == 'expense',
            ApprovalInstance.status == ApprovalStatus.PENDING
        ).all()
        
        for instance in instances:
            # 检查用户是否为当前步骤的审批人
            if can_user_approve(instance.id, user_id):
                # 验证业务对象是否存在
                from app.models.expense import Expense
                expense = Expense.query.get(instance.object_id)
                if expense and expense.status == 'pending':
                    expense_count += 1
        
        return expense_count
        
    except Exception as e:
        current_app.logger.error(f"获取报销单待审批数量失败: {str(e)}")
        return 0


def get_user_expense_approvals(user_id, status=None, page=1, per_page=20):
    """获取用户权限范围内的报销单审批记录

    使用 get_viewable_data 函数获取用户有权查看的报销单，
    权限规则由 access_control.py 中的报销单特殊处理逻辑控制。

    Args:
        user_id: 用户ID
        status: 状态筛选
        page: 页码
        per_page: 每页数量

    Returns:
        分页对象，包含ExpenseApprovalWrapper对象列表
    """
    from app.models.expense import Expense
    from app.models.user import User
    from app.utils.access_control import get_viewable_data

    # 获取用户信息
    target_user = User.query.get(user_id)
    if not target_user:
        try:
            from flask_sqlalchemy import Pagination
        except ImportError:
            from flask_sqlalchemy.pagination import Pagination
        return Pagination(None, page=page, per_page=per_page, total=0, items=[])

    # 使用通用权限过滤函数获取用户有权查看的报销单
    query = get_viewable_data(Expense, target_user)

    # 状态筛选
    if status:
        if isinstance(status, str):
            query = query.filter(Expense.status == status.lower())
        elif hasattr(status, 'name'):
            # 处理枚举类型
            status_map = {
                'PENDING': 'pending',
                'APPROVED': 'approved',
                'REJECTED': 'rejected',
                'DRAFT': 'draft'
            }
            if status.name in status_map:
                query = query.filter(Expense.status == status_map[status.name])

    # 按创建时间倒序排列
    query = query.order_by(Expense.created_at.desc())

    # 分页
    try:
        expenses = query.paginate(page=page, per_page=per_page, error_out=False)
    except Exception as e:
        current_app.logger.error(f"报销单审批分页查询失败: {str(e)}")
        try:
            from flask_sqlalchemy import Pagination
        except ImportError:
            from flask_sqlalchemy.pagination import Pagination
        expenses = Pagination(query=query, page=page, per_page=per_page, total=0, items=[])

    # 包装为审批实例格式
    wrapped_items = []
    for expense in expenses.items:
        wrapped_items.append(ExpenseApprovalWrapper(expense))

    # 创建新的分页对象
    try:
        from flask_sqlalchemy import Pagination
    except ImportError:
        class Pagination:
            def __init__(self, query, page, per_page, total, items):
                self.query = query
                self.page = page
                self.per_page = per_page
                self.total = total
                self.items = items
                self.pages = (total + per_page - 1) // per_page if per_page > 0 else 1
                self.has_prev = page > 1
                self.has_next = page < self.pages
                self.prev_num = page - 1 if self.has_prev else None
                self.next_num = page + 1 if self.has_next else None

    wrapped_pagination = Pagination(
        query=query,
        page=page,
        per_page=per_page,
        total=expenses.total,
        items=wrapped_items
    )

    return wrapped_pagination


def get_tab_counts_for_auto_switch(user_id=None):
    """获取各个页签的审批数量，用于自动切换到有审批提醒的页签

    Args:
        user_id: 用户ID，默认为当前登录用户

    Returns:
        dict: 各页签的审批数量 {'pending': 数量, 'pricing_order': 数量, 'order': 数量, 'created': 数量}
    """
    if user_id is None:
        user_id = current_user.id
    
    try:
        return {
            'pending': get_pending_approval_count(user_id),
            'pricing_order': get_pricing_order_pending_count(user_id),
            'order': get_order_pending_count(user_id),
            'created': get_pending_created_count(user_id)
        }
    except Exception as e:
        current_app.logger.error(f"获取页签计数失败: {str(e)}")
        return {
            'pending': 0,
            'pricing_order': 0,
            'order': 0,
            'created': 0
        }


def recall_approval_process(object_type, object_id, user_id=None):
    """召回审批流程
    
    Args:
        object_type: 业务对象类型 ('expense', 'project', 'quotation', 'customer')
        object_id: 业务对象ID
        user_id: 召回用户ID，默认为当前登录用户
        
    Returns:
        tuple: (success, message)
    """
    if user_id is None:
        user_id = current_user.id
    
    try:
        # 查找相关的审批实例
        instance = ApprovalInstance.query.filter(
            ApprovalInstance.object_type == object_type,
            ApprovalInstance.object_id == object_id,
            ApprovalInstance.status == ApprovalStatus.PENDING
        ).first()
        
        if not instance:
            return False, "未找到待审批的流程实例"
        
        # 检查权限：创建者或管理员可以召回
        from app.models.user import User
        user = User.query.get(user_id)
        if not user:
            return False, "用户不存在"
        
        if instance.created_by != user_id and user.role != 'admin':
            return False, "只有审批流程的创建者或管理员才能召回"
        
        # 更新审批实例状态
        instance.status = ApprovalStatus.RECALLED
        instance.ended_at = datetime.now()
        
        # 解锁业务对象并更新状态（在同一事务中）
        if object_type == 'expense':
            from app.models.expense import Expense
            expense = Expense.query.get(object_id)
            if expense:
                expense.status = 'draft'
                expense.is_locked = False
                current_app.logger.info(f"报销单已解锁并状态重置: {object_id}")
        elif object_type == 'project':
            update_business_object_status('project', object_id, 'draft')
            unlock_project(object_id, user_id)
        elif object_type == 'quotation':
            update_business_object_status('quotation', object_id, 'draft')
            from app.helpers.quotation_helpers import unlock_quotation
            unlock_quotation(object_id, user_id)
        elif object_type == 'customer':
            update_business_object_status('customer', object_id, 'draft')
            from app.helpers.customer_helpers import unlock_customer
            unlock_customer(object_id, user_id)
        
        db.session.commit()

        # 🔥 召回审批后清除待审批数量缓存
        clear_approval_cache_after_operation("召回审批", user_id, object_type, object_id)

        current_app.logger.info(f"用户 {user_id} 召回了 {object_type}#{object_id} 的审批流程")
        return True, "审批流程已成功召回"
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"召回审批流程失败: {str(e)}"
        current_app.logger.error(error_msg)
        return False, error_msg


def get_current_approval_step_editable_fields(object_type, object_id, user_id):
    """
    获取当前用户在当前审核阶段可编辑的字段列表
    
    Args:
        object_type: 业务对象类型 (如 'expense')
        object_id: 业务对象ID
        user_id: 当前用户ID
    
    Returns:
        dict: {
            'can_edit': bool,           # 是否可以编辑
            'editable_fields': list,    # 可编辑的字段列表
            'step_name': str,           # 当前审核步骤名称
            'instance_id': int          # 审核实例ID
        }
    """
    try:
        # 查找当前正在进行的审批实例
        instance = ApprovalInstance.query.filter_by(
            object_type=object_type,
            object_id=object_id,
            status=ApprovalStatus.PENDING
        ).first()
        
        if not instance:
            return {
                'can_edit': False,
                'editable_fields': [],
                'step_name': '',
                'instance_id': None
            }
        
        # 获取当前步骤信息
        current_step_info = instance.get_current_step_info()
        if not current_step_info:
            return {
                'can_edit': False,
                'editable_fields': [],
                'step_name': '',
                'instance_id': instance.id
            }
        
        # 判断当前用户是否为当前步骤的审批人
        if isinstance(current_step_info, dict):
            # 快照数据
            approver_user_id = current_step_info.get('approver_user_id')
            step_name = current_step_info.get('step_name', '')
            editable_fields = current_step_info.get('editable_fields', [])
        else:
            # 模型对象
            approver_user_id = current_step_info.approver_user_id
            step_name = current_step_info.step_name
            editable_fields = current_step_info.editable_fields or []
        
        # 检查当前用户是否为审批人且有可编辑字段
        can_edit = (approver_user_id == user_id and len(editable_fields) > 0)
        
        return {
            'can_edit': can_edit,
            'editable_fields': editable_fields,
            'step_name': step_name,
            'instance_id': instance.id
        }
        
    except Exception as e:
        current_app.logger.error(f"获取审核阶段可编辑字段失败: {str(e)}")
        return {
            'can_edit': False,
            'editable_fields': [],
            'step_name': '',
            'instance_id': None
        }


def update_approval_step_fields(object_type, object_id, field_updates, user_id):
    """
    在审核阶段更新指定字段
    
    Args:
        object_type: 业务对象类型
        object_id: 业务对象ID  
        field_updates: 字段更新字典 {'field_name': 'new_value'}
        user_id: 当前用户ID
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        # 检查用户权限和可编辑字段
        edit_info = get_current_approval_step_editable_fields(object_type, object_id, user_id)
        
        if not edit_info['can_edit']:
            return False, "当前用户无权在此审核阶段编辑字段"
        
        # 验证更新的字段是否在允许编辑的字段列表中
        editable_fields = edit_info['editable_fields']
        for field_name in field_updates.keys():
            if field_name not in editable_fields:
                return False, f"字段 '{field_name}' 不在当前审核阶段的可编辑字段列表中"
        
        # 根据对象类型更新相应的业务对象
        if object_type == 'expense':
            return _update_expense_fields(object_id, field_updates)
        else:
            return False, f"不支持的对象类型: {object_type}"
            
    except Exception as e:
        error_msg = f"更新审核阶段字段失败: {str(e)}"
        current_app.logger.error(error_msg)
        return False, error_msg


def _update_expense_fields(expense_id, field_updates):
    """更新报销单字段"""
    try:
        from app.models.expense import Expense, ExpenseDetail
        
        expense = Expense.query.get(expense_id)
        if not expense:
            return False, "报销单不存在"
        
        # 更新报销单主表字段
        for field_name, field_value in field_updates.items():
            if field_name == 'exchange_rate':
                # 特殊处理汇率字段 - 需要更新报销明细
                try:
                    exchange_rate = float(field_value)
                    if exchange_rate <= 0:
                        return False, "汇率必须大于0"
                    
                    # 更新所有明细的汇率
                    for detail in expense.details:
                        old_rate = detail.exchange_rate or 1.0
                        detail.exchange_rate = exchange_rate
                        
                        # 重新计算明细金额
                        if detail.invoice_amount and detail.invoice_amount > 0:
                            detail.amount = int(detail.invoice_amount * exchange_rate * 100)  # 转换为分
                        
                        current_app.logger.info(f"更新明细 {detail.id} 汇率: {old_rate} -> {exchange_rate}")
                    
                    # 重新计算报销单总金额
                    expense.calculate_total_amount()
                    
                except (ValueError, TypeError):
                    return False, "汇率格式不正确"
            else:
                # 其他字段的直接更新
                if hasattr(expense, field_name):
                    setattr(expense, field_name, field_value)
        
        db.session.commit()
        current_app.logger.info(f"审核阶段字段更新成功: 报销单 {expense_id}, 字段: {list(field_updates.keys())}")
        return True, "字段更新成功"
        
    except Exception as e:
        db.session.rollback()
        error_msg = f"更新报销单字段失败: {str(e)}"
        current_app.logger.error(error_msg)
        return False, error_msg


# =============================================================================
# 通用审批权限和字段编辑服务类
# =============================================================================

class UniversalApprovalPermissionService:
    """
    通用审批权限服务类
    为不同业务模块提供统一的审批权限检查功能
    """
    
    def __init__(self, object_type, model_class=None):
        """
        初始化权限服务
        
        Args:
            object_type: 业务对象类型 (如 'expense', 'order', 'project')
            model_class: 对应的模型类 (可选，用于类型检查)
        """
        self.object_type = object_type
        self.model_class = model_class
    
    def check_approval_edit_permission(self, object_id, user_id):
        """
        检查用户在审批阶段的编辑权限
        
        Args:
            object_id: 业务对象ID
            user_id: 用户ID
        
        Returns:
            dict: 权限信息和可编辑字段
        """
        return get_current_approval_step_editable_fields(
            self.object_type, object_id, user_id
        )
    
    def check_approval_action_permission(self, object_id, user_id, action='approve'):
        """
        检查用户的审批操作权限
        
        Args:
            object_id: 业务对象ID
            user_id: 用户ID
            action: 审批动作 ('approve', 'reject')
        
        Returns:
            dict: {
                'can_action': bool,
                'step_name': str,
                'instance_id': int,
                'message': str
            }
        """
        try:
            # 查找当前正在进行的审批实例
            instance = ApprovalInstance.query.filter_by(
                object_type=self.object_type,
                object_id=object_id,
                status=ApprovalStatus.PENDING
            ).first()
            
            if not instance:
                return {
                    'can_action': False,
                    'step_name': '',
                    'instance_id': None,
                    'message': '没有找到进行中的审批流程'
                }
            
            # 获取当前步骤信息
            current_step_info = instance.get_current_step_info()
            if not current_step_info:
                return {
                    'can_action': False,
                    'step_name': '',
                    'instance_id': instance.id,
                    'message': '无法获取当前审批步骤信息'
                }
            
            # 检查审批人权限
            if isinstance(current_step_info, dict):
                approver_user_id = current_step_info.get('approver_user_id')
                step_name = current_step_info.get('step_name', '')
            else:
                approver_user_id = current_step_info.approver_user_id
                step_name = current_step_info.step_name
            
            can_action = (approver_user_id == user_id)
            message = '有权限进行审批操作' if can_action else '当前用户不是此步骤的审批人'
            
            return {
                'can_action': can_action,
                'step_name': step_name,
                'instance_id': instance.id,
                'message': message
            }
            
        except Exception as e:
            current_app.logger.error(f"检查审批操作权限失败: {str(e)}")
            return {
                'can_action': False,
                'step_name': '',
                'instance_id': None,
                'message': f'权限检查失败: {str(e)}'
            }
    
    def check_submission_permission(self, object_id, user_id):
        """
        检查用户提交审批的权限
        
        Args:
            object_id: 业务对象ID
            user_id: 用户ID
        
        Returns:
            dict: {
                'can_submit': bool,
                'message': str,
                'object_status': str
            }
        """
        try:
            # 检查是否已有正在进行的审批
            existing_instance = ApprovalInstance.query.filter_by(
                object_type=self.object_type,
                object_id=object_id,
                status=ApprovalStatus.PENDING
            ).first()
            
            if existing_instance:
                return {
                    'can_submit': False,
                    'message': '已有审批流程正在进行中',
                    'object_status': 'pending'
                }
            
            # 如果指定了模型类，检查对象的拥有者
            if self.model_class:
                obj = self.model_class.query.get(object_id)
                if obj and hasattr(obj, 'owner_id') and obj.owner_id != user_id:
                    return {
                        'can_submit': False,
                        'message': '只有对象拥有者可以提交审批',
                        'object_status': getattr(obj, 'status', 'unknown')
                    }
            
            return {
                'can_submit': True,
                'message': '可以提交审批',
                'object_status': 'draft'
            }
            
        except Exception as e:
            current_app.logger.error(f"检查提交权限失败: {str(e)}")
            return {
                'can_submit': False,
                'message': f'权限检查失败: {str(e)}',
                'object_status': 'error'
            }


class UniversalFieldEditService:
    """
    通用字段编辑服务类
    为不同业务模块提供统一的审批阶段字段编辑功能
    """
    
    def __init__(self, object_type):
        """
        初始化字段编辑服务
        
        Args:
            object_type: 业务对象类型
        """
        self.object_type = object_type
        self.field_updaters = {}
        self._register_default_updaters()
    
    def _register_default_updaters(self):
        """注册默认的字段更新器"""
        if self.object_type == 'expense':
            self.register_field_updater('exchange_rate', self._update_expense_exchange_rate)
            self.register_field_updater('amount', self._update_expense_amount)
        elif self.object_type == 'order':
            # 订单的字段更新器可以在这里注册
            pass
        elif self.object_type == 'project':
            # 项目的字段更新器可以在这里注册
            pass
    
    def register_field_updater(self, field_name, updater_func):
        """
        注册字段更新器
        
        Args:
            field_name: 字段名称
            updater_func: 更新函数，接收 (object_id, field_value) 参数
        """
        self.field_updaters[field_name] = updater_func
    
    def update_fields(self, object_id, field_updates, user_id):
        """
        更新字段值
        
        Args:
            object_id: 业务对象ID
            field_updates: 字段更新字典
            user_id: 用户ID
        
        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # 检查权限
            edit_info = get_current_approval_step_editable_fields(
                self.object_type, object_id, user_id
            )
            
            if not edit_info['can_edit']:
                return False, "当前用户无权在此审核阶段编辑字段"
            
            # 验证字段权限
            editable_fields = edit_info['editable_fields']
            for field_name in field_updates.keys():
                if field_name not in editable_fields:
                    return False, f"字段 '{field_name}' 不在当前审核阶段的可编辑字段列表中"
            
            # 执行字段更新
            success_count = 0
            error_messages = []
            
            for field_name, field_value in field_updates.items():
                try:
                    if field_name in self.field_updaters:
                        # 使用注册的更新器
                        success, message = self.field_updaters[field_name](object_id, field_value)
                        if success:
                            success_count += 1
                        else:
                            error_messages.append(f"{field_name}: {message}")
                    else:
                        # 使用通用更新逻辑
                        success, message = self._generic_field_update(object_id, field_name, field_value)
                        if success:
                            success_count += 1
                        else:
                            error_messages.append(f"{field_name}: {message}")
                            
                except Exception as e:
                    error_messages.append(f"{field_name}: {str(e)}")
            
            # 返回结果
            if success_count == len(field_updates):
                return True, f"所有字段更新成功 ({success_count}个)"
            elif success_count > 0:
                return False, f"部分字段更新成功 ({success_count}/{len(field_updates)}): {'; '.join(error_messages)}"
            else:
                return False, f"所有字段更新失败: {'; '.join(error_messages)}"
                
        except Exception as e:
            current_app.logger.error(f"字段更新失败: {str(e)}")
            return False, f"字段更新失败: {str(e)}"
    
    def _generic_field_update(self, object_id, field_name, field_value):
        """通用字段更新逻辑"""
        try:
            # 这里可以实现通用的字段更新逻辑
            # 暂时返回成功，具体实现根据业务需要
            current_app.logger.info(f"通用字段更新: {self.object_type} {object_id}, {field_name} = {field_value}")
            return True, "字段更新成功"
        except Exception as e:
            return False, str(e)
    
    def _update_expense_exchange_rate(self, expense_id, exchange_rate):
        """更新报销单汇率

        - exchange_rate 为 dict {str(detail_id): rate} → 明细级粒度,只更新指定行(支持多币种)
        - exchange_rate 为 number/str → 全表批量(向后兼容旧调用方)
        """
        try:
            from app.models.expense import Expense, ExpenseDetail
            from flask import current_app
            current_app.logger.info(
                f"[approval-edit] expense={expense_id} exchange_rate update "
                f"input={exchange_rate!r} type={type(exchange_rate).__name__}"
            )

            details = ExpenseDetail.query.filter_by(expense_id=expense_id).all()
            current_app.logger.info(
                f"[approval-edit] expense={expense_id} loaded {len(details)} details: "
                f"{[(d.id, d.exchange_rate) for d in details]}"
            )
            updated = 0

            if isinstance(exchange_rate, dict):
                # 明细级:逐行匹配
                for d in details:
                    key = str(d.id)
                    if key in exchange_rate:
                        try:
                            new_rate = float(exchange_rate[key])
                        except (TypeError, ValueError):
                            continue
                        old_rate = d.exchange_rate
                        d.exchange_rate = new_rate
                        d.current_amount = round((d.invoice_amount or 0) * new_rate, 2)
                        d.amount = d.current_amount
                        updated += 1
                        current_app.logger.info(
                            f"[approval-edit] detail={d.id} {old_rate} → {new_rate} "
                            f"(amount={d.current_amount})"
                        )
                if updated == 0:
                    return False, f"未匹配到任何明细行(detail_id 不一致)。入参 keys={list(exchange_rate.keys())},DB ids={[d.id for d in details]}"
                msg = f"已更新 {updated} 条明细的汇率"
            else:
                # 全表批量(向后兼容)
                rate_f = float(exchange_rate)
                for d in details:
                    d.exchange_rate = rate_f
                    d.current_amount = round((d.invoice_amount or 0) * rate_f, 2)
                    d.amount = d.current_amount
                    updated += 1
                msg = f"全部 {updated} 条明细汇率统一更新为 {rate_f}"

            db.session.commit()
            current_app.logger.info(f"[approval-edit] commit done · {msg}")
            return True, msg

        except Exception as e:
            db.session.rollback()
            from flask import current_app
            current_app.logger.error(f"[approval-edit] 汇率更新失败: {e}", exc_info=True)
            return False, f"汇率更新失败: {str(e)}"
    
    def _update_expense_amount(self, expense_id, amount):
        """更新报销单金额"""
        try:
            from app.models.expense import Expense
            
            expense = Expense.query.get(expense_id)
            if not expense:
                return False, "报销单不存在"
            
            expense.total_amount = float(amount)
            db.session.commit()
            return True, f"报销金额更新为 {amount}"
            
        except Exception as e:
            db.session.rollback()
            return False, f"金额更新失败: {str(e)}"


# =============================================================================
# 便捷工厂函数
# =============================================================================

def get_approval_permission_service(object_type, model_class=None):
    """
    获取审批权限服务实例
    
    Args:
        object_type: 业务对象类型
        model_class: 模型类（可选）
    
    Returns:
        UniversalApprovalPermissionService: 权限服务实例
    """
    return UniversalApprovalPermissionService(object_type, model_class)


def get_field_edit_service(object_type):
    """
    获取字段编辑服务实例
    
    Args:
        object_type: 业务对象类型
    
    Returns:
        UniversalFieldEditService: 字段编辑服务实例
    """
    return UniversalFieldEditService(object_type)


def check_universal_approval_permission(object_type, object_id, user_id, permission_type='edit'):
    """
    通用审批权限检查函数
    
    Args:
        object_type: 业务对象类型
        object_id: 业务对象ID
        user_id: 用户ID
        permission_type: 权限类型 ('edit', 'approve', 'submit')
    
    Returns:
        dict: 权限检查结果
    """
    service = get_approval_permission_service(object_type)
    
    if permission_type == 'edit':
        return service.check_approval_edit_permission(object_id, user_id)
    elif permission_type == 'approve':
        return service.check_approval_action_permission(object_id, user_id)
    elif permission_type == 'submit':
        return service.check_submission_permission(object_id, user_id)
    else:
        return {
            'can_action': False,
            'message': f'不支持的权限类型: {permission_type}'
        }


def is_current_approver(object_type, object_id, user_id):
    """
    检查用户是否是当前审批步骤的审批人

    Args:
        object_type: 对象类型
        object_id: 对象ID
        user_id: 用户ID

    Returns:
        bool: 是否为当前审批人
    """
    try:
        # 获取审批实例
        approval_instance = get_object_approval_instance(object_type, object_id)
        if not approval_instance or approval_instance.status != ApprovalStatus.PENDING:
            return False

        # 🔥 修复：使用 get_current_step_info() 获取当前步骤
        # current_step 字段可能存储 step_order 或 step_id，需要智能匹配
        current_step_info = approval_instance.get_current_step_info()
        if not current_step_info:
            return False

        # 获取实际审批人
        actual_approver = get_step_actual_approver(current_step_info, approval_instance)
        if not actual_approver:
            return False

        # 检查是否为当前审批人
        # get_step_actual_approver返回User对象，需要获取id
        approver_id = actual_approver.id if hasattr(actual_approver, 'id') else actual_approver.get('approver_id') if isinstance(actual_approver, dict) else None
        return approver_id == user_id

    except Exception as e:
        current_app.logger.error(f"检查审批人权限失败: {str(e)}")
        return False


def get_step_branch_conditions_count(step_id):
    """获取步骤的分支条件数量
    
    Args:
        step_id: 审批步骤ID
        
    Returns:
        int: 分支条件数量
    """
    try:
        count = ApprovalBranchCondition.query.filter_by(step_id=step_id).count()
        current_app.logger.info(f"步骤 {step_id} 的分支条件数量: {count}")
        return count
    except Exception as e:
        current_app.logger.error(f"获取步骤分支条件数量失败: {str(e)}")
        return 0


def get_step_unified_branch_field(step_id):
    """获取步骤的统一分支条件字段
    
    Args:
        step_id: 审批步骤ID
        
    Returns:
        str: 条件字段名称，如果没有条件则返回None
    """
    try:
        # 先从步骤的branch_condition字段获取（主要字段存储位置）
        step = ApprovalStep.query.get(step_id)
        if step and hasattr(step, 'get_branch_field'):
            field_name = step.get_branch_field()
            if field_name:
                current_app.logger.info(f"步骤 {step_id} 的统一条件字段(从步骤获取): {field_name}")
                return field_name
        
        current_app.logger.info(f"步骤 {step_id} 没有分支条件字段配置")
        return None
        
    except Exception as e:
        current_app.logger.error(f"获取步骤统一条件字段失败: {str(e)}")
        return None


def get_step_branch_field_from_step_data(step_id):
    """从步骤的分支条件配置中获取条件字段
    
    Args:
        step_id: 审批步骤ID
        
    Returns:
        str: 条件字段名称，如果没有则返回None
    """
    try:
        # 先尝试从新表获取
        field_from_conditions = get_step_unified_branch_field(step_id)
        if field_from_conditions:
            return field_from_conditions
            
        # 如果新表没有数据，尝试从步骤的branch_condition字段获取（兼容旧数据）
        step = ApprovalStep.query.get(step_id)
        if step and hasattr(step, 'branch_condition') and step.branch_condition:
            try:
                import json
                branch_config = json.loads(step.branch_condition) if isinstance(step.branch_condition, str) else step.branch_condition
                field_name = branch_config.get('field') if isinstance(branch_config, dict) else None
                current_app.logger.info(f"从步骤旧配置获取条件字段: {field_name}")
                return field_name
            except (json.JSONDecodeError, AttributeError) as e:
                current_app.logger.warning(f"解析步骤旧配置失败: {str(e)}")
        
        return None
        
    except Exception as e:
        current_app.logger.error(f"获取步骤条件字段失败: {str(e)}")
        return None


def should_lock_branch_field(step_id, condition_index):
    """判断分支条件字段是否应该锁定
    
    Args:
        step_id: 审批步骤ID
        condition_index: 条件索引（0-based）
        
    Returns:
        bool: True表示应该锁定，False表示可编辑
    """
    try:
        total_conditions = get_step_branch_conditions_count(step_id)
        
        # 第一个条件且有其他条件 → 锁定
        if condition_index == 0 and total_conditions > 1:
            current_app.logger.info(f"锁定字段：第一个条件且存在多个条件 (总数: {total_conditions})")
            return True
        
        # 非第一个条件 → 总是锁定
        if condition_index > 0:
            current_app.logger.info(f"锁定字段：非第一个条件 (索引: {condition_index})")
            return True
        
        # 第一个条件且无其他条件 → 可编辑
        current_app.logger.info(f"允许编辑字段：第一个条件且无其他条件 (总数: {total_conditions})")
        return False
        
    except Exception as e:
        current_app.logger.error(f"判断字段锁定状态失败: {str(e)}")
        return False  # 出错时默认可编辑


def _execute_branch_decision_action(instance, current_step, current_step_obj, record, user_id, pricing_order_data=None):
    """执行分支决策步骤的匹配动作
    
    Args:
        instance: 审批实例对象
        current_step: 当前步骤信息（字典格式）
        current_step_obj: 当前步骤对象（ApprovalStep）
        record: 审批记录对象
        user_id: 操作人ID
        pricing_order_data: 批价单数据，用于保存操作
    """
    try:
        
        # 获取分支条件
        branch_condition = current_step.get('branch_condition')
        if not branch_condition:
            return
        
        
        # 确定匹配的动作
        matched_action = _get_matched_branch_action(instance, branch_condition)
        if not matched_action:
            return
        
        
        # 创建临时的ApprovalStep对象来执行动作
        temp_step = type('TempStep', (), {})()
        temp_step.action_type = matched_action
        temp_step.id = current_step_obj.id if current_step_obj else 'temp'
        
        # 创建目标对象
        target_object = None
        if instance.object_type == 'project':
            from app.models.project import Project
            target_object = Project.query.get(instance.object_id)
        elif instance.object_type == 'expense':
            from app.models.expense import Expense
            target_object = Expense.query.get(instance.object_id)
        elif instance.object_type == 'pricing_order':
            from app.models.pricing_order import PricingOrder
            target_object = PricingOrder.query.get(instance.object_id)
        else:
            return
        
        
        if target_object:
            
            # 创建真正的ApprovalStep对象来执行动作
            from app.models.approval import ApprovalStep, ApprovalActionType
            
            # 创建临时的审批步骤对象
            temp_approval_step = ApprovalStep()
            temp_approval_step.action_type = matched_action  # 例如：'pricing_settlement_approval'
            temp_approval_step.id = current_step_obj.id if current_step_obj else 'branch_temp'
            
            
            try:
                # 调用ApprovalStep的execute_action方法，传递审批记录和目标对象以及批价单数据
                if instance.object_type == 'pricing_order' and pricing_order_data:
                    result = temp_approval_step.execute_action(record, target_object, pricing_order_data)
                else:
                    result = temp_approval_step.execute_action(record, target_object)
            except Exception as action_error:
                current_app.logger.error(f"🔍 [BRANCH_ACTION_EXEC] ❌ execute_action 执行异常: {str(action_error)}")
                import traceback
                current_app.logger.error(traceback.format_exc())
        else:
            pass

    except Exception as e:
        current_app.logger.error(f"🔍 [BRANCH_ACTION_EXEC] ❌ 执行分支动作时发生异常: {str(e)}")
        import traceback
        traceback.print_exc()


def _get_matched_branch_action(instance, branch_condition):
    """获取匹配的分支动作
    
    Args:
        instance: 审批实例对象
        branch_condition: 分支条件配置
        
    Returns:
        str: 匹配的动作类型，如 'pricing_settlement_approval'
    """
    try:
        import json
        if isinstance(branch_condition, str):
            branch_condition = json.loads(branch_condition)
        
        field_name = branch_condition.get('field')
        conditions = branch_condition.get('conditions', [])
        
        
        # 获取字段值
        field_value = _get_field_value_for_branch(instance, field_name)
        
        # 匹配条件
        for i, condition in enumerate(conditions):
            condition_value = condition.get('value')
            operator = condition.get('operator', 'equals')
            action = condition.get('action')
            
            
            is_match = False
            if operator == 'equals':
                is_match = str(field_value) == str(condition_value)
            elif operator == 'in':
                # 处理逗号分隔的值列表
                values = [v.strip() for v in str(condition_value).split(',')]
                is_match = str(field_value) in values
            elif operator == 'contains':
                is_match = str(condition_value) in str(field_value)
            
            
            if is_match and action:
                return action
        
        return None
        
    except Exception as e:
        current_app.logger.error(f"🔍 [BRANCH_MATCH] ❌ 匹配分支动作时发生异常: {str(e)}")
        return None


def _get_field_value_for_branch(instance, field_name):
    """获取用于分支条件匹配的字段值
    
    Args:
        instance: 审批实例对象
        field_name: 字段名称
        
    Returns:
        字段值
    """
    try:
        if instance.object_type == 'pricing_order':
            # 批价单的特殊处理：从关联的报价单获取项目类型
            if field_name == 'project_type':
                from app.models.pricing_order import PricingOrder
                pricing_order = PricingOrder.query.get(instance.object_id)
                if pricing_order and pricing_order.quotation and pricing_order.quotation.project:
                    return pricing_order.quotation.project.project_type
        elif instance.object_type == 'project':
            from app.models.project import Project
            project = Project.query.get(instance.object_id)
            if project and hasattr(project, field_name):
                return getattr(project, field_name)
        elif instance.object_type == 'expense':
            from app.models.expense import Expense
            expense = Expense.query.get(instance.object_id)
            if expense and hasattr(expense, field_name):
                return getattr(expense, field_name)
        
        return None
        
    except Exception as e:
        current_app.logger.error(f"🔍 [FIELD_VALUE] ❌ 获取字段值时发生异常: {str(e)}")
        return None
