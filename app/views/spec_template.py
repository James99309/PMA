"""
规格模板管理路由

提供型号级规格模板（SpecTemplate）的CRUD操作，
以及模板规格项（SpecTemplateItem）的管理。
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, send_file, Response, abort
from flask_login import login_required, current_user
from flask_babel import _
import io
import logging
from urllib.parse import quote
from app import db
from datetime import datetime, timezone
from app.models.spec_template import (
    SpecCategory, SpecTemplate, SpecTemplateItem,
    TestMethodDictionary, TestConditionDictionary,
    ProductConfiguration, ProductConfigValue, SpecAttachment,
    CONFIG_STATUS, REGIONS,
    SAFE_CHARS, calculate_check_digit, generate_safe_code_char,
    CODE_RULE_VERSION
)
from app.models.product_code import (
    ProductCategory, ProductSubcategory, ProductCodeField,
    SpecificationDictionary, SpecificationOption
)
from app.models.dev_product import DevProduct
from app.models.product import Product
from app.decorators import permission_required

logger = logging.getLogger(__name__)


def generate_code_rule_snapshot(config, mn_code, code_items_data):
    """
    生成编码规则快照

    Args:
        config: ProductConfiguration 对象
        mn_code: 生成的 MN 编码字符串
        code_items_data: 参与编码的规格项数据列表

    Returns:
        dict: 完整的编码规则快照
    """
    template = config.template

    return {
        "version": CODE_RULE_VERSION,
        "generated_at": datetime.utcnow().isoformat(),
        "template": {
            "id": template.id,
            "model": template.model,
            "version": template.version
        },
        "category": {
            "id": template.category_id,
            "code": template.category.code_letter if template.category else None
        },
        "subcategory": {
            "id": template.subcategory_id,
            "code": template.subcategory.code_letter if template.subcategory else None
        },
        "region": config.region,
        "code_items": code_items_data,
        "mn_code": mn_code
    }


def generate_mn_code(config, template=None, save_snapshot=True):
    """
    生成配置版本的MN编码

    编码结构：[区域码] + [分类码] + [子分类码] + [规格编码...] + [校验位]

    Args:
        config: ProductConfiguration 对象
        template: SpecTemplate 对象（可选，如果config.template不可用）
        save_snapshot: 是否保存编码规则快照（默认True）

    Returns:
        str: 完整的MN编码（含校验位），或 None（如果无法生成）
    """
    if template is None:
        template = config.template

    if not template:
        return None

    code_parts = []

    # 1. 区域码（来自配置版本的region字段）
    if config.region:
        code_parts.append(config.region)
    else:
        code_parts.append('X')  # 未指定区域

    # 2. 分类码（来自模板的category）
    if template.category and hasattr(template.category, 'code_letter') and template.category.code_letter:
        code_parts.append(template.category.code_letter)
    else:
        code_parts.append('X')

    # 3. 子分类码（来自模板的subcategory）
    if template.subcategory and hasattr(template.subcategory, 'code_letter') and template.subcategory.code_letter:
        code_parts.append(template.subcategory.code_letter)
    else:
        code_parts.append('X')

    # 4. 规格编码（来自 use_in_code=True 的规格项）
    code_items = sorted(
        [item for item in template.items if item.use_in_code],
        key=lambda x: x.display_order
    )

    # 收集快照数据
    code_items_data = []

    for item in code_items:
        # 获取配置值（优先使用配置值，否则使用通用值）
        value = None
        for cv in config.config_values:
            if cv.template_item_id == item.id:
                value = cv.value
                break
        if not value:
            value = item.general_value

        # 编码映射使用 item.options（在编辑模板时自动生成）
        code_options = item.options or {}

        # 生成编码字符
        code_char = generate_safe_code_char(value, code_options)

        # 处理编码长度（1位或2位）
        if item.code_length == 2:
            final_code_char = code_char.ljust(2, 'X')[:2]
        else:
            final_code_char = code_char[:1]

        code_parts.append(final_code_char)

        # 收集快照数据
        code_items_data.append({
            "item_id": item.id,
            "definition_name": item.spec_dict.name if item.spec_dict else None,
            "display_order": item.display_order,
            "code_length": item.code_length,
            "options": code_options,
            "value": value,
            "code_char": final_code_char
        })

    # 合并编码
    main_code = ''.join(code_parts)

    # 5. 计算校验位
    check_digit = calculate_check_digit(main_code)
    full_mn_code = main_code + check_digit

    # 保存快照
    if save_snapshot:
        config.code_rule_version = CODE_RULE_VERSION
        config.code_rule_snapshot = generate_code_rule_snapshot(config, full_mn_code, code_items_data)

        # 标记当前版本已被使用（绑定）
        # 只有第一次生成MN编码时才设置绑定时间
        if template.version_first_used_at is None:
            template.version_first_used_at = datetime.utcnow()

        # 持久化所有规格值（包括使用默认值的），确保数据完整
        existing_item_ids = {cv.template_item_id for cv in config.config_values}
        for item in template.items:
            if item.id not in existing_item_ids and item.general_value:
                # 这个规格项没有保存过值，保存默认值
                new_cv = ProductConfigValue(
                    configuration_id=config.id,
                    template_item_id=item.id,
                    value=item.general_value
                )
                db.session.add(new_cv)

    return full_mn_code


def allocate_code_for_value(value, existing_options):
    """
    根据值内容计算编码字符（基于哈希的分配策略）

    相同的值内容会从相同的起始位置开始查找可用编码，
    使得编码更具有语义关联性，而不是所有默认值都是 "3"。

    Args:
        value: 需要编码的规格值
        existing_options: 已有的编码映射 {"规格值": "编码字符"}

    Returns:
        str: 分配的编码字符，如果全部用完则返回 'X'
    """
    used_codes = set(existing_options.values()) if existing_options else set()

    # 计算值的哈希，确定起始位置
    # 使用字符串哈希，确保相同值总是从相同位置开始
    if value:
        hash_val = sum(ord(c) for c in str(value)) % len(SAFE_CHARS)
    else:
        hash_val = 0

    # 从哈希位置开始，顺序查找第一个未被使用的编码
    for i in range(len(SAFE_CHARS)):
        idx = (hash_val + i) % len(SAFE_CHARS)
        if SAFE_CHARS[idx] not in used_codes:
            return SAFE_CHARS[idx]

    return 'X'  # 所有编码已用完


def ensure_code_for_value(options, value):
    """
    确保值有对应的编码，如果没有则分配新编码

    Args:
        options: 已有的编码映射（可能为 None）
        value: 需要编码的值

    Returns:
        dict: 更新后的编码映射（新字典，不修改原字典）
    """
    # 复制字典，避免修改原对象（SQLAlchemy 需要检测到变化才会保存）
    result = dict(options) if options else {}
    if value and value not in result:
        result[value] = allocate_code_for_value(value, result)
    return result


def increment_version(version):
    """
    递增版本号 V1.0 → V1.1 → V1.2 ...

    Args:
        version: 当前版本号字符串，如 'V1.0'

    Returns:
        str: 递增后的版本号
    """
    import re
    match = re.match(r'V(\d+)\.(\d+)', version or 'V1.0')
    if match:
        major, minor = int(match.group(1)), int(match.group(2))
        return f'V{major}.{minor + 1}'
    return 'V1.1'


def detect_structural_changes(template, new_items_data, new_category_id=None, new_subcategory_id=None):
    """
    检测是否有结构性变更（会影响MN编码结构的变更）

    结构性变更包括：
    - 添加/删除参与编码的规格项（use_in_code 变化）
    - 修改规格项的编码顺序（display_order 变化）
    - 修改编码长度（code_length 变化）
    - 修改分类/子分类（影响MN前两位）

    不包括：
    - 新增值→编码映射（只是扩展 options 字典）
    - 修改通用值
    - 修改规格项名称、单位等非编码相关属性

    Args:
        template: SpecTemplate 对象
        new_items_data: 新的规格项数据列表
        new_category_id: 新的产品分类ID（可选）
        new_subcategory_id: 新的产品子分类ID（可选）

    Returns:
        dict: {
            'has_changes': bool,
            'changes': [{'type': '变更类型', 'name': '规格项名称'}, ...]
        }
    """
    changes = []

    # 检查分类/子分类变化
    if new_category_id is not None and new_category_id != template.category_id:
        old_name = template.category.name if template.category else _('未设置')
        changes.append({
            'type': 'category_changed',
            'name': old_name
        })

    if new_subcategory_id is not None and new_subcategory_id != template.subcategory_id:
        old_name = template.subcategory.name if template.subcategory else _('未设置')
        changes.append({
            'type': 'subcategory_changed',
            'name': old_name
        })

    # 获取现有参与编码的规格项
    old_code_items = {}
    for item in template.items:
        if item.use_in_code:
            old_code_items[item.spec_dict_id] = {
                'item': item,
                'display_order': item.display_order,
                'code_length': item.code_length
            }

    # 构建新的参与编码规格项映射
    new_code_items = {}
    for idx, item_data in enumerate(new_items_data):
        def_id = item_data.get('definition_id')
        use_in_code = item_data.get('use_in_code', False)
        if use_in_code and def_id:
            new_code_items[def_id] = {
                'data': item_data,
                'display_order': item_data.get('display_order', idx),
                'code_length': item_data.get('code_length', 1)
            }

    # 检查新增的参与编码规格项
    for def_id, new_info in new_code_items.items():
        if def_id not in old_code_items:
            # 获取规格项名称（从统一主表）
            definition = SpecificationDictionary.query.get(def_id)
            name = definition.name if definition else str(def_id)
            changes.append({
                'type': 'add_code_item',
                'name': name
            })

    # 检查删除的参与编码规格项
    for def_id, old_info in old_code_items.items():
        if def_id not in new_code_items:
            name = old_info['item'].spec_dict.name if old_info['item'].spec_dict else str(def_id)
            changes.append({
                'type': 'remove_code_item',
                'name': name
            })

    # 检查修改的参与编码规格项
    for def_id in set(old_code_items.keys()) & set(new_code_items.keys()):
        old_info = old_code_items[def_id]
        new_info = new_code_items[def_id]
        name = old_info['item'].spec_dict.name if old_info['item'].spec_dict else str(def_id)

        # 检查编码长度变化
        if old_info['code_length'] != new_info['code_length']:
            changes.append({
                'type': 'code_length_changed',
                'name': name
            })

        # 检查显示顺序变化
        if old_info['display_order'] != new_info['display_order']:
            changes.append({
                'type': 'order_changed',
                'name': name
            })

    # 检查 use_in_code 从 True 变为 False 的情况（已在 remove_code_item 中处理）
    # 检查 use_in_code 从 False 变为 True 的情况（已在 add_code_item 中处理）

    return {
        'has_changes': len(changes) > 0,
        'changes': changes
    }


def _load_definition_indicators(definitions):
    """批量加载每个 SpecificationDictionary 对应的 SpecificationOption 列表

    现在 definitions 就是 SpecificationDictionary 对象列表，直接用 id 即可。
    """
    spec_dict_ids = [d.id for d in definitions]
    if not spec_dict_ids:
        return {}

    all_options = SpecificationOption.query.filter(
        SpecificationOption.spec_id.in_(spec_dict_ids),
        SpecificationOption.is_active == True
    ).order_by(SpecificationOption.id).all()

    options_by_spec_id = {}
    for opt in all_options:
        options_by_spec_id.setdefault(opt.spec_id, []).append(opt)

    definition_indicators = {}
    for d in definitions:
        opts = options_by_spec_id.get(d.id, [])
        if opts:
            definition_indicators[d.id] = [
                {'value': o.value, 'code': o.code} for o in opts
            ]
    return definition_indicators


spec_template_bp = Blueprint('spec_template', __name__, url_prefix='/dev-product/spec-templates')


def _is_template_admin():
    """检查当前用户是否有模板管理员权限（可查看所有模板）"""
    return current_user.role.lower() in ('admin', 'ceo')


def _check_template_owner(template):
    """检查当前用户是否有权访问该模板，无权则 abort(403)"""
    if _is_template_admin():
        return
    if template.created_by != current_user.id:
        abort(403)


def _check_config_owner(config):
    """检查当前用户是否有权访问该配置版本（通过所属模板的 owner 判断）"""
    if _is_template_admin():
        return
    if config.template and config.template.created_by != current_user.id:
        abort(403)


@spec_template_bp.route('/')
@login_required
@permission_required('product_code', 'view')
def list_templates():
    """规格模板列表页"""
    query = SpecTemplate.query.filter(SpecTemplate.deleted_at.is_(None))
    if not _is_template_admin():
        query = query.filter_by(created_by=current_user.id)
    templates = query.order_by(SpecTemplate.created_at.desc()).all()

    return render_template(
        'spec_template/tw_list.html',
        templates=templates
    )


@spec_template_bp.route('/create', methods=['GET'])
@login_required
@permission_required('product_code', 'create')
def create_template_page():
    """创建规格模板页面"""
    categories = SpecCategory.query.filter_by(is_active=True).order_by(SpecCategory.display_order).all()
    definitions = SpecificationDictionary.query.filter_by(is_active=True).order_by(
        SpecificationDictionary.category_id, SpecificationDictionary.display_order
    ).all()
    test_methods = TestMethodDictionary.query.filter_by(is_active=True).order_by(TestMethodDictionary.display_order).all()
    test_conditions = TestConditionDictionary.query.filter_by(is_active=True).order_by(TestConditionDictionary.display_order).all()

    # 按分类组织规格项（跳过无分类的条目，避免 None key 导致 JSON 序列化排序报错）
    definitions_by_category = {}
    for definition in definitions:
        if definition.category_id is None:
            continue
        if definition.category_id not in definitions_by_category:
            definitions_by_category[definition.category_id] = []
        definitions_by_category[definition.category_id].append(definition)

    # 获取产品分类和子分类数据（用于MN编码）
    product_categories = ProductCategory.query.order_by(ProductCategory.display_order).all()
    subcategories = ProductSubcategory.query.order_by(ProductSubcategory.display_order).all()

    # 按分类组织子分类
    subcategories_by_category = {}
    for subcat in subcategories:
        if subcat.category_id not in subcategories_by_category:
            subcategories_by_category[subcat.category_id] = []
        subcategories_by_category[subcat.category_id].append({
            'id': subcat.id,
            'name': subcat.name,
            'name_en': subcat.name_en or '',
            'code_letter': subcat.code_letter
        })

    # 按子分类收集产品库已有产品名称（供模板名称输入下拉参考）
    # 中文名来自本地产品库(SP8D)，英文名来自子分类name_en(已同步OVS)
    existing_products = Product.query.filter(
        Product.subcategory_id.isnot(None),
        Product.is_deleted == False
    ).with_entities(
        Product.subcategory_id,
        Product.product_name
    ).distinct().all()
    product_names_by_subcategory = {}
    for p in existing_products:
        sub_id = str(p.subcategory_id)
        if sub_id not in product_names_by_subcategory:
            product_names_by_subcategory[sub_id] = []
        if p.product_name and p.product_name not in product_names_by_subcategory[sub_id]:
            product_names_by_subcategory[sub_id].append(p.product_name)

    # 规格定义数据（JSON格式，供前端动态排序使用）
    definitions_data = {}
    for category_id, defs in definitions_by_category.items():
        definitions_data[category_id] = [d.to_dict() for d in defs]

    # 批量加载指标选项（通过 SpecificationDictionary.name 桥接）
    definition_indicators = _load_definition_indicators(definitions)

    return render_template(
        'spec_template/tw_edit.html',
        template=None,
        categories=categories,
        definitions_by_category=definitions_by_category,
        definitions_data=definitions_data,
        definition_indicators=definition_indicators,
        test_methods=test_methods,
        test_conditions=test_conditions,
        product_categories=product_categories,
        subcategories_by_category=subcategories_by_category,
        product_names_by_subcategory=product_names_by_subcategory,
        is_edit=False
    )


@spec_template_bp.route('/<int:template_id>', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def view_template(template_id):
    """查看规格模板详情"""
    template = SpecTemplate.query.get_or_404(template_id)
    _check_template_owner(template)
    categories = SpecCategory.query.filter_by(is_active=True).order_by(SpecCategory.display_order).all()

    # 获取模板中的规格项，按分类组织（优先 spec_dict，回退 definition）
    items_by_category = {}
    for item in template.items:
        src = item.spec_dict
        if src and src.category_id:
            cat_id = src.category_id
            if cat_id not in items_by_category:
                items_by_category[cat_id] = []
            items_by_category[cat_id].append(item)

    return render_template(
        'spec_template/tw_detail.html',
        template=template,
        categories=categories,
        items_by_category=items_by_category
    )


@spec_template_bp.route('/<int:template_id>/edit', methods=['GET'])
@login_required
@permission_required('product_code', 'edit')
def edit_template_page(template_id):
    """编辑规格模板页面"""
    template = SpecTemplate.query.get_or_404(template_id)
    _check_template_owner(template)
    categories = SpecCategory.query.filter_by(is_active=True).order_by(SpecCategory.display_order).all()
    definitions = SpecificationDictionary.query.filter_by(is_active=True).order_by(
        SpecificationDictionary.category_id, SpecificationDictionary.display_order
    ).all()
    test_methods = TestMethodDictionary.query.filter_by(is_active=True).order_by(TestMethodDictionary.display_order).all()
    test_conditions = TestConditionDictionary.query.filter_by(is_active=True).order_by(TestConditionDictionary.display_order).all()

    # 按分类组织规格项（跳过无分类的条目，避免 None key 导致 JSON 序列化排序报错）
    definitions_by_category = {}
    for definition in definitions:
        if definition.category_id is None:
            continue
        if definition.category_id not in definitions_by_category:
            definitions_by_category[definition.category_id] = []
        definitions_by_category[definition.category_id].append(definition)

    # 获取模板中已选择的规格项ID和设置
    selected_items = {}
    for item in template.items:
        key = item.spec_dict_id
        selected_items[key] = {
            'id': item.id,
            'definition_id': key,  # 前端字段名保持不变
            'general_value': item.general_value,
            'test_condition_id': item.test_condition_id,
            'test_condition_text': item.test_condition_text,
            'test_method_id': item.test_method_id,
            'test_method_text': item.test_method_text,
            'is_required': item.is_required,
            'options': item.options,
            'use_in_code': item.use_in_code,
            'code_length': item.code_length,
            'display_order': item.display_order
        }

    # 获取产品分类和子分类数据（用于MN编码）
    product_categories = ProductCategory.query.order_by(ProductCategory.display_order).all()
    subcategories = ProductSubcategory.query.order_by(ProductSubcategory.display_order).all()

    # 按分类组织子分类
    subcategories_by_category = {}
    for subcat in subcategories:
        if subcat.category_id not in subcategories_by_category:
            subcategories_by_category[subcat.category_id] = []
        subcategories_by_category[subcat.category_id].append({
            'id': subcat.id,
            'name': subcat.name,
            'name_en': subcat.name_en or '',
            'code_letter': subcat.code_letter
        })

    # 按子分类收集产品库已有产品名称（供模板名称输入下拉参考）
    existing_products = Product.query.filter(
        Product.subcategory_id.isnot(None),
        Product.is_deleted == False
    ).with_entities(
        Product.subcategory_id,
        Product.product_name
    ).distinct().all()
    product_names_by_subcategory = {}
    for p in existing_products:
        sub_id = str(p.subcategory_id)
        if sub_id not in product_names_by_subcategory:
            product_names_by_subcategory[sub_id] = []
        if p.product_name and p.product_name not in product_names_by_subcategory[sub_id]:
            product_names_by_subcategory[sub_id].append(p.product_name)

    # 计算被锁定的编码项（有活跃配置时，已有编码项不可修改）
    locked_code_item_ids = set()
    max_locked_order = 0
    active_configs = [c for c in template.configurations if c.deleted_at is None]
    if active_configs:
        for item in template.items:
            if item.use_in_code:
                locked_code_item_ids.add(item.spec_dict_id)
                max_locked_order = max(max_locked_order, item.display_order or 0)

    # 规格定义数据（JSON格式，供前端动态排序使用）
    definitions_data = {}
    for category_id, defs in definitions_by_category.items():
        definitions_data[category_id] = [d.to_dict() for d in defs]

    # 批量加载指标选项（通过 SpecificationDictionary.name 桥接）
    definition_indicators = _load_definition_indicators(definitions)

    return render_template(
        'spec_template/tw_edit.html',
        template=template,
        categories=categories,
        definitions_by_category=definitions_by_category,
        definitions_data=definitions_data,
        definition_indicators=definition_indicators,
        test_methods=test_methods,
        test_conditions=test_conditions,
        selected_items=selected_items,
        locked_code_item_ids=locked_code_item_ids,
        max_locked_order=max_locked_order,
        product_categories=product_categories,
        subcategories_by_category=subcategories_by_category,
        product_names_by_subcategory=product_names_by_subcategory,
        is_edit=True
    )


# ==================== API 端点 ====================

@spec_template_bp.route('/api/list')
@login_required
@permission_required('product_code', 'view')
def api_list_templates():
    """API: 获取规格模板列表"""
    query = SpecTemplate.query.filter(SpecTemplate.deleted_at.is_(None))
    if not _is_template_admin():
        query = query.filter_by(created_by=current_user.id)
    templates = query.order_by(SpecTemplate.created_at.desc()).all()

    return jsonify({
        'success': True,
        'data': [t.to_dict() for t in templates]
    })


@spec_template_bp.route('/api/create', methods=['POST'])
@login_required
@permission_required('product_code', 'create')
def api_create_template():
    """API: 创建规格模板"""
    data = request.get_json()

    # 验证必填字段
    if not data.get('model'):
        return jsonify({'success': False, 'message': _('产品型号不能为空')}), 400

    # 检查型号是否重复
    existing = SpecTemplate.query.filter(SpecTemplate.model == data['model'], SpecTemplate.deleted_at.is_(None)).first()
    if existing:
        return jsonify({'success': False, 'message': _('该型号的规格模板已存在')}), 400

    # 创建模板
    template = SpecTemplate(
        model=data['model'],
        name=data.get('name'),
        name_en=data.get('name_en'),
        description=data.get('description'),
        version=data.get('version', 'V1.0'),
        category_id=data.get('category_id'),
        subcategory_id=data.get('subcategory_id'),
        created_by=current_user.id
    )

    db.session.add(template)
    db.session.flush()  # 获取ID

    # 添加规格项
    items_data = data.get('items', [])
    for idx, item_data in enumerate(items_data):
        if not item_data.get('definition_id'):
            continue

        # 如果参与编码且有通用值，确保通用值有编码
        use_in_code = item_data.get('use_in_code', False)
        general_value = item_data.get('general_value')
        options = item_data.get('options') or {}
        if use_in_code and general_value:
            options = ensure_code_for_value(options, general_value)

        dict_id = item_data['definition_id']
        item = SpecTemplateItem(
            template_id=template.id,
            spec_dict_id=dict_id,
            general_value=item_data.get('general_value'),
            test_condition_id=item_data.get('test_condition_id'),
            test_condition_text=item_data.get('test_condition_text'),
            test_method_id=item_data.get('test_method_id'),
            test_method_text=item_data.get('test_method_text'),
            is_required=item_data.get('is_required', False),
            options=options,
            display_order=item_data.get('display_order', idx),
            use_in_code=use_in_code,
            code_length=item_data.get('code_length', 1)
        )
        db.session.add(item)

    db.session.commit()

    # 构建返回数据，包含 items 以便前端更新
    result_data = template.to_dict()
    result_data['items'] = [item.to_dict() for item in template.items]

    return jsonify({
        'success': True,
        'message': _('规格模板创建成功'),
        'data': result_data
    })


@spec_template_bp.route('/api/<int:template_id>', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def api_get_template(template_id):
    """API: 获取规格模板详情"""
    template = SpecTemplate.query.get_or_404(template_id)
    _check_template_owner(template)
    result_data = template.to_dict()
    result_data['items'] = [item.to_dict() for item in template.items]
    return jsonify({
        'success': True,
        'data': result_data
    })


@spec_template_bp.route('/api/<int:template_id>', methods=['PUT'])
@login_required
@permission_required('product_code', 'edit')
def api_update_template(template_id):
    """API: 更新规格模板"""
    template = SpecTemplate.query.get_or_404(template_id)
    _check_template_owner(template)
    data = request.get_json()

    # 验证必填字段
    if not data.get('model'):
        return jsonify({'success': False, 'message': _('产品型号不能为空')}), 400

    # 检查型号是否重复（排除自己）
    existing = SpecTemplate.query.filter(
        SpecTemplate.model == data['model'],
        SpecTemplate.id != template_id,
        SpecTemplate.deleted_at.is_(None)
    ).first()
    if existing:
        return jsonify({'success': False, 'message': _('该型号的规格模板已存在')}), 400

    # ========== 版本升级检测 ==========
    items_data = data.get('items', [])
    new_category_id = data.get('category_id')
    new_subcategory_id = data.get('subcategory_id')

    # 检测结构性变更
    structural_check = detect_structural_changes(
        template,
        items_data,
        new_category_id=new_category_id,
        new_subcategory_id=new_subcategory_id
    )

    # ========== 编码项固化保护 ==========
    # 当模板已有活跃配置时，已有编码项不可删除、不可重排、不可取消编码
    active_configs = [c for c in template.configurations if c.deleted_at is None]
    if active_configs:
        # 收集已有的编码项（use_in_code=True）信息
        locked_code_items = {}
        for item in template.items:
            if item.use_in_code:
                locked_code_items[item.spec_dict_id] = {
                    'name': item.spec_dict.name if item.spec_dict else str(item.spec_dict_id),
                    'display_order': item.display_order,
                    'code_length': item.code_length,
                }

        if locked_code_items:
            max_locked_order = max(info['display_order'] for info in locked_code_items.values())

            # 构建新提交的编码项映射
            new_items_by_def_id = {}
            for idx, item_data in enumerate(items_data):
                def_id = item_data.get('definition_id')
                if def_id:
                    new_items_by_def_id[def_id] = item_data

            violations = []

            for def_id, locked_info in locked_code_items.items():
                name = locked_info['name']

                # 检查编码项是否被删除
                if def_id not in new_items_by_def_id:
                    violations.append(_('编码项「%(name)s」已被配置引用，不可删除', name=name))
                    continue

                new_data = new_items_by_def_id[def_id]

                # 检查 use_in_code 是否被取消
                if not new_data.get('use_in_code', False):
                    violations.append(_('编码项「%(name)s」已被配置引用，不可取消编码', name=name))

                # 检查 display_order 是否被更改
                new_order = new_data.get('display_order', 0)
                if new_order != locked_info['display_order']:
                    violations.append(_('编码项「%(name)s」已被配置引用，不可更改顺序（当前: %(old)s, 提交: %(new)s）',
                                        name=name, old=locked_info['display_order'], new=new_order))

                # 检查 code_length 是否被更改
                new_length = new_data.get('code_length', 1)
                if new_length != locked_info['code_length']:
                    violations.append(_('编码项「%(name)s」已被配置引用，不可更改编码长度', name=name))

            # 检查新增编码项的 display_order 必须在已有编码项之后
            for def_id, item_data in new_items_by_def_id.items():
                if item_data.get('use_in_code', False) and def_id not in locked_code_items:
                    new_order = item_data.get('display_order', 0)
                    if new_order <= max_locked_order:
                        definition = SpecificationDictionary.query.get(def_id)
                        name = definition.name if definition else str(def_id)
                        violations.append(
                            _('新编码项「%(name)s」的顺序 %(order)s 必须大于已有编码项最大顺序 %(max)s',
                              name=name, order=new_order, max=max_locked_order))

            if violations:
                return jsonify({
                    'success': False,
                    'code_protection_error': True,
                    'violations': violations,
                    'message': _('模板已有 %(count)s 个活跃配置，编码项受固化保护', count=len(active_configs))
                }), 409

    # 如果有结构性变更且当前版本已被使用过（绑定过）
    if structural_check['has_changes'] and template.version_first_used_at is not None:
        # 检查前端是否确认了版本升级
        if not data.get('confirm_version_upgrade'):
            new_version = increment_version(template.version)
            return jsonify({
                'success': False,
                'require_version_upgrade': True,
                'current_version': template.version,
                'new_version': new_version,
                'changes': structural_check['changes'],
                'message': _('检测到结构性变更，需要确认是否升级版本')
            }), 409  # Conflict

        # 用户确认升级，递增版本
        template.version = increment_version(template.version)
        template.version_first_used_at = None  # 新版本未绑定

    # 更新基本信息
    template.model = data['model']
    template.name = data.get('name')
    template.name_en = data.get('name_en')
    template.description = data.get('description')
    # 只在用户明确要求或版本未被绑定时才直接更新版本号
    if not structural_check['has_changes'] or template.version_first_used_at is None:
        template.version = data.get('version', template.version)
    template.category_id = new_category_id
    template.subcategory_id = new_subcategory_id

    # 删除不再需要的规格项
    existing_definition_ids = {item['definition_id'] for item in items_data if item.get('definition_id')}
    for item in template.items:
        if item.spec_dict_id not in existing_definition_ids:
            # 在删除前，为锁定配置的规格值保存孤立项信息
            for cv in item.config_values:
                if cv.configuration and cv.configuration.mn_locked:
                    # 保存规格信息，以便删除后仍能显示
                    cv.orphaned_spec_name = item.spec_dict.name if item.spec_dict else None
                    cv.orphaned_spec_name_en = item.spec_dict.name_en if item.spec_dict else None
                    cv.orphaned_spec_unit = item.spec_dict.unit if item.spec_dict else None
                    cv.orphaned_category_id = item.spec_dict.category_id if item.spec_dict else None
            db.session.delete(item)

    # 更新或添加规格项
    for idx, item_data in enumerate(items_data):
        if not item_data.get('definition_id'):
            continue

        dict_id = item_data['definition_id']

        # 如果参与编码且有通用值，确保有编码映射
        use_in_code = item_data.get('use_in_code', False)
        general_value = item_data.get('general_value')
        options = item_data.get('options') or {}
        if use_in_code and general_value:
            options = ensure_code_for_value(options, general_value)

        # 查找已存在的规格项
        existing_item = SpecTemplateItem.query.filter_by(
            template_id=template.id,
            spec_dict_id=dict_id
        ).first()

        if existing_item:
            # 更新
            existing_item.spec_dict_id = dict_id  # 确保新FK已设置
            existing_item.general_value = item_data.get('general_value')
            existing_item.test_condition_id = item_data.get('test_condition_id')
            existing_item.test_condition_text = item_data.get('test_condition_text')
            existing_item.test_method_id = item_data.get('test_method_id')
            existing_item.test_method_text = item_data.get('test_method_text')
            existing_item.is_required = item_data.get('is_required', False)
            existing_item.options = options
            existing_item.display_order = item_data.get('display_order', idx)
            existing_item.use_in_code = use_in_code
            existing_item.code_length = item_data.get('code_length', 1)
        else:
            # 新增
            new_item = SpecTemplateItem(
                template_id=template.id,
                spec_dict_id=dict_id,
                general_value=item_data.get('general_value'),
                test_condition_id=item_data.get('test_condition_id'),
                test_condition_text=item_data.get('test_condition_text'),
                test_method_id=item_data.get('test_method_id'),
                test_method_text=item_data.get('test_method_text'),
                is_required=item_data.get('is_required', False),
                options=options,
                display_order=item_data.get('display_order', idx),
                use_in_code=use_in_code,
                code_length=item_data.get('code_length', 1)
            )
            db.session.add(new_item)
            db.session.flush()  # 获取新 ID

            # 查找匹配的孤立配置值（同名规格），重新关联
            definition = SpecificationDictionary.query.get(dict_id)
            if definition:
                config_ids = [c.id for c in template.configurations]
                if config_ids:
                    orphaned_values = ProductConfigValue.query.filter(
                        ProductConfigValue.template_item_id.is_(None),
                        ProductConfigValue.orphaned_spec_name == definition.name,
                        ProductConfigValue.configuration_id.in_(config_ids)
                    ).all()

                    for cv in orphaned_values:
                        cv.template_item_id = new_item.id
                        # 清除孤立标记
                        cv.orphaned_spec_name = None
                        cv.orphaned_spec_name_en = None
                        cv.orphaned_spec_unit = None
                        cv.orphaned_category_id = None

    db.session.commit()

    # 构建返回数据，包含 items 以便前端更新
    result_data = template.to_dict()
    result_data['items'] = [item.to_dict() for item in template.items]

    return jsonify({
        'success': True,
        'message': _('规格模板更新成功'),
        'data': result_data
    })


@spec_template_bp.route('/api/<int:template_id>', methods=['DELETE'])
@login_required
@permission_required('product_code', 'delete')
def api_delete_template(template_id):
    """API: 删除规格模板（软删除）"""
    template = SpecTemplate.query.get_or_404(template_id)
    _check_template_owner(template)

    # 检查是否有研发产品在使用
    dev_products_using = DevProduct.query.filter_by(spec_template_id=template_id).first()
    if dev_products_using:
        return jsonify({
            'success': False,
            'message': _('该模板已被研发产品使用，无法删除')
        }), 400

    template.deleted_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('规格模板删除成功')
    })


@spec_template_bp.route('/api/<int:template_id>/copy', methods=['POST'])
@login_required
@permission_required('product_code', 'create')
def api_copy_template(template_id):
    """API: 复制规格模板"""
    template = SpecTemplate.query.get_or_404(template_id)
    _check_template_owner(template)
    data = request.get_json() or {}

    # 生成新的型号名称
    new_model = data.get('model', f"{template.model}_copy")

    # 检查新型号是否已存在
    if SpecTemplate.query.filter(SpecTemplate.model == new_model, SpecTemplate.deleted_at.is_(None)).first():
        return jsonify({'success': False, 'message': _('该型号的规格模板已存在')}), 400

    # 创建新模板
    new_template = SpecTemplate(
        model=new_model,
        name=data.get('name', f"{template.name or ''} (副本)".strip()),
        name_en=template.name_en,
        description=template.description,
        version='V1.0',
        created_by=current_user.id
    )
    db.session.add(new_template)
    db.session.flush()

    # 复制规格项
    for item in template.items:
        new_item = SpecTemplateItem(
            template_id=new_template.id,
            spec_dict_id=item.spec_dict_id,
            definition_id=None,
            general_value=item.general_value,
            test_condition_id=item.test_condition_id,
            test_condition_text=item.test_condition_text,
            test_method_id=item.test_method_id,
            test_method_text=item.test_method_text,
            is_required=item.is_required,
            options=item.options,
            display_order=item.display_order,
            use_in_code=item.use_in_code,
            code_length=item.code_length
        )
        db.session.add(new_item)

    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('规格模板复制成功'),
        'data': new_template.to_dict()
    })


@spec_template_bp.route('/api/definitions-by-category')
@login_required
@permission_required('product_code', 'view')
def api_definitions_by_category():
    """API: 获取按分类组织的规格定义"""
    categories = SpecCategory.query.filter_by(is_active=True).order_by(SpecCategory.display_order).all()
    definitions = SpecificationDictionary.query.filter_by(is_active=True).order_by(
        SpecificationDictionary.category_id, SpecificationDictionary.display_order
    ).all()

    result = []
    for category in categories:
        cat_definitions = [d.to_dict() for d in definitions if d.category_id == category.id]
        result.append({
            'category': category.to_dict(),
            'definitions': cat_definitions
        })

    return jsonify({
        'success': True,
        'data': result
    })


# ==================== 配置版本管理 API ====================

@spec_template_bp.route('/<int:template_id>/spec-config')
@login_required
@permission_required('product_code', 'view')
def spec_config_matrix_page(template_id):
    """矩阵式规格配置页面"""
    template = SpecTemplate.query.get_or_404(template_id)
    _check_template_owner(template)

    # 获取选中的配置ID（从配置版本管理页面跳转时传入）
    selected_config_id = request.args.get('config_id', type=int)
    categories = SpecCategory.query.filter_by(is_active=True).order_by(SpecCategory.display_order).all()

    # 获取模板中的规格项，按分类组织
    items_by_category = {}
    all_items = []
    for item in template.items:
        all_items.append(item)
        if item.spec_dict and item.spec_dict.category_id:
            cat_id = item.spec_dict.category_id
            if cat_id not in items_by_category:
                items_by_category[cat_id] = []
            items_by_category[cat_id].append(item)

    # 获取所有活跃的配置版本
    configurations = [c for c in template.configurations if c.deleted_at is None]

    # 构建规格值矩阵
    config_values_matrix = {}
    for config in configurations:
        config_values_matrix[config.id] = {}
        for cv in config.config_values:
            config_values_matrix[config.id][cv.template_item_id] = cv.value

    # 查找锁定配置中的"孤立"规格项（已从模板删除但配置中仍有值）
    current_item_ids = {item.id for item in all_items}
    orphaned_items = {}  # {template_item_id: SpecTemplateItem}
    orphaned_items_by_category = {}  # {category_id: [items]}

    # 锁定配置中"新增"的规格项（锁定后添加到模板的规格）
    # {config_id: set(item_ids)} - 这些规格项在该配置锁定后才添加，不应显示默认值
    new_items_after_lock = {}

    for config in configurations:
        if config.mn_locked:  # 只检查锁定的配置
            # 获取 MN 编码生成时间
            mn_generated_at = None
            if config.code_rule_snapshot and isinstance(config.code_rule_snapshot, dict):
                generated_at_str = config.code_rule_snapshot.get('generated_at')
                if generated_at_str:
                    try:
                        mn_generated_at = datetime.fromisoformat(generated_at_str.replace('Z', '+00:00'))
                    except (ValueError, AttributeError):
                        pass

            # 找出在 MN 生成后才添加的规格项
            new_item_ids = set()
            if mn_generated_at:
                for item in all_items:
                    if item.created_at and item.created_at > mn_generated_at:
                        new_item_ids.add(item.id)
            new_items_after_lock[config.id] = new_item_ids

            # 查找孤立规格值（template_item 已被删除或不在当前模板中）
            for cv in config.config_values:
                # 情况1: template_item_id 为 NULL（规格项已被删除）
                if cv.template_item_id is None and cv.orphaned_spec_name:
                    # 使用唯一标识符（基于规格名称和分类）
                    orphan_key = f"orphan_{cv.orphaned_spec_name}_{cv.orphaned_category_id}"
                    if orphan_key not in orphaned_items:
                        # 创建虚拟的孤立项信息
                        orphaned_items[orphan_key] = {
                            'id': orphan_key,
                            'is_virtual': True,  # 标记为虚拟项
                            'spec_name': cv.orphaned_spec_name,
                            'spec_name_en': cv.orphaned_spec_name_en,
                            'spec_unit': cv.orphaned_spec_unit,
                            'category_id': cv.orphaned_category_id
                        }
                        # 按分类组织
                        cat_id = cv.orphaned_category_id
                        if cat_id:
                            if cat_id not in orphaned_items_by_category:
                                orphaned_items_by_category[cat_id] = []
                            orphaned_items_by_category[cat_id].append(orphaned_items[orphan_key])
                    # 记录孤立项的值到矩阵中
                    if config.id not in config_values_matrix:
                        config_values_matrix[config.id] = {}
                    config_values_matrix[config.id][orphan_key] = cv.value

                # 情况2: template_item_id 不在当前模板中（规格项仍存在但被移除了）
                elif cv.template_item_id and cv.template_item_id not in current_item_ids:
                    if cv.template_item_id not in orphaned_items and cv.template_item:
                        item = cv.template_item
                        orphaned_items[cv.template_item_id] = item
                        # 按分类组织
                        if item.spec_dict and item.spec_dict.category_id:
                            cat_id = item.spec_dict.category_id
                            if cat_id not in orphaned_items_by_category:
                                orphaned_items_by_category[cat_id] = []
                            orphaned_items_by_category[cat_id].append(item)

    # 加载指标选项（用于配置矩阵下拉选择）
    # 必须用 spec_dict_id 加载 SpecificationDictionary，而非 definition_id（指向旧表 spec_definitions）
    spec_dict_ids = list({item.spec_dict_id for item in all_items if item.spec_dict_id})
    if spec_dict_ids:
        dict_objs = SpecificationDictionary.query.filter(
            SpecificationDictionary.id.in_(spec_dict_ids)
        ).all()
        definition_indicators = _load_definition_indicators(dict_objs)
    else:
        definition_indicators = {}

    # 构建 MN 编码相关数据
    # 获取参与编码的规格项（按 display_order 排序）
    code_items = sorted(
        [item for item in all_items if item.use_in_code],
        key=lambda x: x.display_order
    )
    code_items_data = []
    # 编码位置映射：item.id -> (位置序号, 起始位置, 编码长度)
    # MN 编码结构：[区域码1位] + [分类码1位] + [子分类码1位] + [规格编码...] + [校验位1位]
    code_position_map = {}
    current_pos = 4  # 前3位是区域+分类+子分类，从第4位开始
    for idx, item in enumerate(code_items):
        # 编码映射直接使用 item.options（编辑模板时已生成）
        code_options = item.options or {}
        code_length = item.code_length or 1

        code_items_data.append({
            'id': item.id,
            'name': item.spec_dict.name if item.spec_dict else '',
            'code_length': code_length,
            'options': code_options,
            'display_order': item.display_order
        })

        # 记录位置信息：第几个编码项，在 MN 编码中的位置
        code_position_map[item.id] = {
            'index': idx + 1,  # 第几个编码项（从1开始）
            'start_pos': current_pos,  # 在 MN 编码中的起始位置
            'length': code_length  # 编码长度
        }
        current_pos += code_length

    return render_template(
        'spec_template/tw_spec_config_matrix.html',
        template=template,
        categories=categories,
        items_by_category=items_by_category,
        all_items=all_items,
        configurations=configurations,
        config_values_matrix=config_values_matrix,
        config_status=CONFIG_STATUS,
        regions=REGIONS,
        code_items_data=code_items_data,
        code_position_map=code_position_map,
        selected_config_id=selected_config_id,
        orphaned_items_by_category=orphaned_items_by_category,
        definition_indicators=definition_indicators
    )


@spec_template_bp.route('/<int:template_id>/configurations')
@login_required
@permission_required('product_code', 'view')
def configurations_page(template_id):
    """配置版本管理页面"""
    template = SpecTemplate.query.get_or_404(template_id)
    _check_template_owner(template)
    categories = SpecCategory.query.filter_by(is_active=True).order_by(SpecCategory.display_order).all()

    # 获取模板中的规格项，按分类组织
    items_by_category = {}
    for item in template.items:
        if item.spec_dict and item.spec_dict.category_id:
            cat_id = item.spec_dict.category_id
            if cat_id not in items_by_category:
                items_by_category[cat_id] = []
            items_by_category[cat_id].append(item)

    # 获取销售区域选项（来自 product_code_fields 的 origin_location，去重）
    sales_regions = db.session.query(
        ProductCodeField.code, ProductCodeField.name
    ).filter_by(field_type='origin_location').distinct().all()
    region_options = [{'value': r.code, 'label': f'{r.name} ({r.code})'} for r in sales_regions]

    # 转换 config_status 为字典格式
    status_options = [{'value': code, 'label': name} for code, name in CONFIG_STATUS]

    return render_template(
        'spec_template/tw_configurations.html',
        template=template,
        categories=categories,
        items_by_category=items_by_category,
        config_status=CONFIG_STATUS,
        status_options=status_options,
        region_options=region_options
    )


@spec_template_bp.route('/api/<int:template_id>/configurations')
@login_required
@permission_required('product_code', 'view')
def api_list_configurations(template_id):
    """API: 获取模板的配置版本列表"""
    template = SpecTemplate.query.get_or_404(template_id)
    _check_template_owner(template)
    configurations = ProductConfiguration.query.filter(
        ProductConfiguration.template_id == template_id,
        ProductConfiguration.deleted_at.is_(None)
    ).order_by(ProductConfiguration.display_order.asc()).all()

    return jsonify({
        'success': True,
        'data': [c.to_dict() for c in configurations]
    })


@spec_template_bp.route('/api/<int:template_id>/configurations', methods=['POST'])
@login_required
@permission_required('product_code', 'create')
def api_create_configuration(template_id):
    """API: 创建配置版本"""
    template = SpecTemplate.query.get_or_404(template_id)
    _check_template_owner(template)
    data = request.get_json()

    # 验证必填字段
    if not data.get('config_code'):
        return jsonify({'success': False, 'message': _('配置编码不能为空')}), 400

    # 检查配置编码是否重复（排除已软删除的记录）
    existing = ProductConfiguration.query.filter(
        ProductConfiguration.template_id == template_id,
        ProductConfiguration.config_code == data['config_code'],
        ProductConfiguration.deleted_at.is_(None)
    ).first()
    if existing:
        return jsonify({'success': False, 'message': _('该配置编码已存在')}), 400

    # 自动查询区域名称
    region_code = data.get('region')
    region_name = data.get('region_name')
    if region_code and not region_name:
        field = ProductCodeField.query.filter_by(field_type='origin_location', code=region_code).first()
        if field:
            region_name = field.name

    # 创建配置版本
    config = ProductConfiguration(
        template_id=template_id,
        config_code=data['config_code'],
        region=region_code,
        region_name=region_name,
        status=data.get('status', 'development'),
        power_spec=data.get('power_spec'),
        power_cord_type=data.get('power_cord_type'),
        notes=data.get('notes'),
        template_version=template.version,
        created_by=current_user.id
    )
    db.session.add(config)
    db.session.flush()

    # 构建前端传入的覆盖值映射
    values_data = data.get('values', [])
    override_map = {}
    for value_data in values_data:
        tid = value_data.get('template_item_id')
        if tid and value_data.get('value'):
            override_map[tid] = value_data

    # 为每个模版规格项创建配置值（快照通用值，前端覆盖优先）
    for item in template.items:
        override = override_map.get(item.id)
        value = override['value'] if override else item.general_value
        if value:
            config_value = ProductConfigValue(
                configuration_id=config.id,
                template_item_id=item.id,
                value=value,
                notes=override.get('notes') if override else None
            )
            db.session.add(config_value)

    # 生成 MN 编码（在添加配置值之后）
    config.mn_code = generate_mn_code(config, template)

    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('配置版本创建成功'),
        'data': config.to_dict()
    })


@spec_template_bp.route('/api/configurations/<int:config_id>', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def api_get_configuration(config_id):
    """API: 获取配置版本详情"""
    try:
        config = ProductConfiguration.query.get_or_404(config_id)
        _check_config_owner(config)

        # 获取配置值
        config_data = config.to_dict()
        config_data['values'] = {}
        for cv in config.config_values:
            if cv.template_item_id is None:
                continue
            config_data['values'][cv.template_item_id] = {
                'id': cv.id,
                'value': cv.value,
                'notes': cv.notes
            }

        return jsonify({
            'success': True,
            'data': config_data
        })
    except Exception as e:
        logger.error(f"获取配置版本详情失败 (config_id={config_id}): {e}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'获取配置版本详情失败: {str(e)}'
        }), 500


@spec_template_bp.route('/api/configurations/<int:config_id>', methods=['PUT'])
@login_required
@permission_required('product_code', 'edit')
def api_update_configuration(config_id):
    """API: 更新配置版本"""
    config = ProductConfiguration.query.get_or_404(config_id)
    _check_config_owner(config)
    data = request.get_json()

    # 检查是否锁定（可生产/停产状态）
    is_locked = config.mn_locked

    # 锁定状态下不更新开发代号和区域
    if not is_locked:
        # 验证必填字段
        if not data.get('config_code'):
            return jsonify({'success': False, 'message': _('配置编码不能为空')}), 400

        # 检查配置编码是否重复（排除自己和已删除的）
        existing = ProductConfiguration.query.filter(
            ProductConfiguration.template_id == config.template_id,
            ProductConfiguration.config_code == data['config_code'],
            ProductConfiguration.id != config_id,
            ProductConfiguration.deleted_at.is_(None)
        ).first()
        if existing:
            return jsonify({'success': False, 'message': _('该配置编码已存在')}), 400

        # 更新开发代号和区域
        config.config_code = data['config_code']
        region_code = data.get('region')
        region_name = data.get('region_name')
        if region_code and not region_name:
            field = ProductCodeField.query.filter_by(field_type='origin_location', code=region_code).first()
            if field:
                region_name = field.name
        config.region = region_code
        config.region_name = region_name

    # 更新其他基本信息（状态、备注等始终可以更新）
    config.status = data.get('status', config.status)
    config.power_spec = data.get('power_spec')
    config.power_cord_type = data.get('power_cord_type')
    config.notes = data.get('notes')

    # 更新规格值（只有当前端明确传入 values 时才处理）
    values_data = data.get('values')
    if values_data is not None:
        existing_item_ids = {v['template_item_id'] for v in values_data if v.get('template_item_id') and v.get('value')}

        # 删除不再需要的规格值（只有明确传入 values 时才删除）
        for cv in config.config_values:
            if cv.template_item_id not in existing_item_ids:
                db.session.delete(cv)

    # 更新或添加规格值
    for value_data in (values_data or []):
        if not value_data.get('template_item_id'):
            continue
        if not value_data.get('value'):
            continue

        existing_cv = ProductConfigValue.query.filter_by(
            configuration_id=config.id,
            template_item_id=value_data['template_item_id']
        ).first()

        if existing_cv:
            existing_cv.value = value_data['value']
            existing_cv.notes = value_data.get('notes')
        else:
            new_cv = ProductConfigValue(
                configuration_id=config.id,
                template_item_id=value_data['template_item_id'],
                value=value_data['value'],
                notes=value_data.get('notes')
            )
            db.session.add(new_cv)

    # 锁定状态下不重新生成 MN 编码
    if not is_locked:
        config.mn_code = generate_mn_code(config)

    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('配置版本更新成功'),
        'data': config.to_dict()
    })


@spec_template_bp.route('/api/configurations/<int:config_id>', methods=['DELETE'])
@login_required
@permission_required('product_code', 'delete')
def api_delete_configuration(config_id):
    """API: 删除配置版本（软删除）"""
    config = ProductConfiguration.query.get_or_404(config_id)
    _check_config_owner(config)

    # 锁定状态（可生产/停产）不允许删除
    if config.mn_locked:
        return jsonify({
            'success': False,
            'message': _('可生产或停产状态的配置版本不能删除')
        }), 403

    # 检查是否有产品在使用
    # TODO: 检查产品库中是否有产品引用此配置

    config.deleted_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('配置版本删除成功')
    })


@spec_template_bp.route('/api/configurations/<int:config_id>/copy', methods=['POST'])
@login_required
@permission_required('product_code', 'create')
def api_copy_configuration(config_id):
    """API: 复制配置版本"""
    config = ProductConfiguration.query.get_or_404(config_id)
    _check_config_owner(config)
    data = request.get_json() or {}

    # 生成新的配置编码
    new_code = data.get('config_code', f"{config.config_code}_copy")

    # 检查新编码是否已存在（排除已软删除的记录）
    if ProductConfiguration.query.filter(
        ProductConfiguration.template_id == config.template_id,
        ProductConfiguration.config_code == new_code,
        ProductConfiguration.deleted_at.is_(None)
    ).first():
        return jsonify({'success': False, 'message': _('该配置编码已存在')}), 400

    # 创建新配置版本
    template = config.template
    region_code = data.get('region', config.region)
    region_name = data.get('region_name', config.region_name)
    if region_code and not region_name:
        field = ProductCodeField.query.filter_by(field_type='origin_location', code=region_code).first()
        if field:
            region_name = field.name
    new_config = ProductConfiguration(
        template_id=config.template_id,
        config_code=new_code,
        region=region_code,
        region_name=region_name,
        status='development',
        mn_code=None,  # MN编码需要重新生成
        power_spec=config.power_spec,
        power_cord_type=config.power_cord_type,
        notes=config.notes,
        template_version=template.version if template else None,
        created_by=current_user.id
    )
    db.session.add(new_config)
    db.session.flush()

    # 复制源配置的规格值快照
    for cv in config.config_values:
        if cv.value:
            new_cv = ProductConfigValue(
                configuration_id=new_config.id,
                template_item_id=cv.template_item_id,
                value=cv.value,
                notes=cv.notes
            )
            db.session.add(new_cv)

    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('配置版本复制成功'),
        'data': new_config.to_dict()
    })


@spec_template_bp.route('/api/<int:template_id>/configurations/order', methods=['PUT'])
@login_required
@permission_required('product_code', 'edit')
def api_update_configurations_order(template_id):
    """API: 更新配置版本排序"""
    template = SpecTemplate.query.get_or_404(template_id)
    _check_template_owner(template)
    data = request.get_json() or {}
    order_list = data.get('order', [])  # [id1, id2, id3...]

    if not order_list:
        return jsonify({'success': False, 'message': _('排序数据不能为空')}), 400

    # 批量更新排序
    for index, config_id in enumerate(order_list):
        config = ProductConfiguration.query.get(config_id)
        if config and config.template_id == template_id:
            config.display_order = index

    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('排序已保存')
    })


@spec_template_bp.route('/api/configurations/<int:config_id>/values', methods=['PUT'])
@login_required
@permission_required('product_code', 'edit')
def api_update_config_values(config_id):
    """API: 批量更新配置版本的规格值"""
    config = ProductConfiguration.query.get_or_404(config_id)
    _check_config_owner(config)
    data = request.get_json()
    values_data = data.get('values', [])
    save_all = data.get('save_all', False)  # 是否保存所有规格值（包括默认值）

    # 收集需要更新编码映射的模板项
    items_to_update_options = {}  # {template_item_id: value}

    # 构建传入值的映射 {template_item_id: value_data}
    values_map = {}
    for value_data in values_data:
        template_item_id = value_data.get('template_item_id')
        if template_item_id:
            values_map[template_item_id] = value_data

    # 如果 save_all=true，获取模板的所有规格项
    if save_all:
        template = config.template
        all_items = template.items if template else []
        # 确保所有模板项都在处理列表中
        for item in all_items:
            if item.id not in values_map:
                values_map[item.id] = {'template_item_id': item.id, 'value': None}

    # 更新规格值
    for template_item_id, value_data in values_map.items():
        value = value_data.get('value')

        existing_cv = ProductConfigValue.query.filter_by(
            configuration_id=config.id,
            template_item_id=template_item_id
        ).first()

        if value:
            # 有值（用户输入或默认值）则更新或创建
            if existing_cv:
                existing_cv.value = value
                existing_cv.notes = value_data.get('notes')
            else:
                new_cv = ProductConfigValue(
                    configuration_id=config.id,
                    template_item_id=template_item_id,
                    value=value,
                    notes=value_data.get('notes')
                )
                db.session.add(new_cv)
            # 记录需要检查编码映射的项
            items_to_update_options[template_item_id] = value
        # 如果连默认值都没有，就不保存

    # 为新值分配编码并更新 SpecTemplateItem.options
    for template_item_id, value in items_to_update_options.items():
        # 刷新获取最新数据，避免并发请求读取到旧的 options
        template_item = db.session.query(SpecTemplateItem).filter_by(id=template_item_id).with_for_update().first()
        if template_item and template_item.use_in_code and value:
            # 确保值有编码映射
            updated_options = ensure_code_for_value(template_item.options, value)
            if updated_options != template_item.options:
                template_item.options = updated_options
                db.session.flush()  # 立即写入，让后续请求能看到

    # 检查 MN 编码是否锁定（可生产/停产状态）
    mn_locked = config.mn_locked

    if not mn_locked:
        # 未锁定：重新生成 MN 编码
        new_mn_code = generate_mn_code(config)

        # 检查 MN 编码全局唯一性
        from app.routes.product import check_mn_code_duplicate
        duplicate_check = check_mn_code_duplicate(new_mn_code, exclude_config_id=config.id)
        if duplicate_check['is_duplicate']:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error_type': 'mn_code_conflict',
                'message': _('MN 编码冲突'),
                'mn_code': new_mn_code,
                'conflict': duplicate_check
            }), 409

        config.mn_code = new_mn_code

    db.session.commit()

    # 收集更新后的 options（用于前端同步 CODE_ITEMS）
    updated_item_options = {}
    for template_item_id in items_to_update_options.keys():
        template_item = SpecTemplateItem.query.get(template_item_id)
        if template_item and template_item.use_in_code:
            updated_item_options[template_item_id] = template_item.options

    return jsonify({
        'success': True,
        'message': _('规格值更新成功') if not mn_locked else _('规格值更新成功（MN编码已锁定）'),
        'mn_code': config.mn_code,
        'mn_locked': mn_locked,
        'updated_options': updated_item_options  # 返回更新后的 options
    })


# ==================== 导入导出 API ====================

@spec_template_bp.route('/api/download-import-template')
@login_required
@permission_required('product_code', 'view')
def api_download_import_template():
    """API: 下载规格模板导入模板Excel"""
    from app.services.spec_import_service import SpecImportService

    try:
        excel_content = SpecImportService.generate_import_template()

        return send_file(
            io.BytesIO(excel_content),
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='规格模板导入模板.xlsx'
        )
    except Exception as e:
        return jsonify({
            'success': False,
            'message': _('生成模板失败: %(error)s', error=str(e))
        }), 500


@spec_template_bp.route('/api/import-create', methods=['POST'])
@login_required
@permission_required('product_code', 'create')
def api_import_create_template():
    """API: 通过Excel导入创建规格模板"""
    from app.services.spec_import_service import SpecImportService

    # 检查文件
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'message': _('请选择要上传的文件')
        }), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({
            'success': False,
            'message': _('请选择要上传的文件')
        }), 400

    # 验证文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({
            'success': False,
            'message': _('请上传Excel文件（.xlsx或.xls格式）')
        }), 400

    # 调用导入服务
    result = SpecImportService.import_template(file, current_user.id)

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


# ========== 配置导出导入 API ==========

@spec_template_bp.route('/api/<int:template_id>/export-configurations')
@login_required
@permission_required('product_code', 'view')
def api_export_configurations(template_id):
    """API: 导出配置矩阵（只导出未锁定的配置）"""
    from app.services.spec_import_service import SpecImportService

    template = SpecTemplate.query.get_or_404(template_id)
    _check_template_owner(template)

    try:
        excel_data = SpecImportService.export_configurations(template_id)
        filename = f"{template.model}_配置矩阵.xlsx" if template else "配置矩阵.xlsx"

        return Response(
            excel_data,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            headers={'Content-Disposition': f'attachment; filename*=UTF-8\'\'{quote(filename)}'}
        )
    except ValueError as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 400
    except Exception as e:
        logger.error(f"导出配置失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': _('导出失败: %(error)s', error=str(e))
        }), 500


@spec_template_bp.route('/api/<int:template_id>/import-configurations', methods=['POST'])
@login_required
@permission_required('product_code', 'edit')
def api_import_configurations(template_id):
    """API: 导入配置矩阵"""
    template = SpecTemplate.query.get_or_404(template_id)
    _check_template_owner(template)

    from app.services.spec_import_service import SpecImportService

    # 检查文件
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'message': _('请选择要上传的文件')
        }), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({
            'success': False,
            'message': _('请选择要上传的文件')
        }), 400

    # 验证文件类型
    if not file.filename.endswith(('.xlsx', '.xls')):
        return jsonify({
            'success': False,
            'message': _('请上传Excel文件（.xlsx或.xls格式）')
        }), 400

    # 调用导入服务
    result = SpecImportService.import_configurations(file, template_id, current_user.id)

    if result['success']:
        return jsonify(result)
    else:
        return jsonify(result), 400


# ============================================================
# 规格附件管理 API
# ============================================================

ALLOWED_ATTACHMENT_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf'}
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10MB


def validate_attachment_file(file):
    """验证附件文件"""
    if not file or file.filename == '':
        return False, _('请选择要上传的文件')

    # 检查文件类型
    file_type = file.content_type
    if file_type not in ALLOWED_ATTACHMENT_TYPES:
        return False, _('不支持的文件类型，仅支持图片和PDF')

    # 检查文件大小
    file.seek(0, 2)
    file_size = file.tell()
    file.seek(0)

    if file_size > MAX_ATTACHMENT_SIZE:
        return False, _('文件大小超过限制（最大10MB）')

    return True, None


@spec_template_bp.route('/api/item/<int:item_id>/attachments', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def api_get_item_attachments(item_id):
    """获取模板规格项的附件列表（默认附件）"""
    item = SpecTemplateItem.query.get_or_404(item_id)
    _check_template_owner(item.template)

    attachments = SpecAttachment.query.filter_by(
        template_item_id=item_id
    ).order_by(SpecAttachment.display_order, SpecAttachment.created_at).all()

    return jsonify({
        'success': True,
        'attachments': [att.to_dict() for att in attachments],
        'is_fallback': False
    })


@spec_template_bp.route('/api/item/<int:item_id>/attachments', methods=['POST'])
@login_required
@permission_required('product_code', 'edit')
def api_upload_item_attachment(item_id):
    """上传模板规格项附件（默认附件）"""
    from app.utils.supabase_client import get_supabase_client

    item = SpecTemplateItem.query.get_or_404(item_id)
    _check_template_owner(item.template)

    # 检查该规格是否允许附件
    if not item.spec_dict or not item.spec_dict.allow_attachment:
        return jsonify({
            'success': False,
            'message': _('该规格项不允许上传附件')
        }), 400

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': _('请选择要上传的文件')}), 400

    file = request.files['file']
    valid, error_msg = validate_attachment_file(file)
    if not valid:
        return jsonify({'success': False, 'message': error_msg}), 400

    try:
        # 获取文件信息
        original_filename = file.filename
        file_type = file.content_type
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)

        # 上传到 Supabase
        supabase_client = get_supabase_client()
        result = supabase_client.upload_file(
            object_id=item.template_id,
            file=file,
            filename=original_filename,
            file_type='spec_attachment',
            bucket_type='invoice',  # 复用现有桶
            business_type=f'spec_template/item_{item_id}'
        )

        if not result or not result.get('url'):
            return jsonify({'success': False, 'message': _('上传失败')}), 500

        # 获取当前最大排序号
        max_order = db.session.query(db.func.max(SpecAttachment.display_order)).filter_by(
            template_item_id=item_id
        ).scalar() or 0

        # 创建附件记录
        attachment = SpecAttachment(
            template_item_id=item_id,
            file_name=original_filename,
            file_path=result.get('url'),
            file_type=file_type,
            file_size=file_size,
            display_order=max_order + 1,
            uploaded_by=current_user.id
        )
        db.session.add(attachment)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': _('上传成功'),
            'data': attachment.to_dict()
        })

    except Exception as e:
        logger.error(f"上传规格附件失败: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'{_("上传失败")}: {str(e)}'}), 500


@spec_template_bp.route('/api/attachment/<int:attachment_id>', methods=['DELETE'])
@login_required
@permission_required('product_code', 'edit')
def api_delete_attachment(attachment_id):
    """删除规格附件"""
    from app.utils.supabase_client import get_supabase_client

    attachment = SpecAttachment.query.get_or_404(attachment_id)
    # 通过 template_item 或 config_value 反查模板 owner
    if attachment.template_item:
        _check_template_owner(attachment.template_item.template)
    elif attachment.config_value and attachment.config_value.configuration:
        _check_config_owner(attachment.config_value.configuration)

    try:
        # 删除云端文件
        if attachment.file_path:
            supabase_client = get_supabase_client()
            supabase_client.delete_file_by_url(attachment.file_path, bucket_type='invoice')

        # 删除数据库记录
        db.session.delete(attachment)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': _('删除成功')
        })

    except Exception as e:
        logger.error(f"删除规格附件失败: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'{_("删除失败")}: {str(e)}'}), 500


@spec_template_bp.route('/api/attachment/<int:attachment_id>/preview')
@login_required
@permission_required('product_code', 'view')
def api_preview_attachment(attachment_id):
    """预览/下载规格附件"""
    import requests

    attachment = SpecAttachment.query.get_or_404(attachment_id)
    if attachment.template_item:
        _check_template_owner(attachment.template_item.template)
    elif attachment.config_value and attachment.config_value.configuration:
        _check_config_owner(attachment.config_value.configuration)

    url = attachment.file_path
    filename = attachment.file_name
    file_type = attachment.file_type or 'application/octet-stream'

    force_download = request.args.get('download') == '1'

    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            encoded_filename = quote(filename, safe='')
            disposition_type = 'attachment' if force_download else 'inline'

            headers = {
                'Content-Type': file_type,
                'Content-Disposition': f"{disposition_type}; filename*=UTF-8''{encoded_filename}"
            }

            return Response(response.content, headers=headers)
        else:
            return jsonify({'success': False, 'message': _('文件获取失败')}), 404

    except Exception as e:
        logger.error(f"预览规格附件失败: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@spec_template_bp.route('/api/config/<int:config_id>/item/<int:item_id>/attachments', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def api_get_config_attachments(config_id, item_id):
    """获取配置版本的规格附件（带回退逻辑）"""
    config = ProductConfiguration.query.get_or_404(config_id)
    _check_config_owner(config)
    item = SpecTemplateItem.query.get_or_404(item_id)

    # 1. 先查找配置级附件
    config_value = ProductConfigValue.query.filter_by(
        configuration_id=config_id,
        template_item_id=item_id
    ).first()

    config_attachments = []
    if config_value:
        config_attachments = SpecAttachment.query.filter_by(
            config_value_id=config_value.id
        ).order_by(SpecAttachment.display_order, SpecAttachment.created_at).all()

    # 2. 查找模板级（默认）附件
    template_attachments = SpecAttachment.query.filter_by(
        template_item_id=item_id
    ).order_by(SpecAttachment.display_order, SpecAttachment.created_at).all()

    # 3. 确定使用哪些附件
    is_fallback = len(config_attachments) == 0 and len(template_attachments) > 0

    if config_attachments:
        # 有配置级附件，使用配置附件
        attachments = [att.to_dict() for att in config_attachments]
    else:
        # 回退到模板默认附件，并标记
        attachments = []
        for att in template_attachments:
            att_dict = att.to_dict()
            att_dict['is_fallback'] = True
            attachments.append(att_dict)

    return jsonify({
        'success': True,
        'attachments': attachments,
        'is_fallback': is_fallback
    })


@spec_template_bp.route('/api/config/<int:config_id>/item/<int:item_id>/attachments', methods=['POST'])
@login_required
@permission_required('product_code', 'edit')
def api_upload_config_attachment(config_id, item_id):
    """上传配置版本的规格附件"""
    from app.utils.supabase_client import get_supabase_client

    config = ProductConfiguration.query.get_or_404(config_id)
    _check_config_owner(config)
    item = SpecTemplateItem.query.get_or_404(item_id)

    # 检查配置是否锁定
    if config.mn_locked:
        return jsonify({
            'success': False,
            'message': _('该配置版本已锁定，无法修改')
        }), 400

    # 检查该规格是否允许附件
    if not item.spec_dict or not item.spec_dict.allow_attachment:
        return jsonify({
            'success': False,
            'message': _('该规格项不允许上传附件')
        }), 400

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': _('请选择要上传的文件')}), 400

    file = request.files['file']
    valid, error_msg = validate_attachment_file(file)
    if not valid:
        return jsonify({'success': False, 'message': error_msg}), 400

    try:
        # 确保有 ProductConfigValue 记录
        config_value = ProductConfigValue.query.filter_by(
            configuration_id=config_id,
            template_item_id=item_id
        ).first()

        if not config_value:
            # 创建配置值记录（使用通用值作为初始值）
            config_value = ProductConfigValue(
                configuration_id=config_id,
                template_item_id=item_id,
                value=item.general_value
            )
            db.session.add(config_value)
            db.session.flush()  # 获取 ID

        # 获取文件信息
        original_filename = file.filename
        file_type = file.content_type
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)

        # 上传到 Supabase
        supabase_client = get_supabase_client()
        result = supabase_client.upload_file(
            object_id=config_id,
            file=file,
            filename=original_filename,
            file_type='spec_attachment',
            bucket_type='invoice',
            business_type=f'spec_config/item_{item_id}'
        )

        if not result or not result.get('url'):
            return jsonify({'success': False, 'message': _('上传失败')}), 500

        # 获取当前最大排序号
        max_order = db.session.query(db.func.max(SpecAttachment.display_order)).filter_by(
            config_value_id=config_value.id
        ).scalar() or 0

        # 创建附件记录
        attachment = SpecAttachment(
            config_value_id=config_value.id,
            file_name=original_filename,
            file_path=result.get('url'),
            file_type=file_type,
            file_size=file_size,
            display_order=max_order + 1,
            uploaded_by=current_user.id
        )
        db.session.add(attachment)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': _('上传成功'),
            'data': attachment.to_dict()
        })

    except Exception as e:
        logger.error(f"上传配置附件失败: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'message': f'{_("上传失败")}: {str(e)}'}), 500


@spec_template_bp.route('/api/attachments/count', methods=['POST'])
@login_required
@permission_required('product_code', 'view')
def api_get_attachments_count():
    """批量获取附件数量（用于矩阵显示）

    请求格式: { items: [{ item_id: int, config_id: int|null }, ...] }
    返回格式: { success: true, counts: { "itemId_configId": { count: int, is_fallback: bool }, ... } }
    """
    data = request.get_json()
    items = data.get('items', [])

    if not items:
        return jsonify({'success': True, 'counts': {}})

    # 收集所有需要查询的 item_id
    item_ids = set()
    config_ids = set()
    for item in items:
        item_ids.add(item.get('item_id'))
        if item.get('config_id'):
            config_ids.add(item.get('config_id'))

    # 1. 查询所有模板级附件数量
    template_counts = {}
    if item_ids:
        counts = db.session.query(
            SpecAttachment.template_item_id,
            db.func.count(SpecAttachment.id)
        ).filter(
            SpecAttachment.template_item_id.in_(item_ids)
        ).group_by(SpecAttachment.template_item_id).all()

        for item_id, count in counts:
            template_counts[item_id] = count

    # 2. 查询所有配置级附件数量
    config_counts = {}  # {(config_id, item_id): count}
    if config_ids and item_ids:
        # 获取相关的 config_value_id
        config_values = db.session.query(
            ProductConfigValue.id,
            ProductConfigValue.configuration_id,
            ProductConfigValue.template_item_id
        ).filter(
            ProductConfigValue.configuration_id.in_(config_ids),
            ProductConfigValue.template_item_id.in_(item_ids)
        ).all()

        cv_map = {}  # {cv_id: (config_id, item_id)}
        for cv_id, config_id, item_id in config_values:
            cv_map[cv_id] = (config_id, item_id)

        if cv_map:
            counts = db.session.query(
                SpecAttachment.config_value_id,
                db.func.count(SpecAttachment.id)
            ).filter(
                SpecAttachment.config_value_id.in_(cv_map.keys())
            ).group_by(SpecAttachment.config_value_id).all()

            for cv_id, count in counts:
                key = cv_map[cv_id]
                config_counts[key] = count

    # 3. 构建返回结果
    result = {}
    for item in items:
        item_id = item.get('item_id')
        config_id = item.get('config_id')

        if config_id:
            # 配置级：检查是否有配置附件，否则回退到模板附件
            key = f"{item_id}_{config_id}"
            config_count = config_counts.get((config_id, item_id), 0)
            template_count = template_counts.get(item_id, 0)

            if config_count > 0:
                result[key] = {'count': config_count, 'is_fallback': False}
            elif template_count > 0:
                result[key] = {'count': template_count, 'is_fallback': True}
            else:
                result[key] = {'count': 0, 'is_fallback': False}
        else:
            # 模板级
            key = f"{item_id}_template"
            result[key] = {'count': template_counts.get(item_id, 0), 'is_fallback': False}

    return jsonify({
        'success': True,
        'counts': result
    })
