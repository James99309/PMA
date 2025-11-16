"""
通用阶段统计组件
提供标准化的阶段分布统计功能，支持不同业务场景
"""

from flask import request, jsonify
from sqlalchemy import func, and_
from app import db
from app.utils.stage_configs import get_stage_config, get_stage_label, get_stage_color
import logging

logger = logging.getLogger(__name__)

class StageAnalyticsComponent:
    """通用阶段统计组件类"""
    
    def __init__(self, stage_config_name, data_source_config, permission_config=None):
        """
        初始化阶段统计组件
        
        Args:
            stage_config_name: 阶段配置名称（如'project', 'order'）
            data_source_config: 数据源配置
            permission_config: 权限配置
        """
        self.stage_config_name = stage_config_name
        self.stage_config = get_stage_config(stage_config_name)
        self.data_source_config = data_source_config
        self.permission_config = permission_config or {}
        
        if not self.stage_config:
            raise ValueError(f"未找到阶段配置: {stage_config_name}")
    
    def build_base_query(self, current_user):
        """构建基础查询 - 使用与原始查询相同的结构"""
        # 为了兼容现有的产品分析查询结构，直接构建具体的查询
        # 这样可以避免复杂的动态JOIN解析问题
        
        from app.models.quotation import Quotation, QuotationDetail
        from app.models.project import Project
        from app.models.user import User
        
        # 构建与原始查询相同的SELECT子句
        query = db.session.query(
            Project.current_stage,
            func.sum(QuotationDetail.quantity).label('total_quantity'),
            func.sum(QuotationDetail.total_price).label('total_amount'),
            func.count(QuotationDetail.id).label('record_count')
        ).join(
            Quotation, QuotationDetail.quotation_id == Quotation.id
        ).join(
            Project, Quotation.project_id == Project.id
        ).join(
            User, Quotation.owner_id == User.id
        )
        
        # 应用权限过滤
        if self.permission_config and 'filter_function' in self.permission_config:
            filter_func = self.permission_config['filter_function']
            if callable(filter_func):
                query = filter_func(query, current_user, 
                                  quotation_alias=Quotation, 
                                  project_alias=Project)
        
        return query
    
    def apply_filters(self, query, filters=None):
        """应用业务筛选条件 - 使用与原始查询相同的筛选逻辑"""
        if not filters:
            return query
        
        from app.models.quotation import QuotationDetail
        from app.models.product import Product
        
        # 应用产品类别筛选
        if 'category' in filters and filters['category']:
            category = filters['category']
            # 使用子查询获取指定类别的产品，避免因Product表重复记录导致的重复统计
            from app.models.product_code import ProductCategory

            category_obj = ProductCategory.query.filter_by(name=category).first()
            if category_obj:
                category_products = db.session.query(
                    Product.product_name,
                    Product.model
                ).filter(
                    Product.category_id == category_obj.id
                ).distinct().subquery()

                query = query.filter(
                    and_(
                        QuotationDetail.product_name == category_products.c.product_name,
                        QuotationDetail.product_model == category_products.c.model
                    )
                )
        
        # 应用产品名称筛选
        if 'product_name' in filters and filters['product_name'] and filters['product_name'].strip():
            query = query.filter(QuotationDetail.product_name == filters['product_name'])
        
        # 应用产品型号筛选
        if 'product_model' in filters and filters['product_model'] and filters['product_model'].strip():
            query = query.filter(QuotationDetail.product_model == filters['product_model'])
        
        return query
    
    def get_statistics(self, current_user, filters=None):
        """获取阶段统计数据"""
        try:
            # 构建基础查询
            query = self.build_base_query(current_user)
            
            # 应用筛选条件
            query = self.apply_filters(query, filters)
            
            # 按阶段分组 - 使用Project.current_stage
            from app.models.project import Project
            results = query.group_by(Project.current_stage).all()
            
            # 构建结果数据
            stage_dict = {}
            
            for result in results:
                stage = result.current_stage or 'unset'
                stage_data = {
                    'stage': stage,
                    'name': get_stage_label(stage, self.stage_config_name),
                    'color_quantity': get_stage_color(stage, 'quantity', self.stage_config_name),
                    'color_amount': get_stage_color(stage, 'amount', self.stage_config_name)
                }
                
                # 添加聚合数据（匹配原始查询的字段名）
                stage_data['quantity'] = int(result.total_quantity) if result.total_quantity else 0
                stage_data['amount'] = float(result.total_amount) if result.total_amount else 0
                stage_data['count'] = int(result.record_count) if result.record_count else 0
                
                stage_dict[stage] = stage_data
            
            # 按配置顺序排序
            stage_data_list = []
            for stage in self.stage_config['stage_order']:
                if stage in stage_dict:
                    stage_item = stage_dict[stage]
                    stage_item['order'] = self.stage_config['stage_order'].index(stage)
                    stage_data_list.append(stage_item)
            
            return {
                'success': True,
                'data': stage_data_list,
                'colors': self.stage_config['stage_colors'],
                'stage_order': self.stage_config['stage_order'],
                'config_name': self.stage_config_name
            }
            
        except Exception as e:
            logger.error(f"获取阶段统计数据失败: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': f'获取阶段统计数据失败: {str(e)}'
            }
    
    def create_api_endpoint(self, blueprint, route_path, permission_decorator=None):
        """为组件创建API端点"""
        def endpoint_function():
            from flask_login import current_user
            
            # 获取筛选参数
            filters = {}
            filter_fields = self.data_source_config.get('filter_fields', {})
            for field_name in filter_fields.keys():
                value = request.args.get(field_name)
                if value and value.strip():
                    filters[field_name] = value.strip()
            
            # 获取统计数据
            result = self.get_statistics(current_user, filters)
            return jsonify(result)
        
        # 设置端点名称
        endpoint_name = f'{route_path.replace("/", "_").strip("_")}_api'
        
        # 应用装饰器
        if permission_decorator:
            endpoint_function = permission_decorator(endpoint_function)
        
        # 注册路由
        blueprint.add_url_rule(
            route_path,
            endpoint_name,
            endpoint_function,
            methods=['GET']
        )