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
    """客户订单列表页(AT 设计)"""
    # 6 个 tab:全部 / 草稿 / 已确认 / 备货中 / 已发货 / 已完成
    tab = request.args.get('tab', 'all')
    customer_id = request.args.get('customer_id', '')
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 30, type=int)

    base_query = get_viewable_data(SalesOrder, current_user)
    query = base_query

    tab_filter_map = {
        'draft':     ['draft'],
        'confirmed': ['confirmed', 'preparing'],
        'shipped':   ['shipped', 'delivered'],
        'completed': ['completed'],
        'cancelled': ['cancelled'],
    }
    if tab in tab_filter_map:
        query = query.filter(SalesOrder.status.in_(tab_filter_map[tab]))
    else:
        # 全部 tab 默认不计入已取消(已取消有独立 tab 查看)
        query = query.filter(SalesOrder.status != 'cancelled')

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
    orders = pagination.items

    stats = SalesOrderService.get_order_statistics(base_query=base_query)
    # 聚合 6 tab 计数
    tab_counts = {
        # 全部 = total - cancelled(与列表过滤一致)
        'all':       max(0, stats.get('total', 0) - stats.get('cancelled', 0)),
        'draft':     stats.get('draft', 0),
        'confirmed': stats.get('confirmed', 0) + stats.get('preparing', 0),
        'shipped':   stats.get('shipped', 0) + stats.get('delivered', 0),
        'completed': stats.get('completed', 0),
        'cancelled': stats.get('cancelled', 0),
    }

    # 客户筛选下拉:仅列出当前用户「可见订单」中实际出现的客户，
    # 避免裸查全部公司导致跨企业泄漏(代理商等只应看到自己企业)
    viewable_customer_ids = [
        cid for (cid,) in base_query.with_entities(SalesOrder.customer_id).distinct().all()
        if cid
    ]
    customers = Company.query.filter(
        Company.id.in_(viewable_customer_ids),
        Company.is_deleted == False
    ).order_by(Company.company_name).all() if viewable_customer_ids else []

    # 货币选项:基于产品库中实际拥有价格的所有货币(Product 主货币 + ProductRegionPrice 区域价货币)
    from app.utils.dictionary_helpers import get_available_product_currencies
    from app.utils.currency_helpers import get_system_currency
    currency_options = get_available_product_currencies()
    default_currency = get_system_currency()

    return render_template(
        'sales_order/at_list.html',
        orders=orders,
        pagination=pagination,
        tab_counts=tab_counts,
        customers=customers,
        current_tab=tab,
        current_customer_id=customer_id,
        search=search,
        currency_options=currency_options,
        default_currency=default_currency,
    )


@sales_order_bp.route('/<int:order_id>')
@login_required
@permission_required('sales_order', 'view')
def detail_view(order_id):
    """客户订单详情页(AT 设计)— 5 阶段从客户视角聚合 PO 状态。"""
    from app.helpers.at_sales_order_helpers import (
        build_so_stages_data, build_so_items_data,
        build_so_shipments_data, build_so_current_action,
    )
    query = get_viewable_data(SalesOrder, current_user)
    order = query.filter(SalesOrder.id == order_id).first()
    if not order:
        flash('订单不存在或无权访问', 'error')
        return redirect(url_for('sales_order.list_view'))

    stages = build_so_stages_data(order)
    items = build_so_items_data(order)
    shipments = build_so_shipments_data(order)
    current_action = build_so_current_action(order, stages)
    currency_symbol = '$' if (order.currency or 'CNY') == 'USD' else '¥'
    is_referenced = SalesOrderService.is_referenced_by_po(order)

    return render_template(
        'sales_order/at_detail.html',
        order=order,
        stages=stages,
        items=items,
        shipments=shipments,
        current_action=current_action,
        currency_symbol=currency_symbol,
        is_referenced=is_referenced,
    )


# 旧 AT URL 兼容 — `/at` 和 `/<id>/at` 301 跳新主入口(避免老书签 404)
@sales_order_bp.route('/at')
@login_required
def _legacy_at_list():
    return redirect(url_for('sales_order.list_view'), code=301)


@sales_order_bp.route('/<int:order_id>/at')
@login_required
def _legacy_at_detail(order_id):
    return redirect(url_for('sales_order.detail_view', order_id=order_id), code=301)


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
                'product_mn': d.product_mn or (d.product.product_mn if d.product else '') or '',
                'quantity': d.quantity,
                'unit': d.unit,
                'unit_price': float(d.unit_price or 0),
                'total_price': float(d.total_price or 0),
                'procured_quantity': d.procured_quantity or 0,
                'remaining_to_procure': d.remaining_to_procure,
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
    """取消订单(仅非草稿、无 PO 引用、未发货时可取消)"""
    data = request.get_json() or {}
    reason = data.get('reason')
    success, message = SalesOrderService.cancel_order(order_id, current_user.id, reason)
    return jsonify({'success': success, 'message': message})


@sales_order_bp.route('/api/<int:order_id>/delete', methods=['POST'])
@login_required
@permission_required('sales_order', 'edit')
def api_delete(order_id):
    """物理删除草稿订单(仅 draft)"""
    success, message = SalesOrderService.delete_order(order_id, current_user.id)
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


@sales_order_bp.route('/api/create-direct', methods=['POST'])
@login_required
@permission_required('sales_order', 'create')
def api_create_direct():
    """直接创建客户订单（不通过批价单）"""
    try:
        data = request.get_json()

        # 验证必填字段
        customer_id = data.get('customer_id')
        if not customer_id:
            return jsonify({'success': False, 'message': '请选择客户'})

        # 验证客户存在
        customer = Company.query.filter_by(id=customer_id, is_deleted=False).first()
        if not customer:
            return jsonify({'success': False, 'message': '客户不存在'})

        # 验证明细
        details_data = data.get('details', [])
        if not details_data:
            return jsonify({'success': False, 'message': '请至少添加一个产品'})

        # 处理交付日期
        delivery_date = None
        if data.get('delivery_date'):
            try:
                delivery_date = datetime.strptime(data['delivery_date'], '%Y-%m-%d')
            except ValueError:
                pass

        # 创建订单
        sales_order = SalesOrder(
            order_number=SalesOrderService.generate_order_number(),
            customer_id=int(customer_id),
            status='draft',
            created_by_id=current_user.id,
            delivery_date=delivery_date,
            delivery_address=data.get('delivery_address'),
            delivery_contact=data.get('delivery_contact'),
            delivery_phone=data.get('delivery_phone'),
            delivery_email=data.get('delivery_email'),
            shipping_method=data.get('shipping_method'),
            freight_terms=data.get('freight_terms'),
            incoterms=data.get('incoterms'),
            notes=data.get('notes'),
            currency='CNY'
        )

        db.session.add(sales_order)
        db.session.flush()  # 获取ID

        # 创建订单明细
        from decimal import Decimal
        total_amount = Decimal('0')
        total_quantity = 0

        for idx, item in enumerate(details_data):
            product_name = (item.get('product_name') or '').strip()
            if not product_name:
                return jsonify({'success': False, 'message': f'第 {idx + 1} 行产品名称不能为空'})

            quantity = item.get('quantity')
            try:
                quantity = int(quantity)
                if quantity <= 0:
                    raise ValueError
            except (TypeError, ValueError):
                return jsonify({'success': False, 'message': f'第 {idx + 1} 行数量无效'})

            unit_price = Decimal(str(item.get('unit_price') or 0))
            discount = Decimal(str(item.get('discount') or 1))
            line_total = unit_price * quantity * discount

            # 查找产品ID
            from app.models.product import Product
            product_id = item.get('product_id')
            product_obj = None
            if product_id:
                product_obj = Product.query.get(int(product_id))
            else:
                # 尝试通过产品名称+型号查找
                product_model = (item.get('product_model') or '').strip()
                q = Product.query.filter_by(name=product_name)
                if product_model:
                    q = q.filter_by(model=product_model)
                product_obj = q.first()
                product_id = product_obj.id if product_obj else None

            if not product_id:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': f'第 {idx + 1} 行产品 "{product_name}" 在产品库中未找到，请确认产品名称和型号'
                })

            # MN 编码:优先用前端传入(支持手工覆盖),其次自动从产品库取
            _mn = (item.get('product_mn') or '').strip()
            if not _mn and product_obj:
                _mn = (product_obj.product_mn or '').strip()

            detail = SalesOrderDetail(
                sales_order_id=sales_order.id,
                product_id=int(product_id),
                product_name=product_name,
                product_model=(item.get('product_model') or '').strip(),
                product_mn=_mn or None,
                quantity=quantity,
                unit=(item.get('unit') or '个').strip(),
                unit_price=unit_price,
                discount=discount,
                total_price=line_total,
                status='pending'
            )
            db.session.add(detail)

            total_amount += line_total
            total_quantity += quantity

        # 更新订单汇总
        sales_order.total_amount = total_amount
        sales_order.total_quantity = total_quantity

        db.session.commit()
        logger.info(f"直接创建客户订单 {sales_order.order_number}, 客户: {customer.company_name}")

        return jsonify({
            'success': True,
            'message': f'客户订单 {sales_order.order_number} 创建成功',
            'order_id': sales_order.id,
            'order_number': sales_order.order_number,
            'redirect_url': url_for('sales_order.detail_view', order_id=sales_order.id)
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"直接创建客户订单失败: {str(e)}")
        return jsonify({'success': False, 'message': f'创建失败: {str(e)}'})


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
