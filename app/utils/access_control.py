"""
确保 can_edit_company_info 可用于 Jinja2 模板
"""

try:
    from flask import current_app as app
except ImportError:
    app = None

# --- 权限函数重构 ---
"""
数据访问控制工具模块
用于根据用户角色和权限过滤数据查询
"""
import logging
from flask_login import current_user
from app import db
from app.models.user import Affiliation, User
from app.models.project import Project
from app.models.customer import Company, Contact
from app.models.quotation import Quotation
from app.models.action import Action
from app.models.expense import Expense
from sqlalchemy import or_, func, desc, text, cast
from sqlalchemy.dialects.postgresql import JSONB

logger = logging.getLogger(__name__)

# ============================================================================
# 权限过滤辅助函数 - 用于消除 get_viewable_data() 中的代码重复
# ============================================================================

def get_company_user_ids(user, include_affiliations=True):
    """
    获取公司级可查看的用户ID列表

    参数:
        user: 用户对象
        include_affiliations: 是否包含归属关系授权的用户（默认True）

    返回:
        list: 用户ID列表（已去重）
    """
    user_ids = [u.id for u in User.query.filter_by(company_name=user.company_name).all()]

    if include_affiliations:
        affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
        user_ids.extend([aff.owner_id for aff in affiliations])

    return list(set(user_ids))

def get_department_user_ids(user, include_affiliations=True):
    """
    获取部门级可查看的用户ID列表

    参数:
        user: 用户对象
        include_affiliations: 是否包含归属关系授权的用户（默认True）

    返回:
        list: 用户ID列表（已去重）
    """
    user_ids = [u.id for u in User.query.filter(
        User.department == user.department,
        User.company_name == user.company_name
    ).all()]

    if include_affiliations:
        affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
        user_ids.extend([aff.owner_id for aff in affiliations])

    return list(set(user_ids))

def get_personal_viewable_user_ids(user):
    """
    获取个人级可查看的用户ID列表（含归属关系和部门负责人权限）

    参数:
        user: 用户对象

    返回:
        list: 用户ID列表（已去重）
    """
    viewable_user_ids = [user.id]

    # 归属关系授权
    affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
    viewable_user_ids.extend([aff.owner_id for aff in affiliations])

    # 部门负责人权限 - 使用新的辅助函数，支持多部门管理
    managed_depts = get_managed_departments(user)
    for dept_name, company_name in managed_depts:
        dept_users = User.query.filter_by(
            department=dept_name,
            company_name=company_name
        ).all()
        viewable_user_ids.extend([u.id for u in dept_users])

    return list(set(viewable_user_ids))


def _pinyin_sort_key(name):
    """姓名排序键:中文按拼音,英文/数字原样;无 pypinyin 时退回小写原串。"""
    name = name or ''
    try:
        from pypinyin import lazy_pinyin
        return ''.join(lazy_pinyin(name)).lower()
    except Exception:
        return name.lower()


def build_owner_filter_options(owner_ids):
    """负责人筛选下拉选项:在职在前、离职在后(灰色 muted),组内按拼音首字母排序,
    离职 label 加「（离职）」。供 AT 列表(项目/客户/报价)筛选面板复用。"""
    if not owner_ids:
        return []
    users = User.query.filter(User.id.in_(owner_ids)).all()
    users.sort(key=lambda u: (not u.is_active, _pinyin_sort_key(u.real_name or u.username)))
    return [{'value': u.id,
             'label': (u.real_name or u.username or str(u.id)) + ('（离职）' if not u.is_active else ''),
             'muted': not u.is_active}
            for u in users]


def get_managed_departments(user):
    """
    获取用户管理的部门列表（兼容新旧两种方式）

    新方式：通过Department.manager_id关联
    旧方式：通过User.is_department_manager标记（向后兼容）

    参数:
        user: 用户对象

    返回:
        list: [(department_name, company_name), ...] 部门名称和公司名称的元组列表
    """
    managed_depts = []

    # 新方式：从Department表获取管理的部门
    from app.models.expense import Department
    departments = Department.query.filter_by(manager_id=user.id).all()
    for dept in departments:
        managed_depts.append((dept.name, dept.company_name))

    # 旧方式：向后兼容is_department_manager标记
    if getattr(user, 'is_department_manager', False) and user.department and user.company_name:
        # 检查是否已经通过新方式添加（避免重复）
        if (user.department, user.company_name) not in managed_depts:
            managed_depts.append((user.department, user.company_name))

    return managed_depts


def is_manager_of_department(user, department_name, company_name):
    """
    检查用户是否是指定部门的负责人（兼容新旧两种方式）

    参数:
        user: 用户对象
        department_name: 部门名称
        company_name: 公司名称

    返回:
        bool: 是否是该部门的负责人
    """
    managed_depts = get_managed_departments(user)
    return (department_name, company_name) in managed_depts

def _check_permission_level_scope(user, target_owner_id, permission_level):
    """
    检查用户的权限级别是否覆盖目标数据拥有者

    用于统一检查change_owner等权限操作中的权限级别范围。

    参数:
        user: 当前用户
        target_owner_id: 目标数据拥有者ID
        permission_level: 权限级别 (system/company/department/personal)

    返回:
        bool: 是否在权限范围内
    """
    if permission_level == 'system':
        return True

    if permission_level == 'personal':
        # personal级别：只能操作自己的数据
        return target_owner_id == user.id

    from app.models.user import User
    owner = User.query.get(target_owner_id)
    if not owner:
        return False

    if permission_level == 'company' and user.company_name:
        return owner.company_name == user.company_name

    elif permission_level == 'department' and user.department and user.company_name:
        return (owner.department == user.department and
               owner.company_name == user.company_name)

    return False

def _apply_join_filter(query, model_class, join_config, allowed_values, filter_key):
    """
    处理需要 JOIN 其他表的筛选

    参数:
        query: 查询对象
        model_class: 主模型类
        join_config: JOIN 配置，包含 model, join_on, filter_attr
        allowed_values: 允许的值列表
        filter_key: 过滤字段名（用于日志）

    返回:
        应用了 JOIN 过滤后的 Query 对象
    """
    model_name = join_config.get('model')
    join_on = join_config.get('join_on')
    filter_attr = join_config.get('filter_attr')

    if not all([model_name, join_on, filter_attr]):
        logger.warning(f"join_config 配置不完整: {join_config}")
        return query

    # 动态获取要 JOIN 的模型类
    join_model = None
    if model_name == 'Project':
        join_model = Project
    elif model_name == 'Company':
        join_model = Company
    elif model_name == 'Contact':
        join_model = Contact
    elif model_name == 'Quotation':
        join_model = Quotation
    # 可按需扩展更多模型

    if not join_model:
        logger.warning(f"未知的 JOIN 模型: {model_name}")
        return query

    # 检查主模型是否有 join_on 字段
    if not hasattr(model_class, join_on):
        logger.warning(f"模型 {model_class.__name__} 没有属性 {join_on}")
        return query

    # 检查 JOIN 模型是否有 filter_attr 字段
    if not hasattr(join_model, filter_attr):
        logger.warning(f"模型 {join_model.__name__} 没有属性 {filter_attr}")
        return query

    # 执行 JOIN 和过滤
    query = query.join(
        join_model,
        getattr(model_class, join_on) == join_model.id
    ).filter(
        or_(
            getattr(join_model, filter_attr).in_(allowed_values),
            getattr(join_model, filter_attr).is_(None)
        )
    )
    logger.debug(f"应用 JOIN 过滤 ({model_name}.{filter_attr}): {allowed_values}")

    return query


def apply_content_filters(query, model_class, module_name, user):
    """
    应用内容过滤器（content_filters）到查询

    参数:
        query: 已经应用了权限级别过滤的Query对象
        model_class: 数据模型类
        module_name: 模块名称
        user: 用户对象

    返回:
        应用了内容过滤后的Query对象

    规则:
        - 如果模块定义了内容筛选选项但用户未配置 → 返回空查询（没权限）
        - 如果配置了 content_filters 但某字段为空列表 → 该字段返回空查询（没权限）
    """
    try:
        # 获取模块的内容筛选配置（定义了哪些字段需要筛选）
        from app.views.config_management import get_content_filter_options
        module_filter_options = get_content_filter_options().get(module_name, {})

        # 获取用户的权限数据（包含content_filters）- 使用缓存
        role_permission, user_permission = user._get_cached_permissions(module_name)

        # 优先使用个人权限的 content_filters
        if user_permission and user_permission.content_filters:
            content_filters = user_permission.content_filters
        elif role_permission and role_permission.content_filters:
            content_filters = role_permission.content_filters
            logger.debug(f"使用角色权限的 content_filters: {content_filters}")
        else:
            # 没有任何 content_filters 配置 = 不限(不过滤,全开)
            # (原"模块可筛选但未配置 → 全关"与"不限=全开"直觉冲突,已废弃;
            #  全开仍受 permission_level 数据范围约束)
            return query

        logger.debug(f"应用 {module_name} 模块的内容过滤: {content_filters}")

        # 缺某筛选字段 = 该维度「不限」(不过滤),不再因缺字段而全关
        # (原"必须配齐每个字段否则全关"与"不限=全开"直觉冲突,已废弃)

        # 动态应用过滤规则（AND 逻辑：仅对"有具体值"的字段过滤;空/缺 = 不限）
        for filter_key, allowed_values in content_filters.items():
            if not isinstance(allowed_values, list):
                continue

            # 仅对「当前模块已定义的可配置维度」生效;存储里的历史遗留键(如 customer 的
            # status,早期是维度后从 UI 配置移除)一律忽略,不再误过滤 —— 否则即便是 system
            # 级用户也会被一个 UI 设不了的孤儿键悄悄裁剪数据(如 ceo 看不全经销商/分销商)。
            if filter_key not in module_filter_options:
                logger.debug(f"{module_name}.{filter_key} 非当前可配置维度(历史遗留键) → 跳过")
                continue

            # 空列表 = 该维度「不限」(不过滤,全开),不再全关
            if not allowed_values:
                logger.debug(f"{module_name}.{filter_key} 为空列表 → 视为不限,跳过该维度过滤")
                continue

            # 获取该字段的配置
            filter_config = module_filter_options.get(filter_key, {})

            # 检查是否需要 JOIN
            join_config = filter_config.get('join_config')
            if join_config:
                query = _apply_join_filter(query, model_class, join_config, allowed_values, filter_key)
            else:
                # 普通字段过滤
                # 优先使用配置中的 model_attr，否则使用 filter_key
                model_attr = filter_config.get('model_attr', filter_key)
                if hasattr(model_class, model_attr):
                    attr = getattr(model_class, model_attr)
                    query = query.filter(
                        or_(
                            attr.in_(allowed_values),
                            attr.is_(None),
                            attr == ''  # 同时允许空字符串（数据库中可能存在空字符串而非NULL）
                        )
                    )
                    logger.debug(f"应用 {module_name}.{filter_key} 过滤: {allowed_values} (含NULL和空字符串)")
                else:
                    logger.warning(f"模型 {model_class.__name__} 没有属性 {model_attr}，跳过过滤")

        return query

    except Exception as e:
        logger.error(f"应用内容过滤时出错: {e}")
        return query  # 出错时返回原查询，不影响基本功能

# ============================================================================
# 权限检查函数
# ============================================================================

def has_approval_permission(user, model_obj):
    """
    检查用户是否对指定对象有审批权限
    
    参数:
        user: 用户对象
        model_obj: 数据对象（如报销单）
        
    返回:
        bool: 是否有审批权限
    """
    try:
        from app.models.approval import ApprovalInstance, ApprovalRecord
        from app.helpers.approval_helpers import get_step_actual_approver
        
        # 获取对象类型
        object_type = model_obj.__class__.__name__.lower()
        if object_type == 'expense':
            object_type = 'expense'
        
        # 查找该对象的进行中的审批实例
        from app.models.approval import ApprovalStatus
        approval_instances = ApprovalInstance.query.filter_by(
            object_id=model_obj.id,
            object_type=object_type,
            status=ApprovalStatus.PENDING
        ).all()
        
        for instance in approval_instances:
            # 获取当前步骤信息
            current_step_info = instance.get_current_step_info()
            if not current_step_info:
                continue
            
            # 检查当前用户是否是当前步骤的审批者
            try:
                approver = get_step_actual_approver(current_step_info, instance)
                
                if approver and approver.id == user.id:
                    return True
            except Exception as e:
                logger.debug(f"检查审批权限时出错: {str(e)}")
                continue
        
        # 检查用户是否曾经审批过该对象（历史审批权限）
        approval_records = ApprovalRecord.query.join(ApprovalInstance).filter(
            ApprovalInstance.object_id == model_obj.id,
            ApprovalInstance.object_type == object_type,
            ApprovalRecord.approver_id == user.id
        ).first()
        
        if approval_records:
            return True
            
        return False
        
    except Exception as e:
        logger.error(f"检查审批权限时发生错误: {str(e)}")
        return False

def get_projects_through_customer_sharing_condition(user, model_class):
    """
    DEPRECATED: 此函数已废弃，客户不再自动共享项目
    获取通过客户共享获得的项目访问权限的查询条件
    
    参数:
        user: 用户对象
        model_class: Project模型类
    
    返回:
        None - 已禁用客户自动项目共享功能
    """
    # 客户共享项目的功能已被移除，改为使用项目直接共享机制
    logger.info("客户自动项目共享功能已被禁用，请使用项目直接共享功能")
    return None

def _get_worklog_shared_ids(user_id, field='project_id'):
    """获取通过行程共享获得的关联ID（子查询）

    Args:
        user_id: 当前用户ID
        field: 'project_id' 或 'customer_id'
    """
    from app.models.worklog import WorkItem

    target_field = getattr(WorkItem, field)
    # 仅"被共享给该用户"的行程才让关联客户/项目在列表可见(与 can_view_company/project 一致)。
    # 不再包含 owner_id==user_id —— 否则"自己给某客户/项目记过行程"会让其误显示在列表,
    # 但详情(只认共享)拒绝,造成"列表看得到、点不进"(转移走后尤为明显)。
    return db.session.query(target_field).filter(
        target_field.isnot(None),
        WorkItem.is_deleted == False,
        cast(WorkItem.shared_with_users, JSONB).op('@>')(text(f"'[{user_id}]'::jsonb"))
    ).distinct()

def _get_task_linked_ids(user_id, field='project_id'):
    """获取通过任务指派获得的关联ID（子查询）

    Args:
        user_id: 当前用户ID
        field: 'project_id' 或 'quotation_id'
    """
    from app.models.task import Task as GeneralTask

    target_field = getattr(GeneralTask, field)
    return db.session.query(target_field).filter(
        target_field.isnot(None),
        GeneralTask.is_deleted == False,
        GeneralTask.status.in_(['pending', 'in_progress', 'completed']),
        db.or_(GeneralTask.assignee_id == user_id, GeneralTask.creator_id == user_id)
    ).distinct()


def additive_grant_conditions(model_class, user):
    """「附加授权」OR 条件 —— 与权限级别无关,任何级别(system 除外,本就全见)都应叠加:
       共享(shared_with_users) + 行程共享 + 任务关联 + 厂商销售负责人。
       按模型自适应字段;返回 list[SQLAlchemy 条件](可能为空)。

    解决:公司/部门级用户收不到跨公司/跨部门「显式共享」给他的数据(原共享仅 personal 级生效)。
    """
    conds = []
    name = model_class.__name__
    # 1) 通用共享 shared_with_users
    if hasattr(model_class, 'shared_with_users'):
        try:
            from app.utils.sharing import SharingService
            c = SharingService.get_sharing_query_condition(model_class, user.id)
            if c is not None:
                conds.append(c)
        except Exception as e:
            logger.warning(f"附加授权-共享条件构建失败 ({name}): {e}")
    # 2) 按模型的其它附加授权
    if name == 'Project':
        conds.append(model_class.vendor_sales_manager_id == user.id)
        conds.append(model_class.id.in_(_get_worklog_shared_ids(user.id, 'project_id')))
        conds.append(model_class.id.in_(_get_task_linked_ids(user.id, 'project_id')))
    elif name == 'Quotation':
        # 报价单的附加授权由项目派生:厂商负责人 / 行程共享 的项目下报价 + 任务关联报价
        proj_ids = set(p[0] for p in Project.query.filter(
            Project.vendor_sales_manager_id == user.id).with_entities(Project.id).all())
        proj_ids.update(r[0] for r in _get_worklog_shared_ids(user.id, 'project_id').all())
        if proj_ids:
            conds.append(model_class.project_id.in_(proj_ids))
        conds.append(model_class.id.in_(_get_task_linked_ids(user.id, 'quotation_id')))
    elif name == 'PricingOrder':
        # 批价单(用 created_by):厂商负责人负责的项目下批价 + 归属上级创建的批价。
        # (批价自身的 shared_with_users 已由上面通用段处理)
        proj_ids = set(p[0] for p in Project.query.filter(
            Project.vendor_sales_manager_id == user.id).with_entities(Project.id).all())
        if proj_ids:
            conds.append(model_class.project_id.in_(proj_ids))
        aff_ids = [aff.owner_id for aff in Affiliation.query.filter_by(viewer_id=user.id).all()]
        if aff_ids:
            conds.append(model_class.created_by.in_(aff_ids))
    elif name == 'Company':
        conds.append(model_class.id.in_(_get_worklog_shared_ids(user.id, 'customer_id')))
    # Contact: 仅通用共享(若有 shared_with_users);其可见性主要随所属公司,不在此叠加
    return conds

def get_viewable_data(model_class, user, special_filters=None):
    """
    通用数据访问控制函数，根据用户权限返回可查看的数据集
    针对 Project 模型，遵循：
    1. 当前用户是项目的 owner_id
    2. 当前用户是项目所有者的上级（归属链）
    3. 当前用户是项目的厂商销售负责人（vendor_sales_manager_id）
    目前项目暂未支持共享字段，仅用 owner_id、归属链和销售负责人字段判断
    """
    if special_filters is None:
        special_filters = []
    logger.debug(f"用户 {user.username} (ID: {user.id}, 角色: {user.role}) 查询 {model_class.__name__} 数据")

    # 管理员可以查看所有数据
    if user.role == 'admin':
        # 为所有支持软删除的模型添加is_deleted过滤条件
        base_filters = []
        if hasattr(model_class, 'is_deleted'):
            base_filters.append(model_class.is_deleted == False)
        all_filters = base_filters + (special_filters if special_filters else [])
        return model_class.query.filter(*all_filters)
    
    # 移除角色特殊权限逻辑，统一使用权限模块系统
    
    # User 模型特殊处理 - User 没有 owner_id 字段
    if model_class.__name__ == 'User':
        # 管理员已经在前面处理
        # 使用纯权限版本的访问控制（不包含数据归属）
        # 账户管理是非业务数据，不应受业务数据归属关系影响
        from app.utils.permissions import get_accessible_users_by_permission_only
        accessible_users = get_accessible_users_by_permission_only(user, 'user_management')
        accessible_user_ids = [u.id for u in accessible_users]
        return model_class.query.filter(model_class.id.in_(accessible_user_ids), *special_filters)
    
    # 产品数据不受限制
    if model_class.__name__ == 'Product':
        return model_class.query.filter(*special_filters)
    
    # 订单数据访问控制 - 使用统一权限系统（重构版）
    if model_class.__name__ == 'PurchaseOrder':
        # 检查用户是否有订单模块的查看权限
        if not user.has_permission('order', 'view'):
            return model_class.query.filter(False)

        # 获取用户在订单模块的权限级别
        permission_level = user.get_permission_level('order')

        # 使用统一的权限级别过滤逻辑
        if permission_level == 'system':
            query = model_class.query.filter(*special_filters if special_filters else [])
        elif permission_level == 'company' and user.company_name:
            company_user_ids = get_company_user_ids(user)
            query = model_class.query.filter(
                model_class.created_by_id.in_(company_user_ids),
                *special_filters
            )
        elif permission_level == 'department' and user.department:
            dept_user_ids = get_department_user_ids(user)
            query = model_class.query.filter(
                model_class.created_by_id.in_(dept_user_ids),
                *special_filters
            )
        else:  # personal
            viewable_user_ids = get_personal_viewable_user_ids(user)
            query = model_class.query.filter(
                model_class.created_by_id.in_(viewable_user_ids),
                *special_filters
            )

        # 应用内容过滤
        query = apply_content_filters(query, model_class, 'order', user)

        return query

    if model_class.__name__ == 'SalesOrder':
        # 客户订单：用 sales_order 模块 + created_by_id（SalesOrder 无 owner_id）
        if not user.has_permission('sales_order', 'view'):
            return model_class.query.filter(False)

        permission_level = user.get_permission_level('sales_order')

        if permission_level == 'system':
            query = model_class.query.filter(*special_filters if special_filters else [])
        elif permission_level == 'company' and user.company_name:
            company_user_ids = get_company_user_ids(user)
            query = model_class.query.filter(
                model_class.created_by_id.in_(company_user_ids),
                *special_filters
            )
        elif permission_level == 'department' and user.department:
            dept_user_ids = get_department_user_ids(user)
            query = model_class.query.filter(
                model_class.created_by_id.in_(dept_user_ids),
                *special_filters
            )
        else:  # personal
            viewable_user_ids = get_personal_viewable_user_ids(user)
            query = model_class.query.filter(
                model_class.created_by_id.in_(viewable_user_ids),
                *special_filters
            )

        query = apply_content_filters(query, model_class, 'sales_order', user)

        return query

    # 处理特殊角色权限 - Project模型 - 基于四级权限管理系统（重构版）
    if model_class.__name__ == 'Project':
        # 检查用户是否有项目模块的查看权限
        if not user.has_permission('project', 'view'):
            return model_class.query.filter(False)

        # 获取用户在项目模块的权限级别
        permission_level = user.get_permission_level('project')
        logger.info(f"🔍 [ACCESS_CONTROL] 用户 {user.username} (角色: {user.role}) 项目权限级别: {permission_level}")

        # 使用统一的权限级别过滤逻辑
        if permission_level == 'system':
            query = model_class.query.filter(*special_filters)
        else:
            # 数据范围(按级别) + 附加授权(共享/行程/任务/厂商负责人,各级统一叠加)
            if permission_level == 'company' and user.company_name:
                scope_ids = get_company_user_ids(user)
            elif permission_level == 'department' and user.department and user.company_name:
                scope_ids = get_department_user_ids(user)
            else:  # personal
                scope_ids = get_personal_viewable_user_ids(user)
            conditions = [model_class.owner_id.in_(scope_ids)]
            conditions += additive_grant_conditions(model_class, user)
            query = model_class.query.filter(db.or_(*conditions), *special_filters)

        # 应用内容过滤
        query = apply_content_filters(query, model_class, 'project', user)

        return query

    # 报价单特殊权限
    if model_class.__name__ == 'Quotation':
        # 检查用户是否有报价单模块的查看权限
        if not user.has_permission('quotation', 'view'):
            # 如果没有报价单查看权限，返回空查询
            return model_class.query.filter(False)

        # 统一处理角色字符串，去除空格
        user_role = user.role.strip() if user.role else ''

        # 基于四级权限系统的数据访问控制
        # 注：财务总监等角色通过权限配置系统授予 system 级权限，无需硬编码
        permission_level = user.get_permission_level('quotation')
        logger.info(f"🔍 [QUOTATION_ACCESS] 用户 {user.username} 权限级别: {permission_level}, company_name: '{user.company_name}'")

        # 构建基础查询
        query = None

        if permission_level == 'system':
            # 系统级权限：可以查看所有报价单
            query = model_class.query.filter(*special_filters if special_filters else [])
        elif permission_level == 'company':
            if not user.company_name:
                # company_name 为空，无法按企业过滤，降级到 personal 级别
                logger.warning(f"⚠️ [QUOTATION_ACCESS] 用户 {user.username} 有 company 级别权限但 company_name 为空，降级到 personal")
            else:
                # 企业级权限：可以查看企业内所有用户创建的报价单
                company_user_ids = get_company_user_ids(user, include_affiliations=True)
                logger.info(f"🔍 [QUOTATION_ACCESS] 用户 {user.username} 公司用户IDs: {company_user_ids}")

                # 公司内 owner + 附加授权(共享/行程/任务/厂商负责人,跨公司显式授权也可见)
                _add = additive_grant_conditions(model_class, user)
                query = model_class.query.filter(
                    db.or_(model_class.owner_id.in_(company_user_ids), *_add),
                    *special_filters if special_filters else []
                )
        elif permission_level == 'department':
            if not user.department or not user.company_name:
                # department 或 company_name 为空，降级到 personal 级别
                logger.warning(f"⚠️ [QUOTATION_ACCESS] 用户 {user.username} 有 department 级别权限但 department='{user.department}' 或 company_name='{user.company_name}' 为空，降级到 personal")
            else:
                # 部门级权限：可以查看部门内所有用户创建的报价单（包括归属关系）
                dept_user_ids = get_department_user_ids(user, include_affiliations=True)
                logger.info(f"🔍 [QUOTATION_ACCESS] 用户 {user.username} 部门用户IDs: {dept_user_ids}")

                # 部门内 owner + 附加授权(共享/行程/任务/厂商负责人)
                _add = additive_grant_conditions(model_class, user)
                query = model_class.query.filter(
                    db.or_(model_class.owner_id.in_(dept_user_ids), *_add),
                    *special_filters if special_filters else []
                )

        # 如果还没有构建查询（降级到 personal 级别）
        if query is None:
            # 收集所有可访问的报价单ID列表，避免使用UNION（因为JSON字段无法比较）
            accessible_quotation_ids = set()

            # 1. 直接归属（自己创建的报价单）
            owned_quotations = model_class.query.filter(model_class.owner_id == user.id).with_entities(model_class.id).all()
            accessible_quotation_ids.update([q.id for q in owned_quotations])

            # 2. 归属链（Affiliation - 下级创建的报价单）
            affiliation_owner_ids = [aff.owner_id for aff in Affiliation.query.filter_by(viewer_id=user.id).all()]
            if affiliation_owner_ids:
                subordinate_quotations = model_class.query.filter(model_class.owner_id.in_(affiliation_owner_ids)).with_entities(model_class.id).all()
                accessible_quotation_ids.update([q.id for q in subordinate_quotations])

            # 3. 销售负责人相关的项目的报价单
            sales_manager_projects = Project.query.filter(
                Project.vendor_sales_manager_id == user.id
            ).with_entities(Project.id).all()
            if sales_manager_projects:
                sales_manager_project_ids = [p.id for p in sales_manager_projects]
                sales_manager_quotations = model_class.query.filter(model_class.project_id.in_(sales_manager_project_ids)).with_entities(model_class.id).all()
                accessible_quotation_ids.update([q.id for q in sales_manager_quotations])

            # 4. PM/SE：行程共享项目 → 项目下报价单可见
            if user_role in ('product_manager', 'solution_manager'):
                worklog_shared_project_ids = _get_worklog_shared_ids(user.id, 'project_id')
                worklog_quotations = model_class.query.filter(
                    model_class.project_id.in_(worklog_shared_project_ids)
                ).with_entities(model_class.id).all()
                accessible_quotation_ids.update([q.id for q in worklog_quotations])

            # 5. 任务关联 → 报价单直接可见（任务明确指定了报价单）
            task_linked_quotation_ids = _get_task_linked_ids(user.id, 'quotation_id')
            task_quotations = model_class.query.filter(
                model_class.id.in_(task_linked_quotation_ids)
            ).with_entities(model_class.id).all()
            accessible_quotation_ids.update([q.id for q in task_quotations])

            # 返回基于ID列表的查询
            if accessible_quotation_ids:
                query = model_class.query.filter(model_class.id.in_(accessible_quotation_ids)).filter(*special_filters if special_filters else [])
            else:
                # 如果没有可访问的报价单，返回空查询
                return model_class.query.filter(model_class.id == -1)

        # 应用内容过滤（统一处理）
        query = apply_content_filters(query, model_class, 'quotation', user)
        return query
    
    # 客户特殊权限处理 - 基于权限管理系统（重构版）
    if model_class.__name__ in ['Company', 'Contact']:
        # 管理员已经在前面处理过，但为了防止意外，再次检查
        if user.role == 'admin':
            base_filters = []
            if hasattr(model_class, 'is_deleted'):
                base_filters.append(model_class.is_deleted == False)
            all_filters = base_filters + (special_filters if special_filters else [])
            return model_class.query.filter(*all_filters)

        # 检查用户是否有客户模块的查看权限
        if not user.has_permission('customer', 'view'):
            return model_class.query.filter(False)

        # 获取用户在客户模块的权限级别
        permission_level = user.get_permission_level('customer')
        logger.info(f"🔍 [ACCESS_CONTROL] 用户 {user.username} (角色: {user.role}) 客户权限级别: {permission_level}")

        # 为Company模型添加is_deleted过滤条件
        base_filters = []
        if model_class.__name__ == 'Company':
            base_filters.append(model_class.is_deleted == False)

        # 使用统一的权限级别过滤逻辑
        if permission_level == 'system':
            query = model_class.query.filter(*(base_filters + (special_filters if special_filters else [])))
        elif permission_level == 'company' and user.company_name:
            company_user_ids = get_company_user_ids(user)
            _add = additive_grant_conditions(model_class, user)
            all_filters = base_filters + [db.or_(model_class.owner_id.in_(company_user_ids), *_add)] + (special_filters if special_filters else [])
            query = model_class.query.filter(*all_filters)
        elif permission_level == 'department' and user.department and user.company_name:
            dept_user_ids = get_department_user_ids(user)
            _add = additive_grant_conditions(model_class, user)
            all_filters = base_filters + [db.or_(model_class.owner_id.in_(dept_user_ids), *_add)] + (special_filters if special_filters else [])
            query = model_class.query.filter(*all_filters)
        else:  # personal
            viewable_user_ids = get_personal_viewable_user_ids(user)

            # owner 范围 + 附加授权(共享/行程,统一函数;与 company/department 级一致)
            permission_conditions = [model_class.owner_id.in_(viewable_user_ids)]
            permission_conditions += additive_grant_conditions(model_class, user)

            all_filters = base_filters + [db.or_(*permission_conditions)] + (special_filters if special_filters else [])
            query = model_class.query.filter(*all_filters)

        # 应用内容过滤
        query = apply_content_filters(query, model_class, 'customer', user)

        return query
    
    # 报销单特殊权限处理 - 不使用数据归属机制（财务隐私保护）
    # 注意：报销单与业务数据不同，不应该基于数据归属关系共享
    # 仅基于权限级别（system/company/department/personal）进行访问控制
    # 参考实现：批价单（PricingOrder）权限逻辑
    if model_class.__name__ == 'Expense':
        # 检查用户是否有报销单模块的查看权限
        if not user.has_permission('expense', 'view'):
            return model_class.query.filter(False)

        # 基础过滤条件：排除已删除的报销单
        base_filters = [model_class.is_deleted == False] if hasattr(model_class, 'is_deleted') else []

        # 统一处理角色字符串，去除空格
        user_role = user.role.strip() if user.role else ''

        # 1. 管理员可以查看所有报销单
        if user_role == 'admin':
            return model_class.query.filter(*(base_filters + (special_filters if special_filters else [])))

        # 2. 其他角色基于权限配置的访问控制（不包含数据归属关系）
        permission_level = user.get_permission_level('expense')

        if permission_level == 'system':
            # 系统级权限：可以查看所有报销单
            query = model_class.query.filter(*(base_filters + (special_filters if special_filters else [])))
        elif permission_level == 'company' and user.company_name:
            # 公司级权限：可以查看公司内用户创建的报销单（不包含归属关系）
            company_user_ids = get_company_user_ids(user, include_affiliations=False)
            all_filters = base_filters + [model_class.owner_id.in_(company_user_ids)] + (special_filters if special_filters else [])
            query = model_class.query.filter(*all_filters)
        elif permission_level == 'department' and user.department and user.company_name:
            # 部门级权限：可以查看部门内用户创建的报销单（不包含归属关系）
            dept_user_ids = get_department_user_ids(user, include_affiliations=False)
            all_filters = base_filters + [model_class.owner_id.in_(dept_user_ids)] + (special_filters if special_filters else [])
            query = model_class.query.filter(*all_filters)
        else:  # personal
            # 个人级权限：只能查看自己创建的报销单 + 归属给自己的报销单
            # 🔥 修复：支持归属人查看归属给自己的报销单
            from sqlalchemy import or_
            personal_condition = or_(
                model_class.owner_id == user.id,  # 自己创建的
                model_class.attributed_to_id == user.id  # 归属给自己的
            )
            all_filters = base_filters + [personal_condition] + (special_filters if special_filters else [])
            query = model_class.query.filter(*all_filters)

        # 应用内容过滤
        query = apply_content_filters(query, model_class, 'expense', user)

        return query
    
    # 行动记录的特殊处理
    if model_class.__name__ == 'Action':
        # 行动记录权限控制：
        # 1. 共享记录(is_shared=True)：跟随客户的访问权限（包括共享权限）
        # 2. 非共享记录(is_shared=False)：仅对管理员、上级账户和记录创建者可见
        
        # 检查是否从项目页面查询
        is_project_query = False
        project_id = None
        if special_filters:
            for filter_condition in special_filters:
                # 检测是否有 project_id 过滤条件
                try:
                    if hasattr(filter_condition, 'left') and hasattr(filter_condition.left, 'key'):
                        if filter_condition.left.key == 'project_id':
                            is_project_query = True
                            # 获取项目ID值
                            if hasattr(filter_condition, 'right'):
                                project_id = filter_condition.right.value
                            break
                except:
                    continue
        
        # 如果是项目查询，检查用户是否有项目访问权限
        if is_project_query and project_id:
            # 管理员可以看到项目的所有行动记录
            if user.role in ['admin', 'system_admin']:
                return model_class.query.filter(
                    model_class.project_id == project_id,
                    *special_filters
                )
            
            # 检查用户是否能看到这个项目
            viewable_projects = get_viewable_data(Project, user)
            project = viewable_projects.filter_by(id=project_id).first()
            
            if project:
                # 用户有项目权限，可以看到项目的所有共享行动记录和自己的记录
                # 不需要检查公司权限
                return model_class.query.filter(
                    model_class.project_id == project_id,
                    db.or_(
                        db.or_(model_class.is_shared == True, model_class.is_shared.is_(None)),  # 共享记录
                        model_class.owner_id == user.id  # 自己的记录
                    ),
                    *special_filters
                )
            else:
                # 用户没有项目权限
                return model_class.query.filter(False)
        
        # 以下是原有的公司过滤逻辑（用于公司页面和通用查询）
        try:
            viewable_company_ids = [row[0] for row in get_viewable_data(Company, user).with_entities(Company.id).all()]
        except Exception as e:
            logger.error(f"获取可查看公司数据时出错: {e}")
            viewable_company_ids = []
        
        # 管理员和系统管理员可以查看所有Action记录（不受company_id限制）
        if user.role in ['admin', 'system_admin']:
            return model_class.query.filter(*special_filters)
        
        # 构建查询条件：
        # - 共享记录：按原有客户权限逻辑
        # - 非共享记录：仅创建者和上级账户可见
        # 如果没有可查看的公司，返回空查询
        if not viewable_company_ids:
            return model_class.query.filter(False)
            
        action_filters = [
            model_class.company_id.in_(viewable_company_ids),
            db.or_(
                db.or_(model_class.is_shared == True, model_class.is_shared.is_(None)),  # 共享记录或NULL值按客户权限
                model_class.owner_id == user.id  # 非共享记录仅创建者可见
            )
        ]
        
        # 上级账户可以查看下级的非共享记录
        subordinate_ids = []
        
        # 1. 基于角色的上级关系
        if user.role in ['sales_director', 'sales_manager', 'business_manager']:
            if user.role == 'sales_director':
                # 销售总监可以查看所有销售相关用户的记录
                subordinates = User.query.filter(
                    User.role.in_(['sales_manager', 'sales', 'channel_manager'])
                ).all()
                subordinate_ids.extend([u.id for u in subordinates])
            elif user.role in ['sales_manager', 'business_manager']:
                # 销售经理和商务经理可以查看同部门用户的记录
                if user.department and user.company_name:
                    subordinates = User.query.filter(
                        User.department == user.department,
                        User.company_name == user.company_name,
                        User.role.in_(['sales', 'business_admin'])
                    ).all()
                    subordinate_ids.extend([u.id for u in subordinates])
        
        # 2. 基于部门负责人关系的上级权限 - 支持多部门管理
        managed_depts = get_managed_departments(user)
        for dept_name, company_name in managed_depts:
            # 部门负责人可以查看本部门所有成员的非共享记录
            dept_members = User.query.filter(
                User.department == dept_name,
                User.company_name == company_name,
                User.id != user.id  # 排除自己
            ).all()
            subordinate_ids.extend([u.id for u in dept_members])
        
        # 去重
        subordinate_ids = list(set(subordinate_ids))
        
        if subordinate_ids:
            # 修改查询条件：非共享记录对创建者和上级可见
            action_filters[-1] = db.or_(
                db.or_(model_class.is_shared == True, model_class.is_shared.is_(None)),  # 共享记录或NULL值按客户权限
                model_class.owner_id.in_([user.id] + subordinate_ids)  # 非共享记录对创建者和上级可见
            )
        
        return model_class.query.filter(*action_filters, *special_filters)
    
    # 批价单的特殊处理 - PricingOrder 使用 created_by 字段而不是 owner_id（重构版）
    if model_class.__name__ == 'PricingOrder':
        # 检查用户是否有批价单模块的查看权限
        if not user.has_permission('pricing_order', 'view'):
            return model_class.query.filter(False)

        # 获取用户在批价单模块的权限级别
        permission_level = user.get_permission_level('pricing_order')

        # 为软删除模型添加is_deleted过滤条件
        base_filters = []
        if hasattr(model_class, 'is_deleted'):
            base_filters.append(model_class.is_deleted == False)

        # 使用统一的权限级别过滤逻辑;各级(system 除外)叠加附加授权(厂商负责人/归属上级/批价自身共享)
        if permission_level == 'system':
            query = model_class.query.filter(*(base_filters + (special_filters if special_filters else [])))
        else:
            if permission_level == 'company' and user.company_name:
                scope_ids = get_company_user_ids(user, include_affiliations=False)
            elif permission_level == 'department' and user.department and user.company_name:
                scope_ids = get_department_user_ids(user, include_affiliations=False)
            else:  # personal
                scope_ids = [user.id]
            _add = additive_grant_conditions(model_class, user)
            all_filters = base_filters + [db.or_(model_class.created_by.in_(scope_ids), *_add)] + (special_filters if special_filters else [])
            query = model_class.query.filter(*all_filters)

        # 应用内容过滤
        query = apply_content_filters(query, model_class, 'pricing_order', user)

        return query
    
    # 标准数据访问控制：自己的数据 + 归属关系授权的数据
    viewable_user_ids = [user.id]

    # 代理商和普通用户只能看到自己的数据
    if user.role not in ['dealer', 'user']:
        # 获取通过归属关系可以查看的数据
        affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
        for affiliation in affiliations:
            viewable_user_ids.append(affiliation.owner_id)

    return model_class.query.filter(
        model_class.owner_id.in_(viewable_user_ids),
        *special_filters
    )

def _has_basic_edit_permission(model_obj, user):
    """
    基本权限保障：检查用户是否对自己的数据拥有编辑权限

    这是一个辅助函数，用于实现"个人数据保底权限"规则：
    无论权限配置如何，用户始终拥有对自己创建数据的完整编辑权限。

    参数:
        model_obj: 数据对象
        user: 用户对象

    返回:
        True - 用户是数据拥有者，直接允许编辑
        False - 需要继续检查其他权限
    """
    # 标准owner_id字段检查（大部分模块使用）
    if hasattr(model_obj, 'owner_id') and model_obj.owner_id == user.id:
        return True

    # 特殊created_by字段检查（用于订单类模块）
    if hasattr(model_obj, 'created_by') and model_obj.created_by == user.id:
        return True

    # 特殊created_by_id字段检查
    if hasattr(model_obj, 'created_by_id') and model_obj.created_by_id == user.id:
        return True

    return False

def can_edit_data(model_obj, user):
    """
    检查用户是否有权限编辑指定的数据对象

    参数:
        model_obj: 数据对象
        user: 用户对象

    返回:
        bool: 是否有编辑权限
    """
    # 管理员有全部编辑权限
    if user.role == 'admin':
        return True
    
    # 统一处理角色字符串，去除空格
    user_role = user.role.strip() if user.role else ''
    
    # 特殊角色权限控制
    model_name = model_obj.__class__.__name__

    # 注：财务总监等角色的编辑权限通过权限配置系统控制
    # 如需限制某角色不能编辑特定模块，在权限配置中设置 can_edit=False

    # 账户(User)编辑：基于 user_management 模块权限,非数据归属机制。
    # 账户没有 owner_id/created_by 归属字段,若落到通用归属判断,任何非创建者(如 HR)都会被拒,
    # 导致有 user_management:edit 的 HR 改不了账户(试用期等)。此处按权限级别放行,
    # 与 get_viewable_data(User) 同口径(system 全部 / company 同企业 / department 同部门 / personal 仅自己)。
    if model_name == 'User':
        if not user.has_permission('user_management', 'edit'):
            return False
        level = user.get_permission_level('user_management')
        if level == 'system':
            return True
        if level == 'company' and user.company_name:
            return model_obj.company_name == user.company_name
        if level == 'department' and user.department and user.company_name:
            return (model_obj.department == user.department
                    and model_obj.company_name == user.company_name)
        return model_obj.id == user.id   # personal:仅自己

    # 产品经理：基于权限系统进行编辑权限控制
    if user_role in ['product_manager', 'product']:
        if model_name == 'Project':
            # 检查是否有项目编辑权限
            return user.has_permission('project', 'edit') and model_obj.owner_id == user.id
        elif model_name == 'Quotation':
            # 检查是否有报价单编辑权限，如果有权限则可以编辑企业内所有报价单
            if user.has_permission('quotation', 'edit') and user.company_name:
                # 检查报价单是否属于同企业
                if hasattr(model_obj, 'project') and model_obj.project:
                    project_owner = User.query.get(model_obj.project.owner_id)
                    return project_owner and project_owner.company_name == user.company_name
                return False
            return False
        # 其他数据按默认规则
        return model_obj.owner_id == user.id
    
    # 解决方案经理：基于权限系统进行编辑权限控制
    if user_role in ['solution_manager', 'solution']:
        if model_name == 'Project':
            # 检查是否有项目编辑权限
            return user.has_permission('project', 'edit') and model_obj.owner_id == user.id
        elif model_name == 'Quotation':
            # 解决方案经理如果有报价单编辑权限，可以编辑权限范围内的所有报价单
            # 不限于同企业，让后续的通用报价单处理逻辑来判断权限级别
            pass  # 不在此处返回，让代码继续执行到报价单通用处理逻辑
        else:
            # 其他数据按默认规则
            return model_obj.owner_id == user.id
    
    # 项目特殊处理：基于权限级别的编辑权限控制
    if model_name == 'Project':
        # 🆕 基本权限保障 - 用户始终可以编辑自己创建的项目
        if _has_basic_edit_permission(model_obj, user):
            return True

        # 厂商负责人特殊权限（独立于权限系统）
        if hasattr(model_obj, 'vendor_sales_manager_id') and model_obj.vendor_sales_manager_id == user.id:
            return True

        # 检查用户是否有项目模块的编辑权限（用于编辑他人数据）
        if not user.has_permission('project', 'edit'):
            return False

        # 检查权限级别（决定可以编辑哪些他人的数据）
        permission_level = user.get_permission_level('project')

        if permission_level == 'system':
            # 系统级权限：可以编辑所有项目
            return True
        elif permission_level == 'company' and user.company_name:
            # 企业级权限：可以编辑企业下所有项目
            data_owner = User.query.get(model_obj.owner_id)
            return data_owner and data_owner.company_name == user.company_name
        elif permission_level == 'department' and user.department and user.company_name:
            # 部门级权限：可以编辑部门下所有项目
            data_owner = User.query.get(model_obj.owner_id)
            return (data_owner and data_owner.department == user.department and
                   data_owner.company_name == user.company_name)

        # personal级别：已在基本权限保障中处理，这里返回False
        return False
    
    # 客户特殊处理：基于权限级别的编辑权限控制
    if model_name == 'Company':
        # 🆕 基本权限保障 - 用户始终可以编辑自己创建的客户
        if _has_basic_edit_permission(model_obj, user):
            return True

        # 检查用户是否有客户模块的编辑权限（用于编辑他人数据）
        if not user.has_permission('customer', 'edit'):
            return False

        # 检查权限级别（决定可以编辑哪些他人的数据）
        permission_level = user.get_permission_level('customer')

        if permission_level == 'system':
            # 系统级权限：可以编辑所有客户
            return True
        elif permission_level == 'company' and user.company_name:
            # 企业级权限：可以编辑企业下所有客户
            data_owner = User.query.get(model_obj.owner_id)
            return data_owner and data_owner.company_name == user.company_name
        elif permission_level == 'department' and user.department and user.company_name:
            # 部门级权限：可以编辑部门下所有客户
            data_owner = User.query.get(model_obj.owner_id)
            return (data_owner and data_owner.department == user.department and
                   data_owner.company_name == user.company_name)

        # personal级别：已在基本权限保障中处理，这里返回False
        return False

    # 联系人特殊处理：归属 customer 模块，按 customer 权限级别控制
    if model_name == 'Contact':
        # 基本权限保障 - 自己创建的联系人始终可编辑
        if _has_basic_edit_permission(model_obj, user):
            return True

        # 需有 customer 模块编辑权限(用于编辑他人数据)
        if not user.has_permission('customer', 'edit'):
            return False

        permission_level = user.get_permission_level('customer')
        if permission_level == 'system':
            return True
        data_owner = User.query.get(model_obj.owner_id)
        if permission_level == 'company' and user.company_name:
            return bool(data_owner and data_owner.company_name == user.company_name)
        if permission_level == 'department' and user.department and user.company_name:
            return bool(data_owner and data_owner.department == user.department and
                        data_owner.company_name == user.company_name)
        # personal级别：仅自己创建(上方已处理)
        return False

    # 报价单特殊处理：基于权限级别的编辑权限控制
    if model_name == 'Quotation':
        # 🆕 基本权限保障 - 用户始终可以编辑自己创建的报价单
        if _has_basic_edit_permission(model_obj, user):
            return True

        # 项目的厂商负责人可以编辑相关报价单（独立于权限系统）
        if (hasattr(model_obj, 'project') and model_obj.project and
            hasattr(model_obj.project, 'vendor_sales_manager_id') and
            model_obj.project.vendor_sales_manager_id == user.id):
            return True

        # 🆕 SM 确认被指派人可以编辑(独立于权限系统,确认核查时需调整产品/数量)
        try:
            from app.models.quotation_confirmation_task import QuotationConfirmationTask
            if QuotationConfirmationTask.query.filter_by(
                quotation_id=model_obj.id, assignee_id=user.id, status='pending'
            ).first():
                return True
        except Exception:
            pass

        # 检查用户是否有报价单模块的编辑权限（用于编辑他人数据）
        # 注：解决方案经理的编辑权限通过权限级别控制，而非直接授权所有报价单
        if not user.has_permission('quotation', 'edit'):
            return False

        # 检查权限级别（决定可以编辑哪些他人的数据）
        permission_level = user.get_permission_level('quotation')

        if permission_level == 'system':
            # 系统级权限：可以编辑所有报价单
            return True
        elif permission_level == 'company' and user.company_name:
            # 企业级权限：可以编辑企业下所有报价单
            data_owner = User.query.get(model_obj.owner_id)
            return data_owner and data_owner.company_name == user.company_name
        elif permission_level == 'department' and user.department and user.company_name:
            # 部门级权限：可以编辑部门下所有报价单
            data_owner = User.query.get(model_obj.owner_id)
            return (data_owner and data_owner.department == user.department and
                   data_owner.company_name == user.company_name)

        # personal级别：已在基本权限保障中处理，这里返回False
        return False
    
    # 报销单特殊处理：支持审批权限
    if model_name == 'Expense':
        # 🆕 基本权限保障 - 用户始终可以编辑自己创建的报销单
        if _has_basic_edit_permission(model_obj, user):
            return True

        # 审批权限特殊处理：审批人在审批过程中可以编辑
        if has_approval_permission(user, model_obj):
            return True

        # 检查用户是否有报销单模块的编辑权限（用于编辑他人数据）
        if not user.has_permission('expense', 'edit'):
            return False

        # 基于四级权限系统的编辑权限控制（决定可以编辑哪些他人的数据）
        # 注：财务总监等角色通过配置 system 级 expense 编辑权限即可编辑所有报销单
        permission_level = user.get_permission_level('expense')

        if permission_level == 'system':
            return True
        elif permission_level == 'company' and user.company_name:
            # 企业级权限：可以编辑企业下所有报销单
            if hasattr(model_obj, 'owner') and model_obj.owner:
                return model_obj.owner.company_name == user.company_name
            else:
                owner = User.query.get(model_obj.owner_id)
                return owner and owner.company_name == user.company_name
        elif permission_level == 'department' and user.department and user.company_name:
            # 部门级权限：可以编辑部门下所有报销单
            if hasattr(model_obj, 'owner') and model_obj.owner:
                return (model_obj.owner.department == user.department and
                       model_obj.owner.company_name == user.company_name)
            else:
                owner = User.query.get(model_obj.owner_id)
                return (owner and owner.department == user.department and
                       owner.company_name == user.company_name)

        # 部门负责人特殊权限：可以编辑本公司本部门所有用户的报销单 - 支持多部门管理
        managed_depts = get_managed_departments(user)
        if managed_depts:
            if hasattr(model_obj, 'owner') and model_obj.owner:
                owner_dept = (model_obj.owner.department, model_obj.owner.company_name)
                if owner_dept in managed_depts:
                    return True
            else:
                owner = User.query.get(model_obj.owner_id)
                if owner:
                    owner_dept = (owner.department, owner.company_name)
                    if owner_dept in managed_depts:
                        return True

        # personal级别：已在基本权限保障中处理，这里返回False
        return False
    
    # 营销总监只能编辑自己的数据
    if user_role == 'sales_director':
        return _has_basic_edit_permission(model_obj, user)

    # 渠道经理只能编辑自己的数据
    if user_role == 'channel_manager':
        return _has_basic_edit_permission(model_obj, user)

    # 销售角色只能编辑自己的数据
    if user_role in ['sales', 'sales_manager']:
        return _has_basic_edit_permission(model_obj, user)

    # 其他角色的编辑权限逻辑：默认使用基本权限保障
    return _has_basic_edit_permission(model_obj, user)

def get_accessible_data(model_class, user, special_filters=None):
    """
    与 get_viewable_data 类似，但提供更严格的数据访问控制
    仅返回用户有完全访问权限的数据
    
    参数:
        model_class: 数据模型类
        user: 用户对象
        special_filters: 额外的过滤条件列表
    
    返回:
        查询结果集
    """
    if special_filters is None:
        special_filters = []
    
    # 记录日志
    logger.debug(f"用户 {user.username} (ID: {user.id}, 角色: {user.role}) 访问 {model_class.__name__} 数据")
    
    # 管理员可以访问所有数据
    if user.role == 'admin':
        return model_class.query.filter(*special_filters)
    
    # 默认情况下，用户只能访问自己创建的数据
    return model_class.query.filter(
        model_class.owner_id == user.id,
        *special_filters
    )

# --- 权限函数重构 ---

def can_view_company(user, company):
    """
    检查用户是否有权限查看指定的客户
    """
    # 处理匿名用户
    if not user or not hasattr(user, 'username') or not hasattr(user, 'id'):
        logger.debug(f"[权限检查] 匿名用户或无效用户 - 拒绝访问企业 '{company.company_name if company else 'unknown'}'")
        return False
    
    logger.debug(f"[权限检查] 用户 {user.username} (ID: {user.id}, 角色: {user.role}) 尝试访问企业 '{company.company_name}' (ID: {company.id}, 拥有者: {company.owner_id})")
    
    if user.role == 'admin':
        logger.debug(f"[权限检查] 管理员权限 - 允许访问")
        return True
    if user.id == company.owner_id:
        logger.debug(f"[权限检查] 企业拥有者权限 - 允许访问")
        return True
    
    # 首先检查用户是否有客户查看权限
    if not user.has_permission('customer', 'view'):
        logger.debug(f"[权限检查] 用户无客户查看权限 - 拒绝访问")
        return False
    
    # 基于四级权限系统的访问控制
    permission_level = user.get_permission_level('customer')
    logger.debug(f"[权限检查] 用户 {user.username} 的客户权限级别: {permission_level}")
    
    if permission_level == 'system':
        # 系统级权限：可以查看所有客户
        logger.debug(f"[权限检查] 系统级权限 - 允许访问")
        return True
    elif permission_level == 'company':
        # 公司级权限：可以查看同公司的所有客户
        if user.company_name:
            company_owner = User.query.get(company.owner_id)
            if company_owner and company_owner.company_name == user.company_name:
                logger.debug(f"[权限检查] 公司级权限 - 同公司客户 - 允许访问")
                return True
    elif permission_level == 'department':
        # 部门级权限：可以查看同部门的客户
        if user.department and user.company_name:
            company_owner = User.query.get(company.owner_id)
            if (company_owner and 
                company_owner.department == user.department and 
                company_owner.company_name == user.company_name):
                logger.debug(f"[权限检查] 部门级权限 - 同部门客户 - 允许访问")
                return True

    # 判断是否通过共享获得权限
    if hasattr(company, 'shared_with_users') and company.shared_with_users:
        if user.id in company.shared_with_users:
            logger.debug(f"[权限检查] 企业共享权限 - 允许访问")
            return True
            
    # 判断是否通过归属关系获得权限
    affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
    if company.owner_id in [affiliation.owner_id for affiliation in affiliations]:
        logger.debug(f"[权限检查] 归属关系权限 - 允许访问")
        return True
    
    # 部门负责人权限：可以查看本公司本部门所有用户的客户 - 支持多部门管理
    managed_depts = get_managed_departments(user)
    if managed_depts:
        company_owner = User.query.get(company.owner_id)
        if company_owner:
            owner_dept = (company_owner.department, company_owner.company_name)
            if owner_dept in managed_depts:
                logger.debug(f"[权限检查] 部门负责人权限 - 允许访问")
                return True

    # 判断是否创建了该公司下的联系人
    from app.models.customer import Contact
    contact_count = Contact.query.filter_by(company_id=company.id, owner_id=user.id).count()
    if contact_count > 0:
        logger.debug(f"[权限检查] 联系人创建权限 - 允许访问")
        return True

    # 行程共享：如果用户被共享了关联该客户的行程记录
    try:
        from app.models.worklog import WorkItem
        is_worklog_shared = WorkItem.query.filter(
            WorkItem.customer_id == company.id,
            WorkItem.is_deleted == False,
            cast(WorkItem.shared_with_users, JSONB).op('@>')(text(f"'[{user.id}]'::jsonb"))
        ).first() is not None
        if is_worklog_shared:
            logger.debug(f"[权限检查] 行程共享权限 - 允许访问")
            return True
    except Exception as e:
        logger.debug(f"检查行程共享权限时出错: {e}")

    logger.debug(f"[权限检查] 所有权限检查失败 - 拒绝访问")
    return False

def can_view_quotation(user, quotation):
    """
    检查用户是否有权限查看指定的报价单

    参数:
        user: 用户对象
        quotation: 报价单对象

    返回:
        bool: 是否有查看权限
    """
    # 处理匿名用户
    if not user or not hasattr(user, 'username') or not hasattr(user, 'id'):
        logger.debug(f"[权限检查] 匿名用户或无效用户 - 拒绝访问报价单 {quotation.id if quotation else 'unknown'}")
        return False

    logger.debug(f"[权限检查] 用户 {user.username} (ID: {user.id}, 角色: {user.role}) 尝试访问报价单 ID: {quotation.id}, Owner: {quotation.owner_id}")

    # 管理员可以查看所有报价单
    if user.role == 'admin':
        logger.debug(f"[权限检查] 管理员权限 - 允许访问")
        return True

    # 自己创建的报价单
    if user.id == quotation.owner_id:
        logger.debug(f"[权限检查] 报价单拥有者权限 - 允许访问")
        return True

    # 首先检查用户是否有报价单查看权限
    if not user.has_permission('quotation', 'view'):
        logger.debug(f"[权限检查] 用户无报价单查看权限 - 拒绝访问")
        return False

    # 基于四级权限系统的访问控制
    permission_level = user.get_permission_level('quotation')
    logger.debug(f"[权限检查] 用户 {user.username} 的报价单权限级别: {permission_level}")

    if permission_level == 'system':
        # 系统级权限：可以查看所有报价单
        logger.debug(f"[权限检查] 系统级权限 - 允许访问")
        return True
    elif permission_level == 'company':
        # 公司级权限：可以查看同公司的所有报价单
        if user.company_name:
            quotation_owner = User.query.get(quotation.owner_id)
            if quotation_owner and quotation_owner.company_name == user.company_name:
                logger.debug(f"[权限检查] 公司级权限 - 同公司报价单 - 允许访问")
                return True
    elif permission_level == 'department':
        # 部门级权限：可以查看同部门的报价单
        if user.department and user.company_name:
            quotation_owner = User.query.get(quotation.owner_id)
            if (quotation_owner and
                quotation_owner.department == user.department and
                quotation_owner.company_name == user.company_name):
                logger.debug(f"[权限检查] 部门级权限 - 同部门报价单 - 允许访问")
                return True

    # 判断是否通过归属关系获得权限
    affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
    if quotation.owner_id in [affiliation.owner_id for affiliation in affiliations]:
        logger.debug(f"[权限检查] 归属关系权限 - 允许访问")
        return True

    # 部门负责人权限：可以查看本公司本部门所有用户的报价单 - 支持多部门管理
    managed_depts = get_managed_departments(user)
    if managed_depts:
        quotation_owner = User.query.get(quotation.owner_id)
        if quotation_owner:
            owner_dept = (quotation_owner.department, quotation_owner.company_name)
            if owner_dept in managed_depts:
                logger.debug(f"[权限检查] 部门负责人权限 - 允许访问")
                return True

    # 判断是否通过共享获得权限
    if hasattr(quotation, 'shared_with_users') and quotation.shared_with_users:
        if user.id in quotation.shared_with_users:
            logger.debug(f"[权限检查] 报价单共享权限 - 允许访问")
            return True

    # 项目「主动共享」不再传导到报价单(共享只给项目本体);
    # 仅「资源池审批」显式勾选了报价单才放行(项目级或客户级 AccessRequest)
    if quotation.project_id:
        project = quotation.project
        if project and getattr(project, 'shared_with_users', None) and user.id in project.shared_with_users:
            from app.models.access_request import AccessRequest
            access_req = AccessRequest.query.filter_by(
                requester_id=user.id, entity_type='project',
                entity_id=project.id, status='approved'
            ).order_by(AccessRequest.resolved_at.desc()).first()
            if access_req:
                if access_req.share_options and access_req.share_options.get('quotations'):
                    logger.debug(f"[权限检查] 资源池项目审批共享(含报价单) - 允许访问")
                    return True
            else:
                # 无项目级 AccessRequest → 检查客户级资源池审批
                from app.models.project_customer_association import ProjectCustomerAssociation
                assoc_company_ids = [a.company_id for a in
                    ProjectCustomerAssociation.query.filter_by(project_id=project.id).all()]
                if assoc_company_ids:
                    customer_req = AccessRequest.query.filter(
                        AccessRequest.requester_id == user.id,
                        AccessRequest.entity_type == 'customer',
                        AccessRequest.entity_id.in_(assoc_company_ids),
                        AccessRequest.status == 'approved'
                    ).order_by(AccessRequest.resolved_at.desc()).first()
                    if customer_req and customer_req.share_options and customer_req.share_options.get('quotations'):
                        logger.debug(f"[权限检查] 资源池客户审批共享(含报价单) - 允许访问")
                        return True
            # 其余(纯主动项目共享 / 未勾选报价单)→ 不放行,继续后续检查

    # 注：财务总监、渠道经理、营销总监、服务经理等角色的报价单查看权限
    # 通过权限配置系统控制：
    # - 配置 quotation 模块的 system/company 级权限
    # - 使用 content_filters 字段限制可见的 project_type
    # 例如：channel_manager 配置 content_filters = {"project_type": ["channel_follow"]}

    # 厂商销售负责人权限：可以查看自己负责的项目的报价单
    if quotation.project and hasattr(quotation.project, 'vendor_sales_manager_id'):
        if quotation.project.vendor_sales_manager_id == user.id:
            logger.debug(f"[权限检查] 厂商销售负责人权限 - 允许访问")
            return True

    # 产品经理/解决方案经理：如果是报价单关联项目的支持人员，允许查看
    if user.role in ('product_manager', 'solution_manager') and quotation.project_id:
        from app.models.worklog import WorkItem
        from sqlalchemy import cast, text
        from sqlalchemy.dialects.postgresql import JSONB
        is_contributor = WorkItem.query.filter(
            WorkItem.project_id == quotation.project_id,
            WorkItem.is_deleted == False,
            db.or_(
                WorkItem.owner_id == user.id,
                cast(WorkItem.shared_with_users, JSONB).op('@>')(text(f"'[{user.id}]'::jsonb"))
            )
        ).first() is not None
        if is_contributor:
            logger.debug(f"[权限检查] 项目支持人员(PM/SE) - 允许访问报价单")
            return True

    # 任务关联：如果用户是关联该报价单的任务的创建者或被指派人
    try:
        from app.models.task import Task as GeneralTask
        is_task_linked = GeneralTask.query.filter(
            GeneralTask.quotation_id == quotation.id,
            GeneralTask.is_deleted == False,
            GeneralTask.status.in_(['pending', 'in_progress', 'completed']),
            db.or_(GeneralTask.assignee_id == user.id, GeneralTask.creator_id == user.id)
        ).first() is not None
        if is_task_linked:
            logger.debug(f"[权限检查] 任务关联权限 - 允许访问报价单")
            return True
    except Exception as e:
        logger.debug(f"检查任务关联权限时出错: {e}")

    logger.debug(f"[权限检查] 所有权限检查失败 - 拒绝访问")
    return False

def can_view_pricing_order(user, pricing_order):
    """
    检查用户是否有权限查看指定的批价单

    参数:
        user: 用户对象
        pricing_order: 批价单对象

    返回:
        bool: 是否有查看权限

    注意：批价单使用 created_by 字段而非 owner_id
    """
    # 处理匿名用户
    if not user or not hasattr(user, 'username') or not hasattr(user, 'id'):
        logger.debug(f"[权限检查] 匿名用户或无效用户 - 拒绝访问批价单 {pricing_order.id if pricing_order else 'unknown'}")
        return False

    logger.debug(f"[权限检查] 用户 {user.username} (ID: {user.id}, 角色: {user.role}) 尝试访问批价单 ID: {pricing_order.id}, Creator: {pricing_order.created_by}")

    # 管理员可以查看所有批价单
    if user.role == 'admin':
        logger.debug(f"[权限检查] 管理员权限 - 允许访问")
        return True

    # 自己创建的批价单
    if user.id == pricing_order.created_by:
        logger.debug(f"[权限检查] 批价单创建者权限 - 允许访问")
        return True

    # 首先检查用户是否有批价单查看权限
    if not user.has_permission('pricing_order', 'view'):
        logger.debug(f"[权限检查] 用户无批价单查看权限 - 拒绝访问")
        return False

    # 基于四级权限系统的访问控制
    permission_level = user.get_permission_level('pricing_order')
    logger.debug(f"[权限检查] 用户 {user.username} 的批价单权限级别: {permission_level}")

    if permission_level == 'system':
        # 系统级权限：可以查看所有批价单
        logger.debug(f"[权限检查] 系统级权限 - 允许访问")
        return True
    elif permission_level == 'company':
        # 公司级权限：可以查看同公司的所有批价单
        if user.company_name:
            creator = User.query.get(pricing_order.created_by)
            if creator and creator.company_name == user.company_name:
                logger.debug(f"[权限检查] 公司级权限 - 同公司批价单 - 允许访问")
                return True
    elif permission_level == 'department':
        # 部门级权限：可以查看同部门的批价单
        if user.department and user.company_name:
            creator = User.query.get(pricing_order.created_by)
            if (creator and
                creator.department == user.department and
                creator.company_name == user.company_name):
                logger.debug(f"[权限检查] 部门级权限 - 同部门批价单 - 允许访问")
                return True

    # 批价单不使用归属关系机制（已移除，与报销单保持一致）

    # 部门负责人权限：可以查看本公司本部门所有用户的批价单 - 支持多部门管理
    managed_depts = get_managed_departments(user)
    if managed_depts:
        creator = User.query.get(pricing_order.created_by)
        if creator:
            creator_dept = (creator.department, creator.company_name)
            if creator_dept in managed_depts:
                logger.debug(f"[权限检查] 部门负责人权限 - 允许访问")
                return True

    # 判断是否通过共享获得权限
    if hasattr(pricing_order, 'shared_with_users') and pricing_order.shared_with_users:
        if user.id in pricing_order.shared_with_users:
            logger.debug(f"[权限检查] 批价单共享权限 - 允许访问")
            return True

    # 厂商销售负责人权限：可以查看自己负责的项目的批价单
    if pricing_order.project and hasattr(pricing_order.project, 'vendor_sales_manager_id'):
        if pricing_order.project.vendor_sales_manager_id == user.id:
            logger.debug(f"[权限检查] 厂商销售负责人权限 - 允许访问")
            return True

    # 归属上级权限：可以查看下属创建的批价单(与"上级全量可见"一致)
    if pricing_order.created_by in [aff.owner_id for aff in Affiliation.query.filter_by(viewer_id=user.id).all()]:
        logger.debug(f"[权限检查] 归属上级权限 - 允许访问")
        return True

    # 审批人权限：检查 V2 审批系统
    if pricing_order.status in ('pending', 'approved', 'rejected', 'recalled'):
        try:
            from app.models.approval import ApprovalInstance, ApprovalStatus, ApprovalRecord
            from app.helpers.approval_helpers import get_step_actual_approver

            # 当前待审批人
            v2_instance = ApprovalInstance.query.filter_by(
                object_type='pricing_order',
                object_id=pricing_order.id,
                status=ApprovalStatus.PENDING
            ).first()
            if v2_instance:
                current_step_info = v2_instance.get_current_step_info()
                if current_step_info:
                    approver = get_step_actual_approver(current_step_info, v2_instance)
                    if approver and approver.id == user.id:
                        logger.debug(f"[权限检查] V2当前审批人权限 - 允许访问")
                        return True

            # 历史审批人（已完结实例）
            v2_past = ApprovalRecord.query.join(ApprovalInstance).filter(
                ApprovalInstance.object_type == 'pricing_order',
                ApprovalInstance.object_id == pricing_order.id,
                ApprovalRecord.approver_id == user.id
            ).first()
            if v2_past:
                logger.debug(f"[权限检查] V2历史审批人权限 - 允许访问")
                return True
        except Exception as e:
            logger.debug(f"[权限检查] V2审批系统检查出错: {str(e)}")

    logger.debug(f"[权限检查] 所有权限检查失败 - 拒绝访问")
    return False

def can_edit_company_info(user, company):
    """
    判断是否可以编辑客户基本信息

    收口到通用 can_edit_data(认 customer 模块 system/company/department 级别),
    再保留「数据归属下属的客户可编辑」。修复:company/department 级用户(如商务助理)
    对同事客户看不到编辑按钮的不一致(按钮闸门曾绕开级别判断)。
    """
    if can_edit_data(company, user):
        return True

    affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
    if company.owner_id in [aff.owner_id for aff in affiliations]:
        return True

    return False

def can_edit_company_sharing(user, company):
    """
    判断是否可以编辑客户共享设置
    允许：
    - 管理员
    - 拥有者
    - 通过Affiliation归属关系（viewer_id为当前用户，owner_id为客户owner）
    """
    if user.role == 'admin':
        return True
    if user.id == company.owner_id:
        return True

    affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
    if company.owner_id in [aff.owner_id for aff in affiliations]:
        return True

    return False

def can_delete_company(user, company):
    """
    只允许admin和拥有者删除
    """
    return user.role == 'admin' or user.id == company.owner_id

def can_view_contact(user, contact):
    """
    检查用户是否有权限查看指定的联系人
    """
    if user.role == 'admin':
        return True
    if user.id == contact.owner_id:
        return True

    # 如果用户拥有该联系人所属的客户，则可以查看该联系人
    company = contact.company
    if company and company.owner_id == user.id:
        return True

    # 基于权限级别的访问控制（与 can_view_company / get_viewable_data 保持一致）
    if user.has_permission('customer', 'view'):
        permission_level = user.get_permission_level('customer')
        if permission_level == 'system':
            return True
        elif permission_level == 'company' and user.company_name:
            contact_owner = User.query.get(contact.owner_id)
            if contact_owner and contact_owner.company_name == user.company_name:
                return True
        elif permission_level == 'department' and user.department and user.company_name:
            contact_owner = User.query.get(contact.owner_id)
            if (contact_owner and
                    contact_owner.department == user.department and
                    contact_owner.company_name == user.company_name):
                return True

    # 判断是否有指定的联系人归属
    if hasattr(contact, 'assigned_to') and contact.assigned_to == user.id:
        return True
    # 判断联系人是否覆盖了公司的共享设置并禁用共享
    if hasattr(contact, 'override_share') and contact.override_share:
        if hasattr(contact, 'shared_disabled') and contact.shared_disabled:
            return False
    # 检查公司共享设置
    if hasattr(company, 'shared_with_users') and company.shared_with_users:
        if user.id in company.shared_with_users:
            # share_contacts 默认值为 True，NULL(旧数据未backfill)视同 True
            if not hasattr(company, 'share_contacts') or company.share_contacts is not False:
                return True
    # 判断是否通过归属关系获得权限
    affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
    if contact.owner_id in [affiliation.owner_id for affiliation in affiliations]:
        return True

    return False

def can_edit_contact(user, contact):
    """
    检查用户是否有权限编辑指定的联系人

    收口到通用 can_edit_data(Contact 分支,认 customer 模块 system/company/department 级别),
    再保留「数据归属下属的联系人可编辑」。修复:company/department 级用户(如商务助理)
    改不了同事联系人的不一致。共享联系人仍只读。
    """
    if can_edit_data(contact, user):
        return True

    # 判断是否通过归属关系获得编辑权限
    affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
    if contact.owner_id in [aff.owner_id for aff in affiliations]:
        return True

    # 共享联系人只能查看，不能编辑
    return False

def can_delete_contact(user, contact):
    """
    检查用户是否有权限删除指定的联系人
    """
    # 管理员可以删除任何联系人
    if user.role == 'admin':
        return True
    # 联系人创建者可以删除自己创建的联系人
    return user.id == contact.owner_id 

def can_view_project(user, project):
    """
    判断用户是否有权查看该项目：
    1. 归属人
    2. 厂商负责人
    3. 归属链
    4. 权限配置系统（system/company/department 级权限 + content_filters）
    5. 共享
    6. 客户拥有者权限：如果用户拥有与项目关联的任一客户
    7. 审批人权限：如果用户是当前审批步骤的审批人
    """
    if user.role == 'admin':
        return True
    if user.id == project.owner_id:
        return True
    
    # 检查是否为当前审批人
    try:
        from app.helpers.approval_helpers import is_current_approver
        if is_current_approver('project', project.id, user.id):
            return True
    except Exception as e:
        logger.warning(f"检查审批人权限时出错: {e}")
    
    # 厂商负责人可以查看项目
    if hasattr(project, 'vendor_sales_manager_id') and project.vendor_sales_manager_id == user.id:
        return True
    
    # 🔥 关键修复：如果用户拥有与项目关联的任一客户，则可以查看该项目
    try:
        # 从 ProjectCustomerAssociation 获取项目关联的客户
        from app.models.project_customer_association import ProjectCustomerAssociation

        associations = ProjectCustomerAssociation.query.filter_by(project_id=project.id).all()

        if associations:
            # 获取关联的客户ID列表
            related_company_ids = [assoc.company_id for assoc in associations]

            # 检查用户是否拥有任一关联客户
            owned_companies = Company.query.filter(
                Company.id.in_(related_company_ids),
                Company.owner_id == user.id,
                Company.is_deleted == False
            ).first()

            if owned_companies:
                return True
    except Exception as e:
        logger.debug(f"检查项目关联客户拥有权限时出错: {e}")
    
    # 注：财务总监、解决方案经理、产品经理、商务助理等角色的项目查看权限
    # 通过权限配置系统控制：
    # - 配置 project 模块的 system/company 级权限
    # - 使用 content_filters 字段限制可见的 project_type
    # 例如：business_admin 配置 content_filters = {"project_type": ["sales_key", "sales_focus", "channel_follow"]}

    affiliation_owner_ids = [aff.owner_id for aff in Affiliation.query.filter_by(viewer_id=user.id).all()]

    # 归属关系权限检查
    if project.owner_id in affiliation_owner_ids:
        return True
    
    # 检查通过项目直接共享获得的访问权限
    try:
        from app.utils.sharing import SharingService
        if (hasattr(project, 'share_enabled') and project.share_enabled and 
            hasattr(project, 'is_shared_with_user') and project.is_shared_with_user(user.id)):
            return True
    except Exception as e:
        logger.debug(f"检查项目直接共享权限时出错: {e}")

    # 行程共享：如果用户被共享了关联该项目的行程记录
    try:
        from app.models.worklog import WorkItem
        is_worklog_shared = WorkItem.query.filter(
            WorkItem.project_id == project.id,
            WorkItem.is_deleted == False,
            cast(WorkItem.shared_with_users, JSONB).op('@>')(text(f"'[{user.id}]'::jsonb"))
        ).first() is not None
        if is_worklog_shared:
            return True
    except Exception as e:
        logger.debug(f"检查行程共享权限时出错: {e}")

    # 任务关联：如果用户是关联该项目的任务的创建者或被指派人
    try:
        from app.models.task import Task as GeneralTask
        is_task_linked = GeneralTask.query.filter(
            GeneralTask.project_id == project.id,
            GeneralTask.is_deleted == False,
            GeneralTask.status.in_(['pending', 'in_progress', 'completed']),
            db.or_(GeneralTask.assignee_id == user.id, GeneralTask.creator_id == user.id)
        ).first() is not None
        if is_task_linked:
            return True
    except Exception as e:
        logger.debug(f"检查任务关联权限时出错: {e}")

    # 最后一道防线:通用权限系统(system/company/department 级 + content_filters)
    # 修复审批通过后,曾经的"当前审批人"失去 is_current_approver 身份,但其
    # 配置的 system 级 project 权限应该让他继续可见 — 之前代码漏了这层 fallback。
    try:
        viewable = get_viewable_data(Project, user, [Project.id == project.id]).first()
        if viewable is not None:
            return True
    except Exception as e:
        logger.debug(f"通用权限系统 fallback 检查失败: {e}")

    return False

def register_context_processors(app):
    """
    注册权限辅助函数到应用上下文处理器
    这个函数应该在应用初始化时被调用
    """
    from app.utils.role_mappings import get_role_special_permissions
    
    @app.context_processor
    def inject_permission_helpers():
        return dict(
            can_edit_company_info=can_edit_company_info,
            can_edit_company_sharing=can_edit_company_sharing,
            can_delete_company=can_delete_company,
            can_view_contact=can_view_contact,
            can_edit_contact=can_edit_contact,
            can_delete_contact=can_delete_contact,
            can_view_project=can_view_project,
            can_view_company=can_view_company,
            can_delete_project=can_delete_project,
            can_delete_quotation=can_delete_quotation,
            can_edit_data=can_edit_data,
            get_role_special_permissions=get_role_special_permissions
        )

def can_change_company_owner(user, company):
    """判断用户是否有权修改客户的拥有人。"""
    if user.role == 'admin':
        return True

    # 检查用户是否具有客户模块的拥有人修改权限
    if user.has_permission('customer', 'change_owner'):
        permission_level = user.get_permission_level('customer')
        return _check_permission_level_scope(user, company.owner_id, permission_level)

    return False

def can_change_project_owner(user, project):
    """判断用户是否有权修改项目的拥有人。"""
    if user.role == 'admin':
        return True

    # 厂商销售负责人特权（唯一无法用权限系统表达的业务关系）
    if hasattr(project, 'vendor_sales_manager_id') and project.vendor_sales_manager_id == user.id:
        return True

    # 检查用户是否具有项目模块的拥有人修改权限
    if user.has_permission('project', 'change_owner'):
        permission_level = user.get_permission_level('project')
        return _check_permission_level_scope(user, project.owner_id, permission_level)

    return False

def can_change_quotation_owner(user, quotation):
    """判断用户是否有权修改报价单的拥有人。"""
    if user.role == 'admin':
        return True

    # 检查用户是否有报价单模块的编辑权限
    if user.has_permission('quotation', 'edit'):
        permission_level = user.get_permission_level('quotation')
        return _check_permission_level_scope(user, quotation.owner_id, permission_level)

    return False

def can_delete_project(user, project):
    """
    检查用户是否有权限删除指定的项目
    
    参数:
        user: 用户对象
        project: 项目对象
    
    返回:
        bool: 是否有删除权限
    """
    # 管理员有全部删除权限
    if user.role == 'admin':
        return True
    
    # 注：财务总监、产品经理等角色的删除权限通过权限配置系统控制
    # 如需禁止某角色删除项目，在权限配置中设置 can_delete=False

    # 项目拥有者可以删除
    if project.owner_id == user.id:
        return True
    
    # 厂商负责人可以删除
    if hasattr(project, 'vendor_sales_manager_id') and project.vendor_sales_manager_id == user.id:
        return True
    
    return False

def can_delete_quotation(user, quotation):
    """
    检查用户是否有权限删除指定的报价单
    
    参数:
        user: 用户对象
        quotation: 报价单对象
    
    返回:
        bool: 是否有删除权限
    """
    # 管理员有全部删除权限
    if user.role == 'admin':
        return True
    
    # 检查用户是否有报价单模块的删除权限
    if not user.has_permission('quotation', 'delete'):
        return False
    
    # 获取用户在报价单模块的权限级别
    permission_level = user.get_permission_level('quotation')
    
    if permission_level == 'system':
        # 系统级权限：可以删除所有报价单
        return True
    elif permission_level == 'company' and user.company_name:
        # 企业级权限：可以删除企业下所有报价单
        owner = User.query.get(quotation.owner_id)
        return owner and owner.company_name == user.company_name
    elif permission_level == 'department' and user.department:
        # 部门级权限：可以删除部门下所有报价单
        owner = User.query.get(quotation.owner_id)
        return (owner and owner.department == user.department and 
                owner.company_name == user.company_name)
    else:
        # 个人级权限：只能删除自己的报价单或作为厂商负责人的报价单
        if quotation.owner_id == user.id:
            return True
        
        # 厂商负责人可以删除项目相关的报价单
        if (hasattr(quotation, 'project') and quotation.project and 
            hasattr(quotation.project, 'vendor_sales_manager_id') and 
            quotation.project.vendor_sales_manager_id == user.id):
            return True
        
        return False

def can_start_approval(model_obj, user):
    """
    检查用户是否有权限发起审批流程
    
    参数:
        model_obj: 数据对象（项目或报价单）
        user: 用户对象
    
    返回:
        bool: 是否有发起审批权限
    """
    # 管理员有全部权限
    if user.role == 'admin':
        return True
    
    model_name = model_obj.__class__.__name__
    
    # 项目审批权限检查
    if model_name == 'Project':
        # 1. 项目拥有者可以发起审批
        if model_obj.owner_id == user.id:
            return True
        # 2. 项目的厂商销售负责人可以发起审批
        if hasattr(model_obj, 'vendor_sales_manager_id') and model_obj.vendor_sales_manager_id == user.id:
            return True
        return False
    
    # 报价单审批权限检查
    elif model_name == 'Quotation':
        # 1. 报价单拥有者可以发起审批
        if model_obj.owner_id == user.id:
            return True
        # 2. 报价单关联项目的厂商销售负责人可以发起审批
        if (hasattr(model_obj, 'project') and model_obj.project and 
            hasattr(model_obj.project, 'vendor_sales_manager_id') and 
            model_obj.project.vendor_sales_manager_id == user.id):
            return True
        return False
    
    # 其他类型的对象，默认只有拥有者可以发起审批
    return model_obj.owner_id == user.id

def can_view_in_approval_context(user, object_type, object_id):
    """
    检查用户是否可以在审批上下文中查看业务对象详情
    
    审批人在审批过程中有权查看审批对象的业务详情，即使他们平时没有查看权限
    
    参数:
        user: 用户对象
        object_type: 业务对象类型 ('project', 'quotation', 'customer', 'purchase_order')
        object_id: 业务对象ID
    
    返回:
        bool: 是否有权限查看
    """
    if not user or not user.is_authenticated:
        return False
    
    # 管理员有全部权限
    if user.role == 'admin':
        return True
    
    # 首先检查是否是当前审批人
    from app.models.approval import ApprovalInstance, ApprovalStep, ApprovalStatus
    from app.models.pricing_order import PricingOrder, PricingOrderApprovalRecord
    
    # 检查通用审批系统
    approval_instance = ApprovalInstance.query.filter_by(
        object_type=object_type,
        object_id=object_id,
        status=ApprovalStatus.PENDING
    ).first()
    
    if approval_instance:
        # 🔥 修复：current_step 存储的是 step_order，使用 get_current_step_info() 获取步骤信息
        current_step = approval_instance.get_current_step_info()

        if current_step:
            # 使用动态审批人确定函数
            from app.helpers.approval_helpers import get_step_actual_approver
            actual_approver = get_step_actual_approver(current_step, approval_instance)
            if actual_approver and actual_approver.id == user.id:
                return True
    
    # 检查批价单审批系统（特殊处理）
    if object_type == 'pricing_order':
        pricing_order = PricingOrder.query.get(object_id)
        if pricing_order and pricing_order.status == 'pending':
            current_approval_record = PricingOrderApprovalRecord.query.filter_by(
                pricing_order_id=pricing_order.id,
                step_order=pricing_order.current_approval_step,
                approver_id=user.id
            ).first()
            if current_approval_record:
                return True
    
    # 检查订单审批系统
    if object_type == 'purchase_order':
        from app.models.inventory import PurchaseOrder
        from app.helpers.approval_helpers import get_step_actual_approver
        import logging
        debug_logger = logging.getLogger(__name__)

        purchase_order = PurchaseOrder.query.get(object_id)
        debug_logger.info(f"[审批权限调试] purchase_order={purchase_order}, object_id={object_id}")

        if purchase_order:
            # 查询订单的审批实例
            order_approval_instance = ApprovalInstance.query.filter_by(
                object_type='purchase_order',
                object_id=purchase_order.id,
                status=ApprovalStatus.PENDING
            ).first()
            debug_logger.info(f"[审批权限调试] approval_instance={order_approval_instance}")

            if order_approval_instance:
                debug_logger.info(f"[审批权限调试] current_step={order_approval_instance.current_step}, template_snapshot类型={type(order_approval_instance.template_snapshot)}")

                # 先查询 ApprovalStep 获取 step_order
                current_approval_step = ApprovalStep.query.filter_by(
                    id=order_approval_instance.current_step
                ).first()
                current_step_order = current_approval_step.step_order if current_approval_step else None
                debug_logger.info(f"[审批权限调试] ApprovalStep id={order_approval_instance.current_step} -> step_order={current_step_order}")

                # 使用模板快照获取当前步骤信息
                current_step_info = None
                if order_approval_instance.template_snapshot:
                    import json
                    try:
                        snapshot = json.loads(order_approval_instance.template_snapshot) if isinstance(order_approval_instance.template_snapshot, str) else order_approval_instance.template_snapshot
                        steps = snapshot.get('steps', [])
                        debug_logger.info(f"[审批权限调试] 快照步骤数={len(steps)}, current_step_order={current_step_order}")
                        for i, step in enumerate(steps):
                            debug_logger.info(f"[审批权限调试] 步骤{i}: id={step.get('id')}, step_order={step.get('step_order')}, approver_type={step.get('approver_type')}, approver_role={step.get('approver_role')}, approver_user_id={step.get('approver_user_id')}")
                            # 使用 step_order 匹配而不是 id（因为 template_snapshot 中的 id 可能为 None）
                            if step.get('step_order') == current_step_order:
                                current_step_info = step
                                debug_logger.info(f"[审批权限调试] 找到当前步骤: {step}")
                                break
                    except Exception as e:
                        debug_logger.error(f"[审批权限调试] 解析快照失败: {e}")

                if current_step_info:
                    # 使用动态审批人获取函数
                    actual_approver = get_step_actual_approver(current_step_info, order_approval_instance)
                    debug_logger.info(f"[审批权限调试] actual_approver={actual_approver}, actual_approver.id={actual_approver.id if actual_approver else None}, user.id={user.id}")
                    if actual_approver and actual_approver.id == user.id:
                        debug_logger.info(f"[审批权限调试] 审批权限通过!")
                        return True
                    else:
                        debug_logger.info(f"[审批权限调试] 审批人不匹配: actual_approver.id={actual_approver.id if actual_approver else None} != user.id={user.id}")
                else:
                    debug_logger.info(f"[审批权限调试] 未找到当前步骤信息，回退检查")
                    # 回退：直接检查 ApprovalStep
                    current_step = ApprovalStep.query.filter_by(
                        id=order_approval_instance.current_step
                    ).first()
                    debug_logger.info(f"[审批权限调试] 回退检查 current_step={current_step}, approver_user_id={current_step.approver_user_id if current_step else None}")
                    if current_step and current_step.approver_user_id == user.id:
                        return True
    
    # 如果不是审批人，则检查常规权限
    # 这里可以调用现有的权限检查函数
    return False


def has_approval_view_permission(user, object_type, object_id):
    """
    检查用户是否有权限查看业务对象（包括审批上下文）
    
    这是一个综合权限检查函数，会先检查审批权限，再检查常规权限
    
    参数:
        user: 用户对象
        object_type: 业务对象类型
        object_id: 业务对象ID
    
    返回:
        bool: 是否有权限查看
    """
    # 首先检查审批上下文权限
    if can_view_in_approval_context(user, object_type, object_id):
        return True
    
    # 然后检查常规权限
    if object_type == 'project':
        project = Project.query.get(object_id)
        if project:
            return can_view_project(user, project)
    
    elif object_type == 'quotation':
        from app.models.quotation import Quotation
        quotation = Quotation.query.get(object_id)
        if quotation:
            # 这里需要实现报价单的权限检查逻辑
            # 可以参考现有的报价单权限检查
            return True  # 临时返回True，需要根据实际情况实现
    
    elif object_type == 'customer':
        from app.models.customer import Company
        company = Company.query.get(object_id)
        if company:
            return can_view_company(user, company)
    
    elif object_type == 'purchase_order':
        from app.models.inventory import PurchaseOrder
        order = PurchaseOrder.query.get(object_id)
        if order:
            # 这里需要实现订单的权限检查逻辑
            # 可以参考现有的订单权限检查
            return True  # 临时返回True，需要根据实际情况实现
    
    return False

def can_view_order(order, current_user):
    """
    检查是否可以查看订单
    基于统一权限系统：
    - admin：可以查看所有订单
    - 基于订单模块权限级别：system > company > department > personal
    - 数据归属关系中的订单
    - 当前审批人可以查看
    """
    # 管理员拥有所有权限
    if current_user.role == 'admin':
        return True
    
    # 检查用户是否有订单模块的查看权限
    if not current_user.has_permission('order', 'view'):
        return False
    
    # 获取用户在订单模块的权限级别
    permission_level = current_user.get_permission_level('order')
    
    if permission_level == 'system':
        # 系统级权限：可以查看所有订单
        return True
    elif permission_level == 'company' and current_user.company_name:
        # 企业级权限：可以查看企业下所有订单
        if hasattr(order, 'created_by_id'):
            creator = User.query.get(order.created_by_id)
            return creator and creator.company_name == current_user.company_name
    elif permission_level == 'department' and current_user.department:
        # 部门级权限：可以查看部门下所有订单
        if hasattr(order, 'created_by_id'):
            creator = User.query.get(order.created_by_id)
            return (creator and creator.department == current_user.department and 
                    creator.company_name == current_user.company_name)
    
    # 个人级权限：创建人可以查看
    if hasattr(order, 'created_by_id') and order.created_by_id == current_user.id:
        return True
    
    # 检查归属关系
    affiliations = Affiliation.query.filter_by(viewer_id=current_user.id).all()
    viewable_user_ids = [affiliation.owner_id for affiliation in affiliations]
    
    if hasattr(order, 'created_by_id') and order.created_by_id in viewable_user_ids:
        return True
    
    # 当前审批人可以查看
    return can_view_in_approval_context(current_user, 'purchase_order', order.id)


def can_export_order_pdf(order, current_user):
    """
    检查是否可以导出订单PDF
    基于统一权限系统：
    - admin：可以导出所有订单PDF
    - 需要有订单模块的查看权限，并且能查看该订单
    - 具体导出权限可以通过权限模块扩展定义
    """
    # 管理员拥有所有权限
    if current_user.role == 'admin':
        return True
    
    # 首先需要能查看该订单
    if not can_view_order(order, current_user):
        return False
    
    # 检查是否有订单模块的查看权限（导出作为查看权限的一部分）
    # 后续可以扩展专门的导出权限
    return current_user.has_permission('order', 'view')