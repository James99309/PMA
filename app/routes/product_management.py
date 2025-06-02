from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app, send_file
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

# 创建日志记录器
logger = logging.getLogger(__name__)

# 创建蓝图
product_management_bp = Blueprint('product_management', __name__, url_prefix='/product-management')

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

# 检查文件大小是否在限制内（2MB）
def check_file_size(file):
    """检查文件大小是否在2MB以内"""
    file.seek(0, 2)  # 移动到文件末尾
    file_size = file.tell()  # 获取文件大小
    file.seek(0)  # 重置文件指针
    return file_size <= 2 * 1024 * 1024  # 2MB

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
        # 创建安全的文件名
        filename = secure_filename(file.filename)
        # 使用UUID生成唯一文件名前缀
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
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
            return None, "PDF文件大小不能超过2MB"
        
        # 创建安全的文件名
        filename = secure_filename(file.filename)
        # 使用UUID生成唯一文件名前缀
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
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
    # 如果是管理员，可以查看所有研发产品
    if current_user.role == 'admin':
        dev_products = DevProduct.query.options(
            joinedload(DevProduct.category),
            joinedload(DevProduct.subcategory)
        ).all()
    else:
        # 普通产品经理只能查看自己创建的产品
        dev_products = DevProduct.query.options(
            joinedload(DevProduct.category),
            joinedload(DevProduct.subcategory)
        ).filter_by(created_by=current_user.id).all()
    
    return render_template('product_management/index.html', dev_products=dev_products)

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
        # 从ProductRegion模型中获取销售区域
        from app.models.product_code import ProductRegion
        regions = ProductRegion.query.all()
        
        regions_data = []
        for region in regions:
            regions_data.append({
                'id': region.id,
                'name': region.name,
                'code': region.code_letter
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
            # 获取表单提交的规格代码
            spec_option_codes = request.form.getlist('spec_option_codes[]')
            current_app.logger.debug(f"获取到的规格编码: {spec_option_codes}")
            
            # 确保有5个规格代码位置
            spec_codes = []
            for code in spec_option_codes:
                if code and code != '0':
                    spec_codes.append(code)
            
            # 不足的用'0'填充
            while len(spec_codes) < 5:
                spec_codes.append('0')
            
            # 只使用前5个代码
            spec_codes = spec_codes[:5]
            
            # 完整MN编码格式，移除末尾2位序号递增的逻辑
            mn_code = f"{category.code_letter}{subcategory.code_letter}{region_code}{''.join(spec_codes)}"
            current_app.logger.debug(f"生成的完整MN编码: {mn_code}")
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
            # 1. 收集现有规格数据 (spec_name[] + spec_value[])
            spec_names = request.form.getlist('spec_name[]')
            spec_values = request.form.getlist('spec_value[]')
            
            # 2. 收集新增规格数据 (new_spec_names[] + new_option_values[])
            new_spec_names = request.form.getlist('new_spec_names[]')
            new_option_values = request.form.getlist('new_option_values[]')
            
            # 3. 合并所有规格数据
            all_specs = []
            
            # 记录日志
            current_app.logger.debug(f"规格名称: {spec_names}")
            current_app.logger.debug(f"规格值: {spec_values}")
            current_app.logger.debug(f"新增规格: {new_spec_names}")
            current_app.logger.debug(f"新增选项: {new_option_values}")
            
            # 合并规格数据
            for i in range(len(spec_names)):
                if i < len(spec_values) and spec_names[i].strip() and spec_values[i].strip():
                    all_specs.append({
                        'field_name': spec_names[i].strip(),
                        'field_value': spec_values[i].strip(),
                        'is_new': False
                    })
            
            # 合并新规格数据        
            for i in range(len(new_spec_names)):
                if i < len(new_option_values) and new_spec_names[i].strip() and new_option_values[i].strip():
                    all_specs.append({
                        'field_name': new_spec_names[i].strip(),
                        'field_value': new_option_values[i].strip(),
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
                
                current_app.logger.debug(f"保存规格: {spec_name} = {spec_value}")
                
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
                            use_in_code=True
                        )
                        db.session.add(new_field)
                        db.session.flush()
                        
                        # 添加规格选项
                        if spec_value:
                            option_id = add_spec_option_if_not_exists(new_field.id, spec_value, model)
                            current_app.logger.info(f"为字段 '{spec_name}' 添加新规格选项: '{spec_value}' (编码: {option_id})")
                            
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
                        option_id = add_spec_option_if_not_exists(field.id, spec_value, model)
                        
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
            flash('新产品已成功添加到研发产品库，自定义规格字段也已同步到产品分类模块', 'success')
            return redirect(url_for('product_management.index'))
            
        except Exception as spec_error:
            # 规格保存出错，但产品已成功保存
            current_app.logger.error(f"规格保存错误: {spec_error}")
            db.session.rollback()  # 回滚规格保存操作
            flash(f'产品已保存，但规格保存失败: {str(spec_error)}', 'warning')
            return redirect(url_for('product_management.index'))
            
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
    
    # 检查权限：只有创建者或管理员可以编辑
    if product.created_by != current_user.id and current_user.role != 'admin':
        flash('您没有权限编辑此产品', 'danger')
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
    
    # 检查权限：只有创建者或管理员可以更新
    if dev_product.created_by != current_user.id and current_user.role != 'admin':
        flash('您没有权限更新此产品', 'danger')
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
            for spec in specs:
                if spec.field_code and spec.field_code != '0':
                    spec_codes.append(spec.field_code)
            
            # 确保正好有5个规格代码
            while len(spec_codes) < 5:
                spec_codes.append('0')
            
            # 只使用前5个代码
            spec_codes = spec_codes[:5]
            
            # 生成新的MN编码，不再使用后缀
            new_mn_code = f"{category.code_letter}{subcategory.code_letter}{region_code}{''.join(spec_codes)}"
            current_app.logger.debug(f"更新MN编码: {dev_product.mn_code} -> {new_mn_code}")
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
        # 先删除现有规格
        DevProductSpec.query.filter_by(dev_product_id=id).delete()
        
        # 获取产品所属的子分类ID
        subcategory_id = dev_product.subcategory_id
        
        # 已有规格字段名列表，用于检查是否需要创建新规格
        existing_spec_fields = ProductCodeField.query.filter_by(
            subcategory_id=subcategory_id,
            field_type='spec'
        ).all()
        existing_spec_names = {field.name.lower(): field for field in existing_spec_fields}
        
        # 添加新规格
        specs_data = request.form.getlist('spec_name[]')
        specs_values = request.form.getlist('spec_value[]')
        
        for i in range(len(specs_data)):
            if specs_data[i].strip():  # 如果字段名不为空
                # 先添加到产品规格表
                spec = DevProductSpec(
                    dev_product_id=dev_product.id,
                    field_name=specs_data[i],
                    field_value=specs_values[i] if i < len(specs_values) else ''
                )
                db.session.add(spec)
                
                spec_value = specs_values[i] if i < len(specs_values) else ''
                
                # 检查规格字段是否存在，如果不存在则创建新字段
                spec_name_lower = specs_data[i].lower()
                if spec_name_lower not in existing_spec_names:
                    # 计算新字段的position
                    max_position = db.session.query(db.func.max(ProductCodeField.position))\
                        .filter_by(subcategory_id=subcategory_id).scalar() or 0
                    new_position = max_position + 1
                    
                    # 创建新的规格字段
                    new_field = ProductCodeField(
                        subcategory_id=subcategory_id,
                        name=specs_data[i],
                        field_type='spec',
                        description=f'从产品 {dev_product.model} 更新时自动添加的规格字段',
                        position=new_position,
                        max_length=1,  # 默认长度
                        is_required=False,  # 默认非必填
                        use_in_code=True  # 默认用于编码
                    )
                    db.session.add(new_field)
                    db.session.flush()  # 获取新字段ID
                    
                    # 添加规格字段到本地缓存
                    existing_spec_names[spec_name_lower] = new_field
                    
                    # 将规格值作为默认选项添加
                    if spec_value:
                        option_id = add_spec_option_if_not_exists(new_field.id, spec_value, dev_product.model)
                        if option_id:
                            option = ProductCodeFieldOption.query.get(option_id)
                            if option:
                                spec.field_code = option.code
                                current_app.logger.debug(f"已设置规格 '{specs_data[i]}' 的编码为: {option.code}")
                else:
                    # 如果规格字段已存在，检查对应的规格值是否已存在，若不存在则添加
                    existing_field = existing_spec_names[spec_name_lower]
                    if spec_value:
                        option_id = add_spec_option_if_not_exists(existing_field.id, spec_value, dev_product.model)
                        if option_id:
                            option = ProductCodeFieldOption.query.get(option_id)
                            if option:
                                spec.field_code = option.code
                                current_app.logger.debug(f"已设置规格 '{specs_data[i]}' 的编码为: {option.code}")
        
        # 提交更改
        db.session.commit()
        
        # 记录变更历史
        try:
            new_values = ChangeTracker.get_new_values(dev_product, old_values.keys())
            ChangeTracker.log_update(dev_product, old_values, new_values)
        except Exception as track_err:
            current_app.logger.warning(f"记录产品变更历史失败: {str(track_err)}")
        
        flash('产品更新成功！', 'success')
        return redirect(url_for('product_management.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'更新产品失败: {str(e)}', 'danger')
        return redirect(url_for('product_management.edit_product', id=id))

# 删除产品
@product_management_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
@permission_required('product_code', 'delete')
def delete_product(id):
    dev_product = DevProduct.query.get_or_404(id)
    
    # 检查权限：只有创建者或管理员可以删除
    if dev_product.created_by != current_user.id and current_user.role != 'admin':
        flash('您没有权限删除此产品', 'danger')
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
        
        flash('产品已成功删除', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'删除产品失败: {str(e)}', 'danger')
    
    return redirect(url_for('product_management.index'))

# 批量删除产品
@product_management_bp.route('/batch-delete', methods=['POST'])
@login_required
@permission_required('product_code', 'delete')
def batch_delete_products():
    # 获取产品ID列表
    product_ids_str = request.form.get('product_ids', '')
    
    if not product_ids_str:
        flash('未选择要删除的产品', 'warning')
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
        # 检查权限：只有创建者或管理员可以删除
        if product.created_by != current_user.id and current_user.role != 'admin':
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
        flash(f'成功删除 {successful_count} 个产品', 'success')
    
    if unauthorized_count > 0:
        flash(f'您没有权限删除其中的 {unauthorized_count} 个产品', 'warning')
    
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
    
    # 如果非管理员且不是创建者，则不能查看
    if current_user.role != 'admin' and dev_product.created_by != current_user.id:
        flash('您没有权限查看此产品', 'danger')
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
    """根据子分类ID获取产品型号列表"""
    try:
        # 获取子分类信息
        subcategory = ProductSubcategory.query.get_or_404(subcategory_id)
        
        # 从主产品库中查找匹配产品名称的产品型号
        from app.models.product import Product
        products = Product.query.filter_by(product_name=subcategory.name).all()
        
        # 处理结果
        result = []
        for product in products:
            result.append({
                'id': product.id,
                'model': product.model,
                'product_mn': product.product_mn
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': f'获取产品型号失败: {str(e)}'}), 500

# 根据子分类ID获取规格字段列表
@product_management_bp.route('/api/subcategory/<int:subcategory_id>/spec-fields', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def get_spec_fields_by_subcategory(subcategory_id):
    """根据子分类ID获取规格字段列表"""
    try:
        # 查找该子分类下的所有规格类型字段
        spec_fields = ProductCodeField.query.filter_by(
            subcategory_id=subcategory_id,
            field_type='spec'
        ).order_by(ProductCodeField.position).all()
        
        # 处理结果
        result = []
        for field in spec_fields:
            field_data = {
                'id': field.id,
                'name': field.name,
                'description': field.description,
                'is_required': field.is_required,
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
        
        return jsonify({'spec_fields': result})
    except Exception as e:
        return jsonify({'error': f'获取规格字段失败: {str(e)}'}), 500

# 查看已入库产品列表
@product_management_bp.route('/inventory', methods=['GET'])
@login_required
def inventory():
    from app.models.product import Product
    
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    products = Product.query.filter_by(type='研发产品').order_by(Product.updated_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    
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
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'添加指标失败: {str(e)}'}), 500

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
        flash('该产品没有PDF文件', 'warning')
        return redirect(url_for('product_management.product_detail', id=id))
    
    # 构建文件完整路径
    pdf_file_path = os.path.join(current_app.static_folder, dev_product.pdf_path)
    
    # 检查文件是否存在
    if not os.path.exists(pdf_file_path):
        flash('PDF文件不存在', 'danger')
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
        flash('下载PDF文件失败', 'danger')
        return redirect(url_for('product_management.product_detail', id=id)) 