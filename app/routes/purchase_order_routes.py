# -*- coding: utf-8 -*-
"""
采购订单路由蓝图 - Tailwind风格页面
管理采购订单的列表、详情、创建、状态流转等
"""
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models.inventory import PurchaseOrder, PurchaseOrderDetail
from app.models.customer import Company
from app.models.product import Product
from app.models.user import User
from app.decorators import permission_required, permission_required_with_approval_context
from app.utils.access_control import get_viewable_data
from app.helpers.purchase_order_helpers import (
    process_order_details,
    upload_signature_image,
    upload_supplier_confirmation_file,
    generate_order_number,
    parse_date,
    get_order_statistics,
    is_supply_chain_user,
    get_condition_label
)
import logging

logger = logging.getLogger(__name__)

purchase_order_bp = Blueprint('purchase_order', __name__, url_prefix='/purchase-order')


# ============== 页面路由 ==============

@purchase_order_bp.route('/')
@login_required
@permission_required('order', 'view')
def list_view():
    """采购订单列表页 - Tailwind风格"""
    # 获取筛选参数
    status = request.args.get('status', '')
    supplier_id = request.args.get('supplier_id', '')
    test_status = request.args.get('test_status', '')
    overdue = request.args.get('overdue', '')  # 超期筛选
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # 基础查询（使用数据归属权限过滤）
    query = get_viewable_data(PurchaseOrder, current_user, [])

    # 状态筛选
    if status:
        query = query.filter(PurchaseOrder.status == status)

    # 供应商筛选
    if supplier_id:
        query = query.filter(PurchaseOrder.company_id == int(supplier_id))

    # 测试状态筛选
    if test_status:
        if test_status == 'factory_passed':
            query = query.filter(PurchaseOrder.factory_test_status == 'passed')
        elif test_status == 'factory_pending':
            query = query.filter(PurchaseOrder.factory_test_status == 'pending')
        elif test_status == 'verification_passed':
            query = query.filter(PurchaseOrder.verification_test_status == 'passed')
        elif test_status == 'verification_pending':
            query = query.filter(PurchaseOrder.verification_test_status == 'pending')

    # 超期筛选
    if overdue == '1':
        query = query.filter(PurchaseOrder.is_overdue == True)

    # 搜索
    if search:
        query = query.filter(
            db.or_(
                PurchaseOrder.order_number.ilike(f'%{search}%'),
                PurchaseOrder.description.ilike(f'%{search}%')
            )
        )

    # 排序和分页
    query = query.order_by(PurchaseOrder.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    orders = pagination.items

    # 获取统计数据
    stats = get_order_statistics()

    # 获取供应商列表（用于筛选）
    suppliers = Company.query.filter(
        Company.is_deleted == False,
        Company.company_type == 'supplier'
    ).order_by(Company.company_name).all()

    return render_template(
        'inventory/tw_purchase_order_list.html',
        orders=orders,
        pagination=pagination,
        stats=stats,
        suppliers=suppliers,
        current_status=status,
        current_supplier_id=supplier_id,
        current_test_status=test_status,
        current_overdue=(overdue == '1'),
        search=search
    )


@purchase_order_bp.route('/<int:order_id>')
@login_required
@permission_required_with_approval_context('order', 'view')
def detail_view(order_id):
    """采购订单详情页 - Tailwind风格"""
    from datetime import date
    order = PurchaseOrder.query.get_or_404(order_id)

    # 获取供应商列表（用于编辑模态框）
    suppliers = Company.query.filter(
        Company.is_deleted == False,
        Company.company_type == 'supplier'
    ).order_by(Company.company_name).all()

    # 判断是否为供应链用户（可以调整交期）
    is_supply_chain = is_supply_chain_user(current_user)

    return render_template(
        'inventory/tw_purchase_order_detail.html',
        order=order,
        suppliers=suppliers,
        is_supply_chain=is_supply_chain,
        today=date.today()
    )


# ============== API路由 ==============

@purchase_order_bp.route('/api/create', methods=['POST'])
@login_required
@permission_required('order', 'create')
def api_create():
    """创建采购订单"""
    try:
        data = request.get_json()

        # 验证必填字段
        supplier_id = data.get('supplier_id')
        if not supplier_id:
            return jsonify({'success': False, 'message': '请选择供应商'})

        # 生成订单号
        order_number = generate_order_number()

        # 创建订单
        order = PurchaseOrder(
            order_number=order_number,
            company_id=supplier_id,
            order_category=data.get('order_category', 'channel'),
            required_date=parse_date(data.get('required_date')),
            incoterms=data.get('incoterms'),
            shipping_method=data.get('shipping_method'),
            freight_terms=data.get('freight_terms'),
            verification_test_type=data.get('verification_test_type'),
            ship_to=data.get('ship_to'),
            payment_terms=data.get('payment_terms'),
            description=data.get('notes'),
            status='draft',
            created_by_id=current_user.id,
            # 交期计划字段
            confirmed_date=parse_date(data.get('confirmed_date')),
            milestone_test_complete_date=parse_date(data.get('milestone_test_complete_date')),
            milestone_ship_date=parse_date(data.get('milestone_ship_date'))
        )

        db.session.add(order)
        db.session.flush()  # 获取 order.id

        # 处理产品明细（使用辅助函数）
        details_data = data.get('details', [])
        process_order_details(order, details_data, is_update=False)
        order.currency = data.get('currency', 'CNY')

        db.session.commit()

        logger.info(f"创建采购订单 {order_number}，包含 {len(order.details)} 条明细")
        return jsonify({
            'success': True,
            'message': f'采购订单 {order_number} 创建成功',
            'order_id': order.id,
            'order_number': order_number,
            'redirect_url': url_for('purchase_order.detail_view', order_id=order.id)
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"创建采购订单失败: {str(e)}")
        return jsonify({'success': False, 'message': f'创建失败: {str(e)}'})


@purchase_order_bp.route('/api/<int:order_id>/update', methods=['PUT'])
@login_required
@permission_required('order', 'edit')
def api_update(order_id):
    """更新采购订单"""
    try:
        order = PurchaseOrder.query.get_or_404(order_id)
        data = request.get_json()

        # 更新可编辑字段（供应商不可修改）
        order.order_category = data.get('order_category', order.order_category)
        order.required_date = parse_date(data.get('required_date')) or order.required_date
        order.incoterms = data.get('incoterms', order.incoterms)
        order.shipping_method = data.get('shipping_method', order.shipping_method)
        order.freight_terms = data.get('freight_terms', order.freight_terms)
        order.verification_test_type = data.get('verification_test_type', order.verification_test_type)
        order.ship_to = data.get('ship_to', order.ship_to)
        order.payment_terms = data.get('payment_terms', order.payment_terms)
        order.description = data.get('notes', order.description)
        order.currency = data.get('currency', order.currency)
        order.updated_at = datetime.now()

        # 交期计划字段（仅在未锁定时可修改）
        if not order.delivery_schedule_locked:
            if 'confirmed_date' in data:
                order.confirmed_date = parse_date(data.get('confirmed_date'))
            if 'milestone_test_complete_date' in data:
                order.milestone_test_complete_date = parse_date(data.get('milestone_test_complete_date'))
            if 'milestone_ship_date' in data:
                order.milestone_ship_date = parse_date(data.get('milestone_ship_date'))

        # 处理产品明细（如果传入了 details）
        details_data = data.get('details')
        if details_data is not None:
            process_order_details(order, details_data, is_update=True)

        db.session.commit()

        logger.info(f"更新采购订单 {order.order_number}")
        return jsonify({
            'success': True,
            'message': f'采购订单 {order.order_number} 更新成功'
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"更新采购订单失败: {str(e)}")
        return jsonify({'success': False, 'message': f'更新失败: {str(e)}'})


@purchase_order_bp.route('/api/<int:order_id>/supplier-confirm', methods=['POST'])
@login_required
@permission_required('order', 'edit')
def api_supplier_confirm(order_id):
    """记录供应商确认（支持文件上传和签名）"""
    try:
        order = PurchaseOrder.query.get_or_404(order_id)

        # 前置状态验证（在文件上传之前检查，避免浪费资源）
        if order.status != 'approved':
            return jsonify({'success': False, 'message': '订单尚未内部审批通过，无法进行供应商确认'})

        # 检查是否有文件上传
        if 'confirmation_file' not in request.files:
            return jsonify({'success': False, 'message': '请上传供应商确认回执文件'})

        file = request.files['confirmation_file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '请选择文件'})

        # 验证文件类型
        allowed_extensions = {'pdf', 'jpg', 'jpeg', 'png'}
        file_ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if file_ext not in allowed_extensions:
            return jsonify({'success': False, 'message': '只支持 PDF、JPG、PNG 格式'})

        # 上传文件到云端存储
        file_url = upload_supplier_confirmation_file(order, file)
        if not file_url:
            return jsonify({'success': False, 'message': '文件上传失败，请重试'})

        # 获取表单数据（multipart/form-data）
        confirmed_by = request.form.get('confirmed_by', '')
        confirmed_date_str = request.form.get('confirmed_date', '')
        notes = request.form.get('notes', '')

        # 处理签名 base64 数据
        signature_data = request.form.get('signature', '')
        signature_url = None
        if signature_data and signature_data.startswith('data:image/'):
            signature_url = upload_signature_image(order, signature_data)
            if signature_url:
                logger.info(f"签名上传成功: {signature_url}")

        # 更新订单
        order.supplier_confirmed = True
        order.supplier_confirmed_date = datetime.now()
        order.supplier_confirmed_by = confirmed_by
        order.supplier_confirmation_file = file_url
        order.supplier_confirmation_notes = notes
        order.confirmed_date = parse_date(confirmed_date_str) if confirmed_date_str else datetime.now()

        # 保存签名URL
        if signature_url:
            order.supplier_signature_url = signature_url

        order.status = 'confirmed'

        # 锁定交期计划
        order.delivery_schedule_locked = True
        order.delivery_schedule_locked_at = datetime.now()

        # 锁定关联的序列号（标记为已确认）
        try:
            from app.models.product_serial_number import ProductSerialNumber
            serial_numbers = ProductSerialNumber.query.filter_by(
                purchase_order_id=order.id
            ).all()

            for sn in serial_numbers:
                # 记录确认时间（可用于追溯）
                confirm_note = f"供应商确认于 {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                if not sn.notes:
                    sn.notes = confirm_note
                else:
                    sn.notes += f"\n{confirm_note}"

            logger.info(f"订单 {order.order_number} 锁定 {len(serial_numbers)} 个序列号")
        except Exception as e:
            logger.error(f"锁定序列号失败: {str(e)}")

        db.session.commit()
        logger.info(f"采购订单 {order.order_number} 供应商确认完成，交期已锁定")
        return jsonify({'success': True, 'message': '供应商确认已记录，交期已锁定'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"记录供应商确认失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


@purchase_order_bp.route('/api/<int:order_id>/serial-numbers', methods=['GET'])
@login_required
@permission_required('order', 'view')
def api_get_serial_numbers(order_id):
    """获取采购订单的序列号列表"""
    try:
        from app.models.product_serial_number import ProductSerialNumber
        from sqlalchemy.orm import joinedload

        order = PurchaseOrder.query.get_or_404(order_id)
        # 使用 joinedload 预加载 product 关系，避免 N+1 查询
        serial_numbers = ProductSerialNumber.query.filter_by(
            purchase_order_id=order_id
        ).options(joinedload(ProductSerialNumber.product)).order_by(ProductSerialNumber.serial_number).all()

        data = [{
            'id': sn.id,
            'serial_number': sn.serial_number,
            'product_name': sn.product.name if sn.product else '',
            'product_model': sn.product.model if sn.product else '',
            'batch_number': sn.batch_number,
            'status': sn.status,
            'status_label': sn.status_label,
            'warehouse_location': sn.warehouse_location
        } for sn in serial_numbers]

        return jsonify({
            'success': True,
            'serial_numbers': data,
            'total': len(data)
        })

    except Exception as e:
        logger.error(f"获取序列号列表失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


@purchase_order_bp.route('/api/<int:order_id>/submit-approval', methods=['POST'])
@login_required
@permission_required('order', 'edit')
def api_submit_approval(order_id):
    """提交审批 - 使用标准审批流程"""
    try:
        from app.helpers.approval_helpers import start_approval_process
        from app.models.approval import ApprovalProcessTemplate

        order = PurchaseOrder.query.get_or_404(order_id)

        # 只有草稿或被驳回的订单可以提交审批
        if order.status not in ['draft', 'rejected']:
            return jsonify({'success': False, 'message': '只有草稿或被驳回的订单可以提交审批'})

        # 获取请求数据
        data = request.get_json() or {}
        template_id = data.get('template_id')

        # 如果未指定模板，使用默认模板
        if not template_id:
            default_template = ApprovalProcessTemplate.query.filter_by(
                object_type='purchase_order',
                is_active=True
            ).first()

            if not default_template:
                return jsonify({
                    'success': False,
                    'message': '未找到可用的采购订单审批模板，请先在审批配置中创建模板'
                }), 400

            template_id = default_template.id

        # 启动审批流程
        approval_instance = start_approval_process(
            object_type='purchase_order',
            object_id=order_id,
            template_id=template_id,
            user_id=current_user.id,
            auto_commit=False
        )

        if not approval_instance:
            db.session.rollback()
            return jsonify({
                'success': False,
                'message': '启动审批流程失败'
            }), 500

        # 更新订单状态
        order.status = 'pending'
        db.session.commit()

        logger.info(f"采购订单 {order.order_number} 审批流程已启动，实例ID: {approval_instance.id}")
        return jsonify({
            'success': True,
            'message': '审批流程已启动',
            'instance_id': approval_instance.id
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"提交审批失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


@purchase_order_bp.route('/api/<int:order_id>/recall', methods=['POST'])
@login_required
@permission_required('order', 'edit')
def api_recall(order_id):
    """召回审批"""
    try:
        from app.helpers.approval_helpers import recall_approval_process

        order = PurchaseOrder.query.get_or_404(order_id)

        # 只有创建人可以召回
        if order.created_by_id != current_user.id:
            return jsonify({'success': False, 'message': '只有订单创建人可以召回审批'})

        # 只有pending状态可以召回
        if order.status != 'pending':
            return jsonify({'success': False, 'message': '只有待审批状态的订单可以召回'})

        # 召回审批流程
        success, message = recall_approval_process(
            object_type='purchase_order',
            object_id=order_id,
            user_id=current_user.id
        )

        if not success:
            return jsonify({'success': False, 'message': message}), 500

        # 更新订单状态
        order.status = 'draft'
        db.session.commit()

        logger.info(f"采购订单 {order.order_number} 审批已召回")
        return jsonify({'success': True, 'message': '审批已召回'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"召回审批失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


def _get_approval_flow_impl(order_id):
    """获取审批流程状态 - 内部实现（无装饰器）"""
    try:
        from app.helpers.approval_helpers import (
            get_object_approval_instance,
            can_recall_approval,
            can_user_approve
        )
        from app.models.approval import ApprovalRecord, ApprovalProcessTemplate

        order = PurchaseOrder.query.get_or_404(order_id)

        # 获取审批实例
        approval_instance = get_object_approval_instance('purchase_order', order_id)

        # 获取可用的审批模板
        templates = ApprovalProcessTemplate.query.filter_by(
            object_type='purchase_order',
            is_active=True
        ).all()

        if not approval_instance:
            return jsonify({
                'success': True,
                'approval_flow': None,
                'control_info': {
                    'status': order.status,
                    'can_submit': order.status in ['draft', 'rejected'] and order.created_by_id == current_user.id,
                    'can_recall': False,
                    'can_approve': False,
                    'is_creator': order.created_by_id == current_user.id
                },
                'templates': [{'id': t.id, 'name': t.name} for t in templates]
            })

        # 获取审批步骤
        steps = approval_instance.get_steps()
        if not steps:
            return jsonify({'success': False, 'message': '审批流程配置错误'})

        # 获取审批记录
        records = ApprovalRecord.query.filter_by(
            instance_id=approval_instance.id
        ).order_by(ApprovalRecord.timestamp.asc()).all()

        # 🔥 修复：current_step 可能是 step_order 或 step_id，需要智能匹配
        current_step_value = approval_instance.current_step
        matched_step_order = None

        # 先尝试用 step_order 匹配
        for step in steps:
            step_order_val = step.get('step_order') if isinstance(step, dict) else step.step_order
            if step_order_val == current_step_value:
                matched_step_order = current_step_value
                break

        # 如果 step_order 匹配不到，尝试用 step_id 匹配
        if matched_step_order is None:
            for step in steps:
                step_id_val = step.get('step_id') or step.get('id') if isinstance(step, dict) else step.id
                if step_id_val == current_step_value:
                    matched_step_order = step.get('step_order') if isinstance(step, dict) else step.step_order
                    logger.info(f"[审批流程] current_step={current_step_value} 通过 step_id 匹配到 step_order={matched_step_order}")
                    break

        current_step_order = matched_step_order

        # 构建步骤数据
        stages_data = []
        for step in steps:
            # 兼容字典（template_snapshot）和ORM对象两种格式
            if isinstance(step, dict):
                step_id = step.get('step_id') or step.get('id')
                step_order = step.get('step_order')
                step_name = step.get('step_name')
                approver_user_id = step.get('approver_user_id')
                approver_real_name = step.get('approver_real_name')
            else:
                step_id = step.id
                step_order = step.step_order
                step_name = step.step_name
                approver_user_id = step.approver_user_id
                approver_real_name = None

            step_records = [r for r in records if r.step_id == step_id]

            # 兜底：模板快照模式（动态生成的step_id写入记录时为NULL）
            if not step_records and records:
                approve_records = [r for r in records if r.action in ('approve', 'reject')]
                if approve_records and all(r.step_id is None for r in approve_records):
                    if step_order <= len(approve_records):
                        step_records = [approve_records[step_order - 1]]

            # 获取审批人名称：优先使用快照中的名称，否则查询数据库
            if approver_real_name:
                approver_name = approver_real_name
            elif approver_user_id:
                approver = User.query.get(approver_user_id)
                approver_name = approver.real_name if approver else '待分配'
            else:
                approver_name = '待分配'

            stage_info = {
                'step_id': step_id,
                'step_order': step_order,
                'stage_name': step_name,  # 前端组件期望 stage_name 而非 step_name
                'approver_name': approver_name,
                'approver_id': approver_user_id,
                'status': 'pending',
                'can_approve': False,
                'records': []
            }

            # 确定步骤状态
            if step_records:
                last_record = step_records[-1]
                if last_record.action == 'skipped':
                    # 跳过的步骤
                    stage_info['status'] = 'skipped'
                    stage_info['comment'] = last_record.comment or '条件不满足，自动跳过'
                    stage_info['completed_time'] = last_record.timestamp.strftime('%Y-%m-%d %H:%M') if last_record.timestamp else None
                else:
                    stage_info['status'] = 'approved' if last_record.action == 'approve' else 'rejected'
                    # 添加完成时间（供前端时间线显示）
                    stage_info['completed_time'] = last_record.timestamp.strftime('%Y-%m-%d %H:%M') if last_record.timestamp else None
                    # 添加审批意见
                    stage_info['comment'] = last_record.comment
                    stage_info['records'] = [{
                        'action': r.action,
                        'comment': r.comment,
                        'timestamp': r.timestamp.strftime('%Y-%m-%d %H:%M') if r.timestamp else '',
                        'approver_name': User.query.get(r.approver_id).real_name if r.approver_id else ''
                    } for r in step_records]
            elif current_step_order == step_order:
                # 🔥 修复：使用已计算的 current_step_order（已兼容 step_id 和 step_order）
                stage_info['status'] = 'current'
                # 检查当前用户是否可以审批此步骤
                stage_info['can_approve'] = can_user_approve(approval_instance.id, current_user.id)

            stages_data.append(stage_info)

        return jsonify({
            'success': True,
            'approval_flow': {
                'instance_id': approval_instance.id,
                'status': approval_instance.status.value if hasattr(approval_instance.status, 'value') else str(approval_instance.status),
                'current_step': approval_instance.current_step,
                'started_at': approval_instance.started_at.strftime('%Y-%m-%d %H:%M') if approval_instance.started_at else None,
                'stages': stages_data
            },
            'control_info': {
                'status': order.status,
                'can_submit': False,
                'can_recall': can_recall_approval('purchase_order', order_id, current_user.id),
                'can_approve': any(s.get('can_approve', False) for s in stages_data),
                'is_creator': order.created_by_id == current_user.id
            },
            'templates': [{'id': t.id, 'name': t.name} for t in templates]
        })

    except Exception as e:
        logger.error(f"获取审批流程失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': f'获取审批流程失败: {str(e)}'}), 500


@purchase_order_bp.route('/api/<int:order_id>/approval-flow', methods=['GET'])
@login_required
@permission_required_with_approval_context('order', 'view')
def api_get_approval_flow(order_id):
    """获取审批流程状态"""
    return _get_approval_flow_impl(order_id)


# ============== 审批组件兼容路由 ==============
# 以下路由是为了兼容标准审批流程组件 tw_approval_flow.html 的API调用格式

@purchase_order_bp.route('/api/approval/<int:order_id>/flow', methods=['GET'])
@login_required
@permission_required_with_approval_context('order', 'view')
def api_approval_flow(order_id):
    """审批流程查询（组件兼容路由）"""
    return _get_approval_flow_impl(order_id)


@purchase_order_bp.route('/api/approval/<int:order_id>/submit', methods=['POST'])
@login_required
@permission_required('order', 'edit')
def api_approval_submit(order_id):
    """提交审批（组件兼容路由）"""
    return api_submit_approval(order_id)


@purchase_order_bp.route('/api/approval/<int:order_id>/recall', methods=['POST'])
@login_required
@permission_required('order', 'edit')
def api_approval_recall(order_id):
    """召回审批（组件兼容路由）"""
    return api_recall(order_id)


@purchase_order_bp.route('/api/approval/<int:order_id>/resubmit', methods=['POST'])
@login_required
@permission_required('order', 'edit')
def api_approval_resubmit(order_id):
    """重新提交审批（组件兼容路由）"""
    return api_submit_approval(order_id)


@purchase_order_bp.route('/api/<int:order_id>/production-progress', methods=['POST'])
@login_required
@permission_required('order', 'edit')
def api_update_production_progress(order_id):
    """更新生产进度"""
    try:
        order = PurchaseOrder.query.get_or_404(order_id)
        data = request.get_json()

        order.production_status = data.get('production_status', order.production_status)
        order.production_progress = data.get('production_progress', order.production_progress)
        order.production_notes = data.get('production_notes', order.production_notes)
        order.estimated_completion_date = parse_date(data.get('estimated_completion_date'))

        # 如果状态是draft或confirmed，更新为producing
        if order.status in ['draft', 'confirmed'] and order.production_status != 'not_started':
            order.status = 'producing'

        db.session.commit()
        return jsonify({'success': True, 'message': '生产进度已更新'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"更新生产进度失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


@purchase_order_bp.route('/api/<int:order_id>/test-report', methods=['POST'])
@login_required
@permission_required('order', 'edit')
def api_upload_test_report(order_id):
    """上传测试报告"""
    try:
        order = PurchaseOrder.query.get_or_404(order_id)
        data = request.get_json()

        test_type = data.get('test_type')  # factory / site_fat / incoming
        test_result = data.get('test_result')  # passed / failed / conditional

        if test_type == 'factory':
            order.factory_test_status = test_result
        elif test_type in ['site_fat', 'incoming']:
            order.verification_test_status = test_result

        # 如果两个测试都通过，更新状态为tested
        if order.factory_test_status == 'passed' and order.verification_test_status in ['passed', 'not_required']:
            order.status = 'tested'

        db.session.commit()
        return jsonify({'success': True, 'message': '测试报告已上传'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"上传测试报告失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


@purchase_order_bp.route('/api/<int:order_id>/ship', methods=['POST'])
@login_required
@permission_required('order', 'edit')
def api_confirm_shipment(order_id):
    """确认发货"""
    try:
        order = PurchaseOrder.query.get_or_404(order_id)
        data = request.get_json()

        order.carrier = data.get('carrier')
        order.tracking_number = data.get('tracking_number')
        order.ship_date = datetime.now()
        order.arrival_date = parse_date(data.get('arrival_date'))
        order.status = 'shipped'

        db.session.commit()
        return jsonify({'success': True, 'message': '发货信息已记录'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"确认发货失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


@purchase_order_bp.route('/api/<int:order_id>/accept', methods=['POST'])
@login_required
@permission_required('order', 'edit')
def api_accept_delivery(order_id):
    """验收入库"""
    try:
        order = PurchaseOrder.query.get_or_404(order_id)
        data = request.get_json()

        order.acceptance_status = data.get('acceptance_status', 'passed')
        order.acceptance_date = datetime.now()
        order.acceptance_by_id = current_user.id
        order.acceptance_notes = data.get('acceptance_notes')
        order.actual_arrival_date = datetime.now()
        order.status = 'stored'

        db.session.commit()
        return jsonify({'success': True, 'message': '验收入库完成'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"验收入库失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


@purchase_order_bp.route('/api/<int:order_id>/add-detail', methods=['POST'])
@login_required
@permission_required('order', 'edit')
def api_add_detail(order_id):
    """添加订单明细"""
    try:
        order = PurchaseOrder.query.get_or_404(order_id)
        data = request.get_json()

        product_id = data.get('product_id')
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'success': False, 'message': '产品不存在'})

        quantity = int(data.get('quantity', 1))
        unit_price = float(data.get('unit_price', 0))
        discount = float(data.get('discount', 1))

        detail = PurchaseOrderDetail(
            order_id=order.id,
            product_id=product_id,
            product_name=product.name,
            product_model=product.model,
            product_desc=data.get('product_desc', ''),
            brand=product.brand,
            quantity=quantity,
            unit=data.get('unit', '台'),
            unit_price=unit_price,
            discount=discount,
            total_price=quantity * unit_price * discount,
            notes=data.get('notes')
        )

        db.session.add(detail)

        # 更新订单汇总
        order.total_quantity = sum(d.quantity for d in order.details) + quantity
        order.total_amount = sum(float(d.total_price or 0) for d in order.details) + detail.total_price

        db.session.commit()
        return jsonify({'success': True, 'message': '明细添加成功'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"添加订单明细失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


@purchase_order_bp.route('/api/<int:order_id>/update-detail/<int:detail_id>', methods=['PUT'])
@login_required
@permission_required('order', 'edit')
def api_update_detail(order_id, detail_id):
    """更新订单明细"""
    try:
        order = PurchaseOrder.query.get_or_404(order_id)
        detail = PurchaseOrderDetail.query.filter_by(id=detail_id, order_id=order_id).first_or_404()
        data = request.get_json()

        # 更新字段
        if 'quantity' in data:
            detail.quantity = int(data['quantity'])
        if 'unit_price' in data:
            detail.unit_price = float(data['unit_price'])
        if 'discount' in data:
            detail.discount = float(data['discount'])
        if 'notes' in data:
            detail.notes = data['notes']

        # 重新计算小计
        detail.total_price = float(detail.unit_price or 0) * (detail.quantity or 0) * float(detail.discount or 1)

        # 更新订单汇总
        order.total_quantity = sum(d.quantity for d in order.details)
        order.total_amount = sum(float(d.total_price or 0) for d in order.details)

        db.session.commit()
        return jsonify({
            'success': True,
            'message': '明细更新成功',
            'detail': {
                'id': detail.id,
                'total_price': float(detail.total_price)
            }
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"更新订单明细失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


@purchase_order_bp.route('/api/<int:order_id>/delete-detail/<int:detail_id>', methods=['DELETE'])
@login_required
@permission_required('order', 'edit')
def api_delete_detail(order_id, detail_id):
    """删除订单明细"""
    try:
        order = PurchaseOrder.query.get_or_404(order_id)
        detail = PurchaseOrderDetail.query.filter_by(id=detail_id, order_id=order_id).first_or_404()

        db.session.delete(detail)

        # 更新订单汇总
        remaining_details = [d for d in order.details if d.id != detail_id]
        order.total_quantity = sum(d.quantity for d in remaining_details)
        order.total_amount = sum(float(d.total_price or 0) for d in remaining_details)

        db.session.commit()
        return jsonify({'success': True, 'message': '明细删除成功'})

    except Exception as e:
        db.session.rollback()
        logger.error(f"删除订单明细失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


@purchase_order_bp.route('/api/<int:order_id>/save-details', methods=['POST'])
@login_required
@permission_required('order', 'edit')
def api_save_details(order_id):
    """批量保存订单明细（支持新增、更新、删除）"""
    try:
        order = PurchaseOrder.query.get_or_404(order_id)
        data = request.get_json()
        details_data = data.get('details', [])

        # 使用辅助函数处理明细
        process_order_details(order, details_data, is_update=True)

        db.session.commit()
        logger.info(f"采购订单 {order.order_number} 明细批量保存成功")
        return jsonify({
            'success': True,
            'message': '明细保存成功',
            'total_quantity': order.total_quantity,
            'total_amount': float(order.total_amount or 0)
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"批量保存订单明细失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


@purchase_order_bp.route('/api/<int:order_id>/details', methods=['GET'])
@login_required
@permission_required('order', 'view')
def api_get_details(order_id):
    """获取订单明细列表"""
    try:
        order = PurchaseOrder.query.get_or_404(order_id)
        details = []
        for d in order.details:
            details.append({
                'id': d.id,
                'item_id': d.id,
                'product_id': d.product_id,
                'product_name': d.product_name,
                'product_model': d.product_model,
                'product_desc': d.product_desc,
                'brand': d.brand,
                'quantity': d.quantity,
                'unit': d.unit,
                'unit_price': float(d.unit_price or 0),
                'discount': float(d.discount or 1),
                'total_price': float(d.total_price or 0),
                'notes': d.notes
            })
        return jsonify({
            'success': True,
            'details': details,
            'total_quantity': order.total_quantity,
            'total_amount': float(order.total_amount or 0)
        })

    except Exception as e:
        logger.error(f"获取订单明细失败: {str(e)}")
        return jsonify({'success': False, 'message': f'操作失败: {str(e)}'})


@purchase_order_bp.route('/api/stats', methods=['GET'])
@login_required
@permission_required('order', 'view')
def api_stats():
    """获取订单统计数据"""
    stats = get_order_statistics()
    return jsonify({'success': True, 'stats': stats})


# ============== 进度管理 API ==============

@purchase_order_bp.route('/api/<int:order_id>/delivery-schedule', methods=['PUT'])
@login_required
@permission_required('order', 'edit')
def api_update_delivery_schedule(order_id):
    """
    更新交期计划（仅供应链人员可用）

    供应链人员可以调整：总交期、测试完成日期、发货日期
    工厂/供应商不能调用此API
    """
    from app.services.po_progress_service import PurchaseOrderProgressService

    # 权限检查：只有供应链和管理员可以修改交期
    if not is_supply_chain_user(current_user):
        return jsonify({'success': False, 'message': '只有供应链人员可以修改交期'}), 403

    order = PurchaseOrder.query.get_or_404(order_id)
    data = request.get_json()

    updates = {}
    if 'confirmed_date' in data:
        updates['confirmed_date'] = parse_date(data['confirmed_date'])
    if 'milestone_test_complete_date' in data:
        updates['milestone_test_complete_date'] = parse_date(data['milestone_test_complete_date'])
    if 'milestone_ship_date' in data:
        updates['milestone_ship_date'] = parse_date(data['milestone_ship_date'])

    if not updates:
        return jsonify({'success': False, 'message': '没有需要更新的字段'})

    success, message = PurchaseOrderProgressService.update_delivery_schedule(
        order_id=order_id,
        user_id=current_user.id,
        updates=updates,
        change_reason=data.get('change_reason', '')
    )

    return jsonify({'success': success, 'message': message})


@purchase_order_bp.route('/api/<int:order_id>/advance-stage', methods=['POST'])
@login_required
@permission_required('order', 'edit')
def api_advance_stage(order_id):
    """
    推进生产阶段（工厂/供应商专用）

    工厂可以推进阶段，但不能修改交期
    测试阶段需要满足条件才能推进
    """
    from app.services.po_progress_service import PurchaseOrderProgressService

    order = PurchaseOrder.query.get_or_404(order_id)
    data = request.get_json()

    new_stage = data.get('new_stage')
    if not new_stage:
        return jsonify({'success': False, 'message': '请指定目标阶段'})

    # 管理员可以强制推进
    force = data.get('force', False) and current_user.role == 'admin'

    success, message = PurchaseOrderProgressService.advance_stage(
        order_id=order_id,
        new_stage=new_stage,
        operator_info={
            'user_id': current_user.id,
            'reason': data.get('reason', ''),
            'notes': data.get('notes', '')
        },
        force=force
    )

    if success:
        # 返回更新后的状态
        return jsonify({
            'success': True,
            'message': message,
            'current_stage': order.production_status,
            'current_progress': order.production_progress,
            'is_overdue': order.is_overdue
        })
    else:
        return jsonify({'success': False, 'message': message})


@purchase_order_bp.route('/api/<int:order_id>/check-stage-conditions', methods=['GET'])
@login_required
@permission_required('order', 'view')
def api_check_stage_conditions(order_id):
    """检查当前阶段的推进条件"""
    from app.services.po_progress_service import PurchaseOrderProgressService, PRODUCTION_STAGES

    order = PurchaseOrder.query.get_or_404(order_id)
    current_config = PRODUCTION_STAGES.get(order.production_status, {})

    conditions = current_config.get('conditions', [])
    if not conditions:
        return jsonify({
            'success': True,
            'can_advance': True,
            'conditions': [],
            'failed_conditions': []
        })

    can_advance, failed = PurchaseOrderProgressService.check_stage_conditions(order, conditions)

    condition_status = []
    for cond in conditions:
        condition_status.append({
            'condition': cond,
            'met': cond not in [f.split(':')[0] for f in failed] if failed else True,
            'label': get_condition_label(cond)
        })

    return jsonify({
        'success': True,
        'can_advance': can_advance,
        'conditions': condition_status,
        'failed_conditions': failed
    })


@purchase_order_bp.route('/api/<int:order_id>/sign-test-report', methods=['POST'])
@login_required
@permission_required('order', 'edit')
def api_sign_test_report(order_id):
    """签证测试报告"""
    from app.services.po_progress_service import PurchaseOrderProgressService

    success, message = PurchaseOrderProgressService.mark_test_signed(
        order_id=order_id,
        user_id=current_user.id
    )

    return jsonify({'success': success, 'message': message})


@purchase_order_bp.route('/api/<int:order_id>/complete-fat', methods=['POST'])
@login_required
@permission_required('order', 'edit')
def api_complete_fat(order_id):
    """标记FAT完成"""
    from app.services.po_progress_service import PurchaseOrderProgressService

    data = request.get_json()
    completed_by = data.get('completed_by', current_user.real_name or current_user.username)

    success, message = PurchaseOrderProgressService.mark_fat_completed(
        order_id=order_id,
        completed_by=completed_by
    )

    return jsonify({'success': success, 'message': message})


@purchase_order_bp.route('/api/<int:order_id>/stage-history', methods=['GET'])
@login_required
@permission_required('order', 'view')
def api_get_stage_history(order_id):
    """获取阶段推进历史"""
    from app.services.po_progress_service import PurchaseOrderProgressService

    history = PurchaseOrderProgressService.get_stage_history(order_id)

    return jsonify({
        'success': True,
        'history': [{
            'id': h.id,
            'from_stage': h.from_stage,
            'to_stage': h.to_stage,
            'from_progress': h.from_progress,
            'to_progress': h.to_progress,
            'changed_by': h.changed_by_user.real_name if h.changed_by_user else h.changed_by_external_name,
            'change_type': h.change_type,
            'change_reason': h.change_reason,
            'created_at': h.created_at.strftime('%Y-%m-%d %H:%M') if h.created_at else None
        } for h in history]
    })


@purchase_order_bp.route('/api/<int:order_id>/delivery-changes', methods=['GET'])
@login_required
@permission_required('order', 'view')
def api_get_delivery_changes(order_id):
    """获取交期变更历史"""
    from app.services.po_progress_service import PurchaseOrderProgressService

    changes = PurchaseOrderProgressService.get_delivery_changes(order_id)

    field_labels = {
        'confirmed_date': '总交期',
        'milestone_test_complete_date': '测试完成日期',
        'milestone_ship_date': '发货日期'
    }

    return jsonify({
        'success': True,
        'changes': [{
            'id': c.id,
            'field_name': c.field_name,
            'field_label': field_labels.get(c.field_name, c.field_name),
            'old_value': c.old_value,
            'new_value': c.new_value,
            'change_reason': c.change_reason,
            'changed_by': c.changed_by.real_name if c.changed_by else None,
            'created_at': c.created_at.strftime('%Y-%m-%d %H:%M') if c.created_at else None
        } for c in changes]
    })


# 辅助函数已移至 app/helpers/purchase_order_helpers.py
