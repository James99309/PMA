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

@search_bp.route('/quotations', methods=['GET'])
@login_required
def search_quotations():
    """
    搜索报价单
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
        
        # 导入必要的模块
        from app.models.quotation import Quotation
        from app.models.project import Project
        from app.utils.access_control import get_viewable_data
        from sqlalchemy import or_
        
        # 获取用户可查看的报价单
        quotations_query = get_viewable_data(Quotation, current_user)
        
        # 添加项目表的JOIN以便搜索项目名称
        quotations_query = quotations_query.join(Project)
        
        # 添加搜索条件
        search_condition = or_(
            Project.project_name.ilike(f'%{query_term}%'),
            Project.authorization_code.ilike(f'%{query_term}%'),
            Quotation.quotation_number.ilike(f'%{query_term}%')
        )
        quotations_query = quotations_query.filter(search_condition)
        
        # 限制结果数量并排序
        quotations = quotations_query.order_by(Quotation.created_at.desc()).limit(limit).all()
        
        # 构建返回结果
        results = []
        for quotation in quotations:
            try:
                # 获取项目信息
                project = quotation.project
                
                # 构建显示文本
                display_text = f"{project.project_name}"
                if project.authorization_code:
                    display_text += f" ({project.authorization_code})"
                if quotation.quotation_number:
                    display_text += f" - {quotation.quotation_number}"
                
                results.append({
                    'quotation_id': quotation.id,
                    'quotation_number': quotation.quotation_number,
                    'project_id': project.id,
                    'project_name': project.project_name,
                    'authorization_code': project.authorization_code or '',
                    'project_type': project.project_type or '',
                    'amount': float(quotation.amount) if quotation.amount else 0,
                    'display_text': display_text,
                    'created_at': quotation.created_at.isoformat() if quotation.created_at else None
                })
                
            except Exception as e:
                logger.error(f"处理报价单搜索结果时出错: {str(e)}")
                # 如果处理失败，至少返回基本信息
                results.append({
                    'quotation_id': quotation.id,
                    'quotation_number': quotation.quotation_number or '',
                    'project_id': quotation.project_id,
                    'project_name': '未知项目',
                    'authorization_code': '',
                    'project_type': '',
                    'amount': 0,
                    'display_text': quotation.quotation_number or f'报价单 {quotation.id}',
                    'created_at': quotation.created_at.isoformat() if quotation.created_at else None
                })
        
        return jsonify({
            'success': True,
            'data': results,
            'count': len(results)
        })
        
    except Exception as e:
        logger.error(f"搜索报价单时出错: {str(e)}")
        return jsonify({
            'success': False,
            'message': '搜索失败，请重试'
        }), 500 