#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
折扣权限检查API
"""
from flask import request, jsonify
from flask_login import login_required, current_user
from app import db
from app.api.v1 import api_v1_bp
from app.services.discount_permission_service import DiscountPermissionService
from app.models.role_permissions import RolePermission


@api_v1_bp.route('/discount/check', methods=['POST'])
@login_required
def check_discount_permission():
    """
    检查折扣权限
    请求格式: {
        "discount_rate": 35.5,
        "order_type": "pricing"  // 或 "settlement"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        discount_rate = data.get('discount_rate')
        order_type = data.get('order_type', 'pricing')
        
        if discount_rate is None:
            return jsonify({
                'success': False,
                'message': '缺少折扣率参数'
            }), 400
        
        # 检查权限
        permission_check = DiscountPermissionService.check_discount_permission(
            current_user, discount_rate, order_type
        )
        
        # 获取用户折扣下限
        limits = DiscountPermissionService.get_user_discount_limits(current_user)
        
        return jsonify({
            'success': True,
            'data': {
                'allowed': permission_check['allowed'],
                'exceeds': permission_check['exceeds'],
                'limit': permission_check['limit'],
                'warning_class': 'discount-warning' if permission_check['exceeds'] else '',
                'user_limits': limits
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'检查折扣权限失败: {str(e)}'
        }), 500


@api_v1_bp.route('/discount/limits', methods=['GET'])
@login_required
def get_user_discount_limits():
    """获取当前用户的折扣下限"""
    try:
        limits = DiscountPermissionService.get_user_discount_limits(current_user)
        
        return jsonify({
            'success': True,
            'data': limits
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'获取折扣下限失败: {str(e)}'
        }), 500


@api_v1_bp.route('/discount/save', methods=['POST'])
@login_required
def save_discount_limits():
    """
    保存角色的折扣下限
    请求格式: {
        "role": "channel_manager",
        "pricing_discount_limit": 40.0,
        "settlement_discount_limit": 30.0
    }
    """
    try:
        # 检查权限
        if current_user.role != 'admin':
            return jsonify({
                'success': False,
                'message': '只有管理员可以设置折扣权限'
            }), 403
        
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据不能为空'
            }), 400
        
        role = data.get('role')
        pricing_limit = data.get('pricing_discount_limit')
        settlement_limit = data.get('settlement_discount_limit')
        
        if not role:
            return jsonify({
                'success': False,
                'message': '缺少角色参数'
            }), 400
        
        # 更新批价单权限
        pricing_perm = RolePermission.query.filter_by(role=role, module='pricing_order').first()
        if pricing_perm:
            pricing_perm.pricing_discount_limit = pricing_limit
            pricing_perm.settlement_discount_limit = settlement_limit
        else:
            # 如果权限不存在，创建一个新的
            pricing_perm = RolePermission(
                role=role,
                module='pricing_order',
                can_view=True,
                can_create=False,
                can_edit=False,
                can_delete=False,
                pricing_discount_limit=pricing_limit,
                settlement_discount_limit=settlement_limit
            )
            db.session.add(pricing_perm)
        
        # 更新结算单权限
        settlement_perm = RolePermission.query.filter_by(role=role, module='settlement_order').first()
        if settlement_perm:
            settlement_perm.pricing_discount_limit = pricing_limit
            settlement_perm.settlement_discount_limit = settlement_limit
        else:
            # 如果权限不存在，创建一个新的
            settlement_perm = RolePermission(
                role=role,
                module='settlement_order',
                can_view=True,
                can_create=False,
                can_edit=False,
                can_delete=False,
                pricing_discount_limit=pricing_limit,
                settlement_discount_limit=settlement_limit
            )
            db.session.add(settlement_perm)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '折扣权限设置已保存'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'保存折扣权限失败: {str(e)}'
        }), 500 