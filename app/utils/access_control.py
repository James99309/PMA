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
from sqlalchemy import or_, func, desc, text, cast
from sqlalchemy.dialects.postgresql import JSONB

logger = logging.getLogger(__name__)

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
        return model_class.query.filter(*special_filters)
    
    # 营销总监特殊处理：可以查看销售重点和渠道跟进项目
    if user.role and user.role.strip() == 'sales_director' and model_class.__name__ == 'Project':
        # 获取自己的项目
        own_projects = model_class.query.filter(model_class.owner_id == user.id)
        
        # 获取销售重点和渠道跟进项目
        special_projects = model_class.query.filter(
            model_class.project_type.in_(['sales_focus', 'channel_follow', '销售重点', '渠道跟进'])
        )
        
        # 获取自己作为销售负责人的项目
        sales_manager_projects = model_class.query.filter(
            model_class.vendor_sales_manager_id == user.id
        )
        
        # 合并查询结果
        combined_query = own_projects.union(special_projects).union(sales_manager_projects)
        return combined_query.filter(*special_filters)
    
    # 渠道经理特殊处理：可以查看渠道跟进项目
    if user.role and user.role.strip() == 'channel_manager' and model_class.__name__ == 'Project':
        # 获取自己的项目
        own_projects = model_class.query.filter(model_class.owner_id == user.id)
        
        # 获取渠道跟进项目
        channel_projects = model_class.query.filter(
            model_class.project_type.in_(['channel_follow', '渠道跟进'])
        )
        
        # 获取自己作为销售负责人的项目
        sales_manager_projects = model_class.query.filter(
            model_class.vendor_sales_manager_id == user.id
        )
        
        # 合并查询结果
        combined_query = own_projects.union(channel_projects).union(sales_manager_projects)
        return combined_query.filter(*special_filters)
    
    # User 模型特殊处理 - User 没有 owner_id 字段
    if model_class.__name__ == 'User':
        # 管理员已经在前面处理
        # 部门经理可以查看本部门用户
        if hasattr(user, 'is_department_manager') and user.is_department_manager and user.department:
            return model_class.query.filter(model_class.department == user.department, *special_filters)
        # 销售总监可以查看所有销售
        elif user.role == 'sales_director':
            return model_class.query.filter(model_class.role == 'sales', *special_filters)
        # 其他用户只能查看自己
        else:
            return model_class.query.filter(model_class.id == user.id, *special_filters)
    
    # 产品数据不受限制
    if model_class.__name__ == 'Product':
        return model_class.query.filter(*special_filters)
    
    # 订单数据访问控制
    if model_class.__name__ == 'PurchaseOrder':
        # 统一处理角色字符串，去除空格
        user_role = user.role.strip() if user.role else ''
        
        # 营销总监、渠道经理、商务助理、财务总监可以查看所有订单
        if user_role in ['sales_director', 'channel_manager', 'business_admin', 'finance_director']:
            return model_class.query.filter(*special_filters if special_filters else [])
        
        # 产品经理、解决方案经理可以查看所有订单（只读权限）
        if user_role in ['product_manager', 'product', 'solution_manager', 'solution']:
            return model_class.query.filter(*special_filters if special_filters else [])
        
        # 默认订单权限逻辑：自己创建的订单 + 归属关系授权的订单
        viewable_user_ids = [user.id]
        
        # 获取通过归属关系可以查看的数据
        affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
        for affiliation in affiliations:
            viewable_user_ids.append(affiliation.owner_id)
        
        return model_class.query.filter(
            model_class.created_by_id.in_(viewable_user_ids),
            *special_filters
        )
    
    # 处理特殊角色权限 - Project模型 - 基于四级权限管理系统
    if model_class.__name__ == 'Project':
        # 检查用户是否有项目模块的查看权限
        if not user.has_permission('project', 'view'):
            # 如果没有项目查看权限，返回空查询
            return model_class.query.filter(False)
        
        # 获取用户在项目模块的权限级别
        permission_level = user.get_permission_level('project')
        
        if permission_level == 'system':
            # 系统级权限：可以查看所有项目
            return model_class.query.filter(*special_filters)
        elif permission_level == 'company' and user.company_name:
            # 企业级权限：可以查看企业下所有项目
            from app.models.user import User
            company_user_ids = [u.id for u in User.query.filter_by(company_name=user.company_name).all()]
            return model_class.query.filter(
                db.or_(
                    model_class.owner_id.in_(company_user_ids),
                    model_class.vendor_sales_manager_id == user.id
                ),
                *special_filters
            )
        elif permission_level == 'department' and user.department and user.company_name:
            # 部门级权限：可以查看部门下所有项目
            from app.models.user import User
            dept_user_ids = [u.id for u in User.query.filter(
                User.department == user.department,
                User.company_name == user.company_name
            ).all()]
            return model_class.query.filter(
                db.or_(
                    model_class.owner_id.in_(dept_user_ids),
                    model_class.vendor_sales_manager_id == user.id
                ),
                *special_filters
            )
        else:
            # 个人级权限：基础权限控制
            viewable_user_ids = [user.id]
            
            # 添加归属关系授权的用户（数据归属权限）
            affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
            for affiliation in affiliations:
                viewable_user_ids.append(affiliation.owner_id)
            
            # 部门负责人权限：可以查看本部门所有用户的数据
            if getattr(user, 'is_department_manager', False) and user.department:
                dept_users = User.query.filter_by(department=user.department).all()
                viewable_user_ids.extend([u.id for u in dept_users])
            
            # 去重
            viewable_user_ids = list(set(viewable_user_ids))
            
            # 基于权限管理系统的数据访问控制
            return model_class.query.filter(
                db.or_(
                    model_class.owner_id.in_(viewable_user_ids),
                    model_class.vendor_sales_manager_id == user.id  # 作为厂商销售负责人的项目
                ),
                *special_filters
            )

    # 报价单特殊权限
    if model_class.__name__ == 'Quotation':
        # 检查用户是否有报价单模块的查看权限
        if not user.has_permission('quotation', 'view'):
            # 如果没有报价单查看权限，返回空查询
            return model_class.query.filter(False)
        
        # 统一处理角色字符串，去除空格
        user_role = user.role.strip() if user.role else ''
        
        # 财务总监可以查看所有报价单（只读权限）
        if user_role in ['finance_director', 'finace_director']:
            return model_class.query.filter(*special_filters if special_filters else [])
        
        # 基于四级权限系统的数据访问控制
        permission_level = user.get_permission_level('quotation')
        
        if permission_level == 'system':
            # 系统级权限：可以查看所有报价单
            return model_class.query.filter(*special_filters if special_filters else [])
        elif permission_level == 'company' and user.company_name:
            # 企业级权限：可以查看企业下所有报价单
            from app.models.user import User
            company_user_ids = [u.id for u in User.query.filter_by(company_name=user.company_name).all()]
            
            # 获取这些用户的项目ID
            from app.models.project import Project
            company_project_ids = [p.id for p in Project.query.filter(Project.owner_id.in_(company_user_ids)).all()]
            
            # 返回企业内所有项目的报价单
            return model_class.query.filter(
                model_class.project_id.in_(company_project_ids),
                *special_filters if special_filters else []
            )
        elif permission_level == 'department' and user.department and user.company_name:
            # 部门级权限：可以查看部门下所有报价单
            from app.models.user import User
            dept_user_ids = [u.id for u in User.query.filter(
                User.department == user.department,
                User.company_name == user.company_name
            ).all()]
            
            # 获取这些用户的项目ID
            from app.models.project import Project
            dept_project_ids = [p.id for p in Project.query.filter(Project.owner_id.in_(dept_user_ids)).all()]
            
            # 返回部门内所有项目的报价单
            return model_class.query.filter(
                model_class.project_id.in_(dept_project_ids),
                *special_filters if special_filters else []
            )
        
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
        from app.models.project import Project
        sales_manager_projects = Project.query.filter(
            Project.vendor_sales_manager_id == user.id
        ).with_entities(Project.id).all()
        if sales_manager_projects:
            sales_manager_project_ids = [p.id for p in sales_manager_projects]
            sales_manager_quotations = model_class.query.filter(model_class.project_id.in_(sales_manager_project_ids)).with_entities(model_class.id).all()
            accessible_quotation_ids.update([q.id for q in sales_manager_quotations])
        
        # 4. 角色特殊处理
        # 渠道经理特殊处理：可以查看所有渠道跟进项目的报价单
        if user_role == 'channel_manager':
            channel_follow_projects = Project.query.filter_by(project_type='channel_follow').with_entities(Project.id).all()
            if channel_follow_projects:
                channel_follow_project_ids = [p.id for p in channel_follow_projects]
                channel_quotations = model_class.query.filter(model_class.project_id.in_(channel_follow_project_ids)).with_entities(model_class.id).all()
                accessible_quotation_ids.update([q.id for q in channel_quotations])
        
        # 营销总监特殊处理：可以查看销售重点和渠道跟进项目的报价单
        elif user_role == 'sales_director':
            marketing_projects = Project.query.filter(
                Project.project_type.in_(['sales_focus', 'channel_follow', '销售重点', '渠道跟进'])
            ).with_entities(Project.id).all()
            if marketing_projects:
                marketing_project_ids = [p.id for p in marketing_projects]
                marketing_quotations = model_class.query.filter(model_class.project_id.in_(marketing_project_ids)).with_entities(model_class.id).all()
                accessible_quotation_ids.update([q.id for q in marketing_quotations])
        
        # 服务经理特殊处理
        elif user_role in ['service', 'service_manager']:
            business_opportunity_projects = Project.query.filter_by(project_type='业务机会').with_entities(Project.id).all()
            if business_opportunity_projects:
                business_opportunity_project_ids = [p.id for p in business_opportunity_projects]
                business_quotations = model_class.query.filter(model_class.project_id.in_(business_opportunity_project_ids)).with_entities(model_class.id).all()
                accessible_quotation_ids.update([q.id for q in business_quotations])
        
        # 商务助理特殊处理：可以查看同部门用户和归属关系授权用户的项目报价单
        elif user_role == 'business_admin':
            viewable_user_ids = [user.id]  # 自己的项目
            
            # 1. 添加同部门用户
            if user.department and user.company_name:
                dept_users = User.query.filter(
                    User.department == user.department,
                    User.company_name == user.company_name
                ).all()
                viewable_user_ids.extend([u.id for u in dept_users])
            
            # 2. 添加归属关系授权的用户
            affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
            for affiliation in affiliations:
                viewable_user_ids.append(affiliation.owner_id)
            
            # 去重
            viewable_user_ids = list(set(viewable_user_ids))
            
            # 获取这些用户拥有的或担任厂商销售的项目
            authorized_projects = Project.query.filter(
                db.or_(
                    Project.owner_id.in_(viewable_user_ids),
                    Project.vendor_sales_manager_id.in_(viewable_user_ids)
                )
            ).with_entities(Project.id).all()
            
            if authorized_projects:
                authorized_project_ids = [p.id for p in authorized_projects]
                business_admin_quotations = model_class.query.filter(model_class.project_id.in_(authorized_project_ids)).with_entities(model_class.id).all()
                accessible_quotation_ids.update([q.id for q in business_admin_quotations])
        
        # 返回基于ID列表的查询
        if accessible_quotation_ids:
            return model_class.query.filter(model_class.id.in_(accessible_quotation_ids)).filter(*special_filters if special_filters else [])
        else:
            # 如果没有可访问的报价单，返回空查询
            return model_class.query.filter(model_class.id == -1)
    
    # 客户特殊权限处理 - 基于权限管理系统
    if model_class.__name__ in ['Company', 'Contact']:
        # 检查用户是否有客户模块的查看权限
        if not user.has_permission('customer', 'view'):
            # 如果没有客户查看权限，返回空查询
            return model_class.query.filter(False)
        
        # 基于四级权限系统的数据访问控制
        permission_level = user.get_permission_level('customer')
        
        if permission_level == 'system':
            # 系统级权限：可以查看所有客户数据
            return model_class.query.filter(*special_filters if special_filters else [])
        elif permission_level == 'company' and user.company_name:
            # 企业级权限：可以查看企业下所有客户数据
            from app.models.user import User
            company_user_ids = [u.id for u in User.query.filter_by(company_name=user.company_name).all()]
            return model_class.query.filter(
                model_class.owner_id.in_(company_user_ids),
                *special_filters if special_filters else []
            )
        elif permission_level == 'department' and user.department and user.company_name:
            # 部门级权限：可以查看部门下所有客户数据
            from app.models.user import User
            dept_user_ids = [u.id for u in User.query.filter(
                User.department == user.department,
                User.company_name == user.company_name
            ).all()]
            return model_class.query.filter(
                model_class.owner_id.in_(dept_user_ids),
                *special_filters if special_filters else []
            )
        
        # 个人级权限或其他情况：基础权限控制
        viewable_user_ids = [user.id]
        
        # 添加归属关系授权的用户（数据归属权限）
        affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
        for affiliation in affiliations:
            viewable_user_ids.append(affiliation.owner_id)
        
        # 部门负责人权限：可以查看本部门所有用户的数据
        if getattr(user, 'is_department_manager', False) and user.department:
            dept_users = User.query.filter_by(department=user.department).all()
            viewable_user_ids.extend([u.id for u in dept_users])
        
        # 商务助理特殊权限：具备部门所有账户的查看权限
        user_role = user.role.strip() if user.role else ''
        if user_role == 'business_admin' and user.department and user.company_name:
            dept_users = User.query.filter(
                User.department == user.department,
                User.company_name == user.company_name
            ).all()
            viewable_user_ids.extend([u.id for u in dept_users])
        
        # 去重
        viewable_user_ids = list(set(viewable_user_ids))
        
        # 基于权限管理系统的数据访问控制
        return model_class.query.filter(
            model_class.owner_id.in_(viewable_user_ids),
            *special_filters
        )
    
    # 行动记录的特殊处理
    if model_class.__name__ == 'Action':
        # 用户可以查看与自己有访问权限的企业相关的行动记录
        viewable_company_ids = [company.id for company in get_viewable_data(Company, user).all()]
        return model_class.query.filter(
            model_class.company_id.in_(viewable_company_ids),
            *special_filters
        )
    
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
    
    # 财务总监：只能查看，不能编辑任何项目和报价单
    if user_role in ['finance_director', 'finace_director']:
        if model_name in ['Project', 'Quotation']:
            return False
        # 其他数据按默认规则
        return model_obj.owner_id == user.id
    
    # 产品经理：基于权限系统进行编辑权限控制
    if user_role in ['product_manager', 'product']:
        if model_name == 'Project':
            # 检查是否有项目编辑权限
            return user.has_permission('project', 'edit') and model_obj.owner_id == user.id
        elif model_name == 'Quotation':
            # 检查是否有报价单编辑权限，如果有权限则可以编辑企业内所有报价单
            if user.has_permission('quotation', 'edit') and user.company_name:
                # 检查报价单是否属于同企业
                from app.models.user import User
                from app.models.project import Project
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
            # 检查是否有报价单编辑权限，如果有权限则可以编辑企业内所有报价单
            if user.has_permission('quotation', 'edit') and user.company_name:
                # 检查报价单是否属于同企业
                from app.models.user import User
                from app.models.project import Project
                if hasattr(model_obj, 'project') and model_obj.project:
                    project_owner = User.query.get(model_obj.project.owner_id)
                    return project_owner and project_owner.company_name == user.company_name
                return False
            return False
        # 其他数据按默认规则
        return model_obj.owner_id == user.id
    
    # 项目特殊处理：厂商负责人享有与拥有人同等权限
    if model_name == 'Project':
        # 项目拥有人可以编辑
        if model_obj.owner_id == user.id:
            return True
        # 厂商负责人可以编辑
        if hasattr(model_obj, 'vendor_sales_manager_id') and model_obj.vendor_sales_manager_id == user.id:
            return True
        return False
    
    # 报价单特殊处理：项目的厂商负责人可以编辑相关报价单
    if model_name == 'Quotation':
        # 报价单拥有人可以编辑
        if model_obj.owner_id == user.id:
            return True
        # 项目的厂商负责人可以编辑相关报价单
        if (hasattr(model_obj, 'project') and model_obj.project and 
            hasattr(model_obj.project, 'vendor_sales_manager_id') and 
            model_obj.project.vendor_sales_manager_id == user.id):
            return True
        # 解决方案经理可以编辑所有报价单
        if user_role in ['solution_manager', 'solution']:
            return True
        return False
    
    # 营销总监只能编辑自己的数据
    if user_role == 'sales_director':
        return model_obj.owner_id == user.id
    
    # 渠道经理只能编辑自己的数据
    if user_role == 'channel_manager':
        return model_obj.owner_id == user.id
    
    # 销售角色只能编辑自己的数据
    if user_role in ['sales', 'sales_manager']:
        return model_obj.owner_id == user.id
    
    # 其他角色的编辑权限逻辑保持不变
    return model_obj.owner_id == user.id

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
    logger.debug(f"[权限检查] 用户 {user.username} (ID: {user.id}, 角色: {user.role}) 尝试访问企业 '{company.company_name}' (ID: {company.id}, 拥有者: {company.owner_id})")
    
    if user.role == 'admin':
        logger.debug(f"[权限检查] 管理员权限 - 允许访问")
        return True
    if user.id == company.owner_id:
        logger.debug(f"[权限检查] 企业拥有者权限 - 允许访问")
        return True
    
    # 商务助理：可以查看同部门用户和归属关系授权用户的客户
    user_role = user.role.strip() if user.role else ''
    if user_role == 'business_admin':
        # 检查是否是同部门用户的客户
        if user.department and user.company_name:
            company_owner = User.query.get(company.owner_id)
            if (company_owner and 
                company_owner.department == user.department and 
                company_owner.company_name == user.company_name):
                return True
        
        # 检查是否是归属关系授权的用户的客户
        affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
        if company.owner_id in [aff.owner_id for aff in affiliations]:
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
    # 判断是否创建了该公司下的联系人
    contact_count = Contact.query.filter_by(company_id=company.id, owner_id=user.id).count()
    if contact_count > 0:
        logger.debug(f"[权限检查] 联系人创建权限 - 允许访问")
        return True
    
    # 移除厂商负责人可以查看项目相关客户的逻辑
    # 这个权限过于宽泛，会导致用户能够查看其他账户拥有的企业详情
    # 即使用户是项目的厂商销售负责人，也不应该允许查看其他账户的企业信息
    
    # 厂商用户特殊权限：可以查看所有经销商类型的公司详情
    if user.is_vendor_user() and company.company_type in ['经销商', 'dealer']:
        logger.debug(f"[权限检查] 厂商用户经销商权限 - 允许访问")
        return True
    
    logger.debug(f"[权限检查] 所有权限检查失败 - 拒绝访问")
    return False

def can_edit_company_info(user, company):
    """
    判断是否可以编辑客户基本信息
    """
    if user.role == 'admin':
        return True
    if user.id == company.owner_id:
        return True
    
    # 商务助理：可以编辑同部门用户和归属关系授权用户的客户信息
    user_role = user.role.strip() if user.role else ''
    if user_role == 'business_admin':
        # 检查是否是同部门用户的客户
        if user.department and user.company_name:
            company_owner = User.query.get(company.owner_id)
            if (company_owner and 
                company_owner.department == user.department and 
                company_owner.company_name == user.company_name):
                return True
        
        # 检查是否是归属关系授权的用户的客户
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
    - 商务助理：可以编辑同部门用户和归属关系授权用户的客户归属
    """
    if user.role == 'admin':
        return True
    if user.id == company.owner_id:
        return True
    
    from app.models.user import Affiliation
    affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
    if company.owner_id in [aff.owner_id for aff in affiliations]:
        return True
    
    # 商务助理：可以编辑同部门用户和归属关系授权用户的客户归属
    user_role = user.role.strip() if user.role else ''
    if user_role == 'business_admin':
        # 检查是否是同部门用户的客户
        if user.department and user.company_name:
            company_owner = User.query.get(company.owner_id)
            if (company_owner and 
                company_owner.department == user.department and 
                company_owner.company_name == user.company_name):
                return True
        
        # 归属关系授权的用户的客户（已在上面检查）
        # 这里不需要重复检查
    
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
    
    # 商务助理：可以查看同部门用户和归属关系授权用户的联系人
    user_role = user.role.strip() if user.role else ''
    if user_role == 'business_admin':
        # 检查是否是同部门用户的联系人
        if user.department and user.company_name:
            contact_owner = User.query.get(contact.owner_id)
            if (contact_owner and 
                contact_owner.department == user.department and 
                contact_owner.company_name == user.company_name):
                return True
        
        # 检查是否是归属关系授权的用户的联系人
        affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
        if contact.owner_id in [aff.owner_id for aff in affiliations]:
            return True
    
    # 判断是否有指定的联系人归属
    if hasattr(contact, 'assigned_to') and contact.assigned_to == user.id:
        return True
    # 判断联系人是否覆盖了公司的共享设置并禁用共享
    if hasattr(contact, 'override_share') and contact.override_share:
        if hasattr(contact, 'shared_disabled') and contact.shared_disabled:
            return False
    # 检查公司共享设置
    company = contact.company
    if hasattr(company, 'shared_with_users') and company.shared_with_users:
        if user.id in company.shared_with_users:
            if hasattr(company, 'share_contacts') and company.share_contacts:
                return True
    # 判断是否通过归属关系获得权限
    affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
    if contact.owner_id in [affiliation.owner_id for affiliation in affiliations]:
        return True
    
    # 厂商用户特殊权限：可以查看经销商公司的联系人详情
    if user.is_vendor_user() and company and company.company_type in ['经销商', 'dealer']:
        return True
    
    return False

def can_edit_contact(user, contact):
    """
    检查用户是否有权限编辑指定的联系人
    """
    if user.role == 'admin':
        return True
    if user.id == contact.owner_id:
        return True
    
    # 商务助理：可以编辑同部门用户和归属关系授权用户的联系人
    user_role = user.role.strip() if user.role else ''
    if user_role == 'business_admin':
        # 检查是否是同部门用户的联系人
        if user.department and user.company_name:
            contact_owner = User.query.get(contact.owner_id)
            if (contact_owner and 
                contact_owner.department == user.department and 
                contact_owner.company_name == user.company_name):
                return True
        
        # 检查是否是归属关系授权的用户的联系人
        affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
        if contact.owner_id in [aff.owner_id for aff in affiliations]:
            return True
    
    # 其他情况使用查看权限逻辑
    return can_view_contact(user, contact)

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
    4. 财务总监、解决方案经理、产品经理可以查看所有项目
    5. 销售经理特殊权限：归属关系中的非业务机会项目
    6. 共享（如有 shared_with_users 字段，暂未支持）
    """
    if user.role == 'admin':
        return True
    if user.id == project.owner_id:
        return True
    
    # 厂商负责人可以查看项目
    if hasattr(project, 'vendor_sales_manager_id') and project.vendor_sales_manager_id == user.id:
        return True
    
    # 统一处理角色字符串，去除空格
    user_role = user.role.strip() if user.role else ''
    
    # 财务总监、解决方案经理、产品经理可以查看所有项目
    if user_role in ['finance_director', 'finace_director', 'solution_manager', 'solution', 'product_manager', 'product']:
        return True
    
    # 商务助理：可以查看销售重点、渠道跟进类型的项目
    if user_role == 'business_admin':
        # 检查是否为允许的项目类型
        allowed_project_types = ['销售重点', 'sales_key', 'sales_focus', '渠道跟进', 'channel_follow']
        if project.project_type in allowed_project_types:
            return True
    
    from app.models.user import Affiliation
    affiliation_owner_ids = [aff.owner_id for aff in Affiliation.query.filter_by(viewer_id=user.id).all()]
    
    # 归属关系权限检查
    if project.owner_id in affiliation_owner_ids:
        # 销售经理角色：只能查看归属关系中的非业务机会项目
        if user_role in ['sales', 'sales_manager']:
            return project.project_type != '业务机会'
        # 其他角色可以查看所有归属关系项目
        return True
    
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
    """
    判断用户是否有权修改客户的拥有人。
    - 管理员可修改所有客户
    - 部门负责人（is_department_manager为True或角色为sales_director）可修改本部门成员的客户
    """
    if user.role == 'admin':
        return True
    # 支持多种部门负责人角色
    if getattr(user, 'is_department_manager', False) or user.role == 'sales_director':
        from app.models.user import User
        owner = User.query.get(company.owner_id)
        if not owner:
            return False
        # 只允许操作本部门成员
        return hasattr(owner, 'department') and hasattr(user, 'department') and owner.department == user.department
    return False

def can_change_project_owner(user, project):
    """
    判断用户是否有权修改项目的拥有人。
    - 管理员可修改所有项目
    - 项目拥有人可以修改
    - 厂商负责人可以修改
    - 部门负责人（is_department_manager为True或角色为sales_director）可修改本部门成员的项目
    """
    if user.role == 'admin':
        return True
    
    # 项目拥有人可以修改
    if project.owner_id == user.id:
        return True
    
    # 厂商负责人可以修改
    if hasattr(project, 'vendor_sales_manager_id') and project.vendor_sales_manager_id == user.id:
        return True
    
    if getattr(user, 'is_department_manager', False) or user.role == 'sales_director':
        from app.models.user import User
        owner = User.query.get(project.owner_id)
        if not owner:
            return False
        return hasattr(owner, 'department') and hasattr(user, 'department') and owner.department == user.department
    return False

def can_change_quotation_owner(user, quotation):
    """
    判断用户是否有权修改报价单的拥有人。
    - 管理员可修改所有报价单
    - 部门负责人（is_department_manager为True或角色为sales_director）可修改本部门成员的报价单
    """
    if user.role == 'admin':
        return True
    if getattr(user, 'is_department_manager', False) or user.role == 'sales_director':
        from app.models.user import User
        owner = User.query.get(quotation.owner_id)
        if not owner:
            return False
        return hasattr(owner, 'department') and hasattr(user, 'department') and owner.department == user.department
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
    
    # 统一处理角色字符串，去除空格
    user_role = user.role.strip() if user.role else ''
    
    # 财务总监、产品经理、解决方案经理：不能删除任何项目
    if user_role in ['finance_director', 'finace_director', 'product_manager', 'product', 'solution_manager', 'solution']:
        return False
    
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
    
    # 统一处理角色字符串，去除空格
    user_role = user.role.strip() if user.role else ''
    
    # 财务总监：不能删除任何报价单
    if user_role in ['finance_director', 'finace_director']:
        return False
    
    # 产品经理、解决方案经理：基于权限系统进行删除权限控制
    if user_role in ['product_manager', 'product', 'solution_manager', 'solution']:
        # 检查是否有报价单删除权限
        return user.has_permission('quotation', 'delete') and quotation.owner_id == user.id
    
    # 报价单拥有者可以删除
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
        # 获取当前步骤
        current_step = ApprovalStep.query.filter_by(
            process_id=approval_instance.process_id,
            step_order=approval_instance.current_step
        ).first()
        
        if current_step and current_step.approver_user_id == user.id:
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
        purchase_order = PurchaseOrder.query.get(object_id)
        if purchase_order:
            # 查询订单的审批实例
            order_approval_instance = ApprovalInstance.query.filter_by(
                object_type='purchase_order',
                object_id=purchase_order.id,
                status=ApprovalStatus.PENDING
            ).first()
            
            if order_approval_instance:
                current_step = ApprovalStep.query.filter_by(
                    process_id=order_approval_instance.process_id,
                    step_order=order_approval_instance.current_step
                ).first()
                
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
        from app.models.project import Project
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
    根据新的权限规则：
    - 营销总监：可以看到所有订单
    - 渠道经理：可以创建和看到所有订单
    - 商务助理：可以创建和看到所有订单
    - 财务总监：可以看到所有订单
    - 其他用户：只能查看自己创建的订单和归属关系中的订单
    """
    # 管理员拥有所有权限
    if current_user.role == 'admin':
        return True
    
    user_role = current_user.role.strip() if current_user.role else ''
    
    # 营销总监、渠道经理、商务助理、财务总监可以查看所有订单
    if user_role in ['sales_director', 'channel_manager', 'business_admin', 'finance_director']:
        return True
    
    # 创建人可以查看
    if hasattr(order, 'created_by_id') and order.created_by_id == current_user.id:
        return True
    
    # 检查归属关系
    from app.models.user import Affiliation
    affiliations = Affiliation.query.filter_by(viewer_id=current_user.id).all()
    viewable_user_ids = [affiliation.owner_id for affiliation in affiliations]
    
    if hasattr(order, 'created_by_id') and order.created_by_id in viewable_user_ids:
        return True
    
    # 当前审批人可以查看
    return can_view_in_approval_context(current_user, 'purchase_order', order.id)


def can_export_order_pdf(order, current_user):
    """
    检查是否可以导出订单PDF
    根据新的权限规则：
    - 商务助理：可以创建和看到所有订单，并且能打印
    - 财务总监：可以看到所有订单和打印
    - 其他角色不能打印订单PDF
    """
    # 管理员拥有所有权限
    if current_user.role == 'admin':
        return True
        
    user_role = current_user.role.strip() if current_user.role else ''
    
    # 商务助理和财务总监可以打印所有订单PDF
    if user_role in ['business_admin', 'finance_director']:
        # 需要先检查是否有查看权限
        return can_view_order(order, current_user)
    
    return False