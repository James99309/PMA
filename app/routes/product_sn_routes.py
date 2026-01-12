# -*- coding: utf-8 -*-
"""
序列号管理路由蓝图
管理产品序列号的录入、查询和生命周期追溯
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models.product_serial_number import ProductSerialNumber, SerialNumberHistory
from app.models.product import Product
from app.services.product_sn_service import ProductSNService
from app.decorators import permission_required
import logging

logger = logging.getLogger(__name__)

product_sn_bp = Blueprint('product_sn', __name__, url_prefix='/product-sn')


# ============== 页面路由 ==============

@product_sn_bp.route('/')
@login_required
@permission_required('inventory', 'view')
def list_view():
    """序列号列表页"""
    # 获取筛选参数
    status = request.args.get('status', '')
    product_id = request.args.get('product_id', '', type=int)
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # 基础查询
    query = ProductSerialNumber.query

    # 状态筛选
    if status:
        query = query.filter(ProductSerialNumber.status == status)

    # 产品筛选
    if product_id:
        query = query.filter(ProductSerialNumber.product_id == product_id)

    # 搜索
    if search:
        query = query.filter(
            db.or_(
                ProductSerialNumber.serial_number.ilike(f'%{search}%'),
                ProductSerialNumber.batch_number.ilike(f'%{search}%')
            )
        )

    # 排序和分页
    query = query.order_by(ProductSerialNumber.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    serial_numbers = pagination.items

    # 获取统计数据
    stats = ProductSNService.get_statistics()

    # 获取产品列表（用于筛选）- Product 模型使用 status 字段，排序用 product_name 列
    products = Product.query.filter(Product.status == 'active').order_by(Product.product_name).all()

    return render_template(
        'product_sn/tw_list.html',
        serial_numbers=serial_numbers,
        pagination=pagination,
        stats=stats,
        products=products,
        current_status=status,
        current_product_id=product_id,
        search=search
    )


@product_sn_bp.route('/<int:sn_id>')
@login_required
@permission_required('inventory', 'view')
def detail_view(sn_id):
    """序列号详情页"""
    sn = ProductSerialNumber.query.get_or_404(sn_id)

    # 获取生命周期时间线
    timeline = ProductSNService.get_timeline(sn_id)

    return render_template(
        'product_sn/tw_detail.html',
        sn=sn,
        timeline=timeline
    )


# ============== API路由 ==============

@product_sn_bp.route('/api/create', methods=['POST'])
@login_required
@permission_required('inventory', 'create')
def api_create():
    """创建单个序列号"""
    try:
        data = request.get_json()
        serial_number = data.get('serial_number', '').strip()
        product_id = data.get('product_id')

        if not serial_number:
            return jsonify({'success': False, 'message': '请输入序列号'})

        if not product_id:
            return jsonify({'success': False, 'message': '请选择产品'})

        sn, error = ProductSNService.create_serial_number(
            serial_number=serial_number,
            product_id=product_id,
            user_id=current_user.id,
            purchase_order_id=data.get('purchase_order_id'),
            purchase_detail_id=data.get('purchase_detail_id'),
            batch_number=data.get('batch_number'),
            notes=data.get('notes')
        )

        if error:
            return jsonify({'success': False, 'message': error})

        return jsonify({
            'success': True,
            'message': f'序列号 {serial_number} 创建成功',
            'sn_id': sn.id,
            'serial_number': sn.serial_number
        })

    except Exception as e:
        logger.error(f"创建序列号失败: {str(e)}")
        return jsonify({'success': False, 'message': f'创建失败: {str(e)}'})


@product_sn_bp.route('/api/batch-create', methods=['POST'])
@login_required
@permission_required('inventory', 'create')
def api_batch_create():
    """批量创建序列号"""
    try:
        data = request.get_json()
        serial_numbers_data = data.get('serial_numbers', [])

        if not serial_numbers_data:
            return jsonify({'success': False, 'message': '没有要导入的数据'})

        success_count, fail_count, errors = ProductSNService.batch_create_serial_numbers(
            serial_numbers_data, current_user.id
        )

        return jsonify({
            'success': True,
            'message': f'导入完成：成功 {success_count} 条，失败 {fail_count} 条',
            'success_count': success_count,
            'fail_count': fail_count,
            'errors': errors
        })

    except Exception as e:
        logger.error(f"批量创建序列号失败: {str(e)}")
        return jsonify({'success': False, 'message': f'导入失败: {str(e)}'})


@product_sn_bp.route('/api/validate-import', methods=['POST'])
@login_required
@permission_required('inventory', 'create')
def api_validate_import():
    """验证导入数据"""
    try:
        data = request.get_json()
        import_data = data.get('data', [])

        valid, duplicates, errors = ProductSNService.validate_import_data(import_data)

        return jsonify({
            'success': True,
            'valid': valid,
            'duplicates': duplicates,
            'errors': errors,
            'summary': {
                'valid_count': len(valid),
                'duplicate_count': len(duplicates),
                'error_count': len(errors)
            }
        })

    except Exception as e:
        logger.error(f"验证导入数据失败: {str(e)}")
        return jsonify({'success': False, 'message': f'验证失败: {str(e)}'})


@product_sn_bp.route('/api/<int:sn_id>', methods=['GET'])
@login_required
@permission_required('inventory', 'view')
def api_get_detail(sn_id):
    """获取序列号详情"""
    sn = ProductSerialNumber.query.get(sn_id)

    if not sn:
        return jsonify({'success': False, 'message': '序列号不存在'})

    return jsonify({
        'success': True,
        'serial_number': {
            'id': sn.id,
            'serial_number': sn.serial_number,
            'product_name': sn.product.name if sn.product else '',
            'product_model': sn.product.model if sn.product else '',
            'batch_number': sn.batch_number,
            'status': sn.status,
            'status_label': sn.status_label,
            'warehouse_location': sn.warehouse_location,
            'warehouse_in_date': sn.formatted_warehouse_in_date,
            'ship_out_date': sn.formatted_ship_out_date,
            'purchase_order_number': sn.purchase_order.order_number if sn.purchase_order else '',
            'sales_order_number': sn.sales_order.order_number if sn.sales_order else '',
            'customer_name': sn.customer.company_name if sn.customer else '',
            'notes': sn.notes
        }
    })


@product_sn_bp.route('/api/<int:sn_id>/stock-in', methods=['POST'])
@login_required
@permission_required('inventory', 'edit')
def api_stock_in(sn_id):
    """序列号入库"""
    try:
        data = request.get_json() or {}
        warehouse_location = data.get('warehouse_location', '').strip()

        if not warehouse_location:
            return jsonify({'success': False, 'message': '请输入仓库位置'})

        success, message = ProductSNService.stock_in(
            serial_number_id=sn_id,
            warehouse_location=warehouse_location,
            user_id=current_user.id,
            inventory_id=data.get('inventory_id'),
            notes=data.get('notes')
        )

        return jsonify({'success': success, 'message': message})

    except Exception as e:
        logger.error(f"序列号入库失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


@product_sn_bp.route('/api/<int:sn_id>/reserve', methods=['POST'])
@login_required
@permission_required('inventory', 'edit')
def api_reserve(sn_id):
    """预留序列号"""
    try:
        data = request.get_json() or {}
        sales_order_id = data.get('sales_order_id')

        if not sales_order_id:
            return jsonify({'success': False, 'message': '请选择客户订单'})

        success, message = ProductSNService.reserve(
            serial_number_id=sn_id,
            sales_order_id=sales_order_id,
            user_id=current_user.id
        )

        return jsonify({'success': success, 'message': message})

    except Exception as e:
        logger.error(f"序列号预留失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


@product_sn_bp.route('/api/<int:sn_id>/ship', methods=['POST'])
@login_required
@permission_required('inventory', 'edit')
def api_ship(sn_id):
    """序列号发货"""
    try:
        data = request.get_json() or {}
        shipment_id = data.get('shipment_id')
        destination = data.get('destination', '').strip()

        if not shipment_id:
            return jsonify({'success': False, 'message': '请选择发货单'})

        success, message = ProductSNService.ship(
            serial_number_id=sn_id,
            shipment_id=shipment_id,
            destination=destination,
            user_id=current_user.id
        )

        return jsonify({'success': success, 'message': message})

    except Exception as e:
        logger.error(f"序列号发货失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


@product_sn_bp.route('/api/<int:sn_id>/deliver', methods=['POST'])
@login_required
@permission_required('inventory', 'edit')
def api_deliver(sn_id):
    """确认序列号交付"""
    try:
        data = request.get_json() or {}
        customer_id = data.get('customer_id')

        if not customer_id:
            return jsonify({'success': False, 'message': '请选择客户'})

        success, message = ProductSNService.deliver(
            serial_number_id=sn_id,
            customer_id=customer_id,
            user_id=current_user.id,
            project_id=data.get('project_id')
        )

        return jsonify({'success': success, 'message': message})

    except Exception as e:
        logger.error(f"序列号交付确认失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


@product_sn_bp.route('/api/<int:sn_id>/timeline', methods=['GET'])
@login_required
@permission_required('inventory', 'view')
def api_get_timeline(sn_id):
    """获取序列号时间线"""
    timeline = ProductSNService.get_timeline(sn_id)
    return jsonify({'success': True, 'timeline': timeline})


@product_sn_bp.route('/api/available', methods=['GET'])
@login_required
@permission_required('inventory', 'view')
def api_get_available():
    """获取可用序列号列表（用于发货选择）"""
    product_id = request.args.get('product_id', type=int)
    status = request.args.get('status', 'in_stock')
    limit = request.args.get('limit', 100, type=int)

    if not product_id:
        return jsonify({'success': False, 'message': '请指定产品'})

    serial_numbers = ProductSNService.get_available_serial_numbers(
        product_id=product_id,
        status=status,
        limit=limit
    )

    return jsonify({'success': True, 'serial_numbers': serial_numbers})


@product_sn_bp.route('/api/search', methods=['GET'])
@login_required
@permission_required('inventory', 'view')
def api_search():
    """搜索序列号"""
    query = request.args.get('q', '').strip()

    if not query:
        return jsonify({'success': False, 'message': '请输入搜索关键词'})

    sn = ProductSNService.search_serial_number(query)

    if not sn:
        return jsonify({'success': False, 'message': '未找到序列号'})

    return jsonify({
        'success': True,
        'serial_number': {
            'id': sn.id,
            'serial_number': sn.serial_number,
            'product_name': sn.product.name if sn.product else '',
            'status': sn.status,
            'status_label': sn.status_label
        }
    })


@product_sn_bp.route('/api/list', methods=['GET'])
@login_required
@permission_required('inventory', 'view')
def api_list():
    """获取序列号列表数据（用于AJAX刷新）"""
    status = request.args.get('status', '')
    product_id = request.args.get('product_id', '', type=int)
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = ProductSerialNumber.query

    if status:
        query = query.filter(ProductSerialNumber.status == status)
    if product_id:
        query = query.filter(ProductSerialNumber.product_id == product_id)
    if search:
        query = query.filter(
            db.or_(
                ProductSerialNumber.serial_number.ilike(f'%{search}%'),
                ProductSerialNumber.batch_number.ilike(f'%{search}%')
            )
        )

    query = query.order_by(ProductSerialNumber.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    data = [{
        'id': sn.id,
        'serial_number': sn.serial_number,
        'product_name': sn.product.name if sn.product else '',
        'product_model': sn.product.model if sn.product else '',
        'batch_number': sn.batch_number,
        'status': sn.status,
        'status_label': sn.status_label,
        'warehouse_location': sn.warehouse_location,
        'warehouse_in_date': sn.formatted_warehouse_in_date,
        'created_at': sn.created_at.strftime('%Y-%m-%d') if sn.created_at else ''
    } for sn in pagination.items]

    return jsonify({
        'success': True,
        'serial_numbers': data,
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': pagination.page
    })


@product_sn_bp.route('/api/stats', methods=['GET'])
@login_required
@permission_required('inventory', 'view')
def api_stats():
    """获取序列号统计数据"""
    stats = ProductSNService.get_statistics()
    return jsonify({'success': True, 'stats': stats})
