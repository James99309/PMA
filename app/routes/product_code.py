from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from app import db
from app.models.product_code import ProductCategory, ProductSubcategory, ProductCodeField, ProductCodeFieldOption, ProductCode, ProductCodeFieldValue
from app.models.product import Product
from app.permissions import admin_required, product_manager_required, permission_required
import json
import random
import string
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text, update, Integer, case
from datetime import datetime

# 创建蓝图
product_code_bp = Blueprint('product_code', __name__, url_prefix='/product-code')

# 管理员视图 - 产品分类管理
@product_code_bp.route('/categories', methods=['GET'])
@login_required
@admin_required
def categories():
    categories = ProductCategory.query.all()
    
    # 获取已使用的标识符列表
    used_identifiers = [category.code_letter for category in categories]
    
    # 可用字母池（A-Z大写字母）
    available_letters = [letter for letter in string.ascii_uppercase if letter not in used_identifiers]
    
    return render_template('product_code/categories.html', 
                           categories=categories,
                           used_letters=used_identifiers,
                           available_letters=available_letters)

def generate_unique_letter():
    """生成一个唯一的分类标识符（优先A-Z字母，然后0-9数字）"""
    # 获取已使用的标识符列表
    used_identifiers = [category.code_letter for category in ProductCategory.query.all()]
    
    # 可用字母池（A-Z大写字母）
    available_letters = [letter for letter in string.ascii_uppercase if letter not in used_identifiers]
    
    # 如果还有可用字母，选择首个未使用的字母
    if available_letters:
        available_letters.sort()  # 按字母顺序排序
        return available_letters[0]  # 返回第一个可用字母
    
    # 如果字母用完，检查数字0-9
    available_digits = [str(digit) for digit in range(10) if str(digit) not in used_identifiers]
    
    # 如果有可用数字，选择首个未使用的数字
    if available_digits:
        available_digits.sort()  # 按数字顺序排序
        return available_digits[0]  # 返回第一个可用数字
        
    # 所有可能的标识符都用完了
    return None

def generate_unique_subcategory_letter(category_id):
    """为特定分类下的子类生成唯一标识符"""
    # 获取该分类下已使用的子类标识符
    used_identifiers = [subcat.code_letter for subcat in ProductSubcategory.query.filter_by(category_id=category_id).all()]
    
    # 可用字母池（A-Z大写字母）
    available_letters = [letter for letter in string.ascii_uppercase if letter not in used_identifiers]
    
    # 如果还有可用字母，选择首个未使用的字母
    if available_letters:
        available_letters.sort()  # 按字母顺序排序
        return available_letters[0]  # 返回第一个可用字母
    
    # 如果字母用完，检查数字0-9
    available_digits = [str(digit) for digit in range(10) if str(digit) not in used_identifiers]
    
    # 如果有可用数字，选择首个未使用的数字
    if available_digits:
        available_digits.sort()  # 按数字顺序排序
        return available_digits[0]  # 返回第一个可用数字
        
    # 所有可能的标识符都用完了
    return None

@product_code_bp.route('/categories/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_category():
    # 获取已使用的标识符列表
    used_identifiers = [category.code_letter for category in ProductCategory.query.all()]
    
    if request.method == 'POST':
        name = request.form.get('name')
        code_letter = request.form.get('code_letter', '').strip().upper()  # 获取用户输入的标识符并转为大写
        description = request.form.get('description', '')
        
        if not name:
            flash('分类名称是必填项', 'danger')
            return render_template('product_code/new_category.html', 
                                  used_letters=used_identifiers,
                                  name=name, 
                                  code_letter=code_letter, 
                                  description=description)
        
        if not code_letter:
            flash('分类标识符是必填项', 'danger')
            return render_template('product_code/new_category.html', 
                                  used_letters=used_identifiers,
                                  name=name, 
                                  description=description)
        
        # 验证标识符是否为单个字符
        if len(code_letter) != 1:
            flash('分类标识符必须是单个字符', 'danger')
            return render_template('product_code/new_category.html', 
                                  used_letters=used_identifiers,
                                  name=name, 
                                  description=description)
        
        # 验证标识符是否合法（A-Z字母或0-9数字）
        if not (code_letter.isalpha() or code_letter.isdigit()):
            flash('分类标识符必须是A-Z字母或0-9数字', 'danger')
            return render_template('product_code/new_category.html', 
                                  used_letters=used_identifiers,
                                  name=name, 
                                  description=description)
            
        # 检查标识符是否已被使用
        if code_letter in used_identifiers:
            flash(f'标识符 {code_letter} 已被使用，请选择其他标识符', 'danger')
            return render_template('product_code/new_category.html', 
                                  used_letters=used_identifiers,
                                  name=name, 
                                  description=description)
        
        category = ProductCategory(name=name, code_letter=code_letter, description=description)
        db.session.add(category)
        
        try:
            db.session.commit()
            flash(f'产品分类创建成功，标识符为：{code_letter}', 'success')
            return redirect(url_for('product_code.categories'))
        except IntegrityError:
            db.session.rollback()
            flash('创建分类失败，可能存在命名冲突', 'danger')
    
    # 获取可用字母池（A-Z大写字母）
    available_letters = [letter for letter in string.ascii_uppercase if letter not in used_identifiers]
    
    return render_template('product_code/new_category.html', 
                          used_letters=used_identifiers,
                          available_letters=available_letters)

@product_code_bp.route('/categories/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_category(id):
    category = ProductCategory.query.get_or_404(id)
    # 获取所有已使用的标识符（除了当前分类的标识符）
    used_identifiers = [cat.code_letter for cat in ProductCategory.query.filter(ProductCategory.id != id).all()]
    
    if request.method == 'POST':
        # 打印表单数据以进行调试
        print("表单数据:", request.form)
        
        # 获取表单数据
        name = request.form.get('name')
        code_letter = request.form.get('code_letter', '').strip().upper()  # 获取用户输入的标识符并转为大写
        description = request.form.get('description', '')
        
        # 打印取到的值进行调试
        print(f"处理后的值: name={name}, code_letter={code_letter}, description={description}")
        
        if not name:
            flash('分类名称是必填项', 'danger')
            return render_template('product_code/edit_category.html', 
                                  category=category,
                                  used_letters=used_identifiers)
            
        if not code_letter:
            flash('分类标识符是必填项', 'danger')
            return render_template('product_code/edit_category.html', 
                                  category=category,
                                  used_letters=used_identifiers)
            
        # 验证标识符是否为单个字符
        if len(code_letter) != 1:
            flash('分类标识符必须是单个字符', 'danger')
            return render_template('product_code/edit_category.html', 
                                  category=category,
                                  used_letters=used_identifiers)
            
        # 验证标识符是否合法（A-Z字母或0-9数字）
        if not (code_letter.isalpha() or code_letter.isdigit()):
            flash('分类标识符必须是A-Z字母或0-9数字', 'danger')
            return render_template('product_code/edit_category.html', 
                                  category=category,
                                  used_letters=used_identifiers)
            
        # 如果标识符已更改，检查是否已被使用
        if code_letter != category.code_letter and code_letter in used_identifiers:
            flash(f'标识符 {code_letter} 已被使用，请选择其他标识符', 'danger')
            return render_template('product_code/edit_category.html', 
                                  category=category,
                                  used_letters=used_identifiers)
        
        # 更新分类数据
        category.name = name
        category.description = description
        category.code_letter = code_letter
        
        # 打印更新后的值进行调试
        print(f"更新后的分类: name={category.name}, code_letter={category.code_letter}, description={category.description}")
        
        try:
            db.session.commit()
            # 提交后再次检查
            db.session.refresh(category)
            print(f"提交后的分类: id={category.id}, name={category.name}, code_letter={category.code_letter}")
            flash('产品分类更新成功', 'success')
            return redirect(url_for('product_code.categories'))
        except IntegrityError as e:
            db.session.rollback()
            print(f"数据库错误: {str(e)}")
            flash(f'更新分类失败: {str(e)}', 'danger')
    
    return render_template('product_code/edit_category.html', 
                          category=category,
                          used_letters=used_identifiers)

@product_code_bp.route('/categories/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_category(id):
    category = ProductCategory.query.get_or_404(id)
    
    # 检查是否有产品编码使用此分类（通过ProductCode表而不是直接查询Product表）
    product_codes_count = ProductCode.query.filter_by(category_id=id).count()
    if product_codes_count > 0:
        flash(f'无法删除：有 {product_codes_count} 个产品编码使用此分类', 'danger')
        return redirect(url_for('product_code.categories'))
    
    # 检查是否有子类
    subcategories_count = ProductSubcategory.query.filter_by(category_id=id).count()
    if subcategories_count > 0:
        flash(f'无法删除：此分类下有 {subcategories_count} 个子类', 'danger')
        return redirect(url_for('product_code.categories'))
    
    # 删除分类
    db.session.delete(category)
    db.session.commit()
    
    flash('产品分类已删除', 'success')
    return redirect(url_for('product_code.categories'))

# 管理员视图 - 子类管理
@product_code_bp.route('/categories/<int:id>/subcategories', methods=['GET'])
@login_required
@admin_required
def category_subcategories(id):
    category = ProductCategory.query.get_or_404(id)
    # 按display_order字段排序
    subcategories = ProductSubcategory.query.filter_by(category_id=id).order_by(ProductSubcategory.display_order).all()
    return render_template('product_code/subcategories.html',
                           category=category,
                           subcategories=subcategories)

@product_code_bp.route('/categories/<int:id>/subcategories/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_subcategory(id):
    category = ProductCategory.query.get_or_404(id)
    
    # 获取当前分类下已使用的标识符
    used_subcategories = ProductSubcategory.query.filter_by(category_id=id).all()
    used_identifiers = [subcat.code_letter for subcat in used_subcategories]
    
    # 初始化空表单数据
    form_data = {'name': '', 'description': '', 'code_letter': ''}
    
    if request.method == 'POST':
        name = request.form.get('name')
        code_letter = request.form.get('code_letter', '').strip().upper()  # 获取用户输入的标识符并转为大写
        description = request.form.get('description', '')
        
        form_data = {'name': name, 'description': description, 'code_letter': code_letter}
        
        if not name:
            flash('产品名称是必填项', 'danger')
            return render_template('product_code/new_subcategory.html', 
                                   category=category, 
                                   form=form_data,
                                   used_subcategories=used_subcategories)
            
        if not code_letter:
            flash('标识符是必填项', 'danger')
            return render_template('product_code/new_subcategory.html', 
                                   category=category, 
                                   form=form_data,
                                   used_subcategories=used_subcategories)
            
        # 验证标识符是否为单个字符
        if len(code_letter) != 1:
            flash('标识符必须是单个字符', 'danger')
            return render_template('product_code/new_subcategory.html', 
                                   category=category, 
                                   form=form_data,
                                   used_subcategories=used_subcategories)
            
        # 验证标识符是否合法（A-Z字母或0-9数字）
        if not (code_letter.isalpha() or code_letter.isdigit()):
            flash('标识符必须是A-Z字母或0-9数字', 'danger')
            return render_template('product_code/new_subcategory.html', 
                                   category=category, 
                                   form=form_data,
                                   used_subcategories=used_subcategories)
            
        # 检查标识符是否已被使用
        if code_letter in used_identifiers:
            flash(f'标识符 {code_letter} 已在此分类下使用，请选择其他标识符', 'danger')
            return render_template('product_code/new_subcategory.html', 
                                   category=category, 
                                   form=form_data,
                                   used_subcategories=used_subcategories)
        
        # 计算新子类别的display_order - 获取当前分类下最大的display_order加1
        max_display_order = db.session.query(db.func.max(ProductSubcategory.display_order))\
            .filter_by(category_id=id).scalar() or 0
        new_display_order = max_display_order + 1
        
        subcategory = ProductSubcategory(
            category_id=id,
            name=name,
            code_letter=code_letter,
            description=description,
            display_order=new_display_order
        )
        db.session.add(subcategory)
        
        try:
            db.session.commit()
            flash(f'产品名称添加成功，标识符为：{code_letter}', 'success')
            return redirect(url_for('product_code.category_subcategories', id=id))
        except IntegrityError as e:
            db.session.rollback()
            flash(f'添加产品名称失败: {str(e)}', 'danger')
    
    return render_template('product_code/new_subcategory.html', 
                           category=category, 
                           form=form_data,
                           used_subcategories=used_subcategories)

@product_code_bp.route('/subcategories/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_subcategory(id):
    subcategory = ProductSubcategory.query.get_or_404(id)
    
    # 获取当前分类下已使用的标识符（除了当前子分类的标识符）
    used_identifiers = [subcat.code_letter for subcat in 
                         ProductSubcategory.query.filter(
                             ProductSubcategory.category_id == subcategory.category_id, 
                             ProductSubcategory.id != id
                         ).all()]
    
    if request.method == 'POST':
        # 打印表单数据以进行调试
        print("子分类表单数据:", request.form)
        
        # 获取表单数据
        name = request.form.get('name')
        code_letter = request.form.get('code_letter', '').strip().upper()  # 获取用户输入的标识符并转为大写
        description = request.form.get('description', '')
        
        # 打印取到的值进行调试
        print(f"子分类处理后的值: name={name}, code_letter={code_letter}, description={description}")
        
        if not name:
            flash('产品名称是必填项', 'danger')
            return render_template('product_code/edit_subcategory.html', 
                                  subcategory=subcategory,
                                  used_identifiers=used_identifiers)
            
        if not code_letter:
            flash('标识符是必填项', 'danger')
            return render_template('product_code/edit_subcategory.html', 
                                  subcategory=subcategory,
                                  used_identifiers=used_identifiers)
            
        # 验证标识符是否为单个字符
        if len(code_letter) != 1:
            flash('标识符必须是单个字符', 'danger')
            return render_template('product_code/edit_subcategory.html', 
                                  subcategory=subcategory,
                                  used_identifiers=used_identifiers)
            
        # 验证标识符是否合法（A-Z字母或0-9数字）
        if not (code_letter.isalpha() or code_letter.isdigit()):
            flash('标识符必须是A-Z字母或0-9数字', 'danger')
            return render_template('product_code/edit_subcategory.html', 
                                  subcategory=subcategory,
                                  used_identifiers=used_identifiers)
            
        # 如果标识符已更改，检查是否已被使用
        if code_letter != subcategory.code_letter and code_letter in used_identifiers:
            flash(f'标识符 {code_letter} 已在此分类下使用，请选择其他标识符', 'danger')
            return render_template('product_code/edit_subcategory.html', 
                                  subcategory=subcategory,
                                  used_identifiers=used_identifiers)
        
        # 更新子分类数据
        subcategory.name = name
        subcategory.description = description
        subcategory.code_letter = code_letter
        
        # 打印更新后的值进行调试
        print(f"更新后的子分类: name={subcategory.name}, code_letter={subcategory.code_letter}")
        
        try:
            db.session.commit()
            # 提交后再次检查
            db.session.refresh(subcategory)
            print(f"提交后的子分类: id={subcategory.id}, name={subcategory.name}, code_letter={subcategory.code_letter}")
            flash('产品名称更新成功', 'success')
            return redirect(url_for('product_code.category_subcategories', id=subcategory.category_id))
        except IntegrityError as e:
            db.session.rollback()
            print(f"子分类数据库错误: {str(e)}")
            flash(f'更新产品名称失败: {str(e)}', 'danger')
    
    return render_template('product_code/edit_subcategory.html', 
                          subcategory=subcategory,
                          used_identifiers=used_identifiers)

@product_code_bp.route('/subcategories/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_subcategory(id):
    subcategory = ProductSubcategory.query.get_or_404(id)
    category_id = subcategory.category_id
    
    # 检查是否有产品编码使用此产品名称
    product_codes_count = ProductCode.query.filter_by(subcategory_id=id).count()
    if product_codes_count > 0:
        flash(f'无法删除：有 {product_codes_count} 个产品编码使用此产品名称', 'danger')
        return redirect(url_for('product_code.category_subcategories', id=category_id))
    
    # 检查是否有字段关联此产品名称
    fields_count = ProductCodeField.query.filter_by(subcategory_id=id).count()
    if fields_count > 0:
        flash(f'无法删除：有 {fields_count} 个字段关联此产品名称', 'danger')
        return redirect(url_for('product_code.category_subcategories', id=category_id))
    
    # 删除产品名称
    db.session.delete(subcategory)
    db.session.commit()
    
    flash('产品名称已删除', 'success')
    return redirect(url_for('product_code.category_subcategories', id=category_id))

# 管理员视图 - 编码字段管理
@product_code_bp.route('/subcategories/<int:id>/fields', methods=['GET'])
@login_required
@admin_required
def subcategory_fields(id):
    subcategory = ProductSubcategory.query.get_or_404(id)
    
    # 使用正确的字段名查询，只获取类型为 'spec' 的字段
    fields = ProductCodeField.query.filter_by(subcategory_id=id, field_type='spec').order_by(ProductCodeField.position).all()
    
    # 如果没有找到字段，可能是旧版数据库结构，尝试使用category_id
    if not fields:
        # 使用原始SQL查询，兼容旧版数据库结构，并添加 field_type 条件
        sql = text("SELECT * FROM product_code_fields WHERE subcategory_id = :subcategory_id AND field_type = 'spec' ORDER BY position")
        result = db.session.execute(sql, {"subcategory_id": id})
        fields = [dict(row) for row in result]
    
    return render_template('product_code/fields.html', subcategory=subcategory, fields=fields)

@product_code_bp.route('/subcategories/<int:id>/fields/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_field(id):
    try:
        subcategory = ProductSubcategory.query.get_or_404(id)
        
        # 计算已经用于编码的字段数量
        active_code_fields_count = ProductCodeField.query.filter_by(
            subcategory_id=id, 
            use_in_code=True
        ).count()
        
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            is_required = 'is_required' in request.form
            use_in_code = 'use_in_code' in request.form
            
            # 自动计算 position 值 - 获取当前子类下最大的 position 值并加1
            max_position = db.session.query(db.func.max(ProductCodeField.position))\
                .filter_by(subcategory_id=id).scalar() or 0
            new_position = max_position + 1
            
            # 默认最大长度为1，可根据需求调整
            max_length = 1
            
            field = ProductCodeField(
                subcategory_id=id,
                name=name,
                field_type='spec',  # 固定设置为'spec'类型
                description=description,
                position=new_position,
                max_length=max_length,
                is_required=is_required,
                use_in_code=use_in_code
            )
            db.session.add(field)
            
            try:
                db.session.commit()
                flash('规格创建成功', 'success')
                return redirect(url_for('product_code.subcategory_fields', id=id))
            except Exception as e:
                db.session.rollback()
                flash(f'创建规格失败: {str(e)}', 'danger')
            
        return render_template('product_code/new_field.html', subcategory=subcategory, active_code_fields_count=active_code_fields_count)
    except Exception as e:
        flash(f'添加规格时发生错误: {str(e)}', 'danger')
        return redirect(url_for('product_code.categories'))

@product_code_bp.route('/fields/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_field(id):
    try:
        field = ProductCodeField.query.get_or_404(id)
        
        # 确保只能编辑 spec 类型的字段
        if field.field_type != 'spec':
            flash('只能编辑产品规格字段', 'danger')
            return redirect(url_for('product_code.subcategory_fields', id=field.subcategory_id))
        
        # 计算已经用于编码的字段数量（不包括当前字段）
        active_code_fields_count = ProductCodeField.query.filter(
            ProductCodeField.subcategory_id == field.subcategory_id,
            ProductCodeField.use_in_code == True,
            ProductCodeField.id != id
        ).count()
        
        if request.method == 'POST':
            name = request.form.get('name')
            description = request.form.get('description')
            is_required = 'is_required' in request.form
            use_in_code = 'use_in_code' in request.form
            
            # 不修改 position，保持原有的位置值
            # 不修改 max_length，保持原有的长度值
            # 不修改 field_type，保持为 'spec'
            
            field.name = name
            field.description = description
            field.is_required = is_required
            field.use_in_code = use_in_code
            
            try:
                db.session.commit()
                flash('规格更新成功', 'success')
                return redirect(url_for('product_code.subcategory_fields', id=field.subcategory_id))
            except Exception as e:
                db.session.rollback()
                flash(f'更新规格失败: {str(e)}', 'danger')
            
        return render_template('product_code/edit_field.html', field=field, active_code_fields_count=active_code_fields_count)
    except Exception as e:
        flash(f'编辑规格时发生错误: {str(e)}', 'danger')
        return redirect(url_for('product_code.categories'))

@product_code_bp.route('/fields/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_field(id):
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

@product_code_bp.route('/fields/<int:id>/options', methods=['GET'])
@login_required
@admin_required
def field_options(id):
    """字段指标管理"""
    field = ProductCodeField.query.get_or_404(id)
    
    # 对于产地区字段，直接重定向回字段管理页面
    if field.field_type == 'origin_location':
        flash('产地区字段不再使用指标管理功能', 'info')
        return redirect(url_for('product_code.origin_fields'))
    
    options = ProductCodeFieldOption.query.filter_by(field_id=id).all()
    return render_template('product_code/field_options.html', field=field, options=options)

@product_code_bp.route('/options/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_option(id):
    option = ProductCodeFieldOption.query.get_or_404(id)
    field_id = option.field_id
    
    # 检查是否有产品编码使用此指标
    if ProductCodeFieldValue.query.filter_by(option_id=id).first():
        flash('无法删除此指标，因为已有产品编码使用此指标', 'danger')
        return redirect(url_for('product_code.field_options', id=field_id))
    
    # 删除指标
    db.session.delete(option)
    db.session.commit()
    
    flash('指标删除成功', 'success')
    return redirect(url_for('product_code.field_options', id=field_id))

@product_code_bp.route('/fields/<int:id>/options/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_option(id):
    field = ProductCodeField.query.get_or_404(id)
    
    if request.method == 'POST':
        value = request.form.get('value')
        description = request.form.get('description')
        
        # 自动生成唯一指标编码
        # 获取该字段下所有已使用的编码
        used_codes = db.session.query(ProductCodeFieldOption.code).filter_by(field_id=id).all()
        used_codes = [code[0] for code in used_codes if code[0] is not None]
        
        # 可用字母池
        available_letters = [letter for letter in string.ascii_uppercase if letter not in used_codes]
        
        # 如果字母用完，使用数字
        if not available_letters:
            available_letters = [str(digit) for digit in range(10) if str(digit) not in used_codes]
        
        # 如果还有可用字符，随机选择一个
        code = random.choice(available_letters) if available_letters else None
        
        if not code:
            flash('无法生成唯一编码，已达到最大指标数量限制', 'danger')
            return render_template('product_code/new_option.html', field=field)
        
        option = ProductCodeFieldOption(
            field_id=id,
            value=value,
            code=code,
            description=description,
            is_active=True  # 默认为活跃状态
        )
        db.session.add(option)
        db.session.commit()
        flash('指标创建成功', 'success')
        return redirect(url_for('product_code.field_options', id=id))
        
    return render_template('product_code/new_option.html', field=field)

@product_code_bp.route('/options/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_option(id):
    option = ProductCodeFieldOption.query.get_or_404(id)
    field = option.field
    
    if request.method == 'POST':
        value = request.form.get('value')
        description = request.form.get('description')
        
        # 不允许修改编码，保持原有的编码不变
        option.value = value
        option.description = description
        
        db.session.commit()
        flash('指标更新成功', 'success')
        return redirect(url_for('product_code.field_options', id=field.id))
        
    return render_template('product_code/edit_option.html', option=option, field=field)

# 产品经理视图 - 创建产品编码
@product_code_bp.route('/generator', methods=['GET'])
@login_required
@permission_required('product_code', 'create')
def generator():
    categories = ProductCategory.query.all()
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
    
    # 构建编码
    code_parts = [category.code_letter, subcategory.code_letter]
    
    # 获取产地区字段（通用字段）
    origin_fields = ProductCodeField.query.filter_by(field_type='origin_location').order_by(ProductCodeField.position).all()
    
    # 获取该子类的特定字段
    subcategory_fields = ProductCodeField.query.filter_by(subcategory_id=subcategory_id).order_by(ProductCodeField.position).all()
    
    # 合并所有字段
    all_fields = origin_fields + subcategory_fields
    
    # 按字段ID排序处理所有字段值
    for field_id_str, field_value in sorted(field_values.items(), key=lambda x: int(x[0])):
        field_id = int(field_id_str)
        if field_value:
            if isinstance(field_value, dict):  # 选项类型
                option_id = field_value.get('option_id')
                if option_id:
                    option = ProductCodeFieldOption.query.get(option_id)
                    if option:
                        code_parts.append(option.code)
            else:  # 自定义值类型
                code_parts.append(str(field_value))
    
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
    db.session.commit()
    
    return jsonify({'success': True, 'message': '产品编码创建成功', 'product_code_id': product_code.id})

# API - 获取现有产品列表
@product_code_bp.route('/api/products', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def api_products():
    search = request.args.get('search', '')
    products = Product.query.filter(
        Product.product_name.ilike(f'%{search}%') | 
        Product.model.ilike(f'%{search}%')
    ).limit(10).all()
    
    result = [
        {'id': p.id, 'name': p.product_name, 'model': p.model, 'current_mn': p.product_mn}
        for p in products
    ]
    
    return jsonify(result)

@product_code_bp.route('/api/generate-letter', methods=['GET'])
@login_required
@admin_required
def api_generate_letter():
    """API端点：生成随机唯一分类标识符"""
    letter = generate_unique_letter()
    return jsonify({'letter': letter})

@product_code_bp.route('/api/generate-subcategory-letter', methods=['GET'])
@login_required
@admin_required
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
@admin_required
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
        
        return render_template('product_code/origin_fields.html', fields=fields)
    except Exception as e:
        flash(f'获取销售区域时发生错误: {str(e)}', 'danger')
        return redirect(url_for('main.index'))

@product_code_bp.route('/origin-fields/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_origin_field():
    """添加新销售区域"""
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        
        # 确保有一个默认的子分类用于销售区域
        default_subcategory = ProductSubcategory.query.first()
        if not default_subcategory:
            flash('需要先创建至少一个产品分类和子分类', 'danger')
            return redirect(url_for('product_code.categories'))
        
        # 创建销售区域字段
        field = ProductCodeField(
            subcategory_id=default_subcategory.id,
            name=name,
            description=description,
            field_type='origin_location',
            position=1,  # 固定位置为1
            max_length=1,  # 固定长度为1
            is_required=True  # 固定为必填
        )
        db.session.add(field)
        
        try:
            db.session.commit()
            
            # 生成唯一编码
            all_options = ProductCodeFieldOption.query.filter(
                ProductCodeFieldOption.field_id.in_(
                    db.session.query(ProductCodeField.id).filter_by(field_type='origin_location')
                )
            ).all()
            used_codes = [opt.code for opt in all_options]
            
            # 生成唯一编码函数（简化版）
            def generate_unique_code(used_codes):
                for char in string.ascii_uppercase:
                    if char not in used_codes:
                        return char
                for num in range(1, 10):
                    code = str(num)
                    if code not in used_codes:
                        return code
                return None
            
            # 生成编码
            new_code = generate_unique_code(used_codes)
            
            # 创建选项并保存编码
            if new_code:
                option = ProductCodeFieldOption(
                    field_id=field.id,
                    value=name,
                    code=new_code,
                    description=f"自动生成的销售区域编码: {name}"
                )
                db.session.add(option)
                
                # 更新字段的编码
                field.code = new_code
                db.session.commit()
            
            flash('销售区域创建成功', 'success')
            return redirect(url_for('product_code.origin_fields'))
        except Exception as e:
            db.session.rollback()
            flash(f'创建销售区域失败: {str(e)}', 'danger')
        
    return render_template('product_code/new_origin_field.html')

@product_code_bp.route('/origin-fields/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
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
@admin_required
def delete_origin_field(id):
    """删除销售区域"""
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
@admin_required
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
@admin_required
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
        
        # 获取字段ID列表
        field_ids = data.get('field_ids', [])
        current_app.logger.info(f"字段ID列表: {field_ids}, 类型: {type(field_ids)}")
        
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
        
        valid_field_ids = []
        invalid_field_ids = []
        
        for field_id in field_ids:
            if field_id in existing_field_ids:
                valid_field_ids.append(field_id)
            else:
                invalid_field_ids.append(field_id)
        
        if invalid_field_ids:
            current_app.logger.warning(f"忽略无效字段ID: {invalid_field_ids}")
        
        if not valid_field_ids:
            current_app.logger.error("没有有效的字段ID")
            return jsonify({"success": False, "error": "没有有效的字段ID属于此子类别"}), 400
        
        # 更新位置值
        try:
            with db.session.begin_nested():  # 创建保存点
                for position, field_id in enumerate(valid_field_ids):
                    db.session.execute(
                        update(ProductCodeField)
                        .where(ProductCodeField.id == field_id)
                        .values(position=position)
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

@product_code_bp.route('/api/category/<int:id>/update-subcategories-order', methods=['POST'])
@login_required
@admin_required
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