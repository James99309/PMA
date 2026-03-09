"""
规格字典管理路由
提供规格字典的增删改查API
"""
from flask import Blueprint, request, jsonify, current_app
from flask_login import login_required, current_user
from app import db
from app.models.product_code import SpecificationDictionary, SpecificationOption, ProductCodeFieldOption, ProductCodeField, ProductCodeFieldValue, ProductCode
from app.models.product import Product
from app.decorators import permission_required
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text
from datetime import datetime

# 创建蓝图
spec_dict_bp = Blueprint('spec_dictionary', __name__, url_prefix='/api/spec-dictionary')


def _is_option_used_in_snapshot(option_value):
    """检查指标值是否在任何 ProductConfiguration 的 code_rule_snapshot 中被引用"""
    result = db.session.execute(text("""
        SELECT 1 FROM product_configurations pc
        WHERE pc.code_rule_snapshot IS NOT NULL
          AND EXISTS (
            SELECT 1 FROM jsonb_array_elements(pc.code_rule_snapshot::jsonb->'code_items') item
            WHERE item->>'value' = :option_value
          )
        LIMIT 1
    """), {'option_value': option_value}).first()
    return result is not None


def _batch_check_snapshot_usage(option_values):
    """批量检查哪些指标值在 code_rule_snapshot 中被引用，返回被引用的值集合"""
    if not option_values:
        return set()
    result = db.session.execute(text("""
        SELECT DISTINCT item->>'value' as used_value
        FROM product_configurations pc,
             jsonb_array_elements(pc.code_rule_snapshot::jsonb->'code_items') item
        WHERE pc.code_rule_snapshot IS NOT NULL
          AND item->>'value' = ANY(:option_values)
    """), {'option_values': list(option_values)}).fetchall()
    return {r.used_value for r in result}


@spec_dict_bp.route('', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def get_spec_list():
    """
    获取规格字典列表

    Query参数:
        active_only: bool - 是否只返回启用的规格（可选）

    返回:
        {
            "success": true,
            "data": [...],
            "total": 15
        }
    """
    try:
        # 是否只返回启用的规格
        active_only = request.args.get('active_only', 'false').lower() == 'true'

        # 构建查询
        query = SpecificationDictionary.query

        if active_only:
            query = query.filter_by(is_active=True)

        # 按排序字段升序排列（拖拽排序），没有排序字段时按创建时间
        specs = query.order_by(
            SpecificationDictionary.display_order.asc(),
            SpecificationDictionary.created_at.desc()
        ).all()

        # 转换为字典列表，添加指标数量
        data = []
        for spec in specs:
            spec_dict = spec.to_dict()
            spec_dict['option_count'] = spec.options.count()  # 添加指标数量
            data.append(spec_dict)

        return jsonify({
            'success': True,
            'data': data,
            'total': len(data)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取规格列表失败: {str(e)}'
        }), 500


@spec_dict_bp.route('', methods=['POST'])
@login_required
@permission_required('product_code', 'edit')
def create_spec():
    """
    创建新规格

    请求体:
        {
            "name": "规格名称",
            "unit": "单位" (可选),
            "is_active": true
        }

    返回:
        {
            "success": true,
            "message": "创建成功",
            "data": {...}
        }
    """
    try:
        data = request.get_json()

        # 验证必填字段
        if not data.get('name') or not data.get('name').strip():
            return jsonify({
                'success': False,
                'message': '规格名称不能为空'
            }), 400

        # 去除首尾空格
        name = data['name'].strip()
        unit = data.get('unit', '').strip() if data.get('unit') else None
        is_active = data.get('is_active', True)

        # 检查名称是否已存在
        existing = SpecificationDictionary.query.filter_by(name=name).first()
        if existing:
            return jsonify({
                'success': False,
                'message': f'规格名称"{name}"已存在'
            }), 400

        # 创建新规格
        new_spec = SpecificationDictionary(
            name=name,
            unit=unit if unit else None,
            is_active=is_active,
            created_at=datetime.utcnow()
        )

        db.session.add(new_spec)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '规格创建成功',
            'data': new_spec.to_dict()
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': '规格名称已存在（唯一性约束）'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建规格失败: {str(e)}'
        }), 500


@spec_dict_bp.route('/<int:spec_id>', methods=['PUT'])
@login_required
@permission_required('product_code', 'edit')
def update_spec(spec_id):
    """
    更新规格

    路径参数:
        spec_id: int - 规格ID

    请求体:
        {
            "name": "新规格名称",
            "unit": "新单位",
            "is_active": true
        }

    返回:
        {
            "success": true,
            "message": "更新成功",
            "data": {...}
        }
    """
    try:
        # 查找规格
        spec = SpecificationDictionary.query.get(spec_id)
        if not spec:
            return jsonify({
                'success': False,
                'message': '规格不存在'
            }), 404

        data = request.get_json()

        # 验证必填字段
        if 'name' in data:
            name = data['name'].strip()
            if not name:
                return jsonify({
                    'success': False,
                    'message': '规格名称不能为空'
                }), 400

            # 检查名称是否与其他规格重复
            existing = SpecificationDictionary.query.filter(
                SpecificationDictionary.name == name,
                SpecificationDictionary.id != spec_id
            ).first()

            if existing:
                return jsonify({
                    'success': False,
                    'message': f'规格名称"{name}"已被其他规格使用'
                }), 400

            spec.name = name

        # 更新单位
        if 'unit' in data:
            unit = data['unit'].strip() if data['unit'] else None
            spec.unit = unit if unit else None

        # 更新启用状态
        if 'is_active' in data:
            spec.is_active = data['is_active']

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '规格更新成功',
            'data': spec.to_dict()
        })

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': '规格名称已存在（唯一性约束）'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新规格失败: {str(e)}'
        }), 500


@spec_dict_bp.route('/<int:spec_id>', methods=['DELETE'])
@login_required
@permission_required('product_code', 'edit')
def delete_spec(spec_id):
    """
    删除规格

    路径参数:
        spec_id: int - 规格ID

    返回:
        {
            "success": true,
            "message": "删除成功"
        }
    """
    try:
        # 查找规格
        spec = SpecificationDictionary.query.get(spec_id)
        if not spec:
            return jsonify({
                'success': False,
                'message': '规格不存在'
            }), 404

        # TODO: 检查是否有产品正在使用此规格
        # 如果有关联数据，可以选择：
        # 1. 禁止删除，提示用户
        # 2. 软删除（设置is_active=False）
        # 3. 级联删除相关数据

        spec_name = spec.name
        db.session.delete(spec)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'规格"{spec_name}"已删除'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除规格失败: {str(e)}'
        }), 500


@spec_dict_bp.route('/<int:spec_id>/toggle', methods=['PUT'])
@login_required
@permission_required('product_code', 'edit')
def toggle_spec_status(spec_id):
    """
    切换规格的启用/停用状态

    路径参数:
        spec_id: int - 规格ID

    返回:
        {
            "success": true,
            "message": "已启用" 或 "已停用",
            "data": {...}
        }
    """
    try:
        # 查找规格
        spec = SpecificationDictionary.query.get(spec_id)
        if not spec:
            return jsonify({
                'success': False,
                'message': '规格不存在'
            }), 404

        # 切换状态
        spec.is_active = not spec.is_active
        db.session.commit()

        status_text = '已启用' if spec.is_active else '已停用'

        return jsonify({
            'success': True,
            'message': f'规格"{spec.name}"{status_text}',
            'data': spec.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'切换状态失败: {str(e)}'
        }), 500


@spec_dict_bp.route('/update-order', methods=['POST'])
@login_required
@permission_required('product_code', 'edit')
def update_spec_order():
    """
    更新规格字典排序序号（用于拖拽排序）

    请求体:
        {
            "items": [
                {"id": 1, "order": 1},
                {"id": 2, "order": 2},
                ...
            ]
        }

    返回:
        {
            "success": true,
            "message": "排序更新成功"
        }
    """
    try:
        data = request.get_json()
        if not data or 'items' not in data:
            return jsonify({
                'success': False,
                'message': '无效的数据格式'
            }), 400

        items = data['items']

        # 批量更新排序
        for item in items:
            spec_id = item.get('id')
            new_order = item.get('order')

            if spec_id is None or new_order is None:
                continue

            # 查找规格字典记录
            spec = SpecificationDictionary.query.get(spec_id)
            if spec:
                spec.display_order = new_order

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '排序更新成功'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新排序失败: {str(e)}'
        }), 500


# ============================================================
# 规格指标（SpecificationOption）相关API
# ============================================================

def generate_smart_code(spec_id, value):
    """智能生成指标编码

    编码规则：
    1. 基于首字符生成编码（数字开头取数字，字母开头取大写字母）
    2. 类型一致性：同一规格的第一个指标决定编码类型
    3. 避免重复：首字符被占用时，取后续有效字符
    4. 排除0：0保留给未选择指标时的填充
    5. 备用策略：字符用完时切换类型

    Args:
        spec_id: 规格字典ID
        value: 指标值（如 "400-450"）

    Returns:
        str: 生成的编码字符
    """
    # 1. 获取该规格已使用的编码
    used_codes = {opt.code for opt in SpecificationOption.query.filter_by(spec_id=spec_id).all()}

    # 2. 判断该规格的编码类型（基于第一个指标）
    first_option = SpecificationOption.query.filter_by(spec_id=spec_id)\
        .order_by(SpecificationOption.id).first()
    code_type = _determine_code_type(first_option.code) if first_option else None

    # 3. 从指标值提取候选字符
    candidates = _extract_candidates(value, code_type)

    # 4. 找到第一个未使用的字符（排除0）
    for char in candidates:
        if char not in used_codes and char != '0':
            return char

    # 5. 候选用完，使用备用字符集
    fallback_chars = _get_fallback_chars(code_type)
    for char in fallback_chars:
        if char not in used_codes and char != '0':
            return char

    return None  # 全部用完（理论上不会发生，共35个字符）


def _determine_code_type(code):
    """判断编码类型"""
    if code and code.isdigit():
        return 'digit'
    elif code and code.isalpha():
        return 'letter'
    return None


def _extract_candidates(value, preferred_type=None):
    """从指标值提取候选编码字符

    Args:
        value: 指标值
        preferred_type: 优先类型 ('digit' 或 'letter')

    Returns:
        list: 候选字符列表，按优先级排序
    """
    digits = []
    letters = []

    for char in str(value):
        if char.isdigit() and char != '0':  # 排除0
            if char not in digits:
                digits.append(char)
        elif char.isalpha() and char.isascii():
            upper_char = char.upper()
            if upper_char not in letters:
                letters.append(upper_char)

    # 根据首字符或优先类型决定顺序
    if preferred_type == 'digit':
        return digits + letters
    elif preferred_type == 'letter':
        return letters + digits
    else:
        # 根据值的首个有效字符决定
        first_char = next((c for c in str(value) if c.isalnum() and c.isascii()), None)
        if first_char and first_char.isdigit():
            return digits + letters
        else:
            return letters + digits


def _get_fallback_chars(code_type):
    """获取备用字符集

    Args:
        code_type: 当前类型 ('digit' 或 'letter')

    Returns:
        list: 备用字符列表
    """
    if code_type == 'digit':
        # 数字用完，返回字母（按数字映射）
        return list('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    else:
        # 字母用完，返回数字
        return list('123456789')


@spec_dict_bp.route('/<int:spec_id>/options', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def get_spec_options(spec_id):
    """
    获取规格的指标列表

    路径参数:
        spec_id: int - 规格ID

    Query参数:
        active_only: bool - 是否只返回启用的指标（可选）

    返回:
        {
            "success": true,
            "data": [...],
            "spec": {...}
        }
    """
    try:
        # 查找规格
        spec = SpecificationDictionary.query.get(spec_id)
        if not spec:
            return jsonify({
                'success': False,
                'message': '规格不存在'
            }), 404

        # 是否只返回启用的指标
        active_only = request.args.get('active_only', 'false').lower() == 'true'

        # 构建查询
        query = SpecificationOption.query.filter_by(spec_id=spec_id)

        if active_only:
            query = query.filter_by(is_active=True)

        # 按position排序
        options = query.order_by(SpecificationOption.position.asc()).all()

        # 为每个选项添加 is_used 字段（批量检查 code_rule_snapshot 引用）
        all_values = {opt.value for opt in options}
        snapshot_used_values = _batch_check_snapshot_usage(all_values)

        options_data = []
        for opt in options:
            opt_dict = opt.to_dict()
            # 检查是否被产品字段选项引用 或 被 code_rule_snapshot 引用
            field_used = ProductCodeFieldOption.query.filter_by(
                spec_option_id=opt.id
            ).first() is not None
            opt_dict['is_used'] = field_used or (opt.value in snapshot_used_values)
            options_data.append(opt_dict)

        return jsonify({
            'success': True,
            'data': options_data,
            'spec': spec.to_dict()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取指标列表失败: {str(e)}'
        }), 500


@spec_dict_bp.route('/<int:spec_id>/preview-code', methods=['POST'])
@login_required
@permission_required('product_code', 'edit')
def preview_option_code(spec_id):
    """
    预览自动生成的编码（不创建指标）

    路径参数:
        spec_id: int - 规格ID

    请求体:
        {
            "value": "指标值"
        }

    返回:
        {
            "success": true,
            "code": "生成的编码",
            "message": "编码预览"
        }
    """
    try:
        # 查找规格
        spec = SpecificationDictionary.query.get(spec_id)
        if not spec:
            return jsonify({
                'success': False,
                'message': '规格不存在'
            }), 404

        data = request.get_json()
        value = data.get('value', '').strip() if data.get('value') else ''

        if not value:
            return jsonify({
                'success': True,
                'code': '',
                'message': '请输入指标值'
            })

        # 检查指标值是否已存在
        existing = SpecificationOption.query.filter_by(
            spec_id=spec_id,
            value=value
        ).first()
        if existing:
            return jsonify({
                'success': False,
                'code': existing.code,
                'message': f'指标值"{value}"已存在，编码为: {existing.code}',
                'exists': True
            })

        # 生成编码
        code = generate_smart_code(spec_id, value)
        if not code:
            return jsonify({
                'success': False,
                'code': '',
                'message': '无法生成唯一编码，编码空间已用尽'
            })

        return jsonify({
            'success': True,
            'code': code,
            'message': f'建议编码: {code}'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'生成编码失败: {str(e)}'
        }), 500


@spec_dict_bp.route('/<int:spec_id>/options', methods=['POST'])
@login_required
@permission_required('product_code', 'edit')
def create_spec_option(spec_id):
    """
    创建新指标（自动生成智能编码）

    路径参数:
        spec_id: int - 规格ID

    请求体:
        {
            "value": "指标值",
            "code": "编码" (可选，不提供则自动生成),
            "description": "描述" (可选)
        }

    返回:
        {
            "success": true,
            "message": "创建成功",
            "data": {...}
        }
    """
    try:
        # 查找规格
        spec = SpecificationDictionary.query.get(spec_id)
        if not spec:
            return jsonify({
                'success': False,
                'message': '规格不存在'
            }), 404

        data = request.get_json()

        # 验证必填字段
        if not data.get('value') or not data.get('value').strip():
            return jsonify({
                'success': False,
                'message': '指标值不能为空'
            }), 400

        value = data['value'].strip()

        # 检查指标值是否已存在
        existing = SpecificationOption.query.filter_by(
            spec_id=spec_id,
            value=value
        ).first()
        if existing:
            return jsonify({
                'success': False,
                'message': f'指标值"{value}"在该规格下已存在'
            }), 400

        # 获取或生成编码
        code = data.get('code', '').strip() if data.get('code') else None
        if not code:
            code = generate_smart_code(spec_id, value)
            if not code:
                return jsonify({
                    'success': False,
                    'message': '无法生成唯一编码，编码空间已用尽'
                }), 400
        else:
            # 检查编码是否已被使用
            existing_code = SpecificationOption.query.filter_by(
                spec_id=spec_id,
                code=code
            ).first()
            if existing_code:
                return jsonify({
                    'success': False,
                    'message': f'编码"{code}"在该规格下已被使用'
                }), 400

        # 获取当前最大position
        max_position = db.session.query(db.func.max(SpecificationOption.position))\
            .filter_by(spec_id=spec_id).scalar() or 0

        # 创建新指标
        new_option = SpecificationOption(
            spec_id=spec_id,
            value=value,
            code=code,
            description=data.get('description', '').strip() if data.get('description') else None,
            is_active=True,
            position=max_position + 1,
            created_at=datetime.utcnow()
        )

        db.session.add(new_option)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'指标创建成功，编码: {code}',
            'data': new_option.to_dict()
        }), 201

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': '指标值或编码已存在（唯一性约束）'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'创建指标失败: {str(e)}'
        }), 500


@spec_dict_bp.route('/options/<int:option_id>', methods=['PUT'])
@login_required
@permission_required('product_code', 'edit')
def update_spec_option(option_id):
    """
    更新指标

    路径参数:
        option_id: int - 指标ID

    请求体:
        {
            "value": "新指标值",
            "code": "新编码",
            "description": "新描述",
            "is_active": true
        }

    返回:
        {
            "success": true,
            "message": "更新成功",
            "data": {...}
        }
    """
    try:
        # 查找指标
        option = SpecificationOption.query.get(option_id)
        if not option:
            return jsonify({
                'success': False,
                'message': '指标不存在'
            }), 404

        # 检查是否被产品使用（字段选项引用 或 code_rule_snapshot 引用）
        is_used = (ProductCodeFieldOption.query.filter_by(spec_option_id=option_id).first() is not None
                   or _is_option_used_in_snapshot(option.value))

        data = request.get_json()

        # 如果被使用，编码不可修改（value 允许修改，配合同步功能）
        if is_used and 'code' in data:
            return jsonify({
                'success': False,
                'message': '此指标已被产品使用，编码不可修改'
            }), 400

        # 更新指标值
        if 'value' in data:
            value = data['value'].strip()
            if not value:
                return jsonify({
                    'success': False,
                    'message': '指标值不能为空'
                }), 400

            # 检查是否与其他指标重复
            existing = SpecificationOption.query.filter(
                SpecificationOption.spec_id == option.spec_id,
                SpecificationOption.value == value,
                SpecificationOption.id != option_id
            ).first()

            if existing:
                return jsonify({
                    'success': False,
                    'message': f'指标值"{value}"在该规格下已存在'
                }), 400

            option.value = value

        # 更新编码
        if 'code' in data:
            code = data['code'].strip()
            if not code:
                return jsonify({
                    'success': False,
                    'message': '编码不能为空'
                }), 400

            # 检查编码是否与其他指标重复
            existing = SpecificationOption.query.filter(
                SpecificationOption.spec_id == option.spec_id,
                SpecificationOption.code == code,
                SpecificationOption.id != option_id
            ).first()

            if existing:
                return jsonify({
                    'success': False,
                    'message': f'编码"{code}"在该规格下已被使用'
                }), 400

            option.code = code

        # 更新描述
        if 'description' in data:
            option.description = data['description'].strip() if data['description'] else None

        # 更新启用状态
        if 'is_active' in data:
            option.is_active = data['is_active']

        db.session.commit()

        return jsonify({
            'success': True,
            'message': '指标更新成功',
            'data': option.to_dict()
        })

    except IntegrityError:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': '指标值或编码已存在（唯一性约束）'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'更新指标失败: {str(e)}'
        }), 500


@spec_dict_bp.route('/options/<int:option_id>', methods=['DELETE'])
@login_required
@permission_required('product_code', 'edit')
def delete_spec_option(option_id):
    """
    删除指标

    路径参数:
        option_id: int - 指标ID

    返回:
        {
            "success": true,
            "message": "删除成功"
        }
    """
    try:
        # 查找指标
        option = SpecificationOption.query.get(option_id)
        if not option:
            return jsonify({
                'success': False,
                'message': '指标不存在'
            }), 404

        # 检查是否被产品使用（字段选项引用 或 code_rule_snapshot 引用）
        is_used = (ProductCodeFieldOption.query.filter_by(spec_option_id=option_id).first() is not None
                   or _is_option_used_in_snapshot(option.value))
        if is_used:
            return jsonify({
                'success': False,
                'message': '此指标已被产品使用，无法删除'
            }), 400

        option_value = option.value
        db.session.delete(option)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'指标"{option_value}"已删除'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'删除指标失败: {str(e)}'
        }), 500


@spec_dict_bp.route('/options/<int:option_id>/toggle', methods=['PUT'])
@login_required
@permission_required('product_code', 'edit')
def toggle_spec_option_status(option_id):
    """
    切换指标的启用/停用状态

    路径参数:
        option_id: int - 指标ID

    返回:
        {
            "success": true,
            "message": "已启用" 或 "已停用",
            "data": {...}
        }
    """
    try:
        # 查找指标
        option = SpecificationOption.query.get(option_id)
        if not option:
            return jsonify({
                'success': False,
                'message': '指标不存在'
            }), 404

        # 切换状态
        option.is_active = not option.is_active
        db.session.commit()

        status_text = '已启用' if option.is_active else '已停用'

        return jsonify({
            'success': True,
            'message': f'指标"{option.value}"{status_text}',
            'data': option.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'切换状态失败: {str(e)}'
        }), 500


@spec_dict_bp.route('/options/<int:option_id>/products', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def get_option_products(option_id):
    """
    获取使用该规格指标的产品列表

    路径参数:
        option_id: int - 指标ID

    返回:
        {
            "success": true,
            "data": [
                {
                    "id": 产品ID,
                    "name": "产品名称",
                    "model": "型号",
                    "product_code": "编号",
                    "spec_description": "规格描述"
                },
                ...
            ]
        }
    """
    try:
        # 查找指标
        option = SpecificationOption.query.get(option_id)
        if not option:
            return jsonify({
                'success': False,
                'message': '指标不存在'
            }), 404

        # 查询引用此指标的分类/子分类
        # ProductCodeFieldOption.spec_option_id -> SpecificationOption
        from app.models.product_code import ProductSubcategory, ProductCategory

        # 查找引用此规格指标的所有 ProductCodeFieldOption
        field_options = ProductCodeFieldOption.query.filter(
            ProductCodeFieldOption.spec_option_id == option_id
        ).all()

        # 收集分类/子分类信息
        category_ids = set()  # 分类级引用
        subcategory_ids = set()  # 子分类级引用
        result_data = []

        for fo in field_options:
            if fo.subcategory_id:
                # 子分类级选项 - 直接引用子分类
                if fo.subcategory_id not in subcategory_ids:
                    subcategory_ids.add(fo.subcategory_id)
            elif fo.field and fo.field.category_id:
                # 分类级选项 - 通过字段获取分类
                if fo.field.category_id not in category_ids:
                    category_ids.add(fo.field.category_id)

        # 处理分类级引用 - 获取分类下所有子分类
        for cat_id in category_ids:
            category = ProductCategory.query.get(cat_id)
            if category:
                # 获取该分类下的所有子分类
                subcategories = ProductSubcategory.query.filter(
                    ProductSubcategory.category_id == cat_id
                ).all()
                for subcat in subcategories:
                    if subcat.id not in subcategory_ids:
                        subcategory_ids.add(subcat.id)
                        product_count = Product.query.filter(
                            Product.subcategory_id == subcat.id
                        ).count()
                        result_data.append({
                            'id': subcat.id,
                            'name': subcat.name,
                            'category_name': category.name,
                            'product_count': product_count,
                            'source': 'category'  # 标记来源
                        })

        # 处理子分类级引用
        for subcat_id in subcategory_ids:
            # 检查是否已添加（避免重复）
            if any(item['id'] == subcat_id for item in result_data):
                continue
            subcategory = ProductSubcategory.query.get(subcat_id)
            if subcategory:
                # 通过 category_id 查询分类名称
                category_name = ''
                if subcategory.category_id:
                    category = ProductCategory.query.get(subcategory.category_id)
                    category_name = category.name if category else ''
                product_count = Product.query.filter(
                    Product.subcategory_id == subcategory.id
                ).count()
                result_data.append({
                    'id': subcategory.id,
                    'name': subcategory.name,
                    'category_name': category_name,
                    'product_count': product_count,
                    'source': 'subcategory'  # 标记来源
                })

        # 查询 code_rule_snapshot 中引用了此指标值的产品配置
        configs = db.session.execute(text("""
            SELECT pc.id, pc.mn_code, pc.status, st.model as product_model
            FROM product_configurations pc
            JOIN spec_templates st ON pc.template_id = st.id
            WHERE pc.code_rule_snapshot IS NOT NULL
              AND EXISTS (
                SELECT 1 FROM jsonb_array_elements(pc.code_rule_snapshot::jsonb->'code_items') item
                WHERE item->>'value' = :option_value
              )
            ORDER BY st.model, pc.mn_code
        """), {'option_value': option.value}).fetchall()

        config_data = [{
            'id': c.id,
            'mn_code': c.mn_code,
            'status': c.status,
            'product_model': c.product_model
        } for c in configs]

        return jsonify({
            'success': True,
            'data': result_data,
            'configurations': config_data
        })

    except Exception as e:
        import traceback
        current_app.logger.error(f"获取引用列表失败: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'获取引用列表失败: {str(e)}'
        }), 500


@spec_dict_bp.route('/options/by-name/<path:spec_name>', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def get_options_by_spec_name(spec_name):
    """
    通过规格名称获取指标列表

    路径参数:
        spec_name: str - 规格名称

    Query参数:
        active_only: bool - 是否只返回启用的指标（可选）
        exclude_subcategory_id: int - 排除已在此子分类中使用的指标（可选）
        field_id: int - 字段ID，与 exclude_subcategory_id 配合使用（可选）

    返回:
        {
            "success": true,
            "data": [...],
            "spec": {...}
        }
    """
    from app.models.product_code import ProductCodeFieldOption

    try:
        # 查找规格
        spec = SpecificationDictionary.query.filter_by(name=spec_name).first()
        if not spec:
            return jsonify({
                'success': False,
                'message': f'规格"{spec_name}"不存在'
            }), 404

        # 是否只返回启用的指标
        active_only = request.args.get('active_only', 'false').lower() == 'true'

        # 排除参数
        exclude_subcategory_id = request.args.get('exclude_subcategory_id', type=int)
        field_id = request.args.get('field_id', type=int)

        # 构建查询
        query = SpecificationOption.query.filter_by(spec_id=spec.id)

        if active_only:
            query = query.filter_by(is_active=True)

        # 排除已在指定子分类中使用的指标
        if exclude_subcategory_id and field_id:
            # 获取已使用的 spec_option_id 列表
            used_spec_option_ids = db.session.query(ProductCodeFieldOption.spec_option_id).filter(
                ProductCodeFieldOption.field_id == field_id,
                ProductCodeFieldOption.subcategory_id == exclude_subcategory_id,
                ProductCodeFieldOption.spec_option_id.isnot(None)
            ).all()
            used_ids = [row[0] for row in used_spec_option_ids]

            if used_ids:
                query = query.filter(~SpecificationOption.id.in_(used_ids))

        # 按position排序
        options = query.order_by(SpecificationOption.position.asc()).all()

        # 为每个选项添加 is_used 字段（批量检查 code_rule_snapshot 引用）
        all_values = {opt.value for opt in options}
        snapshot_used_values = _batch_check_snapshot_usage(all_values)

        options_data = []
        for opt in options:
            opt_dict = opt.to_dict()
            # 检查是否被产品字段选项引用 或 被 code_rule_snapshot 引用
            field_used = ProductCodeFieldOption.query.filter_by(
                spec_option_id=opt.id
            ).first() is not None
            opt_dict['is_used'] = field_used or (opt.value in snapshot_used_values)
            options_data.append(opt_dict)

        return jsonify({
            'success': True,
            'data': options_data,
            'spec': spec.to_dict()
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取指标列表失败: {str(e)}'
        }), 500


@spec_dict_bp.route('/tree', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def get_spec_tree():
    """
    获取规格分类树形结构（SpecCategory → SpecificationDictionary）

    Query参数:
        subcategory_id: int - 如提供则交叉匹配 ProductCodeField 获取 field_id（可选）
        exclude: str - 逗号分隔的已有规格名，排除掉（可选）

    返回:
        {
            "success": true,
            "data": [
                {
                    "id": 1, "name": "射频性能", "name_en": "RF Performance",
                    "specs": [
                        {"id": 10, "name": "频率范围", "name_en": "Frequency Range", "unit": "MHz", "field_id": 5},
                        {"id": 11, "name": "发射功率", "name_en": "TX Power", "unit": "dBm", "field_id": null}
                    ]
                }
            ]
        }
    """
    from app.models.spec_template import SpecCategory

    try:
        subcategory_id = request.args.get('subcategory_id', type=int)
        exclude_str = request.args.get('exclude', '')
        exclude_names = set(n.strip() for n in exclude_str.split(',') if n.strip()) if exclude_str else set()

        # 1. 查询所有活跃分类
        categories = SpecCategory.query.filter_by(is_active=True).order_by(SpecCategory.display_order).all()

        # 2. 查询所有活跃规格定义（统一主表）
        definitions = SpecificationDictionary.query.filter_by(is_active=True).order_by(
            SpecificationDictionary.category_id, SpecificationDictionary.display_order
        ).all()

        # 3. 如有 subcategory_id，构建 {name: field_id} 映射
        field_id_map = {}
        if subcategory_id:
            fields_data = ProductCodeField.get_all_fields_for_subcategory(subcategory_id)
            all_fields = fields_data['inherited'] + fields_data['own']
            for f in all_fields:
                field_id_map[f.name] = f.id

        # 4. 按 category 分组，排除 exclude 中的名称
        cat_specs = {}
        for d in definitions:
            if d.name in exclude_names:
                continue
            if d.category_id not in cat_specs:
                cat_specs[d.category_id] = []
            cat_specs[d.category_id].append({
                'id': d.id,
                'name': d.name,
                'name_en': d.name_en,
                'unit': d.unit,
                'field_id': field_id_map.get(d.name)
            })

        # 5. 只返回有 specs 的分类
        result = []
        for cat in categories:
            specs = cat_specs.get(cat.id, [])
            if specs:
                result.append({
                    'id': cat.id,
                    'name': cat.name,
                    'name_en': cat.name_en,
                    'specs': specs
                })

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取规格树失败: {str(e)}'
        }), 500


@spec_dict_bp.route('/available-for-subcategory/<int:subcategory_id>', methods=['GET'])
@login_required
@permission_required('product_code', 'view')
def get_available_specs_for_subcategory(subcategory_id):
    """
    获取指定子分类的可用非编码规格

    返回该子分类继承的分类级字段 + 子分类级字段中，
    field_type='spec' 且 use_in_code=False 的规格。

    路径参数:
        subcategory_id: int - 子分类ID

    返回:
        {
            "success": true,
            "data": [
                {
                    "id": 1,  // SpecificationDictionary ID
                    "name": "规格名称",
                    "unit": "单位",
                    "field_id": 10  // ProductCodeField ID
                },
                ...
            ]
        }
    """
    try:
        from app.models.product_code import ProductCodeField, ProductSubcategory

        # 验证子分类存在
        subcategory = ProductSubcategory.query.get(subcategory_id)
        if not subcategory:
            return jsonify({
                'success': False,
                'message': '子分类不存在'
            }), 404

        # 获取该子分类的所有字段（继承 + 自有）
        fields_data = ProductCodeField.get_all_fields_for_subcategory(subcategory_id)
        all_fields = fields_data['inherited'] + fields_data['own']

        # 过滤：只要 field_type='spec' 且 use_in_code=False 的非编码规格
        non_coded_spec_fields = [
            f for f in all_fields
            if f.field_type == 'spec' and not f.use_in_code
        ]

        # 收集结果，关联 SpecificationDictionary
        result = []
        for field in non_coded_spec_fields:
            # 查找对应的规格字典条目
            spec_dict = SpecificationDictionary.query.filter_by(name=field.name).first()
            if spec_dict:
                result.append({
                    'id': spec_dict.id,  # 规格字典ID，用于获取选项
                    'name': spec_dict.name,
                    'unit': spec_dict.unit or '',
                    'field_id': field.id
                })
            else:
                # 如果规格字典中没有对应条目，也返回字段信息
                result.append({
                    'id': None,
                    'name': field.name,
                    'unit': '',
                    'field_id': field.id
                })

        return jsonify({
            'success': True,
            'data': result
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取可用规格失败: {str(e)}'
        }), 500
