#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
国际化工具模块
提供语言切换和翻译功能
"""

from flask import session, request, current_app
from flask_babel import get_locale
from flask_login import current_user
import os

# 支持的语言列表
LANGUAGES = {
    'zh': '简体中文',
    'en': 'English'
}

def get_supported_languages():
    """获取支持的语言列表"""
    return LANGUAGES

def get_current_language():
    """获取当前语言"""
    try:
        # 1. 优先从session中获取
        if 'language' in session:
            lang = session['language']
            if lang in LANGUAGES:
                return lang
        
        # 2. 从cookie中获取（用于登录界面等非登录状态）
        if request and 'language' in request.cookies:
            lang = request.cookies.get('language')
            if lang in LANGUAGES:
                return lang
        
        # 3. 如果用户已登录，从用户偏好获取
        if current_user.is_authenticated and hasattr(current_user, 'language_preference'):
            if current_user.language_preference and current_user.language_preference in LANGUAGES:
                return current_user.language_preference
        
        # 4. 从浏览器Accept-Language头获取
        if request:
            browser_lang = request.accept_languages.best_match(LANGUAGES.keys())
            if browser_lang:
                return browser_lang
        
        # 5. 默认返回简体中文
        return 'zh'
    except Exception as e:
        # 如果出现任何异常，记录日志并返回默认语言
        try:
            from flask import current_app
            current_app.logger.warning(f"语言检测异常: {e}")
        except:
            # 如果连日志都无法记录，静默处理
            pass
        return 'zh'

def set_current_language(language):
    """设置当前语言"""
    if language in LANGUAGES:
        session['language'] = language
        return True
    return False


def force_locale(language):
    """强制设置语言上下文管理器，用于测试"""
    from flask_babel import Babel, force_locale as babel_force_locale
    return babel_force_locale(language)

def get_default_currency():
    """根据当前语言环境获取默认货币"""
    current_lang = get_current_language()

    # 根据语言环境返回相应的默认货币
    if current_lang == 'en':
        return 'USD'  # 英文环境默认美元
    else:
        return 'CNY'  # 中文环境默认人民币

def get_currency_symbol(currency):
    """获取货币符号"""
    currency_symbols = {
        'CNY': '¥',
        'USD': '$',
        'SGD': 'S$',
        'MYR': 'RM',
        'IDR': 'Rp',
        'THB': '฿',
        'EUR': '€',
        'GBP': '£',
        'JPY': '¥',
        'HKD': 'HK$',
        'AUD': 'A$',
        'CAD': 'C$'
    }
    return currency_symbols.get(currency, '¤')  # ¤ 是通用货币符号

 