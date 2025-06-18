#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语言切换视图
"""

from flask import Blueprint, request, redirect, url_for, flash, jsonify, session, make_response
from flask_login import login_required, current_user
from app import db
from app.utils.i18n import set_current_language, get_supported_languages
from flask_babel import gettext as _
from datetime import datetime, timedelta

language_bp = Blueprint('language', __name__, url_prefix='/language')

@language_bp.route('/switch', methods=['POST'])
def switch_language():
    """切换语言"""
    try:
        data = request.get_json()
        if not data or 'language' not in data:
            return jsonify({
                'success': False,
                'message': _('语言参数缺失')
            }), 400
        
        language = data['language']
        
        # 验证语言是否支持
        if language not in get_supported_languages():
            return jsonify({
                'success': False,
                'message': _('不支持的语言')
            }), 400
        
        # 设置session中的语言
        if set_current_language(language):
            # 如果用户已登录，同时更新用户偏好
            if current_user.is_authenticated:
                current_user.language_preference = language
                db.session.commit()
            
            # 创建响应并设置cookie
            response = make_response(jsonify({
                'success': True,
                'message': _('语言切换成功'),
                'language': language
            }))
            
            # 设置语言cookie，有效期30天
            response.set_cookie(
                'language', 
                language, 
                max_age=30 * 24 * 60 * 60,  # 30天
                httponly=False,  # 允许JavaScript访问
                secure=False,    # 在开发环境中设置为False
                samesite='Lax'   # 防止CSRF攻击
            )
            
            return response
        else:
            return jsonify({
                'success': False,
                'message': _('语言切换失败')
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'message': _('服务器错误')
        }), 500

@language_bp.route('/current', methods=['GET'])
def get_current_language_api():
    """获取当前语言"""
    from app.utils.i18n import get_current_language as get_lang
    return jsonify({
        'language': get_lang(),
        'supported_languages': get_supported_languages()
    }) 