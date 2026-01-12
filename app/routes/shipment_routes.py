# -*- coding: utf-8 -*-
"""
发货管理路由蓝图
管理发货单的创建、发货确认、签收等
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from decimal import Decimal
from app import db
from app.models.shipment import Shipment, ShipmentDetail
from app.models.sales_order import SalesOrder, SalesOrderDetail
from app.services.shipment_service import ShipmentService
from app.decorators import permission_required
import logging

logger = logging.getLogger(__name__)

shipment_bp = Blueprint('shipment', __name__, url_prefix='/shipment')


# ============== 页面路由 ==============

@shipment_bp.route('/')
@login_required
@permission_required('shipment', 'view')
def list_view():
    """发货记录列表页"""
    # 获取筛选参数
    status = request.args.get('status', '')
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # 基础查询
    query = Shipment.query

    # 状态筛选
    if status:
        query = query.filter(Shipment.status == status)

    # 搜索
    if search:
        query = query.filter(
            db.or_(
                Shipment.shipment_number.ilike(f'%{search}%'),
                Shipment.tracking_number.ilike(f'%{search}%'),
                Shipment.carrier.ilike(f'%{search}%')
            )
        )

    # 排序和分页
    query = query.order_by(Shipment.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    shipments = pagination.items

    # 获取统计数据
    stats = ShipmentService.get_shipment_statistics()

    return render_template(
        'shipment/tw_list.html',
        shipments=shipments,
        pagination=pagination,
        stats=stats,
        current_status=status,
        search=search
    )


@shipment_bp.route('/<int:shipment_id>')
@login_required
@permission_required('shipment', 'view')
def detail_view(shipment_id):
    """发货记录详情页"""
    shipment = Shipment.query.get_or_404(shipment_id)

    # 获取物流时间线
    timeline = ShipmentService.get_tracking_timeline(shipment_id)

    return render_template(
        'shipment/tw_detail.html',
        shipment=shipment,
        timeline=timeline
    )


# ============== API路由 ==============

@shipment_bp.route('/api/create', methods=['POST'])
@login_required
@permission_required('shipment', 'create')
def api_create():
    """创建发货单"""
    try:
        data = request.get_json()
        sales_order_id = data.get('sales_order_id')

        if not sales_order_id:
            return jsonify({'success': False, 'message': '缺少客户订单ID'})

        # 构建发货信息
        shipment_data = {
            'carrier': data.get('carrier'),
            'tracking_number': data.get('tracking_number'),
            'shipping_method': data.get('shipping_method'),
            'ship_from': data.get('ship_from'),
            'ship_to': data.get('ship_to'),
            'contact_name': data.get('contact_name'),
            'contact_phone': data.get('contact_phone'),
            'total_packages': data.get('total_packages', 1),
            'notes': data.get('notes')
        }

        # 处理日期
        if data.get('ship_date'):
            try:
                shipment_data['ship_date'] = datetime.strptime(data['ship_date'], '%Y-%m-%d')
            except ValueError:
                pass

        if data.get('expected_arrival'):
            try:
                shipment_data['expected_arrival'] = datetime.strptime(data['expected_arrival'], '%Y-%m-%d')
            except ValueError:
                pass

        # 处理运费
        if data.get('freight_cost'):
            try:
                shipment_data['freight_cost'] = Decimal(str(data['freight_cost']))
            except:
                pass

        shipment_data['freight_payer'] = data.get('freight_payer')

        # 处理发货明细
        details = data.get('details', [])
        if not details:
            return jsonify({'success': False, 'message': '请选择要发货的产品'})

        # 创建发货单
        shipment, error = ShipmentService.create_shipment(
            sales_order_id, shipment_data, details, current_user.id
        )

        if error:
            return jsonify({'success': False, 'message': error})

        return jsonify({
            'success': True,
            'message': f'发货单 {shipment.shipment_number} 创建成功',
            'shipment_id': shipment.id,
            'shipment_number': shipment.shipment_number,
            'redirect_url': url_for('shipment.detail_view', shipment_id=shipment.id)
        })

    except Exception as e:
        logger.error(f"创建发货单失败: {str(e)}")
        return jsonify({'success': False, 'message': f'创建失败: {str(e)}'})


@shipment_bp.route('/api/<int:shipment_id>', methods=['GET'])
@login_required
@permission_required('shipment', 'view')
def api_get_shipment(shipment_id):
    """获取发货单详情"""
    shipment = Shipment.query.get(shipment_id)

    if not shipment:
        return jsonify({'success': False, 'message': '发货单不存在'})

    return jsonify({
        'success': True,
        'shipment': {
            'id': shipment.id,
            'shipment_number': shipment.shipment_number,
            'status': shipment.status,
            'status_label': shipment.status_label,
            'sales_order_number': shipment.sales_order.order_number if shipment.sales_order else '',
            'carrier': shipment.carrier,
            'tracking_number': shipment.tracking_number,
            'shipping_method': shipment.shipping_method,
            'ship_date': shipment.formatted_ship_date,
            'expected_arrival': shipment.formatted_expected_arrival,
            'actual_arrival': shipment.actual_arrival.strftime('%Y-%m-%d') if shipment.actual_arrival else '',
            'ship_to': shipment.ship_to,
            'contact_name': shipment.contact_name,
            'contact_phone': shipment.contact_phone,
            'total_packages': shipment.total_packages,
            'total_quantity': shipment.total_quantity,
            'received_by': shipment.received_by,
            'received_date': shipment.received_date.strftime('%Y-%m-%d %H:%M') if shipment.received_date else '',
            'details': [{
                'id': d.id,
                'product_name': d.product_name,
                'product_model': d.product_model,
                'quantity': d.quantity,
                'unit': d.unit,
                'received_quantity': d.received_quantity,
                'status': d.status
            } for d in shipment.details]
        }
    })


@shipment_bp.route('/api/<int:shipment_id>/ship', methods=['POST'])
@login_required
@permission_required('shipment', 'edit')
def api_confirm_ship(shipment_id):
    """确认发货"""
    data = request.get_json() or {}
    ship_date = None

    if data.get('ship_date'):
        try:
            ship_date = datetime.strptime(data['ship_date'], '%Y-%m-%d')
        except ValueError:
            pass

    success, message = ShipmentService.confirm_shipment(
        shipment_id, current_user.id, ship_date
    )
    return jsonify({'success': success, 'message': message})


@shipment_bp.route('/api/<int:shipment_id>/receive', methods=['POST'])
@login_required
@permission_required('shipment', 'edit')
def api_confirm_receive(shipment_id):
    """确认签收"""
    try:
        data = request.get_json() or {}

        receipt_info = {
            'received_by': data.get('received_by'),
            'received_notes': data.get('received_notes'),
            'delivery_proof': data.get('delivery_proof', [])
        }

        # 处理签收日期
        if data.get('received_date'):
            try:
                receipt_info['received_date'] = datetime.strptime(
                    data['received_date'], '%Y-%m-%d'
                )
            except ValueError:
                receipt_info['received_date'] = datetime.now()
        else:
            receipt_info['received_date'] = datetime.now()

        success, message = ShipmentService.confirm_receipt(
            shipment_id, receipt_info, current_user.id
        )
        return jsonify({'success': success, 'message': message})

    except Exception as e:
        logger.error(f"确认签收失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


@shipment_bp.route('/api/<int:shipment_id>/tracking', methods=['GET'])
@login_required
@permission_required('shipment', 'view')
def api_get_tracking(shipment_id):
    """获取物流跟踪信息"""
    timeline = ShipmentService.get_tracking_timeline(shipment_id)
    return jsonify({'success': True, 'timeline': timeline})


@shipment_bp.route('/api/<int:shipment_id>/tracking', methods=['PUT'])
@login_required
@permission_required('shipment', 'edit')
def api_update_tracking(shipment_id):
    """更新物流跟踪信息"""
    try:
        data = request.get_json()
        tracking_info = {}

        if 'carrier' in data:
            tracking_info['carrier'] = data['carrier']
        if 'tracking_number' in data:
            tracking_info['tracking_number'] = data['tracking_number']
        if 'status' in data:
            tracking_info['status'] = data['status']
        if data.get('expected_arrival'):
            try:
                tracking_info['expected_arrival'] = datetime.strptime(
                    data['expected_arrival'], '%Y-%m-%d'
                )
            except ValueError:
                pass

        success, message = ShipmentService.update_tracking(
            shipment_id, tracking_info, current_user.id
        )
        return jsonify({'success': success, 'message': message})

    except Exception as e:
        logger.error(f"更新物流信息失败: {str(e)}")
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})


@shipment_bp.route('/api/list', methods=['GET'])
@login_required
@permission_required('shipment', 'view')
def api_list():
    """获取发货单列表数据"""
    status = request.args.get('status', '')
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Shipment.query

    if status:
        query = query.filter(Shipment.status == status)
    if search:
        query = query.filter(
            db.or_(
                Shipment.shipment_number.ilike(f'%{search}%'),
                Shipment.tracking_number.ilike(f'%{search}%')
            )
        )

    query = query.order_by(Shipment.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    shipments_data = [{
        'id': s.id,
        'shipment_number': s.shipment_number,
        'sales_order_number': s.sales_order.order_number if s.sales_order else '',
        'carrier': s.carrier,
        'tracking_number': s.tracking_number,
        'status': s.status,
        'status_label': s.status_label,
        'ship_date': s.formatted_ship_date,
        'total_quantity': s.total_quantity
    } for s in pagination.items]

    return jsonify({
        'success': True,
        'shipments': shipments_data,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    })


@shipment_bp.route('/api/stats', methods=['GET'])
@login_required
@permission_required('shipment', 'view')
def api_stats():
    """获取发货统计数据"""
    stats = ShipmentService.get_shipment_statistics()
    return jsonify({'success': True, 'stats': stats})


# ============== 辅助路由 ==============

@shipment_bp.route('/api/order/<int:order_id>/shippable-details', methods=['GET'])
@login_required
@permission_required('shipment', 'view')
def api_get_shippable_details(order_id):
    """获取订单可发货的明细列表"""
    order = SalesOrder.query.get(order_id)
    if not order:
        return jsonify({'success': False, 'message': '订单不存在'})

    # 获取可发货的明细
    shippable_details = []
    for detail in order.details:
        remaining = detail.remaining_to_ship
        if remaining > 0:
            shippable_details.append({
                'id': detail.id,
                'product_id': detail.product_id,
                'product_name': detail.product_name,
                'product_model': detail.product_model,
                'quantity': detail.quantity,
                'shipped_quantity': detail.shipped_quantity,
                'remaining_to_ship': remaining,
                'unit': detail.unit
            })

    return jsonify({
        'success': True,
        'order': {
            'id': order.id,
            'order_number': order.order_number,
            'customer_name': order.customer.company_name if order.customer else '',
            'delivery_address': order.delivery_address,
            'delivery_contact': order.delivery_contact,
            'delivery_phone': order.delivery_phone
        },
        'details': shippable_details
    })
