"""
规格字典管理路由
提供规格字典的增删改查API
"""
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.product_code import SpecificationDictionary
from app.decorators import permission_required
from sqlalchemy.exc import IntegrityError
from datetime import datetime

# 创建蓝图
spec_dict_bp = Blueprint('spec_dictionary', __name__, url_prefix='/api/spec-dictionary')


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

        # 转换为字典列表
        data = [spec.to_dict() for spec in specs]

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
