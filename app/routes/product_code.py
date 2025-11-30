from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app import db
from app.extensions import csrf
from app.models.product_code import ProductCategory, ProductSubcategory, ProductCodeField, ProductCodeFieldOption, ProductCode, ProductCodeFieldValue, SpecificationDictionary, SpecificationOption
from app.models.product import Product
from app.permissions import admin_required, product_manager_required, permission_required
import json
import random
import string
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text, update, Integer, case
from datetime import datetime
from app.routes.spec_dictionary import generate_smart_code

# 创建蓝图
product_code_bp = Blueprint('product_code', __name__, url_prefix='/product-code')

# ============================================================================
# 辅助函数
# ============================================================================

def check_field_used_in_subcategory(field_name, subcategory_id, field_id=None):
    """
    检查规格字段是否在指定子分类的产品中被使用

    判断条件（必须全部满足）：
    1. 字段名匹配
    2. 位置匹配（产品快照中的位置 = 当前规格定义的位置）
    3. 编码匹配（产品使用的编码是当前规格选项中定义的编码）

    Args:
        field_name (str): 规格字段名称
        subcategory_id (int): 子分类ID
        field_id (int, optional): 字段ID，用于获取位置和选项编码

    Returns:
        bool: 如果被使用返回True，否则返回False
    """
    # 获取字段的当前位置和有效编码列表
    if field_id:
        field = ProductCodeField.query.get(field_id)
    else:
        field = ProductCodeField.query.filter_by(
            name=field_name,
            subcategory_id=subcategory_id,
            field_type='spec'
        ).first()

    if not field:
        return False

    current_position = field.position

    # 获取该字段所有有效的选项编码
    valid_codes = set()
    for option in field.options:
        if option.code and option.is_active:
            valid_codes.add(option.code)

    # 如果没有定义任何编码选项，则不算被使用
    if not valid_codes:
        return False

    # 检查产品库的编码快照
    products = db.session.execute(
        text("""
            SELECT code_definition_snapshot
            FROM products
            WHERE subcategory_id = :subcategory_id
            AND code_definition_snapshot IS NOT NULL
        """),
        {"subcategory_id": subcategory_id}
    ).fetchall()

    for (snapshot,) in products:
        if not snapshot or 'code_parts' not in snapshot:
            continue

        for part in snapshot.get('code_parts', []):
            # 条件1：字段名匹配
            if part.get('field_name') != field_name:
                continue
            # 条件2：位置匹配
            if part.get('position') != current_position:
                continue
            # 条件3：编码匹配（产品使用的编码是当前有效编码之一）
            part_code = part.get('code', '')
            if part_code and part_code in valid_codes:
                return True

    # 研发产品没有编码快照，暂不检查
    # 研发产品的规格变更不影响排序功能

    return False

def get_field_unit(field_name):
    """
    通过规格名称获取单位

    Args:
        field_name (str): 规格字段名称

    Returns:
        str: 单位字符串，如果找不到则返回None
    """
    spec = SpecificationDictionary.query.filter_by(name=field_name).first()
    return spec.unit if spec else None

# ============================================================================
# 路由函数
# ============================================================================

# 管理员和产品经理视图 - 产品分类管理
@product_code_bp.route('/categories', methods=['GET'])
@login_required
@product_manager_required
def categories():
    categories = ProductCategory.get_ordered_list()

    # 检查每个分类是否被使用（研发库+产品库）
    # 编码格式：地区(1位) + 分类字母(1位) + 子分类字母(1位) + 规格...
    for category in categories:
        # 检查研发产品是否使用了此分类（通过 category_id 关联）
        used_in_dev_by_category = db.session.execute(
            text("SELECT 1 FROM dev_products WHERE category_id = :category_id LIMIT 1"),
            {"category_id": category.id}
        ).first() is not None

        # 检查研发产品编码：前3位都匹配（地区+分类+子分类）
        used_in_dev_by_code = db.session.execute(
            text("""
                SELECT 1 FROM dev_products dp
                WHERE LENGTH(dp.mn_code) >= 3
                -- 第1位：有效地区编码
                AND EXISTS (
                    SELECT 1 FROM product_code_field_options o
                    JOIN product_code_fields f ON o.field_id = f.id
                    WHERE f.field_type = 'origin_location'
                    AND o.code = SUBSTRING(dp.mn_code, 1, 1)
                )
                -- 第2位：分类字母
                AND SUBSTRING(dp.mn_code, 2, 1) = :category_code
                -- 第3位：有效子分类字母
                AND EXISTS (
                    SELECT 1 FROM product_subcategories ps
                    WHERE ps.category_id = :category_id
                    AND ps.code_letter = SUBSTRING(dp.mn_code, 3, 1)
                )
                LIMIT 1
            """),
            {"category_code": category.code_letter, "category_id": category.id}
        ).first() is not None

        # 检查产品库编码：前3位都匹配（地区+分类+子分类）
        used_in_product_by_code = db.session.execute(
            text("""
                SELECT 1 FROM products p
                WHERE LENGTH(p.product_mn) >= 3
                -- 第1位：有效地区编码
                AND EXISTS (
                    SELECT 1 FROM product_code_field_options o
                    JOIN product_code_fields f ON o.field_id = f.id
                    WHERE f.field_type = 'origin_location'
                    AND o.code = SUBSTRING(p.product_mn, 1, 1)
                )
                -- 第2位：分类字母
                AND SUBSTRING(p.product_mn, 2, 1) = :category_code
                -- 第3位：有效子分类字母
                AND EXISTS (
                    SELECT 1 FROM product_subcategories ps
                    WHERE ps.category_id = :category_id
                    AND ps.code_letter = SUBSTRING(p.product_mn, 3, 1)
                )
                AND p.category_id IS NOT NULL
                LIMIT 1
            """),
            {"category_code": category.code_letter, "category_id": category.id}
        ).first() is not None

        # 标记分类是否被使用（研发库或产品库任一条件满足即认为被使用）
        category.is_used = (used_in_dev_by_category or used_in_dev_by_code or used_in_product_by_code)
    
    # 获取已使用的标识符列表
    used_identifiers = [category.code_letter for category in categories]
    
    # 可用字母池（A-Z大写字母）
    available_letters = [letter for letter in string.ascii_uppercase if letter not in used_identifiers]
    
    return render_template('product_code/categories.html', 
                           categories=categories,
                           used_letters=used_identifiers,
                           available_letters=available_letters)

def generate_unique_letter():
    """生成一个唯一的分类标识符（优先A-Z字母，然后1-9数字，排除0）"""
    import random
    
    # 获取已使用的标识符列表
    used_identifiers = [category.code_letter for category in ProductCategory.query.all()]
    
    # 可用字母池（A-Z大写字母）
    available_letters = [letter for letter in string.ascii_uppercase if letter not in used_identifiers]
    
    # 如果还有可用字母，随机选择一个
    if available_letters:
        return random.choice(available_letters)
    
    # 如果字母用完，检查数字1-9（排除0）
    available_digits = [str(digit) for digit in range(1, 10) if str(digit) not in used_identifiers]
    
    # 如果有可用数字，随机选择一个
    if available_digits:
        return random.choice(available_digits)
        
    # 所有可能的标识符都用完了
    return None

def generate_unique_subcategory_letter(category_id):
    """为特定分类下的子类生成唯一标识符"""
    import random
    
    # 获取该分类下已使用的子类标识符
    used_identifiers = [subcat.code_letter for subcat in ProductSubcategory.query.filter_by(category_id=category_id).all()]
    
    # 可用字母池（A-Z大写字母）
    available_letters = [letter for letter in string.ascii_uppercase if letter not in used_identifiers]
    
    # 如果还有可用字母，随机选择一个
    if available_letters:
        return random.choice(available_letters)
    
    # 如果字母用完，检查数字1-9（排除0）
    available_digits = [str(digit) for digit in range(1, 10) if str(digit) not in used_identifiers]
    
    # 如果有可用数字，随机选择一个
    if available_digits:
        return random.choice(available_digits)
        
    # 所有可能的标识符都用完了
    return None

@product_code_bp.route('/api/generate-category-code', methods=['GET'])
@login_required
@product_manager_required
def generate_category_code():
    """API端点：为新分类生成唯一标识符"""
    try:
        code = generate_unique_letter()
        if code:
            return jsonify({'success': True, 'code': code})
        else:
            return jsonify({'success': False, 'message': '所有可用标识符都已被使用'})
    except Exception as e:
        current_app.logger.error(f"生成分类标识符时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'生成失败: {str(e)}'}), 500

@product_code_bp.route('/api/generate-subcategory-code/<int:category_id>', methods=['GET'])
@login_required
@product_manager_required
def generate_subcategory_code(category_id):
    """API端点：为指定分类下的新子类生成唯一标识符"""
    try:
        code = generate_unique_subcategory_letter(category_id)
        if code:
            return jsonify({'success': True, 'code': code})
        else:
            return jsonify({'success': False, 'message': '该分类下所有可用标识符都已被使用'})
    except Exception as e:
        current_app.logger.error(f"生成子类标识符时发生错误: {str(e)}")
        return jsonify({'success': False, 'message': f'生成失败: {str(e)}'}), 500

# 旧版路由 - 已被API路由替代（使用模态框）
# @product_code_bp.route('/categories/new', methods=['GET', 'POST'])
# @login_required
# @product_manager_required
# def new_category():
#     # 获取已使用的标识符列表
#     used_identifiers = [category.code_letter for category in ProductCategory.query.all()]
#
#     if request.method == 'POST':
#         name = request.form.get('name')
#         code_letter = request.form.get('code_letter', '').strip().upper()  # 获取用户输入的标识符并转为大写
#         description = request.form.get('description', '')
#
#         if not name:
#             flash('分类名称是必填项', 'danger')
#             return render_template('product_code/new_category.html',
#                                   used_letters=used_identifiers,
#                                   name=name,
#                                   code_letter=code_letter,
#                                   description=description)
#
#         if not code_letter:
#             flash('分类标识符是必填项', 'danger')
#             return render_template('product_code/new_category.html',
#                                   used_letters=used_identifiers,
#                                   name=name,
#                                   description=description)
#
#         # 验证标识符是否为单个字符
#         if len(code_letter) != 1:
#             flash('分类标识符必须是单个字符', 'danger')
#             return render_template('product_code/new_category.html',
#                                   used_letters=used_identifiers,
#                                   name=name,
#                                   description=description)
#
#         # 验证标识符是否合法（A-Z字母或0-9数字）
#         if not (code_letter.isalpha() or code_letter.isdigit()):
#             flash('分类标识符必须是A-Z字母或0-9数字', 'danger')
#             return render_template('product_code/new_category.html',
#                                   used_letters=used_identifiers,
#                                   name=name,
#                                   description=description)
#
#         # 检查标识符是否已被使用
#         if code_letter in used_identifiers:
#             flash(f'标识符 {code_letter} 已被使用，请选择其他标识符', 'danger')
#             return render_template('product_code/new_category.html',
#                                   used_letters=used_identifiers,
#                                   name=name,
#                                   description=description)
#
#         category = ProductCategory(name=name, code_letter=code_letter, description=description)
#         db.session.add(category)
#
#         try:
#             db.session.commit()
#             flash(f'产品分类创建成功，标识符为：{code_letter}', 'success')
#             return redirect(url_for('product_code.categories'))
#         except IntegrityError:
#             db.session.rollback()
#             flash('创建分类失败，可能存在命名冲突', 'danger')
#
#     # 获取可用字母池（A-Z大写字母）
#     available_letters = [letter for letter in string.ascii_uppercase if letter not in used_identifiers]
#
#     return render_template('product_code/new_category.html',
#                           used_letters=used_identifiers,
#                           available_letters=available_letters)

# 旧版路由 - 已被API路由替代（使用模态框）
# @product_code_bp.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
# @login_required
# @product_manager_required
# def edit_category(id):
#     category = ProductCategory.query.get_or_404(id)
#     # 获取所有已使用的标识符（除了当前分类的标识符）
#     used_identifiers = [cat.code_letter for cat in ProductCategory.query.filter(ProductCategory.id != id).all()]
#
#     if request.method == 'POST':
#         # 打印表单数据以进行调试
#         print("表单数据:", request.form)
#
#         # 获取表单数据
#         name = request.form.get('name')
#         code_letter = request.form.get('code_letter', '').strip().upper()  # 获取用户输入的标识符并转为大写
#         description = request.form.get('description', '')
#
#         # 打印取到的值进行调试
#         print(f"处理后的值: name={name}, code_letter={code_letter}, description={description}")
#
#         if not name:
#             flash('分类名称是必填项', 'danger')
#             return render_template('product_code/edit_category.html',
#                                   category=category,
#                                   used_letters=used_identifiers)
#
#         if not code_letter:
#             flash('分类标识符是必填项', 'danger')
#             return render_template('product_code/edit_category.html',
#                                   category=category,
#                                   used_letters=used_identifiers)
#
#         # 验证标识符是否为单个字符
#         if len(code_letter) != 1:
#             flash('分类标识符必须是单个字符', 'danger')
#             return render_template('product_code/edit_category.html',
#                                   category=category,
#                                   used_letters=used_identifiers)
#
#         # 验证标识符是否合法（A-Z字母或0-9数字）
#         if not (code_letter.isalpha() or code_letter.isdigit()):
#             flash('分类标识符必须是A-Z字母或0-9数字', 'danger')
#             return render_template('product_code/edit_category.html',
#                                   category=category,
#                                   used_letters=used_identifiers)
#
#         # 如果标识符已更改，检查是否已被使用
#         if code_letter != category.code_letter and code_letter in used_identifiers:
#             flash(f'标识符 {code_letter} 已被使用，请选择其他标识符', 'danger')
#             return render_template('product_code/edit_category.html',
#                                   category=category,
#                                   used_letters=used_identifiers)
#
#         # 更新分类数据
#         category.name = name
#         category.description = description
#         category.code_letter = code_letter
#
#         # 打印更新后的值进行调试
#         print(f"更新后的分类: name={category.name}, code_letter={category.code_letter}, description={category.description}")
#
#         try:
#             db.session.commit()
#             # 提交后再次检查
#             db.session.refresh(category)
#             print(f"提交后的分类: id={category.id}, name={category.name}, code_letter={category.code_letter}")
#             flash('产品分类更新成功', 'success')
#             return redirect(url_for('product_code.categories'))
#         except IntegrityError as e:
#             db.session.rollback()
#             print(f"数据库错误: {str(e)}")
#             flash(f'更新分类失败: {str(e)}', 'danger')
#
#     return render_template('product_code/edit_category.html',
#                           category=category,
#                           used_letters=used_identifiers)

# 旧版路由 - 已被API路由替代（使用模态框）
# @product_code_bp.route('/categories/<int:id>/delete', methods=['POST'])
# @login_required
# @product_manager_required
# def delete_category(id):
#     from flask import request
#     from flask_wtf.csrf import validate_csrf
#     from werkzeug.exceptions import BadRequest
#
#     # 验证CSRF令牌
#     try:
#         validate_csrf(request.form.get('csrf_token'))
#     except BadRequest:
#         flash('安全验证失败，请重新操作', 'danger')
#         return redirect(url_for('product_code.categories'))
#
#     category = ProductCategory.query.get_or_404(id)
#
#     # 检查是否有产品编码使用此分类（通过ProductCode表而不是直接查询Product表）
#     product_codes_count = ProductCode.query.filter_by(category_id=id).count()
#     if product_codes_count > 0:
#         flash(f'无法删除：有 {product_codes_count} 个产品编码使用此分类', 'danger')
#         return redirect(url_for('product_code.categories'))
#
#     # 检查是否有子类
#     subcategories_count = ProductSubcategory.query.filter_by(category_id=id).count()
#     if subcategories_count > 0:
#         flash(f'无法删除：此分类下有 {subcategories_count} 个子类', 'danger')
#         return redirect(url_for('product_code.categories'))
#
#     # 删除分类
#     db.session.delete(category)
#     db.session.commit()
#
#     flash('产品分类已删除', 'success')
#     return redirect(url_for('product_code.categories'))

# 管理员视图 - 子类管理
@product_code_bp.route('/categories/<int:id>/subcategories', methods=['GET'])
@login_required
@product_manager_required
def category_subcategories(id):
    category = ProductCategory.query.get_or_404(id)

    # 使用原始SQL查询避免ORM自动刷新问题
    # 检查研发库和产品库是否使用了该子分类
    # 编码格式：地区(1位) + 分类字母(1位) + 子分类字母(1位) + 规格...
    subcategories_data = db.session.execute(
        text("""
            SELECT
                s.id,
                s.name,
                s.code_letter,
                s.created_at,
                s.display_order,
                -- 检查是否被使用（研发库+产品库，前3位都要匹配）
                CASE
                    WHEN EXISTS (SELECT 1 FROM dev_products WHERE subcategory_id = s.id LIMIT 1)
                         -- 研发库：前3位都匹配（地区+分类+子分类）
                         OR EXISTS (
                             SELECT 1 FROM dev_products dp
                             WHERE LENGTH(dp.mn_code) >= 3
                             -- 第1位：有效地区编码
                             AND EXISTS (
                                 SELECT 1 FROM product_code_field_options o
                                 JOIN product_code_fields f ON o.field_id = f.id
                                 WHERE f.field_type = 'origin_location'
                                 AND o.code = SUBSTRING(dp.mn_code, 1, 1)
                             )
                             -- 第2位：分类字母
                             AND SUBSTRING(dp.mn_code, 2, 1) = :category_code
                             -- 第3位：子分类字母
                             AND SUBSTRING(dp.mn_code, 3, 1) = s.code_letter
                             LIMIT 1
                         )
                         -- 产品库：前3位都匹配（地区+分类+子分类）
                         OR EXISTS (
                             SELECT 1 FROM products p
                             WHERE LENGTH(p.product_mn) >= 3
                             -- 第1位：有效地区编码
                             AND EXISTS (
                                 SELECT 1 FROM product_code_field_options o
                                 JOIN product_code_fields f ON o.field_id = f.id
                                 WHERE f.field_type = 'origin_location'
                                 AND o.code = SUBSTRING(p.product_mn, 1, 1)
                             )
                             -- 第2位：分类字母
                             AND SUBSTRING(p.product_mn, 2, 1) = :category_code
                             -- 第3位：子分类字母
                             AND SUBSTRING(p.product_mn, 3, 1) = s.code_letter
                             AND p.category_id IS NOT NULL
                             LIMIT 1
                         )
                    THEN true
                    ELSE false
                END as is_used
            FROM product_subcategories s
            WHERE s.category_id = :category_id
            ORDER BY s.display_order
        """),
        {"category_id": id, "category_code": category.code_letter}
    ).fetchall()

    # 使用 expunge_all 清除会话中的所有对象，避免自动刷新
    db.session.expunge_all()

    # 构造子分类对象列表
    subcategories = []
    for row in subcategories_data:
        # 重新加载子分类对象（此时会话是干净的）
        subcategory = db.session.get(ProductSubcategory, row[0])
        subcategory.is_used = row[5]
        subcategories.append(subcategory)

    return render_template('product_code/subcategories.html',
                           category=category,
                           subcategories=subcategories)

# 管理员视图 - 分类级通用编码字段管理
@product_code_bp.route('/categories/<int:id>/fields', methods=['GET'])
@login_required
@product_manager_required
def category_fields(id):
    """分类级通用编码字段配置页面"""
    category = ProductCategory.query.get_or_404(id)

    # 获取分类级编码字段
    fields = ProductCodeField.get_category_fields(id)

    # 检查每个规格是否被使用
    for field in fields:
        # 检查是否被任何子分类的产品使用
        used_count = db.session.execute(
            text("""
                SELECT COUNT(*) FROM dev_product_specs dps
                INNER JOIN dev_products dp ON dps.dev_product_id = dp.id
                INNER JOIN product_subcategories ps ON dp.subcategory_id = ps.id
                WHERE dps.field_name = :field_name
                AND ps.category_id = :category_id
            """),
            {"field_name": field.name, "category_id": id}
        ).scalar() or 0

        field.is_used = used_count > 0
        field.used_count = used_count
        field.unit = get_field_unit(field.name)

    # 获取该分类下的子分类数量
    subcategory_count = ProductSubcategory.query.filter_by(category_id=id).count()

    # 检查是否有任何字段被使用（用于控制排序功能）
    any_field_used = any(getattr(field, 'is_used', False) for field in fields)

    return render_template('product_code/category_fields.html',
                           category=category,
                           fields=fields,
                           subcategory_count=subcategory_count,
                           any_field_used=any_field_used)

# ============================================================================
# 已废弃的子分类（产品名称）路由 - 已替换为模态框API
# 保留代码供参考，请勿使用
# 新API位置: POST /api/subcategories (create_subcategory_api)
# ============================================================================

# @product_code_bp.route('/categories/<int:id>/subcategories/new', methods=['GET', 'POST'])
# @login_required
# @product_manager_required
# def new_subcategory(id):
#     category = ProductCategory.query.get_or_404(id)
#
#     # 获取当前分类下已使用的标识符
#     used_subcategories = ProductSubcategory.query.filter_by(category_id=id).all()
#     used_identifiers = [subcat.code_letter for subcat in used_subcategories]
#
#     # 初始化空表单数据
#     form_data = {'name': '', 'description': '', 'code_letter': ''}
#
#     if request.method == 'POST':
#         name = request.form.get('name')
#         code_letter = request.form.get('code_letter', '').strip().upper()  # 获取用户输入的标识符并转为大写
#         description = request.form.get('description', '')
#
#         form_data = {'name': name, 'description': description, 'code_letter': code_letter}
#
#         if not name:
#             flash('产品名称是必填项', 'danger')
#             return render_template('product_code/new_subcategory.html',
#                                    category=category,
#                                    form=form_data,
#                                    used_subcategories=used_subcategories)
#
#         if not code_letter:
#             flash('标识符是必填项', 'danger')
#             return render_template('product_code/new_subcategory.html',
#                                    category=category,
#                                    form=form_data,
#                                    used_subcategories=used_subcategories)
#
#         # 验证标识符是否为单个字符
#         if len(code_letter) != 1:
#             flash('标识符必须是单个字符', 'danger')
#             return render_template('product_code/new_subcategory.html',
#                                    category=category,
#                                    form=form_data,
#                                    used_subcategories=used_subcategories)
#
#         # 验证标识符是否合法（A-Z字母或0-9数字）
#         if not (code_letter.isalpha() or code_letter.isdigit()):
#             flash('标识符必须是A-Z字母或0-9数字', 'danger')
#             return render_template('product_code/new_subcategory.html',
#                                    category=category,
#                                    form=form_data,
#                                    used_subcategories=used_subcategories)
#
#         # 检查标识符是否已被使用
#         if code_letter in used_identifiers:
#             flash(f'标识符 {code_letter} 已在此分类下使用，请选择其他标识符', 'danger')
#             return render_template('product_code/new_subcategory.html',
#                                    category=category,
#                                    form=form_data,
#                                    used_subcategories=used_subcategories)
#
#         # 计算新子类别的display_order - 获取当前分类下最大的display_order加1
#         max_display_order = db.session.query(db.func.max(ProductSubcategory.display_order))\
#             .filter_by(category_id=id).scalar() or 0
#         new_display_order = max_display_order + 1
#
#         subcategory = ProductSubcategory(
#             category_id=id,
#             name=name,
#             code_letter=code_letter,
#             description=description,
#             display_order=new_display_order
#         )
#         db.session.add(subcategory)
#
#         try:
#             db.session.commit()
#             flash(f'产品名称添加成功，标识符为：{code_letter}', 'success')
#             return redirect(url_for('product_code.category_subcategories', id=id))
#         except IntegrityError as e:
#             db.session.rollback()
#             flash(f'添加产品名称失败: {str(e)}', 'danger')
#
#     return render_template('product_code/new_subcategory.html',
#                            category=category,
#                            form=form_data,
#                            used_subcategories=used_subcategories)

# 新API位置: PUT /api/subcategories/<id> (update_subcategory_api)
# @product_code_bp.route('/subcategories/<int:id>/edit', methods=['GET', 'POST'])
# @login_required
# @product_manager_required
# def edit_subcategory(id):
#     subcategory = ProductSubcategory.query.get_or_404(id)
#
#     # 获取当前分类下已使用的标识符（除了当前子分类的标识符）
#     used_identifiers = [subcat.code_letter for subcat in
#                          ProductSubcategory.query.filter(
#                              ProductSubcategory.category_id == subcategory.category_id,
#                              ProductSubcategory.id != id
#                          ).all()]
#
#     if request.method == 'POST':
#         # 打印表单数据以进行调试
#         print("子分类表单数据:", request.form)
#
#         # 获取表单数据
#         name = request.form.get('name')
#         code_letter = request.form.get('code_letter', '').strip().upper()  # 获取用户输入的标识符并转为大写
#         description = request.form.get('description', '')
#
#         # 打印取到的值进行调试
#         print(f"子分类处理后的值: name={name}, code_letter={code_letter}, description={description}")
#
#         if not name:
#             flash('产品名称是必填项', 'danger')
#             return render_template('product_code/edit_subcategory.html',
#                                   subcategory=subcategory,
#                                   used_identifiers=used_identifiers)
#
#         if not code_letter:
#             flash('标识符是必填项', 'danger')
#             return render_template('product_code/edit_subcategory.html',
#                                   subcategory=subcategory,
#                                   used_identifiers=used_identifiers)
#
#         # 验证标识符是否为单个字符
#         if len(code_letter) != 1:
#             flash('标识符必须是单个字符', 'danger')
#             return render_template('product_code/edit_subcategory.html',
#                                   subcategory=subcategory,
#                                   used_identifiers=used_identifiers)
#
#         # 验证标识符是否合法（A-Z字母或0-9数字）
#         if not (code_letter.isalpha() or code_letter.isdigit()):
#             flash('标识符必须是A-Z字母或0-9数字', 'danger')
#             return render_template('product_code/edit_subcategory.html',
#                                   subcategory=subcategory,
#                                   used_identifiers=used_identifiers)
#
#         # 如果标识符已更改，检查是否已被使用
#         if code_letter != subcategory.code_letter and code_letter in used_identifiers:
#             flash(f'标识符 {code_letter} 已在此分类下使用，请选择其他标识符', 'danger')
#             return render_template('product_code/edit_subcategory.html',
#                                   subcategory=subcategory,
#                                   used_identifiers=used_identifiers)
#
#         # 更新子分类数据
#         subcategory.name = name
#         subcategory.description = description
#         subcategory.code_letter = code_letter
#
#         # 打印更新后的值进行调试
#         print(f"更新后的子分类: name={subcategory.name}, code_letter={subcategory.code_letter}")
#
#         try:
#             db.session.commit()
#             # 提交后再次检查
#             db.session.refresh(subcategory)
#             print(f"提交后的子分类: id={subcategory.id}, name={subcategory.name}, code_letter={subcategory.code_letter}")
#             flash('产品名称更新成功', 'success')
#             return redirect(url_for('product_code.category_subcategories', id=subcategory.category_id))
#         except IntegrityError as e:
#             db.session.rollback()
#             print(f"子分类数据库错误: {str(e)}")
#             flash(f'更新产品名称失败: {str(e)}', 'danger')
#
#     return render_template('product_code/edit_subcategory.html',
#                           subcategory=subcategory,
#                           used_identifiers=used_identifiers)

# 新API位置: DELETE /api/subcategories/<id> (delete_subcategory_api)
# @product_code_bp.route('/subcategories/<int:id>/delete', methods=['POST'])
# @login_required
# @product_manager_required
# def delete_subcategory(id):
#     from flask import request
#     from flask_wtf.csrf import validate_csrf
#     from werkzeug.exceptions import BadRequest
#
#     # 验证CSRF令牌
#     try:
#         validate_csrf(request.form.get('csrf_token'))
#     except BadRequest:
#         flash('安全验证失败，请重新操作', 'danger')
#         return redirect(url_for('product_code.category_subcategories', id=ProductSubcategory.query.get_or_404(id).category_id))
#
#     subcategory = ProductSubcategory.query.get_or_404(id)
#     category_id = subcategory.category_id
#
#     # 检查是否有产品编码使用此产品名称
#     product_codes_count = ProductCode.query.filter_by(subcategory_id=id).count()
#     if product_codes_count > 0:
#         flash(f'无法删除：有 {product_codes_count} 个产品编码使用此产品名称', 'danger')
#         return redirect(url_for('product_code.category_subcategories', id=category_id))
#
#     # 检查是否有字段关联此产品名称
#     fields_count = ProductCodeField.query.filter_by(subcategory_id=id).count()
#     if fields_count > 0:
#         flash(f'无法删除：有 {fields_count} 个字段关联此产品名称', 'danger')
#         return redirect(url_for('product_code.category_subcategories', id=category_id))
#
#     # 删除产品名称
#     db.session.delete(subcategory)
#     db.session.commit()
#
#     flash('产品名称已删除', 'success')
#     return redirect(url_for('product_code.category_subcategories', id=category_id))

# 管理员视图 - 编码字段管理
@product_code_bp.route('/subcategories/<int:id>/fields', methods=['GET'])
@login_required
@product_manager_required
def subcategory_fields(id):
    subcategory = ProductSubcategory.query.get_or_404(id)
    
    # 使用正确的字段名查询，只获取类型为 'spec' 的字段
    # 先显示编码规格（按位置排序），再显示非编码规格（按位置排序）
    # 注意：options 关系使用 lazy='dynamic'，不支持 eager loading，模板中需使用 field.options.all()
    fields = ProductCodeField.query.filter_by(subcategory_id=id, field_type='spec')\
        .order_by(ProductCodeField.use_in_code.desc(), ProductCodeField.position).all()
    
    # 如果没有找到字段，可能是旧版数据库结构，尝试使用category_id
    if not fields:
        # 使用原始SQL查询，兼容旧版数据库结构，并添加 field_type 条件
        sql = text("SELECT * FROM product_code_fields WHERE subcategory_id = :subcategory_id AND field_type = 'spec' ORDER BY position")
        result = db.session.execute(sql, {"subcategory_id": id})
        fields = [dict(row) for row in result]
    
    # 检查每个规格是否被产品编码使用
    for field in fields:
        field_id = field.id if hasattr(field, 'id') else field['id']
        field_name = field.name if hasattr(field, 'name') else field['name']
        
        # 检查正式产品是否使用了此规格（product_code_field_values表）
        used_in_formal = ProductCodeFieldValue.query.filter_by(field_id=field_id).first() is not None

        # 🔥 修改：检查研发产品是否在当前子分类中使用了此规格
        used_in_dev = check_field_used_in_subcategory(field_name, id)

        # 只要任何一种产品使用了此规格，就标记为已使用
        field.is_used = used_in_formal or used_in_dev

        # 为每个字段附加单位信息（从规格字典中获取）
        field.unit = get_field_unit(field_name)

        # 为每个字段的选项计算 is_used 状态
        for option in field.options:
            # 检查是否被旧版产品编码使用
            used_in_product_code = ProductCodeFieldValue.query.filter_by(option_id=option.id).first() is not None

            # 检查是否被研发产品使用
            used_in_dev_option = db.session.execute(
                text("""
                    SELECT 1 FROM dev_product_specs dps
                    INNER JOIN dev_products dp ON dps.dev_product_id = dp.id
                    WHERE dps.field_name = :field_name
                    AND dps.field_value = :value
                    AND dp.subcategory_id = :subcategory_id
                    LIMIT 1
                """),
                {
                    "field_name": field_name,
                    "value": option.value,
                    "subcategory_id": id
                }
            ).first() is not None

            # 检查是否被正式产品使用
            used_in_formal_option = db.session.execute(
                text("""
                    SELECT 1 FROM product_specs ps
                    INNER JOIN products p ON ps.product_id = p.id
                    WHERE ps.field_name = :field_name
                    AND ps.field_value = :value
                    AND p.subcategory_id = :subcategory_id
                    LIMIT 1
                """),
                {
                    "field_name": field_name,
                    "value": option.value,
                    "subcategory_id": id
                }
            ).first() is not None

            # 标记是否被使用
            option.is_used = used_in_product_code or used_in_dev_option or used_in_formal_option

    # 获取分类级继承字段
    inherited_fields = ProductCodeField.get_category_fields(subcategory.category_id)

    # 为继承字段添加 is_used 和 unit 信息
    for field in inherited_fields:
        field_name = field.name
        # 检查是否被使用
        used_in_formal = ProductCodeFieldValue.query.filter_by(field_id=field.id).first() is not None
        used_in_dev = check_field_used_in_subcategory(field_name, id)
        field.is_used = used_in_formal or used_in_dev
        # 附加单位信息
        field.unit = get_field_unit(field_name)

        # 为每个字段的选项计算 is_used 状态
        for option in field.options:
            used_in_product_code = ProductCodeFieldValue.query.filter_by(option_id=option.id).first() is not None
            used_in_dev_option = db.session.execute(
                text("""
                    SELECT 1 FROM dev_product_specs dps
                    INNER JOIN dev_products dp ON dps.dev_product_id = dp.id
                    WHERE dps.field_name = :field_name
                    AND dps.field_value = :value
                    AND dp.subcategory_id = :subcategory_id
                    LIMIT 1
                """),
                {"field_name": field_name, "value": option.value, "subcategory_id": id}
            ).first() is not None

            used_in_formal_option = db.session.execute(
                text("""
                    SELECT 1 FROM product_specs ps
                    INNER JOIN products p ON ps.product_id = p.id
                    WHERE ps.field_name = :field_name
                    AND ps.field_value = :value
                    AND p.subcategory_id = :subcategory_id
                    LIMIT 1
                """),
                {"field_name": field_name, "value": option.value, "subcategory_id": id}
            ).first() is not None

            option.is_used = used_in_product_code or used_in_dev_option or used_in_formal_option

    # 检查是否有任何非继承字段被使用（用于控制排序功能）
    any_own_field_used = any(getattr(field, 'is_used', False) for field in fields)

    return render_template('product_code/fields.html',
                           subcategory=subcategory,
                           fields=fields,
                           inherited_fields=inherited_fields,
                           any_own_field_used=any_own_field_used)

# ============================================================================
# 已废弃的路由 - 已迁移到模态框API模式
# 旧的 new_field 和 edit_field 路由已删除
# 现在使用 /api/fields 系列API端点（见文件末尾）
# ============================================================================

@product_code_bp.route('/fields/<int:id>/delete', methods=['POST'])
@login_required
@product_manager_required
def delete_field(id):
    from flask import request
    from flask_wtf.csrf import validate_csrf
    from werkzeug.exceptions import BadRequest
    
    # 验证CSRF令牌
    try:
        validate_csrf(request.form.get('csrf_token'))
    except BadRequest:
        flash('安全验证失败，请重新操作', 'danger')
        return redirect(url_for('product_code.subcategory_fields', id=ProductCodeField.query.get_or_404(id).subcategory_id))
    
    try:
        field = ProductCodeField.query.get_or_404(id)
        subcategory_id = field.subcategory_id
        
        # 检查是否有产品编码使用此规格
        if ProductCodeFieldValue.query.filter_by(field_id=id).first():
            flash('无法删除此规格，因为已有产品编码使用', 'danger')
            return redirect(url_for('product_code.subcategory_fields', id=subcategory_id))
        
        # 删除规格的所有指标
        ProductCodeFieldOption.query.filter_by(field_id=id).delete()
        
        # 删除规格
        db.session.delete(field)
        db.session.commit()
        
        flash('规格删除成功', 'success')
        return redirect(url_for('product_code.subcategory_fields', id=subcategory_id))
    except Exception as e:
        flash(f'删除规格时发生错误: {str(e)}', 'danger')
        return redirect(url_for('product_code.categories'))

# ============================================================================
# 已废弃的路由 - 指标管理已迁移到模态框API模式
# 旧的 field_options, new_option, edit_option 路由已注释
# 使用新的 API 端点: /product-code/api/fields/<field_id>/options 等
# ============================================================================

# @product_code_bp.route('/fields/<int:id>/options', methods=['GET'])
# @login_required
# @product_manager_required
# def field_options(id):
#     """字段指标管理 - 已废弃，使用模态框"""
#     pass

# @product_code_bp.route('/options/<int:id>/delete', methods=['POST'])
# @login_required
# @product_manager_required
# def delete_option(id):
#     """删除指标 - 已废弃，使用 DELETE /api/options/<id>"""
#     pass

# @product_code_bp.route('/options/<int:id>/toggle', methods=['POST'])
# @login_required
# @product_manager_required
# def toggle_option(id):
#     """切换指标启用/禁用状态 - 已废弃"""
#     pass

# @product_code_bp.route('/fields/<int:id>/options/new', methods=['GET', 'POST'])
# @login_required
# @product_manager_required
# def new_option(id):
#     """创建新指标 - 已废弃，使用 POST /api/fields/<id>/options"""
#     pass

# @product_code_bp.route('/options/<int:id>/edit', methods=['GET', 'POST'])
# @login_required
# @product_manager_required
# def edit_option(id):
#     """编辑指标 - 已废弃，使用 PUT /api/options/<id>"""
#     pass

# 产品经理视图 - 创建产品编码
@product_code_bp.route('/generator', methods=['GET'])
@login_required
@permission_required('product_code', 'create')
def generator():
    categories = ProductCategory.get_ordered_list()
    return render_template('product_code/generator.html', categories=categories)

@product_code_bp.route('/api/category/<int:id>/subcategories', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def api_category_subcategories(id):
    # 按display_order字段升序排序
    subcategories = ProductSubcategory.query.filter_by(category_id=id).order_by(ProductSubcategory.display_order).all()
    result = [
        {'id': s.id, 'name': s.name, 'code_letter': s.code_letter, 'display_order': s.display_order}
        for s in subcategories
    ]
    return jsonify(result)

@product_code_bp.route('/api/subcategory/<int:id>/fields', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def api_subcategory_fields(id):
    # 获取子分类特定的字段
    subcategory_fields = ProductCodeField.query.filter_by(subcategory_id=id).order_by(ProductCodeField.position).all()
    
    # 获取产地区字段（通用字段）
    origin_fields = ProductCodeField.query.filter_by(field_type='origin_location').order_by(ProductCodeField.position).all()
    
    # 合并字段
    all_fields = origin_fields + subcategory_fields
    result = []
    
    for field in all_fields:
        options = ProductCodeFieldOption.query.filter_by(field_id=field.id).all()
        field_data = {
            'id': field.id,
            'name': field.name,
            'type': field.field_type,
            'position': field.position,
            'max_length': field.max_length,
            'required': field.is_required,
            'options': [{'id': opt.id, 'value': opt.value, 'code': opt.code} for opt in options]
        }
        result.append(field_data)
    
    return jsonify(result)

@product_code_bp.route('/generate-preview', methods=['POST'])
@login_required
@permission_required('product_code', 'create')
def generate_preview():
    data = request.json
    category_id = data.get('category_id')
    subcategory_id = data.get('subcategory_id')
    field_values = data.get('field_values', {})

    category = ProductCategory.query.get_or_404(category_id)
    subcategory = ProductSubcategory.query.get_or_404(subcategory_id)

    # 获取产地区字段（通用字段）
    origin_fields = ProductCodeField.query.filter_by(field_type='origin_location').order_by(ProductCodeField.position).all()

    # 先获取地区编码
    region_code = ''
    for field in origin_fields:
        field_id_str = str(field.id)
        if field_id_str in field_values:
            field_value = field_values[field_id_str]
            if field_value and isinstance(field_value, dict):
                option_id = field_value.get('option_id')
                if option_id:
                    option = ProductCodeFieldOption.query.get(option_id)
                    if option:
                        region_code = option.effective_code[:field.max_length] if option.effective_code else ''
                        break

    # 构建编码：地区 + 分类 + 子分类 + 规格编码
    code_parts = [region_code, category.code_letter, subcategory.code_letter]

    # 获取该子类的特定字段
    subcategory_fields = ProductCodeField.query.filter_by(subcategory_id=subcategory_id).order_by(ProductCodeField.position).all()

    # 按字段位置排序处理规格字段值（跳过地区字段，已在前面处理）
    for field in sorted(subcategory_fields, key=lambda f: f.position):
        field_id_str = str(field.id)
        if field_id_str in field_values and field.use_in_code:  # 只有标记为用于编码的字段才参与
            field_value = field_values[field_id_str]
            if field_value:
                if isinstance(field_value, dict):  # 选项类型
                    option_id = field_value.get('option_id')
                    if option_id:
                        option = ProductCodeFieldOption.query.get(option_id)
                        if option:
                            # 确保编码长度符合字段限制
                            code_to_append = option.effective_code[:field.max_length] if option.effective_code else ''
                            if code_to_append:
                                code_parts.append(code_to_append)
                else:  # 自定义值类型
                    # 确保自定义值长度符合字段限制
                    custom_code = str(field_value)[:field.max_length]
                    if custom_code:
                        code_parts.append(custom_code)

    full_code = ''.join(code_parts)
    
    return jsonify({
        'preview_code': full_code,
        'is_unique': ProductCode.query.filter_by(full_code=full_code).first() is None
    })

@product_code_bp.route('/save', methods=['POST'])
@login_required
@permission_required('product_code', 'create')
def save_code():
    data = request.json
    category_id = data.get('category_id')
    subcategory_id = data.get('subcategory_id')
    product_id = data.get('product_id')
    field_values = data.get('field_values', {})
    full_code = data.get('full_code')
    
    # 验证产品ID是否有效
    product = Product.query.get_or_404(product_id)
    
    # 验证编码唯一性
    existing_code = ProductCode.query.filter_by(full_code=full_code).first()
    if existing_code:
        return jsonify({'success': False, 'message': '产品编码已存在'}), 400
    
    # 创建产品编码记录
    product_code = ProductCode(
        product_id=product_id,
        category_id=category_id,
        subcategory_id=subcategory_id,
        full_code=full_code,
        status='draft',
        created_by=current_user.id
    )
    db.session.add(product_code)
    db.session.commit()
    
    # 保存字段值
    for field_id, value in field_values.items():
        field_value = ProductCodeFieldValue(
            product_code_id=product_code.id,
            field_id=int(field_id)
        )
        
        if isinstance(value, dict):  # 选项类型
            field_value.option_id = value.get('option_id')
        else:  # 自定义值类型
            field_value.custom_value = str(value)
        
        db.session.add(field_value)
    
    # 更新产品的MN号
    product.product_mn = full_code
    product.status = 'upcoming'  # 设置为"待上市"状态

    # 注意：编码快照现在由研发库入库流程统一生成，此处不再生成
    # 手动创建产品的方式已废弃，请使用研发库转移流程

    db.session.commit()

    return jsonify({'success': True, 'message': '产品编码创建成功', 'product_code_id': product_code.id})

# API - 获取现有产品列表
@product_code_bp.route('/api/products', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def api_products():
    search = request.args.get('search', '')
    # 先join ProductSubcategory以支持新字段搜索
    products = Product.query\
        .outerjoin(ProductSubcategory, Product.subcategory_id == ProductSubcategory.id)\
        .filter(
            (ProductSubcategory.name.ilike(f'%{search}%')) |  # 新字段
            (Product.product_name.ilike(f'%{search}%')) |     # 旧字段
            (Product.model.ilike(f'%{search}%'))
        ).limit(10).all()

    result = [
        {'id': p.id, 'name': p.name, 'model': p.model, 'current_mn': p.product_mn}  # 使用智能属性
        for p in products
    ]
    
    return jsonify(result)

@product_code_bp.route('/api/generate-letter', methods=['GET'])
@login_required
@product_manager_required
def api_generate_letter():
    """API端点：生成随机唯一分类标识符"""
    letter = generate_unique_letter()
    return jsonify({'letter': letter})

@product_code_bp.route('/api/generate-subcategory-letter', methods=['GET'])
@login_required
@product_manager_required
def api_generate_subcategory_letter():
    """API端点：生成随机唯一子类标识符"""
    category_id = request.args.get('category_id', type=int)
    if not category_id:
        return jsonify({'error': '缺少分类ID参数'}), 400
        
    letter = generate_unique_subcategory_letter(category_id)
    return jsonify({'letter': letter})

# 产地区管理 - 独立于分类系统
@product_code_bp.route('/origin-fields', methods=['GET'])
@login_required
@product_manager_required
def origin_fields():
    """所有销售区域的管理"""
    try:
        # 查询所有类型为'origin_location'的字段
        fields = ProductCodeField.query.filter_by(field_type='origin_location').order_by(ProductCodeField.position).all()
        
        # 获取每个字段的编码（首选从字段的code属性，其次从字段的选项中获取）
        for field in fields:
            if not hasattr(field, 'code') or not field.code:
                # 如果code字段不存在或为空，尝试从选项中获取
                option = ProductCodeFieldOption.query.filter_by(field_id=field.id).first()
                if option:
                    field.code = option.code
                else:
                    field.code = "?"  # 未找到编码时的默认值
            
            # 检查该区域编码是否被研发产品使用
            field_code = getattr(field, 'code', None)
            if field_code and field_code != "?":
                # 检查研发产品是否使用了此区域编码（通过mn_code的第3位字符）
                used_in_dev = db.session.execute(
                    text("SELECT 1 FROM dev_products WHERE SUBSTRING(mn_code, 3, 1) = :region_code LIMIT 1"),
                    {"region_code": field_code}
                ).first() is not None
                
                field.is_used = used_in_dev
            else:
                field.is_used = False
        
        return render_template('product_code/origin_fields.html', fields=fields)
    except Exception as e:
        flash(f'获取销售区域时发生错误: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@product_code_bp.route('/origin-fields/new', methods=['GET', 'POST'])
@login_required
@product_manager_required
def new_origin_field():
    """添加新销售区域"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        code = request.form.get('code', '').strip().upper()  # 获取用户输入的编码并转为大写
        description = request.form.get('description', '')

        # 验证必填字段
        if not name:
            flash('区域名称是必填项', 'danger')
            return render_template('product_code/new_origin_field.html')

        if not code:
            flash('区域编码是必填项', 'danger')
            return render_template('product_code/new_origin_field.html')

        # 验证编码格式（单个字母或数字）
        if len(code) != 1 or not code.isalnum():
            flash('区域编码必须是单个字母或数字', 'danger')
            return render_template('product_code/new_origin_field.html')

        # 检查编码是否已被其他销售区域使用
        existing_field = ProductCodeField.query.filter_by(
            field_type='origin_location',
            code=code
        ).first()
        if existing_field:
            flash(f'编码 "{code}" 已被销售区域 "{existing_field.name}" 使用，请选择其他编码', 'danger')
            return render_template('product_code/new_origin_field.html')

        # 确保有一个默认的子分类用于销售区域
        default_subcategory = ProductSubcategory.query.first()
        if not default_subcategory:
            flash('需要先创建至少一个产品分类和子分类', 'danger')
            return redirect(url_for('product_code.categories'))

        try:
            # 创建销售区域字段（直接使用用户输入的编码）
            field = ProductCodeField(
                subcategory_id=default_subcategory.id,
                name=name,
                code=code,  # 直接使用用户输入的编码
                description=description,
                field_type='origin_location',
                position=1,  # 固定位置为1
                max_length=1,  # 固定长度为1
                is_required=True  # 固定为必填
            )
            db.session.add(field)
            db.session.flush()

            # 创建字段选项（不引用规格字典，直接存储值和编码）
            option = ProductCodeFieldOption(
                field_id=field.id,
                value=name,
                code=code,
                description=description
            )
            db.session.add(option)
            db.session.commit()

            flash('销售区域创建成功', 'success')
            return redirect(url_for('product_code.origin_fields'))
        except Exception as e:
            db.session.rollback()
            flash(f'创建销售区域失败: {str(e)}', 'danger')

    return render_template('product_code/new_origin_field.html')

@product_code_bp.route('/origin-fields/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@product_manager_required
def edit_origin_field(id):
    """编辑销售区域"""
    try:
        field = ProductCodeField.query.get_or_404(id)
        
        # 确保code字段存在
        if not hasattr(field, 'code') or not field.code:
            # 如果code字段不存在或为空，尝试从选项中获取
            option = ProductCodeFieldOption.query.filter_by(field_id=field.id).first()
            if option:
                field.code = option.code
            else:
                field.code = "?"  # 未找到编码时的默认值
        
        # 确保只能编辑销售区域
        if field.field_type != 'origin_location':
            flash('只能编辑销售区域', 'danger')
            return redirect(url_for('product_code.origin_fields'))
        
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            
            field.name = name
            field.description = description
            # 固定值
            field.position = 1
            field.max_length = 1
            field.is_required = True
            
            try:
                # 更新关联选项的值
                option = ProductCodeFieldOption.query.filter_by(field_id=field.id).first()
                if option:
                    option.value = name
                    option.description = f"自动生成的销售区域编码: {name}"
                
                db.session.commit()
                flash('销售区域更新成功', 'success')
                return redirect(url_for('product_code.origin_fields'))
            except Exception as e:
                db.session.rollback()
                flash(f'更新销售区域失败: {str(e)}', 'danger')
            
        return render_template('product_code/edit_origin_field.html', field=field)
    except Exception as e:
        flash(f'编辑销售区域时发生错误: {str(e)}', 'danger')
        return redirect(url_for('product_code.origin_fields'))

@product_code_bp.route('/origin-fields/<int:id>/delete', methods=['POST'])
@login_required
@product_manager_required
def delete_origin_field(id):
    """删除销售区域"""
    from flask import request
    from flask_wtf.csrf import validate_csrf
    from werkzeug.exceptions import BadRequest
    
    # 验证CSRF令牌
    try:
        validate_csrf(request.form.get('csrf_token'))
    except BadRequest:
        flash('安全验证失败，请重新操作', 'danger')
        return redirect(url_for('product_code.origin_fields'))
    
    field = ProductCodeField.query.get_or_404(id)
    
    # 确保只能删除销售区域
    if field.field_type != 'origin_location':
        flash('只能删除销售区域', 'danger')
        return redirect(url_for('product_code.origin_fields'))
    
    # 检查是否有产品编码使用此字段
    if ProductCodeFieldValue.query.filter_by(field_id=id).first():
        flash('无法删除此销售区域，因为已有产品编码使用', 'danger')
        return redirect(url_for('product_code.origin_fields'))
    
    # 删除字段的所有选项
    ProductCodeFieldOption.query.filter_by(field_id=id).delete()
    
    # 删除字段
    db.session.delete(field)
    db.session.commit()
    
    flash('销售区域删除成功', 'success')
    return redirect(url_for('product_code.origin_fields'))

@product_code_bp.route('/categories/update-order', methods=['POST'])
@login_required
@product_manager_required
def update_categories_order():
    """更新产品分类顺序并重排ID"""
    try:
        # 获取前端传来的排序
        data = request.json
        category_ids = data.get('order', [])
        
        if not category_ids:
            return jsonify({'success': False, 'message': '未提供排序数据'}), 400
        
        # 将字符串ID转换为整数ID
        category_ids = [int(id) for id in category_ids]
        
        # 创建ID映射字典
        old_to_new = {old_id: i+1 for i, old_id in enumerate(category_ids)}
        
        # 1. 获取所有分类
        categories = {cat.id: cat for cat in ProductCategory.query.all()}
        
        # 2. 获取所有需要更新的关联记录
        subcategories = ProductSubcategory.query.filter(
            ProductSubcategory.category_id.in_(category_ids)
        ).all()
        
        product_codes = ProductCode.query.filter(
            ProductCode.category_id.in_(category_ids)
        ).all()
        
        # 创建事务
        try:
            # 3. 先保存所有分类的当前数据
            category_data = []
            for old_id in category_ids:
                if old_id in categories:
                    cat = categories[old_id]
                    # 保存分类数据
                    category_data.append({
                        'old_id': old_id,
                        'new_id': old_to_new[old_id],
                        'name': cat.name,
                        'code_letter': cat.code_letter,
                        'description': cat.description,
                        'created_at': cat.created_at
                    })
            
            # 4. 先禁用外键约束检查
            if db.engine.url.drivername == 'sqlite':
                db.session.execute(text('PRAGMA foreign_keys = OFF'))
            
            # 5. 更新关联表中的外键引用
            for subcategory in subcategories:
                if subcategory.category_id in old_to_new:
                    db.session.execute(
                        text("UPDATE product_subcategories SET category_id = :new_id WHERE id = :subcat_id"),
                        {"new_id": old_to_new[subcategory.category_id], "subcat_id": subcategory.id}
                    )
            
            for product_code in product_codes:
                if product_code.category_id in old_to_new:
                    db.session.execute(
                        text("UPDATE product_codes SET category_id = :new_id WHERE id = :code_id"),
                        {"new_id": old_to_new[product_code.category_id], "code_id": product_code.id}
                    )
            
            # 6. 删除原始分类
            for old_id in category_ids:
                db.session.execute(
                    text("DELETE FROM product_categories WHERE id = :id"),
                    {"id": old_id}
                )
            
            # 7. 按新顺序创建分类
            for data in category_data:
                db.session.execute(
                    text("INSERT INTO product_categories (id, name, code_letter, description, created_at, updated_at) VALUES (:id, :name, :code_letter, :description, :created_at, :updated_at)"),
                    {
                        "id": data['new_id'],
                        "name": data['name'],
                        "code_letter": data['code_letter'],
                        "description": data['description'],
                        "created_at": data['created_at'],
                        "updated_at": datetime.now()
                    }
                )
            
            # 8. 重新启用外键约束
            if db.engine.url.drivername == 'sqlite':
                db.session.execute(text('PRAGMA foreign_keys = ON'))
            
            # 提交事务
            db.session.commit()
            
            # 提交后返回成功
            return jsonify({
                'success': True, 
                'message': '分类排序成功，ID已重新排序',
                'new_order': list(old_to_new.values())
            })
        
        except Exception as e:
            # 发生异常时回滚事务
            db.session.rollback()
            
            # 确保外键约束被重新启用
            if db.engine.url.drivername == 'sqlite':
                db.session.execute(text('PRAGMA foreign_keys = ON'))
                
            # 重新抛出异常以便外部捕获
            raise e
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_message = str(e)
        print(f"排序更新失败: {error_message}")
        return jsonify({'success': False, 'message': f'排序更新失败: {error_message}'}), 500 

@product_code_bp.route('/api/subcategory/<int:id>/update-fields-order', methods=['POST'])
@login_required
@product_manager_required
def update_fields_order(id):
    """更新规格字段的顺序"""
    if not request.is_json:
        current_app.logger.error(f"非JSON请求: {request.data}")
        return jsonify({"success": False, "error": "请求必须是JSON格式"}), 400
    
    try:
        # 获取并记录请求体
        request_data = request.get_data(as_text=True)
        current_app.logger.info(f"原始请求数据: {request_data}")
        
        # 解析JSON数据
        try:
            data = request.get_json(force=True)
        except Exception as e:
            current_app.logger.error(f"JSON解析错误: {str(e)}, 原始数据: {request_data}")
            return jsonify({"success": False, "error": f"JSON解析错误: {str(e)}"}), 400
        
        current_app.logger.info(f"接收到的数据: {data}")
        
        if not data:
            current_app.logger.error("无法解析JSON数据")
            return jsonify({"success": False, "error": "无法解析JSON数据"}), 400
        
        # 支持两种格式：sortable-list.js 的 {items: [{id, order}]} 或原有的 {field_ids: []}
        if 'items' in data:
            # sortable-list.js 格式: {items: [{id, order}]}
            items = sorted(data['items'], key=lambda x: x.get('order', 0))
            field_ids = [item['id'] for item in items]
            current_app.logger.info(f"使用items格式，转换后的字段ID列表: {field_ids}")
        elif 'field_ids' in data:
            # 原有格式: {field_ids: []}
            field_ids = data.get('field_ids', [])
            current_app.logger.info(f"使用field_ids格式，字段ID列表: {field_ids}")
        else:
            current_app.logger.error("未提供有效的请求格式")
            return jsonify({"success": False, "error": "请提供 items 或 field_ids 参数"}), 400

        if not field_ids:
            current_app.logger.error("未提供字段ID列表或列表为空")
            return jsonify({"success": False, "error": "未提供字段ID列表"}), 400
        
        # 确保所有ID都是整数
        try:
            field_ids = [int(field_id) for field_id in field_ids if field_id]
            current_app.logger.info(f"转换后的字段ID列表: {field_ids}")
        except (ValueError, TypeError) as e:
            current_app.logger.error(f"ID转换错误: {str(e)}, 原始数据: {field_ids}")
            return jsonify({"success": False, "error": f"字段ID必须是整数: {str(e)}"}), 400
        
        # 确保有效的字段ID
        if not field_ids:
            current_app.logger.error("所有字段ID均无效")
            return jsonify({"success": False, "error": "所有字段ID均无效"}), 400
        
        # 验证子类别是否存在
        subcategory = ProductSubcategory.query.get_or_404(id)
        
        # 验证所有字段ID是否属于这个子类别
        existing_fields = ProductCodeField.query.filter_by(subcategory_id=id).all()
        existing_field_ids = set(field.id for field in existing_fields)
        current_app.logger.info(f"现有字段ID: {existing_field_ids}")
        
        # 使用新的严格检查逻辑：字段名+位置+编码都匹配才算被引用
        valid_field_ids = []
        invalid_field_ids = []
        blocked_field_ids = []  # 被引用无法修改排序的字段

        for field_id in field_ids:
            if field_id in existing_field_ids:
                # 使用新的严格检查逻辑
                field = next((f for f in existing_fields if f.id == field_id), None)
                if field and check_field_used_in_subcategory(field.name, id, field.id):
                    blocked_field_ids.append(field_id)
                    current_app.logger.warning(f"字段 '{field.name}' (ID: {field_id}) 已被产品引用，不允许修改排序")
                else:
                    valid_field_ids.append(field_id)
            else:
                invalid_field_ids.append(field_id)

        # 如果有被引用的字段，返回错误
        if blocked_field_ids:
            blocked_fields = [f for f in existing_fields if f.id in blocked_field_ids]
            blocked_names = [f.name for f in blocked_fields]
            return jsonify({
                "success": False,
                "error": f"以下规格字段已被产品引用，不允许修改排序: {', '.join(blocked_names)}"
            }), 400
        
        if invalid_field_ids:
            current_app.logger.warning(f"忽略无效字段ID: {invalid_field_ids}")
        
        if not valid_field_ids:
            current_app.logger.error("没有有效的字段ID")
            return jsonify({"success": False, "error": "没有有效的字段ID属于此子类别"}), 400
        
        # 获取字段类型参数：coding（编码规格）或 non_coding（非编码规格）
        field_type = data.get('field_type', 'coding')

        if field_type == 'non_coding':
            # 非编码规格：独立的位置序列，从1开始
            start_position = 1
            current_app.logger.info(f"非编码规格排序，起始位置: {start_position}")
        else:
            # 编码规格：位置计算，前3位是固定的（区域+分类+子分类），规格从位置4开始
            FIXED_PREFIX_POSITIONS = 3  # 区域、分类、子分类占用前3位

            # 获取继承字段（分类级字段）的最大位置
            inherited_fields = ProductCodeField.get_category_fields(subcategory.category_id)
            inherited_code_fields = [f for f in inherited_fields if f.use_in_code]

            if inherited_code_fields:
                # 子分类字段从继承字段之后开始
                start_position = max(f.position for f in inherited_code_fields) + 1
            else:
                # 没有继承字段，从位置4开始（前3位是固定前缀）
                start_position = FIXED_PREFIX_POSITIONS + 1

            current_app.logger.info(f"编码规格排序，继承字段数量: {len(inherited_code_fields)}, 起始位置: {start_position}")

        # 更新位置值（编码位置从继承字段之后开始）
        try:
            with db.session.begin_nested():  # 创建保存点
                for idx, field_id in enumerate(valid_field_ids):
                    new_position = start_position + idx
                    db.session.execute(
                        update(ProductCodeField)
                        .where(ProductCodeField.id == field_id)
                        .values(position=new_position)
                    )
            
            db.session.commit()
            current_app.logger.info(f"成功更新字段位置: {valid_field_ids}")
            
            # 获取更新后的字段信息
            updated_fields = ProductCodeField.query.filter(
                ProductCodeField.id.in_(valid_field_ids)
            ).all()
            
            # 构建返回数据
            positions = []
            for field in updated_fields:
                positions.append({
                    'id': field.id,
                    'position': field.position,
                    'use_in_code': field.use_in_code
                })
            
            return jsonify({
                "success": True, 
                "message": "规格顺序已更新",
                "positions": positions
            }), 200
        
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"数据库操作错误: {str(e)}")
            return jsonify({"success": False, "error": f"数据库操作错误: {str(e)}"}), 500
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新规格顺序时出错: {str(e)}")
        return jsonify({"success": False, "error": f"更新规格顺序时出错: {str(e)}"}), 500


@product_code_bp.route('/api/category/<int:id>/update-fields-order', methods=['POST'])
@login_required
@product_manager_required
def update_category_fields_order(id):
    """更新分类级规格字段的顺序

    如果任何字段已被产品引用，则拒绝排序操作
    """
    if not request.is_json:
        return jsonify({"success": False, "message": "请求必须是JSON格式"}), 400

    try:
        data = request.get_json()
        items = data.get('items', [])

        if not items:
            return jsonify({"success": False, "message": "未提供排序数据"}), 400

        # 验证分类存在
        category = ProductCategory.query.get_or_404(id)

        # 获取分类级字段（subcategory_id为NULL，category_id为当前分类）
        existing_fields = ProductCodeField.query.filter(
            ProductCodeField.category_id == id,
            ProductCodeField.subcategory_id.is_(None)
        ).all()
        existing_field_ids = {field.id for field in existing_fields}

        # 检查是否有任何字段被产品引用
        for field in existing_fields:
            used_count = db.session.execute(
                text("""
                    SELECT COUNT(*) FROM dev_product_specs dps
                    INNER JOIN dev_products dp ON dps.dev_product_id = dp.id
                    INNER JOIN product_subcategories ps ON dp.subcategory_id = ps.id
                    WHERE dps.field_name = :field_name
                    AND ps.category_id = :category_id
                """),
                {"field_name": field.name, "category_id": id}
            ).scalar() or 0

            if used_count > 0:
                return jsonify({
                    "success": False,
                    "message": f"规格「{field.name}」已被产品使用，无法调整排序"
                }), 400

        # 验证所有提交的字段ID都属于这个分类
        for item in items:
            field_id = int(item.get('id', 0))
            if field_id not in existing_field_ids:
                return jsonify({
                    "success": False,
                    "message": f"字段ID {field_id} 不属于此分类"
                }), 400

        # 编码位置计算：前3位是固定的（区域+分类+子分类），规格从位置4开始
        FIXED_PREFIX_POSITIONS = 3

        # 更新字段顺序并收集位置信息（位置从4开始）
        positions = []
        for item in items:
            field_id = int(item.get('id'))
            new_order = int(item.get('order'))
            # 位置从4开始（前3位是固定前缀）
            new_position = FIXED_PREFIX_POSITIONS + new_order + 1

            field = ProductCodeField.query.get(field_id)
            if field:
                field.position = new_position
                positions.append({
                    'id': field_id,
                    'position': new_position,
                    'use_in_code': field.use_in_code
                })

        db.session.commit()

        return jsonify({"success": True, "message": "排序已保存", "positions": positions})

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新分类规格顺序时出错: {str(e)}")
        return jsonify({"success": False, "message": f"保存失败: {str(e)}"}), 500


@product_code_bp.route('/api/category/<int:id>/update-subcategories-order', methods=['POST'])
@login_required
@product_manager_required
def update_subcategories_order(id):
    """更新子类别顺序并重排ID"""
    try:
        # 获取前端传来的排序
        data = request.json
        subcategory_ids = data.get('order', [])
        
        if not subcategory_ids:
            return jsonify({'success': False, 'message': '未提供排序数据'}), 400
        
        # 将字符串ID转换为整数ID
        subcategory_ids = [int(id) for id in subcategory_ids]
        
        # 验证所有子类别是否属于这个分类
        category = ProductCategory.query.get_or_404(id)
        existing_subcategories = ProductSubcategory.query.filter_by(category_id=id).all()
        existing_subcategory_ids = set(subcat.id for subcat in existing_subcategories)
        
        for subcat_id in subcategory_ids:
            if subcat_id not in existing_subcategory_ids:
                return jsonify({"success": False, "error": f"子类别ID {subcat_id} 不属于此分类"}), 400
        
        # 创建ID映射字典
        old_to_new = {old_id: i+1 for i, old_id in enumerate(subcategory_ids)}
        
        # 1. 获取所有子类别
        subcategories = {subcat.id: subcat for subcat in existing_subcategories}
        
        # 2. 获取所有需要更新的关联记录
        product_codes = ProductCode.query.filter(
            ProductCode.subcategory_id.in_(subcategory_ids)
        ).all()
        
        fields = ProductCodeField.query.filter(
            ProductCodeField.subcategory_id.in_(subcategory_ids)
        ).all()
        
        # 创建事务
        try:
            # 3. 先保存所有子类别的当前数据
            subcategory_data = []
            for old_id in subcategory_ids:
                if old_id in subcategories:
                    subcat = subcategories[old_id]
                    # 保存子类别数据
                    subcategory_data.append({
                        'old_id': old_id,
                        'new_id': old_to_new[old_id],
                        'category_id': subcat.category_id,
                        'name': subcat.name,
                        'code_letter': subcat.code_letter,
                        'description': subcat.description,
                        'created_at': subcat.created_at
                    })
            
            # 4. 先禁用外键约束检查
            if db.engine.url.drivername == 'sqlite':
                db.session.execute(text('PRAGMA foreign_keys = OFF'))
            
            # 5. 更新关联表中的外键引用
            for product_code in product_codes:
                if product_code.subcategory_id in old_to_new:
                    db.session.execute(
                        text("UPDATE product_codes SET subcategory_id = :new_id WHERE id = :code_id"),
                        {"new_id": old_to_new[product_code.subcategory_id], "code_id": product_code.id}
                    )
            
            for field in fields:
                if field.subcategory_id in old_to_new:
                    db.session.execute(
                        text("UPDATE product_code_fields SET subcategory_id = :new_id WHERE id = :field_id"),
                        {"new_id": old_to_new[field.subcategory_id], "field_id": field.id}
                    )
            
            # 6. 删除原始子类别
            for old_id in subcategory_ids:
                db.session.execute(
                    text("DELETE FROM product_subcategories WHERE id = :id"),
                    {"id": old_id}
                )
            
            # 7. 按新顺序创建子类别
            for data in subcategory_data:
                db.session.execute(
                    text("INSERT INTO product_subcategories (id, category_id, name, code_letter, description, created_at, updated_at) VALUES (:id, :category_id, :name, :code_letter, :description, :created_at, :updated_at)"),
                    {
                        "id": data['new_id'],
                        "category_id": data['category_id'],
                        "name": data['name'],
                        "code_letter": data['code_letter'],
                        "description": data['description'],
                        "created_at": data['created_at'],
                        "updated_at": datetime.now()
                    }
                )
            
            # 8. 重新启用外键约束
            if db.engine.url.drivername == 'sqlite':
                db.session.execute(text('PRAGMA foreign_keys = ON'))
            
            # 提交事务
            db.session.commit()
            
            # 提交后返回成功
            return jsonify({
                'success': True, 
                'message': '子类别排序成功，ID已重新排序',
                'new_order': list(old_to_new.values())
            })
        
        except Exception as e:
            # 发生异常时回滚事务
            db.session.rollback()
            
            # 确保外键约束被重新启用
            if db.engine.url.drivername == 'sqlite':
                db.session.execute(text('PRAGMA foreign_keys = ON'))
                
            # 重新抛出异常以便外部捕获
            raise e
            
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_message = str(e)
        print(f"子类别排序更新失败: {error_message}")
        return jsonify({'success': False, 'message': f'排序更新失败: {error_message}'}), 500 

@product_code_bp.route('/subcategory/update_order', methods=['POST'])
@login_required
def update_subcategory_order():
    """更新子分类排序序号"""
    try:
        data = request.get_json()
        if not data or 'items' not in data:
            return jsonify({'success': False, 'message': '无效的数据格式'}), 400

        items = data['items']
        for item in items:
            subcategory_id = item.get('id')
            new_order = item.get('order')
            
            if subcategory_id is None or new_order is None:
                continue
                
            subcategory = ProductSubcategory.query.get(subcategory_id)
            if subcategory:
                subcategory.display_order = new_order
        
        db.session.commit()
        return jsonify({'success': True, 'message': '排序更新成功'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新子分类排序失败: {str(e)}")
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500

@product_code_bp.route('/category/update_order', methods=['POST'])
@login_required
@product_manager_required
def update_category_display_order():
    """更新产品分类显示顺序（使用display_order字段）"""
    try:
        data = request.get_json()
        if not data or 'items' not in data:
            return jsonify({'success': False, 'message': '无效的数据格式'}), 400

        items = data['items']
        for item in items:
            category_id = item.get('id')
            new_order = item.get('order')

            if category_id is None or new_order is None:
                continue

            category = ProductCategory.query.get(category_id)
            if category:
                category.display_order = new_order

        db.session.commit()
        return jsonify({'success': True, 'message': '分类排序更新成功'})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新分类排序失败: {str(e)}")
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500

@product_code_bp.route('/cleanup-invalid-codes', methods=['POST'])
@login_required
@admin_required
def cleanup_invalid_codes():
    """清理无效的指标编码（非英文字母数字的编码）"""
    try:
        # 查找所有无效编码
        all_options = ProductCodeFieldOption.query.all()
        invalid_options = []
        
        for option in all_options:
            code = option.code
            if code and not (len(code) == 1 and (code.isalpha() or code.isdigit()) and code.isascii()):
                invalid_options.append({
                    'id': option.id,
                    'field_id': option.field_id,
                    'value': option.value,
                    'invalid_code': code
                })
        
        if not invalid_options:
            return jsonify({'success': True, 'message': '未找到无效编码'})
        
        # 为无效编码重新分配有效编码
        fixed_count = 0
        for invalid_option in invalid_options:
            option = ProductCodeFieldOption.query.get(invalid_option['id'])
            if not option:
                continue
                
            # 获取该字段下所有已使用的有效编码
            used_codes = db.session.query(ProductCodeFieldOption.code).filter_by(
                field_id=option.field_id
            ).filter(ProductCodeFieldOption.id != option.id).all()
            
            valid_used_codes = []
            for code_tuple in used_codes:
                code = code_tuple[0]
                if code and len(code) == 1 and (code.isalpha() or code.isdigit()) and code.isascii():
                    valid_used_codes.append(code.upper())
            
            # 找一个可用的编码
            available_letters = [letter for letter in string.ascii_uppercase if letter not in valid_used_codes]
            if not available_letters:
                available_letters = [str(digit) for digit in range(10) if str(digit) not in valid_used_codes]
            
            if available_letters:
                new_code = available_letters[0]  # 取第一个可用的
                option.code = new_code
                fixed_count += 1
                current_app.logger.info(f"修复无效编码: '{invalid_option['invalid_code']}' -> '{new_code}' (指标: {option.value})")
        
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': f'成功修复 {fixed_count} 个无效编码',
            'fixed_count': fixed_count,
            'invalid_options': invalid_options
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"清理无效编码失败: {str(e)}")
        return jsonify({'success': False, 'message': f'清理失败: {str(e)}'}), 500


# ============================================================================
# 快速添加API - 用于通用选择器组件
# ============================================================================

@product_code_bp.route('/api/subcategories/quick-add', methods=['POST'])
@login_required
@product_manager_required
def quick_add_subcategory():
    """
    快速添加产品名称（子分类）API
    用于产品创建页面的产品名称选择器
    """
    try:
        data = request.get_json()
        category_id = data.get('category_id') or data.get('related_id')
        name = data.get('value', '').strip()
        description = data.get('description', '').strip()

        # 验证必填字段
        if not category_id:
            return jsonify({'success': False, 'message': '缺少产品分类ID'}), 400
        if not name:
            return jsonify({'success': False, 'message': '产品名称不能为空'}), 400

        # 验证分类是否存在
        category = ProductCategory.query.get(category_id)
        if not category:
            return jsonify({'success': False, 'message': '产品分类不存在'}), 404

        # 检查同一分类下是否已存在相同名称
        existing = ProductSubcategory.query.filter_by(
            category_id=category_id,
            name=name
        ).first()
        if existing:
            return jsonify({'success': False, 'message': f'产品名称 "{name}" 已存在'}), 400

        # 生成唯一的code_letter
        used_codes = db.session.query(ProductSubcategory.code_letter).filter_by(
            category_id=category_id
        ).all()
        used_codes_set = {code[0].upper() for code in used_codes if code[0]}

        # 优先使用字母，其次使用数字
        available_codes = [letter for letter in string.ascii_uppercase if letter not in used_codes_set]
        if not available_codes:
            available_codes = [str(digit) for digit in range(10) if str(digit) not in used_codes_set]

        if not available_codes:
            return jsonify({'success': False, 'message': '无可用编码，该分类下产品名称已达上限'}), 400

        code_letter = available_codes[0]

        # 创建新的子分类
        new_subcategory = ProductSubcategory(
            category_id=category_id,
            name=name,
            code_letter=code_letter,
            description=description
        )

        db.session.add(new_subcategory)
        db.session.commit()

        current_app.logger.info(f'快速添加产品名称成功: {name} (编码: {code_letter}), 用户: {current_user.username}')

        return jsonify({
            'success': True,
            'message': f'产品名称 "{name}" 添加成功',
            'new_item': {
                'id': new_subcategory.id,
                'name': new_subcategory.name,
                'value': new_subcategory.name,
                'code': code_letter,
                'code_letter': code_letter,
                'description': new_subcategory.description
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'快速添加产品名称失败: {str(e)}', exc_info=True)
        return jsonify({'success': False, 'message': f'添加失败: {str(e)}'}), 500


@product_code_bp.route('/api/regions/quick-add', methods=['POST'])
@login_required
@product_manager_required
def quick_add_region():
    """
    快速添加销售区域API
    用于产品创建页面的销售区域选择器
    """
    try:
        data = request.get_json()
        name = data.get('value', '').strip()
        description = data.get('description', '').strip()

        # 验证必填字段
        if not name:
            return jsonify({'success': False, 'message': '区域名称不能为空'}), 400

        # 检查是否已存在相同名称
        existing = ProductCodeField.query.filter_by(
            field_type='origin_location',
            name=name
        ).first()
        if existing:
            return jsonify({'success': False, 'message': f'销售区域 "{name}" 已存在'}), 400

        # 生成唯一的code
        used_codes = db.session.query(ProductCodeField.code).filter_by(
            field_type='origin_location'
        ).all()
        used_codes_set = {code[0].upper() for code in used_codes if code[0]}

        # 优先使用字母，其次使用数字
        available_codes = [letter for letter in string.ascii_uppercase if letter not in used_codes_set]
        if not available_codes:
            available_codes = [str(digit) for digit in range(10) if str(digit) not in used_codes_set]

        if not available_codes:
            return jsonify({'success': False, 'message': '无可用编码，销售区域已达上限'}), 400

        code = available_codes[0]

        # 获取下一个position
        max_position = db.session.query(db.func.max(ProductCodeField.position)).filter_by(
            field_type='origin_location'
        ).scalar() or 0

        # 创建新的区域（注意：ProductCodeField需要subcategory_id，这里暂时设为NULL或使用特殊值）
        # 由于ProductCodeField的subcategory_id是NOT NULL，我们需要一个解决方案
        # 暂时使用第一个子分类的ID作为占位符
        first_subcategory = ProductSubcategory.query.first()
        if not first_subcategory:
            return jsonify({'success': False, 'message': '系统中没有产品分类，无法创建销售区域'}), 400

        new_region = ProductCodeField(
            subcategory_id=first_subcategory.id,  # 使用占位符
            field_type='origin_location',
            name=name,
            code=code,
            description=description,
            position=max_position + 1,
            is_required=False,
            use_in_code=True
        )

        db.session.add(new_region)
        db.session.commit()

        current_app.logger.info(f'快速添加销售区域成功: {name} (编码: {code}), 用户: {current_user.username}')

        return jsonify({
            'success': True,
            'message': f'销售区域 "{name}" 添加成功',
            'new_item': {
                'id': new_region.id,
                'name': new_region.name,
                'value': new_region.name,
                'code': code,
                'code_letter': code,  # 向后兼容
                'description': new_region.description
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'快速添加销售区域失败: {str(e)}', exc_info=True)
        return jsonify({'success': False, 'message': f'添加失败: {str(e)}'}), 500


@product_code_bp.route('/api/subcategories', methods=['GET'])
@login_required
def get_subcategories():
    """
    获取产品名称列表API
    用于快速添加模态框显示已有项目
    """
    try:
        category_id = request.args.get('category_id')
        if not category_id:
            return jsonify({'success': False, 'message': '缺少分类ID'}), 400

        subcategories = ProductSubcategory.query.filter_by(category_id=category_id).all()

        items = [{
            'id': sub.id,
            'name': sub.name,
            'value': sub.name,
            'code': sub.code_letter,
            'is_active': True
        } for sub in subcategories]

        return jsonify({'success': True, 'items': items})

    except Exception as e:
        current_app.logger.error(f'获取产品名称列表失败: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500


@product_code_bp.route('/api/regions', methods=['GET'])
@login_required
def get_regions():
    """
    获取销售区域列表API
    用于快速添加模态框显示已有项目
    """
    try:
        regions = ProductCodeField.query.filter_by(field_type='origin_location').all()

        items = [{
            'id': region.id,
            'name': region.name,
            'value': region.name,
            'code': region.code,
            'is_active': True
        } for region in regions]

        return jsonify({'success': True, 'items': items})

    except Exception as e:
        current_app.logger.error(f'获取销售区域列表失败: {str(e)}')
        return jsonify({'success': False, 'message': str(e)}), 500

# ============================================================================
# 产品代码字段管理API - 模态框专用
# ============================================================================

@product_code_bp.route('/api/fields/available-specs/<int:subcategory_id>', methods=['GET'])
@login_required
@product_manager_required
@csrf.exempt
def get_available_specs(subcategory_id):
    """
    获取可用规格列表（从规格字典中过滤已使用的）

    Args:
        subcategory_id: 子分类ID
        exclude_field_id: 排除的字段ID（编辑时使用）

    Returns:
        JSON: {success, data: [{id, name, unit}]}
    """
    try:
        exclude_field_id = request.args.get('exclude_field_id', type=int)

        # 获取子分类信息，用于查找父分类
        subcategory = ProductSubcategory.query.get(subcategory_id)
        if not subcategory:
            return jsonify({
                'success': False,
                'message': '子分类不存在'
            }), 404

        # 获取所有启用的规格字典条目
        all_specs = SpecificationDictionary.query.filter_by(is_active=True).all()

        # 获取当前子分类已使用的规格名称（排除正在编辑的字段）
        used_specs_query = ProductCodeField.query.filter_by(
            subcategory_id=subcategory_id,
            field_type='spec'
        )

        if exclude_field_id:
            used_specs_query = used_specs_query.filter(ProductCodeField.id != exclude_field_id)

        used_spec_names = {field.name for field in used_specs_query.all()}

        # 获取分类级继承的规格名称（这些规格不应该在子分类中重复添加）
        inherited_specs = ProductCodeField.get_category_fields(subcategory.category_id)
        inherited_spec_names = {field.name for field in inherited_specs}

        # 合并已使用和继承的规格名称
        all_used_names = used_spec_names | inherited_spec_names

        # 过滤出可用的规格
        available_specs = [
            {
                'id': spec.id,
                'name': spec.name,
                'unit': spec.unit
            }
            for spec in all_specs
            if spec.name not in all_used_names
        ]

        return jsonify({
            'success': True,
            'data': available_specs
        })

    except Exception as e:
        current_app.logger.error(f'获取可用规格失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'获取可用规格失败: {str(e)}'
        }), 500


@product_code_bp.route('/api/fields', methods=['POST'])
@login_required
@product_manager_required
@csrf.exempt
def create_field():
    """
    创建产品代码字段

    Request Body:
        {
            "subcategory_id": int,
            "name": str,
            "is_required": bool,
            "use_in_code": bool
        }

    Returns:
        JSON: {success, message, data}
    """
    try:
        data = request.get_json()

        subcategory_id = data.get('subcategory_id')
        name = data.get('name', '').strip()
        is_required = data.get('is_required', False)
        use_in_code = data.get('use_in_code', False)

        # 验证必填字段
        if not subcategory_id or not name:
            return jsonify({
                'success': False,
                'message': '子分类ID和规格名称不能为空'
            }), 400

        # 验证子分类是否存在
        subcategory = ProductSubcategory.query.get(subcategory_id)
        if not subcategory:
            return jsonify({
                'success': False,
                'message': '子分类不存在'
            }), 404

        # 检查规格名称是否已存在于当前子分类
        existing_field = ProductCodeField.query.filter_by(
            subcategory_id=subcategory_id,
            name=name,
            field_type='spec'
        ).first()

        if existing_field:
            return jsonify({
                'success': False,
                'message': f'规格"{name}"已存在于当前产品分类中'
            }), 400

        # 如果纳入编码，检查编码位置是否已满
        if use_in_code:
            active_code_fields_count = ProductCodeField.query.filter_by(
                subcategory_id=subcategory_id,
                use_in_code=True
            ).count()

            if active_code_fields_count >= 10:
                return jsonify({
                    'success': False,
                    'message': '规格编码位置已满（最多10个位置），请取消其他规格的编码选择后再添加'
                }), 400

            # 计算新的编码位置
            max_code_position = db.session.query(db.func.max(ProductCodeField.position))\
                .filter_by(subcategory_id=subcategory_id, use_in_code=True).scalar()

            new_position = 4 if max_code_position is None else max_code_position + 1

            if new_position > 13:
                return jsonify({
                    'success': False,
                    'message': '编码位置已满（最多10个编码字段，位置4-13）'
                }), 400
        else:
            # 不纳入编码，使用更大的位置值
            max_position = db.session.query(db.func.max(ProductCodeField.position))\
                .filter_by(subcategory_id=subcategory_id).scalar() or 13
            new_position = max(max_position + 1, 14)

        # 创建新字段
        new_field = ProductCodeField(
            subcategory_id=subcategory_id,
            name=name,
            field_type='spec',
            description='',  # 不再使用描述字段
            position=new_position,
            max_length=1,  # 固定为1位
            is_required=is_required,
            use_in_code=use_in_code
        )

        db.session.add(new_field)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '规格创建成功',
            'data': {
                'id': new_field.id,
                'name': new_field.name,
                'position': new_field.position,
                'is_required': new_field.is_required,
                'use_in_code': new_field.use_in_code
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'创建字段失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'创建失败: {str(e)}'
        }), 500


@product_code_bp.route('/api/fields/<int:field_id>', methods=['GET'])
@login_required
@product_manager_required
@csrf.exempt
def get_field(field_id):
    """
    获取单个产品代码字段详情

    Args:
        field_id: 字段ID

    Returns:
        JSON: {success, data}
    """
    try:
        field = ProductCodeField.query.get(field_id)

        if not field:
            return jsonify({
                'success': False,
                'message': '字段不存在'
            }), 404

        if field.field_type != 'spec':
            return jsonify({
                'success': False,
                'message': '只能查询规格类型字段'
            }), 400

        return jsonify({
            'success': True,
            'data': {
                'id': field.id,
                'subcategory_id': field.subcategory_id,
                'name': field.name,
                'position': field.position,
                'is_required': field.is_required,
                'use_in_code': field.use_in_code
            }
        })

    except Exception as e:
        current_app.logger.error(f'获取字段失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@product_code_bp.route('/api/fields/<int:field_id>', methods=['PUT'])
@login_required
@product_manager_required
@csrf.exempt
def update_field(field_id):
    """
    更新产品代码字段

    Args:
        field_id: 字段ID

    Request Body:
        {
            "name": str,
            "is_required": bool,
            "use_in_code": bool
        }

    Returns:
        JSON: {success, message}
    """
    try:
        field = ProductCodeField.query.get(field_id)

        if not field:
            return jsonify({
                'success': False,
                'message': '字段不存在'
            }), 404

        if field.field_type != 'spec':
            return jsonify({
                'success': False,
                'message': '只能编辑规格类型字段'
            }), 400

        # 检查字段是否已被使用
        if check_field_used_in_subcategory(field.name, field.subcategory_id):
            return jsonify({
                'success': False,
                'message': '此规格已被产品使用，无法修改'
            }), 400

        data = request.get_json()

        name = data.get('name', '').strip()
        is_required = data.get('is_required', False)
        use_in_code = data.get('use_in_code', False)

        if not name:
            return jsonify({
                'success': False,
                'message': '规格名称不能为空'
            }), 400

        # 检查名称是否与其他字段冲突（排除当前字段）
        existing_field = ProductCodeField.query.filter(
            ProductCodeField.subcategory_id == field.subcategory_id,
            ProductCodeField.name == name,
            ProductCodeField.field_type == 'spec',
            ProductCodeField.id != field_id
        ).first()

        if existing_field:
            return jsonify({
                'success': False,
                'message': f'规格"{name}"已存在于当前产品分类中'
            }), 400

        # 如果use_in_code状态发生变化，重新计算position
        if field.use_in_code != use_in_code:
            if use_in_code:
                # 变为纳入编码，检查位置是否已满
                active_code_fields_count = ProductCodeField.query.filter(
                    ProductCodeField.subcategory_id == field.subcategory_id,
                    ProductCodeField.use_in_code == True,
                    ProductCodeField.id != field_id
                ).count()

                if active_code_fields_count >= 10:
                    return jsonify({
                        'success': False,
                        'message': '规格编码位置已满（最多10个位置）'
                    }), 400

                # 分配新的编码位置
                field.position = 4 + active_code_fields_count
            else:
                # 变为不纳入编码，使用大的position值
                max_position = db.session.query(db.func.max(ProductCodeField.position))\
                    .filter_by(subcategory_id=field.subcategory_id).scalar() or 100
                field.position = max_position + 1

        # 更新字段属性
        field.name = name
        field.is_required = is_required
        field.use_in_code = use_in_code

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '规格更新成功'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'更新字段失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500


@product_code_bp.route('/api/fields/<int:field_id>', methods=['DELETE'])
@login_required
@product_manager_required
@csrf.exempt
def delete_field_api(field_id):
    """
    删除产品代码字段

    Args:
        field_id: 字段ID

    Returns:
        JSON: {success, message}
    """
    try:
        field = ProductCodeField.query.get(field_id)

        if not field:
            return jsonify({
                'success': False,
                'message': '字段不存在'
            }), 404

        if field.field_type != 'spec':
            return jsonify({
                'success': False,
                'message': '只能删除规格类型字段'
            }), 400

        # 检查是否有产品编码使用此规格
        if ProductCodeFieldValue.query.filter_by(field_id=field_id).first():
            return jsonify({
                'success': False,
                'message': '无法删除此规格，因为已有产品编码使用'
            }), 400

        # 检查字段是否已被使用（研发库）
        if check_field_used_in_subcategory(field.name, field.subcategory_id):
            return jsonify({
                'success': False,
                'message': '此规格已被产品使用，无法删除'
            }), 400

        subcategory_id = field.subcategory_id

        # 删除规格的所有指标
        ProductCodeFieldOption.query.filter_by(field_id=field_id).delete()

        # 删除规格
        db.session.delete(field)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '规格删除成功'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'删除字段失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500
# ============================================================================
# 产品代码指标管理API - 模态框专用
# ============================================================================

@product_code_bp.route('/api/fields/<int:field_id>/options', methods=['GET'])
@login_required
@product_manager_required
@csrf.exempt
def get_options_api(field_id):
    """
    获取指标列表（包含单位信息）

    Args:
        field_id: 规格字段ID

    Returns:
        JSON: {success, data: {options, field_name, field_unit}}
    """
    try:
        field = ProductCodeField.query.get(field_id)

        if not field:
            return jsonify({
                'success': False,
                'message': '规格字段不存在'
            }), 404

        # 获取所有指标，按激活状态和位置排序
        options = ProductCodeFieldOption.query.filter_by(field_id=field_id)\
            .order_by(ProductCodeFieldOption.is_active.desc(), ProductCodeFieldOption.position).all()

        # 检查每个指标是否被使用（研发库+产品库）
        options_data = []
        for option in options:
            # 检查是否被产品编码使用
            used_in_formal = ProductCodeFieldValue.query.filter_by(option_id=option.id).first() is not None

            # 检查是否被研发产品使用
            used_in_dev = db.session.execute(
                text("""
                    SELECT 1 FROM dev_product_specs dps
                    INNER JOIN dev_products dp ON dps.dev_product_id = dp.id
                    WHERE dps.field_name = :field_name
                    AND dps.field_value = :value
                    AND dp.subcategory_id = :subcategory_id
                    LIMIT 1
                """),
                {
                    "field_name": field.name,
                    "value": option.value,
                    "subcategory_id": field.subcategory_id
                }
            ).first() is not None

            # 检查是否被产品库使用
            used_in_product = db.session.execute(
                text("""
                    SELECT 1 FROM product_specs ps
                    INNER JOIN products p ON ps.product_id = p.id
                    WHERE ps.field_name = :field_name
                    AND ps.field_value = :value
                    AND p.subcategory_id = :subcategory_id
                    LIMIT 1
                """),
                {
                    "field_name": field.name,
                    "value": option.value,
                    "subcategory_id": field.subcategory_id
                }
            ).first() is not None

            options_data.append({
                'id': option.id,
                'value': option.value,
                'code': option.code,
                'description': option.description,
                'is_active': option.is_active,
                'position': option.position,
                'is_used': used_in_formal or used_in_dev or used_in_product
            })

        # 获取规格单位
        field_unit = get_field_unit(field.name)

        return jsonify({
            'success': True,
            'data': {
                'options': options_data,
                'field_name': field.name,
                'field_unit': field_unit
            }
        })

    except Exception as e:
        current_app.logger.error(f'获取指标列表失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'获取指标列表失败: {str(e)}'
        }), 500


@product_code_bp.route('/api/fields/<int:field_id>/options', methods=['POST'])
@login_required
@product_manager_required
@csrf.exempt
def create_option_api(field_id):
    """
    创建指标（支持引用模式）

    新架构下，指标和编码统一存储在 SpecificationOption 中，
    ProductCodeFieldOption 只创建引用。

    Args:
        field_id: 规格字段ID

    Request Body:
        {
            "value": str,           # 指标名称
            "description": str,     # 指标说明（可选）
            "spec_option_id": int   # 直接引用已有的规格指标ID（可选）
        }

    Returns:
        JSON: {success, message, data}
    """
    try:
        field = ProductCodeField.query.get(field_id)

        if not field:
            return jsonify({
                'success': False,
                'message': '规格字段不存在'
            }), 404

        data = request.get_json()

        # 如果提供了 spec_option_id，直接创建引用
        spec_option_id = data.get('spec_option_id')
        if spec_option_id:
            return _create_option_by_reference(field_id, spec_option_id)

        # 否则按值创建
        value = data.get('value', '').strip()
        description = data.get('description', '').strip()

        if not value:
            return jsonify({
                'success': False,
                'message': '指标名称不能为空'
            }), 400

        # 检查该字段下是否已有该指标（通过value或spec_option引用）
        existing_option = ProductCodeFieldOption.query.filter_by(
            field_id=field_id,
            value=value
        ).first()

        if existing_option:
            return jsonify({
                'success': False,
                'message': f'指标"{value}"已存在'
            }), 400

        # 检查是否通过spec_option引用已存在
        existing_by_ref = ProductCodeFieldOption.query.filter(
            ProductCodeFieldOption.field_id == field_id,
            ProductCodeFieldOption.spec_option_id.isnot(None)
        ).join(SpecificationOption).filter(
            SpecificationOption.value == value
        ).first()

        if existing_by_ref:
            return jsonify({
                'success': False,
                'message': f'指标"{value}"已存在（通过引用）'
            }), 400

        # 查找对应的规格字典
        spec_dict = SpecificationDictionary.query.filter_by(name=field.name).first()

        if not spec_dict:
            return jsonify({
                'success': False,
                'message': f'规格 {field.name} 不在规格字典中'
            }), 400

        # 使用新架构：引用模式
        return _create_option_with_spec_reference(field_id, field.name, spec_dict.id, value, description)

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'创建指标失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'创建失败: {str(e)}'
        }), 500


def _create_option_by_reference(field_id, spec_option_id):
    """通过引用已有的规格指标创建选项"""
    from app.models.product_code import SpecificationOption

    # 查找规格指标
    spec_option = SpecificationOption.query.get(spec_option_id)
    if not spec_option:
        return jsonify({
            'success': False,
            'message': '规格指标不存在'
        }), 404

    # 检查是否已引用
    existing = ProductCodeFieldOption.query.filter_by(
        field_id=field_id,
        spec_option_id=spec_option_id
    ).first()

    if existing:
        return jsonify({
            'success': False,
            'message': f'指标"{spec_option.value}"已存在于该字段'
        }), 400

    # 计算position
    max_position = db.session.query(db.func.max(ProductCodeFieldOption.position))\
        .filter_by(field_id=field_id).scalar() or 0

    # 创建引用
    new_option = ProductCodeFieldOption(
        field_id=field_id,
        spec_option_id=spec_option_id,
        value=spec_option.value,  # 冗余存储便于查询
        code=spec_option.code,    # 冗余存储便于查询
        is_active=True,
        position=max_position + 1
    )

    db.session.add(new_option)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': '指标引用创建成功',
        'data': {
            'id': new_option.id,
            'value': spec_option.value,
            'code': spec_option.code,
            'spec_option_id': spec_option_id
        }
    })


def _create_option_with_spec_reference(field_id, field_name, spec_id, value, description):
    """使用新架构创建指标（先在规格字典中创建，再引用）"""
    from app.models.product_code import SpecificationOption
    from app.routes.spec_dictionary import generate_smart_code

    # 检查 SpecificationOption 中是否已有该值
    existing_spec_option = SpecificationOption.query.filter_by(
        spec_id=spec_id,
        value=value
    ).first()

    if existing_spec_option:
        # 直接引用
        spec_option = existing_spec_option
    else:
        # 在规格字典中创建新指标
        code = generate_smart_code(spec_id, value)
        if not code:
            return jsonify({
                'success': False,
                'message': '无法生成唯一编码，编码空间已用尽'
            }), 500

        # 获取当前最大position
        max_spec_position = db.session.query(db.func.max(SpecificationOption.position))\
            .filter_by(spec_id=spec_id).scalar() or 0

        spec_option = SpecificationOption(
            spec_id=spec_id,
            value=value,
            code=code,
            description=description if description else None,
            is_active=True,
            position=max_spec_position + 1,
            created_at=datetime.utcnow()
        )
        db.session.add(spec_option)
        db.session.flush()  # 获取ID

    # 计算字段选项的position
    max_position = db.session.query(db.func.max(ProductCodeFieldOption.position))\
        .filter_by(field_id=field_id).scalar() or 0

    # 创建引用
    new_option = ProductCodeFieldOption(
        field_id=field_id,
        spec_option_id=spec_option.id,
        value=spec_option.value,
        code=spec_option.code,
        description=description if description else None,
        is_active=True,
        position=max_position + 1
    )

    db.session.add(new_option)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'指标创建成功，编码: {spec_option.code}',
        'data': {
            'id': new_option.id,
            'value': spec_option.value,
            'code': spec_option.code,
            'spec_option_id': spec_option.id
        }
    })


@product_code_bp.route('/api/options/<int:option_id>', methods=['GET'])
@login_required
@product_manager_required
@csrf.exempt
def get_option_api(option_id):
    """
    获取单个指标详情

    Args:
        option_id: 指标ID

    Returns:
        JSON: {success, data}
    """
    try:
        option = ProductCodeFieldOption.query.get(option_id)

        if not option:
            return jsonify({
                'success': False,
                'message': '指标不存在'
            }), 404

        return jsonify({
            'success': True,
            'data': {
                'id': option.id,
                'field_id': option.field_id,
                'value': option.effective_value,  # 使用 effective_value 获取正确的值
                'code': option.effective_code,    # 使用 effective_code 获取正确的编码
                'description': option.description,
                'is_active': option.is_active,
                'position': option.position
            }
        })

    except Exception as e:
        current_app.logger.error(f'获取指标失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@product_code_bp.route('/api/options/<int:option_id>', methods=['PUT'])
@login_required
@product_manager_required
@csrf.exempt
def update_option_api(option_id):
    """
    更新指标

    Args:
        option_id: 指标ID

    Request Body:
        {
            "value": str,
            "description": str
        }

    Returns:
        JSON: {success, message}
    """
    try:
        option = ProductCodeFieldOption.query.get(option_id)

        if not option:
            return jsonify({
                'success': False,
                'message': '指标不存在'
            }), 404

        # 检查指标是否被使用
        used_in_formal = ProductCodeFieldValue.query.filter_by(option_id=option_id).first() is not None

        field = ProductCodeField.query.get(option.field_id)
        used_in_dev = db.session.execute(
            text("""
                SELECT 1 FROM dev_product_specs dps
                INNER JOIN dev_products dp ON dps.dev_product_id = dp.id
                WHERE dps.field_name = :field_name
                AND dps.field_value = :value
                AND dp.subcategory_id = :subcategory_id
                LIMIT 1
            """),
            {
                "field_name": field.name,
                "value": option.value,
                "subcategory_id": field.subcategory_id
            }
        ).first() is not None

        if used_in_formal or used_in_dev:
            return jsonify({
                'success': False,
                'message': '此指标已被产品使用，无法修改'
            }), 400

        data = request.get_json()
        value = data.get('value', '').strip()
        description = data.get('description', '').strip()

        if not value:
            return jsonify({
                'success': False,
                'message': '指标名称不能为空'
            }), 400

        # 检查名称是否与其他指标冲突
        existing_option = ProductCodeFieldOption.query.filter(
            ProductCodeFieldOption.field_id == option.field_id,
            ProductCodeFieldOption.value == value,
            ProductCodeFieldOption.id != option_id
        ).first()

        if existing_option:
            return jsonify({
                'success': False,
                'message': f'指标"{value}"已存在'
            }), 400

        # 更新指标
        option.value = value
        option.description = description

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '指标更新成功'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'更新指标失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500


@product_code_bp.route('/api/options/<int:option_id>', methods=['DELETE'])
@login_required
@product_manager_required
@csrf.exempt
def delete_option_api(option_id):
    """
    删除指标（软删除）

    如果指标被产品使用，则标记为停用（is_active=False）而不是真删除
    已使用该指标的产品仍可正常显示，但新产品不会显示此选项

    Args:
        option_id: 指标ID

    Returns:
        JSON: {success, message, is_deactivated}
    """
    try:
        option = ProductCodeFieldOption.query.get(option_id)

        if not option:
            return jsonify({
                'success': False,
                'message': '指标不存在'
            }), 404

        field = ProductCodeField.query.get(option.field_id)

        # 检查是否被产品编码使用（旧版产品编码系统）
        used_in_product_code = ProductCodeFieldValue.query.filter_by(option_id=option_id).first() is not None

        # 检查是否被研发产品使用
        used_in_dev = db.session.execute(
            text("""
                SELECT 1 FROM dev_product_specs dps
                INNER JOIN dev_products dp ON dps.dev_product_id = dp.id
                WHERE dps.field_name = :field_name
                AND dps.field_value = :value
                AND dp.subcategory_id = :subcategory_id
                LIMIT 1
            """),
            {
                "field_name": field.name,
                "value": option.value,
                "subcategory_id": field.subcategory_id
            }
        ).first() is not None

        # 检查是否被正式产品使用
        from app.models.product import Product
        used_in_formal = db.session.execute(
            text("""
                SELECT 1 FROM product_specs ps
                INNER JOIN products p ON ps.product_id = p.id
                WHERE ps.field_name = :field_name
                AND ps.field_value = :value
                AND p.subcategory_id = :subcategory_id
                LIMIT 1
            """),
            {
                "field_name": field.name,
                "value": option.value,
                "subcategory_id": field.subcategory_id
            }
        ).first() is not None

        # 如果被任何产品使用，则软删除（标记为停用）
        if used_in_product_code or used_in_dev or used_in_formal:
            option.is_active = False
            db.session.commit()

            return jsonify({
                'success': True,
                'message': '操作成功',
                'is_deactivated': True
            })

        # 如果未被使用，可以真删除
        db.session.delete(option)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '操作成功',
            'is_deactivated': False
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'删除指标失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


@product_code_bp.route('/api/options/<int:option_id>/toggle', methods=['PATCH'])
@login_required
@product_manager_required
@csrf.exempt
def toggle_option_status_api(option_id):
    """
    切换指标启用/禁用状态

    Args:
        option_id: 指标ID

    Returns:
        JSON: {success, message, is_active}
    """
    try:
        option = ProductCodeFieldOption.query.get(option_id)

        if not option:
            return jsonify({
                'success': False,
                'message': '指标不存在'
            }), 404

        # 切换状态
        option.is_active = not option.is_active
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '操作成功',
            'is_active': option.is_active
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'切换指标状态失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'操作失败: {str(e)}'
        }), 500


# ============================================================================
# 产品分类管理 API
# ============================================================================

@product_code_bp.route('/api/categories', methods=['POST'])
@login_required
@product_manager_required
@csrf.exempt
def create_category_api():
    """创建产品分类"""
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        code_letter = data.get('code_letter', '').strip().upper()
        description = data.get('description', '').strip()

        # 验证必填字段
        if not name:
            return jsonify({'success': False, 'message': '分类名称是必填项'}), 400

        if not code_letter:
            return jsonify({'success': False, 'message': '标识符是必填项'}), 400

        # 验证标识符长度
        if len(code_letter) != 1:
            return jsonify({'success': False, 'message': '标识符必须是单个字符'}), 400

        # 验证标识符类型（必须是大写字母A-Z）
        if not code_letter.isalpha() or not code_letter.isupper():
            return jsonify({'success': False, 'message': '标识符必须是大写字母A-Z'}), 400

        # 检查标识符是否已被使用
        existing = ProductCategory.query.filter_by(code_letter=code_letter).first()
        if existing:
            return jsonify({'success': False, 'message': f'标识符 {code_letter} 已被使用'}), 400

        # 计算display_order
        max_order = db.session.query(db.func.max(ProductCategory.display_order)).scalar() or 0

        # 创建分类
        category = ProductCategory(
            name=name,
            code_letter=code_letter,
            description=description,
            display_order=max_order + 1
        )
        db.session.add(category)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '产品分类创建成功',
            'data': {
                'id': category.id,
                'name': category.name,
                'code_letter': category.code_letter,
                'display_order': category.display_order
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'创建失败: {str(e)}'}), 500


@product_code_bp.route('/api/categories/<int:category_id>', methods=['GET'])
@login_required
@product_manager_required
@csrf.exempt
def get_category_api(category_id):
    """获取单个产品分类（编辑时使用）"""
    try:
        category = ProductCategory.query.get_or_404(category_id)

        return jsonify({
            'success': True,
            'data': {
                'id': category.id,
                'name': category.name,
                'code_letter': category.code_letter,
                'description': category.description or ''
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'加载失败: {str(e)}'}), 500


@product_code_bp.route('/api/categories/<int:category_id>', methods=['PUT'])
@login_required
@product_manager_required
@csrf.exempt
def update_category_api(category_id):
    """更新产品分类"""
    try:
        category = ProductCategory.query.get_or_404(category_id)

        data = request.get_json()
        name = data.get('name', '').strip()
        code_letter = data.get('code_letter', '').strip().upper()
        description = data.get('description', '').strip()

        # 验证必填字段
        if not name:
            return jsonify({'success': False, 'message': '分类名称是必填项'}), 400

        if not code_letter:
            return jsonify({'success': False, 'message': '标识符是必填项'}), 400

        # 验证标识符长度
        if len(code_letter) != 1:
            return jsonify({'success': False, 'message': '标识符必须是单个字符'}), 400

        # 验证标识符类型（必须是大写字母A-Z）
        if not code_letter.isalpha() or not code_letter.isupper():
            return jsonify({'success': False, 'message': '标识符必须是大写字母A-Z'}), 400

        # 检查标识符是否已被使用（排除当前分类）
        if code_letter != category.code_letter:
            existing = ProductCategory.query.filter_by(code_letter=code_letter).first()
            if existing:
                return jsonify({'success': False, 'message': f'标识符 {code_letter} 已被使用'}), 400

        # 更新分类
        category.name = name
        category.code_letter = code_letter
        category.description = description
        db.session.commit()

        return jsonify({'success': True, 'message': '产品分类更新成功'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'}), 500


@product_code_bp.route('/api/categories/<int:category_id>', methods=['DELETE'])
@login_required
@product_manager_required
@csrf.exempt
def delete_category_api(category_id):
    """删除产品分类"""
    try:
        category = ProductCategory.query.get_or_404(category_id)

        # 检查是否有子分类使用此分类
        subcategories_count = ProductSubcategory.query.filter_by(category_id=category_id).count()
        if subcategories_count > 0:
            return jsonify({
                'success': False,
                'message': f'无法删除：有 {subcategories_count} 个子分类使用此分类'
            }), 400

        # 删除分类
        db.session.delete(category)
        db.session.commit()

        return jsonify({'success': True, 'message': '产品分类删除成功'})

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'}), 500


@product_code_bp.route('/api/generate-category-code', methods=['GET'])
@login_required
@product_manager_required
@csrf.exempt
def generate_category_code_api():
    """生成可用的分类标识符"""
    try:
        import random
        import string

        # 获取已使用的标识符
        used_letters = [c.code_letter for c in ProductCategory.query.all()]

        # A-Z 字母
        all_letters = list(string.ascii_uppercase)

        # 找到未使用的标识符
        available_letters = [l for l in all_letters if l not in used_letters]

        if not available_letters:
            return jsonify({
                'success': False,
                'message': '所有可用标识符已用完'
            }), 400

        # 随机选择一个
        code = random.choice(available_letters)

        return jsonify({
            'success': True,
            'code': code
        })

    except Exception as e:
        return jsonify({'success': False, 'message': f'生成失败: {str(e)}'}), 500


# ============================================================================
# 子分类（产品名称）管理 API
# ============================================================================

@product_code_bp.route('/api/subcategories', methods=['POST'])
@login_required
@product_manager_required
@csrf.exempt
def create_subcategory_api():
    """
    创建产品名称（子分类）

    Request Body:
        {
            "category_id": int,
            "name": str,
            "code_letter": str
        }

    Returns:
        JSON: {success, message, data}
    """
    try:
        data = request.get_json()

        category_id = data.get('category_id')
        name = data.get('name', '').strip()
        code_letter = data.get('code_letter', '').strip().upper()

        # 验证必填字段
        if not category_id or not name or not code_letter:
            return jsonify({
                'success': False,
                'message': '分类ID、产品名称和标识符不能为空'
            }), 400

        # 验证分类是否存在
        category = ProductCategory.query.get(category_id)
        if not category:
            return jsonify({
                'success': False,
                'message': '分类不存在'
            }), 404

        # 验证标识符长度
        if len(code_letter) != 1:
            return jsonify({
                'success': False,
                'message': '标识符必须是单个字符'
            }), 400

        # 验证标识符字符类型
        if not (code_letter.isalpha() or code_letter.isdigit()):
            return jsonify({
                'success': False,
                'message': '标识符必须是字母（A-Z）或数字（1-9）'
            }), 400

        # 检查标识符是否已被使用
        existing = ProductSubcategory.query.filter_by(
            category_id=category_id,
            code_letter=code_letter
        ).first()

        if existing:
            return jsonify({
                'success': False,
                'message': f'标识符 {code_letter} 已在此分类下使用'
            }), 400

        # 计算 display_order
        max_order = db.session.query(db.func.max(ProductSubcategory.display_order))\
            .filter_by(category_id=category_id).scalar() or 0

        # 创建子分类
        new_subcategory = ProductSubcategory(
            category_id=category_id,
            name=name,
            code_letter=code_letter,
            description='',  # 用户要求不需要描述
            display_order=max_order + 1
        )

        db.session.add(new_subcategory)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '产品名称创建成功',
            'data': {
                'id': new_subcategory.id,
                'name': new_subcategory.name,
                'code_letter': new_subcategory.code_letter,
                'display_order': new_subcategory.display_order
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'创建子分类失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'创建失败: {str(e)}'
        }), 500


@product_code_bp.route('/api/subcategories/<int:subcategory_id>', methods=['GET'])
@login_required
@product_manager_required
@csrf.exempt
def get_subcategory_api(subcategory_id):
    """
    获取单个子分类详情

    Args:
        subcategory_id: 子分类ID

    Returns:
        JSON: {success, data}
    """
    try:
        subcategory = ProductSubcategory.query.get(subcategory_id)

        if not subcategory:
            return jsonify({
                'success': False,
                'message': '产品名称不存在'
            }), 404

        return jsonify({
            'success': True,
            'data': {
                'id': subcategory.id,
                'name': subcategory.name,
                'code_letter': subcategory.code_letter,
                'category_id': subcategory.category_id
            }
        })

    except Exception as e:
        current_app.logger.error(f'获取子分类失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@product_code_bp.route('/api/subcategories/<int:subcategory_id>', methods=['PUT'])
@login_required
@product_manager_required
@csrf.exempt
def update_subcategory_api(subcategory_id):
    """
    更新产品名称

    Args:
        subcategory_id: 子分类ID

    Request Body:
        {
            "name": str,
            "code_letter": str
        }

    Returns:
        JSON: {success, message}
    """
    try:
        subcategory = ProductSubcategory.query.get(subcategory_id)

        if not subcategory:
            return jsonify({
                'success': False,
                'message': '产品名称不存在'
            }), 404

        # 检查是否被使用（与列表页相同的逻辑）
        used_in_dev_by_subcategory = db.session.execute(
            text("SELECT 1 FROM dev_products WHERE subcategory_id = :id LIMIT 1"),
            {"id": subcategory_id}
        ).first() is not None

        pattern = f"{subcategory.parent_category.code_letter}{subcategory.code_letter}%"
        used_in_dev_by_code = db.session.execute(
            text("SELECT 1 FROM dev_products WHERE mn_code LIKE :pattern LIMIT 1"),
            {"pattern": pattern}
        ).first() is not None

        if used_in_dev_by_subcategory or used_in_dev_by_code:
            return jsonify({
                'success': False,
                'message': '此产品名称已被使用，无法修改'
            }), 400

        data = request.get_json()
        name = data.get('name', '').strip()
        code_letter = data.get('code_letter', '').strip().upper()

        # 验证
        if not name or not code_letter:
            return jsonify({
                'success': False,
                'message': '产品名称和标识符不能为空'
            }), 400

        if len(code_letter) != 1:
            return jsonify({
                'success': False,
                'message': '标识符必须是单个字符'
            }), 400

        if not (code_letter.isalpha() or code_letter.isdigit()):
            return jsonify({
                'success': False,
                'message': '标识符必须是字母（A-Z）或数字（1-9）'
            }), 400

        # 检查标识符唯一性（排除自己）
        existing = ProductSubcategory.query.filter(
            ProductSubcategory.category_id == subcategory.category_id,
            ProductSubcategory.code_letter == code_letter,
            ProductSubcategory.id != subcategory_id
        ).first()

        if existing:
            return jsonify({
                'success': False,
                'message': f'标识符 {code_letter} 已在此分类下使用'
            }), 400

        # 更新
        subcategory.name = name
        subcategory.code_letter = code_letter
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '产品名称更新成功'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'更新子分类失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500


@product_code_bp.route('/api/subcategories/<int:subcategory_id>', methods=['DELETE'])
@login_required
@product_manager_required
@csrf.exempt
def delete_subcategory_api(subcategory_id):
    """
    删除产品名称

    Args:
        subcategory_id: 子分类ID

    Returns:
        JSON: {success, message}
    """
    try:
        subcategory = ProductSubcategory.query.get(subcategory_id)

        if not subcategory:
            return jsonify({
                'success': False,
                'message': '产品名称不存在'
            }), 404

        # 检查是否被使用
        used_in_dev_by_subcategory = db.session.execute(
            text("SELECT 1 FROM dev_products WHERE subcategory_id = :id LIMIT 1"),
            {"id": subcategory_id}
        ).first() is not None

        pattern = f"{subcategory.parent_category.code_letter}{subcategory.code_letter}%"
        used_in_dev_by_code = db.session.execute(
            text("SELECT 1 FROM dev_products WHERE mn_code LIKE :pattern LIMIT 1"),
            {"pattern": pattern}
        ).first() is not None

        if used_in_dev_by_subcategory or used_in_dev_by_code:
            return jsonify({
                'success': False,
                'message': '此产品名称已被使用，无法删除'
            }), 400

        # 删除
        db.session.delete(subcategory)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '产品名称删除成功'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'删除子分类失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500


# ============================================================================
# 分类级通用编码字段 API
# ============================================================================

@product_code_bp.route('/api/category-fields/available-specs/<int:category_id>', methods=['GET'])
@login_required
@product_manager_required
@csrf.exempt
def get_category_available_specs(category_id):
    """
    获取分类级可用规格列表（从规格字典中过滤已使用的）

    Args:
        category_id: 分类ID
        exclude_field_id: 排除的字段ID（编辑时使用）

    Returns:
        JSON: {success, data: [{id, name, unit}]}
    """
    try:
        exclude_field_id = request.args.get('exclude_field_id', type=int)

        # 获取所有启用的规格字典条目
        all_specs = SpecificationDictionary.query.filter_by(is_active=True).all()

        # 获取当前分类已使用的规格名称（排除正在编辑的字段）
        used_specs_query = ProductCodeField.query.filter_by(
            category_id=category_id,
            subcategory_id=None,
            field_type='spec'
        )

        if exclude_field_id:
            used_specs_query = used_specs_query.filter(ProductCodeField.id != exclude_field_id)

        used_spec_names = {field.name for field in used_specs_query.all()}

        # 过滤出可用的规格
        available_specs = [
            {
                'id': spec.id,
                'name': spec.name,
                'unit': spec.unit
            }
            for spec in all_specs
            if spec.name not in used_spec_names
        ]

        return jsonify({
            'success': True,
            'data': available_specs
        })

    except Exception as e:
        current_app.logger.error(f'获取分类级可用规格失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'获取可用规格失败: {str(e)}'
        }), 500


@product_code_bp.route('/api/category-fields/<int:field_id>', methods=['GET'])
@login_required
@product_manager_required
@csrf.exempt
def get_category_field(field_id):
    """获取分类级字段详情（用于编辑）"""
    try:
        field = ProductCodeField.query.get_or_404(field_id)

        # 验证是分类级字段
        if field.category_id is None or field.subcategory_id is not None:
            return jsonify({
                'success': False,
                'message': '该字段不是分类级字段'
            }), 400

        return jsonify({
            'success': True,
            'data': {
                'id': field.id,
                'name': field.name,
                'is_required': field.is_required,
                'use_in_code': field.use_in_code,
                'position': field.position
            }
        })

    except Exception as e:
        current_app.logger.error(f'获取分类级字段详情失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'获取字段失败: {str(e)}'
        }), 500


@product_code_bp.route('/api/category-fields', methods=['POST'])
@login_required
@product_manager_required
@csrf.exempt
def create_category_field():
    """
    创建分类级通用编码字段

    Request Body:
        {
            "category_id": int,
            "name": str,
            "position": int,
            "is_required": bool,
            "use_in_code": bool
        }
    """
    try:
        data = request.get_json()

        category_id = data.get('category_id')
        name = data.get('name', '').strip()
        position = data.get('position')
        is_required = data.get('is_required', True)
        use_in_code = data.get('use_in_code', True)

        if not category_id or not name:
            return jsonify({
                'success': False,
                'message': '分类ID和规格名称不能为空'
            }), 400

        # 验证分类是否存在
        category = ProductCategory.query.get(category_id)
        if not category:
            return jsonify({
                'success': False,
                'message': '分类不存在'
            }), 404

        # 检查规格名称是否已存在于当前分类
        existing_field = ProductCodeField.query.filter_by(
            category_id=category_id,
            subcategory_id=None,
            name=name
        ).first()

        if existing_field:
            return jsonify({
                'success': False,
                'message': f'通用规格"{name}"已存在于当前分类中'
            }), 400

        # 如果没有指定位置，计算新位置
        if position is None:
            max_position = db.session.query(db.func.max(ProductCodeField.position))\
                .filter_by(category_id=category_id, subcategory_id=None).scalar()
            position = 4 if max_position is None else max_position + 1

        # 创建新字段
        new_field = ProductCodeField(
            category_id=category_id,
            subcategory_id=None,
            name=name,
            field_type='spec',
            position=position,
            max_length=1,
            is_required=is_required,
            use_in_code=use_in_code
        )

        db.session.add(new_field)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '通用规格创建成功',
            'data': {
                'id': new_field.id,
                'name': new_field.name,
                'position': new_field.position,
                'is_required': new_field.is_required,
                'use_in_code': new_field.use_in_code
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'创建分类级字段失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'创建失败: {str(e)}'
        }), 500


@product_code_bp.route('/api/category-fields/<int:field_id>', methods=['PUT'])
@login_required
@product_manager_required
@csrf.exempt
def update_category_field(field_id):
    """更新分类级通用编码字段"""
    try:
        field = ProductCodeField.query.get_or_404(field_id)

        # 验证是分类级字段
        if not field.is_category_level:
            return jsonify({
                'success': False,
                'message': '该字段不是分类级字段'
            }), 400

        data = request.get_json()

        if 'name' in data:
            field.name = data['name'].strip()
        if 'position' in data:
            field.position = data['position']
        if 'is_required' in data:
            field.is_required = data['is_required']
        if 'use_in_code' in data:
            field.use_in_code = data['use_in_code']

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '通用规格更新成功',
            'data': {
                'id': field.id,
                'name': field.name,
                'position': field.position,
                'is_required': field.is_required,
                'use_in_code': field.use_in_code
            }
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'更新分类级字段失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'更新失败: {str(e)}'
        }), 500


@product_code_bp.route('/api/category-fields/<int:field_id>', methods=['DELETE'])
@login_required
@product_manager_required
@csrf.exempt
def delete_category_field(field_id):
    """删除分类级通用编码字段"""
    try:
        field = ProductCodeField.query.get_or_404(field_id)

        # 验证是分类级字段
        if not field.is_category_level:
            return jsonify({
                'success': False,
                'message': '该字段不是分类级字段'
            }), 400

        # 检查是否被使用
        used_count = db.session.execute(
            text("""
                SELECT COUNT(*) FROM dev_product_specs dps
                INNER JOIN dev_products dp ON dps.dev_product_id = dp.id
                INNER JOIN product_subcategories ps ON dp.subcategory_id = ps.id
                WHERE dps.field_name = :field_name
                AND ps.category_id = :category_id
            """),
            {"field_name": field.name, "category_id": field.category_id}
        ).scalar() or 0

        if used_count > 0:
            return jsonify({
                'success': False,
                'message': f'该通用规格已被 {used_count} 个产品使用，无法删除'
            }), 400

        db.session.delete(field)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '通用规格删除成功'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'删除分类级字段失败: {str(e)}')
        return jsonify({
            'success': False,
            'message': f'删除失败: {str(e)}'
        }), 500
