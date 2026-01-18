# -*- coding: utf-8 -*-
"""
旧规格系统特性开关装饰器

此模块提供用于控制ProductCodeField（旧规格系统）的特性开关装饰器。
允许通过配置完全启用或禁用旧系统的API和功能。

[LegacySpecSystem] - 此文件仅用于管理旧规格系统的特性开关
"""

from functools import wraps
from flask import jsonify, current_app
import logging

logger = logging.getLogger(__name__)


def feature_flag(flag_name):
    """
    特性开关装饰器 - 当特性禁用时返回503 Service Unavailable

    Args:
        flag_name: 特性开关的配置名称（如 'LEGACY_SPEC_SYSTEM_ENABLED'）

    Usage:
        @feature_flag('LEGACY_SPEC_SYSTEM_ENABLED')
        def get_spec_fields(category_id):
            # 此函数仅在 LEGACY_SPEC_SYSTEM_ENABLED=true 时执行
            ...

    Returns:
        当特性禁用时：HTTP 503 响应，source 标识为 'legacy_spec_system'
        当特性启用时：正常执行被装饰的函数
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # [LegacySpecSystem] 检查特性开关
            is_enabled = current_app.config.get(flag_name, True)

            if not is_enabled:
                # [LegacySpecSystem] 旧系统已禁用
                logger.warning(
                    f'[LegacySpecSystem] API "{func.__name__}" called but system is disabled'
                )
                return jsonify({
                    'success': False,
                    'source': 'legacy_spec_system',
                    'error': 'Legacy specification system is disabled',
                    'message': '旧规格系统已禁用，请使用新规格模板系统'
                }), 503

            # [LegacySpecSystem] 旧系统已启用，执行原函数
            return func(*args, **kwargs)

        return wrapper
    return decorator
