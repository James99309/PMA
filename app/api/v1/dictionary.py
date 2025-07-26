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
import re

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
    """添加字典项到指定类型的字典
    
    Args:
        dict_type: 字典类型，如 'role', 'region' 等
        
    Returns:
        包含新创建的字典项的响应
    """
    data = request.get_json()
    
    if not data or 'value' not in data:
        return api_response(
            success=False,
            code=400,
            message="请求数据无效，缺少必要字段"
        )
    
    value = data.get('value', '').strip()
    if not value:
        return api_response(
            success=False,
            code=400,
            message="值不能为空"
        )

    # 如果提供了key，则使用，否则根据value自动生成
    key = data.get('key', '').strip()
    if not key:
        if dict_type == 'role':
            # 特定映射关系（针对角色）
            value_map = {
                '客户销售': 'customer_sales',
                '渠道经理': 'channel_manager',
                '营销总监': 'sales_director',
                '服务': 'service',
                '服务经理': 'service_manager',
                '产品经理': 'product_manager',
                '解决方案经理': 'solution_manager',
                '普通用户': 'user',
                '经销商': 'dealer',
                '管理员': 'admin'
            }
            key = value_map.get(value)
        if not key:
            # 否则用英文分词+下划线（假设value已是英文或拼音）
            key = re.sub(r'[^a-zA-Z0-9]+', '_', value.strip().lower())
            key = re.sub(r'_+', '_', key).strip('_')
    
    # 检查key是否已存在
    exists = Dictionary.query.filter_by(type=dict_type, key=key).first()
    if exists:
        return api_response(
            success=False,
            code=409,
            message="该key已存在"
        )
    
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
    
    # 对企业字典处理厂商标记和详细信息
    if dict_type == 'company':
        if 'is_vendor' in data:
            new_dict.is_vendor = data.get('is_vendor', False)
        
        # 处理企业详细信息字段
        detail_fields = ['address', 'postal_code', 'phone', 'fax', 'email', 'website']
        for field in detail_fields:
            if field in data:
                value = data[field].strip() if data[field] else None
                if value == '':
                    value = None
                setattr(new_dict, field, value)
    
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
        logging.error(f"添加字典项失败: {str(e)}")
        return api_response(
            success=False,
            code=500,
            message=f"添加失败: {str(e)}"
        )

@api_v1_bp.route('/dictionary/<string:dict_type>/edit', methods=['POST'])
@flexible_auth
def edit_dictionary(dict_type):
    """编辑字典项，只允许改value、is_active和is_vendor，禁止改key/sort_order"""
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
    # 对企业字典处理厂商标记和详细信息
    if dict_type == 'company':
        if 'is_vendor' in data:
            dict_item.is_vendor = data.get('is_vendor', False)
        
        # 处理企业详细信息字段
        detail_fields = ['address', 'postal_code', 'phone', 'fax', 'email', 'website']
        for field in detail_fields:
            if field in data:
                value = data[field].strip() if data[field] else None
                if value == '':
                    value = None
                setattr(dict_item, field, value)
        
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

@api_v1_bp.route('/dictionary/company/<int:company_id>/upload_asset', methods=['POST'])
@flexible_auth
def upload_company_asset(company_id):
    """上传企业资产（Logo或邮件签名）"""
    try:
        # 获取企业字典项
        company = Dictionary.query.filter_by(id=company_id, type='company').first()
        if not company:
            return api_response(
                success=False,
                code=404,
                message="企业不存在"
            ), 404
        
        # 获取上传文件
        file = request.files.get('file')
        asset_type = request.form.get('asset_type')
        
        if not file or not asset_type:
            return api_response(
                success=False,
                code=400,
                message="缺少必要参数"
            ), 400
        
        # 验证文件类型
        allowed_types = ['image/png', 'image/jpeg', 'image/jpg', 'image/svg+xml', 'image/gif']
        file_type = file.content_type
        
        if file_type not in allowed_types:
            return api_response(
                success=False,
                code=400,
                message="不支持的文件类型，请使用PNG、JPG、SVG或GIF格式"
            ), 400
        
        # 读取文件数据
        file_data = file.read()
        
        # 验证文件大小
        max_size = 5 * 1024 * 1024 if asset_type == 'logo' else 3 * 1024 * 1024
        if len(file_data) > max_size:
            size_limit = "5MB" if asset_type == 'logo' else "3MB"
            return api_response(
                success=False,
                code=400,
                message=f"文件大小不能超过{size_limit}"
            ), 400
        
        # 上传资产
        if asset_type == 'logo':
            success = company.update_logo(file_data, file.filename)
        elif asset_type == 'signature':
            success = company.update_email_signature(file_data, file.filename)
        else:
            return api_response(
                success=False,
                code=400,
                message="不支持的资产类型"
            ), 400
        
        if not success:
            return api_response(
                success=False,
                code=500,
                message="上传失败"
            ), 500
        
        db.session.commit()
        
        asset_name = "Logo" if asset_type == 'logo' else "邮件签名"
        return api_response(
            success=True,
            message=f"{asset_name}上传成功"
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"上传企业资产失败 (企业ID: {company_id}): {str(e)}")
        return api_response(
            success=False,
            code=500,
            message=f"上传失败: {str(e)}"
        ), 500

@api_v1_bp.route('/dictionary/company/<int:company_id>/delete_asset', methods=['POST'])
@flexible_auth
def delete_company_asset(company_id):
    """删除企业资产（Logo或邮件签名）"""
    try:
        # 获取企业字典项
        company = Dictionary.query.filter_by(id=company_id, type='company').first()
        if not company:
            return api_response(
                success=False,
                code=404,
                message="企业不存在"
            ), 404
        
        asset_type = request.form.get('asset_type')
        if not asset_type:
            return api_response(
                success=False,
                code=400,
                message="缺少资产类型参数"
            ), 400
        
        # 删除资产
        if asset_type == 'logo':
            success = company.clear_logo()
        elif asset_type == 'signature':
            success = company.clear_email_signature()
        else:
            return api_response(
                success=False,
                code=400,
                message="不支持的资产类型"
            ), 400
        
        if not success:
            return api_response(
                success=False,
                code=500,
                message="删除失败"
            ), 500
        
        db.session.commit()
        
        asset_name = "Logo" if asset_type == 'logo' else "邮件签名"
        return api_response(
            success=True,
            message=f"{asset_name}删除成功"
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除企业资产失败 (企业ID: {company_id}): {str(e)}")
        return api_response(
            success=False,
            code=500,
            message=f"删除失败: {str(e)}"
        ), 500

@api_v1_bp.route('/dictionary/company/<int:company_id>/get_asset', methods=['GET'])
@flexible_auth
def get_company_asset(company_id):
    """获取企业资产（Logo或邮件签名）"""
    try:
        # 获取企业字典项
        company = Dictionary.query.filter_by(id=company_id, type='company').first()
        if not company:
            return api_response(
                success=False,
                code=404,
                message="企业不存在"
            ), 404
        
        asset_type = request.args.get('type')
        if not asset_type:
            return api_response(
                success=False,
                code=400,
                message="缺少资产类型参数"
            ), 400
        
        # 获取资产
        if asset_type == 'logo':
            asset_url = company.logo_data_url
        elif asset_type == 'signature':
            asset_url = company.email_signature_data_url
        else:
            return api_response(
                success=False,
                code=400,
                message="不支持的资产类型"
            ), 400
        
        if not asset_url:
            return api_response(
                success=False,
                code=404,
                message="资产不存在"
            ), 404
        
        return api_response(
            success=True,
            message="获取成功",
            data=asset_url
        )
        
    except Exception as e:
        logger.error(f"获取企业资产失败 (企业ID: {company_id}): {str(e)}")
        return api_response(
            success=False,
            code=500,
            message=f"获取失败: {str(e)}"
        ), 500 