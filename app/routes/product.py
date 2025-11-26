from flask import json

# Flask 2.3+ JSON兼容层
try:
    from flask.json import jsonify, loads, dumps
except (ImportError, AttributeError):
    from flask import current_app
    
    def jsonify(*args, **kwargs):
        return current_app.json.response(*args, **kwargs)
    
    def dumps(*args, **kwargs):
        return current_app.json.dumps(*args, **kwargs)
    
    def loads(*args, **kwargs):
        return current_app.json.loads(*args, **kwargs)

# 分开导入其他组件
from flask import Blueprint, request, render_template, flash, redirect, url_for
from flask_babel import gettext as _
import logging

# 设置日志记录器
logger = logging.getLogger(__name__)
try:
    from flask.json.provider import JSONProvider  
except ImportError:
    # 兼容低版本的Flask
    JSONProvider = None
    
from app.models.product import Product
from app.models.product_code import ProductSubcategory, ProductCategory
from app.extensions import db
from app.utils.product_helpers import get_products_by_name
import logging
from decimal import Decimal, InvalidOperation
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import func, and_, or_
from flask import url_for
from app.decorators import permission_required  # 添加权限装饰器导入
import os
import uuid
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app
from app.utils.supabase_client import get_supabase_client
from app.services.product_file_service import get_product_file_service

logger = logging.getLogger(__name__)
# 创建蓝图
bp = Blueprint('product_route', __name__)

# 文件验证和处理功能已移至 ProductFileService

# 本地PDF处理函数已移除，使用 ProductFileService


def _get_product_form_data():
    """获取产品表单所需的通用数据（分类、地区、品牌列表）

    Returns:
        dict: 包含 categories, regions, brands 的字典
    """
    from app.models.product_code import ProductCategory, ProductCodeField, ProductCodeFieldOption

    # 获取所有产品分类
    categories = ProductCategory.get_ordered_list()

    # 获取所有产品地区（从ProductCodeField获取，统一数据源）
    region_fields = ProductCodeField.query.filter_by(field_type='origin_location')\
                                          .order_by(ProductCodeField.position).all()

    regions = []
    for field in region_fields:
        # 获取编码（处理"?"情况）
        code = field.code or '0'
        if code == "?":
            # 从字段选项中获取第一个选项的编码
            option = ProductCodeFieldOption.query.filter_by(field_id=field.id).first()
            code = option.code if option else "0"

        regions.append({
            'id': field.id,
            'name': field.name,
            'code': code
        })

    # 获取现有品牌列表（去重、非空、排序）
    existing_brands = db.session.query(Product.brand)\
        .filter(Product.brand.isnot(None), Product.brand != '')\
        .distinct()\
        .order_by(Product.brand)\
        .all()
    brands = [b[0] for b in existing_brands]

    return {
        'categories': categories,
        'regions': regions,
        'brands': brands
    }


@bp.route('/products', methods=['GET'])
@login_required
@permission_required('product', 'view')  # 产品库只检查product权限
def product_list():
    """产品列表页面"""
    # 获取用户的产品权限
    can_edit_product = current_user.has_permission('product', 'edit')
    can_delete_product = current_user.has_permission('product', 'delete')
    
    # 获取筛选参数
    search = request.args.get('search', '').strip()
    product_type = request.args.get('product_type', '').strip()
    category = request.args.get('category', '').strip()
    brand = request.args.get('brand', '').strip()
    status = request.args.get('status', '').strip()
    
    # 构建查询
    query = Product.query
    
    # 产品停产状态过滤：只有产品经理、解决方案经理和管理员可以查看停产产品
    if current_user.role not in ['admin', 'product_manager', 'solution_manager']:
        query = query.filter(Product.status == 'active')
    
    # 应用搜索条件（搜索产品名称、MN、型号）
    if search:
        search_term = f'%{search}%'
        # 先join ProductSubcategory以支持新字段搜索
        query = query.outerjoin(ProductSubcategory, Product.subcategory_id == ProductSubcategory.id)
        query = query.filter(
            or_(
                ProductSubcategory.name.ilike(search_term),
                Product.product_mn.ilike(search_term),
                Product.model.ilike(search_term)
            )
        )
    
    # 应用筛选条件
    if product_type:
        query = query.filter(Product.type == product_type)
    if category:
        # 通过外键关系筛选
        # 先确保JOIN了ProductSubcategory
        if 'product_subcategories' not in str(query.statement.compile() if hasattr(query, 'statement') else query).lower():
            query = query.outerjoin(ProductSubcategory, Product.subcategory_id == ProductSubcategory.id)
        # 通过ProductSubcategory JOIN ProductCategory
        query = query.outerjoin(ProductCategory, ProductSubcategory.category_id == ProductCategory.id)
        query = query.filter(ProductCategory.name == category)
    if brand:
        query = query.filter(Product.brand == brand)
    if status:
        query = query.filter(Product.status == status)
    
    # 执行查询：按分类体系排序
    # 避免重复JOIN（如果前面的搜索/筛选已经JOIN，则不再重复）
    from app.models.product_code import ProductCategory, ProductSubcategory

    # 检查是否已经JOIN了这些表
    query_str = str(query.statement.compile()) if hasattr(query, 'statement') else str(query)
    has_subcategory_join = 'product_subcategory' in query_str.lower() or 'product_subcategories' in query_str.lower()
    has_category_join = 'product_category' in query_str.lower() or 'product_categories' in query_str.lower()

    # 只在需要时添加JOIN
    if not has_subcategory_join:
        query = query.outerjoin(ProductSubcategory, Product.subcategory_id == ProductSubcategory.id)
    if not has_category_join:
        query = query.outerjoin(ProductCategory, ProductSubcategory.category_id == ProductCategory.id)

    # 添加排序（按分类display_order、子分类display_order、产品型号）
    query = query.order_by(
        ProductCategory.display_order.asc(),
        ProductCategory.id.asc(),
        ProductSubcategory.display_order.asc(),
        ProductSubcategory.name.asc(),
        Product.model.asc(),
        Product.id.asc()
    )

    # 执行查询
    products = query.all()

    # 统计数据
    total_count = len(products)
    active_count = len([p for p in products if p.status == 'active'])
    discontinued_count = len([p for p in products if p.status == 'discontinued'])
    upcoming_count = len([p for p in products if p.status == 'upcoming'])
    
    # 计算总价值
    total_value = sum([(p.retail_price or 0) for p in products])
    
    # 使用标准化金额转换
    from app.utils.dictionary_helpers import prepare_stats_card_amount
    amount_data = prepare_stats_card_amount(total_value)
    
    # 获取筛选选项数据
    product_types = db.session.query(Product.type).distinct().filter(
        Product.type.isnot(None), Product.type != ''
    ).all()
    product_types = [{'value': t[0], 'label': t[0]} for t in product_types if t[0]]
    
    # 从ProductCategory表查询，按display_order排序
    categories = ProductCategory.get_ordered_list()
    categories = [{'value': cat.name, 'label': cat.name} for cat in categories]
    
    brands = db.session.query(Product.brand).distinct().filter(
        Product.brand.isnot(None), Product.brand != ''
    ).all()
    brands = [{'value': b[0], 'label': b[0]} for b in brands if b[0]]
    
    status_options = [
        {'value': 'active', 'label': _('生产中')},
        {'value': 'discontinued', 'label': _('已停产')},
        {'value': 'upcoming', 'label': _('待上市')}
    ]
    
    # 构建筛选配置
    filter_config = {
        'action_url': url_for('product_route.product_list'),
        'form_id': 'productFilterForm',
        'reset_url': url_for('product_route.product_list'),
        'realtime_search': False,
        'auto_submit': True,                    # 启用自动筛选
        'ajax_mode': True,                      # 启用AJAX模式
        'ajax_endpoint': url_for('product_route.product_list_ajax'),
        'ajax_target': 'productTableBody',
        'ajax_columns': 12,
        'dynamic_reset_button': True,           # 启用动态重置按钮
        'adaptive_width': True,
        'adaptive_button_layout': True,
        'search_delay': 300,
        
        'search_field': {
            'name': 'search',
            'label': _('搜索'),
            'placeholder': _('产品名称、MN号或型号'),
            'value': search,
            'col_width': 4
        },
        
        'filter_fields': [
            {
                'name': 'product_type',
                'label': _('产品类型'),
                'all_option_text': _('全部类型'),
                'current_value': product_type,
                'col_width': 2,
                'options': product_types
            },
            {
                'name': 'category',
                'label': _('产品类别'),
                'all_option_text': _('全部类别'),
                'current_value': category,
                'col_width': 2,
                'options': categories
            },
            {
                'name': 'brand',
                'label': _('品牌'),
                'all_option_text': _('全部品牌'),
                'current_value': brand,
                'col_width': 2,
                'options': brands
            },
            {
                'name': 'status',
                'label': _('状态'),
                'all_option_text': _('全部状态'),
                'current_value': status,
                'col_width': 2,
                'options': status_options
            }
        ],
        
        'search_button_text': _('搜索'),
        'reset_button_text': _('重置')
    }
    
    # 标准通用组件配置
    list_config = {
        'module_name': 'product',
        'title': _('产品库管理'),
        'ajax_mode': True,
        
        # 统计卡片
        'stats': {
            'cards': [
                {
                    'id': 'total',
                    'title': _('总产品数'),
                    'icon': 'fas fa-cube',
                    'value': total_count,
                    'amount': amount_data['value'],
                    'unit': _('个'),
                    'amount_unit': amount_data['unit'],
                    'color': 'primary',
                    'data_key': 'total'
                },
                {
                    'id': 'active',
                    'title': _('生产中'),
                    'icon': 'fas fa-play-circle',
                    'value': active_count,
                    'unit': _('个'),
                    'color': 'success',
                    'clickable': True,
                    'click_params': {'status': 'active'},
                    'data_key': 'active'
                },
                {
                    'id': 'discontinued',
                    'title': _('已停产'),
                    'icon': 'fas fa-stop-circle',
                    'value': discontinued_count,
                    'unit': _('个'),
                    'color': 'danger',
                    'clickable': True,
                    'click_params': {'status': 'discontinued'},
                    'data_key': 'discontinued'
                },
                {
                    'id': 'upcoming',
                    'title': _('待上市'),
                    'icon': 'fas fa-clock',
                    'value': upcoming_count,
                    'unit': _('个'),
                    'color': 'warning',
                    'clickable': True,
                    'click_params': {'status': 'upcoming'},
                    'data_key': 'upcoming'
                }
            ]
        },
        
        # 筛选配置
        'filter': filter_config,
        
        # 表格配置
        'table': {
            'ajax_target': 'productTableBody',
            'title': _('产品列表'),
            'icon': 'fas fa-table',
            'fixed_height_scroll': True,  # 启用固定表头功能
            'use_custom_rows': True,
            'custom_rows_template': 'product/product_rows.html',
            'columns': [
                {'key': 'type', 'field': 'type', 'label': _('产品类型'), 'width': '100px', 'sort_type': 'string'},
                {'key': 'category', 'field': 'category', 'label': _('产品类别'), 'width': '120px', 'sort_type': 'string'},
                {'key': 'status', 'field': 'status', 'label': _('状态'), 'width': '100px', 'sort_type': 'string'},
                {'key': 'product_name', 'field': 'product_name', 'label': _('产品名称'), 'width': '180px', 'sort_type': 'string'},
                {'key': 'model', 'field': 'model', 'label': _('型号'), 'width': '120px', 'sort_type': 'string'},
                {'key': 'specification', 'field': 'specification', 'label': _('规格'), 'width': '150px', 'sort_type': 'string'},
                {'key': 'brand', 'field': 'brand', 'label': _('品牌'), 'width': '100px', 'sort_type': 'string'},
                {'key': 'unit', 'field': 'unit', 'label': _('单位'), 'width': '80px', 'sort_type': 'string'},
                {'key': 'retail_price', 'field': 'retail_price', 'label': _('价格'), 'width': '100px', 'sort_type': 'number'},
                {'key': 'product_mn', 'field': 'product_mn', 'label': _('MN号'), 'width': '120px', 'sort_type': 'string'},
                {'key': 'created_at', 'field': 'created_at', 'label': _('创建时间'), 'width': '150px', 'sort_type': 'date'}
            ]
        }
    }

    return render_template('product/index.html', 
                          list_config=list_config,
                          products=products,  # 保留用于行模板
                          can_edit_product=can_edit_product,
                          can_delete_product=can_delete_product)

@bp.route('/products/create', methods=['GET'])
@login_required
@permission_required('product', 'create')  # 添加产品创建权限装饰器
def create_product_page():
    """创建产品页面（标准产品）- 使用统一模板"""
    form_data = _get_product_form_data()
    form_data['product_type'] = 'standard'  # 标记为标准产品
    return render_template('product/create.html', **form_data)

@bp.route('/create', methods=['POST'])
@login_required
@permission_required('product', 'create')
def create():
    """处理产品创建表单提交（新版分类体系+规格管理）"""
    try:
        logger.debug('正在创建新产品（新版）...')

        # 获取表单数据
        product_type = request.form.get('type') or None
        product_status = request.form.get('status', 'active')
        category_id = request.form.get('category_id')
        subcategory_id = request.form.get('subcategory_id')
        region_id = request.form.get('region_id') or None
        product_model = request.form.get('product_model')
        product_mn = request.form.get('product_mn')
        brand = request.form.get('brand') or None
        unit = request.form.get('unit')
        retail_price = request.form.get('retail_price')
        currency = request.form.get('currency', 'CNY')
        description = request.form.get('description')

        # 验证必填字段
        if not all([category_id, subcategory_id, product_model, product_mn]):
            flash('请填写所有必填字段', 'error')
            return redirect(url_for('product_route.create_product_page'))

        # 验证MN号全局唯一性（跨研发库和产品库）
        from app.routes.product_management import check_mn_code_duplicate
        duplicate_info = check_mn_code_duplicate(product_mn)
        if duplicate_info['is_duplicate']:
            # 构建详细错误信息
            error_parts = []
            if duplicate_info['dev_products']:
                dev_models = ', '.join([p['model'] for p in duplicate_info['dev_products']])
                error_parts.append(f"研发产品库: {dev_models}")
            if duplicate_info['standard_products']:
                std_models = ', '.join([p['model'] for p in duplicate_info['standard_products']])
                error_parts.append(f"产品库: {std_models}")

            error_msg = f"MN编号 {product_mn} 已被以下产品使用：" + "；".join(error_parts)
            flash(error_msg, 'error')
            return redirect(url_for('product_route.create_product_page'))

        # 处理零售价格
        if retail_price:
            try:
                retail_price = Decimal(retail_price)
            except (InvalidOperation, ValueError):
                flash('零售价格格式不正确', 'error')
                return redirect(url_for('product_route.create_product_page'))
        else:
            retail_price = Decimal('0.00')

        # 创建新产品
        new_product = Product(
            type=product_type,
            status=product_status,
            category_id=int(category_id),
            subcategory_id=int(subcategory_id),
            region_id=int(region_id) if region_id else None,
            model=product_model,
            product_mn=product_mn,
            brand=brand,
            unit=unit,
            retail_price=retail_price,
            currency=currency,
            specification=description,  # 使用旧字段存储描述
            source_type='manual',  # 手动创建
            owner_id=current_user.id
        )

        # 保存产品以获取ID
        db.session.add(new_product)
        db.session.flush()

        # 保存规格数据
        spec_names = request.form.getlist('spec_name[]')
        spec_values = request.form.getlist('spec_value[]')
        spec_codes = request.form.getlist('spec_option_codes[]')
        spec_field_ids = request.form.getlist('spec_field_ids[]')

        if spec_names:
            spec_data_list = []
            for i in range(len(spec_names)):
                if spec_names[i].strip():  # 只处理非空规格
                    spec_data_list.append({
                        'field_name': spec_names[i],
                        'field_value': spec_values[i] if i < len(spec_values) else '',
                        'field_code': spec_codes[i] if i < len(spec_codes) and spec_codes[i] != '0' else None,
                        'action': 'create'
                    })

            if spec_data_list:
                success, saved_specs, error = save_product_specs(new_product.id, spec_data_list)
                if not success:
                    db.session.rollback()
                    flash(f'保存规格数据失败: {error}', 'error')
                    return redirect(url_for('product_route.create_product_page'))

                logger.debug(f'保存了 {len(saved_specs)} 条规格数据')

        # 提交事务
        db.session.commit()

        logger.info(f'产品创建成功: ID={new_product.id}, MN={new_product.product_mn}, 型号={new_product.model}')
        flash('产品创建成功', 'success')

        # 重定向到产品列表
        return redirect(url_for('product_route.product_list'))

    except Exception as e:
        db.session.rollback()
        logger.error(f'创建产品时出错: {str(e)}', exc_info=True)
        flash(f'创建产品失败: {str(e)}', 'error')
        return redirect(url_for('product_route.create_product_page'))

@bp.route('/products/<int:id>/edit', methods=['GET'])
@login_required
@permission_required('product', 'edit')  # 添加产品编辑权限装饰器
def edit_product_page(id):
    """编辑产品页面"""
    from sqlalchemy.orm import joinedload
    from app.models.product_code import ProductSubcategory
    from app.models.product_spec import ProductSpec

    # 使用joinedload预加载关联数据
    product = db.session.query(Product).options(
        joinedload(Product.category_obj),
        joinedload(Product.subcategory_obj),
        joinedload(Product.region_obj)
    ).filter_by(id=id).first_or_404()

    # 使用统一函数获取通用数据（分类、地区、品牌列表）
    form_data = _get_product_form_data()

    # 获取当前分类下的子分类列表
    subcategories = []
    if product.category_id:
        subcategories = ProductSubcategory.query.filter_by(
            category_id=product.category_id
        ).order_by(ProductSubcategory.display_order).all()

    # 获取产品规格数据
    specs_db = ProductSpec.query.filter_by(product_id=id).order_by(ProductSpec.display_order).all()

    # 将ProductSpec对象转换为字典列表（方便前端使用）
    # 同时查询对应的field_id（用于加载指标选项）
    from app.models.product_code import ProductCodeField
    specs = []
    for spec in specs_db:
        spec_dict = {
            'field_name': spec.field_name,
            'field_value': spec.field_value,
            'field_code': spec.field_code,
            'is_saved': True,  # 标记为已保存的规格，前端将以只读方式显示
            'include_in_description': spec.include_in_description if spec.include_in_description is not None else False
        }
        # 尝试查找对应的ProductCodeField以获取field_id
        field = ProductCodeField.query.filter_by(
            subcategory_id=product.subcategory_id,
            name=spec.field_name
        ).first()
        if field:
            spec_dict['field_id'] = field.id
        specs.append(spec_dict)

    # 获取锁定状态
    is_mn_locked = product.is_mn_locked or False

    # 管理员绕过锁定限制
    is_admin = current_user.role == 'admin'

    # 检查是否被报价单引用（按MN编号检查，MN是唯一标识）
    from app.models.quotation import QuotationDetail
    is_referenced = QuotationDetail.query.filter(
        QuotationDetail.product_mn == product.product_mn
    ).count() > 0

    # 检查关键字段是否有值（用于智能锁定控制）
    has_category = product.category_id is not None
    has_subcategory = product.subcategory_id is not None
    has_region = product.region_id is not None
    has_model = bool(product.model and product.model.strip())
    has_specs = len(specs) > 0

    return render_template('product/create.html',
                         product=product,
                         subcategories=subcategories,
                         specs=specs,
                         product_type='standard',  # 标识为标准产品
                         is_mn_locked=is_mn_locked,
                         is_admin=is_admin,
                         is_referenced=is_referenced,
                         has_category=has_category,
                         has_subcategory=has_subcategory,
                         has_region=has_region,
                         has_model=has_model,
                         has_specs=has_specs,
                         **form_data)

# API路由
@bp.route('/products/ajax', methods=['GET'])
@login_required
@permission_required('product', 'view')
def product_list_ajax():
    """产品列表AJAX端点"""
    try:
        # 导入必需的模型类
        from app.models.product_code import ProductCategory, ProductSubcategory

        # 获取筛选参数
        search = request.args.get('search', '').strip()
        product_type = request.args.get('product_type', '').strip()
        category = request.args.get('category', '').strip()
        brand = request.args.get('brand', '').strip()
        status = request.args.get('status', '').strip()

        # 获取排序参数 (支持两种参数格式)
        sort_field = request.args.get('sort_field') or request.args.get('sort')
        sort_dir = request.args.get('sort_direction') or request.args.get('dir', 'asc')

        # 构建查询
        query = Product.query
        
        # 产品停产状态过滤：只有产品经理、解决方案经理和管理员可以查看停产产品
        if current_user.role not in ['admin', 'product_manager', 'solution_manager']:
            query = query.filter(Product.status == 'active')
        
        # 应用搜索条件（搜索产品名称、MN、型号）
        if search:
            search_term = f'%{search}%'
            # 先join ProductSubcategory以支持新字段搜索
            query = query.outerjoin(ProductSubcategory, Product.subcategory_id == ProductSubcategory.id)
            query = query.filter(
                or_(
                    ProductSubcategory.name.ilike(search_term),
                    Product.product_mn.ilike(search_term),
                    Product.model.ilike(search_term)
                )
            )
        
        # 应用筛选条件
        if product_type:
            query = query.filter(Product.type == product_type)
        if category:
            # 通过外键关系筛选
            # 先确保JOIN了ProductSubcategory
            if 'product_subcategories' not in str(query.statement.compile() if hasattr(query, 'statement') else query).lower():
                query = query.outerjoin(ProductSubcategory, Product.subcategory_id == ProductSubcategory.id)
            # 通过ProductSubcategory JOIN ProductCategory
            query = query.outerjoin(ProductCategory, ProductSubcategory.category_id == ProductCategory.id)
            query = query.filter(ProductCategory.name == category)
        if brand:
            query = query.filter(Product.brand == brand)
        if status:
            query = query.filter(Product.status == status)
        
        # 应用排序
        if sort_field and hasattr(Product, sort_field):
            field = getattr(Product, sort_field)
            if sort_dir.lower() == 'desc':
                query = query.order_by(field.desc())
            else:
                query = query.order_by(field.asc())
        else:
            # 默认排序：按分类体系
            # 避免重复JOIN（如果前面的搜索/筛选已经JOIN，则不再重复）

            # 检查是否已经JOIN了这些表
            query_str = str(query.statement.compile()) if hasattr(query, 'statement') else str(query)
            has_subcategory_join = 'product_subcategory' in query_str.lower() or 'product_subcategories' in query_str.lower()
            has_category_join = 'product_category' in query_str.lower() or 'product_categories' in query_str.lower()

            # 只在需要时添加JOIN
            if not has_subcategory_join:
                query = query.outerjoin(ProductSubcategory, Product.subcategory_id == ProductSubcategory.id)
            if not has_category_join:
                query = query.outerjoin(ProductCategory, ProductSubcategory.category_id == ProductCategory.id)

            query = query.order_by(
                ProductCategory.display_order.asc(),
                ProductCategory.id.asc(),
                ProductSubcategory.display_order.asc(),
                ProductSubcategory.name.asc(),
                Product.model.asc(),
                Product.id.asc()
            )
        
        # 执行查询
        products = query.all()
        total_count = len(products)
        
        # 统计数据
        active_count = len([p for p in products if p.status == 'active'])
        discontinued_count = len([p for p in products if p.status == 'discontinued'])
        upcoming_count = len([p for p in products if p.status == 'upcoming'])
        
        # 计算总价值
        total_value = sum([(p.retail_price or 0) for p in products])
        
        # 渲染产品HTML
        products_html = render_template('product/product_rows.html', 
                                      products=products,
                                      can_edit_product=current_user.has_permission('product', 'edit'),
                                      can_delete_product=current_user.has_permission('product', 'delete'))
        
        return jsonify({
            'success': True,
            'html': products_html,
            'has_more': False,
            'total_count': total_count,
            'loaded_count': total_count,
            'statistics': {
                'total_count': total_count,
                'total_amount': float(total_value / 10000) if total_value > 0 else 0,
                'active_count': active_count,
                'discontinued_count': discontinued_count,
                'upcoming_count': upcoming_count
            }
        })
        
    except Exception as e:
        logger.error(f'获取产品列表AJAX失败: {str(e)}')
        import traceback
        logger.error(f'详细错误: {traceback.format_exc()}')
        return jsonify({
            'success': False,
            'message': f'获取产品列表失败: {str(e)}'
        }), 500

@bp.route('/api/products', methods=['GET'])
@login_required
@permission_required('product', 'view')  # 添加产品查看权限装饰器
def get_products():
    """获取产品列表API"""
    try:
        logger.debug('正在获取产品列表...')
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search_term = request.args.get('search', '')
        sort_by = request.args.get('sort_by', 'id')  # 默认按ID排序
        sort_order = request.args.get('sort_order', 'asc')  # 默认升序
        filter_field = request.args.get('filter_field', '')
        filter_value = request.args.get('filter_value', '')
        
        # 构建查询
        query = Product.query
        
        # 去除数据所有权过滤
        # 如果用户通过了permission_required('product', 'view')装饰器，就应该能查看所有产品
        
        # 产品停产状态过滤：只有产品经理、解决方案经理和管理员可以查看停产产品
        if current_user.role not in ['admin', 'product_manager', 'solution_manager']:
            # 其他角色只能看到生产中的产品（status = 'active'）
            query = query.filter(Product.status == 'active')
        
        # 应用搜索条件
        if search_term:
            search_term = f'%{search_term}%'
            # 先join ProductSubcategory以支持新字段搜索
            query = query.outerjoin(ProductSubcategory, Product.subcategory_id == ProductSubcategory.id)
            query = query.filter(
                or_(
                    ProductSubcategory.name.ilike(search_term),
                    Product.product_mn.ilike(search_term),
                    Product.model.ilike(search_term),
                    Product.type.ilike(search_term)
                )
            )
        
        # 应用字段筛选
        if filter_field and filter_value:
            if filter_field == 'status':
                # 状态字段的特殊处理
                query = query.filter(Product.status == filter_value)
            else:
                # 动态构建筛选条件
                filter_attr = getattr(Product, filter_field, None)
                if filter_attr:
                    query = query.filter(filter_attr.ilike(f'%{filter_value}%'))
        
        # 应用排序
        if sort_by and hasattr(Product, sort_by):
            sort_attr = getattr(Product, sort_by)
            if sort_order == 'desc':
                query = query.order_by(sort_attr.desc())
            else:
                query = query.order_by(sort_attr.asc())
        else:
            # 默认按ID升序排序
            query = query.order_by(Product.id.asc())
        
        # 执行分页查询
        pagination = query.paginate(page=page, per_page=per_page)
        
        # 转换为JSON格式
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            return obj
        
        result = {
            'items': [],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
        
        # 创建用户ID到用户真实姓名的映射
        from app.models.user import User
        user_map = {}
        # 收集所有产品的所有者ID
        owner_ids = [p.owner_id for p in pagination.items if p.owner_id]
        # 如果有所有者ID则查询对应的用户信息
        if owner_ids:
            users = User.query.filter(User.id.in_(set(owner_ids))).all()
            for user in users:
                # 优先使用真实姓名，如果没有则使用用户名
                user_map[user.id] = user.real_name if user.real_name else user.username
        
        for p in pagination.items:
            try:
                product_dict = {
                    'id': p.id,
                    'type': p.type,
                    'category': p.category_name,  # 使用智能属性
                    'product_mn': p.product_mn,
                    'product_name': p.name,  # 使用智能属性
                    'model': p.model,
                    'specification': p.specification,
                    'brand': p.brand,
                    'unit': p.unit,
                    'retail_price': decimal_to_float(p.retail_price) if p.retail_price else 0,
                    'currency': p.currency if hasattr(p, 'currency') else 'CNY',  # 添加货币字段
                    'status': p.status,
                    'is_vendor_product': p.is_vendor_product if hasattr(p, 'is_vendor_product') else False,  # 添加厂商产品标记
                    'created_at': p.created_at.strftime('%Y-%m-%d %H:%M:%S') if p.created_at else None,
                    'updated_at': p.updated_at.strftime('%Y-%m-%d %H:%M:%S') if p.updated_at else None,
                    'owner_id': p.owner_id,  # 添加所有者ID
                    'owner_name': user_map.get(p.owner_id, '未指定') if p.owner_id else '未指定',  # 添加所有者名称
                    'image_path': p.image_path  # 添加图片路径
                }
                result['items'].append(product_dict)
            except Exception as e:
                logger.error(f'处理产品时出错: {p.id} - {str(e)}')
                continue
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f'获取产品列表时出错: {str(e)}')
        return jsonify({
            'error': '获取产品列表失败',
            'message': str(e)
        }), 500

@bp.route('/api/products/categories', methods=['GET'])
@login_required
@permission_required('product', 'view')  # 添加产品查看权限装饰器
def get_product_categories():
    """获取去重后的产品类别列表"""
    try:
        logger.debug('正在获取产品类别列表...')
        # 直接从ProductCategory表查询,按display_order排序
        from app.models.product_code import ProductCategory
        categories = ProductCategory.get_ordered_list()

        # 提取类别名称
        category_list = [cat.name for cat in categories]

        logger.debug(f'找到 {len(category_list)} 个类别')
        return jsonify(category_list)
        
    except Exception as e:
        logger.error(f'获取产品类别列表时出错: {str(e)}')
        return jsonify({
            'error': '获取产品类别列表失败',
            'message': str(e)
        }), 500

@bp.route('/api/products/by-category', methods=['GET'])
@login_required
@permission_required('product', 'view')  # 添加产品查看权限装饰器
def get_products_by_category():
    """获取指定类别的产品列表"""
    try:
        category = request.args.get('category', '')
        logger.debug(f'正在获取类别 "{category}" 的产品列表...')
        
        if not category:
            return jsonify([])
        
        # 查询指定类别的产品
        products = Product.query.filter_by(
            category=category,
            status='active'
        ).all()
        
        logger.debug(f'找到 {len(products)} 个产品')
        
        # 小数类型转换为浮点数
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            return obj
        
        # 构建完整产品信息
        result = []
        for p in products:
            try:
                product_dict = {
                    'id': p.id,
                    'product_name': p.name,  # 使用智能属性
                    'model': p.model,
                    'specification': p.specification,
                    'brand': p.brand,
                    'unit': p.unit,
                    'retail_price': decimal_to_float(p.retail_price) if p.retail_price else 0,
                    'currency': p.currency if hasattr(p, 'currency') else 'CNY',  # 添加货币字段
                    'product_mn': p.product_mn
                }
                result.append(product_dict)
                logger.debug(f'成功处理产品: {p.product_name}, MN: {p.product_mn}')
            except Exception as e:
                logger.error(f'处理产品时出错: {p.id} - {str(e)}')
                continue
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f'获取类别产品列表时出错: {str(e)}')
        return jsonify({
            'error': '获取类别产品列表失败',
            'message': str(e)
        }), 500

@bp.route('/api/products/by-name', methods=['GET'])
@login_required
@permission_required('product', 'view')  # 添加产品查看权限装饰器
def get_products_by_name():
    """按名称获取产品列表"""
    try:
        product_name = request.args.get('product_name', '')
        logger.debug(f'正在获取产品 "{product_name}" 的型号列表...')
        
        if not product_name:
            return jsonify([])

        # 查询指定产品名称的产品型号（使用公共辅助函数）
        products = get_products_by_name(product_name)
        
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            return obj
        
        result = []
        for p in products:
            try:
                product_dict = {
                    'id': p.id,
                    'model': p.model,
                    'product_mn': p.product_mn,
                    'specification': p.specification,
                    'brand': p.brand,
                    'unit': p.unit,
                    'retail_price': decimal_to_float(p.retail_price) if p.retail_price else 0,
                    'currency': p.currency if hasattr(p, 'currency') else 'CNY'  # 添加货币字段
                }
                result.append(product_dict)
            except Exception as e:
                logger.error(f'处理产品时出错: {p.id} - {str(e)}')
                continue
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f'获取产品型号列表时出错: {str(e)}')
        return jsonify({
            'error': '获取产品型号列表失败',
            'message': str(e)
        }), 500

@bp.route('/api/products/models', methods=['GET'])
@login_required
@permission_required('product', 'view')  # 添加产品查看权限装饰器
def get_product_models():
    """获取指定类别和产品名称的型号列表"""
    try:
        category = request.args.get('category', '')
        product_name = request.args.get('product_name', '')
        logger.debug(f'正在获取产品型号，类别: "{category}", 产品名称: "{product_name}"')
        
        if not category or not product_name:
            return jsonify([])
        
        # 查询指定类别和产品名称的产品（包括停产产品）
        products = Product.query.filter_by(
            category=category,
            product_name=product_name
        ).order_by(Product.id).all()
        
        logger.debug(f'找到 {len(products)} 个产品')
        
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            return obj
        
        result = []
        for p in products:
            try:
                product_dict = {
                    'id': p.id,
                    'product_name': p.name,  # 使用智能属性
                    'category': p.category_name,  # 使用智能属性
                    'model': p.model,
                    'product_model': p.model,  # 兼容性字段
                    'product_mn': p.product_mn,
                    'mn': p.product_mn,  # 兼容性字段
                    'specification': p.specification,
                    'product_spec': p.specification,  # 兼容性字段
                    'product_desc': p.specification,  # 兼容性字段
                    'spec': p.specification,  # 兼容性字段
                    'brand': p.brand,
                    'unit': p.unit,
                    'retail_price': decimal_to_float(p.retail_price) if p.retail_price else 0,
                    'market_price': decimal_to_float(p.retail_price) if p.retail_price else 0,  # 兼容性字段
                    'currency': p.currency if hasattr(p, 'currency') else 'CNY',
                    'status': p.status,
                    'product_status': p.status  # 兼容性字段
                }
                result.append(product_dict)
                logger.debug(f'成功处理产品: {p.product_name}, 型号: {p.model}, MN: {p.product_mn}')
            except Exception as e:
                logger.error(f'处理产品时出错: {p.id} - {str(e)}')
                continue
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f'获取产品型号列表时出错: {str(e)}')
        return jsonify({
            'error': '获取产品型号列表失败',
            'message': str(e)
        }), 500

@bp.route('/api/products/<int:product_id>/upload-image', methods=['POST'])
@login_required
@permission_required('product', 'edit')
def upload_product_image(product_id):
    """上传产品图片"""
    file_service = get_product_file_service()
    image_file = request.files.get('image')
    
    if not image_file or not image_file.filename:
        return jsonify({'success': False, 'error': '请选择要上传的图片文件'}), 400
    
    result = file_service.upload_image(product_id, image_file)
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code

@bp.route('/api/products/<int:product_id>/upload-pdf', methods=['POST'])
@login_required
@permission_required('product', 'edit')
def upload_product_pdf(product_id):
    """上传产品PDF文档"""
    file_service = get_product_file_service()
    pdf_file = request.files.get('pdf')
    
    if not pdf_file or not pdf_file.filename:
        return jsonify({'success': False, 'error': '请选择要上传的PDF文件'}), 400
    
    result = file_service.upload_pdf(product_id, pdf_file)
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code

@bp.route('/api/products/<int:product_id>/upload-files', methods=['POST'])
@login_required
@permission_required('product', 'edit')
def upload_product_files(product_id):
    """批量上传产品文件（保持向后兼容）"""
    file_service = get_product_file_service()
    image_file = request.files.get('image')
    pdf_file = request.files.get('pdf')
    
    if not image_file and not pdf_file:
        return jsonify({'success': False, 'error': '请至少选择一个文件上传'}), 400
    
    result = {'success': True, 'image_url': None, 'pdf_url': None, 'errors': []}
    
    # 上传图片
    if image_file and image_file.filename:
        image_result = file_service.upload_image(product_id, image_file)
        if image_result['success']:
            result['image_url'] = image_result['image_url']
        else:
            result['errors'].append(image_result['error'])
    
    # 上传PDF
    if pdf_file and pdf_file.filename:
        pdf_result = file_service.upload_pdf(product_id, pdf_file)
        if pdf_result['success']:
            result['pdf_url'] = pdf_result['pdf_url']
        else:
            result['errors'].append(pdf_result['error'])
    
    result['success'] = len(result['errors']) == 0
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code

@bp.route('/products/<int:product_id>/upload', methods=['GET'])
@login_required
@permission_required('product', 'edit')
def upload_files_page(product_id):
    """显示产品文件上传页面"""
    # 检查产品是否存在
    product = Product.query.get_or_404(product_id)
    
    return render_template('product/upload_files.html', 
                         product_id=product_id,
                         product=product)

@bp.route('/api/products/check-mn', methods=['GET'])
def check_product_mn():
    """检查产品MN号是否重复"""
    try:
        product_mn = request.args.get('product_mn', '')
        exclude_id = request.args.get('exclude_id', 0, type=int)
        
        if not product_mn:
            return jsonify({'valid': False, 'message': 'MN号不能为空'})
        
        # 检查MN号是否已存在
        query = Product.query.filter(Product.product_mn == product_mn)
        
        # 如果是编辑现有产品，排除自身
        if exclude_id > 0:
            query = query.filter(Product.id != exclude_id)
        
        existing_product = query.first()
        
        if existing_product:
            return jsonify({
                'valid': False, 
                'message': f'MN号已被产品 {existing_product.product_name} ({existing_product.model}) 使用'
            })
        
        return jsonify({'valid': True, 'message': 'MN号可用'})
        
    except Exception as e:
        logger.error(f'检查MN号时出错: {str(e)}')
        return jsonify({
            'error': '检查MN号失败',
            'message': str(e)
        }), 500

@bp.route('/api/products/dashboard-data', methods=['GET'])
@login_required
@permission_required('product', 'view')  # 添加产品查看权限装饰器
def get_dashboard_data():
    """获取仪表盘数据"""
    try:
        # 基础查询，根据用户角色筛选可见产品
        base_query = Product.query
        
        # 如果不是管理员、产品经理或解决方案经理，只显示生产中的产品
        if current_user.role not in ['admin', 'product_manager', 'solution_manager']:
            base_query = base_query.filter(Product.status == 'active')
        
        # 按分类统计产品数量
        from app.models.product_code import ProductCategory

        category_stats = db.session.query(
            ProductCategory.name,
            func.count(Product.id)
        ).join(
            Product, Product.category_id == ProductCategory.id
        )

        # 应用产品可见性筛选到类别统计
        if current_user.role not in ['admin', 'product_manager', 'solution_manager']:
            category_stats = category_stats.filter(Product.status == 'active')

        # 完成分组查询，按ProductCategory.id分组保持业务顺序
        category_stats = category_stats.group_by(
            ProductCategory.id,
            ProductCategory.name
        ).order_by(ProductCategory.id).all()

        category_data = [{'category': cat, 'count': count} for cat, count in category_stats]
        
        # 统计各状态产品数量
        # 对于管理员、产品经理和解决方案经理，显示所有产品的状态
        if current_user.role in ['admin', 'product_manager', 'solution_manager']:
            active_count = Product.query.filter(Product.status == 'active').count()
            discontinued_count = Product.query.filter(Product.status == 'discontinued').count()
            upcoming_count = Product.query.filter(Product.status == 'upcoming').count()
        else:
            # 对于其他用户，只统计生产中的产品，其他状态产品显示为0
            active_count = Product.query.filter(Product.status == 'active').count()
            discontinued_count = 0
            upcoming_count = 0
        
        status_stats = {
            'active': active_count,
            'discontinued': discontinued_count,
            'upcoming': upcoming_count
        }
        
        # 统计项目产品和渠道产品数量
        # 构建类型统计查询
        type_stats_query = db.session.query(
            Product.type, 
            func.count(Product.id)
        ).filter(
            Product.type.isnot(None)
        )
        
        # 应用产品可见性筛选
        if current_user.role not in ['admin', 'product_manager', 'solution_manager']:
            # 对于其他用户，只统计生产中的产品
            type_stats_query = type_stats_query.filter(Product.status == 'active')
        
        # 完成分组查询
        type_stats = type_stats_query.group_by(
            Product.type
        ).all()
        
        # 确保type_stats包含所有产品类型，即使数量为0
        product_types = ["项目产品", "渠道产品", "第三方产品"]
        type_data = []
        
        # 创建一个字典，存储已有的统计数据
        existing_types = {t: count for t, count in type_stats}
        
        # 为每种产品类型创建一个条目
        for product_type in product_types:
            count = existing_types.get(product_type, 0)
            type_data.append({'type': product_type, 'count': count})
        
        # 总产品数量也应基于用户权限
        if current_user.role in ['admin', 'product_manager', 'solution_manager']:
            total_products = Product.query.count()
        else:
            total_products = Product.query.filter(Product.status == 'active').count()
        
        # 汇总所有数据
        dashboard_data = {
            'category_stats': category_data,
            'status_stats': status_stats,
            'type_stats': type_data,
            'total_products': total_products
        }
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        logger.error(f'获取仪表盘数据时出错: {str(e)}')
        return jsonify({
            'error': '获取仪表盘数据失败',
            'message': str(e)
        }), 500

# 产品库规格保存函数
def save_product_specs(product_id, spec_data_list, current_logger=None):
    """
    保存产品规格数据（参考研发库实现）

    Args:
        product_id: 产品ID
        spec_data_list: 规格数据列表 [
            {
                'id': existing_spec_id (可选，用于更新),
                'field_name': '规格名称',
                'field_value': '规格值',
                'field_code': '规格编码' (可选),
                'action': 'create'|'update'|'delete' (可选)
            }
        ]
        current_logger: 日志记录器

    Returns:
        tuple: (success, saved_specs, error_message)
    """
    if not current_logger:
        current_logger = logger

    from app.models.product_spec import ProductSpec
    saved_specs = []

    try:
        for spec_data in spec_data_list:
            action = spec_data.get('action', 'create')

            if action == 'delete':
                # 删除规格
                spec_id = spec_data.get('id')
                if spec_id:
                    spec_to_delete = ProductSpec.query.get(spec_id)
                    if spec_to_delete and spec_to_delete.product_id == product_id:
                        # 只能删除非编码规格
                        if not spec_to_delete.field_code or spec_to_delete.field_code.strip() == '':
                            db.session.delete(spec_to_delete)
                            current_logger.debug(f"删除非编码规格: {spec_to_delete.field_name}")

            elif action == 'update':
                # 更新现有规格
                spec_id = spec_data.get('id')
                if spec_id:
                    existing_spec = ProductSpec.query.get(spec_id)
                    if existing_spec and existing_spec.product_id == product_id:
                        existing_spec.field_name = spec_data['field_name']
                        existing_spec.field_value = spec_data['field_value']
                        # 如果是编码规格，更新编码
                        if spec_data.get('field_code'):
                            existing_spec.field_code = spec_data['field_code']
                        # 更新是否纳入描述
                        existing_spec.include_in_description = spec_data.get('include_in_description', False)
                        current_logger.debug(f"更新规格: {spec_data['field_name']} = {spec_data['field_value']}")
                        saved_specs.append(existing_spec)

            else:  # create
                # 创建新规格
                if spec_data.get('field_name', '').strip():
                    new_spec = ProductSpec(
                        product_id=product_id,
                        field_name=spec_data['field_name'],
                        field_value=spec_data.get('field_value', ''),
                        field_code=spec_data.get('field_code') if spec_data.get('field_code') and spec_data.get('field_code') != '0' else None,
                        include_in_description=spec_data.get('include_in_description', False)
                    )
                    db.session.add(new_spec)
                    current_logger.debug(f"添加新规格: {spec_data['field_name']} = {spec_data.get('field_value', '')}")
                    saved_specs.append(new_spec)

        db.session.flush()  # 确保所有更改在同一个事务中
        return (True, saved_specs, None)

    except Exception as e:
        current_logger.error(f"保存产品规格时出错: {str(e)}")
        return (False, [], str(e))

# 产品规格查询API
@bp.route('/api/product/<int:product_id>/specs', methods=['GET'])
@login_required
@permission_required('product', 'view')
def get_product_specs(product_id):
    """
    获取产品的所有规格数据

    Args:
        product_id: 产品ID

    Returns:
        JSON: {
            'specs': [
                {
                    'id': int,
                    'field_name': str,
                    'field_value': str,
                    'field_code': str,
                    'position': int  # 规格在MN编码中的位置
                }
            ]
        }
    """
    try:
        from app.models.product_spec import ProductSpec
        from app.models.product_code import ProductCodeField
        from app.models.product import Product

        # 验证产品存在性
        product = Product.query.get_or_404(product_id)

        # 获取产品规格
        specs = ProductSpec.query.filter_by(product_id=product_id).all()

        # 转换为字典并添加position信息
        spec_list = []
        for spec in specs:
            spec_dict = spec.to_dict()

            # 获取规格字段的position（用于MN编码排序）
            if product.subcategory_id and spec.field_name:
                field = ProductCodeField.query.filter_by(
                    subcategory_id=product.subcategory_id,
                    name=spec.field_name
                ).first()
                if field:
                    spec_dict['position'] = field.position
                else:
                    spec_dict['position'] = 999  # 未找到对应字段，使用默认值
            else:
                spec_dict['position'] = 999

            spec_list.append(spec_dict)

        logger.debug(f"为产品 {product_id} 找到 {len(spec_list)} 个规格")
        return jsonify({'specs': spec_list})

    except Exception as e:
        logger.error(f"获取产品规格失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/products/create', methods=['POST'])
@login_required
@permission_required('product', 'create')  # 添加产品创建权限装饰器
def create_product():
    """创建新产品"""
    try:
        logger.debug('正在创建新产品...')
        
        # 获取表单数据
        product_data = {
            'type': request.form.get('type'),
            'category': request.form.get('category'),
            'product_mn': request.form.get('product_mn'),
            'product_name': request.form.get('product_name'),
            'model': request.form.get('model'),
            'specification': request.form.get('specification'),
            'brand': request.form.get('brand'),
            'unit': request.form.get('unit'),
            'status': request.form.get('status', 'active'),  # 默认为生产中
            'retail_price': request.form.get('retail_price'),
            'currency': request.form.get('currency', 'CNY')  # 默认为人民币
        }
        
        # 验证必填字段
        required_fields = ['product_name', 'model', 'product_mn']
        for field in required_fields:
            if not product_data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field} 字段为必填项'
                }), 400
        
        # 验证MN号唯一性
        existing_product = Product.query.filter_by(product_mn=product_data['product_mn']).first()
        if existing_product:
            return jsonify({
                'success': False,
                'message': f'MN号 {product_data["product_mn"]} 已存在'
            }), 400
        
        # 处理零售价格
        if product_data['retail_price']:
            try:
                product_data['retail_price'] = Decimal(product_data['retail_price'])
            except InvalidOperation:
                return jsonify({
                    'success': False,
                    'message': '零售价格格式不正确'
                }), 400
        else:
            product_data['retail_price'] = Decimal('0.00')
        
        # 只有管理员可以将新产品设置为生产中状态
        if current_user.role == 'admin' and request.form.get('is_active') == 'true':
            product_data['status'] = 'active'
            logger.debug(f'管理员创建产品并设置为生产中状态: {product_data["product_name"]}')
        else:
            product_data['status'] = 'discontinued'
            logger.debug(f'创建产品，默认设置为已停产状态: {product_data["product_name"]}')
        
        # 获取厂商产品标记
        is_vendor_product = request.form.get('is_vendor_product') == 'on'
        
        # 创建新产品
        new_product = Product(
            type=product_data['type'],
            category=product_data['category'],
            product_mn=product_data['product_mn'],
            product_name=product_data['product_name'],
            model=product_data['model'],
            specification=product_data['specification'],
            brand=product_data['brand'],
            unit=product_data['unit'],
            retail_price=product_data['retail_price'],
            currency=product_data['currency'],
            status=product_data['status'],
            is_vendor_product=is_vendor_product,
            owner_id=current_user.id
        )
        
        # 处理产品图片上传到Supabase
        has_image = False
        if 'product_image' in request.files:
            product_image = request.files['product_image']
            if product_image.filename:  # 确保有文件被上传
                logger.debug(f'处理产品图片上传: {product_image.filename}')
                # 使用智能存储系统（自动判断本地/云端环境）
                try:
                    # 先保存产品以获取ID
                    db.session.add(new_product)
                    db.session.flush()  # 获取ID但不提交
                    
                    # 使用Supabase智能存储客户端上传图片
                    supabase_client = get_supabase_client()
                    image_url = supabase_client.upload_product_file(new_product.id, product_image, 'image', 'product')
                    
                    if image_url:
                        new_product.image_path = image_url
                        has_image = True
                        logger.debug(f'产品图片上传成功: {image_url}')
                    else:
                        logger.warning('产品图片上传失败，将创建没有图片的产品')
                except Exception as e:
                    logger.error(f'产品图片上传异常: {str(e)}')
                    logger.warning('图片处理失败，将创建没有图片的产品')
        else:
            logger.debug('没有上传产品图片')
        
        # 处理PDF文件上传（智能选择本地或云端）
        has_pdf = False
        if 'product_pdf' in request.files:
            product_pdf = request.files['product_pdf']
            if product_pdf.filename:  # 确保有文件被上传
                logger.debug(f'处理产品PDF上传: {product_pdf.filename}')
                # 使用智能存储系统（自动判断本地/云端环境）
                try:
                    # 如果产品还没有添加到会话，先添加并flush
                    if new_product not in db.session:
                        db.session.add(new_product)
                        db.session.flush()  # 获取ID但不提交
                    
                    # 使用Supabase智能存储客户端上传PDF
                    supabase_client = get_supabase_client()
                    pdf_url = supabase_client.upload_product_file(new_product.id, product_pdf, 'pdf', 'product')
                    
                    if pdf_url:
                        new_product.pdf_path = pdf_url
                        has_pdf = True
                        logger.debug(f'产品PDF上传成功: {pdf_url}')
                    else:
                        logger.warning('产品PDF上传失败，将创建没有PDF的产品')
                except Exception as e:
                    logger.error(f'产品PDF上传异常: {str(e)}')
                    logger.warning('PDF文件处理失败，将创建没有PDF的产品')
        else:
            logger.debug('没有上传产品PDF文件')
        
        # 保存新产品（如果还没有添加到会话）
        if new_product not in db.session:
            db.session.add(new_product)
        db.session.commit()
        
        logger.info(f'产品创建成功: ID={new_product.id}, MN={new_product.product_mn}, 名称={new_product.product_name}, 有图片={has_image}, 有PDF={has_pdf}')
        
        return jsonify({
            'success': True,
            'message': '产品创建成功',
            'product': {
                'id': new_product.id,
                'product_name': new_product.product_name,
                'product_mn': new_product.product_mn,
                'has_image': has_image,
                'has_pdf': has_pdf
            }
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'创建产品时出错: {str(e)}', exc_info=True)
        return jsonify({
            'success': False,
            'message': f'创建产品失败: {str(e)}'
        }), 500

@bp.route('/products/<int:id>/update', methods=['POST'])
@login_required
@permission_required('product', 'edit')
def update_product(id):
    """更新产品信息（表单提交）"""
    try:
        logger.debug(f'正在更新产品 ID={id}（新版分类体系）...')

        # 查找产品
        product = Product.query.get_or_404(id)

        # 检查权限
        if product.owner_id != current_user.id and current_user.role not in ['admin', 'product_manager']:
            flash('您没有权限编辑此产品', 'error')
            return redirect(url_for('product_route.product_list'))

        # 获取表单数据（新版字段）
        product_type = request.form.get('type') or None
        product_status = request.form.get('status', 'active')
        product_model = request.form.get('product_model')
        brand = request.form.get('brand') or None
        unit = request.form.get('unit')
        retail_price = request.form.get('retail_price')
        currency = request.form.get('currency', 'CNY')
        description = request.form.get('description')

        # 分类字段从表单获取
        category_id = request.form.get('category_id')
        subcategory_id = request.form.get('subcategory_id')
        region_id = request.form.get('region_id') or None

        # 前端已通过disabled属性锁定关键字段，disabled字段不会被提交
        # 因此后端不需要重复检查MN锁定状态，直接信任前端提交的数据即可

        # 验证必填字段
        if not product_model:
            flash('请填写产品型号', 'error')
            return redirect(url_for('product_route.edit_product_page', id=id))

        # 更新产品基本信息
        product.type = product_type
        product.status = product_status
        product.model = product_model
        product.brand = brand
        product.unit = unit
        product.currency = currency
        product.specification = description

        # 更新厂商产品标记（不影响MN编码，允许修改）
        is_vendor_product = request.form.get('is_vendor_product') == 'on'
        if product.is_vendor_product != is_vendor_product:
            product.is_vendor_product = is_vendor_product
            logger.debug(f'厂商产品标记从 {product.is_vendor_product} 更新为 {is_vendor_product}')

        # 更新分类字段（允许补充空值，管理员可以修改已有值）
        if category_id and (not product.category_id or current_user.role == 'admin'):
            product.category_id = int(category_id)
        if subcategory_id and (not product.subcategory_id or current_user.role == 'admin'):
            product.subcategory_id = int(subcategory_id)
        if region_id and (not product.region_id or current_user.role == 'admin'):
            product.region_id = int(region_id)

        # 处理零售价格
        if retail_price:
            try:
                product.retail_price = Decimal(retail_price)
            except (InvalidOperation, ValueError):
                flash('零售价格格式不正确', 'error')
                return redirect(url_for('product_route.edit_product_page', id=id))
        else:
            product.retail_price = Decimal('0.00')

        # 更新规格数据
        # 前端已对编码规格字段禁用（disabled），非编码规格始终可编辑
        spec_names = request.form.getlist('spec_name[]')
        spec_values = request.form.getlist('spec_value[]')
        spec_codes = request.form.getlist('spec_option_codes[]')
        include_in_descriptions = request.form.getlist('include_in_description_indexed[]')

        # 先删除所有现有规格（简单粗暴但可靠的更新方式）
        from app.models.product_spec import ProductSpec
        ProductSpec.query.filter_by(product_id=product.id).delete()
        db.session.flush()

        if spec_names:
            spec_data_list = []
            for i in range(len(spec_names)):
                if spec_names[i].strip():
                    # 获取是否纳入描述的状态，值为 '1' 表示勾选
                    include_in_desc = (i < len(include_in_descriptions) and
                                      include_in_descriptions[i] == '1')
                    spec_data_list.append({
                        'field_name': spec_names[i],
                        'field_value': spec_values[i] if i < len(spec_values) else '',
                        'field_code': spec_codes[i] if i < len(spec_codes) and spec_codes[i] != '0' else None,
                        'include_in_description': include_in_desc,
                        'action': 'create'
                    })

            if spec_data_list:
                # 保存新的规格数据
                success, saved_specs, error = save_product_specs(product.id, spec_data_list)
                if not success:
                    db.session.rollback()
                    flash(f'保存规格数据失败: {error}', 'error')
                    return redirect(url_for('product_route.edit_product_page', id=id))

                # 更新编码定义快照（保存规格成功后）
                from app.utils.product_helpers import generate_product_snapshot
                snapshot = generate_product_snapshot(
                    product=product,
                    source="manual_update"
                )
                if snapshot:
                    product.code_definition_snapshot = snapshot
                    logger.info(f'更新编码快照成功: 产品ID={product.id}')
                else:
                    # 快照更新失败不阻止产品编辑，只记录警告
                    logger.warning(f'快照更新跳过: 产品ID={product.id}（规格数据可能不完整）')

                # 只有在MN未锁定时才更新MN编码（管理员例外）
                if not product.is_mn_locked or current_user.role == 'admin':
                    new_mn = request.form.get('product_mn')
                    if new_mn and new_mn.strip() and new_mn != product.product_mn:
                        # 验证MN唯一性
                        from app.routes.product_management import check_mn_code_duplicate
                        duplicate_info = check_mn_code_duplicate(new_mn, exclude_product_id=product.id)
                        if duplicate_info['exists']:
                            flash(f'MN编号 {new_mn} 已存在，无法更新', 'warning')
                        else:
                            product.product_mn = new_mn
                            logger.info(f'更新产品MN编码: ID={product.id}, 旧MN={product.product_mn} -> 新MN={new_mn}')
                else:
                    logger.debug(f'产品 ID={product.id} MN已锁定，跳过MN编码更新')

        # 提交事务
        db.session.commit()

        logger.info(f'产品更新成功: ID={product.id}, MN={product.product_mn}, 型号={product.model}')
        flash('产品更新成功', 'success')

        return redirect(url_for('product_route.view_product_detail', id=product.id))

    except Exception as e:
        db.session.rollback()
        logger.error(f'更新产品时出错: {str(e)}', exc_info=True)
        flash(f'更新产品失败: {str(e)}', 'error')
        return redirect(url_for('product_route.edit_product_page', id=id))

@bp.route('/api/products/<int:id>/update', methods=['POST'])
@login_required
@permission_required('product', 'edit')  # 添加产品编辑权限装饰器
def update_product_api(id):
    """更新产品信息（JSON API）"""
    try:
        logger.debug(f'正在更新产品 ID={id}...')
        
        # 查找产品
        product = Product.query.get(id)
        if not product:
            return jsonify({
                'success': False,
                'message': f'未找到ID为 {id} 的产品'
            }), 404
        
        # 检查所有权
        if product.owner_id != current_user.id and current_user.role not in ['admin', 'product_manager']:
            logger.warning(f'用户 {current_user.username} 尝试编辑不属于他的产品 {id}')
            return jsonify({
                'success': False,
                'message': '您没有权限编辑此产品'
            }), 403
        
        # 获取表单数据
        product_data = {
            'type': request.form.get('type'),
            'category': request.form.get('category'),
            'product_mn': request.form.get('product_mn'),
            'product_name': request.form.get('product_name'),
            'model': request.form.get('model'),
            'specification': request.form.get('specification'),
            'brand': request.form.get('brand'),
            'unit': request.form.get('unit'),
            'retail_price': request.form.get('retail_price'),
            'currency': request.form.get('currency', 'CNY')  # 默认为人民币
        }
        
        # 只有管理员能修改生产状态
        if current_user.role == 'admin':
            # 直接从表单获取status字段，而不是错误的is_active字段
            status_value = request.form.get('status')
            if status_value in ['active', 'discontinued', 'upcoming']:
                product_data['status'] = status_value
                logger.debug(f"管理员更新产品状态: status={status_value}")
            else:
                # 如果状态值无效，保持原状态
                product_data['status'] = product.status
                logger.debug(f"状态值无效({status_value})，保持原状态: {product_data['status']}")
        else:
            # 非管理员不能修改生产状态，保持原状态
            product_data['status'] = product.status
            logger.debug(f"非管理员用户无法修改产品生产状态，保持原状态: {product_data['status']}")
        
        # 验证必填字段
        required_fields = ['product_name', 'model', 'product_mn']
        for field in required_fields:
            if not product_data.get(field):
                return jsonify({
                    'success': False,
                    'message': f'{field} 字段为必填项'
                }), 400
        
        # 验证MN号唯一性 (排除当前产品)
        if product.product_mn != product_data['product_mn']:
            existing_product = Product.query.filter_by(product_mn=product_data['product_mn']).first()
            if existing_product:
                return jsonify({
                    'success': False,
                    'message': f'MN号 {product_data["product_mn"]} 已存在'
                }), 400
        
        # 处理零售价格
        if product_data['retail_price']:
            try:
                product_data['retail_price'] = Decimal(product_data['retail_price'])
            except InvalidOperation:
                return jsonify({
                    'success': False,
                    'message': '零售价格格式不正确'
                }), 400
        else:
            product_data['retail_price'] = Decimal('0.00')
        
        # 设置数据是否有变化的标志，用于决定是否提交到数据库
        data_changed = False
        
        # 处理产品图片上传（智能选择本地或云端）
        image_changed = False
        if 'product_image' in request.files:
            product_image = request.files['product_image']
            if product_image.filename:  # 确保有文件被上传
                logger.debug(f'处理产品图片上传: {product_image.filename}')
                # 使用智能存储系统（自动判断本地/云端环境）
                try:
                    # 使用Supabase智能存储客户端上传图片
                    supabase_client = get_supabase_client()
                    image_url = supabase_client.upload_product_file(product.id, product_image, 'image', 'product')
                    
                    if image_url:
                        # 如果已有旧图片且是本地路径，删除本地文件
                        if product.image_path and not product.image_path.startswith('http'):
                            old_image_path = os.path.join(UPLOAD_FOLDER, product.image_path)
                            if os.path.exists(old_image_path):
                                try:
                                    os.remove(old_image_path)
                                    logger.info(f"删除旧本地图片: {old_image_path}")
                                except Exception as e:
                                    logger.warning(f"删除旧图片失败: {str(e)}")
                        
                        # 更新图片路径
                        product.image_path = image_url
                        image_changed = True
                        data_changed = True
                        logger.debug(f'产品图片上传成功: {image_url}')
                    else:
                        logger.warning('产品图片上传失败')
                except Exception as e:
                    logger.error(f'产品图片上传异常: {str(e)}')
        
        # 检查是否需要删除图片
        if request.form.get('remove_image') == 'true' and product.image_path:
            logger.debug('删除产品图片')
            try:
                # 使用智能存储系统删除文件（支持本地和云端）
                supabase_client = get_supabase_client()
                
                # 判断文件类型并删除
                if product.image_path.startswith('http'):
                    # 云端文件，使用智能存储删除
                    delete_success = supabase_client.delete_product_file(product.id, 'image', 'product')
                    if delete_success:
                        logger.info(f'云端产品图片删除成功: {product.image_path}')
                    else:
                        logger.warning(f'云端产品图片删除失败: {product.image_path}')
                else:
                    # 本地文件，直接删除
                    image_path = os.path.join(UPLOAD_FOLDER, product.image_path)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                        logger.info(f'本地产品图片删除成功: {image_path}')
                
                # 清空图片路径
                product.image_path = None
                image_changed = True
                data_changed = True
                
            except Exception as e:
                logger.error(f'删除产品图片失败: {str(e)}')
                flash(_('删除图片失败，请重试'), 'warning')
        
        # 处理PDF文件上传（智能选择本地或云端）
        pdf_changed = False
        if 'product_pdf' in request.files:
            product_pdf = request.files['product_pdf']
            if product_pdf.filename:  # 确保有文件被上传
                logger.debug(f'处理产品PDF上传: {product_pdf.filename}')
                # 使用智能存储系统（自动判断本地/云端环境）
                try:
                    # 使用Supabase智能存储客户端上传PDF
                    supabase_client = get_supabase_client()
                    pdf_url = supabase_client.upload_product_file(product.id, product_pdf, 'pdf', 'product')
                    
                    if pdf_url:
                        # 如果已有旧PDF且是本地路径，删除本地文件
                        if product.pdf_path and not product.pdf_path.startswith('http'):
                            old_pdf_path = os.path.join(current_app.static_folder, product.pdf_path)
                            if os.path.exists(old_pdf_path):
                                try:
                                    os.remove(old_pdf_path)
                                    logger.info(f"删除旧本地PDF: {old_pdf_path}")
                                except Exception as e:
                                    logger.warning(f"删除旧PDF失败: {str(e)}")
                        
                        # 更新PDF路径
                        product.pdf_path = pdf_url
                        pdf_changed = True
                        data_changed = True
                        logger.debug(f'产品PDF上传成功: {pdf_url}')
                    else:
                        logger.warning('产品PDF上传失败')
                except Exception as e:
                    logger.error(f'产品PDF上传异常: {str(e)}')
        
        # 检查是否需要删除PDF文件
        if request.form.get('remove_pdf') == 'true' and product.pdf_path:
            logger.debug('删除产品PDF文件')
            try:
                # 使用智能存储系统删除PDF文件（支持本地和云端）
                supabase_client = get_supabase_client()
                
                # 判断文件类型并删除
                if product.pdf_path.startswith('http'):
                    # 云端文件，使用智能存储删除
                    delete_success = supabase_client.delete_product_file(product.id, 'pdf', 'product')
                    if delete_success:
                        logger.info(f'云端产品PDF删除成功: {product.pdf_path}')
                    else:
                        logger.warning(f'云端产品PDF删除失败: {product.pdf_path}')
                else:
                    # 本地文件，直接删除
                    pdf_path = os.path.join(current_app.static_folder, product.pdf_path)
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
                        logger.info(f'本地产品PDF删除成功: {pdf_path}')
                
                # 清空PDF路径
                product.pdf_path = None
                pdf_changed = True
                data_changed = True
                
            except Exception as e:
                logger.error(f'删除产品PDF文件失败: {str(e)}')
                flash(_('删除PDF文件失败，请重试'), 'warning')
        
        # 更新产品信息 - 仅当值发生变化时才更新
        if product.type != product_data['type']:
            product.type = product_data['type']
            data_changed = True

        if product.product_mn != product_data['product_mn']:
            product.product_mn = product_data['product_mn']
            data_changed = True

        if product.model != product_data['model']:
            product.model = product_data['model']
            data_changed = True
            
        if product.specification != product_data['specification']:
            product.specification = product_data['specification']
            data_changed = True
            
        if product.brand != product_data['brand']:
            product.brand = product_data['brand']
            data_changed = True
            
        if product.unit != product_data['unit']:
            product.unit = product_data['unit']
            data_changed = True
            
        # 特殊处理Decimal类型的比较
        current_price = float(product.retail_price) if product.retail_price else 0.0
        new_price = float(product_data['retail_price']) if product_data['retail_price'] else 0.0
        if abs(current_price - new_price) > 0.001:  # 使用小数点精度进行比较
            product.retail_price = product_data['retail_price']
            data_changed = True
        
        # 更新货币类型
        if product.currency != product_data['currency']:
            product.currency = product_data['currency']
            data_changed = True
        
        # 获取厂商产品标记并更新
        is_vendor_product = request.form.get('is_vendor_product') == 'on'
        if product.is_vendor_product != is_vendor_product:
            product.is_vendor_product = is_vendor_product
            data_changed = True
            logger.debug(f'厂商产品标记从 {product.is_vendor_product} 更新为 {is_vendor_product}')
        
        # 更新生产状态 - 只有当用户有权限且状态有变化时才更新
        if product.status != product_data['status']:
            product.status = product_data['status']
            data_changed = True
            logger.info(f'产品状态已更新: ID={product.id}, 新状态={product.status}')
        
        # 如果存在图片变更或任何其他数据变更，则保存更新
        if data_changed or image_changed or pdf_changed:
            logger.info(f'产品数据已变更，正在提交更新: ID={product.id}')
            db.session.commit()
            return jsonify({
                'success': True,
                'message': '产品更新成功',
                'product': {
                    'id': product.id,
                    'product_name': product.name,  # 使用智能属性
                    'product_mn': product.product_mn,
                    'image_updated': image_changed,
                    'pdf_updated': pdf_changed
                }
            })
        else:
            logger.info(f'产品数据未变更，不需要更新: ID={product.id}')
            return jsonify({
                'success': True,
                'message': '产品数据未发生变化',
                'product': {
                    'id': product.id,
                    'product_name': product.name,  # 使用智能属性
                    'product_mn': product.product_mn
                }
            })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新产品时出错: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'更新产品失败: {str(e)}'
        }), 500

@bp.route('/api/products/<int:id>', methods=['GET'])
@login_required
@permission_required('product', 'view')  # 添加产品查看权限装饰器
def get_product(id):
    """获取单个产品详情"""
    try:
        logger.debug(f'正在获取产品详情: ID={id}')
        
        # 查询产品
        product = Product.query.get(id)
        if not product:
            return jsonify({
                'error': '未找到产品',
                'message': f'未找到ID为 {id} 的产品'
            }), 404
        
        # 查询所有者信息
        owner_name = None
        if product.owner_id:
            from app.models.user import User
            owner = User.query.get(product.owner_id)
            if owner:
                # 优先使用真实姓名，如果没有则使用用户名
                owner_name = owner.real_name if owner.real_name else owner.username
        
        # 小数类型转换为浮点数
        def decimal_to_float(obj):
            if isinstance(obj, Decimal):
                return float(obj)
            return obj
        
        # 构建响应数据
        response = {
            'id': product.id,
            'type': product.type,
            'category': product.category_name,  # 使用智能属性
            'product_mn': product.product_mn,
            'product_name': product.name,  # 使用智能属性
            'model': product.model,
            'specification': product.specification,
            'brand': product.brand,
            'unit': product.unit,
            'retail_price': decimal_to_float(product.retail_price) if product.retail_price else 0,
            'currency': product.currency if hasattr(product, 'currency') else 'CNY',
            'status': product.status,
            'is_vendor_product': product.is_vendor_product if hasattr(product, 'is_vendor_product') else False,
            'created_at': product.created_at.strftime('%Y-%m-%d %H:%M:%S') if product.created_at else None,
            'updated_at': product.updated_at.strftime('%Y-%m-%d %H:%M:%S') if product.updated_at else None,
            'owner_id': product.owner_id,
            'owner_name': owner_name,
            'image_path': product.image_path,
            'pdf_path': product.pdf_path
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f'获取产品详情时出错: {str(e)}')
        return jsonify({
            'error': '获取产品详情失败',
            'message': str(e)
        }), 500

@bp.route('/api/products/<int:id>/delete', methods=['POST'])
@login_required
# 注意：不使用 @permission_required 装饰器，因为创建者即使没有模块权限也可以删除自己的产品
def delete_product(id):
    """删除产品API - 创建者或有权限的角色可以删除未被引用的产品"""
    try:
        product = Product.query.get_or_404(id)

        # 权限检查：管理员、产品经理或产品创建者可以删除
        can_delete = (
            current_user.role == 'admin' or
            current_user.role in ['product_manager', 'product'] or
            current_user.has_permission('product', 'delete') or
            (hasattr(product, 'created_by') and product.created_by == current_user.id)
        )

        if not can_delete:
            return jsonify({
                'success': False,
                'message': '您没有权限删除此产品'
            }), 403
        
        # 检查产品是否被报价单引用（按MN编号检查，MN是唯一标识）
        from app.models.quotation import QuotationDetail
        referenced_count = QuotationDetail.query.filter(
            QuotationDetail.product_mn == product.product_mn
        ).count()

        if referenced_count > 0:
            return jsonify({
                'success': False,
                'message': f'该产品（MN: {product.product_mn}）已被 {referenced_count} 个报价单引用，不能删除。如需停产，请使用"停产"功能。',
                'code': 'PRODUCT_REFERENCED'
            }), 400
        
        # 如果产品未被引用，可以删除
        product_name = product.product_name
        
        # 删除产品图片文件（如果存在）
        if product.image_path:
            try:
                image_file_path = os.path.join(current_app.static_folder, product.image_path)
                if os.path.exists(image_file_path):
                    os.remove(image_file_path)
                    logger.debug(f"已删除产品图片文件: {image_file_path}")
            except Exception as e:
                logger.warning(f"删除产品图片文件失败: {str(e)}")
        
        # 删除PDF文件（如果存在）
        if hasattr(product, 'pdf_path') and product.pdf_path:
            try:
                pdf_file_path = os.path.join(current_app.static_folder, product.pdf_path)
                if os.path.exists(pdf_file_path):
                    os.remove(pdf_file_path)
                    logger.debug(f"已删除产品PDF文件: {pdf_file_path}")
            except Exception as e:
                logger.warning(f"删除产品PDF文件失败: {str(e)}")
        
        # 删除产品记录
        db.session.delete(product)
        db.session.commit()
        
        logger.info(f'{current_user.role} {current_user.username} 删除了产品: {product_name} (ID: {id})')
        
        return jsonify({
            'success': True,
            'message': f'产品 {product_name} 删除成功'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'删除产品时出错: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'删除产品失败: {str(e)}'
        }), 500

@bp.route('/api/products/<int:id>/toggle-status', methods=['POST'])
@login_required
@permission_required('product', 'edit')  # 添加产品编辑权限装饰器
def toggle_product_status(id):
    """切换产品状态API - 仅管理员可用"""
    try:
        logger.debug(f'正在切换产品状态: ID={id}')
        
        # 检查用户是否为管理员
        if current_user.role != 'admin':
            logger.warning(f'非管理员用户 {current_user.username} 尝试切换产品状态: ID={id}')
            return jsonify({
                'success': False,
                'message': '只有管理员可以切换产品生产状态'
            }), 403
        
        # 解析请求数据
        data = request.json
        if not data or 'status' not in data:
            return jsonify({
                'success': False,
                'message': '请求数据格式不正确'
            }), 400
            
        # 获取目标状态
        target_status = data['status']
        if target_status not in ['active', 'discontinued']:
            return jsonify({
                'success': False,
                'message': '状态值无效，请使用 active 或 discontinued'
            }), 400
        
        # 查找产品
        product = Product.query.get(id)
        if not product:
            return jsonify({
                'success': False,
                'message': f'未找到ID为 {id} 的产品'
            }), 404
        
        # 如果状态没有变化，直接返回成功
        if product.status == target_status:
            return jsonify({
                'success': True,
                'message': '产品状态未变更',
                'status': target_status
            })
            
        # 更新状态
        product.status = target_status
        db.session.commit()
        
        # 记录操作
        status_text = '已停产' if target_status == 'discontinued' else '生产中'
        logger.info(f'管理员 {current_user.username} 将产品状态更新为 {status_text}: ID={product.id}, 名称={product.product_name}')
        
        return jsonify({
            'success': True,
            'message': f'产品状态已更新为 {status_text}',
            'status': target_status
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'切换产品状态时出错: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'切换产品状态失败: {str(e)}'
        }), 500

@bp.route('/api/products/units', methods=['GET'])
@login_required
@permission_required('product', 'view')  # 添加产品查看权限装饰器
def get_product_units():
    """获取去重后的产品单位列表"""
    try:
        logger.debug('正在获取产品单位列表...')
        # 使用 distinct 获取唯一的单位列表
        units = db.session.query(Product.unit).distinct().filter(
            Product.unit.isnot(None)
        ).all()
        
        # 将结果转换为列表
        unit_list = [unit[0] for unit in units if unit[0]]
        
        # 排序单位列表
        unit_list.sort()
        
        logger.debug(f'找到 {len(unit_list)} 个单位')
        return jsonify(unit_list)
        
    except Exception as e:
        logger.error(f'获取产品单位列表时出错: {str(e)}')
        return jsonify({
            'error': '获取产品单位列表失败',
            'message': str(e)
        }), 500

@bp.route('/api/products/types', methods=['GET'])
@login_required
@permission_required('product', 'view')  # 添加产品查看权限装饰器
def get_product_types():
    """获取产品类型列表，并按规则转换"""
    try:
        logger.debug('正在获取产品类型列表...')
        # 使用 distinct 获取唯一的类型列表
        types = db.session.query(Product.type).distinct().filter(
            Product.type.isnot(None),
            Product.type != ''
        ).all()
        
        # 将结果转换为列表
        type_list = [type_value[0] for type_value in types if type_value[0]]
        
        # 确保列表中有标准类型
        standard_types = {
            '0': '项目产品',
            '1': '渠道产品'
        }
        
        # 处理特殊类型值的转换
        result_types = []
        for type_value in type_list:
            if type_value in standard_types:
                # 如果是特殊值，转换为对应的名称
                result_types.append({
                    'value': type_value,
                    'text': standard_types[type_value]
                })
            else:
                # 保留原始值
                result_types.append({
                    'value': type_value,
                    'text': type_value
                })
        
        logger.debug(f'找到 {len(result_types)} 个产品类型')
        return jsonify(result_types)
        
    except Exception as e:
        logger.error(f'获取产品类型列表时出错: {str(e)}')
        return jsonify({
            'error': '获取产品类型列表失败',
            'message': str(e)
        }), 500

@bp.route('/api/products/brands', methods=['GET'])
@login_required
@permission_required('product', 'view')  # 添加产品查看权限装饰器
def get_product_brands():
    """获取去重后的产品品牌列表"""
    try:
        logger.debug('正在获取产品品牌列表...')
        # 使用 distinct 获取唯一的品牌列表
        brands = db.session.query(Product.brand).distinct().filter(
            Product.brand.isnot(None),
            Product.brand != ''
        ).all()
        
        # 将结果转换为列表
        brand_list = [brand[0] for brand in brands if brand[0]]
        
        # 排序品牌列表
        brand_list.sort()
        
        logger.debug(f'找到 {len(brand_list)} 个品牌')
        return jsonify(brand_list)
        
    except Exception as e:
        logger.error(f'获取产品品牌列表时出错: {str(e)}')
        return jsonify({
            'error': '获取产品品牌列表失败',
            'message': str(e)
        }), 500

@bp.route('/products/<int:id>/detail', methods=['GET'])
@login_required
@permission_required('product', 'view')  # 添加产品查看权限装饰器
def view_product_detail(id):
    """查看产品详情页面"""
    try:
        from app.models.product_spec import ProductSpec
        from app.routes.product_code import get_field_unit

        # 获取产品详情
        product = Product.query.get_or_404(id)

        # 检查产品停产状态的权限：只有产品经理、解决方案经理和管理员可以查看停产产品
        if product.status == 'discontinued' and current_user.role not in ['admin', 'product_manager', 'solution_manager']:
            logger.warning(f"用户 {current_user.username} 尝试查看停产产品详情: {id}")
            flash(_('您没有权限查看已停产的产品'), 'danger')
            return redirect(url_for('product_route.product_list'))

        # 获取产品规格数据（按display_order排序）
        product_specs_objects = ProductSpec.query.filter_by(product_id=id).order_by(ProductSpec.display_order).all()

        # 为每个规格附加单位信息
        product_specs = []
        for spec in product_specs_objects:
            spec_dict = spec.to_dict()
            # 从规格字典获取单位
            spec_dict['unit'] = get_field_unit(spec.field_name)
            product_specs.append(spec_dict)

        return render_template('product/detail.html', product=product, product_specs=product_specs)
    except Exception as e:
        logger.error(f'查看产品详情页面时出错: {str(e)}')
        flash(_('查看产品详情失败: %s') % str(e), 'danger')
        return redirect(url_for('product_route.product_list')) 

@bp.route('/api/products/<int:id>/update-status', methods=['POST'])
@login_required
@permission_required('product', 'edit')  # 添加产品编辑权限装饰器
def update_product_status(id):
    """更新产品状态API - 支持三种状态切换"""
    try:
        logger.debug(f'正在更新产品状态: ID={id}')
        
        # 检查用户是否为管理员
        if current_user.role != 'admin':
            logger.warning(f'非管理员用户 {current_user.username} 尝试更新产品状态: ID={id}')
            return jsonify({
                'success': False,
                'message': '只有管理员可以更新产品状态'
            }), 403
        
        # 解析请求数据
        data = request.json
        if not data or 'status' not in data:
            return jsonify({
                'success': False,
                'message': '请求数据格式不正确'
            }), 400
            
        # 获取目标状态
        target_status = data['status']
        if target_status not in ['active', 'discontinued', 'upcoming']:
            return jsonify({
                'success': False,
                'message': '状态值无效，请使用 active、discontinued 或 upcoming'
            }), 400
        
        # 查找产品
        product = Product.query.get(id)
        if not product:
            return jsonify({
                'success': False,
                'message': f'未找到ID为 {id} 的产品'
            }), 404
        
        # 如果状态没有变化，直接返回成功
        if product.status == target_status:
            return jsonify({
                'success': True,
                'message': '产品状态未变更',
                'status': target_status
            })
            
        # 更新状态
        product.status = target_status
        db.session.commit()
        
        # 记录操作
        status_text = ''
        if target_status == 'active':
            status_text = '生产中'
        elif target_status == 'discontinued':
            status_text = '已停产'
        elif target_status == 'upcoming':
            status_text = '待上市'
            
        logger.info(f'管理员 {current_user.username} 将产品状态更新为 {status_text}: ID={product.id}, 名称={product.product_name}')
        
        return jsonify({
            'success': True,
            'message': f'产品状态已更新为 {status_text}',
            'status': target_status
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'更新产品状态时出错: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'更新产品状态失败: {str(e)}'
        }), 500

# PDF文件下载
@bp.route('/api/products/<int:id>/download-pdf', methods=['GET'])
@login_required
@permission_required('product', 'view')
def download_pdf(id):
    """下载产品PDF文件"""
    file_service = get_product_file_service()
    return file_service.download_pdf(id)



# PDF预览缩略图专用API（用于产品详情页面的小预览图）
@bp.route('/api/products/<int:id>/pdf-preview', methods=['GET'])
@login_required
@permission_required('product', 'view')
def get_pdf_preview(id):
    """获取PDF文件用于预览缩略图（不强制下载，支持PDF.js加载）"""
    file_service = get_product_file_service()
    return file_service.preview_pdf(id)


# ============= 报价单产品级联选择相关API =============

@bp.route('/api/products/subcategories', methods=['GET'])
@login_required
def get_subcategories_api():
    """
    获取指定分类下的所有子分类
    用于报价单产品选择的级联菜单
    """
    try:
        category = request.args.get('category')

        if not category:
            return jsonify({
                'success': False,
                'message': '缺少分类参数'
            }), 400

        # 查询该分类下的所有产品
        from app.models.product_code import ProductCategory

        category_obj = ProductCategory.query.filter_by(name=category).first()
        if not category_obj:
            return jsonify({
                'success': False,
                'message': f'未找到分类: {category}'
            }), 404

        products = Product.query.filter(
            Product.category_id == category_obj.id,
            Product.status == 'active'
        ).all()

        # 统计子分类（支持新旧数据结构，记录display_order用于排序）
        subcategory_data = {}  # {name: {'count': x, 'display_order': y}}
        for product in products:
            # 优先使用新的关联子分类，回退到旧的product_name字段
            if product.subcategory_obj:
                subcategory_name = product.subcategory_obj.name
                display_order = product.subcategory_obj.display_order or 999
            elif product.product_name:
                subcategory_name = product.product_name
                display_order = 999  # 旧数据放在最后
            else:
                continue  # 跳过没有子分类信息的产品

            if subcategory_name not in subcategory_data:
                subcategory_data[subcategory_name] = {
                    'count': 0,
                    'display_order': display_order
                }
            subcategory_data[subcategory_name]['count'] += 1

        # 构建返回结果，按display_order排序
        result = []
        for name, data in sorted(subcategory_data.items(), key=lambda x: x[1]['display_order']):
            result.append({
                'name': name,
                'count': data['count']
            })

        logger.info(f'查询分类 {category} 下的子分类，共 {len(result)} 个')

        return jsonify({
            'success': True,
            'subcategories': result
        })

    except Exception as e:
        logger.error(f'查询子分类时出错: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'查询子分类失败: {str(e)}'
        }), 500


@bp.route('/api/products/by-subcategory', methods=['GET'])
@login_required
def get_products_by_subcategory_api():
    """
    获取指定分类和子分类下的所有产品，按型号分组
    用于报价单产品选择：显示型号列表，每个型号下可能有多个产品
    注意：不返回product_desc字段（按需求隐藏描述）
    """
    try:
        category = request.args.get('category')
        subcategory = request.args.get('subcategory')

        if not category or not subcategory:
            return jsonify({
                'success': False,
                'message': '缺少分类或子分类参数'
            }), 400

        # 查询所有产品（支持新旧数据结构）
        from app.models.product_code import ProductSubcategory, ProductCategory

        # 先查询该分类下的生产中产品（排除停产和待上市）
        category_obj = ProductCategory.query.filter_by(name=category).first()
        if not category_obj:
            return jsonify({
                'success': False,
                'message': f'未找到分类: {category}'
            }), 404

        all_products = Product.query.filter(
            Product.category_id == category_obj.id,
            Product.status == 'active'
        ).all()

        # 在Python中过滤子分类（支持新旧数据）
        products = []
        for product in all_products:
            product_subcategory = None
            if product.subcategory_obj:
                product_subcategory = product.subcategory_obj.name
            elif product.product_name:
                product_subcategory = product.product_name

            if product_subcategory == subcategory:
                products.append(product)

        # 按型号分组
        model_groups = {}
        for product in products:
            # 使用model字段作为型号
            model = product.model or product.product_name or '未知型号'

            if model not in model_groups:
                model_groups[model] = []

            # 获取产品配置数量
            from app.models.product_relation import ProductRelation
            config_relations = ProductRelation.get_relations_for_product(product.id)
            config_count = len(config_relations)

            # 构建产品数据
            product_data = {
                'id': product.id,
                'product_name': product.product_name,
                'model': product.model,
                'product_mn': product.product_mn,
                'specification': product.specification,
                'brand': product.brand,
                'unit': product.unit,
                'retail_price': float(product.retail_price) if product.retail_price else None,
                'currency': product.currency,
                'status': product.status,
                'code_definition_snapshot': product.code_definition_snapshot,
                'image_path': product.image_path,
                'config_count': config_count,
                'has_configurations': config_count > 0
            }

            model_groups[model].append(product_data)

        # 构建返回结果
        result = []
        for model, products_list in model_groups.items():
            result.append({
                'model': model,
                'count': len(products_list),
                'products': products_list
            })

        # 按型号名称排序
        result.sort(key=lambda x: x['model'])

        logger.info(f'查询 {category}/{subcategory} 下的产品，共 {len(result)} 个型号，{len(products)} 个产品')

        return jsonify({
            'success': True,
            'model_groups': result
        })

    except Exception as e:
        logger.error(f'查询产品按子分类时出错: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'查询产品失败: {str(e)}'
        }), 500


@bp.route('/api/products/<int:product_id>/configurations', methods=['GET'])
@login_required
@permission_required('product', 'view')
def get_product_configurations(product_id):
    """
    获取指定产品的配置列表

    根据产品ID获取其关联的配置产品（配件、附件等）
    按产品名称分组返回

    Args:
        product_id: 产品ID

    Returns:
        JSON格式的配置列表，按产品名称分组
    """
    try:
        from app.models.product import Product
        from app.models.product_relation import ProductRelation

        # 验证产品是否存在
        product = Product.query.get(product_id)
        if not product:
            return jsonify({
                'success': False,
                'message': '产品不存在'
            }), 404

        # 获取产品的关联配置
        relations = ProductRelation.get_relations_for_product(product_id)

        # 按产品名称分组配置
        config_groups = {}
        for relation in relations:
            if relation.related_product and relation.related_product.status == 'active':
                related_prod = relation.related_product
                product_name = related_prod.product_name or '其他配置'

                if product_name not in config_groups:
                    config_groups[product_name] = []

                config_groups[product_name].append({
                    'id': related_prod.id,
                    'model': related_prod.model,
                    'product_mn': related_prod.product_mn,
                    'specification': related_prod.specification,
                    'product_name': related_prod.product_name,
                    'brand': related_prod.brand,
                    'unit': related_prod.unit,
                    'retail_price': float(related_prod.retail_price) if related_prod.retail_price else None,
                    'currency': related_prod.currency,
                    'relation_type': relation.relation_type,
                    'is_required': relation.is_required,
                    'default_quantity': relation.default_quantity
                })

        # 转换为列表格式
        configurations = []
        for product_name, items in config_groups.items():
            configurations.append({
                'product_name': product_name,
                'items': items
            })

        logger.info(f'获取产品 {product_id} 的配置，共 {len(configurations)} 个分组')

        return jsonify({
            'success': True,
            'configurations': configurations
        })

    except Exception as e:
        logger.error(f'获取产品配置时出错: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'获取配置失败: {str(e)}'
        }), 500 