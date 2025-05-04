from flask import request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from app.api.v1 import api_v1_bp
from app.api.v1.utils import api_response, jwt_required_with_permission
from app.models.dictionary import Dictionary
from app.models.user import User
from app import db
import logging
from sqlalchemy import func
from flask_login import current_user
from functools import wraps
import uuid

logger = logging.getLogger(__name__)

def flexible_auth(fn):
    """允许JWT认证或基于会话的认证的装饰器"""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            # 尝试JWT认证
            verify_jwt_in_request(optional=True)
            if get_jwt_identity():
                # JWT认证成功
                return fn(*args, **kwargs)
        except Exception as e:
            logger.debug(f"JWT认证失败: {str(e)}")
        
        # 如果JWT认证失败，检查当前用户是否已登录
        if current_user and current_user.is_authenticated:
            return fn(*args, **kwargs)
        
        # 如果都未认证，返回401错误
        return api_response(
            success=False,
            code=401,
            message="未认证"
        ), 401
        
    return wrapper

@api_v1_bp.route('/dictionary/<string:dict_type>', methods=['GET'])
@flexible_auth
def get_dictionaries(dict_type):
    """获取指定类型的字典列表
    
    Args:
        dict_type: 字典类型，如 'role', 'region' 等
        
    Returns:
        包含字典项列表的响应
    """
    # 检查是否只获取激活的项
    only_active = request.args.get('active_only', 'true').lower() == 'true'
    
    # 查询条件
    query = Dictionary.query.filter_by(type=dict_type)
    if only_active:
        query = query.filter_by(is_active=True)
    
    # 排序
    dictionaries = query.order_by(Dictionary.sort_order, Dictionary.id).all()
    
    # 转换为字典列表
    dict_data = [item.to_dict() for item in dictionaries]
    
    return api_response(
        success=True,
        message="获取成功",
        data=dict_data
    )

@api_v1_bp.route('/dictionary/<string:dict_type>/add', methods=['POST'])
@flexible_auth
def add_dictionary(dict_type):
    """添加新的字典项，自动分配key和排序，前端无需传递"""
    data = request.get_json()
    value = data.get('value')
    if not value:
        return api_response(
            success=False,
            code=400,
            message="显示文本必填"
        )
    # 自动分配key（UUID短码）
    key = str(uuid.uuid4())[:8]
    # 自动分配排序
    max_order = db.session.query(func.max(Dictionary.sort_order)).filter(
        Dictionary.type == dict_type
    ).scalar() or 0
    new_dict = Dictionary(
        type=dict_type,
        key=key,
        value=value,
        is_active=data.get('is_active', True),
        sort_order=max_order + 10
    )
    db.session.add(new_dict)
    try:
        db.session.commit()
        return api_response(
            success=True,
            message="添加成功",
            data=new_dict.to_dict()
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"添加字典项失败: {str(e)}")
        return api_response(
            success=False,
            code=500,
            message=f"添加失败: {str(e)}"
        )

@api_v1_bp.route('/dictionary/<string:dict_type>/edit', methods=['POST'])
@flexible_auth
def edit_dictionary(dict_type):
    """编辑字典项，只允许改value和is_active，禁止改key/sort_order"""
    data = request.get_json()
    if not data or 'id' not in data:
        return api_response(
            success=False,
            code=400,
            message="请求数据无效"
        )
    dict_id = data.get('id')
    dict_item = Dictionary.query.get(dict_id)
    if not dict_item or dict_item.type != dict_type:
        return api_response(
            success=False,
            code=404,
            message="字典项不存在"
        )
    if 'value' in data:
        dict_item.value = data['value']
    if 'is_active' in data:
        dict_item.is_active = data['is_active']
    try:
        db.session.commit()
        return api_response(
            success=True,
            message="更新成功",
            data=dict_item.to_dict()
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新字典项失败: {str(e)}")
        return api_response(
            success=False,
            code=500,
            message=f"更新失败: {str(e)}"
        )

@api_v1_bp.route('/dictionary/<string:dict_type>/toggle', methods=['POST'])
@flexible_auth
def toggle_dictionary(dict_type):
    """切换字典项的活动状态
    
    Args:
        dict_type: 字典类型，如 'role', 'region' 等
        
    Returns:
        包含更新后的字典项的响应
    """
    data = request.get_json()
    
    if not data or 'id' not in data:
        return api_response(
            success=False,
            code=400,
            message="请求数据无效"
        )
    
    # 获取字典项
    dict_id = data.get('id')
    dict_item = Dictionary.query.get(dict_id)
    
    if not dict_item or dict_item.type != dict_type:
        return api_response(
            success=False,
            code=404,
            message="字典项不存在"
        )
    
    # 切换状态
    dict_item.is_active = not dict_item.is_active
    
    try:
        db.session.commit()
        status = "启用" if dict_item.is_active else "禁用"
        return api_response(
            success=True,
            message=f"{status}成功",
            data=dict_item.to_dict()
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新字典项状态失败: {str(e)}")
        return api_response(
            success=False,
            code=500,
            message=f"更新状态失败: {str(e)}"
        )

@api_v1_bp.route('/dictionary/<string:dict_type>/delete', methods=['POST'])
@flexible_auth
def delete_dictionary(dict_type):
    """删除字典项
    
    Args:
        dict_type: 字典类型，如 'role', 'region' 等
        
    Returns:
        操作结果响应
    """
    data = request.get_json()
    
    if not data or 'id' not in data:
        return api_response(
            success=False,
            code=400,
            message="请求数据无效"
        )
    
    # 获取字典项
    dict_id = data.get('id')
    dict_item = Dictionary.query.get(dict_id)
    
    if not dict_item or dict_item.type != dict_type:
        return api_response(
            success=False,
            code=404,
            message="字典项不存在"
        )
    
    # 检查是否被引用（针对角色字典）
    if dict_type == 'role':
        # 检查是否有用户使用此角色
        refs = User.query.filter_by(role=dict_item.key).count()
        if refs > 0:
            return api_response(
                success=False,
                code=400,
                message=f"无法删除：此角色已被 {refs} 个用户引用"
            )
    
    try:
        db.session.delete(dict_item)
        db.session.commit()
        return api_response(
            success=True,
            message="删除成功"
        )
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除字典项失败: {str(e)}")
        return api_response(
            success=False,
            code=500,
            message=f"删除失败: {str(e)}"
        ) 