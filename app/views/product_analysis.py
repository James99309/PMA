from flask import Blueprint, render_template, render_template_string, request, jsonify, url_for
from types import SimpleNamespace
from flask_login import login_required, current_user
from flask_babel import gettext as _
from app.decorators import permission_required
from app.permissions import has_permission
from app.models.quotation import Quotation, QuotationDetail
from app.models.project import Project
from app.models.product import Product
from app.models.user import User, Affiliation
from app.utils.access_control import get_viewable_data
from app.components.stage_analytics import StageAnalyticsComponent
from app.utils.chinese_mapping_manager import mapping_manager
from sqlalchemy import func, and_, or_, extract
from datetime import datetime, timedelta
from app import db
import logging
from app.utils.dictionary_helpers import project_stage_label

logger = logging.getLogger(__name__)

product_analysis = Blueprint('product_analysis', __name__)

def _get_latest_quotation_subquery():
    """
    创建最新报价单子查询

    返回每个项目的最新报价单ID（基于报价单创建时间）
    这确保了当一个项目有多个报价单时，只统计最新的那一个

    返回: 包含 project_id 和 latest_quotation_id 的子查询
    """
    latest_quotation_subq = db.session.query(
        Quotation.project_id,
        func.max(Quotation.id).label('latest_quotation_id')
    ).group_by(Quotation.project_id).subquery()

    return latest_quotation_subq

def _calculate_product_analysis_stats(base_query, current_month=None):
    """
    模组化的产品分析统计计算函数
    
    参数:
    - base_query: 基础查询对象（已应用权限和筛选条件）
    - current_month: 本月开始时间（可选，用于计算本月新增）
    
    返回: 包含各项统计数据的字典
    """
    try:
        # 计算总体统计
        total_stats = base_query.with_entities(
            func.sum(QuotationDetail.total_price).label('total_amount'),
            func.sum(QuotationDetail.quantity).label('total_quantity'),
            func.count(QuotationDetail.id).label('record_count')
        ).first()
        
        total_amount = float(total_stats.total_amount) if total_stats.total_amount else 0
        total_quantity = int(total_stats.total_quantity) if total_stats.total_quantity else 0
        
        # 计算平均单价（每个单位的价格，不需要除以10000）
        avg_unit_price = (total_amount / total_quantity) if total_quantity > 0 else 0
        
        # 计算本月新增数据（如果提供了current_month）
        monthly_quantity = 0
        monthly_amount = 0
        if current_month:
            monthly_stats = base_query.filter(
                QuotationDetail.created_at >= current_month
            ).with_entities(
                func.sum(QuotationDetail.total_price).label('monthly_amount'),
                func.sum(QuotationDetail.quantity).label('monthly_quantity')
            ).first()
            
            monthly_quantity = int(monthly_stats.monthly_quantity) if monthly_stats.monthly_quantity else 0
            monthly_amount = float(monthly_stats.monthly_amount) if monthly_stats.monthly_amount else 0
        
        return {
            'total_amount': total_amount,           # 总金额（原始金额，元）
            'total_quantity': total_quantity,       # 总数量
            'avg_unit_price': avg_unit_price,       # 平均单价（元/个）
            'monthly_quantity': monthly_quantity,   # 本月新增数量
            'monthly_amount': monthly_amount,       # 本月新增金额（原始金额，元）
            'record_count': int(total_stats.record_count) if total_stats.record_count else 0
        }
        
    except Exception as e:
        logger.error(f"统计计算失败: {e}")
        return {
            'total_amount': 0,
            'total_quantity': 0,
            'avg_unit_price': 0,
            'monthly_quantity': 0,
            'monthly_amount': 0,
            'record_count': 0
        }

def apply_permission_based_filters(query, current_user, quotation_alias=Quotation, project_alias=Project):
    """
    基于四级权限系统应用数据过滤
    """
    # 如果没有用户，返回空查询
    if not current_user:
        return query.filter(False)
    
    # 检查是否是管理员或CEO（使用传入的用户对象）
    if (hasattr(current_user, 'role') and 
        current_user.role in ['admin', 'CEO'] and 
        hasattr(current_user, 'has_permission')):
        if current_user.has_permission('product', 'admin'):
            return query
    
    # 检查用户是否有报价单查看权限
    if not (hasattr(current_user, 'has_permission') and current_user.has_permission('quotation', 'view')):
        # 如果没有权限，返回空查询
        return query.filter(False)
    
    # 获取权限级别
    permission_level = current_user.get_permission_level('quotation')
    
    if permission_level == 'system':
        # 系统级权限：可以查看所有数据
        return query
    elif permission_level == 'company' and current_user.company_name:
        # 企业级权限：可以查看企业下所有数据
        company_user_ids = [u.id for u in User.query.filter_by(company_name=current_user.company_name).all()]
        return query.filter(project_alias.owner_id.in_(company_user_ids))
    elif permission_level == 'department' and current_user.department and current_user.company_name:
        # 部门级权限：可以查看部门下所有数据
        dept_user_ids = [u.id for u in User.query.filter(
            User.department == current_user.department,
            User.company_name == current_user.company_name
        ).all()]
        return query.filter(project_alias.owner_id.in_(dept_user_ids))
    else:
        # 个人级权限：应用传统的权限过滤逻辑
        permission_filters = []
        
        # 1. 自己创建的报价单
        permission_filters.append(quotation_alias.owner_id == current_user.id)
        
        # 2. 归属关系 - 使用子查询优化
        affiliation_subquery = db.session.query(Affiliation.owner_id).filter(
            Affiliation.viewer_id == current_user.id
        ).subquery()
        permission_filters.append(quotation_alias.owner_id.in_(affiliation_subquery))
        
        # 3. 销售负责人相关项目
        permission_filters.append(project_alias.vendor_sales_manager_id == current_user.id)
        
        # 4. 其他角色特殊权限
        user_role = current_user.role.strip() if current_user.role else ''
        if user_role == 'channel_manager':
            # 渠道经理：额外可以查看渠道跟进项目
            permission_filters.append(project_alias.project_type == 'channel_follow')
        elif user_role == 'sales_director':
            # 营销总监：额外可以查看销售重点和渠道跟进项目
            permission_filters.append(project_alias.project_type.in_(['sales_focus', 'sales_key', 'channel_follow']))
        elif user_role in ['service', 'service_manager']:
            # 服务经理：额外可以查看客户服务项目
            permission_filters.append(project_alias.project_type == 'business_opportunity')
        elif user_role == 'business_admin':
            # 商务助理：可以查看同部门用户和归属关系授权用户的项目
            viewable_user_ids = [current_user.id]  # 自己的项目
            
            # 1. 添加同部门用户
            if current_user.department and current_user.company_name:
                dept_users = User.query.filter(
                    User.department == current_user.department,
                    User.company_name == current_user.company_name
                ).all()
                viewable_user_ids.extend([u.id for u in dept_users])
            
            # 2. 添加归属关系授权的用户
            affiliations = Affiliation.query.filter_by(viewer_id=current_user.id).all()
            for affiliation in affiliations:
                viewable_user_ids.append(affiliation.owner_id)
            
            # 去重
            viewable_user_ids = list(set(viewable_user_ids))
            
            # 添加权限过滤条件
            permission_filters.append(
                db.or_(
                    project_alias.owner_id.in_(viewable_user_ids),
                    project_alias.vendor_sales_manager_id.in_(viewable_user_ids)
                )
            )
        
        # 应用权限过滤条件
        if permission_filters:
            return query.filter(or_(*permission_filters))
        else:
            # 如果没有任何权限，返回空查询
            return query.filter(False)

# 阶段配置现在统一由 stage_configs.py 管理

def get_stage_label(stage_key):
    """获取阶段中文标签"""
    return project_stage_label(stage_key, 'zh')

# 创建阶段统计组件实例
def create_stage_analytics_component():
    """创建产品分析阶段统计组件"""
    # 数据源配置
    data_source_config = {
        'primary_table': Project,
        'join_tables': [
            {
                'table': Quotation,
                'join_on': 'Quotation.project_id == Project.id'
            },
            {
                'table': QuotationDetail, 
                'join_on': 'QuotationDetail.quotation_id == Quotation.id'
            },
            {
                'table': User,
                'join_on': 'Quotation.owner_id == User.id'
            }
        ],
        'aggregate_fields': {
            'quantity': 'func.sum(QuotationDetail.quantity)',
            'amount': 'func.sum(QuotationDetail.total_price)'
        },
        'filter_fields': {
            'category': {
                'type': 'subquery',
                'main_table': QuotationDetail,
                'main_fields': ['product_name', 'product_model'],
                'subquery': {
                    'table': Product,
                    'fields': ['product_name', 'model'],
                    'condition': {'field': 'category'}
                }
            },
            'product_name': {
                'type': 'direct',
                'table': QuotationDetail,
                'field': 'product_name'
            },
            'product_model': {
                'type': 'direct', 
                'table': QuotationDetail,
                'field': 'product_model'
            }
        }
    }
    
    # 权限配置
    permission_config = {
        'filter_function': apply_permission_based_filters
    }
    
    return StageAnalyticsComponent(
        stage_config_name='project',
        data_source_config=data_source_config,
        permission_config=permission_config
    )

@product_analysis.route('/analysis')
@login_required
@permission_required('quotation', 'view')
def analysis():
    """产品分析主页面 - 只统计每个项目的最新报价单"""
    # 获取最新报价单子查询
    latest_quotation_subq = _get_latest_quotation_subquery()

    # 获取基础查询，应用权限过滤
    # 重要：只查询最新报价单的产品明细
    base_query = db.session.query(
        QuotationDetail.product_name,
        QuotationDetail.product_model,
        QuotationDetail.product_desc
    ).join(
        Quotation, QuotationDetail.quotation_id == Quotation.id
    ).join(
        latest_quotation_subq,
        and_(
            Quotation.project_id == latest_quotation_subq.c.project_id,
            Quotation.id == latest_quotation_subq.c.latest_quotation_id
        )
    ).join(
        Project, Quotation.project_id == Project.id
    ).join(
        User, Quotation.owner_id == User.id
    )

    # 应用权限过滤（与主查询保持一致）
    base_query = apply_permission_based_filters(base_query, current_user)
    
    # 从实际可访问的报价单明细中获取筛选选项
    # 通过连接Product表获取产品类别
    try:
        from app.models.product_code import ProductCategory

        # 方案2：只通过model字段关联（避免使用已迁移的product_name字段）
        categories_query = base_query.join(
            Product, QuotationDetail.product_model == Product.model
        ).join(
            ProductCategory, Product.category_id == ProductCategory.id
        ).with_entities(ProductCategory.name).distinct().order_by(ProductCategory.id)

        categories = categories_query.all()
        logger.info(f"✅ 从报价单明细中获取到 {len(categories)} 个产品类别")
    except Exception as e:
        logger.warning(f"⚠️ 连接Product表获取类别失败: {str(e)}, 使用空列表")
        db.session.rollback()  # 回滚失败的事务，避免影响后续查询
        categories = []
    
    # 获取实际在报价单中使用的产品名称
    product_names = base_query.with_entities(QuotationDetail.product_name).distinct().filter(
        QuotationDetail.product_name.isnot(None),
        QuotationDetail.product_name != '',  # 排除空字符串
        QuotationDetail.product_name != ' '   # 排除空格字符串
    ).order_by(QuotationDetail.product_name).all()
    
    # 获取实际在报价单中使用的产品型号
    product_models = base_query.with_entities(QuotationDetail.product_model).distinct().filter(
        QuotationDetail.product_model.isnot(None),
        QuotationDetail.product_model != '',  # 排除空字符串
        QuotationDetail.product_model != ' '   # 排除空格字符串
    ).order_by(QuotationDetail.product_model).all()
    
    # 记录调试信息
    logger.info(f"🔍 产品型号筛选选项: {[m[0] for m in product_models[:5]]}...")
    
    # 使用模组化函数计算初始统计数据
    from datetime import datetime
    current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # 创建基础查询用于统计计算
    # 重要：只统计最新报价单的产品明细
    base_stats_query = db.session.query(QuotationDetail).join(
        Quotation, QuotationDetail.quotation_id == Quotation.id
    ).join(
        latest_quotation_subq,
        and_(
            Quotation.project_id == latest_quotation_subq.c.project_id,
            Quotation.id == latest_quotation_subq.c.latest_quotation_id
        )
    ).join(
        Project, Quotation.project_id == Project.id
    ).join(
        User, Quotation.owner_id == User.id
    )

    # 应用权限过滤
    base_stats_query = apply_permission_based_filters(base_stats_query, current_user)
    
    # 使用模组化函数计算统计数据
    stats_data = _calculate_product_analysis_stats(base_stats_query, current_month)
    
    # 构建筛选配置
    filter_config = {
        'action_url': request.url,
        'form_id': 'productAnalysisFilterForm',
        'reset_url': request.path,
        'realtime_search': False,
        'auto_submit': True,
        'ajax_mode': True,
        'ajax_endpoint': url_for('product_analysis.products_list_ajax'),
        'ajax_target': 'productAnalysisTableBody',
        'ajax_columns': 13,
        'dynamic_reset_button': True,
        'adaptive_width': True,
        'adaptive_button_layout': True,
        'search_delay': 300,
        
        'search_field': {
            'name': 'search',
            'label': '搜索',
            'placeholder': '产品名称、型号、描述或MN号',
            'value': request.args.get('search', ''),
            'col_width': 3
        },
        
        'filter_fields': [
            {
                'name': 'category',
                'label': '产品类别',
                'all_option_text': '全部类别',
                'current_value': request.args.get('category', ''),
                'col_width': 3,
                'options': [{'value': c[0], 'label': c[0], 'translate': False} for c in categories if c[0] and c[0].strip()]
            },
            {
                'name': 'product_name',
                'label': '产品名称',
                'all_option_text': '全部产品',
                'current_value': request.args.get('product_name', ''),
                'col_width': 3,
                'options': [{'value': p[0], 'label': p[0], 'translate': False} for p in product_names if p[0] and p[0].strip()]
            },
            {
                'name': 'product_model',
                'label': '产品型号',
                'all_option_text': '全部型号',
                'current_value': request.args.get('product_model', ''),
                'col_width': 3,
                'options': [{'value': m[0], 'label': m[0], 'translate': False} for m in product_models if m[0] and m[0].strip()]
            }
        ],
        
        'search_button_text': '搜索',
        'reset_button_text': '重置'
    }
    
    # 构建统一的list_config配置
    list_config = {
        'module_name': 'product_analysis',
        'title': _('植入产品分析'),
        'ajax_mode': True,
        
        # 统计卡片配置（产品分析模块：手动转换为万元以兼容通用模组）
        'stats': {
            'cards': [
                {
                    'id': 'total_amount',
                    'title': _('总金额'),
                    'icon': 'fas fa-dollar-sign',
                    'value': 1,  # 数量固定为1，重点是金额
                    'amount': round(stats_data['total_amount'] / 10000, 2),  # 转换为万元
                    'unit': _('项'),
                    'amount_unit': _('万元'),  # 通用模组将自动处理语言感知切换
                    'color': 'primary',
                    'clickable': False,
                    'data_key': 'total_amount'
                },
                {
                    'id': 'total_quantity',
                    'title': _('产品数量'),
                    'icon': 'fas fa-boxes',
                    'value': stats_data['total_quantity'],
                    'unit': _('个'),
                    'color': 'success',
                    'clickable': False,
                    'data_key': 'total_quantity'
                },
                {
                    'id': 'monthly_increase',
                    'title': _('本月新增'),
                    'icon': 'fas fa-chart-line',
                    'value': stats_data['monthly_quantity'],  # 本月新增数量
                    'amount': round(stats_data['monthly_amount'] / 10000, 2),  # 转换为万元
                    'unit': _('个'),
                    'amount_unit': _('万元'),  # 通用模组将自动处理语言感知切换
                    'color': 'warning',
                    'clickable': False,
                    'data_key': 'monthly_increase'
                },
                {
                    'id': 'avg_unit_price',
                    'title': _('平均单价'),
                    'icon': 'fas fa-calculator',
                    'value': 1,  # 数量固定为1，重点是金额
                    'amount': round(stats_data['avg_unit_price'] / 10000, 4),  # 转换为万元，保留4位小数
                    'unit': _('项'),
                    'amount_unit': _('万元'),  # 通用模组将自动处理语言感知切换
                    'color': 'info',
                    'clickable': False,
                    'data_key': 'avg_unit_price'
                }
            ]
        },
        
        # 筛选配置
        'filter': filter_config,
        
        # 表格配置
        'table': {
            'ajax_target': 'productAnalysisTableBody',
            'title': _('产品明细列表'),
            'icon': 'fas fa-table',
            'fixed_height_scroll': True,   # 启用蓝色滚动条
            'enhanced_striping': True,     # 启用增强斑马纹
            'use_custom_rows': True,
            'custom_rows_template': 'product_analysis/product_analysis_rows_simple.html',
            'columns': [
                {'key': 'product_name', 'field': 'product_name', 'label': _(mapping_manager.get_field_display_name('product', 'product_name')), 'width': '150px', 'sort_type': 'string'},
                {'key': 'product_model', 'field': 'product_model', 'label': _(mapping_manager.get_field_display_name('product', 'product_model')), 'width': '200px', 'sort_type': 'string'},
                {'key': 'quantity', 'field': 'quantity', 'label': _(mapping_manager.get_field_display_name('common', 'quantity')), 'width': '80px', 'align': 'center', 'sort_type': 'number'},
                {'key': 'discount', 'field': 'discount', 'label': _(mapping_manager.get_field_display_name('common', 'discount')), 'width': '80px', 'align': 'center', 'sort_type': 'number'},
                {'key': 'unit_price', 'field': 'unit_price', 'label': _(mapping_manager.get_field_display_name('common', 'unit_price')), 'width': '100px', 'align': 'right', 'sort_type': 'number'},
                {'key': 'total_price', 'field': 'total_price', 'label': _(mapping_manager.get_field_display_name('common', 'total_price')), 'width': '100px', 'align': 'right', 'sort_type': 'number'},
                {'key': 'product_mn', 'field': 'product_mn', 'label': _('MN号'), 'width': '120px', 'sort_type': 'string'},
                {'key': 'owner_name', 'field': 'owner_name', 'label': _(mapping_manager.get_field_display_name('common', 'owner_id')), 'width': '100px', 'sort_type': 'string'},
                {'key': 'project_name', 'field': 'project_name', 'label': _(mapping_manager.get_field_display_name('project', 'project_name')), 'width': '150px', 'sort_type': 'string'},
                {'key': 'current_stage', 'field': 'current_stage', 'label': _(mapping_manager.get_field_display_name('project', 'current_stage')), 'width': '100px', 'align': 'center', 'sort_type': 'string'},
                {'key': 'quotation_number', 'field': 'quotation_number', 'label': _(mapping_manager.get_field_display_name('quotation', 'quotation_number')), 'width': '120px', 'sort_type': 'string'},
                {'key': 'updated_at', 'field': 'updated_at', 'label': _(mapping_manager.get_field_display_name('common', 'updated_at')), 'width': '140px', 'sort_type': 'date'},
                {'key': 'created_at', 'field': 'created_at', 'label': _(mapping_manager.get_field_display_name('common', 'created_at')), 'width': '140px', 'sort_type': 'date'}
            ]
        },
        
        # 无限滚动配置（使用标准格式）
        'infinite_scroll': {
            'enabled': True,
            'page_size': 50,
            'scroll_threshold': 100,
            'loading_text': _('正在加载更多产品数据...'),
            'no_more_text': _('已加载全部产品数据')
        },
        
        # 阶段统计组件配置
        'stage_analytics': {
            'container_id': 'stageAnalyticsContainer',
            'chart_id': 'stageAnalyticsChart',
            'api_endpoint': url_for('product_analysis.api_stage_statistics_api'),
            'title': '阶段分布统计',
            'icon': 'fas fa-chart-bar',
            'chart_type': 'bar',
            'switchable': True,
            'filter_integration': True,
            'height': '350px'
        }
    }
    
    return render_template('product_analysis/analysis.html',
                         list_config=list_config,
                         categories=[c[0] for c in categories],
                         product_names=[p[0] for p in product_names],
                         product_models=[m[0] for m in product_models])

@product_analysis.route('/api/filter_options')
@login_required
@permission_required('quotation', 'view')
def get_filter_options():
    """获取筛选选项的联动数据"""
    try:
        category = request.args.get('category')
        product_name = request.args.get('product_name')
        
        # 构建基础查询
        query = db.session.query(Product)

        # 获取产品类别选项（不受其他筛选条件影响）
        from app.models.product_code import ProductCategory
        categories = db.session.query(ProductCategory.name).order_by(
            ProductCategory.id
        ).all()

        # 根据已选择的条件进行筛选
        if category:
            # 通过ProductCategory关联过滤
            category_obj = ProductCategory.query.filter_by(name=category).first()
            if category_obj:
                query = query.filter(Product.category_id == category_obj.id)
        if product_name:
            query = query.filter(Product.product_name == product_name)
        
        # 获取产品名称选项
        product_names = query.with_entities(Product.product_name).distinct().filter(
            Product.product_name.isnot(None)
        ).order_by(Product.product_name).all()
        
        # 获取产品型号选项
        product_models = query.with_entities(Product.model).distinct().filter(
            Product.model.isnot(None)
        ).order_by(Product.model).all()
        
        return jsonify({
            'success': True,
            'categories': [c[0] for c in categories],
            'product_names': [p[0] for p in product_names],
            'product_models': [m[0] for m in product_models]
        })
        
    except Exception as e:
        logger.error(f"获取筛选选项失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@product_analysis.route('/api/analysis_data')
@login_required
@permission_required('quotation', 'view')
def get_analysis_data():
    """获取产品分析数据 - 性能优化版本，只统计每个项目的最新报价单"""
    try:
        # 获取筛选参数
        category = request.args.get('category')
        product_name = request.args.get('product_name')
        product_model = request.args.get('product_model')

        # 获取分页参数
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 50))  # 默认每页50条

        # 获取最新报价单子查询
        latest_quotation_subq = _get_latest_quotation_subquery()

        # 性能优化：直接在主查询中处理权限逻辑，避免先查询所有可见报价单
        # 构建基础查询 - 避免因Product表重复记录导致的重复统计
        # 重要：只查询最新报价单的产品明细
        query = db.session.query(
            QuotationDetail.id,
            QuotationDetail.product_name,
            QuotationDetail.product_model,
            QuotationDetail.product_desc,
            QuotationDetail.quantity,
            QuotationDetail.discount,
            QuotationDetail.unit_price,
            QuotationDetail.total_price,
            QuotationDetail.product_mn,
            User,  # 获取完整的User对象
            Project.id.label('project_id'),
            Project.project_name,
            Project.current_stage,
            Quotation.id.label('quotation_id'),
            Quotation.quotation_number,
            QuotationDetail.updated_at,
            QuotationDetail.created_at
        ).join(
            Quotation, QuotationDetail.quotation_id == Quotation.id
        ).join(
            latest_quotation_subq,
            and_(
                Quotation.project_id == latest_quotation_subq.c.project_id,
                Quotation.id == latest_quotation_subq.c.latest_quotation_id
            )
        ).join(
            Project, Quotation.project_id == Project.id
        ).join(
            User, Quotation.owner_id == User.id
        )
        
        # 应用基于权限系统的数据过滤
        query = apply_permission_based_filters(query, current_user)

        # 应用筛选条件
        if category:
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
        
        if product_name and product_name.strip():
            query = query.filter(QuotationDetail.product_name == product_name)
        
        if product_model and product_model.strip():
            query = query.filter(QuotationDetail.product_model == product_model)
        
        # 获取总数（用于分页）
        total_count = query.count()
        
        # 执行分页查询 - 默认按更新时间降序排序
        try:
            results = query.order_by(QuotationDetail.updated_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
        except Exception as e:
            logger.warning(f"使用updated_at排序失败: {str(e)}, 尝试使用id排序")
            try:
                # 回滚失败的事务
                db.session.rollback()
                results = query.order_by(QuotationDetail.id.desc()).offset((page - 1) * per_page).limit(per_page).all()
            except Exception as e2:
                logger.error(f"产品分析查询失败: {str(e2)}")
                # 回滚失败的事务
                db.session.rollback()
                results = []
        
        # 格式化数据
        data = []
        for row in results:
            item = {
                'id': row.id,
                'product_name': row.product_name,
                'product_model': row.product_model,
                'product_desc': row.product_desc,
                'quantity': row.quantity,
                'discount': f"{row.discount * 100:.1f}%" if row.discount else "100.0%",
                'unit_price': float(row.unit_price) if row.unit_price else 0,
                'total_price': float(row.total_price) if row.total_price else 0,
                'product_mn': row.product_mn,
                'owner_name': row.owner_name,
                'owner_real_name': row.owner_real_name,
                'company_name': row.company_name,
                'project_id': row.project_id,
                'project_name': row.project_name,
                'current_stage': row.current_stage,
                'quotation_id': row.quotation_id,
                'quotation_number': row.quotation_number,
                'updated_at': row.updated_at.strftime('%Y-%m-%d %H:%M') if row.updated_at else '',
                'created_at': row.created_at.strftime('%Y-%m-%d %H:%M') if row.created_at else ''
            }
            data.append(item)
        
        # 性能优化：为统计数据使用单独的聚合查询
        stats_query = query.with_entities(
            func.sum(QuotationDetail.total_price).label('total_amount'),
            func.sum(QuotationDetail.quantity).label('total_quantity'),
            func.count(QuotationDetail.id).label('record_count')
        )
        stats_result = stats_query.first()
        
        total_amount = float(stats_result.total_amount) if stats_result.total_amount else 0
        total_quantity = int(stats_result.total_quantity) if stats_result.total_quantity else 0
        
        # 计算平均单价（转换为万元）
        avg_unit_price = (total_amount / 10000 / total_quantity) if total_quantity > 0 else 0
        
        # 计算本月新增数量 - 使用单独的查询
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_query = query.filter(QuotationDetail.created_at >= current_month)
        monthly_result = monthly_query.with_entities(func.sum(QuotationDetail.quantity)).scalar()
        monthly_increase = int(monthly_result) if monthly_result else 0
        
        # 计算分页信息
        total_pages = (total_count + per_page - 1) // per_page
        has_next = page < total_pages
        has_prev = page > 1
        
        return jsonify({
            'success': True,
            'data': data,
            'statistics': {
                'total_amount': total_amount,
                'total_count': total_quantity,
                'monthly_increase': monthly_increase,
                'avg_unit_price': avg_unit_price
            },
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_count': total_count,
                'total_pages': total_pages,
                'has_next': has_next,
                'has_prev': has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"获取产品分析数据失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# 创建并注册阶段统计组件API端点
stage_analytics_component = create_stage_analytics_component()
stage_analytics_component.create_api_endpoint(
    product_analysis, 
    '/api/stage_statistics',
    permission_decorator=login_required
)


@product_analysis.route('/api/products/filter')
@login_required
@permission_required('quotation', 'view')
def products_list_ajax():
    """植入产品分析AJAX筛选端点 - 只统计每个项目的最新报价单"""
    try:
        # 获取筛选参数
        search = request.args.get('search', '').strip()
        category = request.args.get('category', '').strip()
        product_name = request.args.get('product_name', '').strip()
        product_model = request.args.get('product_model', '').strip()

        # 获取分页参数
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 50, type=int)

        # 排序参数
        sort_field = request.args.get('sort_field', '')
        sort_direction = request.args.get('sort_direction', 'asc')

        # 获取最新报价单子查询
        latest_quotation_subq = _get_latest_quotation_subquery()

        # 构建基础查询 - 避免因Product表重复记录导致的重复统计
        # 重要：只查询最新报价单的产品明细
        query = db.session.query(
            QuotationDetail.id,
            QuotationDetail.product_name,
            QuotationDetail.product_model,
            QuotationDetail.product_desc,
            QuotationDetail.quantity,
            QuotationDetail.discount,
            QuotationDetail.unit_price,
            QuotationDetail.total_price,
            QuotationDetail.product_mn,
            User,  # 获取完整的User对象
            Project.id.label('project_id'),
            Project.project_name,
            Project.current_stage,
            Quotation.id.label('quotation_id'),
            Quotation.quotation_number,
            QuotationDetail.updated_at,
            QuotationDetail.created_at
        ).join(
            Quotation, QuotationDetail.quotation_id == Quotation.id
        ).join(
            latest_quotation_subq,
            and_(
                Quotation.project_id == latest_quotation_subq.c.project_id,
                Quotation.id == latest_quotation_subq.c.latest_quotation_id
            )
        ).join(
            Project, Quotation.project_id == Project.id
        ).join(
            User, Quotation.owner_id == User.id
        )
        
        # 应用基于权限系统的数据过滤
        query = apply_permission_based_filters(query, current_user)
        
        # 应用搜索过滤
        if search:
            search_filter = or_(
                QuotationDetail.product_name.ilike(f'%{search}%'),
                QuotationDetail.product_model.ilike(f'%{search}%'),
                QuotationDetail.product_desc.ilike(f'%{search}%'),
                QuotationDetail.product_mn.ilike(f'%{search}%'),
                Project.project_name.ilike(f'%{search}%'),
                Quotation.quotation_number.ilike(f'%{search}%'),
                User.username.ilike(f'%{search}%'),
                User.real_name.ilike(f'%{search}%')
            )
            query = query.filter(search_filter)

        # 应用筛选条件
        if category:
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
        
        if product_name and product_name.strip():
            query = query.filter(QuotationDetail.product_name == product_name)
        
        if product_model and product_model.strip():
            query = query.filter(QuotationDetail.product_model == product_model)
        
        # 获取总数（用于分页）
        total_count = query.count()
        
        # 动态排序（产品分析复杂查询需要特殊处理）
        if sort_field and sort_direction:
            print(f"🔍 产品分析排序调试 - 字段: {sort_field}, 方向: {sort_direction}")
            
            # 字段映射（已经JOIN的表字段）
            field_mapping = {
                # QuotationDetail 表字段
                'product_name': QuotationDetail.product_name,
                'product_model': QuotationDetail.product_model,
                'quantity': QuotationDetail.quantity,
                'unit_price': QuotationDetail.unit_price,
                'total_price': QuotationDetail.total_price,
                'product_mn': QuotationDetail.product_mn,
                'created_at': QuotationDetail.created_at,
                'updated_at': QuotationDetail.updated_at,
                'discount': QuotationDetail.discount,
                # 关联表字段（已JOIN）
                'owner_name': User.real_name,  # 负责人名称
                'project_name': Project.project_name,  # 项目名称
                'current_stage': Project.current_stage,  # 项目阶段
                'quotation_number': Quotation.quotation_number  # 报价单编号
            }
            
            if sort_field in field_mapping:
                sort_column = field_mapping[sort_field]
                if sort_direction.lower() == 'desc':
                    query = query.order_by(sort_column.desc())
                    print(f"✅ 应用降序排序: {sort_field}")
                else:
                    query = query.order_by(sort_column.asc())
                    print(f"✅ 应用升序排序: {sort_field}")
            else:
                print(f"❌ 未知排序字段: {sort_field}")
                # 默认排序
                query = query.order_by(QuotationDetail.updated_at.desc())
        else:
            print("📊 使用默认排序: updated_at desc")
            # 默认排序
            query = query.order_by(QuotationDetail.updated_at.desc())
        
        # 执行分页查询
        try:
            results = query.offset(offset).limit(limit).all()
            logger.info(f"植入产品分析查询成功: 总计 {total_count} 条，offset={offset}, limit={limit}, 返回 {len(results)} 条")
        except Exception as e:
            logger.warning(f"查询失败: {str(e)}, 尝试使用id排序")
            try:
                # 回滚失败的事务
                db.session.rollback()
                results = query.order_by(QuotationDetail.id.desc()).offset(offset).limit(limit).all()
                logger.info(f"植入产品分析查询(id排序)成功: 总计 {total_count} 条，offset={offset}, limit={limit}, 返回 {len(results)} 条")
            except Exception as e2:
                logger.error(f"产品分析查询失败: {str(e2)}")
                # 回滚失败的事务
                db.session.rollback()
                results = []
        
        # 使用模板渲染表格行HTML
        
        if not results:
            from app.utils.mobile_helpers import is_mobile_request
            if is_mobile_request():
                html = '<div class="text-center py-4">暂无符合条件的数据</div>'
            else:
                html = '<tr><td colspan="13" class="text-center py-4">暂无符合条件的数据</td></tr>'
        else:
            # 创建简单的数据结构供模板使用
            formatted_results = []
            for row in results:
                # 使用命名空间对象，更简单可靠
                # 注意：现在row[9]是完整的User对象，row[10]开始是project_id等
                formatted_row = SimpleNamespace(
                    id=row[0],
                    product_name=row[1],
                    product_model=row[2],
                    product_desc=row[3],
                    quantity=row[4],
                    discount=row[5],
                    unit_price=row[6],
                    total_price=row[7],
                    product_mn=row[8],
                    owner=row[9],  # 完整的User对象
                    project_id=row[10],
                    project_name=row[11],
                    current_stage=row[12],
                    current_stage_label=get_stage_label(row[12] or 'unset'),
                    quotation_id=row[13],
                    quotation_number=row[14],
                    updated_at=row[15],
                    created_at=row[16]
                )
                formatted_results.append(formatted_row)
            
            # 检测移动端并使用智能移动卡片
            from app.utils.mobile_helpers import is_mobile_request
            
            if is_mobile_request():
                # 智能移动卡片配置 - 产品植入分析
                smart_mobile_card = {
                    'module': 'product_analysis',
                    'title_field': {'field': 'product_name'},
                    'badges': [
                        {'field': 'current_stage_label', 'renderer': 'project_stage'}
                    ],
                    'details': [
                        {'field': 'product_model', 'label': '产品型号'},
                        {'field': 'product_mn', 'label': '产品料号'},
                        {'field': 'project_name', 'label': '关联项目', 'renderer': 'project_link'},
                        {'field': 'quotation_number', 'label': '报价单号'},
                        {'field': 'quantity', 'label': '数量'},
                        {'field': 'total_price', 'label': '总价', 'format': 'currency'},
                        {'field': 'updated_at', 'label': '更新时间', 'format': 'date'}
                    ]
                }
                
                # 使用智能移动卡片模板渲染
                html = render_template_string('''
                {% from 'macros/ui_helpers.html' import render_smart_mobile_cards %}
                {{ render_smart_mobile_cards(items, card_config) }}
                ''', items=formatted_results, card_config=smart_mobile_card)
            else:
                # 桌面端使用传统表格行渲染
                html = render_template('product_analysis/product_analysis_rows_simple.html', items=formatted_results)
            logger.info(f"✅ 模板渲染成功，生成了 {len(formatted_results)} 行数据")
        
        # 使用模组化函数计算统计信息
        current_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        ajax_stats_data = _calculate_product_analysis_stats(query, current_month)
        
        # 计算是否还有更多数据
        has_more = (offset + len(results)) < total_count
        
        return jsonify({
            'success': True,
            'html': html,
            'has_more': has_more,
            'total_count': total_count,
            'loaded_count': offset + len(results),
            'statistics': {
                # 使用模组化统计计算结果，转换为万元以兼容通用模组
                # 总项目数
                'total_count': ajax_stats_data['record_count'],
                'total_amount': round(ajax_stats_data['total_amount'] / 10000, 2),  # 转换为万元
                
                # 本月新增（包含数量和金额）
                'monthly_increase_count': ajax_stats_data['monthly_quantity'],
                'monthly_increase_amount': round(ajax_stats_data['monthly_amount'] / 10000, 2),  # 转换为万元
                
                # 平均单价
                'avg_unit_price_count': 1,  # 固定显示1个单位
                'avg_unit_price_amount': round(ajax_stats_data['avg_unit_price'] / 10000, 4)  # 转换为万元，保留4位小数
            }
        })
        
    except Exception as e:
        logger.error(f"植入产品分析AJAX筛选失败: {str(e)}", exc_info=True)
        return jsonify({
            'success': False, 
            'error': f'筛选失败: {str(e)}',
            'html': '<tr><td colspan="13" class="text-center py-4 text-danger">加载失败，请刷新页面重试</td></tr>'
        }), 500

@product_analysis.route('/api/export_analysis')
@login_required
@permission_required('quotation', 'view')
def export_analysis():
    """导出产品分析数据"""
    try:
        # 获取分析数据
        category = request.args.get('category')
        product_name = request.args.get('product_name')
        product_model = request.args.get('product_model')
        
        # 这里可以实现导出功能，例如导出为Excel
        # 暂时返回成功消息
        return jsonify({
            'success': True,
            'message': '导出功能正在开发中'
        })
        
    except Exception as e:
        logger.error(f"导出产品分析数据失败: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500 