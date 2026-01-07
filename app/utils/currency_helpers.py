# -*- coding: utf-8 -*-
"""
货币辅助函数模块

基于数据库类型提供统一的货币配置访问接口。
货币和单位由数据库类型决定，与用户语言设置解耦。

- SP8D/本地: CNY (¥), 万元, 除以10000
- OVS: USD ($), M (million), 除以1000000
"""

from flask import current_app
from flask_babel import get_locale


def get_system_currency():
    """
    获取系统默认货币代码

    Returns:
        str: 货币代码 ('CNY' 或 'USD')
    """
    return current_app.config.get('DEFAULT_CURRENCY', 'CNY')


def get_currency_symbol():
    """
    获取货币符号

    Returns:
        str: 货币符号 ('¥' 或 '$')
    """
    return current_app.config.get('CURRENCY_SYMBOL', '¥')


def get_amount_unit():
    """
    获取金额单位（根据当前语言返回）

    Returns:
        str: 金额单位 (中文: '万元', 英文: '0K')
    """
    base_unit = current_app.config.get('AMOUNT_UNIT', '万元')
    # OVS 数据库使用 'M' 单位，不需要翻译
    if base_unit == 'M':
        return base_unit
    # 中文万元在英文界面显示为 '0K'
    try:
        locale = get_locale()
        if locale and str(locale) == 'en':
            return '0K'
    except RuntimeError:
        pass
    return base_unit


def get_amount_divisor():
    """
    获取金额除数（用于大金额显示）

    Returns:
        int: 除数 (10000 或 1000000)
    """
    return current_app.config.get('AMOUNT_DIVISOR', 10000)


def get_count_unit():
    """
    获取计数单位

    Returns:
        str: 计数单位 ('个' 或 'pcs')
    """
    return current_app.config.get('COUNT_UNIT', '个')


def format_large_amount(amount, with_symbol=True, with_unit=True):
    """
    格式化大金额显示

    Args:
        amount: 原始金额（分或元）
        with_symbol: 是否包含货币符号
        with_unit: 是否包含单位

    Returns:
        str: 格式化后的金额字符串
    """
    if amount is None:
        amount = 0

    symbol = get_currency_symbol() if with_symbol else ''
    unit = get_amount_unit() if with_unit else ''
    divisor = get_amount_divisor()

    value = amount / divisor

    if with_unit:
        return f"{symbol}{value:,.2f} {unit}"
    else:
        return f"{symbol}{value:,.2f}"


def get_currency_config():
    """
    获取完整的货币配置（用于传递到模板）

    Returns:
        dict: 包含所有货币配置的字典
    """
    return {
        'currency': get_system_currency(),
        'symbol': get_currency_symbol(),
        'amount_unit': get_amount_unit(),
        'amount_divisor': get_amount_divisor(),
        'count_unit': get_count_unit()
    }


def is_ovs_database():
    """
    检查是否为OVS数据库

    Returns:
        bool: 是否为OVS数据库
    """
    return current_app.config.get('IS_OVS', False)


def is_sp8d_database():
    """
    检查是否为SP8D数据库

    Returns:
        bool: 是否为SP8D数据库
    """
    return current_app.config.get('IS_SP8D', False)
