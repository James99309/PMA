"""
规格字典管理路由

提供全局规格字典（SpecDefinition）的CRUD操作，
以及测试方法和测试条件字典的管理。
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_babel import _
from app import db
from app.models.spec_template import (
    SpecCategory, SpecDefinition, TestMethodDictionary, TestConditionDictionary,
    SPEC_CATEGORIES
)
from app.decorators import permission_required

spec_definition_bp = Blueprint('spec_definition', __name__, url_prefix='/admin/spec-definitions')


@spec_definition_bp.route('/')
@login_required
@permission_required('rd_product', 'view')
def list_definitions():
    """规格字典列表页"""
    categories = SpecCategory.query.filter_by(is_active=True).order_by(SpecCategory.display_order).all()

    # 获取当前选中的分类
    category_id = request.args.get('category_id', type=int)
    if not category_id and categories:
        category_id = categories[0].id

    # 获取该分类下的规格项
    definitions = []
    current_category = None
    if category_id:
        current_category = SpecCategory.query.get(category_id)
        definitions = SpecDefinition.query.filter_by(
            category_id=category_id,
            is_active=True
        ).order_by(SpecDefinition.display_order).all()

    # 获取测试方法和测试条件字典（用于下拉选择）
    test_methods = TestMethodDictionary.query.filter_by(is_active=True).order_by(TestMethodDictionary.display_order).all()
    test_conditions = TestConditionDictionary.query.filter_by(is_active=True).order_by(TestConditionDictionary.display_order).all()

    return render_template(
        'spec_definition/tw_list.html',
        categories=categories,
        current_category=current_category,
        definitions=definitions,
        test_methods=test_methods,
        test_conditions=test_conditions
    )


@spec_definition_bp.route('/api/list')
@login_required
@permission_required('rd_product', 'view')
def api_list_definitions():
    """API: 获取规格字典列表"""
    category_id = request.args.get('category_id', type=int)

    query = SpecDefinition.query.filter_by(is_active=True)
    if category_id:
        query = query.filter_by(category_id=category_id)

    definitions = query.order_by(SpecDefinition.display_order).all()

    return jsonify({
        'success': True,
        'data': [d.to_dict() for d in definitions]
    })


@spec_definition_bp.route('/api/create', methods=['POST'])
@login_required
@permission_required('rd_product', 'create')
def api_create_definition():
    """API: 创建规格项"""
    data = request.get_json()

    # 验证必填字段
    if not data.get('name'):
        return jsonify({'success': False, 'message': _('规格名称不能为空')}), 400
    if not data.get('category_id'):
        return jsonify({'success': False, 'message': _('请选择规格分类')}), 400

    # 检查名称是否重复
    existing = SpecDefinition.query.filter_by(
        category_id=data['category_id'],
        name=data['name']
    ).first()
    if existing:
        return jsonify({'success': False, 'message': _('该分类下已存在同名规格项')}), 400

    # 获取最大排序号
    max_order = db.session.query(db.func.max(SpecDefinition.display_order)).filter_by(
        category_id=data['category_id']
    ).scalar() or 0

    definition = SpecDefinition(
        category_id=data['category_id'],
        name=data['name'],
        name_en=data.get('name_en'),
        unit=data.get('unit'),
        description=data.get('description'),
        value_type=data.get('value_type', 'text'),
        default_test_condition_id=data.get('default_test_condition_id'),
        default_test_method_id=data.get('default_test_method_id'),
        display_order=max_order + 1
    )

    db.session.add(definition)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('规格项创建成功'),
        'data': definition.to_dict()
    })


@spec_definition_bp.route('/api/<int:definition_id>', methods=['GET'])
@login_required
@permission_required('rd_product', 'view')
def api_get_definition(definition_id):
    """API: 获取规格项详情"""
    definition = SpecDefinition.query.get_or_404(definition_id)
    return jsonify({
        'success': True,
        'data': definition.to_dict()
    })


@spec_definition_bp.route('/api/<int:definition_id>', methods=['PUT'])
@login_required
@permission_required('rd_product', 'edit')
def api_update_definition(definition_id):
    """API: 更新规格项"""
    definition = SpecDefinition.query.get_or_404(definition_id)
    data = request.get_json()

    # 验证必填字段
    if not data.get('name'):
        return jsonify({'success': False, 'message': _('规格名称不能为空')}), 400

    # 检查名称是否重复（排除自己）
    existing = SpecDefinition.query.filter(
        SpecDefinition.category_id == definition.category_id,
        SpecDefinition.name == data['name'],
        SpecDefinition.id != definition_id
    ).first()
    if existing:
        return jsonify({'success': False, 'message': _('该分类下已存在同名规格项')}), 400

    # 更新字段
    definition.name = data['name']
    definition.name_en = data.get('name_en')
    definition.unit = data.get('unit')
    definition.description = data.get('description')
    definition.value_type = data.get('value_type', 'text')
    definition.default_test_condition_id = data.get('default_test_condition_id')
    definition.default_test_method_id = data.get('default_test_method_id')

    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('规格项更新成功'),
        'data': definition.to_dict()
    })


@spec_definition_bp.route('/api/<int:definition_id>', methods=['DELETE'])
@login_required
@permission_required('rd_product', 'delete')
def api_delete_definition(definition_id):
    """API: 删除规格项（软删除）"""
    definition = SpecDefinition.query.get_or_404(definition_id)

    # 检查是否有模板在使用
    if definition.template_items:
        return jsonify({
            'success': False,
            'message': _('该规格项已被模板使用，无法删除')
        }), 400

    definition.is_active = False
    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('规格项删除成功')
    })


@spec_definition_bp.route('/api/reorder', methods=['POST'])
@login_required
@permission_required('rd_product', 'edit')
def api_reorder_definitions():
    """API: 规格项排序"""
    data = request.get_json()
    items = data.get('items', [])  # [{'id': 1, 'order': 0}, ...]

    print(f"[DEBUG] api_reorder_definitions called with items: {items}")

    updated_count = 0
    for item in items:
        definition = SpecDefinition.query.get(item['id'])
        if definition:
            old_order = definition.display_order
            definition.display_order = item['order']
            print(f"[DEBUG] Definition {definition.id} ({definition.name}): {old_order} -> {item['order']}")
            updated_count += 1
        else:
            print(f"[DEBUG] Definition {item['id']} not found!")

    db.session.commit()
    print(f"[DEBUG] Committed {updated_count} definition updates")

    return jsonify({
        'success': True,
        'message': _('排序更新成功')
    })


# ==================== 规格分类管理 ====================

@spec_definition_bp.route('/api/categories', methods=['GET'])
@login_required
@permission_required('rd_product', 'view')
def api_list_categories():
    """API: 获取规格分类列表"""
    categories = SpecCategory.query.filter_by(is_active=True).order_by(SpecCategory.display_order).all()
    return jsonify({
        'success': True,
        'data': [c.to_dict() for c in categories]
    })


@spec_definition_bp.route('/api/categories', methods=['POST'])
@login_required
@permission_required('rd_product', 'create')
def api_create_category():
    """API: 创建规格分类"""
    data = request.get_json()

    if not data.get('name'):
        return jsonify({'success': False, 'message': _('分类名称不能为空')}), 400
    if not data.get('code'):
        return jsonify({'success': False, 'message': _('分类代码不能为空')}), 400

    # 检查代码是否重复
    existing = SpecCategory.query.filter_by(code=data['code']).first()
    if existing:
        return jsonify({'success': False, 'message': _('该分类代码已存在')}), 400

    # 检查名称是否重复
    existing_name = SpecCategory.query.filter_by(name=data['name']).first()
    if existing_name:
        return jsonify({'success': False, 'message': _('该分类名称已存在')}), 400

    # 获取最大排序号
    max_order = db.session.query(db.func.max(SpecCategory.display_order)).scalar() or 0

    category = SpecCategory(
        code=data['code'].upper(),
        name=data['name'],
        name_en=data.get('name_en'),
        description=data.get('description'),
        display_order=data.get('display_order', max_order + 1)
    )

    db.session.add(category)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('规格分类创建成功'),
        'data': category.to_dict()
    })


@spec_definition_bp.route('/api/categories/<int:category_id>', methods=['PUT'])
@login_required
@permission_required('rd_product', 'edit')
def api_update_category(category_id):
    """API: 更新规格分类"""
    category = SpecCategory.query.get_or_404(category_id)
    data = request.get_json()

    if not data.get('name'):
        return jsonify({'success': False, 'message': _('分类名称不能为空')}), 400

    # 检查名称是否重复（排除自己）
    existing = SpecCategory.query.filter(
        SpecCategory.name == data['name'],
        SpecCategory.id != category_id
    ).first()
    if existing:
        return jsonify({'success': False, 'message': _('该分类名称已存在')}), 400

    # 更新字段（code 不允许修改）
    category.name = data['name']
    category.name_en = data.get('name_en')
    category.description = data.get('description')
    if data.get('display_order') is not None:
        category.display_order = data['display_order']

    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('规格分类更新成功'),
        'data': category.to_dict()
    })


@spec_definition_bp.route('/api/categories/<int:category_id>', methods=['DELETE'])
@login_required
@permission_required('rd_product', 'delete')
def api_delete_category(category_id):
    """API: 删除规格分类（软删除）"""
    category = SpecCategory.query.get_or_404(category_id)

    # 检查是否有规格定义在使用
    definition_count = SpecDefinition.query.filter_by(
        category_id=category_id,
        is_active=True
    ).count()

    if definition_count > 0:
        return jsonify({
            'success': False,
            'message': _('该分类下有 %(count)s 个规格定义，请先删除或移动这些规格项', count=definition_count)
        }), 400

    category.is_active = False
    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('规格分类删除成功')
    })


@spec_definition_bp.route('/api/categories/reorder', methods=['POST'])
@login_required
@permission_required('rd_product', 'edit')
def api_reorder_categories():
    """API: 分类排序"""
    data = request.get_json()
    items = data.get('items', [])  # [{'id': 1, 'order': 0}, ...]

    print(f"[DEBUG] api_reorder_categories called with items: {items}")

    updated_count = 0
    for item in items:
        category = SpecCategory.query.get(item['id'])
        if category:
            old_order = category.display_order
            category.display_order = item['order']
            print(f"[DEBUG] Category {category.id} ({category.name}): {old_order} -> {item['order']}")
            updated_count += 1
        else:
            print(f"[DEBUG] Category {item['id']} not found!")

    db.session.commit()
    print(f"[DEBUG] Committed {updated_count} category updates")

    return jsonify({
        'success': True,
        'message': _('排序更新成功')
    })


# ==================== 测试方法字典 ====================

@spec_definition_bp.route('/test-methods')
@login_required
@permission_required('rd_product', 'view')
def list_test_methods():
    """测试方法字典列表页"""
    methods = TestMethodDictionary.query.filter_by(is_active=True).order_by(TestMethodDictionary.display_order).all()
    return render_template('spec_definition/tw_test_methods.html', methods=methods)


@spec_definition_bp.route('/api/test-methods', methods=['GET'])
@login_required
@permission_required('rd_product', 'view')
def api_list_test_methods():
    """API: 获取测试方法列表"""
    methods = TestMethodDictionary.query.filter_by(is_active=True).order_by(TestMethodDictionary.display_order).all()
    return jsonify({
        'success': True,
        'data': [m.to_dict() for m in methods]
    })


@spec_definition_bp.route('/api/test-methods', methods=['POST'])
@login_required
@permission_required('rd_product', 'create')
def api_create_test_method():
    """API: 创建测试方法"""
    data = request.get_json()

    if not data.get('name'):
        return jsonify({'success': False, 'message': _('测试方法名称不能为空')}), 400

    existing = TestMethodDictionary.query.filter_by(name=data['name']).first()
    if existing:
        return jsonify({'success': False, 'message': _('该测试方法已存在')}), 400

    max_order = db.session.query(db.func.max(TestMethodDictionary.display_order)).scalar() or 0

    method = TestMethodDictionary(
        name=data['name'],
        description=data.get('description'),
        category=data.get('category'),
        display_order=max_order + 1
    )

    db.session.add(method)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('测试方法创建成功'),
        'data': method.to_dict()
    })


@spec_definition_bp.route('/api/test-methods/<int:method_id>', methods=['PUT'])
@login_required
@permission_required('rd_product', 'edit')
def api_update_test_method(method_id):
    """API: 更新测试方法"""
    method = TestMethodDictionary.query.get_or_404(method_id)
    data = request.get_json()

    if not data.get('name'):
        return jsonify({'success': False, 'message': _('测试方法名称不能为空')}), 400

    existing = TestMethodDictionary.query.filter(
        TestMethodDictionary.name == data['name'],
        TestMethodDictionary.id != method_id
    ).first()
    if existing:
        return jsonify({'success': False, 'message': _('该测试方法已存在')}), 400

    method.name = data['name']
    method.description = data.get('description')
    method.category = data.get('category')

    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('测试方法更新成功'),
        'data': method.to_dict()
    })


@spec_definition_bp.route('/api/test-methods/<int:method_id>', methods=['DELETE'])
@login_required
@permission_required('rd_product', 'delete')
def api_delete_test_method(method_id):
    """API: 删除测试方法（软删除）"""
    method = TestMethodDictionary.query.get_or_404(method_id)
    method.is_active = False
    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('测试方法删除成功')
    })


# ==================== 测试条件字典 ====================

@spec_definition_bp.route('/test-conditions')
@login_required
@permission_required('rd_product', 'view')
def list_test_conditions():
    """测试条件字典列表页"""
    conditions = TestConditionDictionary.query.filter_by(is_active=True).order_by(TestConditionDictionary.display_order).all()
    return render_template('spec_definition/tw_test_conditions.html', conditions=conditions)


@spec_definition_bp.route('/api/test-conditions', methods=['GET'])
@login_required
@permission_required('rd_product', 'view')
def api_list_test_conditions():
    """API: 获取测试条件列表"""
    conditions = TestConditionDictionary.query.filter_by(is_active=True).order_by(TestConditionDictionary.display_order).all()
    return jsonify({
        'success': True,
        'data': [c.to_dict() for c in conditions]
    })


@spec_definition_bp.route('/api/test-conditions', methods=['POST'])
@login_required
@permission_required('rd_product', 'create')
def api_create_test_condition():
    """API: 创建测试条件"""
    data = request.get_json()

    if not data.get('name'):
        return jsonify({'success': False, 'message': _('测试条件名称不能为空')}), 400

    existing = TestConditionDictionary.query.filter_by(name=data['name']).first()
    if existing:
        return jsonify({'success': False, 'message': _('该测试条件已存在')}), 400

    max_order = db.session.query(db.func.max(TestConditionDictionary.display_order)).scalar() or 0

    condition = TestConditionDictionary(
        name=data['name'],
        description=data.get('description'),
        display_order=max_order + 1
    )

    db.session.add(condition)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('测试条件创建成功'),
        'data': condition.to_dict()
    })


@spec_definition_bp.route('/api/test-conditions/<int:condition_id>', methods=['PUT'])
@login_required
@permission_required('rd_product', 'edit')
def api_update_test_condition(condition_id):
    """API: 更新测试条件"""
    condition = TestConditionDictionary.query.get_or_404(condition_id)
    data = request.get_json()

    if not data.get('name'):
        return jsonify({'success': False, 'message': _('测试条件名称不能为空')}), 400

    existing = TestConditionDictionary.query.filter(
        TestConditionDictionary.name == data['name'],
        TestConditionDictionary.id != condition_id
    ).first()
    if existing:
        return jsonify({'success': False, 'message': _('该测试条件已存在')}), 400

    condition.name = data['name']
    condition.description = data.get('description')

    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('测试条件更新成功'),
        'data': condition.to_dict()
    })


@spec_definition_bp.route('/api/test-conditions/<int:condition_id>', methods=['DELETE'])
@login_required
@permission_required('rd_product', 'delete')
def api_delete_test_condition(condition_id):
    """API: 删除测试条件（软删除）"""
    condition = TestConditionDictionary.query.get_or_404(condition_id)
    condition.is_active = False
    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('测试条件删除成功')
    })
