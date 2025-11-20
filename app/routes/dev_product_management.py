#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
研发产品管理路由

提供研发产品的列表、详情查看和入库审批功能
"""
from flask import Blueprint, request, render_template, flash, redirect, url_for, jsonify
from flask_babel import gettext as _
from flask_login import login_required, current_user
from app.decorators import permission_required, permission_required_with_approval_context
from app.models.dev_product import DevProduct, DevProductSpec
from app.models.product import Product
from app.models.product_code import ProductCategory, ProductSubcategory
from app.models.approval import ApprovalInstance, ApprovalProcessTemplate, ApprovalStatus
from app.services.product_warehousing_service import ProductWarehousingService
from app import db
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('dev_product', __name__, url_prefix='/dev-product')


@bp.route('/list', methods=['GET'])
@login_required
@permission_required('product', 'view')
def dev_product_list():
    """研发产品列表页面"""
    # 获取筛选参数
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '').strip()
    category_id = request.args.get('category_id', '').strip()

    # 使用标准权限过滤构建查询（支持四级权限：system/company/department/personal）
    from app.utils.access_control import get_viewable_data
    query = get_viewable_data(DevProduct, current_user)

    # 🔍 调试：记录查询结果数量
    total_before_filter = query.count()
    logger.info(f"🔍 [DEV_PRODUCT_LIST] 用户 {current_user.username} (ID:{current_user.id}, 角色:{current_user.role}) 权限过滤后数量: {total_before_filter}")

    # 搜索条件
    if search:
        query = query.filter(
            db.or_(
                DevProduct.model.ilike(f'%{search}%'),
                DevProduct.mn_code.ilike(f'%{search}%'),
                DevProduct.name.ilike(f'%{search}%')
            )
        )

    # 状态筛选
    if status_filter:
        query = query.filter(DevProduct.status == status_filter)

    # 分类筛选
    if category_id:
        query = query.filter(DevProduct.category_id == int(category_id))

    # 排序
    dev_products = query.order_by(DevProduct.updated_at.desc()).all()

    # 获取分类列表用于筛选
    categories = ProductCategory.query.order_by(ProductCategory.name).all()

    # 获取所有可能的状态（对应stage_configs.py中的STATUS_TO_STAGE_MAPPING）
    available_statuses = ['调研中', '立项中', '研发中', '申请入库', '已入库', '已取消', '暂停']

    # 构建筛选配置
    filter_config = {
        'action_url': url_for('dev_product.dev_product_list'),
        'form_id': 'devProductFilterForm',
        'search_field': {
            'name': 'search',
            'label': '搜索',
            'placeholder': '搜索型号、MN编号、名称',
            'value': search
        },
        'dropdown_filters': [
            {
                'name': 'status',
                'label': '状态',
                'options': [{'value': '', 'label': '全部状态'}] +
                          [{'value': s, 'label': s} for s in available_statuses],
                'selected': status_filter
            },
            {
                'name': 'category_id',
                'label': '产品分类',
                'options': [{'value': '', 'label': '全部分类'}] +
                          [{'value': str(c.id), 'label': c.name} for c in categories],
                'selected': category_id
            }
        ]
    }

    return render_template(
        'dev_product/list.html',
        dev_products=dev_products,
        filter_config=filter_config,
        search=search,
        status_filter=status_filter,
        category_id=category_id
    )


@bp.route('/detail/<int:dev_product_id>', methods=['GET'])
@login_required
@permission_required_with_approval_context('product', 'view')
def dev_product_detail(dev_product_id):
    """研发产品详情页面"""
    # 使用标准权限过滤获取研发产品（支持审批上下文）
    from app.utils.access_control import get_viewable_data
    viewable_dev_products = get_viewable_data(DevProduct, current_user)
    dev_product = viewable_dev_products.filter(DevProduct.id == dev_product_id).first_or_404()

    # 获取规格数据
    specs = DevProductSpec.query.filter_by(dev_product_id=dev_product_id).all()

    # 检查是否有正在进行的审批
    approval_instance = ApprovalInstance.query.filter_by(
        object_type='rd_product',
        object_id=dev_product_id,
        status=ApprovalStatus.PENDING
    ).first()

    # 检查是否已入库（查找对应的产品记录）
    warehoused_product = None
    if dev_product.status == '已入库':
        warehoused_product = Product.query.filter_by(
            source_dev_product_id=dev_product_id
        ).first()

    # 获取可用的入库审批流程模板
    available_templates = ApprovalProcessTemplate.query.filter_by(
        object_type='rd_product',
        is_active=True
    ).all()

    return render_template(
        'product_management/product_detail.html',
        dev_product=dev_product,
        specs=specs,
        approval_instance=approval_instance,
        warehoused_product=warehoused_product,
        available_templates=available_templates,
        is_owner=dev_product.owner_id == current_user.id
    )


@bp.route('/submit-approval/<int:dev_product_id>', methods=['POST'])
@login_required
@permission_required('product', 'edit')
def submit_warehousing_approval(dev_product_id):
    """提交入库审批"""
    try:
        dev_product = DevProduct.query.get_or_404(dev_product_id)

        # 权限检查：只有所有者和管理员可以提交审批
        if current_user.role not in ['admin', 'product_manager', 'rd_manager']:
            if dev_product.owner_id != current_user.id:
                return jsonify({
                    'success': False,
                    'message': '您没有权限提交此研发产品的审批'
                }), 403

        # 检查是否已有正在进行的审批
        existing_approval = ApprovalInstance.query.filter_by(
            object_type='rd_product',
            object_id=dev_product_id,
            status=ApprovalStatus.PENDING
        ).first()

        if existing_approval:
            return jsonify({
                'success': False,
                'message': '该研发产品已有正在进行的审批流程'
            }), 400

        # 检查是否已入库
        if dev_product.status == '已入库':
            return jsonify({
                'success': False,
                'message': '该研发产品已完成入库'
            }), 400

        # 获取审批流程模板
        template_id = request.json.get('template_id')
        if not template_id:
            return jsonify({
                'success': False,
                'message': '请选择审批流程模板'
            }), 400

        template = ApprovalProcessTemplate.query.get(template_id)
        if not template or not template.is_active:
            return jsonify({
                'success': False,
                'message': '审批流程模板不存在或已停用'
            }), 400

        # 创建审批实例
        from app.helpers.approval_helpers import start_approval_process

        approval_instance = start_approval_process(
            object_type='rd_product',
            object_id=dev_product_id,
            template_id=template.id,
            user_id=current_user.id
        )

        if not approval_instance:
            return jsonify({
                'success': False,
                'message': '启动审批流程失败'
            }), 500

        # 更新研发产品状态
        dev_product.status = '审批中'

        # 自动设置"申请入库"阶段的开始日期
        dev_product.update_stage(
            'apply_storage',
            user_id=current_user.id,
            description='提交入库审批，自动进入申请入库阶段'
        )

        db.session.commit()

        logger.info(f"研发产品入库审批提交成功: DevProduct#{dev_product_id}, ApprovalInstance#{approval_instance.id}")

        return jsonify({
            'success': True,
            'message': '入库审批已提交',
            'approval_id': approval_instance.id
        })

    except Exception as e:
        db.session.rollback()
        logger.error(f"提交入库审批失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'提交失败: {str(e)}'
        }), 500


@bp.route('/check-mn-duplicate', methods=['POST'])
@login_required
@permission_required('product', 'view')
def check_mn_duplicate():
    """检查MN编号是否重复（API接口）"""
    try:
        mn_code = request.json.get('mn_code')
        if not mn_code:
            return jsonify({
                'exists': False,
                'message': 'MN编号为空'
            })

        service = ProductWarehousingService()
        result = service.check_mn_duplicate(mn_code)

        if result['exists']:
            product = result['product']
            return jsonify({
                'exists': True,
                'message': f'MN编号已存在',
                'product_id': product.id,
                'product_model': product.model
            })
        else:
            return jsonify({
                'exists': False,
                'message': 'MN编号可用'
            })

    except Exception as e:
        logger.error(f"检查MN重复失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@bp.route('/api/approval/<int:object_id>/flow')
@login_required
@permission_required_with_approval_context('product', 'view')
def get_dev_product_approval_flow(object_id):
    """获取研发产品审批流程信息"""
    try:
        # 使用标准权限过滤获取研发产品（支持审批上下文）
        from app.utils.access_control import get_viewable_data
        viewable_dev_products = get_viewable_data(DevProduct, current_user)
        dev_product = viewable_dev_products.filter(DevProduct.id == object_id).first_or_404()

        # 导入审批相关函数
        from app.helpers.approval_helpers import get_object_approval_instance, can_recall_approval, can_resubmit_approval
        from app.models.approval import ApprovalRecord

        # 获取审批实例（包含被拒绝的实例）
        approval_instance = get_object_approval_instance('rd_product', object_id, include_rejected=True)

        if not approval_instance:
            # 没有审批实例
            control_info = {
                'status': dev_product.status,
                'is_creator': dev_product.created_by == current_user.id,
                'can_submit': dev_product.status == '申请入库' and dev_product.created_by == current_user.id,
                'can_recall': False,
                'can_resubmit': False
            }
            return jsonify({
                'success': False,
                'message': '未找到审批流程',
                'approval_flow': None,
                'control_info': control_info
            })

        # 获取审批步骤
        steps = approval_instance.get_steps()
        if not steps:
            return jsonify({'success': False, 'message': '审批流程配置错误'})

        # 获取审批记录
        records = ApprovalRecord.query.filter_by(
            instance_id=approval_instance.id
        ).order_by(ApprovalRecord.timestamp.asc()).all()

        # 获取当前步骤的step_order（current_step存储的是step_id）
        current_step_order = None
        if approval_instance.current_step:
            from app.models.approval import ApprovalStep
            current_step_obj = ApprovalStep.query.filter_by(id=approval_instance.current_step).first()
            current_step_order = current_step_obj.step_order if current_step_obj else None

        logger.info(f"Debug: 当前步骤ID: {approval_instance.current_step}, 当前步骤顺序: {current_step_order}")
        logger.info(f"Debug: 找到 {len(records)} 个审批记录")

        # 构建流程数据
        stages_data = []
        for i, step in enumerate(steps):
            # 获取步骤信息
            if isinstance(step, dict):
                step_name = step.get('step_name', f'步骤{i+1}')
                step_order = step.get('step_order', i+1)
                approver_user_id = step.get('approver_user_id')
            else:
                step_name = step.step_name
                step_order = step.step_order
                approver_user_id = step.approver_user_id

            # 查找审批记录
            step_record = None
            if hasattr(step, 'id') and isinstance(step.id, int):
                step_record = next((r for r in records if r.step_id == step.id), None)
            elif step_order <= len(records):
                step_record = records[step_order - 1]

            # 获取审批人信息
            approver_name = '未分配'
            if approver_user_id:
                from app.models.user import User
                approver = User.query.get(approver_user_id)
                approver_name = approver.real_name if approver and approver.real_name else (approver.username if approver else '未分配')

            # 确定状态和时间戳
            if step_record:
                # 有审批记录的步骤，根据实际审批结果设置状态
                status = 'approved' if step_record.action == 'approve' else 'rejected'
                processed_at = step_record.timestamp.isoformat() if step_record.timestamp else None
                comment = step_record.comment
                logger.info(f"Debug: 步骤 {step_order} 状态: {status} (有记录)")
            elif step_order == current_step_order:
                # 当前待审批步骤 - 使用 'current' 状态以匹配前端显示逻辑
                status = 'current'
                processed_at = None
                comment = None
                logger.info(f"Debug: 步骤 {step_order} 状态: current (当前步骤)")
            else:
                # 其他步骤都是等待状态（无论是之前的还是之后的）
                status = 'waiting'
                processed_at = None
                comment = None
                logger.info(f"Debug: 步骤 {step_order} 状态: waiting (其他步骤)")

            # 使用标准格式构建步骤数据
            stage_data = {
                'id': step.id if hasattr(step, 'id') else f'step_{i}',
                'stage_name': step_name,
                'stage_order': step_order,
                'status': status,
                'approver_name': approver_name,
                'arrived_at': approval_instance.started_at.isoformat() if step_order <= (current_step_order or 0) else None,
                'processed_at': processed_at,
                'comment': comment
            }
            stages_data.append(stage_data)

        # 检查当前用户是否可以审批（使用现有辅助函数）
        from app.helpers.approval_helpers import is_current_approver
        can_approve = is_current_approver('rd_product', object_id, current_user.id)

        # 统一返回格式（与订单API保持一致）
        return jsonify({
            'success': True,
            'approval_flow': {
                'stages': stages_data,
                'current_stage': current_step_order,  # 返回step_order而不是step_id，前端需要用order比较
                'can_approve': can_approve,
                'status': approval_instance.status.value,
                'can_recall': can_recall_approval('rd_product', object_id, current_user.id),
                'can_resubmit': can_resubmit_approval('rd_product', object_id, current_user.id),
                'is_creator': dev_product.created_by == current_user.id,
                'creator_id': dev_product.created_by,
                'instance_id': approval_instance.id,
                'created_at': approval_instance.started_at.strftime('%Y-%m-%d %H:%M:%S') if approval_instance.started_at else None
            }
        })

    except Exception as e:
        logger.error(f"获取审批流程失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'获取失败: {str(e)}'
        }), 500


@bp.route('/warehousing-status/<int:dev_product_id>', methods=['GET'])
@login_required
@permission_required('product', 'view')
def warehousing_status(dev_product_id):
    """获取入库状态（API接口）"""
    try:
        dev_product = DevProduct.query.get_or_404(dev_product_id)

        # 查找审批实例
        approval_instance = ApprovalInstance.query.filter_by(
            object_type='rd_product',
            object_id=dev_product_id
        ).order_by(ApprovalInstance.started_at.desc()).first()

        # 查找入库后的产品
        warehoused_product = None
        if dev_product.status == '已入库':
            warehoused_product = Product.query.filter_by(
                source_dev_product_id=dev_product_id
            ).first()

        return jsonify({
            'success': True,
            'status': dev_product.status,
            'has_approval': approval_instance is not None,
            'approval_status': approval_instance.status.value if approval_instance else None,
            'is_warehoused': dev_product.status == '已入库',
            'product_id': warehoused_product.id if warehoused_product else None
        })

    except Exception as e:
        logger.error(f"获取入库状态失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
