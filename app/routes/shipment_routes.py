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
from app.models.inventory import PurchaseOrder, PurchaseOrderDetail
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
    purchase_order_id = request.args.get('purchase_order_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # 基础查询
    query = Shipment.query

    # 状态筛选
    if status:
        query = query.filter(Shipment.status == status)

    # 采购订单筛选
    if purchase_order_id:
        query = query.filter(Shipment.purchase_order_id == purchase_order_id)

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
    import json as json_mod

    shipment = Shipment.query.get_or_404(shipment_id)

    # 获取物流时间线
    timeline = ShipmentService.get_tracking_timeline(shipment_id)

    # 解析文档 JSON 供模板使用
    courier_docs = []
    if shipment.documents:
        try:
            courier_docs = json_mod.loads(shipment.documents)
        except (json_mod.JSONDecodeError, TypeError):
            pass

    receipt_docs = []
    if shipment.delivery_proof:
        try:
            receipt_docs = json_mod.loads(shipment.delivery_proof)
        except (json_mod.JSONDecodeError, TypeError):
            pass

    return render_template(
        'shipment/tw_detail.html',
        shipment=shipment,
        timeline=timeline,
        courier_docs=courier_docs,
        receipt_docs=receipt_docs
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


@shipment_bp.route('/api/<int:shipment_id>/delete', methods=['DELETE'])
@login_required
@permission_required('shipment', 'edit')
def api_delete_shipment(shipment_id):
    """删除发货单（仅 pending 且无快递单时可删）"""
    try:
        shipment = Shipment.query.get_or_404(shipment_id)
        if shipment.status != 'pending':
            return jsonify({'success': False, 'message': '只能删除待发货状态的发货单'})
        if shipment.documents:
            return jsonify({'success': False, 'message': '已上传快递单的发货单不能删除'})

        # 恢复 PO 明细的 dispatched_quantity 和 SO 明细的 shipped_quantity
        from app.models.sales_order import SalesOrderDetail
        for detail in shipment.details:
            if detail.purchase_order_detail_id:
                po_detail = PurchaseOrderDetail.query.get(detail.purchase_order_detail_id)
                if po_detail:
                    po_detail.dispatched_quantity = max(0, (po_detail.dispatched_quantity or 0) - detail.quantity)
            if detail.sales_order_detail_id:
                so_detail = SalesOrderDetail.query.get(detail.sales_order_detail_id)
                if so_detail:
                    so_detail.shipped_quantity = max(0, (so_detail.shipped_quantity or 0) - detail.quantity)
            db.session.delete(detail)

        db.session.delete(shipment)
        db.session.commit()
        return jsonify({'success': True, 'message': '发货单已删除'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除发货单失败: {str(e)}")
        return jsonify({'success': False, 'message': f'删除失败: {str(e)}'})


@shipment_bp.route('/api/<int:shipment_id>/ship', methods=['POST'])
@login_required
@permission_required('shipment', 'edit')
def api_confirm_ship(shipment_id):
    """确认发货（支持快递单文件上传）

    接受 JSON 或 FormData：
    - JSON: { ship_date: '2026-01-01' }
    - FormData: file (快递单文件) + ship_date
    上传快递单后自动变更状态为 shipped
    """
    try:
        import json as json_mod, uuid

        shipment = Shipment.query.get(shipment_id)
        if not shipment:
            return jsonify({'success': False, 'message': '发货单不存在'})

        if shipment.status != 'pending':
            return jsonify({'success': False, 'message': f'当前状态 {shipment.status_label} 不允许确认发货'})

        # 兼容 JSON 和 FormData
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json() or {}
            courier_file = None
        else:
            data = request.form.to_dict()
            courier_file = request.files.get('file')

        # 处理快递单文件上传
        if courier_file and courier_file.filename:
            from app.helpers.purchase_order_helpers import upload_file_to_storage
            po = shipment.purchase_order
            if po:
                file_ext = courier_file.filename.rsplit('.', 1)[-1].lower() if '.' in courier_file.filename else 'pdf'
                content_types = {'pdf': 'application/pdf', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png'}
                content_type = content_types.get(file_ext, 'application/octet-stream')
                unique_id = uuid.uuid4().hex[:8]
                filename = f"courier_{datetime.now().strftime('%Y%m%d')}_{unique_id}.{file_ext}"
                file_content = courier_file.read()
                file_url = upload_file_to_storage(po, file_content, filename, content_type, subfolder='courier')
                if file_url:
                    # 合并到现有 documents
                    existing_docs = []
                    if shipment.documents:
                        try:
                            existing_docs = json_mod.loads(shipment.documents)
                        except (json_mod.JSONDecodeError, TypeError):
                            pass
                    existing_docs.append({'name': courier_file.filename, 'url': file_url})
                    shipment.documents = json_mod.dumps(existing_docs)

        # 解析发货日期
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

    except Exception as e:
        db.session.rollback()
        logger.error(f"确认发货失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


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

        if success:
            # Step 5: 检查该PO的所有发货单是否都已签收 → 自动推进验收入库
            shipment = Shipment.query.get(shipment_id)
            if shipment:
                _check_auto_acceptance(shipment)

        return jsonify({'success': success, 'message': message})

    except Exception as e:
        logger.error(f"确认签收失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


@shipment_bp.route('/api/<int:shipment_id>/receive-with-file', methods=['POST'])
@login_required
@permission_required('shipment', 'edit')
def api_confirm_receive_with_file(shipment_id):
    """确认签收（支持文件上传）- 供 tw_upload_confirm_modal 组件调用"""
    try:
        import json as json_mod, uuid

        shipment = Shipment.query.get(shipment_id)
        if not shipment:
            return jsonify({'success': False, 'message': '发货单不存在'})

        if shipment.status not in ['shipped', 'in_transit', 'delivered']:
            return jsonify({'success': False, 'message': f'当前状态 {shipment.status_label} 不允许签收'})

        # 处理签收回执文件
        delivery_proof = []
        file = request.files.get('file')
        if file and file.filename:
            from app.helpers.purchase_order_helpers import upload_file_to_storage
            po = shipment.purchase_order
            if po:
                file_ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else 'pdf'
                content_types = {'pdf': 'application/pdf', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png'}
                content_type = content_types.get(file_ext, 'application/octet-stream')
                unique_id = uuid.uuid4().hex[:8]
                filename = f"receipt_{datetime.now().strftime('%Y%m%d')}_{unique_id}.{file_ext}"
                file_content = file.read()
                file_url = upload_file_to_storage(po, file_content, filename, content_type, subfolder='receipt')
                if file_url:
                    delivery_proof.append({'name': file.filename, 'url': file_url})

        received_by = request.form.get('received_by', current_user.real_name or current_user.username)
        notes = request.form.get('notes', '')

        receipt_info = {
            'received_by': received_by,
            'received_notes': notes,
            'received_date': datetime.now(),
            'delivery_proof': delivery_proof
        }

        success, message = ShipmentService.confirm_receipt(
            shipment_id, receipt_info, current_user.id
        )

        if success:
            # Step 5: 检查该PO的所有发货单是否都已签收 → 自动推进验收入库
            _check_auto_acceptance(shipment)

        return jsonify({'success': success, 'message': message})

    except Exception as e:
        logger.error(f"确认签收（含文件）失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


def _check_auto_acceptance(shipment):
    """检查PO关联的所有发货单是否全部签收，自动推进验收入库"""
    try:
        po_id = shipment.purchase_order_id
        if not po_id:
            return

        po = PurchaseOrder.query.get(po_id)
        if not po or po.status in ['stored', 'completed', 'cancelled']:
            return

        # 条件1：所有PO明细都已发完
        all_dispatched = all(
            (d.dispatched_quantity or 0) >= d.quantity for d in po.details
        )
        if not all_dispatched:
            return

        # 条件2：所有发货单都已签收
        all_shipments = Shipment.query.filter_by(purchase_order_id=po_id).all()
        if not all_shipments:
            return
        all_received = all(s.status == 'received' for s in all_shipments)
        if not all_received:
            return

        # 两个条件都满足，自动推进PO到验收入库
        po.status = 'stored'
        po.production_status = 'completed'
        po.production_progress = 100
        po.acceptance_status = 'passed'
        po.acceptance_date = datetime.now()
        po.actual_arrival_date = datetime.now()

        # 备货型明细自动入库
        from app.utils.inventory_helpers import update_inventory
        for detail in po.details:
            if not detail.sales_order_detail_id:
                qty = detail.dispatched_quantity or detail.quantity or 0
                if qty > 0:
                    update_inventory(
                        company_id=po.company_id,
                        product_id=detail.product_id,
                        quantity_change=qty,
                        transaction_type='in',
                        reference_type='order',
                        reference_id=po.id,
                        description=f'采购订单 {po.order_number} 全部签收自动入库',
                        user_id=shipment.created_by_id
                    )

        db.session.commit()
        logger.info(f"采购订单 {po.order_number} 所有发货单已签收，自动推进验收入库")

    except Exception as e:
        logger.error(f"自动验收入库检查失败: {str(e)}")
        # 不要 rollback，因为签收操作已成功，自动验收失败不应影响签收结果


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


@shipment_bp.route('/api/po/<int:po_id>/dispatchable-details', methods=['GET'])
@login_required
@permission_required('shipment', 'view')
def api_get_dispatchable_details(po_id):
    """获取采购订单中可发货的明细列表

    可选参数 sales_order_id：如果指定，只返回能匹配该SO的明细
    """
    po = PurchaseOrder.query.get(po_id)
    if not po:
        return jsonify({'success': False, 'message': '采购订单不存在'})

    target_so_id = request.args.get('sales_order_id', type=int)

    from app.models.sales_order import SalesOrder, SalesOrderDetail
    dispatchable_details = []
    for detail in po.details:
        # PO可发 = 总量 - 已发出量
        po_remaining = max(0, detail.quantity - (detail.dispatched_quantity or 0))
        if po_remaining <= 0:
            continue

        so_remaining = None
        matched_so_detail_id = detail.sales_order_detail_id

        if target_so_id:
            # 指定了目标SO：只显示能匹配该SO的产品
            if detail.sales_order_detail_id:
                # PO明细已关联SO明细，检查是否属于目标SO
                so_detail = SalesOrderDetail.query.get(detail.sales_order_detail_id)
                if so_detail and so_detail.sales_order_id == target_so_id:
                    so_remaining = so_detail.remaining_to_ship
                else:
                    continue  # 不属于目标SO，跳过
            else:
                # PO明细未关联SO，尝试按product_id匹配目标SO的明细
                so_detail = SalesOrderDetail.query.filter_by(
                    sales_order_id=target_so_id,
                    product_id=detail.product_id
                ).first()
                if so_detail and so_detail.remaining_to_ship > 0:
                    so_remaining = so_detail.remaining_to_ship
                    matched_so_detail_id = so_detail.id
                else:
                    continue  # 目标SO中没有这个产品，跳过
        else:
            # 未指定SO（入仓库模式）：显示所有可发明细
            if detail.sales_order_detail_id:
                so_detail = SalesOrderDetail.query.get(detail.sales_order_detail_id)
                if so_detail:
                    so_remaining = so_detail.remaining_to_ship

        # 实际可发 = min(PO可发, SO可发)
        remaining = min(po_remaining, so_remaining) if so_remaining is not None else po_remaining

        if remaining > 0:
            dispatchable_details.append({
                'id': detail.id,
                'product_id': detail.product_id,
                'product_name': detail.product_name,
                'product_model': detail.product_model,
                'quantity': detail.quantity,
                'received_quantity': detail.received_quantity or 0,
                'dispatched_quantity': detail.dispatched_quantity or 0,
                'remaining_to_dispatch': remaining,
                'so_remaining_to_ship': so_remaining,
                'unit': detail.unit,
                'sales_order_detail_id': matched_so_detail_id
            })

    return jsonify({
        'success': True,
        'purchase_order': {
            'id': po.id,
            'order_number': po.order_number,
            'supplier_name': po.company.company_name if po.company else '',
        },
        'details': dispatchable_details
    })


@shipment_bp.route('/api/create-from-po', methods=['POST'])
@login_required
@permission_required('shipment', 'create')
def api_create_from_po():
    """从采购订单创建发货单（支持 JSON 和 FormData）"""
    try:
        import json as json_mod

        # 兼容 JSON 和 FormData 两种提交方式
        if request.content_type and 'application/json' in request.content_type:
            data = request.get_json()
            details = data.get('details', [])
            courier_file = None
        else:
            data = request.form.to_dict()
            details_str = data.get('details', '[]')
            try:
                details = json_mod.loads(details_str)
            except (json_mod.JSONDecodeError, TypeError):
                details = []
            courier_file = request.files.get('courier_document')

        purchase_order_id = data.get('purchase_order_id')
        if purchase_order_id:
            purchase_order_id = int(purchase_order_id)
        destination_type = data.get('destination_type')  # 'sales_order' or 'warehouse'
        sales_order_id = data.get('sales_order_id')
        if sales_order_id:
            sales_order_id = int(sales_order_id)

        if not purchase_order_id:
            return jsonify({'success': False, 'message': '缺少采购订单ID'})

        if not details:
            return jsonify({'success': False, 'message': '请选择要发货的产品'})

        if destination_type == 'sales_order' and not sales_order_id:
            return jsonify({'success': False, 'message': '请选择目标客户订单'})

        # 验证采购订单
        po = PurchaseOrder.query.get(purchase_order_id)
        if not po:
            return jsonify({'success': False, 'message': '采购订单不存在'})

        # 验证客户订单（如果有）
        sales_order = None
        if sales_order_id:
            sales_order = SalesOrder.query.get(sales_order_id)
            if not sales_order:
                return jsonify({'success': False, 'message': '客户订单不存在'})

        # 处理快递单文件上传
        courier_doc_info = None
        if courier_file and courier_file.filename:
            from app.helpers.purchase_order_helpers import upload_file_to_storage
            import uuid
            file_ext = courier_file.filename.rsplit('.', 1)[-1].lower() if '.' in courier_file.filename else 'pdf'
            content_types = {'pdf': 'application/pdf', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png'}
            content_type = content_types.get(file_ext, 'application/octet-stream')
            unique_id = uuid.uuid4().hex[:8]
            filename = f"courier_{datetime.now().strftime('%Y%m%d')}_{unique_id}.{file_ext}"
            file_content = courier_file.read()
            file_url = upload_file_to_storage(po, file_content, filename, content_type, subfolder='courier')
            if file_url:
                courier_doc_info = {'name': courier_file.filename, 'url': file_url}

        # 创建发货单
        shipment = Shipment(
            shipment_number=ShipmentService.generate_shipment_number(),
            purchase_order_id=purchase_order_id,
            sales_order_id=sales_order_id if destination_type == 'sales_order' else None,
            carrier=data.get('carrier'),
            tracking_number=data.get('tracking_number'),
            shipping_method=data.get('shipping_method'),
            ship_from=data.get('ship_from'),
            ship_to=data.get('ship_to'),
            contact_name=data.get('contact_name'),
            contact_phone=data.get('contact_phone'),
            total_packages=data.get('total_packages', 1),
            notes=data.get('notes'),
            status='pending',
            created_by_id=current_user.id
        )

        # 保存快递单文档信息
        if courier_doc_info:
            shipment.documents = json_mod.dumps([courier_doc_info])

        # 处理日期
        if data.get('ship_date'):
            try:
                shipment.ship_date = datetime.strptime(data['ship_date'], '%Y-%m-%d')
            except ValueError:
                pass

        if data.get('expected_arrival'):
            try:
                shipment.expected_arrival = datetime.strptime(data['expected_arrival'], '%Y-%m-%d')
            except ValueError:
                pass

        db.session.add(shipment)
        db.session.flush()  # 获取 shipment.id

        # 创建发货明细
        for item in details:
            po_detail_id = item.get('purchase_order_detail_id')
            quantity = int(item.get('quantity', 0))

            if quantity <= 0:
                continue

            # 验证PO明细
            po_detail = PurchaseOrderDetail.query.get(po_detail_id)
            if not po_detail:
                db.session.rollback()
                return jsonify({'success': False, 'message': f'采购明细 ID {po_detail_id} 不存在'})

            # 验证数量不超过PO可发数量
            remaining = po_detail.remaining_to_dispatch
            if quantity > remaining:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': f'{po_detail.product_name} PO可发数量为 {remaining}，不能发 {quantity}'
                })

            # 验证数量不超过SO可发数量（如有关联）
            so_detail_id = item.get('sales_order_detail_id') or po_detail.sales_order_detail_id
            if so_detail_id and destination_type == 'sales_order':
                from app.models.sales_order import SalesOrderDetail as SOD
                so_detail = SOD.query.get(so_detail_id)
                if so_detail and quantity > so_detail.remaining_to_ship:
                    db.session.rollback()
                    return jsonify({
                        'success': False,
                        'message': f'{po_detail.product_name} 客户订单剩余可发 {so_detail.remaining_to_ship}，不能发 {quantity}'
                    })

            # 处理序列号
            serial_numbers = item.get('serial_numbers', [])
            serial_numbers_json = json_mod.dumps(serial_numbers) if serial_numbers else None

            # 创建发货明细
            shipment_detail = ShipmentDetail(
                shipment_id=shipment.id,
                purchase_order_detail_id=po_detail_id,
                sales_order_detail_id=item.get('sales_order_detail_id') if destination_type == 'sales_order' else None,
                product_id=item.get('product_id', po_detail.product_id),
                product_name=item.get('product_name', po_detail.product_name),
                product_model=item.get('product_model', po_detail.product_model),
                quantity=quantity,
                unit=item.get('unit', po_detail.unit),
                serial_numbers=serial_numbers_json,
                status='pending'
            )
            db.session.add(shipment_detail)

            # 更新采购明细的已发货数量
            po_detail.dispatched_quantity = (po_detail.dispatched_quantity or 0) + quantity

            # 如果是发给客户订单，同时更新客户订单明细的发货数量
            if destination_type == 'sales_order' and item.get('sales_order_detail_id'):
                so_detail = SalesOrderDetail.query.get(item['sales_order_detail_id'])
                if so_detail:
                    so_detail.shipped_quantity = (so_detail.shipped_quantity or 0) + quantity

            # 更新 ProductSerialNumber 记录（如果提供了SN）
            if serial_numbers:
                try:
                    from app.models.product_serial_number import ProductSerialNumber
                    for sn_str in serial_numbers:
                        sn_record = ProductSerialNumber.query.filter_by(serial_number=sn_str).first()
                        if sn_record:
                            sn_record.shipment_id = shipment.id
                            sn_record.status = 'shipped'
                            sn_record.ship_out_date = datetime.now()
                except Exception as sn_err:
                    logger.warning(f"更新序列号记录失败（非致命）: {sn_err}")

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'发货单 {shipment.shipment_number} 创建成功',
            'shipment_id': shipment.id,
            'shipment_number': shipment.shipment_number,
            'redirect_url': url_for('shipment.detail_view', shipment_id=shipment.id)
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"从采购订单创建发货单失败: {str(e)}")
        return jsonify({'success': False, 'message': f'创建失败: {str(e)}'})


@shipment_bp.route('/api/available-sales-orders', methods=['GET'])
@login_required
@permission_required('shipment', 'view')
def api_available_sales_orders():
    """获取可选的客户订单列表（状态为 confirmed 或 preparing）"""
    search = request.args.get('search', '').strip()

    query = SalesOrder.query.filter(
        SalesOrder.status.in_(['confirmed', 'preparing', 'shipped', 'delivered'])
    )

    if search:
        query = query.filter(
            db.or_(
                SalesOrder.order_number.ilike(f'%{search}%'),
            )
        )

    orders = query.order_by(SalesOrder.created_at.desc()).limit(50).all()

    return jsonify({
        'success': True,
        'orders': [{
            'id': o.id,
            'order_number': o.order_number,
            'customer_name': o.customer.company_name if o.customer else '',
            'status': o.status,
            'delivery_address': o.delivery_address,
            'delivery_contact': o.delivery_contact,
            'delivery_phone': o.delivery_phone,
            'total_quantity': o.total_quantity
        } for o in orders]
    })
