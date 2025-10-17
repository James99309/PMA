#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
权限辅助函数模块

提供统一的权限判断逻辑，用于检查模块是否启用等常见权限操作。
"""


def is_module_enabled(permission):
    """
    判断模块是否启用（即是否有任何有效权限）

    模块被视为"启用"的条件：
    - 权限级别不是 'none'
    - 至少有一个基础权限（can_view, can_create, can_edit, can_delete）为 True

    参数:
        permission: Permission对象或RolePermission对象

    返回:
        bool: 模块是否启用

    示例:
        >>> from app.models.user import Permission
        >>> perm = Permission.query.filter_by(user_id=1, module='customer').first()
        >>> is_module_enabled(perm)
        True
    """
    if not permission:
        return False

    # 如果权限级别为 'none'，模块未启用
    permission_level = getattr(permission, 'permission_level', None)
    if permission_level == 'none':
        return False

    # 检查是否有任何基础权限
    has_any_permission = (
        getattr(permission, 'can_view', False) or
        getattr(permission, 'can_create', False) or
        getattr(permission, 'can_edit', False) or
        getattr(permission, 'can_delete', False)
    )

    return has_any_permission
