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

logger = logging.getLogger(__name__)

def get_viewable_data(model_class, user, special_filters=None):
    """
    通用数据访问控制函数，根据用户权限返回可查看的数据集
    
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
    logger.debug(f"用户 {user.username} (ID: {user.id}, 角色: {user.role}) 查询 {model_class.__name__} 数据")
    
    # 产品数据不受限制
    if model_class.__name__ == 'Product':
        return model_class.query.filter(*special_filters)
    
    # 管理员可以查看所有数据
    if user.role == 'admin':
        return model_class.query.filter(*special_filters)
    
    # 处理特殊角色权限
    if model_class.__name__ == 'Project':
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
        if user.role == 'marketing_director':
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
        # 产品经理和解决方案经理可以查看所有报价单
        if user.role in ['product_manager', 'solution_manager']:
            return model_class.query.filter(*special_filters)
        # 服务经理可以查看自己的报价单以及与业务机会项目相关的报价单
        elif user.role in ['service', 'service_manager']:
            # 获取所有业务机会项目的ID
            business_opportunity_projects = Project.query.filter_by(project_type='业务机会').all()
            business_opportunity_project_ids = [p.id for p in business_opportunity_projects]
            
            # 返回自己的报价单和业务机会项目相关的报价单
            return model_class.query.filter(
                db.or_(
                    model_class.owner_id == user.id,
                    model_class.project_id.in_(business_opportunity_project_ids)
                ),
                *special_filters
            )
        # 销售角色：查看自己的报价单 + 通过归属关系可见的报价单
        elif user.role == 'sales':
            # 获取通过归属关系可以查看的用户ID列表
            viewable_user_ids = [user.id]
            affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
            for affiliation in affiliations:
                viewable_user_ids.append(affiliation.owner_id)
                
            return model_class.query.filter(
                model_class.owner_id.in_(viewable_user_ids),
                *special_filters
            )
    
    # 客户特殊权限处理
    if model_class.__name__ in ['Company', 'Contact']:
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
        # 销售角色：查看自己的客户 + 通过归属关系可见的客户
        if user.role == 'sales':
            # 获取通过归属关系可以查看的用户ID列表
            viewable_user_ids = [user.id]
            affiliations = Affiliation.query.filter_by(viewer_id=user.id).all()
            for affiliation in affiliations:
                viewable_user_ids.append(affiliation.owner_id)
                
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