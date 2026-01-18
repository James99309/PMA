"""
员工列表外部 API
用于 Stargirl 培训系统获取员工信息
"""
from flask import request, jsonify
from functools import wraps
import os

from . import external_api_bp
from app.models.user import User


def external_api_key_required(f):
    """
    外部 API Key 认证装饰器
    需要在请求头中提供 X-External-API-Key
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-External-API-Key')
        expected_key = os.getenv('EXTERNAL_API_KEY')

        if not expected_key:
            return jsonify({
                'success': False,
                'message': '服务器未配置外部 API Key'
            }), 500

        if not api_key or api_key != expected_key:
            return jsonify({
                'success': False,
                'message': '无效的 API Key'
            }), 401

        return f(*args, **kwargs)
    return decorated


@external_api_bp.route('/employees', methods=['GET'])
@external_api_key_required
def get_employees():
    """
    获取所有激活的员工列表

    用于培训系统用户组管理

    Query Parameters:
        - limit: 返回数量限制 (默认 500)
        - offset: 偏移量 (默认 0)
        - company: 按公司筛选
        - search: 搜索关键词 (姓名/用户名)

    Returns:
        {
            "success": true,
            "data": [
                {
                    "user_id": "1",
                    "name": "张三",
                    "username": "zhangsan",
                    "company": "SP8D",
                    "department": "销售部"
                }
            ],
            "total": 100
        }
    """
    try:
        limit = min(int(request.args.get('limit', 500)), 1000)
        offset = int(request.args.get('offset', 0))
        company = request.args.get('company', '').strip()
        search = request.args.get('search', '').strip()

        # 查询激活的用户
        query = User.query.filter(User._is_active == True)

        # 按公司筛选
        if company:
            query = query.filter(User.company_name == company)

        # 搜索
        if search:
            query = query.filter(
                (User.real_name.ilike(f'%{search}%')) |
                (User.username.ilike(f'%{search}%'))
            )

        # 获取总数
        total = query.count()

        # 分页
        users = query.order_by(User.real_name).offset(offset).limit(limit).all()

        # 转换数据格式
        employees = []
        for user in users:
            employees.append({
                'user_id': str(user.id),  # 转为字符串，与 stargirl 系统兼容
                'name': user.real_name or user.username,
                'username': user.username,
                'company': user.company_name or '',
                'department': user.department or ''
            })

        return jsonify({
            'success': True,
            'data': employees,
            'total': total
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@external_api_bp.route('/employees/<user_id>', methods=['GET'])
@external_api_key_required
def get_employee(user_id):
    """
    获取单个员工信息
    """
    try:
        user = User.query.get(int(user_id))

        if not user:
            return jsonify({
                'success': False,
                'message': '员工不存在'
            }), 404

        return jsonify({
            'success': True,
            'data': {
                'user_id': str(user.id),
                'name': user.real_name or user.username,
                'username': user.username,
                'company': user.company_name or '',
                'department': user.department or ''
            }
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
