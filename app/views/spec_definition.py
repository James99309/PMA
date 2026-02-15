"""
规格字典管理路由

提供全局规格字典（SpecDefinition）的CRUD操作，
以及测试方法和测试条件字典的管理。
"""
import logging
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from flask_babel import _
from app import db
from app.models.spec_template import (
    SpecCategory, SpecDefinition, TestMethodDictionary, TestConditionDictionary,
    SPEC_CATEGORIES
)
from app.models.product_code import SpecificationDictionary, SpecificationOption, ProductCodeFieldOption
from app.models.product_spec import ProductSpec
from app.decorators import permission_required
from app.routes.spec_dictionary import _is_option_used_in_snapshot

spec_definition_bp = Blueprint('spec_definition', __name__, url_prefix='/admin/spec-definitions')


@spec_definition_bp.route('/')
@login_required
@permission_required('product_code', 'view')
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
@permission_required('product_code', 'view')
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
@permission_required('product_code', 'create')
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
        allow_attachment=data.get('allow_attachment', False),
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
@permission_required('product_code', 'view')
def api_get_definition(definition_id):
    """API: 获取规格项详情"""
    definition = SpecDefinition.query.get_or_404(definition_id)
    return jsonify({
        'success': True,
        'data': definition.to_dict()
    })


@spec_definition_bp.route('/api/<int:definition_id>', methods=['PUT'])
@login_required
@permission_required('product_code', 'edit')
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
    definition.allow_attachment = data.get('allow_attachment', False)
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
@permission_required('product_code', 'delete')
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


@spec_definition_bp.route('/api/<int:definition_id>/toggle', methods=['PUT'])
@login_required
@permission_required('product_code', 'edit')
def api_toggle_definition(definition_id):
    """API: 切换规格项启用/禁用状态"""
    definition = SpecDefinition.query.get_or_404(definition_id)

    # 切换状态
    definition.is_active = not definition.is_active
    db.session.commit()

    status_text = _('已启用') if definition.is_active else _('已禁用')

    return jsonify({
        'success': True,
        'message': f'{definition.name} {status_text}',
        'data': definition.to_dict()
    })


@spec_definition_bp.route('/api/disabled')
@login_required
@permission_required('product_code', 'view')
def api_list_disabled_definitions():
    """API: 获取已禁用的规格项列表"""
    category_id = request.args.get('category_id', type=int)

    query = SpecDefinition.query.filter_by(is_active=False)
    if category_id:
        query = query.filter_by(category_id=category_id)

    definitions = query.order_by(SpecDefinition.display_order).all()

    return jsonify({
        'success': True,
        'data': [d.to_dict() for d in definitions]
    })


@spec_definition_bp.route('/api/reorder', methods=['POST'])
@login_required
@permission_required('product_code', 'edit')
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
@permission_required('product_code', 'view')
def api_list_categories():
    """API: 获取规格分类列表"""
    categories = SpecCategory.query.filter_by(is_active=True).order_by(SpecCategory.display_order).all()
    return jsonify({
        'success': True,
        'data': [c.to_dict() for c in categories]
    })


@spec_definition_bp.route('/api/categories', methods=['POST'])
@login_required
@permission_required('product_code', 'create')
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
@permission_required('product_code', 'edit')
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
@permission_required('product_code', 'delete')
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


@spec_definition_bp.route('/api/categories/<int:category_id>/toggle', methods=['PUT'])
@login_required
@permission_required('product_code', 'edit')
def api_toggle_category(category_id):
    """API: 切换规格分类启用/禁用状态"""
    category = SpecCategory.query.get_or_404(category_id)

    # 切换状态
    category.is_active = not category.is_active
    db.session.commit()

    status_text = _('已启用') if category.is_active else _('已禁用')

    return jsonify({
        'success': True,
        'message': f'{category.name} {status_text}',
        'data': category.to_dict()
    })


@spec_definition_bp.route('/api/categories/reorder', methods=['POST'])
@login_required
@permission_required('product_code', 'edit')
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
@permission_required('product_code', 'view')
def list_test_methods():
    """测试方法字典列表页"""
    methods = TestMethodDictionary.query.filter_by(is_active=True).order_by(TestMethodDictionary.display_order).all()
    return render_template('spec_definition/tw_test_methods.html', methods=methods)


@spec_definition_bp.route('/api/test-methods', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def api_list_test_methods():
    """API: 获取测试方法列表"""
    methods = TestMethodDictionary.query.filter_by(is_active=True).order_by(TestMethodDictionary.display_order).all()
    return jsonify({
        'success': True,
        'data': [m.to_dict() for m in methods]
    })


@spec_definition_bp.route('/api/test-methods', methods=['POST'])
@login_required
@permission_required('product_code', 'create')
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
@permission_required('product_code', 'edit')
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
@permission_required('product_code', 'delete')
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
@permission_required('product_code', 'view')
def list_test_conditions():
    """测试条件字典列表页"""
    conditions = TestConditionDictionary.query.filter_by(is_active=True).order_by(TestConditionDictionary.display_order).all()
    return render_template('spec_definition/tw_test_conditions.html', conditions=conditions)


@spec_definition_bp.route('/api/test-conditions', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def api_list_test_conditions():
    """API: 获取测试条件列表"""
    conditions = TestConditionDictionary.query.filter_by(is_active=True).order_by(TestConditionDictionary.display_order).all()
    return jsonify({
        'success': True,
        'data': [c.to_dict() for c in conditions]
    })


@spec_definition_bp.route('/api/test-conditions', methods=['POST'])
@login_required
@permission_required('product_code', 'create')
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
@permission_required('product_code', 'edit')
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
@permission_required('product_code', 'delete')
def api_delete_test_condition(condition_id):
    """API: 删除测试条件（软删除）"""
    condition = TestConditionDictionary.query.get_or_404(condition_id)
    condition.is_active = False
    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('测试条件删除成功')
    })


# ==================== 规格指标管理（桥接到 SpecificationDictionary/SpecificationOption） ====================

def _get_or_create_spec_dict(definition):
    """通过 SpecDefinition.name 查找或创建 SpecificationDictionary 记录"""
    spec_dict = SpecificationDictionary.query.filter_by(name=definition.name).first()
    if not spec_dict:
        spec_dict = SpecificationDictionary(
            name=definition.name,
            unit=definition.unit,
            is_active=True
        )
        db.session.add(spec_dict)
        db.session.flush()
    return spec_dict


@spec_definition_bp.route('/api/<int:definition_id>/indicators', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def api_list_indicators(definition_id):
    """API: 获取规格定义的指标列表（通过 name 桥接到 SpecificationOption）"""
    definition = SpecDefinition.query.get_or_404(definition_id)

    spec_dict = SpecificationDictionary.query.filter_by(name=definition.name).first()
    if not spec_dict:
        return jsonify({
            'success': True,
            'data': [],
            'spec_dict_id': None
        })

    options = SpecificationOption.query.filter_by(
        spec_id=spec_dict.id
    ).order_by(SpecificationOption.position, SpecificationOption.id).all()

    # 批量检查 ProductCodeFieldOption 引用
    from app.models.product_code import ProductCodeFieldOption
    field_option_refs = db.session.query(ProductCodeFieldOption.spec_option_id).filter(
        ProductCodeFieldOption.spec_option_id.in_([opt.id for opt in options])
    ).distinct().all()
    field_option_used_ids = {r[0] for r in field_option_refs}

    # 批量检查 ProductSpec.field_code 引用（code 编辑值时不变，比 value 更可靠）
    # 同时检测待同步状态：field_code 匹配但 field_value 不等于当前 option.value
    option_codes = [opt.code for opt in options if opt.code]
    product_spec_used_codes = set()
    # { code: [{old_value, count}] } — 记录需要同步的旧值
    pending_sync_by_code = {}
    if option_codes:
        # 构建 code→current_value 映射
        code_to_value = {opt.code: opt.value for opt in options if opt.code}

        ps_rows = db.session.query(
            ProductSpec.field_code,
            ProductSpec.field_value,
            db.func.count(ProductSpec.id)
        ).filter(
            ProductSpec.field_name == definition.name,
            ProductSpec.field_code.in_(option_codes)
        ).group_by(ProductSpec.field_code, ProductSpec.field_value).all()

        for code, value, cnt in ps_rows:
            product_spec_used_codes.add(code)
            # field_value 与当前 option.value 不一致 → 待同步
            if code in code_to_value and value != code_to_value[code]:
                pending_sync_by_code.setdefault(code, []).append({
                    'old_value': value,
                    'count': cnt
                })

    data = []
    for opt in options:
        d = opt.to_dict()
        d['is_used'] = (opt.id in field_option_used_ids
                        or opt.code in product_spec_used_codes)
        # 附加待同步信息
        sync_info = pending_sync_by_code.get(opt.code)
        if sync_info:
            total = sum(item['count'] for item in sync_info)
            d['sync_pending'] = True
            d['sync_old_values'] = sync_info
            d['sync_affected_count'] = total
        data.append(d)

    return jsonify({
        'success': True,
        'data': data,
        'spec_dict_id': spec_dict.id
    })


@spec_definition_bp.route('/api/<int:definition_id>/indicators', methods=['POST'])
@login_required
@permission_required('product_code', 'create')
def api_create_indicator(definition_id):
    """API: 创建指标（通过 name 桥接，自动创建 SpecificationDictionary）"""
    from app.views.spec_template import allocate_code_for_value

    definition = SpecDefinition.query.get_or_404(definition_id)
    data = request.get_json()

    value = (data.get('value') or '').strip()
    if not value:
        return jsonify({'success': False, 'message': _('指标值不能为空')}), 400

    # 查找或创建 SpecificationDictionary
    spec_dict = _get_or_create_spec_dict(definition)

    # 检查重复
    existing = SpecificationOption.query.filter_by(
        spec_id=spec_dict.id, value=value
    ).first()
    if existing:
        return jsonify({'success': False, 'message': _('指标值已存在')}), 400

    # 生成编码（使用 allocate_code_for_value 与 MN 编码系统保持一致）
    existing_options = {opt.value: opt.code for opt in
        SpecificationOption.query.filter_by(spec_id=spec_dict.id, is_active=True).all()}
    code = allocate_code_for_value(value, existing_options)

    option = SpecificationOption(
        spec_id=spec_dict.id,
        value=value,
        code=code,
        is_active=True
    )
    db.session.add(option)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('指标创建成功'),
        'data': option.to_dict()
    })


@spec_definition_bp.route('/api/indicators/<int:option_id>', methods=['DELETE'])
@login_required
@permission_required('product_code', 'delete')
def api_delete_indicator(option_id):
    """API: 删除指标（检查是否被引用）"""
    option = SpecificationOption.query.get_or_404(option_id)

    # 检查是否被子分类引用（ProductCodeFieldOption）
    from app.models.product_code import ProductCodeFieldOption
    ref_count = ProductCodeFieldOption.query.filter_by(
        spec_option_id=option.id
    ).count()
    if ref_count > 0:
        return jsonify({
            'success': False,
            'message': _('该指标已被 %(count)s 个子分类引用，无法删除', count=ref_count)
        }), 400

    # 检查是否被产品编码快照引用
    if _is_option_used_in_snapshot(option.value):
        return jsonify({
            'success': False,
            'message': _('该指标已被产品编码使用，无法删除')
        }), 400

    db.session.delete(option)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('指标删除成功')
    })


def _check_indicator_is_used(option):
    """检查指标是否被产品或快照引用"""
    ref = ProductCodeFieldOption.query.filter_by(spec_option_id=option.id).first()
    if ref:
        return True
    return _is_option_used_in_snapshot(option.value)


@spec_definition_bp.route('/api/indicators/<int:option_id>', methods=['PUT'])
@login_required
@permission_required('product_code', 'edit')
def api_update_indicator(option_id):
    """API: 编辑指标值（编码不可修改）"""
    option = SpecificationOption.query.get_or_404(option_id)
    data = request.get_json()

    old_value = option.value

    # 更新 value
    new_value = (data.get('value') or '').strip()
    if not new_value:
        return jsonify({'success': False, 'message': _('指标值不能为空')}), 400

    if new_value == old_value:
        return jsonify({'success': True, 'message': _('未做修改'), 'data': option.to_dict()})

    # 检查重复
    existing = SpecificationOption.query.filter(
        SpecificationOption.spec_id == option.spec_id,
        SpecificationOption.value == new_value,
        SpecificationOption.id != option_id
    ).first()
    if existing:
        return jsonify({'success': False, 'message': _('指标值已存在')}), 400

    option.value = new_value
    db.session.commit()

    response_data = option.to_dict()

    # 直接检查 ProductSpec 是否有需要同步的记录（不依赖 is_used 判断）
    # 修复：二次编辑后 option.value 已变，_check_indicator_is_used 按新值查快照会失败
    spec_name = option.spec.name
    affected_count = ProductSpec.query.filter(
        ProductSpec.field_name == spec_name,
        ProductSpec.field_value == old_value
    ).count()
    if affected_count > 0:
        response_data['sync_needed'] = True
        response_data['old_value'] = old_value
        response_data['affected_count'] = affected_count

    return jsonify({
        'success': True,
        'message': _('指标更新成功'),
        'data': response_data
    })


@spec_definition_bp.route('/api/indicators/<int:option_id>/sync-preview', methods=['GET'])
@login_required
@permission_required('product_code', 'edit')
def api_sync_preview(option_id):
    """API: 预览同步将影响的产品列表"""
    from app.models.product import Product

    option = SpecificationOption.query.get_or_404(option_id)
    old_value = request.args.get('old_value', '').strip()
    if not old_value:
        return jsonify({'success': False, 'message': _('缺少原始值参数')}), 400

    spec_name = option.spec.name

    affected = db.session.query(
        Product.product_name,
        Product.model,
        ProductSpec.field_value
    ).join(Product, ProductSpec.product_id == Product.id).filter(
        ProductSpec.field_name == spec_name,
        ProductSpec.field_value == old_value
    ).all()

    products = [
        {
            'product_name': row.product_name or '',
            'model': row.model or '',
            'old_value': row.field_value
        }
        for row in affected
    ]

    return jsonify({
        'success': True,
        'data': products,
        'total': len(products)
    })


@spec_definition_bp.route('/api/indicators/<int:option_id>/sync-products', methods=['POST'])
@login_required
@permission_required('product_code', 'edit')
def api_sync_indicator_to_products(option_id):
    """API: 将指标值变更同步到所有引用的产品规格"""
    from app.utils.product_helpers import generate_spec_mn, generate_product_snapshot

    option = SpecificationOption.query.get_or_404(option_id)
    data = request.get_json()

    old_value = (data.get('old_value') or '').strip()
    if not old_value:
        return jsonify({'success': False, 'message': _('缺少原始值参数')}), 400

    spec_name = option.spec.name
    new_value = option.value

    # 查找需要同步的 ProductSpec
    affected_specs = ProductSpec.query.filter(
        ProductSpec.field_name == spec_name,
        ProductSpec.field_value == old_value
    ).all()

    if not affected_specs:
        return jsonify({
            'success': True,
            'message': _('没有需要同步的产品'),
            'data': {'synced_specs': 0, 'synced_products': 0}
        })

    # 更新 field_value（field_code 不变）
    synced_product_ids = set()
    for spec in affected_specs:
        spec.field_value = new_value
        synced_product_ids.add(spec.product_id)

    db.session.flush()

    # 重新生成每个受影响产品的 MN 和 snapshot
    from app.models.product import Product
    mn_errors = []
    for product_id in synced_product_ids:
        product = Product.query.get(product_id)
        if not product:
            continue
        try:
            new_mn = generate_spec_mn(product)
            if new_mn:
                product.spec_mn = new_mn
        except Exception as e:
            mn_errors.append(f'产品{product_id}: MN生成失败 - {str(e)}')
            logging.getLogger(__name__).warning(f'产品{product_id} MN重新生成失败: {e}')
        try:
            generate_product_snapshot(product, source='sync')
        except Exception as e:
            logging.getLogger(__name__).warning(f'产品{product_id} 快照重新生成失败: {e}')

    db.session.commit()

    message = _('同步完成：%(specs)s 条规格，%(products)s 个产品',
                specs=len(affected_specs), products=len(synced_product_ids))
    if mn_errors:
        message += f' ({len(mn_errors)} 个MN生成警告)'

    return jsonify({
        'success': True,
        'message': message,
        'data': {
            'synced_specs': len(affected_specs),
            'synced_products': len(synced_product_ids),
            'warnings': mn_errors if mn_errors else None
        }
    })
