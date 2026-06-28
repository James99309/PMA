#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
折扣权限服务
"""
from app.models.role_permissions import RolePermission
from app.models.user import User, Permission


class DiscountPermissionService:
    """折扣权限服务类"""
    
    @staticmethod
    def get_user_discount_limits(user_or_id):
        """
        获取用户的折扣下限
        
        Args:
            user_or_id: User对象或用户ID
            
        Returns:
            dict: 包含pricing_discount_limit和settlement_discount_limit的字典
        """
        # 如果传入的是ID，先获取用户对象
        if isinstance(user_or_id, int):
            user = User.query.get(user_or_id)
        else:
            user = user_or_id
            
        if not user:
            return {'pricing_discount_limit': None, 'settlement_discount_limit': None}
        
        # 管理员无限制
        if user.role == 'admin':
            return {'pricing_discount_limit': 0.0, 'settlement_discount_limit': 0.0}
        
        # 角色级下限(批价单 / 结算单)
        pricing_perm = RolePermission.query.filter_by(
            role=user.role,
            module='pricing_order'
        ).first()
        settlement_perm = RolePermission.query.filter_by(
            role=user.role,
            module='settlement_order'
        ).first()
        role_pricing = pricing_perm.pricing_discount_limit if pricing_perm else None
        role_settlement = settlement_perm.settlement_discount_limit if settlement_perm else None

        # 账户级下限(permissions 表,user_id+module)——优先,为空则回退角色级
        user_pricing_perm = Permission.query.filter_by(
            user_id=user.id, module='pricing_order'
        ).first()
        user_settlement_perm = Permission.query.filter_by(
            user_id=user.id, module='settlement_order'
        ).first()

        pricing_limit = role_pricing
        if user_pricing_perm and user_pricing_perm.pricing_discount_limit is not None:
            pricing_limit = user_pricing_perm.pricing_discount_limit

        settlement_limit = role_settlement
        if user_settlement_perm and user_settlement_perm.settlement_discount_limit is not None:
            settlement_limit = user_settlement_perm.settlement_discount_limit

        return {
            'pricing_discount_limit': pricing_limit,
            'settlement_discount_limit': settlement_limit
        }
    
    @staticmethod
    def check_discount_permission(user, discount_rate, order_type='pricing'):
        """
        检查折扣率是否超出用户权限
        
        Args:
            user: User对象
            discount_rate: 折扣率（百分比形式，如40.5表示40.5%）
            order_type: 订单类型，'pricing'或'settlement'
            
        Returns:
            dict: {
                'allowed': bool,  # 是否允许
                'limit': float,   # 用户的折扣下限
                'exceeds': bool   # 是否超出限制
            }
        """
        limits = DiscountPermissionService.get_user_discount_limits(user)
        
        if order_type == 'pricing':
            limit = limits['pricing_discount_limit']
        else:
            limit = limits['settlement_discount_limit']
        
        # 如果没有设置限制，则允许任何折扣
        if limit is None:
            return {'allowed': True, 'limit': None, 'exceeds': False}
        
        # 检查是否超出限制（折扣率低于下限）
        exceeds = discount_rate < limit
        
        return {
            'allowed': not exceeds,
            'limit': limit,
            'exceeds': exceeds
        }
    
    @staticmethod
    def get_discount_warning_class(user, discount_rate, order_type='pricing'):
        """
        获取折扣率的CSS样式类
        
        Args:
            user: User对象
            discount_rate: 折扣率（百分比形式）
            order_type: 订单类型，'pricing'或'settlement'
            
        Returns:
            str: CSS样式类名
        """
        permission_check = DiscountPermissionService.check_discount_permission(
            user, discount_rate, order_type
        )
        
        if permission_check['exceeds']:
            return 'discount-warning'  # 红色背景，白色字体
        else:
            return ''  # 正常样式 