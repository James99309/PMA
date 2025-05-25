"""
搜索API端点
提供各种模糊查询服务
"""

import logging
from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from app.utils.search_helpers import (
    search_projects_by_name,
    search_companies_by_name,
    search_contacts_by_name,
    search_products_by_name,
    search_projects_without_quotations,
    fuzzy_search_field
)

logger = logging.getLogger(__name__)

search_bp = Blueprint('search', __name__)

@search_bp.route('/projects', methods=['GET'])
@login_required
def search_projects():
    """
    搜索项目
    """
    try:
        query_term = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 10)), 50)
        
        if not query_term:
            return jsonify({
                'success': True,
                'data': [],
                'message': '搜索关键词不能为空'
            })
        
        if len(query_term) < 1:
            return jsonify({
                'success': True,
                'data': [],
                'message': '搜索关键词太短'
            })
        
        results = search_projects_by_name(query_term, current_user, limit)
        
        return jsonify({
            'success': True,
            'data': results,
            'count': len(results)
        })
        
    except Exception as e:
        logger.error(f"搜索项目时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': '搜索失败，请重试'
        }), 500

@search_bp.route('/projects/without-quotations', methods=['GET'])
@login_required
def search_projects_without_quotations_api():
    """
    搜索没有报价单的项目（用于创建报价单）
    """
    try:
        query_term = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 10)), 50)
        
        if not query_term:
            return jsonify({
                'success': True,
                'data': [],
                'message': '搜索关键词不能为空'
            })
        
        if len(query_term) < 1:
            return jsonify({
                'success': True,
                'data': [],
                'message': '搜索关键词太短'
            })
        
        results = search_projects_without_quotations(query_term, current_user, limit)
        
        return jsonify({
            'success': True,
            'data': results,
            'count': len(results)
        })
        
    except Exception as e:
        logger.error(f"搜索无报价单项目时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': '搜索失败，请重试'
        }), 500

@search_bp.route('/companies', methods=['GET'])
@login_required
def search_companies():
    """
    搜索公司
    """
    try:
        query_term = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 10)), 50)
        
        if not query_term:
            return jsonify({
                'success': True,
                'data': [],
                'message': '搜索关键词不能为空'
            })
        
        results = search_companies_by_name(query_term, current_user, limit)
        
        return jsonify({
            'success': True,
            'data': results,
            'count': len(results)
        })
        
    except Exception as e:
        logger.error(f"搜索公司时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': '搜索失败，请重试'
        }), 500

@search_bp.route('/contacts', methods=['GET'])
@login_required
def search_contacts():
    """
    搜索联系人
    """
    try:
        query_term = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 10)), 50)
        
        if not query_term:
            return jsonify({
                'success': True,
                'data': [],
                'message': '搜索关键词不能为空'
            })
        
        results = search_contacts_by_name(query_term, current_user, limit)
        
        return jsonify({
            'success': True,
            'data': results,
            'count': len(results)
        })
        
    except Exception as e:
        logger.error(f"搜索联系人时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': '搜索失败，请重试'
        }), 500

@search_bp.route('/products', methods=['GET'])
@login_required
def search_products():
    """
    搜索产品
    """
    try:
        query_term = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 10)), 50)
        
        if not query_term:
            return jsonify({
                'success': True,
                'data': [],
                'message': '搜索关键词不能为空'
            })
        
        results = search_products_by_name(query_term, current_user, limit)
        
        return jsonify({
            'success': True,
            'data': results,
            'count': len(results)
        })
        
    except Exception as e:
        logger.error(f"搜索产品时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': '搜索失败，请重试'
        }), 500 