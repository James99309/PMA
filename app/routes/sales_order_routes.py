# -*- coding: utf-8 -*-
"""
客户订单路由蓝图
管理销售订单的创建、列表、详情、状态流转等
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models.sales_order import SalesOrder, SalesOrderDetail
from app.models.pricing_order import PricingOrder
from app.models.customer import Company
from app.services.sales_order_service import SalesOrderService
from app.decorators import permission_required
from app.utils.access_control import get_viewable_data
import logging

logger = logging.getLogger(__name__)

sales_order_bp = Blueprint('sales_order', __name__, url_prefix='/sales-order')


# ============== 页面路由 ==============

@sales_order_bp.route('/')
@login_required
@permission_required('sales_order', 'view')
def list_view():
    """客户订单列表页"""
    # 获取筛选参数
    status = request.args.get('status', '')
    customer_id = request.args.get('customer_id', '')
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # 基础查询（带权限过滤）
    base_query = get_viewable_data(SalesOrder, current_user)
    query = base_query

    # 状态筛选
    if status:
        query = query.filter(SalesOrder.status == status)

    # 客户筛选
    if customer_id:
        query = query.filter(SalesOrder.customer_id == int(customer_id))

    # 搜索
    if search:
        query = query.filter(
            db.or_(
                SalesOrder.order_number.ilike(f'%{search}%'),
                SalesOrder.notes.ilike(f'%{search}%')
            )
        )

    # 排序和分页
    query = query.order_by(SalesOrder.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    orders = pagination.items

    # 获取统计数据（复用 base_query 避免重复 get_viewable_data）
    stats = SalesOrderService.get_order_statistics(base_query=base_query)

    # 获取客户列表（用于筛选）
    customers = Company.query.filter(
        Company.is_deleted == False,
        Company.company_type.in_(['customer', 'dealer', 'distributor'])
    ).order_by(Company.company_name).all()

    return render_template(
        'sales_order/tw_list.html',
        orders=orders,
        pagination=pagination,
        stats=stats,
        customers=customers,
        current_status=status,
        current_customer_id=customer_id,
        search=search
    )


@sales_order_bp.route('/<int:order_id>')
@login_required
@permission_required('sales_order', 'view')
def detail_view(order_id):
    """客户订单详情页"""
    # 带权限过滤获取订单
    query = get_viewable_data(SalesOrder, current_user)
    order = query.filter(SalesOrder.id == order_id).first()

    if not order:
        flash('订单不存在或无权访问', 'error')
        return redirect(url_for('sales_order.list_view'))

    return render_template(
        'sales_order/tw_detail.html',
        order=order
    )


# ============== API路由 ==============

@sales_order_bp.route('/api/create', methods=['POST'])
@login_required
@permission_required('sales_order', 'create')
def api_create():
    """从批价单创建客户订单"""
    try:
        data = request.get_json()
        pricing_order_id = data.get('pricing_order_id')

        if not pricing_order_id:
            return jsonify({'success': False, 'message': '缺少批价单ID'})

        # 构建交付信息
        delivery_info = {
            'delivery_date': None,
            'delivery_address': data.get('delivery_address'),
            'delivery_contact': data.get('delivery_contact'),
            'delivery_phone': data.get('delivery_phone'),
            'delivery_email': data.get('delivery_email'),
            'shipping_method': data.get('shipping_method'),
            'freight_terms': data.get('freight_terms'),
            'incoterms': data.get('incoterms'),
            'notes': data.get('notes')
        }

        # 处理日期
        if data.get('delivery_date'):
            try:
                delivery_info['delivery_date'] = datetime.strptime(
                    data['delivery_date'], '%Y-%m-%d'
                )
            except ValueError:
                pass

        # 创建订单
        order, error = SalesOrderService.create_from_pricing_order(
            pricing_order_id, delivery_info, current_user.id
        )

        if error:
            return jsonify({'success': False, 'message': error})

        return jsonify({
            'success': True,
            'message': f'客户订单 {order.order_number} 创建成功',
            'order_id': order.id,
            'order_number': order.order_number,
            'redirect_url': url_for('sales_order.detail_view', order_id=order.id)
        })

    except Exception as e:
        logger.error(f"创建客户订单失败: {str(e)}")
        return jsonify({'success': False, 'message': f'创建失败: {str(e)}'})


@sales_order_bp.route('/api/<int:order_id>', methods=['GET'])
@login_required
@permission_required('sales_order', 'view')
def api_get_order(order_id):
    """获取订单详情"""
    query = get_viewable_data(SalesOrder, current_user)
    order = query.filter(SalesOrder.id == order_id).first()

    if not order:
        return jsonify({'success': False, 'message': '订单不存在或无权访问'})

    return jsonify({
        'success': True,
        'order': {
            'id': order.id,
            'order_number': order.order_number,
            'status': order.status,
            'customer_name': order.customer.company_name if order.customer else '',
            'total_amount': float(order.total_amount or 0),
            'total_quantity': order.total_quantity,
            'shipped_quantity': order.shipped_quantity,
            'received_quantity': order.received_quantity,
            'delivery_progress': order.delivery_progress,
            'delivery_date': order.formatted_delivery_date,
            'delivery_address': order.delivery_address,
            'delivery_contact': order.delivery_contact,
            'delivery_phone': order.delivery_phone,
            'shipping_method': order.shipping_method,
            'created_at': order.created_at.strftime('%Y-%m-%d %H:%M') if order.created_at else '',
            'details': [{
                'id': d.id,
                'product_name': d.product_name,
                'product_model': d.product_model,
                'quantity': d.quantity,
                'unit': d.unit,
                'unit_price': float(d.unit_price or 0),
                'total_price': float(d.total_price or 0),
                'shipped_quantity': d.shipped_quantity,
                'received_quantity': d.received_quantity,
                'remaining_to_ship': d.remaining_to_ship,
                'status': d.status
            } for d in order.details]
        }
    })


@sales_order_bp.route('/api/<int:order_id>/confirm', methods=['POST'])
@login_required
@permission_required('sales_order', 'edit')
def api_confirm(order_id):
    """确认订单"""
    success, message = SalesOrderService.confirm_order(order_id, current_user.id)
    return jsonify({'success': success, 'message': message})


@sales_order_bp.route('/api/<int:order_id>/cancel', methods=['POST'])
@login_required
@permission_required('sales_order', 'edit')
def api_cancel(order_id):
    """取消订单"""
    data = request.get_json() or {}
    reason = data.get('reason')
    success, message = SalesOrderService.cancel_order(order_id, current_user.id, reason)
    return jsonify({'success': success, 'message': message})


@sales_order_bp.route('/api/<int:order_id>/delivery-info', methods=['PUT'])
@login_required
@permission_required('sales_order', 'edit')
def api_update_delivery_info(order_id):
    """更新交付信息"""
    try:
        data = request.get_json()
        delivery_info = {}

        # 处理日期
        if 'delivery_date' in data:
            if data['delivery_date']:
                try:
                    delivery_info['delivery_date'] = datetime.strptime(
                        data['delivery_date'], '%Y-%m-%d'
                    )
                except ValueError:
                    pass
            else:
                delivery_info['delivery_date'] = None

        # 其他字段
        for field in ['delivery_address', 'delivery_contact', 'delivery_phone',
                      'delivery_email', 'shipping_method', 'freight_terms', 'incoterms']:
            if field in data:
                delivery_info[field] = data[field]

        success, message = SalesOrderService.update_delivery_info(
            order_id, delivery_info, current_user.id
        )
        return jsonify({'success': success, 'message': message})

    except Exception as e:
        logger.error(f"更新交付信息失败: {str(e)}")
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})


@sales_order_bp.route('/api/list', methods=['GET'])
@login_required
@permission_required('sales_order', 'view')
def api_list():
    """获取订单列表数据（用于AJAX刷新）"""
    status = request.args.get('status', '')
    customer_id = request.args.get('customer_id', '')
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = get_viewable_data(SalesOrder, current_user)

    if status:
        query = query.filter(SalesOrder.status == status)
    if customer_id:
        query = query.filter(SalesOrder.customer_id == int(customer_id))
    if search:
        query = query.filter(
            db.or_(
                SalesOrder.order_number.ilike(f'%{search}%'),
                SalesOrder.notes.ilike(f'%{search}%')
            )
        )

    query = query.order_by(SalesOrder.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    orders_data = [{
        'id': o.id,
        'order_number': o.order_number,
        'customer_name': o.customer.company_name if o.customer else '',
        'total_amount': float(o.total_amount or 0),
        'total_quantity': o.total_quantity,
        'status': o.status,
        'delivery_progress': o.delivery_progress,
        'created_at': o.created_at.strftime('%Y-%m-%d') if o.created_at else ''
    } for o in pagination.items]

    return jsonify({
        'success': True,
        'orders': orders_data,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    })


@sales_order_bp.route('/api/stats', methods=['GET'])
@login_required
@permission_required('sales_order', 'view')
def api_stats():
    """获取订单统计数据"""
    stats = SalesOrderService.get_order_statistics(current_user)
    return jsonify({'success': True, 'stats': stats})
