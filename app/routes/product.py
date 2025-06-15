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
try:
    from flask.json.provider import JSONProvider  
except ImportError:
    # 兼容低版本的Flask
    JSONProvider = None
    
from app.models.product import Product
from app.extensions import db
import logging
from decimal import Decimal, InvalidOperation
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import func, and_, or_
from app.decorators import permission_required  # 添加权限装饰器导入
import os
import uuid
from PIL import Image
from werkzeug.utils import secure_filename
from flask import current_app

logger = logging.getLogger(__name__)
# 创建蓝图
bp = Blueprint('product_route', __name__)

# 在路由代码的合适位置添加以下常量
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
ALLOWED_PDF_EXTENSIONS = {'pdf'}
UPLOAD_FOLDER = 'app/static/uploads/products'

# 检查允许的文件类型
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 检查PDF文件扩展名是否允许
def allowed_pdf_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_PDF_EXTENSIONS

# 添加英文文件名验证函数
def validate_english_filename(filename):
    """验证文件名是否为英文字符（字母、数字、点、下划线、连字符）"""
    import re
    return re.match(r'^[a-zA-Z0-9._-]+$', filename) is not None

# 检查文件大小是否在限制内（12MB）
def check_file_size(file):
    """检查文件大小是否在12MB以内"""
    file.seek(0, 2)  # 移动到文件末尾
    file_size = file.tell()  # 获取文件大小
    file.seek(0)  # 重置文件指针
    return file_size <= 12 * 1024 * 1024  # 12MB

# 保存上传的PDF文件
def save_product_pdf(file):
    """
    保存上传的PDF文件
    
    参数:
    - file: 上传的文件对象
    
    返回:
    - 成功时返回保存的文件路径，失败时返回None和错误信息
    """
    if file and allowed_pdf_file(file.filename):
        # 验证文件名是否为英文
        if not validate_english_filename(file.filename):
            return None, "文件名必须是英文字符（字母、数字、点、下划线、连字符）"
            
        # 检查文件大小
        if not check_file_size(file):
            return None, "PDF文件大小不能超过12MB"
        
        # 重置文件指针到开始位置（修复第一次上传失败的问题）
        file.seek(0)
        
        # 处理文件名，保留中文字符
        original_filename = file.filename
        # 获取文件扩展名
        if '.' in original_filename:
            name_part, extension = original_filename.rsplit('.', 1)
            extension = extension.lower()
        else:
            name_part = original_filename
            extension = 'pdf'
        
        # 生成唯一文件名，保留原始文件名（包括中文）
        import re
        # 移除文件名中的特殊字符，但保留中文、英文、数字、下划线、连字符
        safe_name = re.sub(r'[^\w\u4e00-\u9fff\-_.]', '_', name_part)
        unique_filename = f"{uuid.uuid4().hex}_{safe_name}.{extension}"
        
        # 创建上传目录
        upload_folder = os.path.join(current_app.static_folder, 'uploads', 'products', 'pdfs')
        os.makedirs(upload_folder, exist_ok=True)
        
        # 保存文件
        filepath = os.path.join(upload_folder, unique_filename)
        file.save(filepath)
        
        # 返回相对路径
        return os.path.join('uploads', 'products', 'pdfs', unique_filename), None
    
    return None, None

# 处理图片上传、调整大小并保存
def process_product_image(file):
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
            import re
            # 移除文件名中的特殊字符，但保留中文、英文、数字、下划线、连字符
            safe_name = re.sub(r'[^\w\u4e00-\u9fff\-_.]', '_', name_part)
            unique_filename = f"{uuid.uuid4().hex}_{safe_name}.{extension}"
            
            logger.debug(f"处理图片: {original_filename} -> {unique_filename}, 大小: {file_size} bytes")
            
            # 确保上传目录存在
            if not os.path.exists(UPLOAD_FOLDER):
                logger.debug(f"创建上传目录: {UPLOAD_FOLDER}")
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            # 保存临时文件
            temp_path = os.path.join(UPLOAD_FOLDER, f"temp_{unique_filename}")
            file.save(temp_path)
            logger.debug(f"临时文件已保存: {temp_path}")
            
            # 打开图片并转换为正方形
            with Image.open(temp_path) as img:
                # 获取原始尺寸
                width, height = img.size
                logger.debug(f"原始图片尺寸: {width}x{height}")
                
                # 确定正方形尺寸（使用较短的边）
                square_size = min(width, height)
                # 计算裁剪区域
                left = (width - square_size) // 2
                top = (height - square_size) // 2
                right = left + square_size
                bottom = top + square_size
                
                # 裁剪为正方形
                img = img.crop((left, top, right, bottom))
                logger.debug(f"图片已裁剪为正方形: {square_size}x{square_size}")
                
                # 调整为标准大小(例如 500x500)
                img = img.resize((500, 500), Image.Resampling.LANCZOS)
                logger.debug("图片已调整大小为 500x500")
                
                # 保存处理后的图片，使用更高的压缩率以减小文件大小
                final_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                img.save(final_path, optimize=True, quality=75)  # 降低质量从85到75
                logger.debug(f"处理后的图片已保存: {final_path}")
                
                # 删除临时文件
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    logger.debug(f"临时文件已删除: {temp_path}")
                
                return unique_filename
                
        except Exception as e:
            logger.error(f"处理图片时出错: {str(e)}", exc_info=True)
            # 删除临时文件
            temp_path = os.path.join(UPLOAD_FOLDER, f"temp_{unique_filename}")
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

@bp.route('/products', methods=['GET'])
@login_required
@permission_required('product', 'view')  # 产品库只检查product权限
def product_list():
    """产品列表页面"""
    # 获取用户的产品权限
    can_edit_product = current_user.has_permission('product', 'edit')
    can_delete_product = current_user.has_permission('product', 'delete')
    
    return render_template('product/index.html', 
                          can_edit_product=can_edit_product,
                          can_delete_product=can_delete_product)

@bp.route('/products/create', methods=['GET'])
@login_required
@permission_required('product', 'create')  # 添加产品创建权限装饰器
def create_product_page():
    """创建产品页面"""
    return render_template('product/create.html')

@bp.route('/products/<int:id>/edit', methods=['GET'])
@login_required
@permission_required('product', 'edit')  # 添加产品编辑权限装饰器
def edit_product_page(id):
    """编辑产品页面"""
    product = Product.query.get_or_404(id)
    return render_template('product/create.html', product=product)

# API路由
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
            query = query.filter(
                or_(
                    Product.product_name.ilike(search_term),
                    Product.product_mn.ilike(search_term),
                    Product.model.ilike(search_term),
                    Product.category.ilike(search_term),
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
                    'category': p.category,
                    'product_mn': p.product_mn,
                    'product_name': p.product_name,
                    'model': p.model,
                    'specification': p.specification,
                    'brand': p.brand,
                    'unit': p.unit,
                    'retail_price': decimal_to_float(p.retail_price) if p.retail_price else 0,
                    'status': p.status,
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
        # 使用 distinct 获取唯一的类别列表
        categories = db.session.query(Product.category).distinct().filter(
            Product.category.isnot(None)
        ).all()
        
        # 将结果转换为列表
        category_list = [category[0] for category in categories if category[0]]
        
        # 定义类别的自定义顺序
        category_order = {
            '基站': 1,
            '合路平台': 2, 
            '直放站': 3,
            '天线': 4,
            '功率分配器': 5,
            '功率/耦合器': 6,
            '对讲机': 7,
            '配件': 8,
            '应用': 9,
            '服务': 10
        }
        
        # 按自定义顺序排序
        def custom_sort(item):
            return category_order.get(item, 999)  # 未定义顺序的类别排在最后
            
        category_list.sort(key=custom_sort)
        
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
                    'product_name': p.product_name,
                    'model': p.model,
                    'specification': p.specification,
                    'brand': p.brand,
                    'unit': p.unit,
                    'retail_price': decimal_to_float(p.retail_price) if p.retail_price else 0,
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
        
        # 查询指定产品名称的产品型号
        products = Product.query.filter_by(product_name=product_name).all()
        
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
                    'retail_price': decimal_to_float(p.retail_price) if p.retail_price else 0
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
        category_stats = db.session.query(
            Product.category, 
            func.count(Product.id)
        ).filter(
            Product.category.isnot(None)
        )
        
        # 应用产品可见性筛选到类别统计
        if current_user.role not in ['admin', 'product_manager', 'solution_manager']:
            category_stats = category_stats.filter(Product.status == 'active')
        
        # 完成分组查询
        category_stats = category_stats.group_by(
            Product.category
        ).all()
        
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
            'retail_price': request.form.get('retail_price')
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
            status=product_data['status'],
            owner_id=current_user.id
        )
        
        # 处理产品图片上传
        has_image = False
        if 'product_image' in request.files:
            product_image = request.files['product_image']
            if product_image.filename:  # 确保有文件被上传
                logger.debug(f'处理产品图片上传: {product_image.filename}')
                image_filename = process_product_image(product_image)
                if image_filename:
                    new_product.image_path = image_filename
                    has_image = True
                    logger.debug(f'新图片已保存: {image_filename}')
                else:
                    logger.warning('图片处理失败，将创建没有图片的产品')
        else:
            logger.debug('没有上传产品图片')
        
        # 处理PDF文件上传
        has_pdf = False
        if 'product_pdf' in request.files:
            product_pdf = request.files['product_pdf']
            if product_pdf.filename:  # 确保有文件被上传
                logger.debug(f'处理产品PDF上传: {product_pdf.filename}')
                pdf_path, pdf_error = save_product_pdf(product_pdf)
                if pdf_error:
                    return jsonify({
                        'success': False,
                        'message': pdf_error
                    }), 400
                elif pdf_path:
                    new_product.pdf_path = pdf_path
                    has_pdf = True
                    logger.debug(f'新PDF文件已保存: {pdf_path}')
                else:
                    logger.warning('PDF文件处理失败，将创建没有PDF的产品')
        else:
            logger.debug('没有上传产品PDF文件')
        
        # 保存新产品
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

@bp.route('/api/products/<int:id>/update', methods=['POST'])
@login_required
@permission_required('product', 'edit')  # 添加产品编辑权限装饰器
def update_product(id):
    """更新产品信息"""
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
            'retail_price': request.form.get('retail_price')
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
        
        # 处理产品图片上传
        image_changed = False
        if 'product_image' in request.files:
            product_image = request.files['product_image']
            if product_image.filename:  # 确保有文件被上传
                logger.debug(f'处理产品图片上传: {product_image.filename}')
                # 如果有旧图片，删除它
                if product.image_path:
                    old_image_path = os.path.join(UPLOAD_FOLDER, product.image_path)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                
                # 处理并保存新图片
                image_filename = process_product_image(product_image)
                if image_filename:
                    product.image_path = image_filename
                    image_changed = True
                    data_changed = True
                    logger.debug(f'新图片已保存: {image_filename}')
        
        # 检查是否需要删除图片
        if request.form.get('remove_image') == 'true' and product.image_path:
            logger.debug('删除产品图片')
            # 删除图片文件
            image_path = os.path.join(UPLOAD_FOLDER, product.image_path)
            if os.path.exists(image_path):
                os.remove(image_path)
            # 清空图片路径
            product.image_path = None
            image_changed = True
            data_changed = True
        
        # 处理PDF文件上传
        pdf_changed = False
        if 'product_pdf' in request.files:
            product_pdf = request.files['product_pdf']
            if product_pdf.filename:  # 确保有文件被上传
                logger.debug(f'处理产品PDF上传: {product_pdf.filename}')
                # 如果有旧PDF文件，删除它
                if product.pdf_path:
                    old_pdf_path = os.path.join(current_app.static_folder, product.pdf_path)
                    if os.path.exists(old_pdf_path):
                        os.remove(old_pdf_path)
                
                # 处理并保存新PDF文件
                pdf_path, pdf_error = save_product_pdf(product_pdf)
                if pdf_error:
                    return jsonify({
                        'success': False,
                        'message': pdf_error
                    }), 400
                elif pdf_path:
                    product.pdf_path = pdf_path
                    pdf_changed = True
                    data_changed = True
                    logger.debug(f'新PDF文件已保存: {pdf_path}')
        
        # 检查是否需要删除PDF文件
        if request.form.get('remove_pdf') == 'true' and product.pdf_path:
            logger.debug('删除产品PDF文件')
            # 删除PDF文件
            pdf_path = os.path.join(current_app.static_folder, product.pdf_path)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            # 清空PDF路径
            product.pdf_path = None
            pdf_changed = True
            data_changed = True
        
        # 更新产品信息 - 仅当值发生变化时才更新
        if product.type != product_data['type']:
            product.type = product_data['type']
            data_changed = True
            
        if product.category != product_data['category']:
            product.category = product_data['category']
            data_changed = True
            
        if product.product_mn != product_data['product_mn']:
            product.product_mn = product_data['product_mn']
            data_changed = True
            
        if product.product_name != product_data['product_name']:
            product.product_name = product_data['product_name']
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
                    'product_name': product.product_name,
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
                    'product_name': product.product_name,
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
            'category': product.category,
            'product_mn': product.product_mn,
            'product_name': product.product_name,
            'model': product.model,
            'specification': product.specification,
            'brand': product.brand,
            'unit': product.unit,
            'retail_price': decimal_to_float(product.retail_price) if product.retail_price else 0,
            'status': product.status,
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
@permission_required('product', 'delete')  # 添加产品删除权限装饰器
def delete_product(id):
    """删除产品API - 只有admin和product_manager可以删除未被引用的产品"""
    try:
        # 检查用户角色权限
        if current_user.role not in ['admin', 'product_manager']:
            return jsonify({
                'success': False,
                'message': '只有管理员和产品经理可以删除产品'
            }), 403
        
        product = Product.query.get_or_404(id)
        
        # 检查产品是否被报价单引用
        from app.models.quotation import QuotationDetail
        referenced_count = QuotationDetail.query.filter(
            QuotationDetail.product_name == product.product_name,
            QuotationDetail.product_model == product.model
        ).count()
        
        if referenced_count > 0:
            return jsonify({
                'success': False,
                'message': f'该产品已被 {referenced_count} 个报价单引用，不能删除。如需停产，请使用"停产"功能。',
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
        # 获取产品详情
        product = Product.query.get_or_404(id)
        
        # 检查产品停产状态的权限：只有产品经理、解决方案经理和管理员可以查看停产产品
        if product.status == 'discontinued' and current_user.role not in ['admin', 'product_manager', 'solution_manager']:
            logger.warning(f"用户 {current_user.username} 尝试查看停产产品详情: {id}")
            flash('您没有权限查看已停产的产品', 'danger')
            return redirect(url_for('product_route.product_list'))
        
        return render_template('product/detail.html', product=product)
    except Exception as e:
        logger.error(f'查看产品详情页面时出错: {str(e)}')
        flash(f'查看产品详情失败: {str(e)}', 'danger')
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
    from flask import send_file, abort
    
    product = Product.query.get_or_404(id)
    
    # 检查是否有PDF文件
    if not product.pdf_path:
        flash('该产品没有PDF文件', 'warning')
        return redirect(url_for('product_route.view_product_detail', id=id))
    
    # 构建文件完整路径
    pdf_file_path = os.path.join(current_app.static_folder, product.pdf_path)
    
    # 检查文件是否存在
    if not os.path.exists(pdf_file_path):
        flash('PDF文件不存在', 'danger')
        return redirect(url_for('product_route.view_product_detail', id=id))
    
    try:
        # 获取原始文件名（去掉UUID前缀）
        original_filename = os.path.basename(product.pdf_path)
        if '_' in original_filename:
            # 去掉UUID前缀，保留原始文件名
            original_filename = '_'.join(original_filename.split('_')[1:])
        
        # 如果没有原始文件名，使用产品型号作为文件名
        if not original_filename or original_filename == '':
            original_filename = f"{product.model}.pdf"
        
        return send_file(
            pdf_file_path,
            as_attachment=True,
            download_name=original_filename,
            mimetype='application/pdf'
        )
    except Exception as e:
        logger.error(f"下载PDF文件失败: {str(e)}")
        flash('下载PDF文件失败', 'danger')
        return redirect(url_for('product_route.view_product_detail', id=id)) 