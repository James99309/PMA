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
from app.models.user import Affiliation
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
    3. 当前用户的 ID 被包含在 shared_with_users（如有该字段）
    目前项目暂未支持共享字段，仅用 owner_id 与归属链判断
    """
    if special_filters is None:
        special_filters = []
    logger.debug(f"用户 {user.username} (ID: {user.id}, 角色: {user.role}) 查询 {model_class.__name__} 数据")
    # 管理员可以查看所有数据
    if user.role == 'admin':
        return model_class.query.filter(*special_filters)
    # 针对 Project 权限逻辑
    if model_class.__name__ == 'Project':
        # 1. 直接归属
        owned_query = model_class.query.filter(model_class.owner_id == user.id)
        # 2. 归属链（Affiliation）
        affiliation_owner_ids = [aff.owner_id for aff in Affiliation.query.filter_by(viewer_id=user.id).all()]
        subordinate_query = model_class.query.filter(model_class.owner_id.in_(affiliation_owner_ids))
        # 合并去重
        return owned_query.union(subordinate_query).filter(*special_filters)
    # 其他模型按原逻辑
    if model_class.__name__ == 'Product':
        return model_class.query.filter(*special_filters)
    
    # 处理特殊角色权限
    if model_class.__name__ == 'Project':
        # 产品经理可以查看所有项目
        if user.role in ['product_manager', 'product']:
            return model_class.query.filter(*special_filters if special_filters else [])
        # 渠道经理：可以查看所有渠道跟进项目 + 自己的项目
        if user.role == 'channel_manager':
            return model_class.query.filter(
                db.or_(
                    model_class.owner_id == user.id,
                    model_class.project_type == 'channel_follow'
                ),
                *special_filters
            )
        
        # 营销总监：可以查看所有渠道跟进和销售重点项目 + 自己的项目
        if user.role == 'sales_director':
            return model_class.query.filter(
                db.or_(
                    model_class.owner_id == user.id,
                    model_class.project_type.in_(['channel_follow', 'sales_focus'])
                ),
                *special_filters
            )
            
        # 服务经理：可以查看所有业务机会项目 + 自己的项目
        if user.role in ['service', 'service_manager']:
            return model_class.query.filter(
                db.or_(
                    model_class.owner_id == user.id,
                    model_class.project_type == '业务机会'
                ),
                *special_filters
            )
            
        # 销售角色：查看自己的项目 + 通过归属关系可见的项目，且不能看到业务机会类型的项目
        if user.role == 'sales':
            # 获取通过归属关系可以查看的用户ID列表
            viewable_user_ids = [user.id]
            affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
            for affiliation in affiliations:
                viewable_user_ids.append(affiliation.owner_id)
                
            # 允许查看自己创建的所有项目(包括业务机会) + 归属关系中的非业务机会项目
            return model_class.query.filter(
                db.or_(
                    model_class.owner_id == user.id,  # 自己的所有项目都可见
                    db.and_(
                        model_class.owner_id.in_(viewable_user_ids),
                        model_class.project_type != '业务机会'  # 归属关系中只能看非业务机会项目
                    )
                ),
                *special_filters
            )
    
    # 报价单特殊权限
    if model_class.__name__ == 'Quotation':
        # 管理员特殊角色直接返回全部
        if user.role in ['product_manager', 'solution_manager', 'product', 'solution']:
            return model_class.query.filter(*special_filters if special_filters else [])
        
        # 1. 直接归属（自己创建的报价单）
        owned_query = model_class.query.filter(model_class.owner_id == user.id)
        
        # 2. 归属链（Affiliation - 下级创建的报价单，参考Project模块逻辑）
        affiliation_owner_ids = [aff.owner_id for aff in Affiliation.query.filter_by(viewer_id=user.id).all()]
        subordinate_query = model_class.query.filter(model_class.owner_id.in_(affiliation_owner_ids))
        
        # 3. 角色特殊处理
        special_query = None
        # 服务经理特殊处理
        if user.role in ['service', 'service_manager']:
            # 获取所有业务机会项目的ID
            business_opportunity_projects = Project.query.filter_by(project_type='业务机会').all()
            business_opportunity_project_ids = [p.id for p in business_opportunity_projects]
            # 业务机会项目相关的报价单
            special_query = model_class.query.filter(model_class.project_id.in_(business_opportunity_project_ids))
        
        # 合并查询条件
        if special_query:
            return owned_query.union(subordinate_query).union(special_query).filter(*special_filters)
        else:
            return owned_query.union(subordinate_query).filter(*special_filters)
    
    # 客户特殊权限处理
    if model_class.__name__ in ['Company', 'Contact']:
        # 产品经理可以查看所有客户信息
        if user.role in ['product_manager', 'product']:
            return model_class.query.filter(*special_filters if special_filters else [])
        # 渠道经理不能看到其他账户的客户信息
        if user.role == 'channel_manager':
            return model_class.query.filter(
                model_class.owner_id == user.id,
                *special_filters
            )
        # 服务经理只能查看自己的客户信息和授权的客户信息
        if user.role in ['service', 'service_manager']:
            # 获取通过归属关系可以查看的数据
            viewable_user_ids = [user.id]
            affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
            for affiliation in affiliations:
                viewable_user_ids.append(affiliation.owner_id)
            return model_class.query.filter(
                model_class.owner_id.in_(viewable_user_ids),
                *special_filters
            )
        # 销售角色：查看自己的客户 + 通过归属关系可见的客户 + 被共享的客户
        if user.role == 'sales' or model_class.__name__ == 'Company':
            # 获取通过归属关系可以查看的用户ID列表
            viewable_user_ids = [user.id]
            affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
            for affiliation in affiliations:
                viewable_user_ids.append(affiliation.owner_id)
            
            # Company模型需要特殊处理共享
            if model_class.__name__ == 'Company':
                from app.models.customer import Contact
                # 获取用户创建的所有联系人所属的公司ID列表
                user_contact_company_ids = db.session.query(Contact.company_id).filter(
                    Contact.owner_id == user.id
                ).distinct().all()
                user_contact_company_ids = [company_id for (company_id,) in user_contact_company_ids]
                
                # 查找出所有共享给当前用户的公司ID (单独查询)
                shared_company_ids = []
                for company in Company.query.all():
                    if hasattr(company, 'shared_with_users') and company.shared_with_users:
                        # 确保是列表类型
                        if isinstance(company.shared_with_users, list) and user.id in company.shared_with_users:
                            shared_company_ids.append(company.id)
                
                # 合并三个条件
                return model_class.query.filter(
                    or_(
                        model_class.owner_id.in_(viewable_user_ids),
                        model_class.id.in_(user_contact_company_ids),
                        model_class.id.in_(shared_company_ids)
                    ),
                    *special_filters
                )
            else:  # Contact模型使用常规查询
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
    
    # 销售角色只能编辑自己的数据
    if user.role == 'sales':
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
    if user.role == 'admin':
        return True
    if user.id == company.owner_id:
        return True
    # 判断是否通过共享获得权限
    if hasattr(company, 'shared_with_users') and company.shared_with_users:
        if user.id in company.shared_with_users:
            return True
    # 判断是否通过归属关系获得权限
    affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
    if company.owner_id in [affiliation.owner_id for affiliation in affiliations]:
        return True
    # 判断是否创建了该公司下的联系人
    contact_count = Contact.query.filter_by(company_id=company.id, owner_id=user.id).count()
    if contact_count > 0:
        return True
    return False

def can_edit_company_info(user, company):
    """
    判断是否可以编辑客户基本信息
    """
    if user.role == 'admin':
        return True
    if user.id == company.owner_id:
        return True
    return False

def can_edit_company_sharing(user, company):
    """
    判断是否可以编辑客户共享设置
    """
    if user.role == 'admin':
        return True
    if user.id == company.owner_id:
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
    return False

def can_edit_contact(user, contact):
    """
    检查用户是否有权限编辑指定的联系人
    """
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
    2. 归属链
    3. 共享（如有 shared_with_users 字段，暂未支持）
    """
    if user.role == 'admin':
        return True
    if user.id == project.owner_id:
        return True
    from app.models.user import Affiliation
    affiliation_owner_ids = [aff.owner_id for aff in Affiliation.query.filter_by(viewer_id=user.id).all()]
    if project.owner_id in affiliation_owner_ids:
        return True
    return False 

def register_context_processors(app):
    """
    注册权限辅助函数到应用上下文处理器
    这个函数应该在应用初始化时被调用
    """
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
            can_view_company=can_view_company
        )

def can_change_company_owner(user, company):
    """
    判断用户是否有权修改客户的拥有人。
    - 管理员可修改所有客户
    - 部门负责人（is_department_manager为True或角色为sales_director/department_manager）可修改本部门成员的客户
    """
    if user.role == 'admin':
        return True
    # 支持多种部门负责人角色
    if getattr(user, 'is_department_manager', False) or user.role in ['sales_director', 'department_manager']:
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
    - 部门负责人（is_department_manager为True或角色为sales_director/department_manager）可修改本部门成员的项目
    """
    if user.role == 'admin':
        return True
    if getattr(user, 'is_department_manager', False) or user.role in ['sales_director', 'department_manager']:
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
    - 部门负责人（is_department_manager为True或角色为sales_director/department_manager）可修改本部门成员的报价单
    """
    if user.role == 'admin':
        return True
    if getattr(user, 'is_department_manager', False) or user.role in ['sales_director', 'department_manager']:
        from app.models.user import User
        owner = User.query.get(quotation.owner_id)
        if not owner:
            return False
        return hasattr(owner, 'department') and hasattr(user, 'department') and owner.department == user.department
    return False