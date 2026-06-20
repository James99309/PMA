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
from app.decorators import admin_required
import logging

logger = logging.getLogger(__name__)

product_sn_bp = Blueprint('product_sn', __name__, url_prefix='/product-sn')


# ============== 页面路由 ==============

@product_sn_bp.route('/')
@login_required
@admin_required
def list_view():
    """序列号查询页(AT 设计 · 搜索为中心,无列表/分页/筛选)"""
    total = ProductSerialNumber.query.count()
    return render_template('product_sn/at_list.html', total_sn=total)


def _sn_to_dict(sn, brief=False):
    """SN ORM → JSON dict。brief=True 时只返回搜索摘要字段。

    供应商 / 入库公司 fallback:
      - supplier_id 为空 → 从 purchase_order.company 推断(PO 的 company_id 就是供应商)
      - inventory.company 为空 → 不再尝试推断(避免误导)
    """
    # 供应商:优先 SN.supplier,否则用 PO.company
    supplier_name = ''
    if sn.supplier:
        supplier_name = sn.supplier.company_name
    elif sn.purchase_order and sn.purchase_order.company:
        supplier_name = sn.purchase_order.company.company_name + '(自 PO)'

    base = {
        'id': sn.id,
        'serial_number': sn.serial_number,
        'status': sn.status,
        'status_label': sn.status_label,
        'product_name': sn.product.product_name if sn.product else '',
        'product_model': sn.product.model if sn.product else '',
        'shipment_number': sn.shipment.shipment_number if sn.shipment else '',
    }
    if brief:
        return base
    base.update({
        'supplier_name': supplier_name,
        'warehouse_location': sn.warehouse_location or '',
        'warehouse_in_date': sn.warehouse_in_date.strftime('%Y-%m-%d') if sn.warehouse_in_date else '',
        'purchase_order_number': sn.purchase_order.order_number if sn.purchase_order else '',
        'sales_order_number': sn.sales_order.order_number if sn.sales_order else '',
        'customer_name': sn.customer.company_name if sn.customer else '',
        'inventory_company': (sn.inventory.company.company_name
                              if sn.inventory and getattr(sn.inventory, 'company', None) else ''),
        'is_in_stock': bool(sn.inventory_id),
    })
    return base


@product_sn_bp.route('/api/search')
@login_required
@admin_required
def api_search():
    """SN 搜索：精确匹配返完整详情；模糊匹配返简略列表（最多 20 条）。"""
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'success': True, 'mode': 'empty', 'total': 0, 'results': []})

    # 精确
    exact = ProductSerialNumber.query.filter_by(serial_number=q).first()
    if exact:
        return jsonify({'success': True, 'mode': 'exact', 'total': 1,
                        'results': [_sn_to_dict(exact, brief=False)]})

    # 模糊
    base_q = ProductSerialNumber.query.filter(
        ProductSerialNumber.serial_number.ilike(f'%{q}%')
    )
    total = base_q.count()
    rows = base_q.order_by(ProductSerialNumber.serial_number.asc()).limit(20).all()
    return jsonify({'success': True, 'mode': 'fuzzy', 'total': total,
                    'results': [_sn_to_dict(sn, brief=True) for sn in rows]})


@product_sn_bp.route('/api/<int:sn_id>')
@login_required
@admin_required
def api_get_sn(sn_id):
    """SN 详情(就地展开用)"""
    sn = ProductSerialNumber.query.get_or_404(sn_id)
    return jsonify({'success': True, 'sn': _sn_to_dict(sn, brief=False)})


@product_sn_bp.route('/<int:sn_id>')
@login_required
@admin_required
def detail_view(sn_id):
    """序列号详情页(AT 设计)"""
    from app.helpers.at_product_sn_helpers import (
        build_sn_stages_data, normalize_sn_timeline, sn_status_meta,
    )
    sn = ProductSerialNumber.query.get_or_404(sn_id)
    timeline_raw = ProductSNService.get_timeline(sn_id)

    return render_template(
        'product_sn/at_detail.html',
        sn=sn,
        stages=build_sn_stages_data(sn),
        timeline=normalize_sn_timeline(timeline_raw),
        status_meta=sn_status_meta(sn.status),
    )


# ============== API路由 ==============

@product_sn_bp.route('/api/create', methods=['POST'])
@login_required
@admin_required
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
@admin_required
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
@admin_required
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


@product_sn_bp.route('/api/<int:sn_id>/stock-in', methods=['POST'])
@login_required
@admin_required
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
@admin_required
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
@admin_required
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
@admin_required
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


@product_sn_bp.route('/api/available', methods=['GET'])
@login_required
@admin_required
def api_get_available():
    """获取可用序列号列表(用于发货选择)— 由 shipment 流程调用"""
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
