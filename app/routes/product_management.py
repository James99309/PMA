from flask import Blueprint, render_template, render_template_string, request, jsonify, redirect, url_for, flash, current_app, send_file, Response
from flask_babel import gettext as _
from flask_login import login_required, current_user
from app import db
from app.models.product_code import ProductCategory, ProductSubcategory, ProductCodeField, ProductCodeFieldOption
from app.models.dev_product import DevProduct, DevProductSpec
from app.permissions import admin_required, product_manager_required, permission_required, has_permission
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
from PIL import Image
from app.utils.supabase_client import get_supabase_client
from app.routes.product_code import get_field_unit

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
    保存上传的产品图片（等比例缩放处理）
    
    参数:
    - file: 上传的文件对象
    
    返回:
    - 成功时返回保存的文件路径，失败时返回None
    """
    if file and allowed_file(file.filename):
        try:
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
            
            logger.debug(f"处理研发产品图片: {original_filename} -> {unique_filename}, 大小: {file_size} bytes")
            
            # 确保上传目录存在
            upload_folder = os.path.join(current_app.static_folder, 'uploads', 'products')
            os.makedirs(upload_folder, exist_ok=True)
            
            # 保存临时文件
            temp_path = os.path.join(upload_folder, f"temp_{unique_filename}")
            file.save(temp_path)
            logger.debug(f"临时文件已保存: {temp_path}")
            
            # 打开图片并等比例缩放（保持完整图片内容）
            with Image.open(temp_path) as img:
                # 获取原始尺寸
                width, height = img.size
                logger.debug(f"原始图片尺寸: {width}x{height}")
                
                # 设置最大尺寸限制
                max_size = 800  # 增加到800像素以获得更好的显示效果
                
                # 计算等比例缩放尺寸（保持宽高比，不裁剪）
                if width > max_size or height > max_size:
                    # 计算缩放比例
                    width_ratio = max_size / width
                    height_ratio = max_size / height
                    scale_ratio = min(width_ratio, height_ratio)  # 使用较小的比例确保完整显示
                    
                    new_width = int(width * scale_ratio)
                    new_height = int(height * scale_ratio)
                    
                    # 等比例缩放（保持完整图片，不裁剪）
                    img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                    logger.debug(f"研发产品图片已等比例缩放至: {new_width}x{new_height}")
                else:
                    logger.debug("研发产品图片尺寸在限制范围内，无需缩放")
                
                # 保存处理后的图片，使用更高的压缩率以减小文件大小
                final_path = os.path.join(upload_folder, unique_filename)
                img.save(final_path, optimize=True, quality=75)  # 降低质量从85到75
                logger.debug(f"处理后的研发产品图片已保存: {final_path}")
                
                # 删除临时文件
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    logger.debug(f"临时文件已删除: {temp_path}")
                
                # 返回相对路径
                return os.path.join('uploads', 'products', unique_filename)
                
        except Exception as e:
            logger.error(f"处理研发产品图片时出错: {str(e)}", exc_info=True)
            # 删除临时文件
            temp_path = os.path.join(upload_folder, f"temp_{unique_filename}")
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    logger.debug(f"出错后清理临时文件: {temp_path}")
                except Exception as cleanup_error:
                    logger.error(f"清理临时文件时出错: {str(cleanup_error)}")
    else:
        if file:
            logger.warning(f"不支持的文件类型: {file.filename}")
        else:
            logger.warning("没有提供文件")
    
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
        status_filter = request.args.get('status_filter', '')  # 默认显示所有状态
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
                    DevProduct.creator.has(company_name=current_user.company_name)
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

        # 按分类体系排序：分类 → 子分类 → 产品名称 → 型号 → ID
        products = query.join(ProductSubcategory, DevProduct.subcategory_id == ProductSubcategory.id)\
                        .join(ProductCategory, ProductSubcategory.category_id == ProductCategory.id)\
                        .order_by(
                            ProductCategory.code_letter.asc(),
                            ProductSubcategory.display_order.asc(),
                            DevProduct.name.asc(),  # ✅ 修复：DevProduct使用name字段，不是product_name
                            DevProduct.model.asc(),
                            DevProduct.id.asc()
                        ).all()

        # 获取分类列表用于筛选（按ID顺序，与产品分类管理页面一致）
        categories = ProductCategory.get_ordered_list()

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
            'reset_url': url_for('product_management.index', status_filter='生产中'),
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
                        'field': 'category',
                        'label': _('产品分类'),
                        'type': 'text',
                        'width': '120px',
                        'sort_type': 'string'
                    },
                    {
                        'key': 'subcategory',
                        'field': 'subcategory',
                        'label': _('子分类'),
                        'type': 'text',
                        'width': '120px',
                        'sort_type': 'string'
                    },
                    {
                        'key': 'model',
                        'field': 'model',
                        'label': _('产品型号'),
                        'type': 'link',
                        'url_template': '/product-management/{id}',
                        'width': '150px',
                        'sort_type': 'string'
                    },
                    {
                        'key': 'status',
                        'field': 'status',
                        'label': _('产品状态'),
                        'type': 'badge',
                        'render': 'render_dev_product_status_badge',
                        'width': '100px',
                        'sort_type': 'string'
                    },
                    {
                        'key': 'mn_code',
                        'field': 'mn_code',
                        'label': _('MN编码'),
                        'type': 'text',
                        'width': '120px',
                        'sort_type': 'string'
                    },
                    {
                        'key': 'creator',
                        'field': 'creator',
                        'label': _('创建者'),
                        'type': 'text',
                        'width': '100px',
                        'sort_type': 'string'
                    },
                    {
                        'key': 'created_at',
                        'field': 'created_at',
                        'label': _('创建时间'),
                        'type': 'date',
                        'format': '%Y-%m-%d',
                        'width': '120px',
                        'sort_type': 'date'
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
        status_filter = request.args.get('status_filter', '')  # 默认显示所有状态
        creator_filter = request.args.get('creator_filter', '')
        
        # 分页参数
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        # 排序参数
        sort_field = request.args.get('sort_field', '')
        sort_direction = request.args.get('sort_direction', 'asc')
        
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
                    DevProduct.creator.has(company_name=current_user.company_name)
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
        
        # 获取总数
        total_count = query.count()
        
        # 动态排序（研发产品库复杂查询需要特殊处理）
        if sort_field and sort_direction:
            print(f"🔍 研发产品库排序调试 - 字段: {sort_field}, 方向: {sort_direction}")
            
            # 字段映射（已经JOIN的表字段）
            field_mapping = {
                'model': DevProduct.model,
                'mn_code': DevProduct.mn_code,
                'description': DevProduct.description,
                'status': DevProduct.status,
                'created_at': DevProduct.created_at,
                'updated_at': DevProduct.updated_at,
                # 关联字段需要特殊处理（已经JOIN）
                'category': ProductCategory.name,  # 产品分类
                'subcategory': ProductSubcategory.name,  # 子分类
                'creator': User.real_name  # 创建者
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
                # 默认排序：按分类体系
                query = query.join(ProductSubcategory, DevProduct.subcategory_id == ProductSubcategory.id)\
                             .join(ProductCategory, ProductSubcategory.category_id == ProductCategory.id)\
                             .order_by(
                                 ProductCategory.code_letter.asc(),
                                 ProductSubcategory.display_order.asc(),
                                 DevProduct.name.asc(),  # ✅ 修复：DevProduct使用name字段
                                 DevProduct.model.asc(),
                                 DevProduct.id.asc()
                             )
        else:
            print("📊 使用默认排序: 分类体系排序")
            # 默认排序：按分类体系
            query = query.join(ProductSubcategory, DevProduct.subcategory_id == ProductSubcategory.id)\
                         .join(ProductCategory, ProductSubcategory.category_id == ProductCategory.id)\
                         .order_by(
                             ProductCategory.code_letter.asc(),
                             ProductSubcategory.display_order.asc(),
                             DevProduct.name.asc(),  # ✅ 修复：DevProduct使用name字段
                             DevProduct.model.asc(),
                             DevProduct.id.asc()
                         )
        
        # 分页数据
        products = query.offset(offset).limit(limit).all()
        
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
                    DevProduct.creator.has(company_name=current_user.company_name)
                )
            elif permission_level == 'department':
                base_query = base_query.join(DevProduct.creator).filter(
                    DevProduct.creator.has(department=current_user.department)
                )
            else:
                base_query = base_query.filter_by(created_by=current_user.id)
        
        # 检测移动端并使用智能移动卡片
        from app.utils.mobile_helpers import is_mobile_request
        from types import SimpleNamespace
        
        if products:
            # 格式化产品数据为标准结构
            formatted_results = []
            for product in products:
                creator_name = '-'
                if product.creator:
                    creator_name = product.creator.real_name or product.creator.username
                
                formatted_product = SimpleNamespace(
                    id=product.id,
                    model=product.model,
                    mn_code=product.mn_code or '',
                    status=product.status or '未设置',
                    category_name=product.category.name if product.category else '-',
                    subcategory_name=product.subcategory.name if product.subcategory else '-',
                    creator_name=creator_name,
                    description=product.description or '',
                    created_at=product.created_at
                )
                formatted_results.append(formatted_product)
            
            if is_mobile_request():
                # 智能移动卡片配置 - 研发产品库
                smart_mobile_card = {
                    'module': 'rd_product',
                    'title_field': {'field': 'model'},
                    'link_url': '/product-management/{id}',
                    'badges': [
                        {'field': 'status', 'renderer': 'render_dev_product_status_badge'}
                    ],
                    'details': [
                        {'field': 'mn_code', 'label': '产品料号'},
                        {'field': 'category_name', 'label': '产品分类'},
                        {'field': 'subcategory_name', 'label': '子分类'},
                        {'field': 'creator_name', 'label': '创建人'},
                        {'field': 'description', 'label': '产品描述'},
                        {'field': 'created_at', 'label': '创建时间', 'format': 'date'}
                    ]
                }
                
                # 使用智能移动卡片模板渲染
                html = render_template_string('''
                {% from 'macros/ui_helpers.html' import render_smart_mobile_cards %}
                {{ render_smart_mobile_cards(items, card_config) }}
                ''', items=formatted_results, card_config=smart_mobile_card)
            else:
                # 桌面端使用传统表格行渲染
                html_rows = []
                for product in formatted_results:
                    # 使用通用徽章宏渲染产品状态
                    status_badge = render_template_string('''
                    {% from 'macros/ui_helpers.html' import render_dev_product_status_badge %}
                    {{ render_dev_product_status_badge(status) }}
                    ''', status=product.status if product.status else '未设置')
                    
                    created_at = product.created_at.strftime('%Y-%m-%d') if product.created_at else '-'
                    
                    html_row = f"""
                    <tr>
                        <td>{product.category_name}</td>
                        <td>{product.subcategory_name}</td>
                        <td><a href="/product-management/{product.id}" class="text-primary text-decoration-none">{product.model}</a></td>
                        <td><code class="text-muted">{product.mn_code}</code></td>
                        <td>{status_badge}</td>
                        <td>{product.creator_name}</td>
                        <td class="text-muted">{created_at}</td>
                    </tr>
                    """
                    html_rows.append(html_row)
                html = '\n'.join(html_rows)
        else:
            if is_mobile_request():
                html = '<div class="text-center py-4">暂无符合条件的数据</div>'
            else:
                html = '<tr><td colspan="7" class="text-center text-muted py-4">暂无符合条件的数据</td></tr>'
        
        # 计算是否还有更多数据
        has_more = (offset + limit) < total_count
        
        return jsonify({
            'success': True,
            'html': html,
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
    """创建研发产品页面 - 使用统一模板"""
    from app.models.product_code import ProductCodeField, ProductCodeFieldOption

    # 获取所有产品分类（按ID顺序，与产品分类管理页面一致）
    categories = ProductCategory.get_ordered_list()

    # 获取所有产品地区（从ProductCodeField获取，与标准产品统一数据源）
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

    return render_template('product/create.html',
                           categories=categories,
                           regions=regions,  # 添加地区数据
                           product_type='research',  # 标记为研发产品
                           brands=[])  # 研发产品不需要品牌列表

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

# 生成MN编码（旧版本，保留以兼容）
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

# 统一的MN编码生成函数（基于规格position）
def generate_mn_code_from_specs(category, subcategory, region_code, specs_data):
    """
    统一的MN编码生成函数
    
    Args:
        category: 产品分类对象
        subcategory: 产品子分类对象
        region_code: 区域编码字符
        specs_data: 包含position和code的规格数据列表
                   [{'position': 1, 'code': 'A'}, ...]
    
    Returns:
        str: 生成的MN编码
    """
    # 按position排序
    specs_data.sort(key=lambda x: x.get('position', 999))
    
    # 提取前10个规格编码
    spec_codes = []
    for spec in specs_data[:10]:
        spec_codes.append(spec.get('code', '0'))
    
    # 去掉末尾的'0'
    last_non_zero_index = -1
    for i in range(len(spec_codes) - 1, -1, -1):
        if spec_codes[i] != '0':
            last_non_zero_index = i
            break
    
    if last_non_zero_index >= 0:
        effective_spec_codes = spec_codes[:last_non_zero_index + 1]
    else:
        effective_spec_codes = []
    
    # 生成MN编码
    mn_code = f"{category.code_letter}{subcategory.code_letter}{region_code}{''.join(effective_spec_codes)}"
    
    return mn_code

# 标准的研发产品规格处理函数
def save_dev_product_specs(dev_product_id, spec_data_list, logger=None):
    """
    标准的研发产品规格保存函数

    Args:
        dev_product_id: 研发产品ID
        spec_data_list: 规格数据列表
            [
                {
                    'id': existing_spec_id (可选，用于更新),
                    'field_name': '规格名称',
                    'field_value': '规格值',
                    'field_code': '规格编码' (可选),
                    'action': 'create'|'update'|'delete' (可选)
                }
            ]
        logger: 日志记录器

    Returns:
        tuple: (success, saved_specs, error_message)
    """
    if not logger:
        logger = current_app.logger

    saved_specs = []

    try:
        for spec_data in spec_data_list:
            action = spec_data.get('action', 'create')

            if action == 'delete':
                # 删除规格
                spec_id = spec_data.get('id')
                if spec_id:
                    spec_to_delete = DevProductSpec.query.get(spec_id)
                    if spec_to_delete and spec_to_delete.dev_product_id == dev_product_id:
                        # 只能删除非编码规格
                        if not spec_to_delete.field_code or spec_to_delete.field_code.strip() == '':
                            db.session.delete(spec_to_delete)
                            logger.debug(f"删除非编码规格: {spec_to_delete.field_name}")

            elif action == 'update':
                # 更新现有规格
                spec_id = spec_data.get('id')
                if spec_id:
                    existing_spec = DevProductSpec.query.get(spec_id)
                    if existing_spec and existing_spec.dev_product_id == dev_product_id:
                        existing_spec.field_name = spec_data['field_name']
                        existing_spec.field_value = spec_data['field_value']

                        # 检查该规格字段是否参与编码
                        from app.models.product_code import ProductCodeField
                        dev_product = DevProduct.query.get(dev_product_id)
                        code_field = ProductCodeField.query.filter_by(
                            subcategory_id=dev_product.subcategory_id,
                            name=spec_data['field_name']
                        ).first()

                        # 只有use_in_code=True的规格才保存编码值
                        if code_field and code_field.use_in_code and spec_data.get('field_code'):
                            existing_spec.field_code = spec_data['field_code']
                        else:
                            # 非编码规格，清空field_code
                            existing_spec.field_code = None

                        logger.debug(f"更新规格: {spec_data['field_name']} = {spec_data['field_value']}, 编码: {existing_spec.field_code or '无'}")
                        saved_specs.append(existing_spec)

            else:  # create
                # 创建新规格（简化逻辑，与编辑时一致）
                if spec_data.get('field_name', '').strip():
                    # 检查该规格字段是否参与编码
                    from app.models.product_code import ProductCodeField
                    dev_product = DevProduct.query.get(dev_product_id)
                    code_field = ProductCodeField.query.filter_by(
                        subcategory_id=dev_product.subcategory_id,
                        name=spec_data['field_name']
                    ).first()

                    # 只有use_in_code=True的规格才保存编码值
                    field_code_value = None
                    if code_field and code_field.use_in_code:
                        if spec_data.get('field_code') and spec_data.get('field_code') != '0':
                            field_code_value = spec_data.get('field_code')

                    new_spec = DevProductSpec(
                        dev_product_id=dev_product_id,
                        field_name=spec_data['field_name'],
                        field_value=spec_data.get('field_value', ''),
                        field_code=field_code_value
                    )
                    db.session.add(new_spec)
                    logger.debug(f"添加新规格: {spec_data['field_name']} = {spec_data.get('field_value', '')}, 编码: {field_code_value or '无'}")
                    saved_specs.append(new_spec)

        db.session.flush()  # 确保所有更改在同一个事务中
        return (True, saved_specs, None)

    except Exception as e:
        logger.error(f"保存规格时出错: {str(e)}")
        return (False, [], str(e))


# MN编号重复检查函数（通用版本 - 支持研发库和产品库调用）
def check_mn_code_duplicate(mn_code, exclude_dev_product_id=None, exclude_product_id=None):
    """
    检查MN编号全局唯一性（跨研发产品库和标准产品库）

    Args:
        mn_code: 要检查的MN编号
        exclude_dev_product_id: 排除的研发产品ID（研发库编辑时使用）
        exclude_product_id: 排除的产品ID（产品库编辑时使用）

    Returns:
        dict: {
            'is_duplicate': bool,
            'dev_products': [{...}],  # 研发库重复产品列表
            'standard_products': [{...}],  # 产品库重复产品列表
            'total_duplicates': int
        }

    Examples:
        # 产品库新增时检查
        check_mn_code_duplicate('BDE01')

        # 产品库编辑时检查（排除当前产品）
        check_mn_code_duplicate('BDE01', exclude_product_id=123)

        # 研发库编辑时检查（排除当前研发产品）
        check_mn_code_duplicate('BDE01', exclude_dev_product_id=456)
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
        prod_query = Product.query.filter(Product.product_mn == mn_code)
        if exclude_product_id:
            prod_query = prod_query.filter(Product.id != exclude_product_id)

        standard_duplicates = prod_query.all()
        
        for product in standard_duplicates:
            # 优先使用新的分类体系，回退到旧字段
            category_name = product.category_obj.name if product.category_obj else (product.category or '未知')

            duplicate_standard_products.append({
                'id': product.id,
                'model': product.model,
                'name': product.product_name,
                'status': product.status,
                'category': category_name,
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

# 向后兼容别名（保持现有代码正常工作）
def check_mn_code_duplicate_internal(mn_code, exclude_dev_product_id=None):
    """
    向后兼容函数 - 调用新的通用检查函数

    此函数保留用于向后兼容，新代码应使用 check_mn_code_duplicate()
    """
    return check_mn_code_duplicate(mn_code, exclude_dev_product_id=exclude_dev_product_id)


# ==================== 研发产品辅助函数 ====================
# 以下函数用于save()和update_product()的公共逻辑提取，遵循DRY原则


def _collect_spec_data_for_create() -> list:
    """
    收集创建产品时的规格数据

    从request.form收集以下字段:
    - spec_name[], spec_value[], spec_option_codes[] (现有规格)
    - new_spec_names[], new_option_values[] (新增规格)

    Returns:
        规格数据列表 [{'field_name', 'field_value', 'field_code', 'action': 'create'}, ...]
    """
    # 1. 收集现有规格数据
    spec_names = request.form.getlist('spec_name[]')
    spec_values = request.form.getlist('spec_value[]')
    spec_option_codes = request.form.getlist('spec_option_codes[]')

    # 2. 收集新增规格数据
    new_spec_names = request.form.getlist('new_spec_names[]')
    new_option_values = request.form.getlist('new_option_values[]')

    # 记录日志
    current_app.logger.debug(f"规格名称: {spec_names}")
    current_app.logger.debug(f"规格值: {spec_values}")
    current_app.logger.debug(f"规格编码: {spec_option_codes}")
    current_app.logger.debug(f"新增规格: {new_spec_names}")
    current_app.logger.debug(f"新增选项: {new_option_values}")

    # 3. 转换为标准格式
    spec_data_list = []

    # 处理现有规格数据
    for i in range(len(spec_names)):
        if i < len(spec_values) and spec_names[i].strip() and spec_values[i].strip():
            spec_code = spec_option_codes[i] if i < len(spec_option_codes) and spec_option_codes[i] != '0' else None
            spec_data_list.append({
                'field_name': spec_names[i].strip(),
                'field_value': spec_values[i].strip(),
                'field_code': spec_code,
                'action': 'create'
            })

    # 处理新增规格数据（非编码规格）
    for i in range(len(new_spec_names)):
        if i < len(new_option_values) and new_spec_names[i].strip() and new_option_values[i].strip():
            spec_data_list.append({
                'field_name': new_spec_names[i].strip(),
                'field_value': new_option_values[i].strip(),
                'field_code': None,  # 新增规格都是非编码
                'action': 'create'
            })

    current_app.logger.debug(f"准备保存 {len(spec_data_list)} 个规格")

    return spec_data_list


def _collect_spec_data_for_update() -> list:
    """
    收集更新产品时的规格数据

    从request.form收集以下字段:
    - deleted_spec_ids[] (删除操作)
    - existing_spec_ids[], spec_name[], spec_value[], spec_option_codes[] (更新操作)
    - 无existing_spec_ids但有spec_name的 (新增操作)

    Returns:
        规格数据列表 [{'id', 'field_name', 'field_value', 'field_code', 'action'}, ...]
        action可以是: 'delete', 'update', 'create'
    """
    # 1. 收集删除操作
    deleted_spec_ids = request.form.getlist('deleted_spec_ids[]')

    # 2. 收集现有规格的更新操作
    existing_spec_ids = request.form.getlist('existing_spec_ids[]')
    spec_names = request.form.getlist('spec_name[]')
    spec_values = request.form.getlist('spec_value[]')
    spec_codes = request.form.getlist('spec_option_codes[]')

    # 转换为标准格式
    spec_data_list = []

    # 处理删除操作
    for spec_id in deleted_spec_ids:
        if spec_id:
            spec_data_list.append({
                'id': spec_id,
                'action': 'delete'
            })

    # 处理更新操作
    for i in range(len(existing_spec_ids)):
        if existing_spec_ids[i] and i < len(spec_names) and i < len(spec_values):
            spec_code = spec_codes[i] if i < len(spec_codes) else None
            spec_data_list.append({
                'id': existing_spec_ids[i],
                'field_name': spec_names[i],
                'field_value': spec_values[i],
                'field_code': spec_code,
                'action': 'update'
            })

    # 处理新增操作（没有existing_spec_ids的）
    for i in range(len(spec_names)):
        if (i >= len(existing_spec_ids) or not existing_spec_ids[i]) and spec_names[i].strip():
            spec_data_list.append({
                'field_name': spec_names[i],
                'field_value': spec_values[i] if i < len(spec_values) else '',
                'field_code': None,  # 新增规格都是非编码
                'action': 'create'
            })

    return spec_data_list


def _handle_ajax_file_upload_response(success: bool, message: str = None, error: Exception = None) -> tuple:
    """
    处理AJAX文件上传响应

    检测请求是否为AJAX文件上传请求，如果是则返回JSON响应

    Args:
        success: 操作是否成功
        message: 成功或错误消息
        error: 异常对象（可选）

    Returns:
        (is_handled, response)
        - is_handled=True时表示已处理，response为JSON响应对象
        - is_handled=False时调用方应继续正常流程
    """
    is_ajax_request = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    has_file_upload = 'product_image' in request.files or 'product_pdf' in request.files

    if is_ajax_request and has_file_upload:
        if success:
            return True, jsonify({
                'success': True,
                'message': message or _('文件上传成功！')
            })
        else:
            return True, jsonify({
                'success': False,
                'message': message or (str(error) if error else _('操作失败'))
            })

    return False, None


# ==================== 研发产品路由函数 ====================

# 保存新产品
@product_management_bp.route('/save', methods=['POST'])
@login_required
@permission_required('product_code', 'create')
def save():
    """保存新产品（统一处理研发和标准产品）"""
    from app.services.product_creation_service import ProductCreationService

    # 检查产品类型参数
    product_type = request.form.get('product_type', 'research')  # 默认为研发产品

    return ProductCreationService.save_product(product_type)

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
    
    # 获取所有产品分类
    categories = db.session.query(ProductCategory).order_by(ProductCategory.name).all()
    subcategories = db.session.query(ProductSubcategory).filter_by(category_id=product.category_id).order_by(ProductSubcategory.name).all()
    
    # 获取产品规格并添加详细日志
    specs_db = db.session.query(DevProductSpec).filter_by(dev_product_id=id).all()
    current_app.logger.debug(f"为产品 {id} 找到 {len(specs_db)} 个规格: {[(spec.id, spec.field_name, spec.field_value) for spec in specs_db]}")
    
    if not specs_db:
        # 尝试通过ORM关系获取规格
        product_specs = product.specs if hasattr(product, 'specs') else []
        current_app.logger.debug(f"通过ORM关系获取规格，找到 {len(product_specs)} 个规格")
        specs_db = product_specs
    
    # 获取当前产品分类下的有效规格名称（用于标记快照规格）
    valid_spec_names = set()
    if dev_product.subcategory_id:
        from app.models.product_code import ProductCodeField
        valid_fields = ProductCodeField.query.filter_by(
            subcategory_id=dev_product.subcategory_id
        ).all()
        valid_spec_names = {field.name for field in valid_fields}

    # 将DevProductSpec对象转换为可JSON序列化的字典列表
    # 标记哪些是快照规格（不在当前规格定义中的历史数据）
    specs = []
    for spec in specs_db:
        # 尝试查找对应的ProductCodeField（用于未来功能，快照规格可能为None）
        field = ProductCodeField.query.filter_by(
            name=spec.field_name,
            field_type='spec'
        ).first()

        is_snapshot = spec.field_name not in valid_spec_names

        specs.append({
            'field_name': spec.field_name,
            'field_value': spec.field_value,
            'field_code': getattr(spec, 'field_code', None),  # 兼容字段编码
            'field_id': field.id if field else None,  # 添加 field_id（快照规格可能为 None）
            'is_saved': True,
            'is_snapshot': is_snapshot  # 标记快照规格
        })

    # 获取所有产品地区（使用ProductCodeField，与创建页面一致）
    from app.models.product_code import ProductCodeField, ProductCodeFieldOption
    region_fields = ProductCodeField.query.filter_by(field_type='origin_location')\
                                          .order_by(ProductCodeField.position).all()

    regions = []
    for field in region_fields:
        code = field.code or '0'
        if code == "?":
            option = ProductCodeFieldOption.query.filter_by(field_id=field.id).first()
            code = option.code if option else "0"

        regions.append({
            'id': field.id,
            'name': field.name,
            'code': code
        })

    # 获取锁定状态（研发产品根据状态判断，而非is_mn_locked字段）
    # 研发产品在"已入库"状态后不允许修改关键字段
    locked_statuses = ['已入库', '已取消']
    is_mn_locked = product.status in locked_statuses

    # 检查是否被引用（研发产品入库后会生成标准产品）
    is_referenced = False
    if product.status == '已入库':
        from app.models.product import Product
        is_referenced = Product.query.filter(
            Product.source_dev_product_id == product.id
        ).count() > 0

    # 检查关键字段是否有值（用于智能锁定控制）
    has_category = product.category_id is not None
    has_subcategory = product.subcategory_id is not None
    has_region = product.region_id is not None
    has_model = bool(product.model and product.model.strip())
    has_specs = len(specs) > 0

    # 使用统一的create.html模板，传递product_type='research'
    return render_template(
        'product/create.html',
        product=product,  # 注意：统一使用product变量名
        specs=specs,
        categories=categories,
        regions=regions,
        subcategories=subcategories,
        product_type='research',  # 标记为研发产品
        brands=[],  # 研发产品不需要品牌列表
        is_mn_locked=is_mn_locked,
        is_referenced=is_referenced,
        has_category=has_category,
        has_subcategory=has_subcategory,
        has_region=has_region,
        has_model=has_model,
        has_specs=has_specs
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
        # 注意：研发产品的name字段通常跟model一致，或者从subcategory获取
        model = request.form.get('product_model')  # 表单字段名是product_model
        dev_product.model = model
        dev_product.name = model  # 研发产品的name默认使用model
        dev_product.description = request.form.get('description', '')
        dev_product.unit = request.form.get('unit', '')
        
        retail_price = request.form.get('retail_price', '')
        dev_product.retail_price = float(retail_price) if retail_price else None
        
        # 更新货币字段
        currency = request.form.get('currency', 'CNY')
        dev_product.currency = currency

        # 更新销售区域
        region_id = request.form.get('region_id') or None
        if region_id:
            dev_product.region_id = int(region_id)
        else:
            dev_product.region_id = None

        dev_product.updated_at = datetime.now()
        
        # WYSIWYG方案：直接从前端获取已计算好的MN编码，后端只负责验证
        no_update_mn = request.form.get('no_update_mn') == 'true'
        new_mn_code = None

        if not no_update_mn:
            new_mn_code = request.form.get('mn_code_preview', '').strip()
            current_app.logger.debug(f"[WYSIWYG] 从前端获取MN编码: {new_mn_code}")

            # 只做重复检查（只在MN编码确实变化时检查）
            if new_mn_code and new_mn_code != dev_product.mn_code:
                duplicate_check = check_mn_code_duplicate_internal(new_mn_code, exclude_dev_product_id=id)
                if duplicate_check['is_duplicate']:
                    # 构建重复产品信息字符串
                    duplicate_info = []
                    for product in duplicate_check['dev_products']:
                        duplicate_info.append(
                            f"研发产品库: {product['name']} "
                            f"(型号: {product['model']}, "
                            f"状态: {product['status']}, "
                            f"创建者: {product['creator']}, "
                            f"创建时间: {product['created_at']})"
                        )
                    for product in duplicate_check['standard_products']:
                        duplicate_info.append(
                            f"标准产品库: {product['name']} "
                            f"(型号: {product['model']}, "
                            f"状态: {product['status']}, "
                            f"拥有者: {product['owner']}, "
                            f"创建时间: {product['created_at']})"
                        )

                    duplicate_message = (
                        f"MN编号 {new_mn_code} 已存在重复产品！\n\n"
                        f"重复产品详细信息:\n" + "\n".join(duplicate_info)
                    )
                    flash(duplicate_message, 'danger')
                    return redirect(url_for('product_management.edit_product', id=id))

                # 更新MN编码
                current_app.logger.debug(f"更新MN编码: {dev_product.mn_code} -> {new_mn_code}")
                dev_product.mn_code = new_mn_code
        
        # 处理图片上传（智能选择本地或云端）
        if 'product_image' in request.files:
            file = request.files['product_image']
            if file.filename:
                # 使用智能存储系统（自动判断本地/云端环境）
                try:
                    supabase_client = get_supabase_client()
                    image_url = supabase_client.upload_product_file(dev_product.id, file, 'image', 'rd_product')
                    
                    if image_url:
                        # 如果已有旧图片且是本地路径，删除本地文件
                        if dev_product.image_path and not dev_product.image_path.startswith('http'):
                            old_image_path = os.path.join(current_app.static_folder, dev_product.image_path)
                            if os.path.exists(old_image_path):
                                try:
                                    os.remove(old_image_path)
                                    current_app.logger.info(f"删除旧本地图片: {old_image_path}")
                                except Exception as e:
                                    current_app.logger.warning(f"删除旧图片失败: {str(e)}")
                        
                        # 更新图片路径
                        dev_product.image_path = image_url
                        current_app.logger.info(f"研发产品图片上传成功: {image_url}")
                    else:
                        flash(_('图片上传失败，请检查文件格式和大小'), 'warning')
                        current_app.logger.warning("研发产品图片上传失败")
                except Exception as e:
                    flash(_('图片上传过程中发生错误'), 'danger')
                    current_app.logger.error(f"研发产品图片上传异常: {str(e)}")
        
        # 处理PDF文件上传（智能选择本地或云端）
        if 'product_pdf' in request.files:
            file = request.files['product_pdf']
            if file.filename:
                # 使用智能存储系统（自动判断本地/云端环境）
                try:
                    supabase_client = get_supabase_client()
                    pdf_url = supabase_client.upload_product_file(dev_product.id, file, 'pdf', 'rd_product')
                    
                    if pdf_url:
                        # 如果已有旧PDF且是本地路径，删除本地文件
                        if dev_product.pdf_path and not dev_product.pdf_path.startswith('http'):
                            old_pdf_path = os.path.join(current_app.static_folder, dev_product.pdf_path)
                            if os.path.exists(old_pdf_path):
                                try:
                                    os.remove(old_pdf_path)
                                    current_app.logger.info(f"删除旧本地PDF: {old_pdf_path}")
                                except Exception as e:
                                    current_app.logger.warning(f"删除旧PDF文件失败: {str(e)}")
                        
                        # 更新PDF路径
                        dev_product.pdf_path = pdf_url
                        current_app.logger.info(f"研发产品PDF上传成功: {pdf_url}")
                    else:
                        flash(_('PDF文件上传失败，请检查文件格式和大小'), 'warning')
                        current_app.logger.warning("研发产品PDF上传失败")
                except Exception as e:
                    flash(_('PDF文件上传过程中发生错误'), 'danger')
                    current_app.logger.error(f"研发产品PDF上传异常: {str(e)}")
        
        # 检查是否需要删除图片
        if request.form.get('remove_image') == 'true' and dev_product.image_path:
            current_app.logger.debug('删除研发产品图片')
            try:
                # 使用智能存储系统删除文件（支持本地和云端）
                supabase_client = get_supabase_client()
                
                # 判断文件类型并删除
                if dev_product.image_path.startswith('http'):
                    # 云端文件，使用智能存储删除
                    delete_success = supabase_client.delete_product_file(dev_product.id, 'image', 'rd_product')
                    if delete_success:
                        current_app.logger.info(f'云端研发产品图片删除成功: {dev_product.image_path}')
                    else:
                        current_app.logger.warning(f'云端研发产品图片删除失败: {dev_product.image_path}')
                else:
                    # 本地文件，直接删除
                    image_path = os.path.join(current_app.static_folder, dev_product.image_path)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                        current_app.logger.info(f'本地研发产品图片删除成功: {image_path}')
                
                # 清空图片路径
                dev_product.image_path = None
                
            except Exception as e:
                current_app.logger.error(f'删除研发产品图片失败: {str(e)}')
                flash(_('删除图片失败，请重试'), 'warning')
        
        # 检查是否需要删除PDF文件
        if request.form.get('remove_pdf') == 'true' and dev_product.pdf_path:
            current_app.logger.debug('删除研发产品PDF文件')
            try:
                # 使用智能存储系统删除PDF文件（支持本地和云端）
                supabase_client = get_supabase_client()
                
                # 判断文件类型并删除
                if dev_product.pdf_path.startswith('http'):
                    # 云端文件，使用智能存储删除
                    delete_success = supabase_client.delete_product_file(dev_product.id, 'pdf', 'rd_product')
                    if delete_success:
                        current_app.logger.info(f'云端研发产品PDF删除成功: {dev_product.pdf_path}')
                    else:
                        current_app.logger.warning(f'云端研发产品PDF删除失败: {dev_product.pdf_path}')
                else:
                    # 本地文件，直接删除
                    pdf_path = os.path.join(current_app.static_folder, dev_product.pdf_path)
                    if os.path.exists(pdf_path):
                        os.remove(pdf_path)
                        current_app.logger.info(f'本地研发产品PDF删除成功: {pdf_path}')
                
                # 清空PDF路径
                dev_product.pdf_path = None
                
            except Exception as e:
                current_app.logger.error(f'删除研发产品PDF文件失败: {str(e)}')
                flash(_('删除PDF文件失败，请重试'), 'warning')
        
        # 处理规格字段
        try:
            # 收集规格数据（使用辅助函数）
            spec_data_list = _collect_spec_data_for_update()

            # 使用标准函数处理规格
            success, saved_specs, error_message = save_dev_product_specs(
                dev_product.id,
                spec_data_list,
                current_app.logger
            )

            if not success:
                current_app.logger.error(f"规格处理失败: {error_message}")
                flash(f'规格处理失败: {error_message}', 'warning')

        except Exception as spec_error:
            current_app.logger.error(f"规格处理异常: {str(spec_error)}")
            flash('规格处理时发生错误，请重试', 'warning')
        
        # 提交更改
        db.session.commit()
        
        # 记录变更历史
        try:
            new_values = ChangeTracker.get_new_values(dev_product, old_values.keys())
            ChangeTracker.log_update(dev_product, old_values, new_values)
        except Exception as track_err:
            current_app.logger.warning(f"记录产品变更历史失败: {str(track_err)}")
        
        # 检查是否为AJAX文件上传请求（使用辅助函数）
        is_handled, response = _handle_ajax_file_upload_response(success=True)
        if is_handled:
            return response

        flash(_('产品更新成功！'), 'success')
        return redirect(url_for('product_management.product_detail', id=id))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'更新产品失败: {str(e)}', exc_info=True)

        # 检查是否为AJAX文件上传请求（使用辅助函数）
        is_handled, response = _handle_ajax_file_upload_response(success=False, error=e)
        if is_handled:
            return response

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

    # 已入库产品删除需要二次确认（高风险操作）
    is_warehoused = dev_product.status == '已入库'
    if is_warehoused:
        # 检查是否有关联的产品库产品
        from app.models.product import Product
        linked_products_count = Product.query.filter_by(source_dev_product_id=id).count()

        # 检查是否已经二次确认
        confirm_high_risk = request.form.get('confirm_high_risk')
        if confirm_high_risk != 'yes':
            # 第一次点击，要求二次确认
            warning_msg = _('警告：该研发产品已入库')
            if linked_products_count > 0:
                warning_msg += _('，产品库中有 %d 个关联产品。删除后这些产品将失去来源追溯。') % linked_products_count
            warning_msg += _('此操作不可恢复，请再次点击删除按钮确认操作。')
            flash(warning_msg, 'warning')
            return redirect(url_for('product_management.product_detail', id=id))

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
    
    # 获取规格字段 - 通过JOIN ProductCodeField按position排序
    from sqlalchemy import case

    specs_objects = db.session.query(DevProductSpec).join(
        ProductCodeField,
        db.and_(
            ProductCodeField.subcategory_id == dev_product.subcategory_id,
            ProductCodeField.name == DevProductSpec.field_name
        ),
        isouter=True  # 左连接，保留没有匹配的规格
    ).filter(
        DevProductSpec.dev_product_id == id
    ).order_by(
        # 编码规格优先（use_in_code=True）
        case((ProductCodeField.use_in_code == True, 0), else_=1),
        # 然后按position排序
        ProductCodeField.position.asc().nullslast(),
        # 最后按规格名称排序（作为后备）
        DevProductSpec.field_name.asc()
    ).all()
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

        # 获取规格单位
        field_unit = get_field_unit(spec.field_name)

        specs.append({
            'id': spec.id,
            'field_name': spec.field_name,
            'field_value': spec.field_value,
            'field_unit': field_unit
        })

    # 查询入库审批实例
    from app.models.approval import ApprovalInstance
    approval_instance = ApprovalInstance.query.filter_by(
        object_type='rd_product',
        object_id=dev_product.id
    ).order_by(ApprovalInstance.started_at.desc()).first()

    # 检查是否已入库（查找对应的产品记录）
    from app.models.product import Product
    warehoused_product = Product.query.filter_by(
        source_dev_product_id=dev_product.id
    ).first()

    # 查询可用的入库审批流程模板
    from app.models.approval import ApprovalProcessTemplate
    available_templates = ApprovalProcessTemplate.query.filter_by(
        object_type='rd_product',
        is_active=True
    ).all()

    # 计算按钮显示权限
    locked_statuses = ['审批中', '已入库', '已取消']

    # 管理员拥有最高权限，可以编辑和删除任何状态的产品
    if current_user.role == 'admin':
        can_edit_button = True
        can_delete_button = True
    else:
        # 普通创建者只能编辑和删除未锁定状态的产品
        is_creator = current_user.id == dev_product.created_by
        can_edit_button = is_creator and dev_product.status not in locked_statuses
        can_delete_button = is_creator and dev_product.status not in locked_statuses

    return render_template('product_management/product_detail.html',
                          dev_product=dev_product,
                          specs=specs,
                          approval_instance=approval_instance,
                          warehoused_product=warehoused_product,
                          available_templates=available_templates,
                          can_edit_button=can_edit_button,
                          can_delete_button=can_delete_button)

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
        # 查找该子分类下的所有规格类型字段（包括编码和非编码规格）
        spec_fields = ProductCodeField.query.filter(
            ProductCodeField.subcategory_id == subcategory_id,
            ProductCodeField.field_type == 'spec'
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
        # 查询该子分类下的所有规格字段：
        # 1. 编码规格（use_in_code = True 或 NULL）
        # 2. 必填的非编码规格（use_in_code = False AND is_required = True）
        from sqlalchemy import or_, and_
        spec_fields = ProductCodeField.query.filter(
            ProductCodeField.subcategory_id == subcategory_id,
            ProductCodeField.field_type == 'spec',
            or_(
                ProductCodeField.use_in_code == True,
                ProductCodeField.use_in_code.is_(None),
                and_(
                    ProductCodeField.use_in_code == False,
                    ProductCodeField.is_required == True
                )
            )
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
        
        # 修改编码生成逻辑，优先使用指标值首字母，然后随机分配
        # 首先尝试使用指标值的首字母
        unique_code = None

        # 对于任何指标，首选使用首字母
        if option_value and isinstance(option_value, str):
            first_letter = option_value[0].upper()
            if first_letter.isalpha() and first_letter not in existing_codes:
                unique_code = first_letter

        # 如果首字母不可用，使用随机分配（避免所有字段都从A开始）
        if not unique_code:
            import random

            # 候选字符：A-Z + 1-9 + 0
            chars = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ') + list('123456789') + ['0']

            # 随机打乱顺序
            random.shuffle(chars)

            # 从打乱的列表中找到第一个未使用的编码
            for char in chars:
                if char not in existing_codes:
                    unique_code = char
                    break
            
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
    from flask import send_file, abort, redirect as flask_redirect
    
    dev_product = DevProduct.query.get_or_404(id)
    
    # 检查是否有PDF文件
    if not dev_product.pdf_path:
        flash(_('该产品没有PDF文件'), 'warning')
        return redirect(url_for('product_management.product_detail', id=id))
    
    # 如果是Supabase URL，直接重定向到云端URL
    if dev_product.pdf_path.startswith('http'):
        return flask_redirect(dev_product.pdf_path)
    
    # 处理本地文件
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
        
        # 获取该字段的选项
        # 支持可选参数 include_inactive：是否包含禁用的指标
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'

        if include_inactive:
            # 返回所有指标（包括禁用的）
            options = ProductCodeFieldOption.query.filter_by(
                field_id=field.id
            ).order_by(ProductCodeFieldOption.position).all()
        else:
            # 只返回启用的指标（默认行为）
            options = ProductCodeFieldOption.query.filter_by(
                field_id=field.id,
                is_active=True
            ).order_by(ProductCodeFieldOption.position).all()
        
        options_data = []
        for option in options:
            options_data.append({
                'id': option.id,
                'value': option.value,
                'code': option.code,
                'description': option.description,
                'is_active': option.is_active  # 添加启用状态
            })

        # 获取规格单位
        field_unit = get_field_unit(field.name)

        return jsonify({
            'options': options_data,
            'field_id': field.id,
            'field_name': field.name,
            'field_unit': field_unit
        })

    except Exception as e:
        current_app.logger.error(f"获取规格字段选项失败: {str(e)}")
        return jsonify({'options': []})

# 获取可用的规格字段选项（排除已选择的）
@product_management_bp.route('/api/spec-field-options/available', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def get_available_spec_options():
    """获取可用的指标选项（排除已选择的）

    参数:
        - subcategory_id: 产品名称ID
        - spec_name: 规格名称
        - field_id: 规格字段ID（可选）
        - exclude_ids: 要排除的指标ID列表（逗号分隔字符串，如"1,2,3"）
        - include_inactive: 是否包含禁用的指标（默认false）
        - include_product_values: 是否仅返回产品使用值（排除预定义选项，默认false）

    返回:
        {
            'options': [...],
            'field_id': 字段ID,
            'field_name': 字段名称,
            'field_unit': 字段单位
        }
    """
    try:
        subcategory_id = request.args.get('subcategory_id', type=int)
        spec_name = request.args.get('spec_name', '').strip()
        field_id = request.args.get('field_id', type=int)
        exclude_ids_str = request.args.get('exclude_ids', '').strip()

        # 调试日志：记录API入口参数
        current_app.logger.info(f"[API入口] get_available_spec_options 请求参数: "
                                f"subcategory_id={subcategory_id}, spec_name='{spec_name}', "
                                f"field_id={field_id}, exclude_ids='{exclude_ids_str}'")

        # 参数验证：如果提供了field_id，不需要spec_name；否则必须提供subcategory_id和spec_name
        if not field_id and (not subcategory_id or not spec_name):
            current_app.logger.warning(f"[API验证失败] 参数不足: field_id={field_id}, "
                                      f"subcategory_id={subcategory_id}, spec_name='{spec_name}'")
            return jsonify({'options': []})

        # 解析排除ID列表
        exclude_ids = []
        if exclude_ids_str:
            try:
                exclude_ids = [int(id_str.strip()) for id_str in exclude_ids_str.split(',') if id_str.strip()]
            except ValueError:
                current_app.logger.warning(f"无效的exclude_ids格式: {exclude_ids_str}")

        # 检查是否仅返回产品使用值
        include_product_values = request.args.get('include_product_values', 'false').lower() == 'true'

        # 优先使用spec_name查询所有同名字段（跨产品汇总模式）
        all_fields = []
        if spec_name:
            all_fields = ProductCodeField.query.filter_by(
                name=spec_name,
                field_type='spec'
            ).all()
            current_app.logger.info(f"[调试] 按规格名称'{spec_name}'查询到 {len(all_fields)} 个字段")

        # 备用：使用field_id查找单个字段
        elif field_id:
            field = ProductCodeField.query.get(field_id)
            if field:
                all_fields = [field]
                current_app.logger.info(f"[调试] 按field_id={field_id}查询到字段: {field.name}")

        # 兼容旧逻辑：通过产品分类和名称查找
        elif subcategory_id and spec_name:
            field = ProductCodeField.query.filter_by(
                subcategory_id=subcategory_id,
                name=spec_name,
                field_type='spec'
            ).first()
            if field:
                all_fields = [field]
                current_app.logger.info(f"[调试] 按产品分类查询到字段: {field.name}")

        if not all_fields:
            current_app.logger.warning(f"[调试] 未找到任何字段")
            return jsonify({'options': []})

        # 如果仅返回产品值，执行专门的查询逻辑
        if include_product_values:
            # 1. 汇总所有字段的预定义选项值（用于排除）
            existing_option_values = set()
            for field in all_fields:
                for option in field.options.all():
                    if option.value and option.value.strip():
                        existing_option_values.add(option.value.strip())

            # 2. 查询产品使用值（使用规格名称，而不是字段名）
            from app.models.dev_product import DevProductSpec
            from app.models.product_spec import ProductSpec

            # 使用第一个字段的名称（所有同名字段的名称应该相同）
            field_name = all_fields[0].name

            # 从研发产品表提取值
            dev_values = db.session.query(DevProductSpec.field_value)\
                .filter(DevProductSpec.field_name == field_name)\
                .distinct()\
                .all()

            # 从产品库表提取值
            product_values = db.session.query(ProductSpec.field_value)\
                .filter(ProductSpec.field_name == field_name)\
                .distinct()\
                .all()

            # 3. 合并并去重
            all_product_values = set()
            for (value,) in dev_values:
                if value and value.strip():
                    all_product_values.add(value.strip())
            for (value,) in product_values:
                if value and value.strip():
                    all_product_values.add(value.strip())

            # 4. 排除预定义值（关键逻辑）
            product_only_values = all_product_values - existing_option_values

            # 调试日志
            current_app.logger.info(f"[调试] 汇总了 {len(all_fields)} 个字段的预定义值: {existing_option_values}")
            current_app.logger.info(f"[调试] DevProductSpec查询结果: {len(dev_values)}个")
            current_app.logger.info(f"[调试] ProductSpec查询结果: {len(product_values)}个")
            current_app.logger.info(f"[调试] 合并后的产品值: {all_product_values}")
            current_app.logger.info(f"[调试] 排除预定义后: {product_only_values}")

            # 5. 获取规格单位
            field_unit = get_field_unit(field_name)

            # 6. 组装返回数据（仅产品值）
            options_data = []
            for value in sorted(product_only_values):
                options_data.append({
                    'id': None,
                    'value': value,
                    'code': '',
                    'description': '',
                    'is_active': True,
                    'source': 'product',
                    'unit': field_unit
                })

            return jsonify({
                'options': options_data,
                'field_name': field_name,
                'field_unit': field_unit
            })

        # 原有逻辑：获取预定义选项（现在从多个字段汇总）
        include_inactive = request.args.get('include_inactive', 'false').lower() == 'true'

        # 汇总所有字段的预定义选项并去重
        seen_values = {}  # {value: option对象}
        for field in all_fields:
            for option in field.options:
                # 过滤已删除的选项（兼容有/无is_deleted字段的情况）
                if hasattr(option, 'is_deleted') and option.is_deleted:
                    continue

                # 过滤不活跃的选项（根据参数）
                if not include_inactive and hasattr(option, 'is_active') and not option.is_active:
                    continue

                # 排除已选择的指标（通过exclude_ids）
                if exclude_ids and option.id in exclude_ids:
                    continue

                # 去重逻辑：同值保留is_active优先的选项
                if option.value not in seen_values:
                    seen_values[option.value] = option
                elif hasattr(option, 'is_active') and option.is_active:
                    # 如果新选项是活跃的，检查旧选项是否不活跃
                    old_is_active = hasattr(seen_values[option.value], 'is_active') and seen_values[option.value].is_active
                    if not old_is_active:
                        # 旧选项不活跃，则替换
                        seen_values[option.value] = option

        # 转换为列表
        options = list(seen_values.values())

        # 按position排序（如果有的话）
        options.sort(key=lambda x: (x.position if x.position is not None else 9999, x.value))

        # 获取规格单位
        field_name = all_fields[0].name
        field_unit = get_field_unit(field_name)

        # 调试日志
        current_app.logger.info(f"[调试] 汇总了 {len(all_fields)} 个字段的预定义选项")
        current_app.logger.info(f"[调试] 去重后选项数: {len(options)}")
        current_app.logger.info(f"[调试] 排除的ID: {exclude_ids}")

        # 组装返回数据
        options_data = []
        for option in options:
            options_data.append({
                'id': option.id,
                'value': option.value,
                'code': option.code,
                'description': option.description or '',
                'is_active': option.is_active,
                'unit': field_unit
            })

        return jsonify({
            'options': options_data,
            'field_name': field_name,
            'field_unit': field_unit
        })

    except Exception as e:
        current_app.logger.error(f"获取可用规格字段选项失败: {str(e)}")
        return jsonify({'options': []})

@product_management_bp.route('/api/spec-field-options/add', methods=['POST'])
@login_required
@permission_required('product_code', 'edit')
def add_spec_field_option():
    """快速添加规格字段选项"""
    try:
        data = request.get_json()

        subcategory_id = data.get('subcategory_id')
        spec_name = data.get('spec_name')
        field_id = data.get('field_id')
        value = data.get('value', '').strip()
        description = data.get('description', '').strip()

        # 验证必填字段
        if not subcategory_id or not spec_name or not value:
            return jsonify({
                'success': False,
                'message': '缺少必填字段'
            }), 400

        # 查找规格字段
        if field_id:
            spec_field = ProductCodeField.query.get(field_id)
        else:
            spec_field = ProductCodeField.query.filter_by(
                subcategory_id=subcategory_id,
                name=spec_name,
                field_type='spec'
            ).first()

        if not spec_field:
            return jsonify({
                'success': False,
                'message': '找不到对应的规格字段'
            }), 404

        # 检查是否已存在相同的指标值
        existing_option = ProductCodeFieldOption.query.filter_by(
            field_id=spec_field.id,
            value=value
        ).first()

        if existing_option:
            return jsonify({
                'success': False,
                'message': f'指标值 "{value}" 已存在'
            }), 400

        # 生成唯一编码（随机分配，避免所有字段都从A开始）
        existing_codes = [opt.code for opt in ProductCodeFieldOption.query.filter_by(
            field_id=spec_field.id
        ).all() if opt.code]

        # 生成编码逻辑（使用随机打乱，增加MN编码的区分度）
        import random

        unique_code = None
        # 候选字符：A-Z + 1-9 + 0
        chars = list('ABCDEFGHIJKLMNOPQRSTUVWXYZ') + list('123456789') + ['0']

        # 随机打乱顺序（避免所有字段都从A开始）
        random.shuffle(chars)

        # 从打乱的列表中找到第一个未使用的编码
        for char in chars:
            if char not in existing_codes:
                unique_code = char
                break

        # 如果所有编码都已使用（理论上不应该发生）
        if not unique_code:
            unique_code = '0'

        # 获取当前最大position
        max_position = db.session.query(db.func.max(ProductCodeFieldOption.position))\
            .filter_by(field_id=spec_field.id).scalar() or 0

        # 创建新选项
        new_option = ProductCodeFieldOption(
            field_id=spec_field.id,
            value=value,
            code=unique_code,
            description=description or f'快速添加的指标',
            is_active=True,
            position=max_position + 1
        )

        db.session.add(new_option)
        db.session.commit()

        current_app.logger.info(f"快速添加指标成功: {spec_name} - {value} ({unique_code})")

        # 获取规格单位
        field_unit = get_field_unit(spec_field.name)

        return jsonify({
            'success': True,
            'message': '指标添加成功',
            'new_item': {
                'id': new_option.id,
                'value': new_option.value,
                'code': new_option.code,
                'description': new_option.description,
                'unit': field_unit
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'快速添加指标失败: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'添加失败: {str(e)}'
        }), 500

@product_management_bp.route('/api/product/<int:product_id>/specs', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def get_product_specs(product_id):
    """获取产品的现有规格数据"""
    try:
        # 获取产品信息
        product = DevProduct.query.get(product_id)
        if not product:
            return jsonify({'specs': []})
        
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
            
            # 尝试获取规格的position信息
            if product.subcategory_id and spec.field_name:
                spec_field = ProductCodeField.query.filter_by(
                    subcategory_id=product.subcategory_id,
                    name=spec.field_name
                ).first()
                if spec_field:
                    spec_data['position'] = spec_field.position
                else:
                    spec_data['position'] = 999  # 未找到position的默认值
            else:
                spec_data['position'] = 999
            
            specs_data.append(spec_data)

        # 按position排序specs_data
        specs_data.sort(key=lambda x: x.get('position', 999))

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

        # 优先检查正式产品库（产品库新建应先检查产品库）
        from app.models.product import Product
        formal_product = Product.query.filter(
            Product.product_mn == mn_code
        ).first()

        # 如果产品库已存在，立即返回，不再检查研发库
        if formal_product:
            return jsonify({
                'exists': True,
                'source': 'formal',
                'product_model': formal_product.model
            })

        # 产品库不存在重复，再检查研发产品库
        dev_query = DevProduct.query.filter(
            DevProduct.mn_code == mn_code
        )
        if exclude_product_id:
            dev_query = dev_query.filter(DevProduct.id != exclude_product_id)

        dev_product = dev_query.first()

        if dev_product:
            return jsonify({
                'exists': True,
                'source': 'dev',
                'product_model': dev_product.model if hasattr(dev_product, 'model') else None
            })

        # 都不存在重复
        return jsonify({'exists': False})
            
    except Exception as e:
        current_app.logger.error(f"检查MN编码重复失败: {str(e)}")
        return jsonify({'exists': False, 'error': str(e)})

# 上传研发产品图片
@product_management_bp.route('/api/rd-products/<int:product_id>/upload-image', methods=['POST'])
@login_required
@permission_required('product_code', 'edit')
def upload_rd_product_image(product_id):
    """上传研发产品图片"""
    try:
        # 获取产品
        dev_product = DevProduct.query.get_or_404(product_id)
        
        # 检查权限：只有管理员或产品创建者可以上传图片
        if current_user.role != 'admin' and current_user.id != dev_product.created_by:
            return jsonify({'success': False, 'error': '您没有权限上传此产品的图片'}), 403
        
        # 检查是否有图片文件
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': '请选择图片文件'}), 400
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'success': False, 'error': '请选择图片文件'}), 400
        
        # 验证文件类型
        allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
        if not ('.' in image_file.filename and 
                image_file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({'success': False, 'error': '不支持的图片格式！请选择 JPG、PNG 或 GIF 文件'}), 400
        
        # 验证文件大小 (12MB)
        max_size = 12 * 1024 * 1024
        image_file.seek(0, 2)  # 移动到文件末尾
        file_size = image_file.tell()
        image_file.seek(0)  # 回到文件开始
        
        if file_size > max_size:
            return jsonify({
                'success': False, 
                'error': f'图片文件太大！最大允许 12MB，当前文件: {file_size / (1024*1024):.1f}MB'
            }), 400
        
        # 使用Supabase服务上传图片
        from app.utils.supabase_client import get_supabase_client
        supabase_client = get_supabase_client()
        
        if supabase_client:
            # 上传到Supabase
            image_url = supabase_client.upload_product_file(dev_product.id, image_file, 'image', 'rd_product')
            if image_url:
                # 更新数据库
                dev_product.image_path = image_url
                dev_product.updated_at = datetime.now()
                db.session.commit()
                
                current_app.logger.info(f"研发产品 {dev_product.id} 图片上传成功: {image_url}")
                return jsonify({'success': True, 'image_url': image_url})
            else:
                return jsonify({'success': False, 'error': '上传到云端存储失败'}), 500
        else:
            return jsonify({'success': False, 'error': '云端存储服务不可用'}), 500
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"上传研发产品图片失败: {str(e)}")
        return jsonify({'success': False, 'error': f'上传失败: {str(e)}'}), 500

# 更新研发产品阶段
@product_management_bp.route('/api/rd-products/<int:product_id>/update-stage', methods=['POST'])
@login_required
@permission_required('product_code', 'edit')
def update_rd_product_stage(product_id):
    """更新研发产品阶段"""
    try:
        # 获取产品
        dev_product = DevProduct.query.get_or_404(product_id)
        
        # 检查权限：只有管理员或产品创建者可以更新阶段
        if current_user.role != 'admin' and current_user.id != dev_product.created_by:
            return jsonify({
                'success': False, 
                'message': '您没有权限更新此产品的阶段'
            }), 403
        
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据格式错误'
            }), 400
            
        target_stage = data.get('current_stage')
        description = data.get('description', '')
        
        if not target_stage:
            return jsonify({
                'success': False,
                'message': '目标阶段不能为空'
            }), 400
        
        # 验证阶段是否有效
        from app.config.stage_configs import get_stage_by_key
        stage_info = get_stage_by_key('rd_product', target_stage)
        if not stage_info:
            return jsonify({
                'success': False,
                'message': f'无效的阶段: {target_stage}'
            }), 400
        
        # 检查阶段推进是否被阻止
        can_advance, reason = dev_product.can_advance_to_stage(target_stage)
        if not can_advance:
            return jsonify({
                'success': False,
                'message': reason,
                'blocked': True
            }), 400
        
        # 更新阶段
        old_stage = dev_product.current_stage_key
        dev_product.update_stage(
            target_stage, 
            user_id=current_user.id,
            description=description
        )
        
        # 提交数据库更改
        db.session.commit()

        current_app.logger.info(f"用户 {current_user.username} 将研发产品 {dev_product.id} 的阶段从 {old_stage} 更新为 {target_stage}")

        # 返回成功响应
        response_data = {
            'success': True,
            'message': f'阶段已更新为: {stage_info["name"]}',
            'new_stage': target_stage,
            'stage_name': stage_info['name']
        }

        return jsonify(response_data)
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新研发产品阶段失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500


@product_management_bp.route('/api/rd-products/<int:product_id>/stage-records', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def get_stage_records(product_id):
    """获取研发产品的阶段记录（支持层级化查询）"""
    try:
        dev_product = DevProduct.query.get_or_404(product_id)

        # 获取查询的阶段keys参数
        stage_keys_param = request.args.get('stage_keys', '')
        stage_keys = [key.strip() for key in stage_keys_param.split(',') if key.strip()] if stage_keys_param else []

        # 获取阶段记录 (存储在JSON字段中)
        all_stage_records = getattr(dev_product, 'stage_records', []) or []

        # 如果指定了stage_keys，则按阶段过滤记录
        if stage_keys:
            filtered_records = []
            for record in all_stage_records:
                # 确保记录有stage_key字段，如果没有则跳过
                if 'stage_key' in record and record['stage_key'] in stage_keys:
                    filtered_records.append(record)
        else:
            # 如果没有指定stage_keys，返回所有记录
            filtered_records = all_stage_records

        return jsonify({
            'success': True,
            'records': filtered_records
        })

    except Exception as e:
        current_app.logger.error(f"获取阶段记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@product_management_bp.route('/api/rd-products/<int:product_id>/stage-records', methods=['POST'])
@login_required
@permission_required('product_code', 'edit')
def add_stage_record(product_id):
    """添加研发产品阶段记录"""
    try:
        dev_product = DevProduct.query.get_or_404(product_id)
        
        # 检查权限：只有创建者可以添加记录
        if dev_product.created_by != current_user.id:
            return jsonify({
                'success': False,
                'message': '只有产品创建者可以添加阶段记录'
            }), 403
        
        data = request.get_json()
        content = data.get('content', '').strip()
        stage_key = data.get('stage_key', '')
        
        if not content:
            return jsonify({
                'success': False,
                'message': '记录内容不能为空'
            }), 400
        
        # 创建新记录
        new_record = {
            'id': int(time.time() * 1000),  # 使用时间戳作为临时ID
            'content': content,
            'stage_key': stage_key,
            'created_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'creator_id': current_user.id,
            'creator_name': current_user.username or current_user.real_name or '未知用户'
        }
        
        # 获取现有记录
        stage_records = getattr(dev_product, 'stage_records', []) or []
        
        # 添加新记录到开头（最新的在上面）
        stage_records.insert(0, new_record)
        
        # 更新产品记录（需要通过setattr触发更新）
        setattr(dev_product, 'stage_records', stage_records)
        
        # 标记字段为已修改（对于JSON字段很重要）
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(dev_product, 'stage_records')
        
        # 提交到数据库
        db.session.commit()
        
        current_app.logger.info(f"用户 {current_user.username} 为研发产品 {product_id} 添加了阶段记录")
        
        return jsonify({
            'success': True,
            'message': '阶段记录已保存',
            'record': new_record
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"添加阶段记录失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'保存失败: {str(e)}'
        }), 500


@product_management_bp.route('/api/rd-products/<int:product_id>/stage-records/<int:record_id>', methods=['DELETE'])
@login_required
@permission_required('product_code', 'edit')
def delete_stage_record(product_id, record_id):
    """删除研发产品阶段记录（仅创建者）"""
    try:
        dev_product = DevProduct.query.get_or_404(product_id)

        # 只有产品创建者可删
        if dev_product.created_by != current_user.id:
            return jsonify({'success': False, 'message': '只有产品创建者可以删除阶段记录'}), 403

        stage_records = getattr(dev_product, 'stage_records', []) or []
        new_records = [r for r in stage_records if int(r.get('id', -1)) != int(record_id)]
        if len(new_records) == len(stage_records):
            return jsonify({'success': False, 'message': '记录不存在或已删除'}), 404

        setattr(dev_product, 'stage_records', new_records)
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(dev_product, 'stage_records')
        db.session.commit()

        return jsonify({'success': True})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除阶段记录失败: {str(e)}")
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


@product_management_bp.route('/api/rd-products/<int:product_id>/stage-attachments', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def get_stage_attachments(product_id):
    """获取阶段附件列表（支持层级化查询）"""
    try:
        dev_product = DevProduct.query.get_or_404(product_id)

        from app.models.gantt_models import StageAttachment

        # 支持两种参数方式：单个stage_key或多个stage_keys
        stage_key = request.args.get('stage_key')
        stage_keys_param = request.args.get('stage_keys', '')

        # 构建查询条件
        query = StageAttachment.query.filter_by(product_id=product_id)

        if stage_keys_param:
            # 支持多阶段查询（新的层级化功能）
            stage_keys = [key.strip() for key in stage_keys_param.split(',') if key.strip()]
            if stage_keys:
                query = query.filter(StageAttachment.stage_key.in_(stage_keys))
        elif stage_key:
            # 保持对单个stage_key的向后兼容
            query = query.filter_by(stage_key=stage_key)
        
        attachments = query.order_by(StageAttachment.uploaded_at.desc()).all()
        
        # 转换为前端格式
        attachment_list = []
        for att in attachments:
            attachment_list.append({
                'id': att.id,
                'file_name': att.file_name,
                'file_path': att.file_path,
                'file_size': att.file_size,
                'file_size_mb': att.file_size_mb,
                'file_type': att.file_type,
                'stage_key': att.stage_key,
                'uploaded_at': att.uploaded_at.strftime('%Y-%m-%d %H:%M:%S'),
                'uploader_name': att.uploader.real_name or att.uploader.username if att.uploader else '未知',
                'description': att.description
            })
        
        return jsonify({
            'success': True,
            'attachments': attachment_list
        })
        
    except Exception as e:
        current_app.logger.error(f"获取阶段附件失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@product_management_bp.route('/api/rd-products/<int:product_id>/stage-attachments/upload', methods=['POST'])
@login_required
@permission_required('product_code', 'edit')
def upload_stage_attachment(product_id):
    """上传阶段附件到Supabase"""
    try:
        dev_product = DevProduct.query.get_or_404(product_id)
        
        # 检查权限：只有创建者和管理员可以上传附件
        if current_user.role != 'admin' and current_user.id != dev_product.created_by:
            return jsonify({
                'success': False,
                'message': '您没有权限上传此产品的附件'
            }), 403
        
        # 检查文件
        if 'attachment' not in request.files:
            return jsonify({
                'success': False, 
                'message': '请选择要上传的文件'
            }), 400
        
        file = request.files['attachment']
        stage_key = request.form.get('stage_key')
        description = request.form.get('description', '')
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '请选择要上传的文件'
            }), 400
            
        if not stage_key:
            return jsonify({
                'success': False,
                'message': '缺少阶段信息'
            }), 400
        
        # 验证文件类型
        allowed_extensions = {
            'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 
            'txt', 'zip', 'rar', '7z', 'jpg', 'jpeg', 'png', 'gif'
        }
        if not ('.' in file.filename and 
                file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({
                'success': False,
                'message': '不支持的文件格式！请选择文档、图片或压缩文件'
            }), 400
        
        # 验证文件大小 (20MB)
        max_size = 20 * 1024 * 1024
        file.seek(0, 2)  # 移动到文件末尾
        file_size = file.tell()
        file.seek(0)  # 回到开头
        
        if file_size > max_size:
            return jsonify({
                'success': False,
                'message': '文件大小不能超过20MB'
            }), 400
        
        # 上传到Supabase
        supabase_client = get_supabase_client()
        if not supabase_client:
            return jsonify({
                'success': False,
                'message': 'Supabase存储服务不可用'
            }), 500
        
        # 生成文件路径
        import uuid
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        file_path = f"products/{product_id}/stages/{stage_key}/{unique_filename}"
        
        # 根据文件扩展名判断文件类型
        if file_extension in ['jpg', 'jpeg', 'png', 'gif']:
            file_type = 'image'
        elif file_extension == 'pdf':
            file_type = 'pdf'
        else:
            file_type = 'attachment'  # 新增的附件类型
        
        # 使用现有的 upload_product_file 方法
        file_url = supabase_client.upload_product_file(
            product_id=product_id,
            file=file,
            file_type=file_type,
            bucket_type='rd_product'
        )
        
        if file_url:
            # 从URL中提取文件路径
            import re
            # URL格式: https://xxx.supabase.co/storage/v1/object/public/rd-product-images/rd_product_files/xxx/xxx/filename
            file_path_match = re.search(r'rd_product_files/(.+)$', file_url)
            file_path = file_path_match.group(0) if file_path_match else unique_filename
            
            current_app.logger.info(f"附件上传成功: {file_url}")
        else:
            return jsonify({
                'success': False,
                'message': '文件上传失败'
            }), 500
        
        # 保存附件记录到数据库
        from app.models.gantt_models import StageAttachment
        
        attachment = StageAttachment(
            product_id=product_id,
            stage_key=stage_key,
            file_name=file.filename,
            file_path=file_url,  # 保存完整的URL
            file_size=file_size,
            file_type=file_extension,  # 使用文件扩展名而非 content_type
            uploaded_by=current_user.id,
            description=description
        )
        
        db.session.add(attachment)
        db.session.commit()
        
        current_app.logger.info(f"用户 {current_user.username} 为研发产品 {product_id} 上传了阶段附件")
        
        return jsonify({
            'success': True,
            'message': '附件上传成功',
            'attachment': {
                'id': attachment.id,
                'file_name': attachment.file_name,
                'file_size_mb': attachment.file_size_mb,
                'file_type': attachment.file_type,
                'uploaded_at': attachment.uploaded_at.strftime('%Y-%m-%d %H:%M:%S')
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"上传阶段附件失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'上传失败: {str(e)}'
        }), 500


@product_management_bp.route('/api/rd-products/<int:product_id>/stage-attachments/<int:attachment_id>', methods=['DELETE'])
@login_required
@permission_required('product_code', 'edit')
def delete_stage_attachment(product_id, attachment_id):
    """删除阶段附件"""
    try:
        from app.models.gantt_models import StageAttachment
        
        attachment = StageAttachment.query.filter_by(
            id=attachment_id, 
            product_id=product_id
        ).first_or_404()
        
        # 检查权限：只有上传者和管理员可以删除
        if current_user.role != 'admin' and current_user.id != attachment.uploaded_by:
            return jsonify({
                'success': False,
                'message': '您没有权限删除此附件'
            }), 403
        
        # 从Supabase删除文件
        cloud_delete_success = True
        if attachment.file_path:
            current_app.logger.info(f"准备删除研发产品附件: ID={attachment.id}, 文件名={attachment.file_name}, 路径={attachment.file_path}")
            supabase_client = get_supabase_client()
            if supabase_client:
                # 指定正确的bucket_type为rd_product
                current_app.logger.info(f"使用bucket_type='rd_product'删除云端文件: {attachment.file_path}")
                cloud_delete_success = supabase_client.delete_file_by_url(attachment.file_path, 'rd_product')
                if cloud_delete_success:
                    current_app.logger.info(f"✅ 云端文件删除成功: {attachment.file_path}")
                else:
                    current_app.logger.warning(f"❌ 云端文件删除失败: {attachment.file_path}")
                    # 注意：云端删除失败不阻止数据库删除，但会记录警告
            else:
                current_app.logger.warning("Supabase客户端不可用，跳过云端文件删除")
                cloud_delete_success = False
        
        # 删除数据库记录
        db.session.delete(attachment)
        db.session.commit()
        
        current_app.logger.info(f"用户 {current_user.username} 删除了附件 {attachment.file_name}")
        
        # 根据云端删除结果返回相应消息
        if cloud_delete_success:
            message = '附件删除成功'
        else:
            message = '附件数据库记录已删除，但云端文件删除失败'
        
        return jsonify({
            'success': True,
            'message': message,
            'cloud_delete_success': cloud_delete_success
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除阶段附件失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500

# 下载阶段附件（使用与删除一致的地址：数据库保存的公有URL）
@product_management_bp.route('/api/rd-products/<int:product_id>/stage-attachments/<int:attachment_id>/download', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def download_stage_attachment(product_id, attachment_id):
    """下载阶段附件：直接重定向到保存的公有URL，并附加download参数"""
    try:
        # 延迟导入，避免循环依赖
        from app.models.gantt_models import StageAttachment

        # 获取产品（确保产品存在）
        dev_product = DevProduct.query.get_or_404(product_id)

        # 兜底校验查看权限
        if not current_user.has_permission('product_code', 'view'):
            return jsonify({'success': False, 'message': '您没有权限访问此附件'}), 403

        # 获取附件记录
        attachment = StageAttachment.query.filter_by(
            id=attachment_id,
            product_id=product_id
        ).first()

        if not attachment or not attachment.file_path:
            return jsonify({'success': False, 'message': '附件不存在或未找到文件路径'}), 404

        # 直接重定向到公有URL，附带download参数强制下载
        from urllib.parse import quote
        download_url = f"{attachment.file_path}?download={quote(attachment.file_name or 'download')}"
        return redirect(download_url)

    except Exception as e:
        current_app.logger.error(f"下载阶段附件失败: {str(e)}")
        return jsonify({'success': False, 'message': f'下载失败: {str(e)}'}), 500


# ================== 研发产品子阶段（里程碑）API ==================

@product_management_bp.route('/api/rd-products/<int:product_id>/stages', methods=['POST'])
@login_required
@permission_required('product_code', 'edit')
def create_rd_product_sub_stage(product_id):
    """创建研发产品的子阶段（使用 DevProductMilestone 持久化）"""
    try:
        from app.models.gantt_models import DevProductMilestone

        # 产品存在性校验
        dev_product = DevProduct.query.get_or_404(product_id)

        # 权限：管理员或创建者
        if current_user.role != 'admin' and current_user.id != dev_product.created_by:
            return jsonify({'success': False, 'message': '您没有权限创建子阶段'}), 403

        data = request.get_json(silent=True) or {}
        stage_data = data.get('stage_data') or data  # 兼容两种传参

        name = (stage_data or {}).get('name', '').strip()
        stage_key = (stage_data or {}).get('parent_stage', '').strip()
        description = (stage_data or {}).get('description', '')
        progress = int((stage_data or {}).get('progress') or 0)
        status = (stage_data or {}).get('status') or 'planned'
        start_date_raw = (stage_data or {}).get('start_date')
        end_date_raw = (stage_data or {}).get('end_date')

        if not name or not stage_key:
            return jsonify({'success': False, 'message': '阶段名称与所属主阶段不能为空'}), 400

        # 日期解析
        def parse_date(val):
            if not val:
                return None
            try:
                from datetime import datetime
                if isinstance(val, str):
                    v = val.replace('Z', '+00:00')
                    try:
                        return datetime.fromisoformat(v)
                    except Exception:
                        # 兼容仅日期
                        return datetime.strptime(val[:10], '%Y-%m-%d')
                return None
            except Exception:
                return None

        planned_start = parse_date(start_date_raw)
        planned_end = parse_date(end_date_raw)

        milestone = DevProductMilestone(
            product_id=product_id,
            stage_key=stage_key,
            name=name,
            description=description,
            planned_start_date=planned_start,
            planned_end_date=planned_end,
            status=status,
            progress=progress,
            created_by=current_user.id
        )

        db.session.add(milestone)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '子阶段创建成功',
            'id': milestone.id,
            'stage': {
                'id': milestone.id,
                'name': milestone.name,
                'parent': milestone.stage_key,
                'start_date': milestone.planned_start_date.isoformat() if milestone.planned_start_date else None,
                'end_date': milestone.planned_end_date.isoformat() if milestone.planned_end_date else None,
                'progress': milestone.progress,
                'status': milestone.status,
                'description': milestone.description
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"创建子阶段失败: {str(e)}")
        return jsonify({'success': False, 'message': f'创建失败: {str(e)}'}), 500


@product_management_bp.route('/api/rd-products/<int:product_id>/stages', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def list_rd_product_sub_stages(product_id):
    """获取研发产品的子阶段（里程碑）列表"""
    try:
        from app.models.gantt_models import DevProductMilestone

        # 确认产品存在
        DevProduct.query.get_or_404(product_id)

        # 查询该产品的所有里程碑
        milestones = (DevProductMilestone
                      .query
                      .filter_by(product_id=product_id)
                      .order_by(DevProductMilestone.created_at.asc())
                      .all())

        def iso(dt):
            return dt.isoformat() if dt else None

        stages = []
        for m in milestones:
            stages.append({
                'id': m.id,
                'name': m.name,
                'stage_key': m.stage_key,
                'description': m.description or '',
                'status': m.status or 'planned',
                'progress': m.progress or 0,
                'start_date': iso(m.planned_start_date),
                'end_date': iso(m.planned_end_date),
                'created_at': iso(m.created_at),
                'updated_at': iso(m.updated_at)
            })

        return jsonify({'success': True, 'stages': stages})

    except Exception as e:
        current_app.logger.error(f"获取子阶段列表失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取失败: {str(e)}'}), 500


@product_management_bp.route('/api/rd-products/<int:product_id>/stages/<int:stage_id>', methods=['DELETE'])
@login_required
@permission_required('product_code', 'edit')
def delete_rd_product_sub_stage(product_id, stage_id):
    """删除研发产品子阶段（里程碑）"""
    try:
        from app.models.gantt_models import DevProductMilestone

        dev_product = DevProduct.query.get_or_404(product_id)

        # 权限：管理员或产品创建者
        if current_user.role != 'admin' and current_user.id != dev_product.created_by:
            return jsonify({'success': False, 'message': '您没有权限删除子阶段'}), 403

        milestone = DevProductMilestone.query.filter_by(id=stage_id, product_id=product_id).first()
        if not milestone:
            return jsonify({'success': False, 'message': '子阶段不存在'}), 404

        db.session.delete(milestone)
        db.session.commit()

        return jsonify({'success': True, 'message': '子阶段删除成功'})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除子阶段失败: {str(e)}")
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


@product_management_bp.route('/api/rd-products/<int:product_id>/stages/<int:stage_id>', methods=['PUT'])
@login_required
@permission_required('product_code', 'edit')
def update_rd_product_sub_stage(product_id, stage_id):
    """更新研发产品子阶段（里程碑）"""
    try:
        from app.models.gantt_models import DevProductMilestone

        dev_product = DevProduct.query.get_or_404(product_id)

        # 权限：管理员或产品创建者
        if current_user.role != 'admin' and current_user.id != dev_product.created_by:
            return jsonify({'success': False, 'message': '您没有权限更新子阶段'}), 403

        milestone = DevProductMilestone.query.filter_by(id=stage_id, product_id=product_id).first()
        if not milestone:
            return jsonify({'success': False, 'message': '子阶段不存在'}), 404

        data = request.get_json(silent=True) or {}
        stage_data = data.get('stage_data') or data

        def parse_date(val):
            if not val:
                return None
            try:
                from datetime import datetime
                v = str(val).replace('Z', '+00:00')
                try:
                    return datetime.fromisoformat(v)
                except Exception:
                    return datetime.strptime(v[:10], '%Y-%m-%d')
            except Exception:
                return None

        # 更新字段（仅提供的项）
        if 'name' in stage_data:
            milestone.name = (stage_data.get('name') or '').strip() or milestone.name
        if 'parent_stage' in stage_data:
            milestone.stage_key = (stage_data.get('parent_stage') or milestone.stage_key)
        if 'description' in stage_data:
            milestone.description = stage_data.get('description') or ''
        if 'status' in stage_data:
            milestone.status = stage_data.get('status') or milestone.status
        if 'progress' in stage_data:
            try:
                milestone.progress = int(stage_data.get('progress') or 0)
            except Exception:
                pass
        if 'start_date' in stage_data:
            milestone.planned_start_date = parse_date(stage_data.get('start_date'))
        if 'end_date' in stage_data:
            milestone.planned_end_date = parse_date(stage_data.get('end_date'))

        db.session.commit()

        return jsonify({'success': True, 'message': '子阶段更新成功'})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新子阶段失败: {str(e)}")
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500


@product_management_bp.route('/api/rd-products/<int:product_id>/main-stage/plan', methods=['PUT'])
@login_required
@permission_required('product_code', 'edit')
def update_rd_product_main_stage_plan(product_id):
    """更新研发产品主阶段的计划起止时间（持久化到stage_history JSON中）"""
    try:
        dev_product = DevProduct.query.get_or_404(product_id)

        # 权限：管理员或产品创建者
        if current_user.role != 'admin' and current_user.id != dev_product.created_by:
            return jsonify({'success': False, 'message': '您没有权限更新主阶段计划'}), 403

        data = request.get_json(silent=True) or {}
        stage_key = data.get('stage_key')
        planned_start_date = data.get('planned_start_date')  # ISO或YYYY-MM-DD
        planned_end_date = data.get('planned_end_date')
        progress = data.get('progress')
        status = (data.get('status') or '').strip()  # in-progress/paused/completed 或空

        if not stage_key:
            return jsonify({'success': False, 'message': '缺少阶段标识 stage_key'}), 400

        # 解析日期
        def parse_date(val):
            if not val:
                return None
            from datetime import datetime
            v = str(val).replace('Z', '+00:00')
            try:
                dt = datetime.fromisoformat(v)
            except Exception:
                try:
                    dt = datetime.strptime(v[:10], '%Y-%m-%d')
                except Exception:
                    dt = None
            return dt.strftime('%Y-%m-%d %H:%M:%S') if dt else None

        planned_start = parse_date(planned_start_date)
        planned_end = parse_date(planned_end_date)

        # 更新或插入对应阶段的计划字段
        history = dev_product.stage_history or []
        updated = False
        for rec in history:
            if rec.get('stage') == stage_key:
                rec['plannedStart'] = planned_start
                rec['plannedEnd'] = planned_end
                if progress is not None:
                    try:
                        rec['progress'] = int(progress)
                    except Exception:
                        pass
                updated = True
                break
        if not updated:
            # 若不存在该阶段记录，创建一个仅含计划信息的记录
            new_rec = {
                'stage': stage_key,
                'plannedStart': planned_start,
                'plannedEnd': planned_end
            }
            if progress is not None:
                try:
                    new_rec['progress'] = int(progress)
                except Exception:
                    pass
            history.append(new_rec)

        from sqlalchemy.orm.attributes import flag_modified
        dev_product.stage_history = history
        flag_modified(dev_product, 'stage_history')
        dev_product.updated_at = datetime.now()
        # 如果带有状态更新，按照规则同步产品阶段
        from app.config.stage_configs import get_next_stage
        # current_stage_key 基于产品 status 映射
        current_stage_key = dev_product.current_stage_key
        new_stage_key = None
        if status == 'in-progress':
            # 如果切换到当前主阶段进行中且产品还不在该阶段，则推进到该阶段
            if current_stage_key != stage_key:
                new_stage_key = stage_key
        elif status == 'completed':
            # 如果当前产品正处于该主阶段，推进到下一阶段
            if current_stage_key == stage_key:
                nxt = get_next_stage('rd_product', current_stage_key)
                if nxt:
                    new_stage_key = nxt.get('key') or nxt.get('stage')
        # 暂停状态不改变产品阶段

        if new_stage_key:
            # 使用模型自带方法推进阶段（会写入历史并更新status）
            dev_product.update_stage(new_stage_key, user_id=current_user.id,
                                     description=f'甘特图同步：{stage_key} 完成/启动 → {new_stage_key}')

        db.session.commit()

        return jsonify({'success': True, 'message': '主阶段计划已更新',
                        'synced_stage': new_stage_key or current_stage_key})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新主阶段计划失败: {str(e)}")
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500


# ============================================================================
# 产品关联配置相关API
# ============================================================================

@product_management_bp.route('/api/product/<int:product_id>/relations', methods=['GET'])
@login_required
def get_product_relations(product_id):
    """
    获取产品的关联配置列表

    支持互斥组分组显示：
    - 互斥组内的产品会被分组在一起
    - 每个互斥组有自己的显示名称、选择模式、是否必选等属性
    - 普通关联产品单独列出

    Returns:
        {
            'success': True,
            'data': [...],  # 普通关联产品列表
            'groups': {...},  # 互斥组字典 {group_id: {name, is_required, selection_mode, products: [...]}}
            'total': int
        }
    """
    try:
        from app.models.product import Product
        from app.models.product_relation import ProductRelation

        # 验证产品存在
        product = Product.query.get_or_404(product_id)

        # 查询产品级关联，按关联产品的产品名称降序排序
        relations_query = ProductRelation.query.join(
            Product,
            ProductRelation.related_product_id == Product.id
        ).filter(
            ProductRelation.main_product_type == ProductRelation.MAIN_TYPE_PRODUCT,
            ProductRelation.main_product_id == product_id,
            ProductRelation.is_active == True
        ).order_by(
            ProductRelation.display_order.asc(),
            Product.product_name.desc()
        ).all()

        # 分离普通关联和互斥组关联
        normal_relations = []
        mutual_groups = {}

        for relation in relations_query:
            if not relation.related_product:
                continue

            # 使用自定义CSS类名映射
            badge_class_map = {
                'required_accessory': 'badge relation-type-badge relation-type-required rounded-pill',
                'recommended': 'badge relation-type-badge relation-type-recommended rounded-pill',
                'required_mutual': 'badge relation-type-badge relation-type-required-mutual rounded-pill',
                'optional_mutual': 'badge relation-type-badge relation-type-optional-mutual rounded-pill'
            }
            badge_class = badge_class_map.get(relation.relation_type, 'badge relation-type-badge relation-type-unknown rounded-pill')

            # 构建关联产品基本信息
            relation_info = {
                'id': relation.id,
                'related_product_id': relation.related_product_id,
                'product_name': relation.related_product.product_name or relation.related_product.model or '',
                'product_model': relation.related_product.model or relation.related_product.product_name or '',
                'product_mn': relation.related_product.product_mn,
                'brand': relation.related_product.brand or '',  # 品牌
                'specification': relation.related_product.specification or '',  # 产品描述
                'retail_price': float(relation.related_product.retail_price) if relation.related_product.retail_price else 0,  # 市场价格
                'unit': relation.related_product.unit or 'Set',  # 单位
                'relation_type': relation.relation_type,
                'relation_type_label': ProductRelation.get_relation_type_label(relation.relation_type),
                'relation_type_label_class': badge_class,
                'default_quantity': relation.default_quantity,
                'is_required': relation.is_required,
                'is_default': relation.is_default or False  # 是否为互斥组默认选项
            }

            # 判断是否属于互斥组
            if relation.is_in_mutual_exclusion_group():
                group_id = relation.mutual_exclusion_group

                # 如果该互斥组还未初始化，创建组信息
                if group_id not in mutual_groups:
                    is_required = relation.is_group_required or False
                    # 互斥组徽章样式
                    group_badge_class = badge_class_map.get(
                        'required_mutual' if is_required else 'optional_mutual',
                        'badge relation-type-badge relation-type-unknown rounded-pill'
                    )
                    mutual_groups[group_id] = {
                        'group_id': group_id,
                        'group_name': relation.group_display_name or group_id,
                        'is_required': is_required,
                        'selection_mode': relation.group_selection_mode or 'single',
                        'badge_class': group_badge_class,  # 添加徽章样式类
                        'badge_label': '必选互斥' if is_required else '可选互斥',  # 添加徽章文字
                        'products': []
                    }

                # 将产品添加到对应的互斥组
                mutual_groups[group_id]['products'].append(relation_info)
            else:
                # 普通关联产品
                normal_relations.append(relation_info)

        # 计算总数
        total_count = len(normal_relations) + sum(len(group['products']) for group in mutual_groups.values())

        return jsonify({
            'success': True,
            'data': normal_relations,  # 普通关联产品
            'groups': mutual_groups,   # 互斥组字典
            'total': total_count
        })

    except Exception as e:
        logger.error(f"获取产品关联失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取产品关联失败: {str(e)}'}), 500


@product_management_bp.route('/api/product/<int:product_id>/relations/<int:relation_id>', methods=['DELETE'])
@login_required
@permission_required('product', 'edit')
def delete_product_relation(product_id, relation_id):
    """删除产品关联配置"""
    try:
        from app.models.product_relation import ProductRelation

        relation = ProductRelation.query.filter_by(
            id=relation_id,
            main_product_type=ProductRelation.MAIN_TYPE_PRODUCT,
            main_product_id=product_id
        ).first()

        if not relation:
            return jsonify({'success': False, 'message': '关联记录不存在'}), 404

        db.session.delete(relation)
        db.session.commit()

        logger.info(f"用户 {current_user.id} 删除了产品 {product_id} 的关联 {relation_id}")
        return jsonify({'success': True, 'message': '删除成功'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"删除产品关联失败: {str(e)}")
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


@product_management_bp.route('/api/product/<int:product_id>/mutual-exclusion-group', methods=['DELETE'])
@login_required
@permission_required('product', 'edit')
def delete_mutual_exclusion_group(product_id):
    """删除互斥组（删除组内所有产品关联）"""
    try:
        from app.models.product_relation import ProductRelation

        data = request.get_json()
        group_id = data.get('group_id')

        if not group_id:
            return jsonify({'success': False, 'message': '缺少互斥组ID'}), 400

        # 查询该互斥组下的所有关联记录
        relations = ProductRelation.query.filter_by(
            main_product_type=ProductRelation.MAIN_TYPE_PRODUCT,
            main_product_id=product_id,
            mutual_exclusion_group=group_id
        ).all()

        if not relations:
            return jsonify({'success': False, 'message': '互斥组不存在或已被删除'}), 404

        # 删除所有关联记录
        deleted_count = 0
        for relation in relations:
            db.session.delete(relation)
            deleted_count += 1

        db.session.commit()

        logger.info(f"用户 {current_user.id} 删除了产品 {product_id} 的互斥组 {group_id}，共删除 {deleted_count} 条关联记录")
        return jsonify({
            'success': True,
            'message': f'成功删除互斥组，共删除 {deleted_count} 个产品关联',
            'deleted_count': deleted_count
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"删除互斥组失败: {str(e)}")
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


@product_management_bp.route('/api/product/<int:product_id>/relations/batch', methods=['POST'])
@login_required
@permission_required('product', 'edit')
def batch_add_product_relations(product_id):
    """批量添加产品关联配置"""
    try:
        from app.models.product import Product
        from app.models.product_relation import ProductRelation

        # 验证产品存在
        product = Product.query.get_or_404(product_id)

        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '缺少请求数据'}), 400

        product_ids = data.get('product_ids', [])
        relation_type = data.get('relation_type', 'required_accessory')
        default_quantity = data.get('default_quantity', 1)

        if not product_ids:
            return jsonify({'success': False, 'message': '请至少选择一个产品'}), 400

        # 验证关联类型
        valid_types = ['required_accessory', 'recommended', 'optional_accessory', 'alternative']
        if relation_type not in valid_types:
            return jsonify({'success': False, 'message': f'无效的关联类型: {relation_type}'}), 400

        # 是否为必选配件
        is_required = (relation_type == 'required_accessory')

        # 批量创建关联记录
        added_count = 0
        skipped_count = 0
        errors = []

        for related_product_id in product_ids:
            try:
                # 验证关联产品存在
                related_product = Product.query.get(related_product_id)
                if not related_product:
                    errors.append(f'产品ID {related_product_id} 不存在')
                    continue

                # 检查是否已存在相同关联
                existing = ProductRelation.query.filter_by(
                    main_product_type=ProductRelation.MAIN_TYPE_PRODUCT,
                    main_product_id=product_id,
                    related_product_id=related_product_id,
                    is_active=True
                ).first()

                if existing:
                    skipped_count += 1
                    continue

                # 创建关联记录
                relation = ProductRelation(
                    main_product_type=ProductRelation.MAIN_TYPE_PRODUCT,
                    main_product_id=product_id,
                    related_product_id=related_product_id,
                    relation_type=relation_type,
                    is_required=is_required,
                    default_quantity=default_quantity,
                    is_active=True,
                    display_order=0
                )
                db.session.add(relation)
                added_count += 1

            except Exception as e:
                errors.append(f'添加产品ID {related_product_id} 失败: {str(e)}')
                continue

        # 提交事务
        db.session.commit()

        # 构建响应消息
        message_parts = []
        if added_count > 0:
            message_parts.append(f'成功添加 {added_count} 个关联产品')
        if skipped_count > 0:
            message_parts.append(f'跳过 {skipped_count} 个已存在的关联')
        if errors:
            message_parts.append(f'失败 {len(errors)} 个')

        message = '；'.join(message_parts)

        logger.info(f"用户 {current_user.id} 批量添加了产品 {product_id} 的关联: {message}")

        return jsonify({
            'success': True,
            'message': message,
            'data': {
                'added': added_count,
                'skipped': skipped_count,
                'failed': len(errors),
                'errors': errors
            }
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"批量添加产品关联失败: {str(e)}")
        return jsonify({'success': False, 'message': f'批量添加失败: {str(e)}'}), 500


@product_management_bp.route('/api/product/<int:product_id>/relations/batch-mutual-group', methods=['POST'])
@login_required
@permission_required('product', 'edit')
def batch_add_mutual_exclusion_group(product_id):
    """
    批量添加互斥组配置

    请求示例:
    {
        "product_ids": [123, 124, 125],
        "group_name": "电源线规格",
        "is_required": true,
        "default_product_id": 123,
        "default_quantity": 1
    }
    """
    try:
        from app.models.product import Product
        from app.models.product_relation import ProductRelation
        from datetime import datetime

        # 验证产品存在
        product = Product.query.get_or_404(product_id)

        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '缺少请求数据'}), 400

        product_ids = data.get('product_ids', [])
        group_name = data.get('group_name', '').strip()
        is_required = data.get('is_required', False)
        default_product_id = data.get('default_product_id')
        default_quantity = data.get('default_quantity', 1)

        # 验证数据
        if not product_ids or len(product_ids) < 2:
            return jsonify({'success': False, 'message': '互斥组至少需要2个产品'}), 400

        if not group_name:
            return jsonify({'success': False, 'message': '请输入互斥组名称'}), 400

        # 生成唯一的互斥组ID
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        group_id = f"{group_name.lower().replace(' ', '_')}_{timestamp}"

        # 批量创建关联
        added_count = 0
        skipped_count = 0
        errors = []

        for pid in product_ids:
            try:
                # 验证关联产品存在
                related_product = Product.query.get(pid)
                if not related_product:
                    errors.append(f'产品ID {pid} 不存在')
                    continue

                # 检查是否已存在相同关联
                existing = ProductRelation.query.filter_by(
                    main_product_type=ProductRelation.MAIN_TYPE_PRODUCT,
                    main_product_id=product_id,
                    related_product_id=pid,
                    is_active=True
                ).first()

                if existing:
                    skipped_count += 1
                    continue

                # 创建关联记录
                relation = ProductRelation(
                    main_product_type=ProductRelation.MAIN_TYPE_PRODUCT,
                    main_product_id=product_id,
                    related_product_id=pid,
                    relation_type=ProductRelation.RECOMMENDED,  # 基础类型使用推荐
                    default_quantity=default_quantity,
                    is_required=False,  # 个体不设为必选，组级别控制
                    # 互斥组字段
                    mutual_exclusion_group=group_id,
                    group_display_name=group_name,
                    is_group_required=is_required,
                    group_selection_mode='single',  # 单选模式
                    is_default=(pid == default_product_id)
                )

                db.session.add(relation)
                added_count += 1

            except Exception as e:
                errors.append(f'添加产品ID {pid} 失败: {str(e)}')
                continue

        # 提交事务
        db.session.commit()

        # 构建响应消息
        message = f'成功创建互斥组"{group_name}"'
        if skipped_count > 0:
            message += f'，跳过 {skipped_count} 个已存在的关联'

        logger.info(f"用户 {current_user.id} 为产品 {product_id} 创建了互斥组: {group_name}")

        return jsonify({
            'success': True,
            'message': message,
            'data': {
                'group_id': group_id,
                'added': added_count,
                'skipped': skipped_count,
                'failed': len(errors),
                'errors': errors
            }
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"创建互斥组失败: {str(e)}")
        return jsonify({'success': False, 'message': f'创建失败: {str(e)}'}), 500


@product_management_bp.route('/api/product-tree', methods=['GET'])
@login_required
def get_product_tree():
    """
    获取产品树数据 - 用于树状选择器

    返回格式:
    [
        {
            'id': 1,
            'name': '分类名称',
            'code_letter': 'Z',
            'type': 'category',
            'icon': 'fa-folder',
            'children': [
                {
                    'id': 10,
                    'name': '子分类名称',
                    'code_letter': 'F',
                    'type': 'subcategory',
                    'icon': 'fa-folder-open',
                    'children': [
                        {
                            'id': 100,
                            'mn': 'ZFZ-2000-100W',
                            'name': '产品名称',
                            'description': '规格说明',
                            'type': 'product',
                            'icon': 'fa-box'
                        }
                    ]
                }
            ]
        }
    ]
    """
    try:
        from app.models.product import Product

        tree_data = []

        # 查询所有分类（按ID排序）
        categories = ProductCategory.query.order_by(ProductCategory.id).all()

        for category in categories:
            category_node = {
                'id': f'cat_{category.id}',
                'category_id': category.id,
                'name': category.name,
                'code_letter': category.code_letter,
                'type': 'category',
                'icon': 'fa-layer-group',
                'children': []
            }

            # 查询该分类下的所有子分类（按display_order排序）
            subcategories = ProductSubcategory.query.filter_by(
                category_id=category.id
            ).order_by(ProductSubcategory.display_order).all()

            for subcategory in subcategories:
                subcategory_node = {
                    'id': f'sub_{subcategory.id}',
                    'subcategory_id': subcategory.id,
                    'name': subcategory.name,
                    'code_letter': subcategory.code_letter,
                    'type': 'subcategory',
                    'icon': 'fa-boxes',
                    'children': []
                }

                # 查询该子分类下的所有产品（按product_mn排序）
                # 只返回生产中的产品，过滤掉停产和待上市的产品
                products = Product.query.filter_by(
                    subcategory_id=subcategory.id,
                    status='active'  # 只包含生产中的产品
                ).order_by(Product.product_mn).all()

                for product in products:
                    product_node = {
                        'id': f'prod_{product.id}',
                        'product_id': product.id,
                        'mn': product.product_mn,
                        'model': product.model or product.product_name or '',
                        'name': product.product_name or '',
                        'description': product.specification or '',
                        'type': 'product',
                        'icon': 'fa-microchip',
                        'status': product.status
                    }
                    subcategory_node['children'].append(product_node)

                # 只添加有产品的子分类
                if subcategory_node['children']:
                    category_node['children'].append(subcategory_node)

            # 只添加有子分类的分类
            if category_node['children']:
                tree_data.append(category_node)

        return jsonify({
            'success': True,
            'data': tree_data,
            'total_categories': len(tree_data)
        })

    except Exception as e:
        logger.error(f"获取产品树数据失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取产品树数据失败: {str(e)}'
        }), 500


# ==================== 标准产品保存逻辑（用于统一创建页面） ====================

