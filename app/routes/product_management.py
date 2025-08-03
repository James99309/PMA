from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app, send_file
from flask_babel import gettext as _
from flask_login import login_required, current_user
from app import db
from app.models.product_code import ProductCategory, ProductSubcategory, ProductCodeField, ProductCodeFieldOption, ProductRegion
from app.models.dev_product import DevProduct, DevProductSpec
from app.permissions import admin_required, product_manager_required, permission_required
from sqlalchemy.exc import IntegrityError
from datetime import datetime
import random
import string
import logging
import time
import os
import uuid
from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload
import re

# 创建日志记录器
logger = logging.getLogger(__name__)

# 序列修复工具函数
def fix_table_sequence(table_name):
    """修复指定表的序列"""
    try:
        from sqlalchemy import text
        result = db.session.execute(text(f'SELECT COALESCE(MAX(id), 0) FROM {table_name}')).scalar()
        max_id = result if result is not None else 0
        next_id = max_id + 1
        db.session.execute(text(f"ALTER SEQUENCE {table_name}_id_seq RESTART WITH {next_id}"))
        db.session.commit()
        logger.info(f"表 {table_name} 的序列已修复，重置为 {next_id}")
        return True
    except Exception as e:
        logger.error(f"修复表 {table_name} 序列失败: {str(e)}")
        return False

# 创建蓝图
product_management_bp = Blueprint('product_management', __name__, url_prefix='/product-management')

# 通用权限检查函数
def check_product_access(product, current_user):
    """检查用户是否有权限访问产品"""
    if current_user.role == 'admin':
        return True
    if product.created_by == current_user.id:
        return True
    
    # 检查权限等级
    from app.models.role_permissions import RolePermission
    role_permission = RolePermission.query.filter_by(
        role=current_user.role, 
        module='product_code'
    ).first()
    
    if role_permission:
        permission_level = role_permission.permission_level
        if permission_level == 'system':
            return True
        elif permission_level == 'company':
            return product.creator and product.creator.company == current_user.company
        elif permission_level == 'department':
            return product.creator and product.creator.department == current_user.department
    
    return False

# 允许的图片扩展名
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# 允许的PDF扩展名
ALLOWED_PDF_EXTENSIONS = {'pdf'}

# 检查文件扩展名是否允许
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 检查PDF文件扩展名是否允许
def allowed_pdf_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_PDF_EXTENSIONS

# 检查文件大小是否在限制内（12MB）
def check_file_size(file):
    """检查文件大小是否在12MB以内"""
    file.seek(0, 2)  # 移动到文件末尾
    file_size = file.tell()  # 获取文件大小
    file.seek(0)  # 重置文件指针
    return file_size <= 12 * 1024 * 1024  # 12MB

# 添加英文文件名验证函数
def validate_english_filename(filename):
    """验证文件名是否为英文字符（字母、数字、点、下划线、连字符）"""
    return re.match(r'^[a-zA-Z0-9._-]+$', filename) is not None

# 保存上传的产品图片
def save_product_image(file):
    """
    保存上传的产品图片
    
    参数:
    - file: 上传的文件对象
    
    返回:
    - 成功时返回保存的文件路径，失败时返回None
    """
    if file and allowed_file(file.filename):
        # 检查文件大小（最大5MB）
        file.seek(0, 2)  # 移动到文件末尾
        file_size = file.tell()  # 获取文件大小
        file.seek(0)  # 重置文件指针
        if file_size > 5 * 1024 * 1024:  # 5MB
            logger.warning(f"图片文件过大: {file_size} bytes (最大5MB)")
            return None
        
        # 处理文件名，支持中文字符
        original_filename = file.filename
        # 获取文件扩展名
        if '.' in original_filename:
            name_part, extension = original_filename.rsplit('.', 1)
            extension = extension.lower()
        else:
            name_part = original_filename
            extension = 'jpg'  # 默认扩展名
        
        # 生成唯一文件名，保留原始文件名（包括中文）
        # 移除文件名中的特殊字符，但保留中文、英文、数字、下划线、连字符
        safe_name = re.sub(r'[^\w\u4e00-\u9fff\-_.]', '_', name_part)
        unique_filename = f"{uuid.uuid4().hex}_{safe_name}.{extension}"
        
        # 确保上传目录存在
        upload_folder = os.path.join(current_app.static_folder, 'uploads', 'products')
        os.makedirs(upload_folder, exist_ok=True)
        
        # 保存文件
        filepath = os.path.join(upload_folder, unique_filename)
        file.save(filepath)
        
        # 返回相对路径
        return os.path.join('uploads', 'products', unique_filename)
    
    return None

# 保存上传的产品PDF文件
def save_product_pdf(file):
    """
    保存上传的产品PDF文件
    
    参数:
    - file: 上传的文件对象
    
    返回:
    - 成功时返回保存的文件路径，失败时返回None
    """
    if file and allowed_pdf_file(file.filename):
        # 检查文件大小
        if not check_file_size(file):
            return None, "PDF文件大小不能超过12MB"
        
        # 处理文件名，支持中文字符
        original_filename = file.filename
        # 获取文件扩展名
        if '.' in original_filename:
            name_part, extension = original_filename.rsplit('.', 1)
            extension = extension.lower()
        else:
            name_part = original_filename
            extension = 'pdf'
        
        # 生成唯一文件名，保留原始文件名（包括中文）
        # 移除文件名中的特殊字符，但保留中文、英文、数字、下划线、连字符
        safe_name = re.sub(r'[^\w\u4e00-\u9fff\-_.]', '_', name_part)
        unique_filename = f"{uuid.uuid4().hex}_{safe_name}.{extension}"
        
        # 确保上传目录存在
        upload_folder = os.path.join(current_app.static_folder, 'uploads', 'products', 'pdfs')
        os.makedirs(upload_folder, exist_ok=True)
        
        # 保存文件
        filepath = os.path.join(upload_folder, unique_filename)
        file.save(filepath)
        
        # 返回相对路径
        return os.path.join('uploads', 'products', 'pdfs', unique_filename), None
    
    return None, "无效的PDF文件格式"

# 产品管理首页 - 展示研发产品库列表
@product_management_bp.route('/', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def index():
    try:
        # 获取搜索和筛选参数
        search = request.args.get('search', '').strip()
        category_filter = request.args.get('category_filter', '')
        status_filter = request.args.get('status_filter', '')
        creator_filter = request.args.get('creator_filter', '')
        
        # 获取用户的权限等级
        from app.models.role_permissions import RolePermission
        from app.models.user import Permission, User
        
        # 构建基础查询
        query = DevProduct.query.options(
            joinedload(DevProduct.category),
            joinedload(DevProduct.subcategory),
            joinedload(DevProduct.creator)
        )
        
        # 权限控制
        if current_user.role != 'admin':
            # 检查用户权限等级
            permission_level = 'personal'  # 默认个人级别
            
            # 检查角色权限
            role_permission = RolePermission.query.filter_by(
                role=current_user.role, 
                module='product_code'
            ).first()
            if role_permission:
                permission_level = role_permission.permission_level
            
            # 根据权限等级限制查询范围
            if permission_level == 'system':
                # 系统级权限：查看所有产品 - 不添加额外限制
                pass
            elif permission_level == 'company':
                # 公司级权限：查看同公司的产品
                query = query.join(DevProduct.creator).filter(
                    DevProduct.creator.has(company=current_user.company)
                )
            elif permission_level == 'department':
                # 部门级权限：查看同部门的产品
                query = query.join(DevProduct.creator).filter(
                    DevProduct.creator.has(department=current_user.department)
                )
            else:
                # 个人级权限：只能查看自己创建的产品
                query = query.filter_by(created_by=current_user.id)
        
        # 应用搜索筛选
        if search:
            query = query.filter(
                db.or_(
                    DevProduct.model.ilike(f'%{search}%'),
                    DevProduct.mn_code.ilike(f'%{search}%'),
                    DevProduct.description.ilike(f'%{search}%')
                )
            )
        
        if category_filter:
            query = query.filter(DevProduct.category_id == category_filter)
        
        if status_filter:
            query = query.filter(DevProduct.status == status_filter)
        
        if creator_filter:
            query = query.filter(DevProduct.created_by == creator_filter)
        
        # 获取总数据
        total_products = query.count()
        products = query.order_by(DevProduct.created_at.desc()).all()
        
        # 获取分类列表用于筛选
        categories = ProductCategory.query.all()
        
        # 获取实际存在的产品分类（基于当前权限范围内的数据）
        actual_categories = db.session.query(ProductCategory).join(
            DevProduct, DevProduct.category_id == ProductCategory.id
        ).filter(DevProduct.id.in_([p.id for p in query.all()])).distinct().all()
        
        # 获取实际存在的创建者列表（基于当前权限范围内的数据）
        creators = User.query.filter(
            User.id.in_([p.created_by for p in query.all() if p.created_by])
        ).all()
        
        # 获取实际存在的状态选项（基于当前权限范围内的数据）
        actual_statuses = db.session.query(DevProduct.status).filter(
            DevProduct.id.in_([p.id for p in query.all()])
        ).distinct().all()
        
        status_options = []
        for status_tuple in actual_statuses:
            status = status_tuple[0]
            if status:  # 确保状态不为空
                status_options.append({
                    'value': status, 
                    'label': status, 
                    'translate': False
                })
        
        # 计算统计数据（基于当前权限范围）
        all_products_count = query.count()
        development_products = query.filter(DevProduct.status == '研发中').count()
        completed_products = query.filter(DevProduct.status == '已入库').count()
        research_products = query.filter(DevProduct.status == '调研中').count()
        planning_products = query.filter(DevProduct.status == '立项中').count()
        
        # 筛选配置
        filter_config = {
            'action_url': url_for('product_management.index'),
            'form_id': 'productFilterForm',
            'reset_url': url_for('product_management.index'),
            'search_field': {
                'name': 'search',
                'label': _('搜索'),
                'placeholder': _('产品型号、MN编码或描述'),
                'value': search,
                'col_width': 4
            },
            'filter_fields': [
                {
                    'name': 'category_filter',
                    'label': _('产品分类'),
                    'all_option_text': _('全部分类'),
                    'current_value': category_filter,
                    'col_width': 2,
                    'options': [
                        {'value': str(cat.id), 'label': cat.name, 'translate': False}
                        for cat in actual_categories
                    ]
                },
                {
                    'name': 'status_filter',
                    'label': _('产品状态'),
                    'all_option_text': _('全部状态'),
                    'current_value': status_filter,
                    'col_width': 2,
                    'options': status_options
                },
                {
                    'name': 'creator_filter',
                    'label': _('创建者'),
                    'all_option_text': _('全部创建者'),
                    'current_value': creator_filter,
                    'col_width': 2,
                    'options': [
                        {'value': str(user.id), 'label': user.real_name or user.username, 'translate': False}
                        for user in creators
                    ]
                }
            ],
            'search_button_text': _('搜索'),
            'reset_button_text': _('重置')
        }
        
        # 通用列表组件配置
        list_config = {
            'module_name': 'product_management',
            'title': _('研发产品库'),
            'ajax_mode': True,
            
            # 统计卡片配置
            'stats': {
                'cards': [
                    {
                        'id': 'total',
                        'title': _('全部产品'),
                        'icon': 'fas fa-cube',
                        'value': all_products_count,
                        'unit': _('个'),
                        'color': 'primary',
                        'clickable': True,
                        'click_params': {},  # 清空筛选条件显示全部
                        'data_key': 'total'
                    },
                    {
                        'id': 'development',
                        'title': _('研发中'),
                        'icon': 'fas fa-cogs',
                        'value': development_products,
                        'unit': _('个'),
                        'color': 'warning',
                        'clickable': True,
                        'click_params': {'status_filter': '研发中'},
                        'data_key': 'development'
                    },
                    {
                        'id': 'completed',
                        'title': _('已入库'),
                        'icon': 'fas fa-check-circle',
                        'value': completed_products,
                        'unit': _('个'),
                        'color': 'success',
                        'clickable': True,
                        'click_params': {'status_filter': '已入库'},
                        'data_key': 'completed'
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
                'show_header': True,
                'enhanced_striping': True,  # 启用增强斑马纹
                'ajax_endpoint': url_for('product_management.products_list_ajax'),
                'columns': [
                    {
                        'key': 'category',
                        'label': _('产品分类'),
                        'type': 'text',
                        'width': '120px'
                    },
                    {
                        'key': 'subcategory',
                        'label': _('子分类'),
                        'type': 'text',
                        'width': '120px'
                    },
                    {
                        'key': 'model',
                        'label': _('产品型号'),
                        'type': 'link',
                        'url_template': '/product-management/{id}',
                        'width': '150px'
                    },
                    {
                        'key': 'mn_code',
                        'label': _('MN编码'),
                        'type': 'text',
                        'width': '120px'
                    },
                    {
                        'key': 'status',
                        'label': _('产品状态'),
                        'type': 'badge',
                        'render': 'render_dev_product_status_badge',
                        'width': '100px'
                    },
                    {
                        'key': 'creator',
                        'label': _('创建者'),
                        'type': 'text',
                        'width': '100px'
                    },
                    {
                        'key': 'created_at',
                        'label': _('创建时间'),
                        'type': 'date',
                        'format': '%Y-%m-%d',
                        'width': '120px'
                    }
                ]
            }
        }
        
        return render_template('product_management/index.html',
                              products=products,
                              list_config=list_config)
                              
    except Exception as e:
        logger.error(f"加载研发产品库列表时出错: {str(e)}", exc_info=True)
        
        # 创建错误时的默认配置
        error_list_config = {
            'module_name': 'product_management',
            'title': _('研发产品库'),
            'ajax_mode': False,
            'stats': {
                'cards': [
                    {
                        'id': 'total',
                        'title': _('全部产品'),
                        'icon': 'fas fa-cube',
                        'value': 0,
                        'unit': _('个'),
                        'color': 'primary',
                        'clickable': False,
                        'data_key': 'total'
                    }
                ]
            },
            'filter': {
                'action_url': url_for('product_management.index'),
                'form_id': 'productFilterForm',
                'reset_url': url_for('product_management.index'),
                'search_field': {
                    'name': 'search',
                    'label': _('搜索'),
                    'placeholder': _('产品型号、MN编码或描述'),
                    'value': '',
                    'col_width': 4
                },
                'filter_fields': [],
                'search_button_text': _('搜索'),
                'reset_button_text': _('重置')
            },
            'table': {
                'columns': [],
                'actions': [
                    {
                        'text': _('新增产品'),
                        'href': url_for('product_management.new_product'),
                        'color': 'primary',
                        'icon': 'fas fa-plus'
                    }
                ]
            }
        }
        
        return render_template('product_management/index.html',
                              products=[],
                              list_config=error_list_config)

# AJAX筛选端点
@product_management_bp.route('/api/products/filter', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def products_list_ajax():
    """研发产品库列表AJAX筛选API"""
    try:
        # 获取搜索和筛选参数
        search = request.args.get('search', '').strip()
        category_filter = request.args.get('category_filter', '')
        status_filter = request.args.get('status_filter', '')
        creator_filter = request.args.get('creator_filter', '')
        
        # 分页参数
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        # 限制每次加载数量范围
        limit = max(10, min(limit, 100))
        
        from app.models.role_permissions import RolePermission
        from app.models.user import User
        
        # 构建基础查询
        query = DevProduct.query.options(
            joinedload(DevProduct.category),
            joinedload(DevProduct.subcategory),
            joinedload(DevProduct.creator)
        )
        
        # 权限控制
        if current_user.role != 'admin':
            permission_level = 'personal'
            role_permission = RolePermission.query.filter_by(
                role=current_user.role, 
                module='product_code'
            ).first()
            if role_permission:
                permission_level = role_permission.permission_level
            
            if permission_level == 'system':
                pass
            elif permission_level == 'company':
                query = query.join(DevProduct.creator).filter(
                    DevProduct.creator.has(company=current_user.company)
                )
            elif permission_level == 'department':
                query = query.join(DevProduct.creator).filter(
                    DevProduct.creator.has(department=current_user.department)
                )
            else:
                query = query.filter_by(created_by=current_user.id)
        
        # 应用搜索筛选
        if search:
            query = query.filter(
                db.or_(
                    DevProduct.model.ilike(f'%{search}%'),
                    DevProduct.mn_code.ilike(f'%{search}%'),
                    DevProduct.description.ilike(f'%{search}%')
                )
            )
        
        if category_filter:
            query = query.filter(DevProduct.category_id == category_filter)
        
        if status_filter:
            query = query.filter(DevProduct.status == status_filter)
        
        if creator_filter:
            query = query.filter(DevProduct.created_by == creator_filter)
        
        # 获取总数和分页数据
        total_count = query.count()
        products = query.order_by(DevProduct.created_at.desc()).offset(offset).limit(limit).all()
        
        # 为统计数据创建基础查询（不包含分页）
        base_query = DevProduct.query.options(
            joinedload(DevProduct.category),
            joinedload(DevProduct.subcategory),
            joinedload(DevProduct.creator)
        )
        
        # 应用相同的权限控制
        if current_user.role != 'admin':
            permission_level = 'personal'
            role_permission = RolePermission.query.filter_by(
                role=current_user.role, 
                module='product_code'
            ).first()
            if role_permission:
                permission_level = role_permission.permission_level
            
            if permission_level == 'system':
                pass
            elif permission_level == 'company':
                base_query = base_query.join(DevProduct.creator).filter(
                    DevProduct.creator.has(company=current_user.company)
                )
            elif permission_level == 'department':
                base_query = base_query.join(DevProduct.creator).filter(
                    DevProduct.creator.has(department=current_user.department)
                )
            else:
                base_query = base_query.filter_by(created_by=current_user.id)
        
        # 渲染HTML片段
        html_rows = []
        for product in products:
            # 格式化产品数据
            creator_name = '-'
            if product.creator:
                creator_name = product.creator.real_name or product.creator.username
            
            created_at = product.created_at.strftime('%Y-%m-%d') if product.created_at else '-'
            
            # 产品状态徽章
            status_badge = ''
            if product.status:
                status_map = {
                    '调研中': '<span class="badge badge-pill badge-transparent product-status-research">调研中</span>',
                    '立项中': '<span class="badge badge-pill badge-transparent product-status-planning">立项中</span>',
                    '研发中': '<span class="badge badge-pill badge-transparent product-status-development">研发中</span>',
                    '已入库': '<span class="badge badge-pill badge-transparent product-status-completed">已入库</span>',
                    '已停产': '<span class="badge badge-pill badge-transparent product-status-discontinued">已停产</span>'
                }
                status_badge = status_map.get(product.status, f'<span class="badge badge-pill badge-transparent badge-muted">{product.status}</span>')
            else:
                status_badge = '<span class="badge badge-pill badge-transparent badge-muted">未设置</span>'
            
            html_row = f"""
            <tr>
                <td>{product.category.name if product.category else '-'}</td>
                <td>{product.subcategory.name if product.subcategory else '-'}</td>
                <td><a href="/product-management/{product.id}" class="text-primary text-decoration-none">{product.model}</a></td>
                <td><code class="text-muted">{product.mn_code or ''}</code></td>
                <td>{status_badge}</td>
                <td>{creator_name}</td>
                <td class="text-muted">{created_at}</td>
            </tr>
            """
            html_rows.append(html_row)
        
        # 计算是否还有更多数据
        has_more = (offset + limit) < total_count
        
        return jsonify({
            'success': True,
            'html': '\n'.join(html_rows),
            'has_more': has_more,
            'total_count': total_count,
            'loaded_count': offset + len(products),
            'statistics': {
                'total': base_query.count(),
                'development': base_query.filter(DevProduct.status == '研发中').count(),
                'completed': base_query.filter(DevProduct.status == '已入库').count()
            }
        })
        
    except Exception as e:
        logger.error(f"AJAX筛选产品列表时出错: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '加载产品列表失败',
            'html': '<tr><td colspan="7" class="text-center text-muted py-4">加载数据时出错</td></tr>',
            'has_more': False,
            'total_count': 0,
            'loaded_count': 0
        }), 500

# 新增产品
@product_management_bp.route('/new', methods=['GET'])
@login_required
@permission_required('product_code', 'create')
def new_product():
    # 获取所有产品分类
    categories = ProductCategory.query.all()
    # 获取所有状态选项
    statuses = ['调研中', '立项中', '研发中']
    
    return render_template('product_management/new_product.html', 
                           categories=categories,
                           statuses=statuses)

# 获取子分类API
@product_management_bp.route('/api/category/<int:category_id>/subcategories', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def get_subcategories(category_id):
    # 修改查询，按照display_order升序排序
    subcategories = ProductSubcategory.query.filter_by(category_id=category_id).order_by(ProductSubcategory.display_order).all()
    return jsonify({
        'subcategories': [
            {'id': sub.id, 'name': sub.name, 'code_letter': sub.code_letter, 'display_order': sub.display_order}
            for sub in subcategories
        ]
    })

# 获取销售区域选项API
@product_management_bp.route('/api/region-options', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def get_region_options():
    try:
        # 从ProductCodeField中获取销售区域 (field_type='origin_location')
        regions = ProductCodeField.query.filter_by(field_type='origin_location').order_by(ProductCodeField.position).all()
        
        regions_data = []
        for field in regions:
            # 获取编码，优先从字段的code属性，其次从字段的选项中获取
            code = getattr(field, 'code', None)
            if not code or code == "?":
                option = ProductCodeFieldOption.query.filter_by(field_id=field.id).first()
                if option:
                    code = option.code
                else:
                    code = "0"  # 默认编码
            
            regions_data.append({
                'id': field.id,
                'name': field.name,
                'code': code
            })
        
        current_app.logger.debug(f"返回 {len(regions_data)} 个销售区域选项: {regions_data}")
        return jsonify({'regions': regions_data})
    except Exception as e:
        current_app.logger.error(f"获取销售区域选项出错: {str(e)}")
        return jsonify({'regions': [], 'error': str(e)}), 500

# 生成MN编码
def generate_mn_code(category, subcategory, region_code):
    # MN编码格式：XYZ XXXXX 
    # X: 分类编码, Y: 子分类编码, Z: 销售区域编码, XXXXX: 5位自动生成的唯一标识符
    
    # 生成5位随机字符（大写字母+数字）
    chars = string.ascii_uppercase + string.digits
    unique_part = ''.join(random.choice(chars) for _ in range(5))
    
    # 构建MN编码
    mn_code = f"{category.code_letter}{subcategory.code_letter}{region_code}{unique_part}"
    
    # 检查是否已存在，如果存在则重新生成
    while DevProduct.query.filter_by(mn_code=mn_code).first():
        unique_part = ''.join(random.choice(chars) for _ in range(5))
        mn_code = f"{category.code_letter}{subcategory.code_letter}{region_code}{unique_part}"
    
    return mn_code

# 辅助函数：检查规格字段是否有特定选项，如果没有则添加
def add_spec_option_if_not_exists(field_id, option_value, product_model):
    """
    检查规格字段是否已包含指定的选项值，如果没有则添加
    
    参数:
    - field_id: 规格字段ID
    - option_value: 选项值
    - product_model: 产品型号，用于描述信息
    
    返回:
    - 如果已存在匹配选项，返回该选项ID
    - 如果不存在并成功添加，返回新选项ID
    - 如果添加失败，返回None
    """
    try:
        # 检查是否已存在相同值的选项
        existing_option = ProductCodeFieldOption.query.filter_by(
            field_id=field_id, 
            value=option_value
        ).first()
        
        if existing_option:
            return existing_option.id
        
        # 获取字段信息，确认是规格字段
        field = ProductCodeField.query.get(field_id)
        if not field or field.field_type != 'spec':
            logger.warning(f"字段ID {field_id} 不是有效的规格字段")
            return None
        
        # 查找当前最大排序位置
        max_position = db.session.query(db.func.max(ProductCodeFieldOption.position))\
            .filter_by(field_id=field_id).scalar() or 0
        
        # 生成一个唯一编码
        # 首先查询该字段的现有选项编码
        existing_options = ProductCodeFieldOption.query.filter_by(field_id=field_id).all()
        existing_codes = [opt.code for opt in existing_options]
        
        # 尝试使用数字编码（规格值通常使用数字编码）
        # 检查是否是数值型规格值
        try:
            numeric_value = float(option_value.replace(',', ''))
            is_numeric = True
        except (ValueError, AttributeError):
            is_numeric = False
        
        unique_code = None
        
        # 对于数值型规格，尝试使用数值编码
        if is_numeric:
            # 尝试使用短编码 (1-9)
            for code in range(1, 10):
                if str(code) not in existing_codes:
                    unique_code = str(code)
                    break
                    
            # 如果短编码不可用，尝试使用A-Z
            if not unique_code:
                for code in string.ascii_uppercase:
                    if code not in existing_codes:
                        unique_code = code
                        break
        else:
            # 对于文本型规格，首选使用首字母
            if option_value and isinstance(option_value, str):
                first_letter = option_value[0].upper()
                if first_letter.isalpha() and first_letter not in existing_codes:
                    unique_code = first_letter
            
            # 如果首字母不可用，尝试使用A-Z
            if not unique_code:
                for code in string.ascii_uppercase:
                    if code not in existing_codes:
                        unique_code = code
                        break
            
            # 如果字母不可用，尝试使用数字
            if not unique_code:
                for code in range(1, 10):
                    if str(code) not in existing_codes:
                        unique_code = str(code)
                        break
        
        # 如果所有尝试都失败，使用一个替代方案
        if not unique_code:
            # 尝试使用两位数或两个字符的代码
            for prefix in string.ascii_uppercase:
                for suffix in range(1, 10):
                    code = f"{prefix}{suffix}"
                    if code not in existing_codes:
                        unique_code = code
                        break
                if unique_code:
                    break
            
            # 如果仍然找不到唯一编码，使用 "X" + 时间戳后两位作为最后手段
            if not unique_code:
                timestamp = int(time.time()) % 100  # 获取时间戳后两位
                unique_code = f"X{timestamp:02d}"
                logger.warning(f"为字段ID {field_id} 使用时间戳生成编码: {unique_code}")
        
        # 创建新选项
        new_option = ProductCodeFieldOption(
            field_id=field_id,
            value=option_value,
            code=unique_code,
            description=f"从产品 {product_model} 自动添加的规格值",
            position=max_position + 1
        )
        db.session.add(new_option)
        db.session.flush()  # 获取新ID但不提交事务
        
        logger.info(f"为字段 '{field.name}' 添加新规格选项: '{option_value}' (编码: {unique_code})")
        return new_option.id
    except Exception as e:
        logger.error(f"添加规格选项失败: {str(e)}")
        return None

# MN编号重复检查函数
def check_mn_code_duplicate_internal(mn_code, exclude_dev_product_id=None):
    """
    检查MN编号是否在研发产品库和标准产品库中重复
    
    Args:
        mn_code: 要检查的MN编号
        exclude_dev_product_id: 排除的研发产品ID（用于编辑时排除当前产品）
    
    Returns:
        dict: {'is_duplicate': bool, 'dev_products': [], 'standard_products': []}
    """
    if not mn_code:
        return {'is_duplicate': False, 'dev_products': [], 'standard_products': []}
    
    logger = logging.getLogger(__name__)
    
    try:
        duplicate_dev_products = []
        duplicate_standard_products = []
        
        # 检查研发产品库
        dev_query = DevProduct.query.filter(DevProduct.mn_code == mn_code)
        if exclude_dev_product_id:
            dev_query = dev_query.filter(DevProduct.id != exclude_dev_product_id)
        
        dev_duplicates = dev_query.all()
        
        for product in dev_duplicates:
            duplicate_dev_products.append({
                'id': product.id,
                'model': product.model,
                'name': product.name,
                'status': product.status,
                'category': product.category.name if product.category else '未知',
                'subcategory': product.subcategory.name if product.subcategory else '未知',
                'created_at': product.created_at.strftime('%Y-%m-%d %H:%M:%S') if product.created_at else '未知',
                'creator': product.creator.username if product.creator else '未知',
                'mn_code': product.mn_code,
                'source': '研发产品库'
            })
        
        # 检查标准产品库
        from app.models.product import Product
        standard_duplicates = Product.query.filter(Product.product_mn == mn_code).all()
        
        for product in standard_duplicates:
            duplicate_standard_products.append({
                'id': product.id,
                'model': product.model,
                'name': product.product_name,
                'status': product.status,
                'category': product.category,
                'type': product.type,
                'created_at': product.created_at.strftime('%Y-%m-%d %H:%M:%S') if product.created_at else '未知',
                'owner': product.owner.username if product.owner else '未知',
                'mn_code': product.product_mn,
                'source': '标准产品库'
            })
        
        is_duplicate = len(duplicate_dev_products) > 0 or len(duplicate_standard_products) > 0
        
        if is_duplicate:
            logger.warning(f"检测到MN编号 {mn_code} 重复，研发产品: {len(duplicate_dev_products)}个, 标准产品: {len(duplicate_standard_products)}个")
        
        return {
            'is_duplicate': is_duplicate,
            'dev_products': duplicate_dev_products,
            'standard_products': duplicate_standard_products,
            'total_duplicates': len(duplicate_dev_products) + len(duplicate_standard_products)
        }
        
    except Exception as e:
        logger.error(f"检查MN编号重复时出错: {str(e)}")
        return {'is_duplicate': False, 'dev_products': [], 'standard_products': [], 'error': str(e)}

# 添加规格选项（使用指定编码）
def add_spec_option_with_code(field_id, option_value, option_code, product_model):
    """添加规格选项，使用指定的编码"""
    logger = logging.getLogger(__name__)
    
    try:
        # 检查字段是否存在
        field = ProductCodeField.query.get(field_id)
        if not field:
            logger.error(f"字段ID {field_id} 不存在")
            return None
        
        # 检查选项是否已存在
        existing_option = ProductCodeFieldOption.query.filter_by(
            field_id=field_id,
            value=option_value
        ).first()
        
        if existing_option:
            logger.info(f"选项 '{option_value}' 已存在于字段 '{field.name}'")
            return existing_option.id
        
        # 检查编码是否已被使用
        existing_code = ProductCodeFieldOption.query.filter_by(
            field_id=field_id,
            code=option_code
        ).first()
        
        if existing_code:
            logger.warning(f"编码 '{option_code}' 已被字段 '{field.name}' 的选项 '{existing_code.value}' 使用")
            # 如果编码已被使用，回退到自动编码
            return add_spec_option_if_not_exists(field_id, option_value, product_model)
        
        # 获取最大position
        max_position = db.session.query(db.func.max(ProductCodeFieldOption.position))\
            .filter_by(field_id=field_id).scalar() or 0
        
        # 创建新选项
        new_option = ProductCodeFieldOption(
            field_id=field_id,
            value=option_value,
            code=option_code,
            description=f"从产品 {product_model} 自动添加的规格值 (动态编码)",
            position=max_position + 1
        )
        db.session.add(new_option)
        db.session.flush()  # 获取新ID但不提交事务
        
        logger.info(f"为字段 '{field.name}' 添加新规格选项: '{option_value}' (动态编码: {option_code})")
        return new_option.id
    except Exception as e:
        logger.error(f"添加规格选项失败: {str(e)}")
        return None

# 保存新产品
@product_management_bp.route('/save', methods=['POST'])
@login_required
@permission_required('product_code', 'create')
def save():
    """保存新产品"""
    try:
        # 调试: 打印完整表单数据
        current_app.logger.debug(f"表单数据: {request.form}")
        current_app.logger.debug(f"表单字段名: {list(request.form.keys())}")
        current_app.logger.debug(f"spec_value[]字段: {request.form.getlist('spec_value[]')}")
        current_app.logger.debug(f"spec_name[]字段: {request.form.getlist('spec_name[]')}")
        
        # 获取表单数据
        category_id = request.form.get('category_id')
        subcategory_id = request.form.get('subcategory_id')
        region_id = request.form.get('region_id')
        name = request.form.get('name') or ""
        model = request.form.get('model')
        description = request.form.get('description') or ""
        unit = request.form.get('unit') or ""
        retail_price = request.form.get('retail_price')
        currency = request.form.get('currency', 'CNY')  # 获取货币类型，默认为人民币
        status = request.form.get('status', '研发中')
        no_update_mn = request.form.get('no_update_mn') == 'true'  # 检查是否不更新MN编码
        
        # 验证必填字段
        if not all([category_id, subcategory_id, model]):
            flash('请填写所有必填字段', 'danger')
            return redirect(url_for('product_management.new_product'))
        
        # 获取分类和子分类信息
        category = ProductCategory.query.get(category_id)
        subcategory = ProductSubcategory.query.get(subcategory_id)
        
        if not category or not subcategory:
            flash('无效的产品分类', 'danger')
            return redirect(url_for('product_management.new_product'))
        
        # 产品名称默认使用型号
        if not name:
            name = model
        
        # 获取区域编码
        region_code = '0'  # 默认为0
        if region_id:
            # 获取区域选项
            region_options = ProductCodeFieldOption.query.filter_by(id=region_id).first()
            if region_options:
                region_code = region_options.code
            else:
                current_app.logger.warning(f"无法找到区域选项ID {region_id}的编码，使用默认值'0'")
        
        # 生成MN编码
        mn_code = None
        if not no_update_mn:  # 只有在需要更新MN编码时才生成
            # 修改为使用完整MN编码格式（包含规格编码）
            # 获取表单提交的规格代码和规格值
            spec_option_codes = request.form.getlist('spec_option_codes[]')
            spec_values = request.form.getlist('spec_value[]')
            spec_field_ids = request.form.getlist('spec_field_ids[]')
            current_app.logger.debug(f"获取到的规格编码: {spec_option_codes}")
            current_app.logger.debug(f"获取到的规格值: {spec_values}")
            current_app.logger.debug(f"获取到的规格字段ID: {spec_field_ids}")
            
            # 获取规格字段的位置信息，按position排序
            spec_position_data = []
            for i, field_id in enumerate(spec_field_ids):
                if field_id and i < len(spec_option_codes):
                    field = ProductCodeField.query.get(field_id)
                    if field:
                        spec_position_data.append({
                            'position': field.position,
                            'code': spec_option_codes[i] if spec_option_codes[i] else '0'
                        })
                        current_app.logger.debug(f"规格字段 {field.name} (ID: {field_id}) 位置: {field.position}, 编码: {spec_option_codes[i] if spec_option_codes[i] else '0'}")
            
            # 按position排序
            spec_position_data.sort(key=lambda x: x['position'])
            
            # 提取排序后的编码，映射到MN编码位置4-13
            spec_codes = []
            for i, spec_data in enumerate(spec_position_data[:10]):  # 最多10个规格位置
                spec_codes.append(spec_data['code'])
                current_app.logger.debug(f"规格顺序 {i + 1} (数据库位置 {spec_data['position']}) -> MN位置 {4 + i}, 编码: {spec_data['code']}")
            
            # 构建MN编码时去掉末尾的'0'
            # 找到最后一个非'0'编码的位置
            last_non_zero_index = -1
            for i in range(len(spec_codes) - 1, -1, -1):
                if spec_codes[i] != '0':
                    last_non_zero_index = i
                    break
            
            # 只使用到最后一个有效编码的部分
            if last_non_zero_index >= 0:
                effective_spec_codes = spec_codes[:last_non_zero_index + 1]
            else:
                effective_spec_codes = []  # 如果都是'0'，则不包含规格编码
            
            current_app.logger.debug(f"有效规格编码序列: {effective_spec_codes}")
            
            # 完整MN编码格式，去掉末尾的'0'
            mn_code = f"{category.code_letter}{subcategory.code_letter}{region_code}{''.join(effective_spec_codes)}"
            current_app.logger.debug(f"生成的完整MN编码: {mn_code}")
            
            # 检查MN编号是否重复
            duplicate_check = check_mn_code_duplicate_internal(mn_code)
            if duplicate_check['is_duplicate']:
                # 构建重复产品信息字符串
                duplicate_info = []
                for product in duplicate_check['dev_products']:
                    duplicate_info.append(f"研发产品库: {product['name']} (型号: {product['model']}, 状态: {product['status']}, 创建者: {product['creator']}, 创建时间: {product['created_at']})")
                for product in duplicate_check['standard_products']:
                    duplicate_info.append(f"标准产品库: {product['name']} (型号: {product['model']}, 状态: {product['status']}, 拥有者: {product['owner']}, 创建时间: {product['created_at']})")
                
                duplicate_message = f"MN编号 {mn_code} 已存在重复产品！\\n\\n重复产品详细信息:\\n" + "\\n".join(duplicate_info)
                flash(duplicate_message, 'danger')
                return redirect(url_for('product_management.new_product'))
        else:
            current_app.logger.debug("用户选择不更新MN编码")
        
        # 处理图片上传
        image_path = None
        if 'product_image' in request.files:
            file = request.files['product_image']
            if file.filename:
                image_path = save_product_image(file)
                if not image_path:
                    current_app.logger.warning("图片上传失败或格式不支持")
        
        # 处理PDF文件上传
        pdf_path = None
        pdf_error = None
        if 'product_pdf' in request.files:
            file = request.files['product_pdf']
            if file.filename:
                pdf_path, pdf_error = save_product_pdf(file)
                if pdf_error:
                    flash(pdf_error, 'danger')
                    return redirect(url_for('product_management.new_product'))
                elif not pdf_path:
                    current_app.logger.warning("PDF文件上传失败或格式不支持")
        
        # 创建新的研发产品
        new_product = DevProduct(
            category_id=category_id,
            subcategory_id=subcategory_id,
            region_id=region_id if region_id else None,
            name=name,
            model=model,
            description=description,
            unit=unit,
            retail_price=retail_price if retail_price else None,
            currency=currency,  # 添加货币字段
            status=status,
            mn_code=mn_code,  # 可能为None，表示不设置MN编码
            image_path=image_path,
            pdf_path=pdf_path,  # 添加PDF文件路径
            created_by=current_user.id
        )
        
        # 先保存产品到数据库获取ID
        db.session.add(new_product)
        db.session.commit()
        
        current_app.logger.debug(f"新产品ID: {new_product.id}")
        
        # 记录创建历史
        try:
            from app.utils.change_tracker import ChangeTracker
            ChangeTracker.log_create(new_product)
        except Exception as track_err:
            current_app.logger.warning(f"记录产品创建历史失败: {str(track_err)}")
        
        # 处理所有规格数据
        try:
            # 1. 收集现有规格数据 (spec_name[] + spec_value[] + spec_option_codes[])
            spec_names = request.form.getlist('spec_name[]')
            spec_values = request.form.getlist('spec_value[]')
            spec_option_codes = request.form.getlist('spec_option_codes[]')
            
            # 2. 收集新增规格数据 (new_spec_names[] + new_option_values[])
            new_spec_names = request.form.getlist('new_spec_names[]')
            new_option_values = request.form.getlist('new_option_values[]')
            
            # 3. 合并所有规格数据
            all_specs = []
            
            # 记录日志
            current_app.logger.debug(f"规格名称: {spec_names}")
            current_app.logger.debug(f"规格值: {spec_values}")
            current_app.logger.debug(f"规格编码: {spec_option_codes}")
            current_app.logger.debug(f"新增规格: {new_spec_names}")
            current_app.logger.debug(f"新增选项: {new_option_values}")
            
            # 合并规格数据
            for i in range(len(spec_names)):
                if i < len(spec_values) and spec_names[i].strip() and spec_values[i].strip():
                    spec_code = spec_option_codes[i] if i < len(spec_option_codes) else '0'
                    all_specs.append({
                        'field_name': spec_names[i].strip(),
                        'field_value': spec_values[i].strip(),
                        'field_code': spec_code,
                        'is_new': False
                    })
            
            # 合并新规格数据        
            for i in range(len(new_spec_names)):
                if i < len(new_option_values) and new_spec_names[i].strip() and new_option_values[i].strip():
                    all_specs.append({
                        'field_name': new_spec_names[i].strip(),
                        'field_value': new_option_values[i].strip(),
                        'field_code': '0',
                        'is_new': True
                    })
            
            # 查找现有规格字段
            existing_fields = ProductCodeField.query.filter_by(
                subcategory_id=subcategory_id,
                field_type='spec'
            ).all()
            existing_names = {field.name.lower(): field for field in existing_fields}
            
            # 打印准备保存的规格数据
            current_app.logger.debug(f"准备保存 {len(all_specs)} 个规格")
            
            # 保存规格数据
            saved_specs = []
            
            for spec in all_specs:
                spec_name = spec['field_name']
                spec_value = spec['field_value']
                spec_code = spec['field_code']
                
                current_app.logger.debug(f"保存规格: {spec_name} = {spec_value} (编码: {spec_code})")
                
                try:
                    # 创建产品规格记录
                    new_spec = DevProductSpec(
                        dev_product_id=new_product.id,
                        field_name=spec_name,
                        field_value=spec_value
                    )
                    db.session.add(new_spec)
                    db.session.flush()  # 保存规格获取ID
                    saved_specs.append(new_spec)
                    
                    # 检查是否需要创建或更新规格字段
                    spec_lower = spec_name.lower()
                    if spec_lower not in existing_names:
                        # 创建新规格字段
                        max_pos = db.session.query(db.func.max(ProductCodeField.position))\
                            .filter_by(subcategory_id=subcategory_id).scalar() or 0
                        
                        new_field = ProductCodeField(
                            subcategory_id=subcategory_id,
                            name=spec_name,
                            field_type='spec',
                            description=f'从产品 {model} 自动添加的规格字段',
                            position=max_pos + 1,
                            max_length=1,
                            is_required=False,
                            use_in_code=False  # 产品中新增的规格默认不纳入编码
                        )
                        db.session.add(new_field)
                        db.session.flush()
                        
                        # 添加规格选项，如果有动态编码则使用动态编码
                        if spec_value:
                            if spec_code and spec_code != '0':
                                # 使用动态编码创建选项
                                option_id = add_spec_option_with_code(new_field.id, spec_value, spec_code, model)
                                current_app.logger.info(f"为字段 '{spec_name}' 添加新规格选项: '{spec_value}' (动态编码: {spec_code})")
                            else:
                                # 使用自动编码创建选项
                                option_id = add_spec_option_if_not_exists(new_field.id, spec_value, model)
                                current_app.logger.info(f"为字段 '{spec_name}' 添加新规格选项: '{spec_value}' (自动编码)")
                            
                            # 检索选项对象以获取编码
                            if option_id:
                                option = ProductCodeFieldOption.query.get(option_id)
                                if option:
                                    new_spec.field_code = option.code
                                    current_app.logger.debug(f"已设置规格 '{spec_name}' 的编码为: {option.code}")
                        
                        # 更新已有字段字典
                        existing_names[spec_lower] = new_field
                    else:
                        # 为现有字段添加选项
                        field = existing_names[spec_lower]
                        
                        if spec_code and spec_code != '0':
                            # 使用动态编码创建选项
                            option_id = add_spec_option_with_code(field.id, spec_value, spec_code, model)
                            current_app.logger.info(f"为现有字段 '{spec_name}' 添加新规格选项: '{spec_value}' (动态编码: {spec_code})")
                        else:
                            # 使用自动编码创建选项
                            option_id = add_spec_option_if_not_exists(field.id, spec_value, model)
                            current_app.logger.info(f"为现有字段 '{spec_name}' 添加新规格选项: '{spec_value}' (自动编码)")
                        
                        # 检索选项对象以获取编码
                        if option_id:
                            option = ProductCodeFieldOption.query.get(option_id)
                            if option:
                                new_spec.field_code = option.code
                                current_app.logger.debug(f"已设置规格 '{spec_name}' 的编码为: {option.code}")
                except Exception as e:
                    current_app.logger.error(f"保存规格 '{spec_name}' 时出错: {str(e)}")
                    # 继续处理其他规格
            
            # 提交所有规格数据
            db.session.commit()
            
            # 验证规格是否成功保存
            saved_specs_db = DevProductSpec.query.filter_by(dev_product_id=new_product.id).all()
            current_app.logger.info(f"为产品 ID:{new_product.id} 保存了 {len(saved_specs_db)} 个规格: {[spec.field_name for spec in saved_specs_db]}")
            current_app.logger.info(f"规格详情: {[(spec.id, spec.field_name, spec.field_value) for spec in saved_specs_db]}")
            
            if not saved_specs_db:
                current_app.logger.warning(f"产品 ID:{new_product.id} 没有保存任何规格，尽管尝试保存了: {[spec.field_name for spec in saved_specs]}")
                # 检查数据库表是否存在问题
                db_error = None
                try:
                    test_spec = DevProductSpec(
                        dev_product_id=new_product.id,
                        field_name="测试规格",
                        field_value="测试值"
                    )
                    db.session.add(test_spec)
                    db.session.commit()
                    current_app.logger.info(f"测试规格保存成功，ID: {test_spec.id}")
                except Exception as e:
                    db_error = str(e)
                    current_app.logger.error(f"数据库测试规格保存失败: {db_error}")
                    db.session.rollback()
            
            # 成功保存，重定向到产品列表
            flash(_('新产品已成功添加到研发产品库，自定义规格字段也已同步到产品分类模块'), 'success')
            return redirect(url_for('product_management.index'))
            
        except IntegrityError as spec_error:
            # 规格保存时的完整性错误
            db.session.rollback()
            if 'duplicate key value violates unique constraint' in str(spec_error) and 'dev_product_specs_pkey' in str(spec_error):
                current_app.logger.warning(f"检测到规格表主键序列问题，尝试修复: {str(spec_error)}")
                if fix_table_sequence('dev_product_specs'):
                    flash(f'产品已保存，规格表序列已修复。请编辑产品重新添加规格。', 'warning')
                else:
                    flash(f'产品已保存，但规格保存失败，数据库序列错误: {str(spec_error)}', 'warning')
            else:
                current_app.logger.error(f"规格保存数据完整性错误: {str(spec_error)}")
                flash(f'产品已保存，但规格保存失败，数据完整性错误: {str(spec_error)}', 'warning')
            return redirect(url_for('product_management.index'))
        except Exception as spec_error:
            # 规格保存出错，但产品已成功保存
            current_app.logger.error(f"规格保存错误: {spec_error}")
            db.session.rollback()  # 回滚规格保存操作
            flash(f'产品已保存，但规格保存失败: {str(spec_error)}', 'warning')
            return redirect(url_for('product_management.index'))
            
    except IntegrityError as e:
        db.session.rollback()
        # 检查是否是主键重复错误
        if 'duplicate key value violates unique constraint' in str(e) and 'dev_products_pkey' in str(e):
            current_app.logger.warning(f"检测到主键序列问题，尝试修复: {str(e)}")
            if fix_table_sequence('dev_products'):
                flash('数据库序列已修复，请重新提交表单', 'warning')
            else:
                flash(f'创建产品失败，数据库序列错误: {str(e)}', 'danger')
        else:
            current_app.logger.error(f"数据完整性错误: {str(e)}")
            flash(f'创建产品失败，数据完整性错误: {str(e)}', 'danger')
        return redirect(url_for('product_management.new_product'))
    except Exception as e:
        # 主要保存错误
        current_app.logger.error(f"创建产品失败: {str(e)}")
        db.session.rollback()
        flash(f'创建产品失败: {str(e)}', 'danger')
        return redirect(url_for('product_management.new_product'))

# 编辑产品
@product_management_bp.route('/<int:id>/edit', methods=['GET'])
@login_required
@permission_required('product_code', 'edit')
def edit_product(id):
    from sqlalchemy.orm import joinedload
    
    # 使用joinedload减少查询次数
    product = db.session.query(DevProduct).options(
        joinedload(DevProduct.category),
        joinedload(DevProduct.subcategory),
        joinedload(DevProduct.region)
    ).filter_by(id=id).first_or_404()
    
    if not check_product_access(product, current_user):
        flash(_('您没有权限编辑此产品'), 'danger')
        return redirect(url_for('product_management.index'))
    
    # 获取所有产品分类和状态
    categories = db.session.query(ProductCategory).order_by(ProductCategory.name).all()
    subcategories = db.session.query(ProductSubcategory).filter_by(category_id=product.category_id).order_by(ProductSubcategory.name).all()
    statuses = ['调研中', '立项中', '研发中', '申请入库', '已入库']
    
    # 获取产品规格并添加详细日志
    specs_db = db.session.query(DevProductSpec).filter_by(dev_product_id=id).all()
    current_app.logger.debug(f"为产品 {id} 找到 {len(specs_db)} 个规格: {[(spec.id, spec.field_name, spec.field_value) for spec in specs_db]}")
    
    if not specs_db:
        # 尝试通过ORM关系获取规格
        product_specs = product.specs if hasattr(product, 'specs') else []
        current_app.logger.debug(f"通过ORM关系获取规格，找到 {len(product_specs)} 个规格")
        specs_db = product_specs
    
    # 将DevProductSpec对象转换为可JSON序列化的字典列表
    specs = [
        {
            'field_name': spec.field_name,
            'field_value': spec.field_value
        } for spec in specs_db
    ]
    
    return render_template(
        'product_management/edit_product.html', 
        dev_product=product, 
        specs=specs,
        categories=categories,
        subcategories=subcategories,
        statuses=statuses
    )

# 更新产品
@product_management_bp.route('/<int:id>/update', methods=['POST'])
@login_required
@permission_required('product_code', 'edit')
def update_product(id):
    dev_product = DevProduct.query.get_or_404(id)
    
    if not check_product_access(dev_product, current_user):
        flash(_('您没有权限更新此产品'), 'danger')
        return redirect(url_for('product_management.index'))
    
    try:
        # 捕获修改前的值
        from app.utils.change_tracker import ChangeTracker
        old_values = ChangeTracker.capture_old_values(dev_product)
        
        # 更新基本信息
        dev_product.name = request.form.get('name')
        dev_product.model = request.form.get('model')
        dev_product.description = request.form.get('description', '')
        dev_product.unit = request.form.get('unit', '')
        
        retail_price = request.form.get('retail_price', '')
        dev_product.retail_price = float(retail_price) if retail_price else None
        
        # 更新货币字段
        currency = request.form.get('currency', 'CNY')
        dev_product.currency = currency
        
        dev_product.status = request.form.get('status', '研发中')
        dev_product.updated_at = datetime.now()
        
        # 检查是否需要更新MN编码
        no_update_mn = request.form.get('no_update_mn') == 'true'
        
        # 如果前端请求不更新MN编码，则不修改现有MN编码
        if no_update_mn:
            current_app.logger.debug(f"保留现有MN编码: {dev_product.mn_code}")
        else:
            # 重新计算MN编码
            category = ProductCategory.query.get(dev_product.category_id)
            subcategory = ProductSubcategory.query.get(dev_product.subcategory_id)
            
            # 获取区域编码
            region_code = '0'  # 默认为0
            if dev_product.region_id:
                region_options = ProductCodeFieldOption.query.filter_by(id=dev_product.region_id).first()
                if region_options:
                    region_code = region_options.code
            
            # 获取规格编码（从产品关联的规格中获取）
            spec_codes = []
            specs = DevProductSpec.query.filter_by(dev_product_id=id).all()
            
            # 按规格名称确定位置，构建规格编码数组
            position_codes = ['0'] * 10  # 初始化10个位置都是'0'
            
            # 定义规格名称到位置的映射
            spec_position_mapping = {
                '频率范围': 0,  # 第4位
                '带宽': 1,      # 第5位
                '功率': 2,      # 第6位
                '阻抗': 3,      # 第7位
                '电源类型': 4   # 第8位
            }
            
            for spec in specs:
                if spec.field_code and spec.field_name in spec_position_mapping:
                    position_index = spec_position_mapping[spec.field_name]
                    if 0 <= position_index < 10:
                        position_codes[position_index] = spec.field_code
            
            # 构建MN编码时去掉末尾的'0'
            # 找到最后一个非'0'编码的位置
            last_non_zero_index = -1
            for i in range(len(position_codes) - 1, -1, -1):
                if position_codes[i] != '0':
                    last_non_zero_index = i
                    break
            
            # 只使用到最后一个有效编码的部分
            if last_non_zero_index >= 0:
                effective_spec_codes = position_codes[:last_non_zero_index + 1]
            else:
                effective_spec_codes = []  # 如果都是'0'，则不包含规格编码
            
            # 生成新的MN编码，去掉末尾的'0'
            new_mn_code = f"{category.code_letter}{subcategory.code_letter}{region_code}{''.join(effective_spec_codes)}"
            current_app.logger.debug(f"更新MN编码: {dev_product.mn_code} -> {new_mn_code}")
            
            # 检查新MN编号是否重复（排除当前产品）
            duplicate_check = check_mn_code_duplicate_internal(new_mn_code, exclude_dev_product_id=dev_product.id)
            if duplicate_check['is_duplicate']:
                # 构建重复产品信息字符串
                duplicate_info = []
                for product in duplicate_check['dev_products']:
                    duplicate_info.append(f"研发产品库: {product['name']} (型号: {product['model']}, 状态: {product['status']}, 创建者: {product['creator']}, 创建时间: {product['created_at']})")
                for product in duplicate_check['standard_products']:
                    duplicate_info.append(f"标准产品库: {product['name']} (型号: {product['model']}, 状态: {product['status']}, 拥有者: {product['owner']}, 创建时间: {product['created_at']})")
                
                duplicate_message = f"MN编号 {new_mn_code} 已存在重复产品！\\n\\n重复产品详细信息:\\n" + "\\n".join(duplicate_info)
                flash(duplicate_message, 'danger')
                return redirect(url_for('product_management.edit_product', id=id))
            
            dev_product.mn_code = new_mn_code
        
        # 处理图片上传
        if 'product_image' in request.files:
            file = request.files['product_image']
            if file.filename:
                # 保存新图片
                image_path = save_product_image(file)
                if image_path:
                    # 如果已有旧图片，可以选择删除
                    if dev_product.image_path:
                        old_image_path = os.path.join(current_app.static_folder, dev_product.image_path)
                        if os.path.exists(old_image_path):
                            try:
                                os.remove(old_image_path)
                            except Exception as e:
                                current_app.logger.warning(f"删除旧图片失败: {str(e)}")
                    
                    # 更新图片路径
                    dev_product.image_path = image_path
                else:
                    current_app.logger.warning("更新图片上传失败或格式不支持")
        
        # 处理PDF文件上传
        if 'product_pdf' in request.files:
            file = request.files['product_pdf']
            if file.filename:
                # 保存新PDF文件
                pdf_path, pdf_error = save_product_pdf(file)
                if pdf_error:
                    flash(pdf_error, 'danger')
                    return redirect(url_for('product_management.edit_product', id=id))
                elif pdf_path:
                    # 如果已有旧PDF文件，删除它
                    if dev_product.pdf_path:
                        old_pdf_path = os.path.join(current_app.static_folder, dev_product.pdf_path)
                        if os.path.exists(old_pdf_path):
                            try:
                                os.remove(old_pdf_path)
                            except Exception as e:
                                current_app.logger.warning(f"删除旧PDF文件失败: {str(e)}")
                    
                    # 更新PDF文件路径
                    dev_product.pdf_path = pdf_path
                else:
                    current_app.logger.warning("更新PDF文件上传失败或格式不支持")
        
        # 处理规格字段
        # 1. 处理删除的规格
        deleted_spec_ids = request.form.getlist('deleted_spec_ids[]')
        if deleted_spec_ids:
            for spec_id in deleted_spec_ids:
                if spec_id:
                    spec_to_delete = DevProductSpec.query.get(spec_id)
                    if spec_to_delete and spec_to_delete.dev_product_id == id:
                        # 只能删除非编码规格（没有field_code的规格）
                        if not spec_to_delete.field_code or spec_to_delete.field_code.strip() == '':
                            db.session.delete(spec_to_delete)
                            current_app.logger.debug(f"删除非编码规格: {spec_to_delete.field_name}")
        
        # 2. 处理现有规格的更新
        existing_spec_ids = request.form.getlist('existing_spec_ids[]')
        spec_names = request.form.getlist('spec_name[]')
        spec_values = request.form.getlist('indicator_values[]')
        spec_codes = request.form.getlist('indicator_codes[]')
        
        for i in range(len(existing_spec_ids)):
            if existing_spec_ids[i] and i < len(spec_names) and i < len(spec_values):
                existing_spec = DevProductSpec.query.get(existing_spec_ids[i])
                if existing_spec and existing_spec.dev_product_id == id:
                    # 更新规格数据
                    existing_spec.field_name = spec_names[i]
                    existing_spec.field_value = spec_values[i]
                    
                    # 如果是编码规格，更新编码
                    if existing_spec.field_code and i < len(spec_codes):
                        existing_spec.field_code = spec_codes[i]
                    
                    current_app.logger.debug(f"更新规格: {spec_names[i]} = {spec_values[i]}")
        
        # 3. 处理新增的规格（没有existing_spec_ids的）
        for i in range(len(spec_names)):
            # 如果这个索引没有对应的existing_spec_id，说明是新增的
            if (i >= len(existing_spec_ids) or not existing_spec_ids[i]) and spec_names[i].strip():
                # 创建新的非编码规格
                new_spec = DevProductSpec(
                    dev_product_id=dev_product.id,
                    field_name=spec_names[i],
                    field_value=spec_values[i] if i < len(spec_values) else '',
                    field_code=None  # 非编码规格没有编码
                )
                db.session.add(new_spec)
                current_app.logger.debug(f"添加新非编码规格: {spec_names[i]} = {spec_values[i] if i < len(spec_values) else ''}")
        
        # 提交更改
        db.session.commit()
        
        # 记录变更历史
        try:
            new_values = ChangeTracker.get_new_values(dev_product, old_values.keys())
            ChangeTracker.log_update(dev_product, old_values, new_values)
        except Exception as track_err:
            current_app.logger.warning(f"记录产品变更历史失败: {str(track_err)}")
        
        flash(_('产品更新成功！'), 'success')
        return redirect(url_for('product_management.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(_('更新产品失败: %s') % str(e), 'danger')
        return redirect(url_for('product_management.edit_product', id=id))

# 删除产品
@product_management_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('product_code', 'delete')
def delete_product(id):
    dev_product = DevProduct.query.get_or_404(id)
    
    if not check_product_access(dev_product, current_user):
        flash(_('您没有权限删除此产品'), 'danger')
        return redirect(url_for('product_management.index'))
    
    try:
        # 记录删除历史
        try:
            from app.utils.change_tracker import ChangeTracker
            ChangeTracker.log_delete(dev_product)
        except Exception as track_err:
            current_app.logger.warning(f"记录产品删除历史失败: {str(track_err)}")
        
        # 删除关联的规格记录
        DevProductSpec.query.filter_by(dev_product_id=id).delete()
        
        # 删除产品记录
        db.session.delete(dev_product)
        db.session.commit()
        
        flash(_('产品已成功删除'), 'success')
    except Exception as e:
        db.session.rollback()
        flash(_('删除产品失败: %s') % str(e), 'danger')
    
    return redirect(url_for('product_management.index'))

# 批量删除产品
@product_management_bp.route('/batch-delete', methods=['POST'])
@login_required
@permission_required('product_code', 'delete')
def batch_delete_products():
    # 获取产品ID列表
    product_ids_str = request.form.get('product_ids', '')
    
    if not product_ids_str:
        flash(_('未选择要删除的产品'), 'warning')
        return redirect(url_for('product_management.index'))
    
    # 将逗号分隔的ID字符串拆分为列表
    try:
        product_ids = [int(id_str) for id_str in product_ids_str.split(',') if id_str.strip()]
    except ValueError:
        flash('无效的产品ID', 'danger')
        return redirect(url_for('product_management.index'))
    
    if not product_ids:
        flash('未选择有效的产品ID', 'warning')
        return redirect(url_for('product_management.index'))
    
    # 查询这些产品
    dev_products = DevProduct.query.filter(DevProduct.id.in_(product_ids)).all()
    
    # 计数器
    successful_count = 0
    failed_count = 0
    unauthorized_count = 0
    
    for product in dev_products:
        if not check_product_access(product, current_user):
            unauthorized_count += 1
            continue
        
        try:
            # 记录删除历史
            try:
                from app.utils.change_tracker import ChangeTracker
                ChangeTracker.log_delete(product)
            except Exception as track_err:
                current_app.logger.warning(f"记录产品删除历史失败: {str(track_err)}")
            
            # 删除关联的规格记录
            DevProductSpec.query.filter_by(dev_product_id=product.id).delete()
            
            # 删除产品记录
            db.session.delete(product)
            successful_count += 1
        except Exception as e:
            current_app.logger.error(f"批量删除产品 {product.id} 失败: {str(e)}")
            failed_count += 1
    
    # 提交所有更改
    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        flash(f'提交批量删除更改失败: {str(e)}', 'danger')
        return redirect(url_for('product_management.index'))
    
    # 显示结果消息
    if successful_count > 0:
        flash(_('成功删除 %d 个产品') % successful_count, 'success')
    
    if unauthorized_count > 0:
        flash(_('您没有权限删除其中的 %d 个产品') % unauthorized_count, 'warning')
    
    if failed_count > 0:
        flash(f'删除 {failed_count} 个产品时发生错误', 'danger')
    
    return redirect(url_for('product_management.index'))

# 申请入库
@product_management_bp.route('/<int:id>/apply', methods=['POST'])
@login_required
@permission_required('product_code', 'edit')
def apply_product(id):
    dev_product = DevProduct.query.get_or_404(id)
    
    # 检查权限：只有创建者可以申请入库
    if dev_product.created_by != current_user.id:
        flash('您没有权限申请此产品入库', 'danger')
        return redirect(url_for('product_management.index'))
    
    try:
        # 更新产品状态为"申请入库"
        dev_product.status = '申请入库'
        dev_product.updated_at = datetime.now()
        
        db.session.commit()
        flash('产品入库申请已提交，等待管理员审核', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'申请入库失败: {str(e)}', 'danger')
    
    return redirect(url_for('product_management.index'))

# 管理员审核入库
@product_management_bp.route('/<int:id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_product(id):
    dev_product = DevProduct.query.get_or_404(id)
    
    try:
        # 更新研发产品的状态为"已入库"
        dev_product.status = '已入库'
        dev_product.updated_at = datetime.now()
        
        # 执行实际入库操作 - 添加到正式产品库
        from app.models.product import Product
        
        # 检查是否已存在相同MN编码的产品
        existing_product = Product.query.filter_by(product_mn=dev_product.mn_code).first()
        
        if existing_product:
            # 更新已有产品
            existing_product.product_name = dev_product.name
            existing_product.model = dev_product.model
            existing_product.unit = dev_product.unit
            existing_product.retail_price = dev_product.retail_price
            existing_product.specification = dev_product.description
            existing_product.updated_at = datetime.now()
        else:
            # 创建新产品记录
            new_product = Product(
                type='研发产品',
                category=dev_product.category.name,
                product_mn=dev_product.mn_code,
                product_name=dev_product.name,
                model=dev_product.model,
                specification=dev_product.description,
                brand='公司自研',
                unit=dev_product.unit,
                retail_price=dev_product.retail_price,
                status='active',  # 设置为生产中状态
                owner_id=dev_product.created_by  # 将创建者设置为产品所有者
            )
            db.session.add(new_product)
        
        db.session.commit()
        flash('产品已成功入库到正式产品库', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'产品入库失败: {str(e)}', 'danger')
    
    return redirect(url_for('product_management.index'))

# 产品详情
@product_management_bp.route('/<int:id>', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def product_detail(id):
    from sqlalchemy.orm import joinedload
    
    # 使用joinedload减少查询次数
    dev_product = DevProduct.query.options(
        joinedload(DevProduct.category),
        joinedload(DevProduct.subcategory),
        joinedload(DevProduct.region)
    ).filter_by(id=id).first_or_404()
    
    if not check_product_access(dev_product, current_user):
        flash(_('您没有权限查看此产品'), 'danger')
        return redirect(url_for('product_management.index'))
    
    # 获取规格字段
    specs_objects = DevProductSpec.query.filter_by(dev_product_id=id).all()
    current_app.logger.debug(f"为产品 {id} 找到 {len(specs_objects)} 个规格: {[(spec.id, spec.field_name, spec.field_value) for spec in specs_objects]}")
    
    # 将DevProductSpec对象转换为可JSON序列化的字典
    specs = []
    field_names_seen = set()  # 用于跟踪已经处理过的规格名称
    
    for spec in specs_objects:
        # 如果此规格名称已处理过且有值，则跳过，避免重复
        if spec.field_name.lower() in field_names_seen:
            continue
            
        # 将规格名称标记为已处理
        field_names_seen.add(spec.field_name.lower())
        
        specs.append({
            'id': spec.id,
            'field_name': spec.field_name,
            'field_value': spec.field_value
        })
    
    return render_template('product_management/product_detail.html', 
                          dev_product=dev_product,
                          specs=specs)

# 根据子分类ID获取产品型号列表
@product_management_bp.route('/api/subcategory/<int:subcategory_id>/models', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def get_models_by_subcategory(subcategory_id):
    """根据子分类ID获取产品型号列表（从研发产品库和标准产品库）"""
    try:
        # 获取子分类信息
        subcategory = ProductSubcategory.query.get_or_404(subcategory_id)
        
        result = []
        
        # 1. 从研发产品库中获取产品型号
        dev_products = DevProduct.query.filter_by(subcategory_id=subcategory_id).all()
        for dev_product in dev_products:
            if dev_product.model:  # 确保型号不为空
                result.append({
                    'model': dev_product.model,
                    'library_type': '研发产品库',
                    'status': dev_product.status or '未知',
                    'source': 'dev'
                })
        
        # 2. 从标准产品库中查找匹配产品名称且是厂商品牌的产品型号
        from app.models.product import Product
        products = Product.query.filter_by(
            product_name=subcategory.name,
            is_vendor_product=True  # 只显示厂商品牌的产品
        ).all()
        
        for product in products:
            if product.model:  # 确保型号不为空
                result.append({
                    'model': product.model,
                    'library_type': '标准产品库', 
                    'status': product.status or '未知',
                    'source': 'standard'
                })
        
        # 去重复（基于型号）
        seen_models = set()
        unique_result = []
        for item in result:
            if item['model'] not in seen_models:
                seen_models.add(item['model'])
                unique_result.append(item)
            else:
                # 如果型号重复，优先保留研发产品库的记录
                for i, existing in enumerate(unique_result):
                    if existing['model'] == item['model'] and item['source'] == 'dev':
                        unique_result[i] = item
                        break
        
        # 按库类型排序：研发产品库在前，标准产品库在后
        unique_result.sort(key=lambda x: (0 if x['source'] == 'dev' else 1, x['model']))
        
        return jsonify(unique_result)
    except Exception as e:
        return jsonify({'error': f'获取产品型号失败: {str(e)}'}), 500

# 根据子分类ID获取规格字段列表
@product_management_bp.route('/api/subcategory/<int:subcategory_id>/spec-fields', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def get_spec_fields_by_subcategory(subcategory_id):
    """根据子分类ID获取规格字段列表"""
    try:
        # 查找该子分类下的所有规格类型字段（只包含用于编码的字段）
        spec_fields = ProductCodeField.query.filter(
            ProductCodeField.subcategory_id == subcategory_id,
            ProductCodeField.field_type == 'spec',
            (ProductCodeField.use_in_code == True) | (ProductCodeField.use_in_code.is_(None))
        ).order_by(ProductCodeField.position).all()
        
        # 处理结果
        result = []
        for field in spec_fields:
            field_data = {
                'id': field.id,
                'name': field.name,
                'description': field.description,
                'position': field.position,
                'is_required': field.is_required,
                'use_in_code': field.use_in_code,
                'options': []
            }
            
            # 获取字段选项
            options = ProductCodeFieldOption.query.filter_by(field_id=field.id).order_by(ProductCodeFieldOption.position).all()
            for option in options:
                field_data['options'].append({
                    'id': option.id,
                    'value': option.value,
                    'code': option.code
                })
                
            result.append(field_data)
        
        current_app.logger.debug(f"获取子分类 {subcategory_id} 的规格字段成功，找到 {len(result)} 个字段")
        return jsonify({'spec_fields': result})
    except Exception as e:
        current_app.logger.error(f"获取子分类 {subcategory_id} 的规格字段失败: {str(e)}")
        return jsonify({'error': f'获取规格字段失败: {str(e)}'}), 500

@product_management_bp.route('/api/all-spec-fields', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def get_all_spec_fields():
    """获取所有产品名称下的规格字段，支持关键词搜索"""
    try:
        search_term = request.args.get('search', '').strip()
        current_subcategory_id = request.args.get('subcategory_id', type=int)
        non_code_only = request.args.get('non_code_only', 'false').lower() == 'true'
        
        # 查询所有规格类型字段
        query = db.session.query(
            ProductCodeField.id,
            ProductCodeField.name,
            ProductCodeField.description,
            ProductCodeField.subcategory_id,
            ProductCodeField.use_in_code,
            ProductSubcategory.name.label('subcategory_name')
        ).join(ProductSubcategory).filter(
            ProductCodeField.field_type == 'spec'
        )
        
        # 根据参数过滤编码/非编码规格
        if non_code_only:
            query = query.filter(ProductCodeField.use_in_code == False)
        # 默认显示所有规格（编码和非编码），不再只显示编码规格
        
        # 如果有搜索词，添加搜索条件
        if search_term:
            query = query.filter(
                ProductCodeField.name.ilike(f'%{search_term}%')
            )
        
        spec_fields = query.order_by(
            # 当前产品名称的规格排在前面
            (ProductCodeField.subcategory_id != current_subcategory_id),
            ProductSubcategory.name,
            ProductCodeField.position
        ).all()
        
        # 组织返回数据
        result = []
        current_subcategory_specs = []
        other_subcategory_specs = []
        
        for field in spec_fields:
            spec_data = {
                'id': field.id,
                'name': field.name,
                'description': field.description,
                'subcategory_name': field.subcategory_name,
                'subcategory_id': field.subcategory_id
            }
            
            if field.subcategory_id == current_subcategory_id:
                current_subcategory_specs.append(spec_data)
            else:
                other_subcategory_specs.append(spec_data)
        
        return jsonify({
            'current_subcategory_specs': current_subcategory_specs,
            'other_subcategory_specs': other_subcategory_specs
        })
        
    except Exception as e:
        return jsonify({'error': f'获取规格字段失败: {str(e)}'}), 500

@product_management_bp.route('/api/subcategory/<int:subcategory_id>/spec-structure', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def get_spec_structure(subcategory_id):
    """获取该产品名称下的规格结构（按position排序）"""
    try:
        # 查询该子分类下的所有规格字段，按position排序
        spec_fields = ProductCodeField.query.filter(
            ProductCodeField.subcategory_id == subcategory_id,
            ProductCodeField.field_type == 'spec',
            (ProductCodeField.use_in_code == True) | (ProductCodeField.use_in_code.is_(None))
        ).order_by(ProductCodeField.position).all()
        
        # 查询该子分类下是否已有产品使用了这些规格
        existing_products = db.session.query(DevProduct).filter_by(
            subcategory_id=subcategory_id
        ).all()
        
        # 分析现有产品的规格使用情况
        used_positions = set()
        position_spec_mapping = {}
        
        for product in existing_products:
            for spec in product.specs:
                # 尝试找到对应的规格字段
                matching_field = None
                for field in spec_fields:
                    if field.name == spec.field_name:
                        matching_field = field
                        break
                
                if matching_field:
                    used_positions.add(matching_field.position)
                    if matching_field.position not in position_spec_mapping:
                        position_spec_mapping[matching_field.position] = {
                            'field_id': matching_field.id,
                            'field_name': matching_field.name,
                            'position': matching_field.position
                        }
        
        # 构建返回结果
        result = {
            'spec_fields': [],
            'has_existing_products': len(existing_products) > 0,
            'position_mapping': position_spec_mapping
        }
        
        for field in spec_fields:
            field_data = {
                'id': field.id,
                'name': field.name,
                'description': field.description,
                'position': field.position,
                'is_required': field.is_required,
                'use_in_code': field.use_in_code,
                'is_used_by_existing_products': field.position in used_positions,
                'options': []
            }
            
            # 获取字段选项
            options = ProductCodeFieldOption.query.filter_by(
                field_id=field.id,
                is_active=True
            ).order_by(ProductCodeFieldOption.position).all()
            
            for option in options:
                field_data['options'].append({
                    'id': option.id,
                    'value': option.value,
                    'code': option.code,
                    'description': option.description
                })
                
            result['spec_fields'].append(field_data)
        
        current_app.logger.debug(f"获取子分类 {subcategory_id} 的规格结构成功，找到 {len(result['spec_fields'])} 个字段，现有产品: {result['has_existing_products']}")
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"获取子分类 {subcategory_id} 的规格结构失败: {str(e)}")
        return jsonify({'error': f'获取规格结构失败: {str(e)}'}), 500

# 查看已入库产品列表
@product_management_bp.route('/inventory', methods=['GET'])
@login_required
def inventory():
    from app.models.product import Product
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    try:
        products = Product.query.filter_by(type='研发产品').order_by(Product.updated_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False)
    except Exception as e:
        current_app.logger.warning(f"使用updated_at排序失败: {str(e)}, 尝试使用id排序")
        try:
            # 回滚失败的事务
            db.session.rollback()
            products = Product.query.filter_by(type='研发产品').order_by(Product.id.desc()).paginate(
                page=page, per_page=per_page, error_out=False)
        except Exception as e2:
            current_app.logger.error(f"产品库存查询失败: {str(e2)}")
            # 回滚失败的事务
            db.session.rollback()
            # 创建一个空的分页对象
            from flask_sqlalchemy import Pagination
            products = Pagination(query=Product.query.filter_by(type='研发产品'), page=page, per_page=per_page, total=0, items=[])
    
    return render_template('product_management/inventory.html', products=products)

# 查看入库产品详情
@product_management_bp.route('/view-product/<int:product_id>', methods=['GET'])
@login_required
def view_product(product_id):
    from app.models.product import Product
    
    product = Product.query.get_or_404(product_id)
    
    return render_template('product_management/view_product.html', product=product)

# 添加新的规格指标
@product_management_bp.route('/api/add-spec-option', methods=['POST'])
@login_required
@permission_required('product_code', 'edit')
def add_spec_option():
    """添加新的规格指标并返回其编码"""
    try:
        data = request.json
        field_id = data.get('field_id')
        option_value = data.get('option_value')
        product_model = data.get('product_model', '新增产品')
        
        if not field_id or not option_value:
            return jsonify({'success': False, 'error': '参数不完整'}), 400
            
        # 检查字段是否存在
        field = ProductCodeField.query.get(field_id)
        if not field:
            return jsonify({'success': False, 'error': '规格字段不存在'}), 404
            
        # 检查是否已有相同的选项
        existing_option = ProductCodeFieldOption.query.filter_by(
            field_id=field_id,
            value=option_value
        ).first()
        
        if existing_option:
            # 已存在此选项，直接返回其信息
            return jsonify({
                'success': True, 
                'option': {
                    'id': existing_option.id,
                    'value': existing_option.value,
                    'code': existing_option.code
                },
                'message': '选项已存在'
            })
        
        # 查找当前最大排序位置
        max_position = db.session.query(db.func.max(ProductCodeFieldOption.position))\
            .filter_by(field_id=field_id).scalar() or 0
            
        # 生成编码
        existing_options = ProductCodeFieldOption.query.filter_by(field_id=field_id).all()
        existing_codes = [opt.code for opt in existing_options]
        
        # 修改编码生成逻辑，与规格管理保持一致，优先使用字母
        # 首先尝试使用指标值的首字母
        unique_code = None
        
        # 对于任何指标，首选使用首字母（与规格管理一致）
        if option_value and isinstance(option_value, str):
            first_letter = option_value[0].upper()
            if first_letter.isalpha() and first_letter not in existing_codes:
                unique_code = first_letter
        
        # 如果首字母不可用，尝试使用A-Z中其他字母
        if not unique_code:
            for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ':
                if letter not in existing_codes:
                    unique_code = letter
                    break
        
        # 如果所有字母都不可用，再尝试使用数字编码1-9
        if not unique_code:
            for i in range(1, 10):  # 尝试1-9
                if str(i) not in existing_codes:
                    unique_code = str(i)
                    break
        
        # 最后尝试数字编码0
        if not unique_code and '0' not in existing_codes:
            unique_code = '0'
            
        # 如果所有可能都已被使用，返回错误
        if not unique_code:
            return jsonify({'success': False, 'error': '无法生成唯一编码，所有可能的编码已被使用'}), 409
            
        # 创建新选项
        new_option = ProductCodeFieldOption(
            field_id=field_id,
            value=option_value,
            code=unique_code,
            description=f'从产品 {product_model} 自动添加的指标',
            position=max_position + 1
        )
        
        db.session.add(new_option)
        db.session.commit()
        
        # 返回新选项信息
        return jsonify({
            'success': True,
            'option': {
                'id': new_option.id,
                'value': new_option.value,
                'code': new_option.code
            },
            'message': '新指标添加成功'
        })
        
    except IntegrityError as e:
        db.session.rollback()
        if 'duplicate key value violates unique constraint' in str(e) and 'product_code_field_options_pkey' in str(e):
            current_app.logger.warning(f"检测到指标选项表主键序列问题，尝试修复: {str(e)}")
            if fix_table_sequence('product_code_field_options'):
                return jsonify({'success': False, 'error': '数据库序列已修复，请重新尝试添加指标'}), 500
            else:
                return jsonify({'success': False, 'error': f'数据库序列错误: {str(e)}'}), 500
        else:
            return jsonify({'success': False, 'error': f'数据完整性错误: {str(e)}'}), 500
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'添加指标失败: {str(e)}'}), 500

# 获取字段的指标选项
@product_management_bp.route('/api/field/<int:field_id>/options', methods=['GET'])
@login_required
def get_field_options(field_id):
    """获取指定规格字段的所有指标选项"""
    try:
        # 检查字段是否存在
        field = ProductCodeField.query.get(field_id)
        if not field:
            return jsonify({'success': False, 'error': '规格字段不存在'}), 404
            
        # 获取字段的所有选项
        options = ProductCodeFieldOption.query.filter_by(field_id=field_id)\
            .order_by(ProductCodeFieldOption.position.asc()).all()
            
        option_list = []
        for option in options:
            option_list.append({
                'id': option.id,
                'value': option.value,
                'code': option.code,
                'description': option.description,
                'position': option.position
            })
            
        return jsonify({
            'success': True,
            'options': option_list,
            'field_name': field.name
        })
        
    except Exception as e:
        current_app.logger.error(f"获取字段选项失败: {str(e)}")
        return jsonify({'success': False, 'error': f'获取字段选项失败: {str(e)}'}), 500

# PDF文件下载
@product_management_bp.route('/<int:id>/download-pdf', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def download_pdf(id):
    """下载产品PDF文件"""
    from flask import send_file, abort
    
    dev_product = DevProduct.query.get_or_404(id)
    
    # 检查是否有PDF文件
    if not dev_product.pdf_path:
        flash(_('该产品没有PDF文件'), 'warning')
        return redirect(url_for('product_management.product_detail', id=id))
    
    # 构建文件完整路径
    pdf_file_path = os.path.join(current_app.static_folder, dev_product.pdf_path)
    
    # 检查文件是否存在
    if not os.path.exists(pdf_file_path):
        flash(_('PDF文件不存在'), 'danger')
        return redirect(url_for('product_management.product_detail', id=id))
    
    try:
        # 获取原始文件名（去掉UUID前缀）
        original_filename = os.path.basename(dev_product.pdf_path)
        if '_' in original_filename:
            # 去掉UUID前缀，保留原始文件名
            original_filename = '_'.join(original_filename.split('_')[1:])
        
        # 如果没有原始文件名，使用产品型号作为文件名
        if not original_filename or original_filename == '':
            original_filename = f"{dev_product.model}.pdf"
        
        return send_file(
            pdf_file_path,
            as_attachment=True,
            download_name=original_filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        current_app.logger.error(f"下载PDF文件失败: {str(e)}")
        flash(_('下载PDF文件失败'), 'danger')
        return redirect(url_for('product_management.product_detail', id=id))

# 获取规格字段的选项
@product_management_bp.route('/api/spec-field-options', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def get_spec_field_options():
    """获取指定规格字段的所有选项"""
    try:
        subcategory_id = request.args.get('subcategory_id', type=int)
        spec_name = request.args.get('spec_name', '').strip()
        field_id = request.args.get('field_id', type=int)
        
        if not subcategory_id or not spec_name:
            return jsonify({'options': []})
        
        # 优先使用field_id查找，否则通过名称查找
        if field_id:
            field = ProductCodeField.query.get(field_id)
        else:
            field = ProductCodeField.query.filter_by(
                subcategory_id=subcategory_id,
                name=spec_name,
                field_type='spec'
            ).first()
        
        if not field:
            return jsonify({'options': []})
        
        # 获取该字段的所有选项
        options = ProductCodeFieldOption.query.filter_by(
            field_id=field.id
        ).order_by(ProductCodeFieldOption.position).all()
        
        options_data = []
        for option in options:
            options_data.append({
                'id': option.id,
                'value': option.value,
                'code': option.code,
                'description': option.description
            })
        
        return jsonify({
            'options': options_data,
            'field_id': field.id,
            'field_name': field.name
        })
        
    except Exception as e:
        current_app.logger.error(f"获取规格字段选项失败: {str(e)}")
        return jsonify({'options': []})

@product_management_bp.route('/api/product/<int:product_id>/specs', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def get_product_specs(product_id):
    """获取产品的现有规格数据"""
    try:
        # 获取产品的所有规格
        specs = DevProductSpec.query.filter_by(dev_product_id=product_id).all()
        
        specs_data = []
        for spec in specs:
            spec_data = {
                'id': spec.id,
                'field_name': spec.field_name,
                'field_value': spec.field_value,
                'field_code': spec.field_code
            }
            specs_data.append(spec_data)
        
        return jsonify({'specs': specs_data})
        
    except Exception as e:
        current_app.logger.error(f"获取产品规格失败: {str(e)}")
        return jsonify({'specs': []})

@product_management_bp.route('/api/spec-field/<int:field_id>/options', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def get_spec_field_options_by_id(field_id):
    """获取指定规格字段的所有选项"""
    try:
        # 获取规格字段
        field = ProductCodeField.query.get(field_id)
        if not field:
            return jsonify({'options': [], 'error': '规格字段不存在'}), 404
        
        # 获取该字段的所有选项
        options = ProductCodeFieldOption.query.filter_by(field_id=field_id).order_by(ProductCodeFieldOption.id).all()
        
        options_data = []
        for option in options:
            option_data = {
                'id': option.id,
                'value': option.value,
                'code': option.code,
                'description': option.description
            }
            options_data.append(option_data)
        
        return jsonify({
            'options': options_data,
            'field_id': field.id,
            'field_name': field.name
        })
        
    except Exception as e:
        current_app.logger.error(f"获取规格字段选项失败: {str(e)}")
        return jsonify({'options': []}) 

@product_management_bp.route('/api/check-mn-code', methods=['POST'])
@login_required
@permission_required('product_code', 'create')
def check_mn_code_duplicate_api():
    """检查MN编码是否重复"""
    try:
        data = request.get_json()
        mn_code = data.get('mn_code', '').strip()
        exclude_product_id = data.get('exclude_product_id')
        
        if not mn_code:
            return jsonify({'exists': False})
        
        # 检查研发产品库
        dev_query = DevProduct.query.filter(
            DevProduct.mn_code == mn_code,
            DevProduct.is_deleted == False
        )
        if exclude_product_id:
            dev_query = dev_query.filter(DevProduct.id != exclude_product_id)
        
        dev_exists = dev_query.first() is not None
        
        # 检查正式产品库
        from app.models.product import Product
        formal_exists = Product.query.filter(
            Product.mn_code == mn_code,
            Product.is_deleted == False
        ).first() is not None
        
        if dev_exists:
            return jsonify({'exists': True, 'source': 'dev'})
        elif formal_exists:
            return jsonify({'exists': True, 'source': 'formal'})
        else:
            return jsonify({'exists': False})
            
    except Exception as e:
        current_app.logger.error(f"检查MN编码重复失败: {str(e)}")
        return jsonify({'exists': False, 'error': str(e)})