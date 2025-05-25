"""
搜索辅助工具模块
提供通用的模糊查询功能，支持权限控制和安全防护
"""

import logging
from typing import List, Dict, Any, Optional, Union
from sqlalchemy import or_, and_, text, select
from sqlalchemy.orm import Query
from flask_login import current_user
from app import db
from app.utils.access_control import get_viewable_data

logger = logging.getLogger(__name__)

def fuzzy_search_field(
    model_class,
    search_fields: Union[str, List[str]],
    query_term: str,
    user=None,
    limit: int = 10,
    return_fields: Optional[List[str]] = None,
    additional_filters: Optional[List] = None,
    order_by: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    通用模糊查询函数
    
    参数:
        model_class: 数据模型类
        search_fields: 要搜索的字段名或字段名列表
        query_term: 搜索关键词
        user: 用户对象，用于权限控制（默认使用current_user）
        limit: 返回结果数量限制
        return_fields: 要返回的字段列表（默认返回id和搜索字段）
        additional_filters: 额外的过滤条件
        order_by: 排序字段
    
    返回:
        包含搜索结果的字典列表
    """
    try:
        # 参数验证
        if not model_class or not search_fields or not query_term:
            logger.warning("模糊查询参数不完整")
            return []
        
        # 清理和验证搜索词，防止SQL注入
        query_term = str(query_term).strip()
        if len(query_term) < 1:
            return []
        
        # 限制搜索词长度，防止过长查询
        if len(query_term) > 100:
            query_term = query_term[:100]
        
        # 转换为列表格式
        if isinstance(search_fields, str):
            search_fields = [search_fields]
        
        # 验证字段名，防止SQL注入
        valid_fields = []
        for field_name in search_fields:
            if hasattr(model_class, field_name):
                valid_fields.append(field_name)
            else:
                logger.warning(f"模型 {model_class.__name__} 不存在字段 {field_name}")
        
        if not valid_fields:
            logger.error(f"没有有效的搜索字段")
            return []
        
        # 使用权限控制获取基础查询
        user = user or current_user
        if not user:
            logger.warning("未提供用户信息，无法进行权限控制")
            return []
        
        # 获取用户可访问的数据查询
        query = get_viewable_data(model_class, user, additional_filters or [])
        
        # 构建模糊搜索条件
        search_conditions = []
        search_pattern = f"%{query_term}%"
        
        for field_name in valid_fields:
            field = getattr(model_class, field_name)
            # 使用ilike进行不区分大小写的模糊匹配
            search_conditions.append(field.ilike(search_pattern))
        
        # 应用搜索条件（OR关系）
        if search_conditions:
            query = query.filter(or_(*search_conditions))
        
        # 应用排序
        if order_by and hasattr(model_class, order_by):
            order_field = getattr(model_class, order_by)
            query = query.order_by(order_field)
        else:
            # 默认按ID排序
            if hasattr(model_class, 'id'):
                query = query.order_by(model_class.id)
        
        # 限制结果数量
        query = query.limit(min(limit, 50))  # 最多返回50条记录
        
        # 执行查询
        results = query.all()
        
        # 构建返回字段列表
        if not return_fields:
            return_fields = ['id'] + valid_fields
        
        # 验证返回字段
        valid_return_fields = []
        for field_name in return_fields:
            if hasattr(model_class, field_name):
                valid_return_fields.append(field_name)
        
        # 构建结果
        result_list = []
        for item in results:
            result_dict = {}
            for field_name in valid_return_fields:
                try:
                    value = getattr(item, field_name)
                    # 处理特殊类型
                    if value is None:
                        result_dict[field_name] = None
                    elif hasattr(value, 'isoformat'):  # datetime对象
                        result_dict[field_name] = value.isoformat()
                    else:
                        result_dict[field_name] = str(value)
                except Exception as e:
                    logger.warning(f"获取字段 {field_name} 值时出错: {str(e)}")
                    result_dict[field_name] = None
            
            result_list.append(result_dict)
        
        logger.debug(f"模糊查询 {model_class.__name__} 返回 {len(result_list)} 条结果")
        return result_list
        
    except Exception as e:
        logger.error(f"模糊查询时出错: {str(e)}")
        return []

def search_projects_by_name(query_term: str, user=None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    按项目名称模糊搜索项目
    
    参数:
        query_term: 搜索关键词
        user: 用户对象
        limit: 返回结果数量限制
    
    返回:
        项目列表
    """
    from app.models.project import Project
    from app.models.user import User
    
    try:
        # 使用基础搜索功能
        results = fuzzy_search_field(
            model_class=Project,
            search_fields=['project_name', 'authorization_code'],
            query_term=query_term,
            user=user,
            limit=limit,
            return_fields=['id', 'project_name', 'authorization_code', 'project_type', 'current_stage', 'owner_id'],
            order_by='project_name'
        )
        
        # 增强结果，添加拥有者信息和中文标签
        enhanced_results = []
        for result in results:
            try:
                # 获取拥有者信息
                owner_name = ''
                if result.get('owner_id'):
                    owner = User.query.get(result['owner_id'])
                    if owner:
                        # 优先使用真实姓名，如果没有则使用用户名
                        owner_name = owner.real_name or owner.username
                
                # 添加中文标签
                from app.utils.dictionary_helpers import project_type_label, project_stage_label
                
                enhanced_result = {
                    'id': result['id'],
                    'project_name': result['project_name'],
                    'authorization_code': result.get('authorization_code', ''),
                    'project_type': result.get('project_type', ''),
                    'project_type_display': project_type_label(result.get('project_type', '')),
                    'current_stage': result.get('current_stage', ''),
                    'current_stage_display': project_stage_label(result.get('current_stage', '')),
                    'owner_id': result.get('owner_id'),
                    'owner_name': owner_name
                }
                
                enhanced_results.append(enhanced_result)
                
            except Exception as e:
                logger.error(f"处理项目搜索结果时出错: {str(e)}")
                # 如果处理失败，至少返回基本信息
                enhanced_results.append({
                    'id': result['id'],
                    'project_name': result['project_name'],
                    'authorization_code': result.get('authorization_code', ''),
                    'project_type': result.get('project_type', ''),
                    'project_type_display': result.get('project_type', ''),
                    'current_stage': result.get('current_stage', ''),
                    'current_stage_display': result.get('current_stage', ''),
                    'owner_id': result.get('owner_id'),
                    'owner_name': ''
                })
        
        return enhanced_results
        
    except Exception as e:
        logger.error(f"项目搜索失败: {str(e)}")
        return []

def search_projects_without_quotations(query_term: str, user=None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    按项目名称模糊搜索没有报价单的项目（用于创建报价单）
    
    参数:
        query_term: 搜索关键词
        user: 用户对象
        limit: 返回结果数量限制
    
    返回:
        没有报价单的项目列表
    """
    from app.models.project import Project
    from app.models.quotation import Quotation
    from app.models.user import User
    from app.utils.access_control import get_viewable_data
    from sqlalchemy import and_, or_
    
    try:
        # 获取用户可查看的项目
        projects_query = get_viewable_data(Project, user)
        
        # 添加搜索条件
        if query_term:
            search_condition = or_(
                Project.project_name.ilike(f'%{query_term}%'),
                Project.authorization_code.ilike(f'%{query_term}%')
            )
            projects_query = projects_query.filter(search_condition)
        
        # 过滤掉已有报价单的项目
        # 使用子查询找出已有报价单的项目ID
        subquery = select(Quotation.project_id).distinct()
        projects_query = projects_query.filter(~Project.id.in_(subquery))
        
        # 限制结果数量并排序
        projects = projects_query.order_by(Project.project_name).limit(limit).all()
        
        # 构建返回结果
        results = []
        for project in projects:
            try:
                # 获取拥有者信息
                owner_name = ''
                if project.owner_id:
                    owner = User.query.get(project.owner_id)
                    if owner:
                        # 优先使用真实姓名，如果没有则使用用户名
                        owner_name = owner.real_name or owner.username
                
                # 添加中文标签
                from app.utils.dictionary_helpers import project_type_label, project_stage_label
                
                result = {
                    'id': project.id,
                    'project_name': project.project_name,
                    'authorization_code': project.authorization_code or '',
                    'project_type': project.project_type or '',
                    'project_type_display': project_type_label(project.project_type or ''),
                    'current_stage': project.current_stage or '',
                    'current_stage_display': project_stage_label(project.current_stage or ''),
                    'owner_id': project.owner_id,
                    'owner_name': owner_name
                }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"处理项目搜索结果时出错: {str(e)}")
                # 如果处理失败，至少返回基本信息
                results.append({
                    'id': project.id,
                    'project_name': project.project_name,
                    'authorization_code': project.authorization_code or '',
                    'project_type': project.project_type or '',
                    'project_type_display': project.project_type or '',
                    'current_stage': project.current_stage or '',
                    'current_stage_display': project.current_stage or '',
                    'owner_id': project.owner_id,
                    'owner_name': ''
                })
        
        return results
        
    except Exception as e:
        logger.error(f"搜索无报价单项目失败: {str(e)}")
        return []

def search_companies_by_name(query_term: str, user=None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    按公司名称模糊搜索公司
    
    参数:
        query_term: 搜索关键词
        user: 用户对象
        limit: 返回结果数量限制
    
    返回:
        公司列表
    """
    from app.models.customer import Company
    
    # 添加额外过滤条件：排除已删除的公司
    additional_filters = []
    if hasattr(Company, 'is_deleted'):
        additional_filters.append(Company.is_deleted == False)
    
    return fuzzy_search_field(
        model_class=Company,
        search_fields=['company_name'],
        query_term=query_term,
        user=user,
        limit=limit,
        return_fields=['id', 'company_name', 'company_type'],
        additional_filters=additional_filters,
        order_by='company_name'
    )

def search_contacts_by_name(query_term: str, user=None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    按联系人姓名模糊搜索联系人
    
    参数:
        query_term: 搜索关键词
        user: 用户对象
        limit: 返回结果数量限制
    
    返回:
        联系人列表
    """
    from app.models.customer import Contact
    
    return fuzzy_search_field(
        model_class=Contact,
        search_fields=['contact_name', 'phone', 'email'],
        query_term=query_term,
        user=user,
        limit=limit,
        return_fields=['id', 'contact_name', 'phone', 'email', 'company_id'],
        order_by='contact_name'
    )

def search_products_by_name(query_term: str, user=None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    按产品名称模糊搜索产品
    
    参数:
        query_term: 搜索关键词
        user: 用户对象
        limit: 返回结果数量限制
    
    返回:
        产品列表
    """
    from app.models.product import Product
    
    # 添加额外过滤条件：排除停产产品
    additional_filters = []
    if hasattr(Product, 'status'):
        additional_filters.append(Product.status != '停产')
    
    return fuzzy_search_field(
        model_class=Product,
        search_fields=['product_name', 'product_mn', 'model'],
        query_term=query_term,
        user=user,
        limit=limit,
        return_fields=['id', 'product_name', 'product_mn', 'model', 'brand', 'retail_price'],
        additional_filters=additional_filters,
        order_by='product_name'
    ) 