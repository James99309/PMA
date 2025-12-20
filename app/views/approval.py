from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from flask_babel import gettext as _
from app.permissions import admin_required, has_permission
from app.helpers.approval_helpers import (
    get_user_created_approvals,
    get_user_pending_approvals,
    get_all_approvals,
    get_approval_details,
    get_approval_object_url,
    start_approval_process,
    process_approval,
    process_approval_with_project_type,
    get_template_steps,
    get_approval_records_by_instance,
    get_current_step_info,
    get_last_approver,
    delete_approval_instance,
    can_user_approve,
    get_template_details,
    get_object_type_display,
    _get_field_display_name,
    rollback_order_approval,
    can_rollback_order_approval
)
from app.models.approval import (
    ApprovalStatus, 
    ApprovalAction,
    ApprovalProcessTemplate,
    ApprovalStep,
    ApprovalInstance
)
from app.helpers.project_helpers import lock_project, unlock_project, is_project_editable
from flask import session
import json
from app.utils.access_control import can_start_approval
from app import db
from datetime import datetime

# 创建Blueprint
approval_bp = Blueprint('approval', __name__, url_prefix='/approval')


@approval_bp.route('/center')
@login_required
def center():
    """审批中心视图"""
    try:
        # 获取统计数据（先于tab参数处理，用于智能页签选择）
        from app.helpers.approval_helpers import (
            get_pending_approval_count,
            get_pending_created_count, 
            get_pricing_order_pending_count,
            get_order_pending_count,
            get_expense_pending_count
        )

        # 🔥 进入审批中心时强制刷新待审批数量缓存
        pending_count = get_pending_approval_count(current_user.id, force_refresh=True)
        created_pending_count = get_pending_created_count(current_user.id)
        pricing_order_pending_count = get_pricing_order_pending_count(current_user.id)
        order_pending_count = get_order_pending_count(current_user.id)
        expense_pending_count = get_expense_pending_count(current_user.id)
        
        # 计算总的待审批数量
        total_pending_count = pending_count + pricing_order_pending_count + order_pending_count + expense_pending_count
        
        # 🔥 智能页签选择：优先根据待审批数量选择，兼顾用户指定的tab参数
        tab_param = request.args.get('tab')
        
        if tab_param and tab_param == 'pending' and total_pending_count == 0:
            # 特殊情况：用户指定了pending页签但没有待审批项目，智能切换到created页签
            tab = 'created'
            current_app.logger.info(f'智能页签选择：用户指定pending页签但无待审批项目，自动切换到我发起的页签')
        elif tab_param:
            # 用户明确指定了页签且是有效的
            tab = tab_param
            current_app.logger.info(f'使用用户指定的页签：{tab_param}')
        else:
            # 智能选择：有待审批显示"待审批"页签，无则显示"我发起的"页签
            if total_pending_count > 0:
                tab = 'pending'
                current_app.logger.info(f'智能页签选择：用户有{total_pending_count}个待审批项目，自动切换到待审批页签')
            else:
                tab = 'created'
                current_app.logger.info('智能页签选择：用户无待审批项目，显示我发起的页签')
        
        # 其他基础参数
        object_type = request.args.get('object_type')
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        # 构建通用列表配置
        list_config = build_approval_list_config(
            tab=tab,
            object_type=object_type,
            status=status,
            pending_count=pending_count,
            created_pending_count=created_pending_count,
            pricing_order_pending_count=pricing_order_pending_count,
            order_pending_count=order_pending_count,
            expense_pending_count=expense_pending_count
        )
        
        # 渲染模板
        return render_template(
            'approval/center.html',
            current_tab=tab,
            object_type=object_type,
            status=status,
            pending_count=pending_count,
            created_pending_count=created_pending_count,
            pricing_order_pending_count=pricing_order_pending_count,
            order_pending_count=order_pending_count,
            list_config=list_config
        )
    except Exception as e:
        # 捕获任何错误并显示
        import traceback
        error_detail = traceback.format_exc()
        return f"<h1>Error in approval center:</h1><pre>{error_detail}</pre>", 500


@approval_bp.route('/tw_center')
@login_required
def tw_center():
    """审批中心视图 - Tailwind CSS 版本"""
    try:
        # 获取统计数据
        from app.helpers.approval_helpers import (
            get_pending_approval_count,
            get_pending_created_count,
            get_pricing_order_pending_count,
            get_order_pending_count,
            get_expense_pending_count
        )

        pending_count = get_pending_approval_count(current_user.id, force_refresh=True)
        created_pending_count = get_pending_created_count(current_user.id)
        pricing_order_pending_count = get_pricing_order_pending_count(current_user.id)
        order_pending_count = get_order_pending_count(current_user.id)
        expense_pending_count = get_expense_pending_count(current_user.id)

        total_pending_count = pending_count + pricing_order_pending_count + order_pending_count + expense_pending_count

        # 智能页签选择
        tab_param = request.args.get('tab')
        if tab_param and tab_param == 'pending' and total_pending_count == 0:
            tab = 'created'
        elif tab_param:
            tab = tab_param
        else:
            tab = 'pending' if total_pending_count > 0 else 'created'

        # 其他参数
        object_type = request.args.get('object_type', '')
        status = request.args.get('status', '')
        search_value = request.args.get('search', '')
        sort_field = request.args.get('sort', 'started_at')
        sort_order = request.args.get('order', 'desc')
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 20, type=int)

        # 获取初始数据
        items, total_count, has_more = get_tw_approval_items(
            tab=tab,
            object_type=object_type,
            status=status,
            offset=offset,
            limit=limit
        )

        # 统计数据
        stats = {
            'total': pending_count + created_pending_count + pricing_order_pending_count + order_pending_count + expense_pending_count,
            'pending': pending_count,
            'created': created_pending_count,
            'pricing_order': pricing_order_pending_count,
            'order': order_pending_count,
            'expense': expense_pending_count
        }

        # 标签页配置
        tab_config = [
            {'key': 'pending', 'label': _('待我审批'), 'icon': 'hourglass_top', 'icon_class': 'text-amber-500', 'count': pending_count},
            {'key': 'created', 'label': _('我发起的'), 'icon': 'upload_file', 'count': created_pending_count},
            {'key': 'pricing_order', 'label': _('批价单'), 'icon': 'receipt_long', 'count': pricing_order_pending_count},
            {'key': 'order', 'label': _('订单'), 'icon': 'shopping_cart', 'count': order_pending_count},
            {'key': 'expense', 'label': _('报销单'), 'icon': 'payments', 'count': expense_pending_count}
        ]

        # 如果有全部审批权限，添加全部审批标签页
        if has_permission('approval_management', 'all'):
            tab_config.append({'key': 'all', 'label': _('全部'), 'icon': 'checklist'})

        # 筛选字段配置
        filter_fields = [
            {
                'name': 'object_type',
                'label': _('业务类型'),
                'all_option_text': _('全部类型'),
                'current_value': object_type,
                'options': [
                    {'value': 'project', 'label': _('项目')},
                    {'value': 'quotation', 'label': _('报价单')},
                    {'value': 'customer', 'label': _('客户')},
                    {'value': 'purchase_order', 'label': _('采购订单')},
                    {'value': 'pricing_order', 'label': _('批价单')},
                    {'value': 'expense', 'label': _('报销单')}
                ]
            },
            {
                'name': 'status',
                'label': _('审批状态'),
                'all_option_text': _('全部状态'),
                'current_value': status,
                'options': [
                    {'value': 'draft', 'label': _('草稿')},
                    {'value': 'pending', 'label': _('审批中')},
                    {'value': 'approved', 'label': _('已通过')},
                    {'value': 'rejected', 'label': _('已拒绝')},
                    {'value': 'recalled', 'label': _('已召回')}
                ]
            }
        ]

        # 表格列配置
        table_columns = [
            {'field': 'approval_number', 'label': _('审批编号'), 'min_width': '120px'},
            {'field': 'project_name', 'label': _('关联项目'), 'min_width': '150px'},
            {'field': 'process_name', 'label': _('流程名称'), 'min_width': '180px'},
            {'field': 'object_type', 'label': _('关联业务'), 'min_width': '100px'},
            {'field': 'creator', 'label': _('提交人'), 'min_width': '80px'},
            {'field': 'current_approver', 'label': _('当前审批人'), 'min_width': '100px'},
            {'field': 'status', 'label': _('状态'), 'min_width': '80px'},
            {'field': 'started_at', 'label': _('发起时间'), 'min_width': '140px'}
        ]

        # 计算结算单可见权限
        from app.services.pricing_order_service import PricingOrderService
        can_view_settlement = PricingOrderService.can_view_settlement_tab(current_user)

        return render_template(
            'approval/tw_center.html',
            current_tab=tab,
            tab_config=tab_config,
            stats=stats,
            filter_fields=filter_fields,
            search_value=search_value,
            table_columns=table_columns,
            items=items,
            total_count=total_count,
            has_more=has_more,
            sort_field=sort_field,
            sort_order=sort_order,
            offset=offset,
            limit=limit,
            can_view_settlement=can_view_settlement
        )
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        current_app.logger.error(f"tw_center error: {error_detail}")
        return f"<h1>Error in approval center:</h1><pre>{error_detail}</pre>", 500


@approval_bp.route('/tw_center_ajax')
@login_required
def tw_center_ajax():
    """审批中心 AJAX 端点 - Tailwind CSS 版本"""
    try:
        # 获取参数
        tab = request.args.get('tab', 'created')
        object_type = request.args.get('object_type', '')
        status = request.args.get('status', '')
        search = request.args.get('search', '').strip()
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 20, type=int)
        sort_field = request.args.get('sort', 'started_at')
        sort_order = request.args.get('order', 'desc')

        # 获取数据
        items, total_count, has_more = get_tw_approval_items(
            tab=tab,
            object_type=object_type,
            status=status,
            offset=offset,
            limit=limit
        )

        # 渲染行 HTML
        html = render_template(
            'approval/tw_center_rows.html',
            items=items
        )

        # 获取统计数据
        from app.helpers.approval_helpers import (
            get_pending_approval_count,
            get_pending_created_count,
            get_pricing_order_pending_count,
            get_order_pending_count,
            get_expense_pending_count
        )

        pending_count = get_pending_approval_count(current_user.id)
        created_count = get_pending_created_count(current_user.id)
        pricing_order_count = get_pricing_order_pending_count(current_user.id)
        order_count = get_order_pending_count(current_user.id)
        expense_count = get_expense_pending_count(current_user.id)

        statistics = {
            'total': pending_count + created_count + pricing_order_count + order_count + expense_count,
            'pending': pending_count,
            'created': created_count,
            'pricing_order': pricing_order_count,
            'order': order_count,
            'expense': expense_count
        }

        tab_counts = {
            'created': created_count,
            'pending': pending_count,
            'pricing_order': pricing_order_count,
            'order': order_count,
            'expense': expense_count
        }

        return jsonify({
            'success': True,
            'html': html,
            'total_count': total_count,
            'loaded_count': len(items),
            'has_more': has_more,
            'statistics': statistics,
            'tab_counts': tab_counts
        })

    except Exception as e:
        import traceback
        current_app.logger.error(f"tw_center_ajax error: {traceback.format_exc()}")
        return jsonify({
            'success': False,
            'message': str(e),
            'html': '<tr><td colspan="8" class="p-12 text-center"><span class="text-slate-500">数据加载失败</span></td></tr>'
        }), 500


def get_tw_approval_items(tab, object_type, status, offset=0, limit=20):
    """获取审批项目列表（用于 Tailwind 版本）

    Returns:
        tuple: (items, total_count, has_more)
    """
    from app.helpers.approval_helpers import (
        get_user_created_approvals,
        get_user_pending_approvals,
        get_all_approvals,
        get_user_pricing_order_approvals,
        get_user_order_approvals
    )

    page = (offset // limit) + 1 if limit > 0 else 1
    per_page = limit

    try:
        if tab == 'pending':
            if status and status not in ['', 'pending']:
                return [], 0, False
            approvals = get_user_pending_approvals(
                user_id=current_user.id,
                object_type=object_type if object_type else None,
                page=page,
                per_page=per_page
            )
        elif tab == 'pricing_order':
            approvals = get_user_pricing_order_approvals(
                user_id=current_user.id,
                status=status if status else None,
                page=page,
                per_page=per_page
            )
        elif tab == 'order':
            approvals = get_user_order_approvals(
                user_id=current_user.id,
                status_filter=status if status else None,
                page=page,
                per_page=per_page
            )
        elif tab == 'expense':
            approvals = get_user_created_approvals(
                user_id=current_user.id,
                object_type='expense',
                status=status if status else None,
                page=page,
                per_page=per_page
            )
        elif tab == 'all' and has_permission('approval_management', 'all'):
            approvals = get_all_approvals(
                object_type=object_type if object_type else None,
                status=status if status else None,
                page=page,
                per_page=per_page
            )
        else:  # created
            if status == 'draft':
                object_type = 'pricing_order'
            approvals = get_user_created_approvals(
                user_id=current_user.id,
                object_type=object_type if object_type else None,
                status=status if status else None,
                page=page,
                per_page=per_page
            )

        # 转换为统一格式
        items = []
        raw_items = approvals.items if hasattr(approvals, 'items') else approvals

        for item in raw_items:
            items.append(convert_approval_item(item, tab))

        total_count = approvals.total if hasattr(approvals, 'total') else len(items)
        has_more = approvals.has_next if hasattr(approvals, 'has_next') else False

        return items, total_count, has_more

    except Exception as e:
        current_app.logger.error(f"get_tw_approval_items error: {str(e)}")
        return [], 0, False


def convert_approval_item(item, tab):
    """将审批项目转换为统一的字典格式"""
    from app.helpers.approval_helpers import get_current_step_info, get_last_approver, get_step_actual_approver

    result = {
        'id': None,
        'object_id': None,  # 业务对象ID（用于链接到详情页）
        'approval_number': None,
        'project_name': None,
        'process_name': None,
        'object_type': None,
        'creator': None,
        'current_approver': None,
        'status': None,
        'started_at': None
    }

    try:
        # 根据不同类型的审批项提取数据
        if hasattr(item, 'wrapper_type'):
            # PricingOrderApprovalWrapper, ExpenseApprovalWrapper, OrderApprovalWrapper
            if item.wrapper_type == 'pricing_order':
                result['id'] = f'po_{item.id}'
                result['object_id'] = item.id
                result['approval_number'] = f'APV-po_{item.id}'
                result['project_name'] = getattr(item, 'project_name', None)
                result['process_name'] = _('批价单审批流程')
                result['object_type'] = 'pricing_order'
                result['creator'] = item.created_by if hasattr(item, 'created_by') else None
                result['status'] = item.approval_status if hasattr(item, 'approval_status') else 'draft'
                result['started_at'] = item.created_at if hasattr(item, 'created_at') else None
            elif item.wrapper_type == 'expense':
                result['id'] = f'expense_{item.id}'
                result['object_id'] = item.id
                result['approval_number'] = f'APV-expense_{item.id}'
                result['project_name'] = None
                result['process_name'] = _('报销单审批流程')
                result['object_type'] = 'expense'
                result['creator'] = item.owner if hasattr(item, 'owner') else None
                result['status'] = item.approval_status if hasattr(item, 'approval_status') else 'draft'
                result['started_at'] = item.created_at if hasattr(item, 'created_at') else None
            elif item.wrapper_type == 'order':
                result['id'] = f'order_{item.id}'
                result['object_id'] = item.id
                result['approval_number'] = f'APV-order_{item.id}'
                result['project_name'] = None
                result['process_name'] = _('订单审批流程')
                result['object_type'] = 'purchase_order'
                result['creator'] = item.created_by if hasattr(item, 'created_by') else None
                result['status'] = item.approval_status if hasattr(item, 'approval_status') else 'draft'
                result['started_at'] = item.created_at if hasattr(item, 'created_at') else None
        else:
            # ApprovalInstance
            result['id'] = item.id
            result['object_id'] = item.object_id if hasattr(item, 'object_id') else None
            result['approval_number'] = f'APV-{item.id}'
            result['object_type'] = item.object_type if hasattr(item, 'object_type') else None
            result['creator'] = item.created_by_user if hasattr(item, 'created_by_user') else None
            result['started_at'] = item.started_at if hasattr(item, 'started_at') else None

            # 获取流程名称
            if hasattr(item, 'process') and item.process:
                result['process_name'] = item.process.name
            elif hasattr(item, 'template_snapshot') and item.template_snapshot:
                result['process_name'] = item.template_snapshot.get('name', _('未知流程'))
            else:
                result['process_name'] = _('未知流程')

            # 获取关联项目名称
            if result['object_type'] == 'project' and hasattr(item, 'object_id'):
                from app.models.project import Project
                project = Project.query.get(item.object_id)
                if project:
                    result['project_name'] = project.name

            # 获取状态
            if hasattr(item, 'status'):
                status = item.status
                if hasattr(status, 'value'):
                    result['status'] = status.value
                elif hasattr(status, 'name'):
                    result['status'] = status.name.lower()
                else:
                    result['status'] = str(status).lower()

            # 获取当前审批人
            try:
                current_step = item.get_current_step_info() if hasattr(item, 'get_current_step_info') else None
                if current_step:
                    result['current_approver'] = get_step_actual_approver(current_step, item)
            except:
                pass

    except Exception as e:
        current_app.logger.error(f"convert_approval_item error: {str(e)}")

    return type('ApprovalItem', (), result)()


@approval_bp.route('/detail/<string:instance_id>')
@login_required
def detail(instance_id):
    """审批详情视图
    
    显示审批流程的详细信息，包括流程图、当前步骤和所有审批步骤
    支持普通审批实例（数字ID）、批价单审批（po_数字格式）、报销单审批（expense_数字格式）和订单审批（order_数字格式）
    """
    # 检查是否是批价单审批
    if isinstance(instance_id, str) and instance_id.startswith('po_'):
        # 处理批价单审批详情
        try:
            pricing_order_id = int(instance_id.split('_')[1])
            # 重定向到批价单详情页面
            return redirect(url_for('pricing_order.edit_pricing_order', order_id=pricing_order_id))
        except (ValueError, IndexError):
            flash(_('无效的批价单审批ID'), 'danger')
            return redirect(url_for('approval.center'))
    
    # 检查是否是报销单审批
    if isinstance(instance_id, str) and instance_id.startswith('expense_'):
        # 处理报销单审批详情
        try:
            expense_id = int(instance_id.split('_')[1])
            # 重定向到报销单详情页面
            return redirect(url_for('expense.expense_detail', id=expense_id, from_approval='true'))
        except (ValueError, IndexError):
            flash(_('无效的报销单审批ID'), 'danger')
            return redirect(url_for('approval.center'))
    
    # 检查是否是订单审批
    if isinstance(instance_id, str) and instance_id.startswith('order_'):
        # 处理订单审批详情
        try:
            order_id = int(instance_id.split('_')[1])
            # 重定向到订单详情页面
            return redirect(url_for('inventory.order_detail', id=order_id))
        except (ValueError, IndexError):
            flash(_('无效的订单审批ID'), 'danger')
            return redirect(url_for('approval.center'))
    
    # 处理普通审批实例
    try:
        instance_id = int(instance_id)
    except (ValueError, TypeError):
        flash(_('无效的审批实例ID'), 'danger')
        return redirect(url_for('approval.center'))
    
    # 获取审批实例
    instance = get_approval_details(instance_id)
    
    # 获取对应业务对象的URL
    object_url = get_approval_object_url(instance)
    
    # 获取审批记录和当前步骤信息
    records = get_approval_records_by_instance(instance_id)
    current_step = get_current_step_info(instance) if instance.status == ApprovalStatus.PENDING else None
    
    # 获取所有模板步骤
    all_steps = get_template_steps(instance.process_id)
    
    # 构建完整的审批步骤信息
    completed_step_ids = [record.step_id for record in records]
    
    workflow_steps = []
    for step in all_steps:
        # 获取审批人真实姓名
        approver_name = step.approver.real_name if step.approver and hasattr(step.approver, 'real_name') and step.approver.real_name else step.approver.username if step.approver else '未指定'
        
        step_info = {
            'id': step.id,
            'name': step.step_name,
            'order': step.step_order,
            'approver': approver_name,
            'is_completed': step.id in completed_step_ids,
            'is_current': current_step and current_step.id == step.id,
        }
        
        # 查找对应的审批记录
        for record in records:
            if record.step_id == step.id:
                step_info['action'] = record.action
                step_info['comment'] = record.comment
                step_info['timestamp'] = record.timestamp
                break
                
        workflow_steps.append(step_info)
    
    # 导入工具函数
    from app.utils.dictionary_helpers import project_type_label, project_stage_label
    from app.models.project import Project
    
    # 获取项目数据的辅助函数
    def get_project_by_id(project_id):
        return Project.query.get(project_id)
    
    # 获取报价单数据的辅助函数
    def get_quotation_by_id(quotation_id):
        from app.models.quotation import Quotation
        return Quotation.query.get(quotation_id)
    
    # 渲染审批详情模板
    return render_template(
        'approval/detail.html',
        instance=instance,
        records=records,
        current_step=current_step,
        workflow_steps=workflow_steps,
        object_url=object_url,
        ApprovalStatus=ApprovalStatus,
        total_steps=len(all_steps),
        # 添加工具函数到模板上下文
        project_type_label=project_type_label,
        project_stage_label=project_stage_label,
        get_project_by_id=get_project_by_id,
        get_quotation_by_id=get_quotation_by_id
    )


@approval_bp.route('/start', methods=['POST'])
@login_required
def start_approval():
    """发起审批流程
    
    从业务对象详情页调用，创建新的审批实例
    """
    # 获取表单数据
    object_type = request.form.get('object_type')
    object_id = request.form.get('object_id', type=int)
    template_id = request.form.get('template_id', type=int)
    
    # 参数验证
    if not all([object_type, object_id, template_id]):
        flash(_('参数不完整，无法发起审批'), 'danger')
        return redirect(request.referrer or url_for('index'))
    
    # 获取业务对象并检查权限
    business_obj = None
    if object_type == 'project':
        from app.models.project import Project
        business_obj = Project.query.get(object_id)
    elif object_type == 'quotation':
        from app.models.quotation import Quotation
        business_obj = Quotation.query.get(object_id)
    elif object_type == 'customer':
        from app.models.customer import Company
        business_obj = Company.query.filter_by(id=object_id, is_deleted=False).first()
    
    if not business_obj:
        flash(f'找不到业务对象: {object_type}:{object_id}', 'danger')
        return redirect(request.referrer or url_for('index'))
    
    # 检查发起审批的权限
    if not can_start_approval(business_obj, current_user):
        flash(_('您没有权限发起此审批流程'), 'danger')
        return redirect(request.referrer or url_for('index'))
    
    # 获取审批流程模板
    template = ApprovalProcessTemplate.query.get(template_id)
    if not template:
        flash(_('审批流程模板不存在'), 'danger')
        return redirect(request.referrer or url_for('index'))
    
    # 检查模板是否适用于当前业务对象类型
    if template.object_type != object_type:
        flash(f'审批模板不适用于当前业务类型: {object_type}', 'danger')
        return redirect(request.referrer or url_for('index'))
    
    # 获取业务对象的特定类型信息
    business_type = None
    if object_type == 'project':
        business_type = business_obj.project_type
    
    # 检查是否包含授权编号步骤
    has_authorization_step = any(
        step.action_type == 'authorization' 
        for step in ApprovalStep.query.filter_by(process_id=template_id).all()
        if hasattr(step, 'action_type') and step.action_type
    )
    
    # 检查必填字段是否已填写
    missing_fields = []
    if hasattr(template, 'required_fields') and template.required_fields and len(template.required_fields) > 0:
        # 根据业务对象类型获取对象
        if object_type == 'project':
            from app.models.project import Project
            obj = Project.query.get(object_id)
        elif object_type == 'quotation':
            from app.models.quotation import Quotation
            obj = Quotation.query.get(object_id)
        elif object_type == 'customer':
            from app.models.customer import Company
            obj = Company.query.filter_by(id=object_id, is_deleted=False).first()
        else:
            obj = None
        
        if not obj:
            flash(f'找不到业务对象: {object_type}:{object_id}', 'danger')
            return redirect(request.referrer or url_for('index'))
        
        # 检查每个必填字段
        for field in template.required_fields:
            if hasattr(obj, field):
                field_value = getattr(obj, field)
                if field_value is None or field_value == '' or (isinstance(field_value, list) and len(field_value) == 0):
                    field_display = _get_field_display_name(field)
                    missing_fields.append({'code': field, 'name': field_display})
            else:
                current_app.logger.warning(f"业务对象 {object_type} 没有字段 {field}")
                field_display = _get_field_display_name(field)
                missing_fields.append({'code': field, 'name': field_display})
        
        if missing_fields:
            # 构建错误信息JSON并传递给前端
            missing_fields_json = json.dumps(missing_fields)
            readable_fields = [field['name'] for field in missing_fields]
            error_msg = f"发起审批失败: 以下字段必填但未填写: {', '.join(readable_fields)}"
            flash(error_msg, 'danger')
            
            # 将缺失字段信息保存到会话中，以便前端能够高亮显示
            session['missing_fields'] = missing_fields_json
            session['failed_approval_template_id'] = template_id
            
            # 重定向回业务对象详情页
            if object_type == 'project':
                return redirect(url_for('project.view_project', project_id=object_id, missing_fields=missing_fields_json))
            elif object_type == 'quotation':
                return redirect(url_for('quotation.view_quotation', id=object_id, missing_fields=missing_fields_json))
            elif object_type == 'customer':
                return redirect(url_for('customer.view_company', company_id=object_id, missing_fields=missing_fields_json))
            else:
                return redirect(url_for('index'))
    
    # 如果是项目类型且包含授权步骤，先锁定项目
    if object_type == 'project' and has_authorization_step:
        lock_result = lock_project(
            project_id=object_id, 
            reason=f"授权编号审批锁定: {template.name}",
            user_id=current_user.id
        )
        if not lock_result:
            flash(_('无法锁定项目，可能已被其他流程锁定'), 'warning')
            # 继续处理，因为锁定失败可能是由于项目已经被锁定
    
    # 创建审批实例
    instance = start_approval_process(object_type, object_id, template_id, user_id=current_user.id)
    
    if instance:
        flash(_('审批流程已成功发起'), 'success')
        # 重定向到审批详情页面，显示完整的审批流程图
        return redirect(url_for('approval.detail', instance_id=instance.id))
    else:
        # 如果创建失败且项目已锁定，则解锁项目
        if object_type == 'project' and has_authorization_step:
            unlock_project(object_id, current_user.id)
        flash(_('发起审批失败，请检查是否已存在审批流程或模板是否有效'), 'danger')
    
    # 重定向回业务对象详情页
    if object_type == 'project':
        return redirect(url_for('project.view_project', project_id=object_id))
    elif object_type == 'quotation':
        return redirect(url_for('quotation.view_quotation', id=object_id))
    elif object_type == 'customer':
        return redirect(url_for('customer.view_company', company_id=object_id))
    else:
        return redirect(url_for('index'))


@approval_bp.route('/approve/<int:instance_id>', methods=['POST'])
@login_required
def approve(instance_id):
    """处理审批
    
    处理用户对审批实例的同意/拒绝操作
    """
    
    # 获取表单数据
    action_value = request.form.get('action')
    comment = request.form.get('comment', '')
    project_type = request.form.get('project_type')  # 获取项目类型，如果有的话
    
    # 调试：记录请求头信息
    
    # 检查是否是AJAX请求 - 修复检测逻辑
    is_ajax = (
        request.headers.get('X-Requested-With') == 'XMLHttpRequest' or
        'X-CSRFToken' in request.headers or
        request.is_json or
        request.headers.get('Accept', '').find('application/json') != -1
    )
    
    
    # 参数验证
    if not action_value or action_value not in ('approve', 'reject'):
        if is_ajax:
            return jsonify({
                'success': False,
                'message': '无效的审批操作'
            }), 400
        flash(_('无效的审批操作'), 'danger')
        return redirect(request.referrer or url_for('approval.center'))
    
    # 转换为枚举值
    if action_value == 'approve':
        action = ApprovalAction.APPROVE
    else:
        action = ApprovalAction.REJECT
    
    # 获取审批实例，检查当前步骤是否是授权步骤
    instance = ApprovalInstance.query.get(instance_id)
    if not instance:
        if is_ajax:
            return jsonify({
                'success': False,
                'message': '找不到审批实例'
            }), 404
        flash(_('找不到审批实例'), 'danger')
        return redirect(url_for('approval.center'))
    
    # 收集批价单相关数据
    pricing_order_data = {}
    if instance.object_type == 'pricing_order':
        current_app.logger.info(f"批价单审批 - 开始收集页面数据，实例ID: {instance_id}")

        # 从JSON字符串解析完整数据（包含基本信息和明细数据）
        pricing_order_data_str = request.form.get('pricing_order_data')
        if pricing_order_data_str:
            try:
                import json
                pricing_order_data = json.loads(pricing_order_data_str)
                current_app.logger.info(f"批价单审批 - 成功解析数据，包含字段: {list(pricing_order_data.keys())}")
                current_app.logger.info(f"批价单审批 - 数据详情: {pricing_order_data}")
            except json.JSONDecodeError as e:
                current_app.logger.error(f"批价单审批 - JSON解析失败: {str(e)}")
                pricing_order_data = {}
        else:
            current_app.logger.warning(f"批价单审批 - 未收到pricing_order_data字段")

        current_app.logger.info(f"批价单审批 - 是否有数据: {bool(pricing_order_data)}")
    
    current_step = get_current_step_info(instance)
    # 检查是否是授权步骤或分支决策步骤（分支决策步骤可能包含授权动作）
    action_type = getattr(current_step, 'action_type', None) if current_step else None
    is_authorization_step = (
        action_type in [
            'authorization',
            'project_authorization',
            'channel_authorization',
            'business_authorization',
            'customer_service_authorization'
        ]
    )
    is_branch_decision_step = (
        current_step and 
        hasattr(current_step, 'action_type') and 
        current_step.action_type == 'branch_decision'
    )
    
    try:
        # 执行审批操作，如果是授权步骤或分支决策步骤并且提供了项目类型，则传递项目类型
        from app.helpers.approval_helpers import process_approval as helper_process_approval
        
        if pricing_order_data:
            pass
        
        # 对于项目审批，如果是授权步骤或分支决策步骤，传递项目类型参数
        if (is_authorization_step or is_branch_decision_step) and instance.object_type == 'project':
            # 如果前端没有提供project_type，从项目对象中获取
            if not project_type:
                from app.models.project import Project
                project_obj = Project.query.get(instance.object_id)
                if project_obj:
                    project_type = project_obj.project_type
            
            success = helper_process_approval(instance_id, action, comment, project_type=project_type)
        elif instance.object_type == 'pricing_order' and pricing_order_data:
            
            # 对于批价单审批，传递收集到的页面数据
            success = helper_process_approval(instance_id, action, comment, pricing_order_data=pricing_order_data)
        else:
            success = helper_process_approval(instance_id, action, comment)
        
        if success:
            if action == ApprovalAction.APPROVE:
                success_message = '已同意此审批'
                # 记录日志
                current_app.logger.info(f"用户 {current_user.username} 同意了审批 {instance_id}")
                # 记录授权信息到日志，但不在消息中显示具体编号
                if instance.object_type == 'project' and (is_authorization_step or is_branch_decision_step):
                    from app.models.project import Project
                    project = Project.query.get(instance.object_id)
                    if project and project.authorization_code:
                        current_app.logger.info(f"为项目 {project.id} 生成授权编号: {project.authorization_code}")
            else:
                success_message = '已拒绝此审批'
                current_app.logger.info(f"用户 {current_user.username} 拒绝了审批 {instance_id}")
            
            if is_ajax:
                current_app.logger.info(f"返回JSON响应: {success_message}")
                return jsonify({
                    'success': True,
                    'message': success_message
                })
            flash(success_message, 'success' if action == ApprovalAction.APPROVE else 'warning')
        else:
            error_message = '处理审批失败，请检查您是否有权限或该审批是否有效'
            current_app.logger.error(f"用户 {current_user.username} 处理审批 {instance_id} 失败")
            
            if is_ajax:
                return jsonify({
                    'success': False,
                    'message': error_message
                }), 400
            flash(error_message, 'danger')
            
    except Exception as e:
        error_message = f'处理审批时发生错误: {str(e)}'
        current_app.logger.error(f"用户 {current_user.username} 处理审批 {instance_id} 时发生异常: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        
        if is_ajax:
            return jsonify({
                'success': False,
                'message': error_message
            }), 500
        flash(error_message, 'danger')
    
    # 对于非AJAX请求，返回到审批详情页面
    current_app.logger.info(f"返回重定向响应到审批详情页面")
    return redirect(url_for('approval.detail', instance_id=instance_id))


@approval_bp.route('/api/template-steps/<int:template_id>')
def get_template_steps_api(template_id):
    """API端点：获取审批模板的步骤信息
    
    Returns:
        JSON格式的模板步骤信息
    """
    try:
        # 获取模板信息
        template = ApprovalProcessTemplate.query.get(template_id)
        if not template:
            return jsonify({
                'success': False,
                'message': '未找到模板'
            }), 404
            
        # 获取模板步骤
        steps = get_template_steps(template_id)
        if not steps:
            return jsonify({
                'success': False,
                'message': '该模板没有配置步骤'
            }), 404
        
        # 转换为JSON格式
        steps_data = []
        for step in steps:
            steps_data.append({
                'id': step.id,
                'step_order': step.step_order,
                'step_name': step.step_name,
                'approver_id': step.approver_user_id,
                'approver_name': step.approver.username if step.approver else '未指定',
                'send_email': step.send_email
            })
        
        # 构建模板信息，确保包含required_fields字段
        required_fields = []
        if hasattr(template, 'required_fields') and template.required_fields:
            # 确保处理JSON字符串或已经是列表的情况
            if isinstance(template.required_fields, str):
                try:
                    required_fields = json.loads(template.required_fields)
                except:
                    current_app.logger.error(f"解析required_fields失败: {template.required_fields}")
                    required_fields = []
            else:
                required_fields = template.required_fields
        
        template_data = {
            'id': template.id,
            'name': template.name,
            'object_type': template.object_type,
            'required_fields': required_fields
        }
        
        # 将字段转换为可读名称
        field_display_names = {}
        for field in required_fields:
            field_display_names[field] = _get_field_display_name(field)
        
        return jsonify({
            'success': True,
            'steps': steps_data,
            'template': template_data,
            'field_display_names': field_display_names
        })
    except Exception as e:
        current_app.logger.error(f"获取模板步骤出错: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'获取模板步骤出错: {str(e)}'
        }), 500 


@approval_bp.route('/api/check-required-fields', methods=['POST'])
def check_required_fields_api():
    """API端点：检查业务对象是否已填写必填字段
    
    Returns:
        JSON格式的字段检查结果
    """
    try:
        # 获取请求数据
        data = request.json
        
        if not data:
            return jsonify({
                'success': False,
                'message': '请求数据为空'
            }), 400
            
        object_type = data.get('object_type')
        object_id = data.get('object_id')
        required_fields = data.get('required_fields', [])
        
        if not all([object_type, object_id]) or not isinstance(required_fields, list):
            return jsonify({
                'success': False,
                'message': '参数不完整或格式错误'
            }), 400
            
        # 根据业务对象类型获取对象
        if object_type == 'project':
            from app.models.project import Project
            obj = Project.query.get(object_id)
        elif object_type == 'quotation':
            from app.models.quotation import Quotation
            obj = Quotation.query.get(object_id)
        elif object_type == 'customer':
            from app.models.customer import Company
            obj = Company.query.filter_by(id=object_id, is_deleted=False).first()
        else:
            return jsonify({
                'success': False,
                'message': f'不支持的业务对象类型: {object_type}'
            }), 400
        
        if not obj:
            return jsonify({
                'success': False,
                'message': f'找不到业务对象: {object_type}:{object_id}'
            }), 404
        
        # 检查每个必填字段
        missing_fields = []
        for field in required_fields:
            if hasattr(obj, field):
                field_value = getattr(obj, field)
                if field_value is None or field_value == '' or (isinstance(field_value, list) and len(field_value) == 0):
                    missing_fields.append(field)
            else:
                current_app.logger.warning(f"业务对象 {object_type} 没有字段 {field}")
                missing_fields.append(field)
        
        # 转换字段名为可读名称
        missing_fields_display = []
        for field in missing_fields:
            display_name = _get_field_display_name(field)
            missing_fields_display.append({
                'code': field,
                'name': display_name
            })
        
        return jsonify({
            'success': True,
            'missing_fields': missing_fields,
            'missing_fields_display': missing_fields_display,
            'is_valid': len(missing_fields) == 0
        })
    except Exception as e:
        current_app.logger.error(f"检查必填字段出错: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'检查必填字段出错: {str(e)}'
        }), 500


@approval_bp.route('/delete/<int:instance_id>', methods=['POST'])
@login_required
@admin_required
def delete_approval(instance_id):
    """删除审批实例
    
    仅管理员可以删除审批实例
    """
    # 获取审批实例信息
    instance = get_approval_details(instance_id)
    if not instance:
        flash(_('找不到审批实例'), 'danger')
        return redirect(url_for('approval.center'))
    
    # 获取原业务对象的URL
    object_url = get_approval_object_url(instance)
    
    # 执行删除操作
    result = delete_approval_instance(instance_id)
    
    if result:
        flash(_('审批实例已成功删除'), 'success')
    else:
        flash(_('删除审批实例失败'), 'danger')
    
    # 返回到审批中心
    return redirect(url_for('approval.center'))


@approval_bp.route('/api/preview-authorization-code', methods=['POST'])
def preview_authorization_code():
    """API端点：预览项目授权编号
    
    根据项目类型预览可能生成的授权编号格式
    """
    project_type = request.json.get('project_type')
    if not project_type:
        return jsonify({'success': False, 'message': '未提供项目类型'}), 400
    
    # 将项目类型映射为中文
    from app.utils.dictionary_helpers import project_type_label
    from app.utils.i18n import get_current_language
    lang_code = get_current_language()
    project_type_zh = project_type_label(project_type, lang_code)
    
    # 从utils中获取前缀
    from app.utils.authorization import PROJECT_TYPE_PREFIXES
    prefix = PROJECT_TYPE_PREFIXES.get(project_type_zh)
    
    if not prefix:
        return jsonify({'success': False, 'message': '无效的项目类型'}), 400
    
    # 构建预览格式（不实际生成，避免数据库查询）
    year_month = datetime.now().strftime('%Y%m')
    preview_code = f"{prefix}{year_month}-001"
    
    return jsonify({
        'success': True, 
        'preview_code': preview_code,
        'prefix': prefix,
        'year_month': year_month
    })


@approval_bp.route('/api/check-pricing-approval-limits', methods=['POST'])
@login_required
def check_pricing_approval_limits():
    """API端点：检查批价单审批权限下限
    
    在审批前检查当前用户的权限下限是否符合批价单/结算单折扣率
    返回权限违规警告信息
    """
    try:
        data = request.json
        object_type = data.get('object_type')  # 'pricing_order' 或 'settlement_order'
        object_id = data.get('object_id')
        approver_id = data.get('approver_id', current_user.id)
        
        if not all([object_type, object_id]):
            return jsonify({
                'success': False, 
                'message': '缺少必要参数'
            }), 400
        
        # 获取审批人信息
        from app.models.user import User
        approver = User.query.get(approver_id)
        if not approver:
            return jsonify({
                'success': False, 
                'message': '找不到审批人信息'
            }), 404
        
        # 获取审批人角色权限配置
        from app.permissions import get_role_permission
        role_permission = get_role_permission(approver.role, object_type)
        if not role_permission:
            return jsonify({
                'success': False, 
                'message': f'找不到角色权限配置: {approver.role}'
            }), 404
        
        pricing_limit = role_permission.pricing_discount_limit or 0
        settlement_limit = role_permission.settlement_discount_limit or 0
        
        violations = []
        warnings = []
        
        # 根据对象类型检查权限下限
        if object_type == 'pricing_order':
            from app.models.pricing_order import PricingOrder
            pricing_order = PricingOrder.query.get(object_id)
            if not pricing_order:
                return jsonify({
                    'success': False, 
                    'message': '找不到批价单'
                }), 404
            
            current_pricing_rate = (pricing_order.pricing_total_discount_rate or 1.0) * 100
            current_settlement_rate = (pricing_order.settlement_total_discount_rate or 1.0) * 100
            
            if current_pricing_rate < pricing_limit:
                violations.append({
                    'type': 'pricing',
                    'current': round(current_pricing_rate, 1),
                    'limit': pricing_limit,
                    'message': f'批价单折扣率{current_pricing_rate:.1f}%低于权限下限{pricing_limit}%'
                })
            
            if settlement_limit > 0 and current_settlement_rate < settlement_limit:
                violations.append({
                    'type': 'settlement',
                    'current': round(current_settlement_rate, 1),
                    'limit': settlement_limit,
                    'message': f'结算单折扣率{current_settlement_rate:.1f}%低于权限下限{settlement_limit}%'
                })
                
        elif object_type == 'settlement_order':
            from app.models.pricing_order import SettlementOrder
            settlement_order = SettlementOrder.query.get(object_id)
            if not settlement_order:
                return jsonify({
                    'success': False, 
                    'message': '找不到结算单'
                }), 404
            
            current_settlement_rate = (settlement_order.total_discount_rate or 1.0) * 100
            
            if settlement_limit > 0 and current_settlement_rate < settlement_limit:
                violations.append({
                    'type': 'settlement',
                    'current': round(current_settlement_rate, 1),
                    'limit': settlement_limit,
                    'message': f'结算单折扣率{current_settlement_rate:.1f}%低于权限下限{settlement_limit}%'
                })
        
        # 构建返回结果
        result = {
            'success': True,
            'has_violations': len(violations) > 0,
            'violations': violations,
            'warnings': warnings,
            'approver': {
                'name': approver.real_name or approver.username,
                'role': approver.role,
                'limits': {
                    'pricing_limit': pricing_limit,
                    'settlement_limit': settlement_limit
                }
            }
        }
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"检查批价审批权限下限失败: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'权限检查失败: {str(e)}'
        }), 500


@approval_bp.route('/authorize/<int:instance_id>', methods=['GET'])
@login_required
def authorize(instance_id):
    """显示授权编号审批页面
    
    仅对含有authorization动作的步骤显示特殊界面
    """
    instance = ApprovalInstance.query.get_or_404(instance_id)
    
    # 检查当前用户是否可以审批
    if not can_user_approve(instance_id):
        flash(_('您没有权限进行此审批操作'), 'danger')
        return redirect(url_for('approval.detail', instance_id=instance_id))
    
    # 获取当前步骤信息
    current_step = get_current_step_info(instance)
    
    # 检查是否是授权步骤
    if not (hasattr(current_step, 'action_type') and current_step.action_type == 'authorization'):
        # 如果不是授权步骤，重定向到普通审批页面
        return redirect(url_for('approval.detail', instance_id=instance_id))
    
    # 确认是项目类型
    if instance.object_type != 'project':
        flash(_('此授权步骤仅适用于项目'), 'warning')
        return redirect(url_for('approval.detail', instance_id=instance_id))
    
    # 获取项目信息
    from app.models.project import Project
    project = Project.query.get(instance.object_id)
    if not project:
        flash(_('找不到相关项目'), 'danger')
        return redirect(url_for('approval.center'))
    
    # 获取项目类型选项
    from app.utils.dictionary_helpers import PROJECT_TYPE_LABELS, project_type_label
    
    # 获取当前日期信息，用于预览
    today = datetime.now()
    year = today.strftime('%Y')
    month = today.strftime('%m')
    
    # 获取项目类型对应的前缀
    from app.utils.authorization import PROJECT_TYPE_PREFIXES
    
    # 生成当前类型的预览授权编号 
    from app.utils.i18n import get_current_language
    lang_code = get_current_language()
    
    project_type_zh = project_type_label(project.project_type, lang_code) if project.project_type else ''
    prefix = PROJECT_TYPE_PREFIXES.get(project_type_zh, '')
    preview_code = f"{prefix}{year}{month}-001" if prefix else ''
    
    # 为模板传递当前项目类型的中文显示名称
    current_project_type_display = project_type_label(project.project_type, lang_code) if project.project_type else project.project_type
    
    return render_template('approval/authorization_step.html',
                          instance=instance,
                          project=project,
                          project_types=PROJECT_TYPE_LABELS,
                          type_prefixes=PROJECT_TYPE_PREFIXES,
                          today_date=today.strftime('%Y-%m-%d'),
                          year=year,
                          month=month,
                          prefix=prefix,
                          preview_code=preview_code,
                          current_project_type_display=current_project_type_display)


@approval_bp.route('/quotation/<int:quotation_id>/approve', methods=['POST'])
@login_required
def approve_quotation(quotation_id):
    """报价审核API - 对指定报价单进行审核操作"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400
            
        action = data.get('action')  # approve 或 reject
        comment = data.get('comment', '')
        
        if action not in ['approve', 'reject']:
            return jsonify({'success': False, 'message': '无效的审核动作'}), 400
        
        # 获取报价单
        from app.models.quotation import Quotation
        quotation = Quotation.query.get(quotation_id)
        if not quotation:
            return jsonify({'success': False, 'message': '报价单不存在'}), 404
        
        # 检查用户权限 - 只有管理员和有审批权限的用户可以执行审核
        from app.permissions import has_permission
        if not (has_permission('quotation', 'admin') or has_permission('quotation_approval', 'create')):
            return jsonify({'success': False, 'message': '无权限执行审核操作'}), 403
        
        # 获取项目当前阶段
        project_stage = quotation.project.current_stage if quotation.project else None
        if not project_stage:
            return jsonify({'success': False, 'message': '项目阶段未设置，无法执行审核'}), 400
        
        # 检查是否已经在该阶段获得审核
        from app.models.quotation import QuotationApprovalStatus
        target_approval_status = QuotationApprovalStatus.STAGE_TO_APPROVAL.get(project_stage)
        if not target_approval_status:
            return jsonify({'success': False, 'message': f'项目阶段 {project_stage} 不支持审核'}), 400
        
        # 检查是否已经通过该阶段审核
        if quotation.approved_stages and target_approval_status in quotation.approved_stages:
            return jsonify({'success': False, 'message': f'该报价单已在 {project_stage} 阶段获得审核，不允许重复审核'}), 400
        
        # 执行审核操作
        if action == 'approve':
            # 通过审核
            quotation.approval_status = target_approval_status
            
            # 添加到已审核阶段列表
            if not quotation.approved_stages:
                quotation.approved_stages = []
            quotation.approved_stages.append(target_approval_status)
            
            # 添加审核历史
            if not quotation.approval_history:
                quotation.approval_history = []
            quotation.approval_history.append({
                'action': 'approve',
                'stage': project_stage,
                'approval_status': target_approval_status,
                'approver_id': current_user.id,
                'approver_name': current_user.username,
                'comment': comment,
                'timestamp': datetime.now().isoformat()
            })
            
            # 添加待确认徽章（新增逻辑）
            quotation.set_pending_confirmation_badge()
            
            message = f'报价单已通过 {QuotationApprovalStatus.APPROVAL_STATUS_LABELS.get(target_approval_status, {}).get("zh", target_approval_status)} 审核'
            
        else:  # action == 'reject'
            # 拒绝审核
            quotation.approval_status = QuotationApprovalStatus.REJECTED
            
            # 添加审核历史
            if not quotation.approval_history:
                quotation.approval_history = []
            quotation.approval_history.append({
                'action': 'reject',
                'stage': project_stage,
                'approver_id': current_user.id,
                'approver_name': current_user.username,
                'comment': comment,
                'timestamp': datetime.now().isoformat()
            })
            
            message = '报价单审核被拒绝'
        
        # 保存到数据库
        from app import db
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': message,
            'approval_status': quotation.approval_status
        })
        
    except Exception as e:
        current_app.logger.error(f"报价审核操作失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        
        from app import db
        db.session.rollback()
        return jsonify({'success': False, 'message': f'审核操作失败: {str(e)}'}), 500


@approval_bp.route('/quotation/<int:quotation_id>/approval-status', methods=['GET'])
@login_required  
def get_quotation_approval_status(quotation_id):
    """获取报价单审核状态API"""
    try:
        # 获取报价单
        from app.models.quotation import Quotation
        quotation = Quotation.query.get(quotation_id)
        if not quotation:
            return jsonify({'success': False, 'message': '报价单不存在'}), 404
        
        # 获取项目当前阶段
        project_stage = quotation.project.current_stage if quotation.project else None
        
        # 检查当前阶段是否可以审核
        from app.models.quotation import QuotationApprovalStatus
        target_approval_status = QuotationApprovalStatus.STAGE_TO_APPROVAL.get(project_stage) if project_stage else None
        can_approve_current_stage = (
            project_stage and 
            target_approval_status and 
            (not quotation.approved_stages or target_approval_status not in quotation.approved_stages)
        )
        
        # 检查用户权限
        from app.permissions import has_permission
        can_user_approve = has_permission('quotation', 'admin') or has_permission('quotation_approval', 'create')
        
        return jsonify({
            'success': True,
            'quotation_id': quotation_id,
            'approval_status': quotation.approval_status,
            'approved_stages': quotation.approved_stages or [],
            'approval_history': quotation.approval_history or [],
            'project_stage': project_stage,
            'target_approval_status': target_approval_status,
            'can_approve_current_stage': can_approve_current_stage,
            'can_user_approve': can_user_approve
        })
        
    except Exception as e:
        current_app.logger.error(f"获取报价审核状态失败: {str(e)}")
        return jsonify({'success': False, 'message': f'获取审核状态失败: {str(e)}'}), 500 


@approval_bp.route('/batch-delete', methods=['POST'])
@login_required
def batch_delete():
    """批量删除审批流程
    
    只有管理员或审批发起人可以删除审批流程
    """
    approval_ids = request.form.getlist('approval_ids')
    
    if not approval_ids:
        flash(_('请选择要删除的审批流程'), 'warning')
        return redirect(url_for('approval.center'))
    
    try:
        deleted_count = 0
        failed_count = 0
        
        for approval_id in approval_ids:
            try:
                # 检查是否是批价单ID（格式：po_123）
                if approval_id.startswith('po_'):
                    # 处理批价单删除
                    pricing_order_id = int(approval_id.split('_')[1])
                    from app.models.pricing_order import PricingOrder
                    pricing_order = PricingOrder.query.get(pricing_order_id)
                    
                    if not pricing_order:
                        failed_count += 1
                        continue
                    
                    # 检查权限：只有管理员或发起人可以删除
                    if current_user.role != 'admin' and pricing_order.created_by != current_user.id:
                        failed_count += 1
                        continue
                    
                    # 删除批价单（只允许删除草稿状态的批价单）
                    if pricing_order.status == 'draft':
                        db.session.delete(pricing_order)
                        deleted_count += 1
                    else:
                        failed_count += 1
                        continue
                        
                else:
                    # 处理通用审批实例删除
                    instance = ApprovalInstance.query.get(int(approval_id))
                    if not instance:
                        failed_count += 1
                        continue
                    
                    # 检查权限：只有管理员或发起人可以删除
                    if current_user.role != 'admin' and instance.creator_id != current_user.id:
                        failed_count += 1
                        continue
                    
                    # 删除审批实例
                    delete_approval_instance(instance.id)
                    deleted_count += 1
                
            except Exception as e:
                current_app.logger.error(f"删除审批流程 {approval_id} 失败: {str(e)}")
                failed_count += 1
        
        # 统一提交数据库事务
        if deleted_count > 0:
            db.session.commit()
        
        # 显示结果消息
        if deleted_count > 0:
            flash(f'成功删除 {deleted_count} 个审批流程', 'success')
        
        if failed_count > 0:
            flash(f'{failed_count} 个审批流程删除失败（权限不足或不存在）', 'warning')
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"批量删除审批流程失败: {str(e)}")
        flash(_('批量删除操作失败，请稍后重试'), 'danger')
    
    return redirect(url_for('approval.center')) 


@approval_bp.route('/process/<int:instance_id>', methods=['POST'])
@login_required
def process_approval(instance_id):
    """处理审批 - JSON API版本
    
    用于支持前端AJAX请求的审批处理
    """
    try:
        # 获取JSON数据
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'})
        
        action = data.get('action')
        comment = data.get('comment', '')
        
        if action not in ['approve', 'reject']:
            return jsonify({'success': False, 'message': '无效的操作类型'})
        
        # 获取审批实例
        instance = ApprovalInstance.query.get_or_404(instance_id)
        
        # 检查用户权限
        if not can_user_approve(instance_id, current_user.id):
            return jsonify({'success': False, 'message': '您没有权限审批此流程'})
        
        # 检查是否是授权步骤（包含所有授权类型）
        current_step = get_current_step_info(instance)
        action_type = getattr(current_step, 'action_type', None) if current_step else None
        is_authorization_step = action_type in [
            'authorization',
            'project_authorization',
            'channel_authorization',
            'business_authorization',
            'customer_service_authorization'
        ]
        
        # 处理审批
        approval_action = ApprovalAction.APPROVE if action == 'approve' else ApprovalAction.REJECT
        success = process_approval_with_project_type(
            instance_id,
            approval_action,
            project_type=None,
            comment=comment,
            user_id=current_user.id,
            pricing_order_data=None
        )
        
        if success:
            message = '审批通过' if action == 'approve' else '审批拒绝'
            
            # 如果是项目授权步骤，添加授权信息
            if instance.object_type == 'project' and is_authorization_step and action == 'approve':
                from app.models.project import Project
                project = Project.query.get(instance.object_id)
                if project and project.authorization_code:
                    message += f'，已生成授权编号: {project.authorization_code}'
            
            return jsonify({'success': True, 'message': message})
        else:
            return jsonify({'success': False, 'message': '审批处理失败，请检查您的权限或审批状态'})
            
    except Exception as e:
        current_app.logger.error(f"处理审批请求失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': '服务器错误，请稍后重试'}), 500


@approval_bp.route('/test-links')
@login_required
def test_links():
    """测试审批链接生成"""
    return render_template('test_approval_links.html') 


@approval_bp.route('/test-center-links')
@login_required
def test_center_links():
    """测试审批中心链接生成"""
    return render_template('test_approval_center.html') 


@approval_bp.route('/recall/<int:instance_id>', methods=['POST'])
@login_required
def recall_approval(instance_id):
    """召回审批流程
    
    只有发起人可以召回正在进行中的审批流程
    """
    try:
        # 获取审批实例
        instance = ApprovalInstance.query.get_or_404(instance_id)
        
        # 检查权限：只有发起人可以召回
        if current_user.id != instance.created_by:
            return jsonify({'success': False, 'message': '只有发起人可以召回审批流程'}), 403
        
        # 检查状态：只有进行中的审批可以召回
        if instance.status != ApprovalStatus.PENDING:
            return jsonify({'success': False, 'message': '只有进行中的审批流程可以召回'}), 400
        
        # 获取召回原因
        data = request.get_json()
        reason = data.get('reason', '') if data else ''
        
        # 更新审批实例状态
        instance.status = ApprovalStatus.REJECTED
        instance.ended_at = datetime.now()
        
        # 获取当前步骤ID（用于记录是在哪个步骤被召回的）
        current_step = get_current_step_info(instance)
        current_step_id = current_step.id if current_step else None
        
        # 如果无法获取当前步骤ID，使用实例对应流程的第一个步骤
        if not current_step_id:
            from app.models.approval import ApprovalStep
            first_step = ApprovalStep.query.filter_by(
                process_id=instance.process_id,
                step_order=1
            ).first()
            current_step_id = first_step.id if first_step else None
        
        # 如果仍然无法获取步骤ID，创建一个临时记录步骤
        if not current_step_id:
            current_app.logger.error(f"无法为召回操作找到合适的步骤ID，审批实例: {instance_id}")
            return jsonify({'success': False, 'message': '召回失败：无法确定当前审批步骤'}), 500
        
        # 添加召回记录
        from app.models.approval import ApprovalRecord
        recall_record = ApprovalRecord(
            instance_id=instance_id,
            step_id=current_step_id,  # 使用当前步骤ID或第一个步骤ID
            approver_id=current_user.id,
            action='recall',
            comment=f"发起人召回审批流程。原因：{reason}" if reason else "发起人召回审批流程",
            timestamp=datetime.now()
        )
        
        db.session.add(recall_record)
        
        # 解锁对象（重要：召回后需要解锁对象，允许用户重新编辑）
        if instance.object_type == 'project':
            unlock_project(instance.object_id, current_user.id)
            current_app.logger.info(f"召回审批后已解锁项目: {instance.object_id}")
        elif instance.object_type == 'quotation':
            from app.helpers.quotation_helpers import unlock_quotation
            unlock_quotation(instance.object_id, current_user.id)
            current_app.logger.info(f"召回审批后已解锁报价单: {instance.object_id}")
        
        db.session.commit()
        
        # 记录日志
        current_app.logger.info(f"用户 {current_user.username} 召回了审批实例 {instance_id}")
        
        return jsonify({
            'success': True,
            'message': '审批流程已成功召回'
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"召回审批失败: {str(e)}")
        return jsonify({'success': False, 'message': f'召回失败: {str(e)}'}), 500


@approval_bp.route('/rollback-order/<int:order_id>', methods=['POST'])
@login_required
@admin_required
def rollback_order(order_id):
    """管理员退回已通过的订单审批"""
    try:
        # 检查权限
        if not can_rollback_order_approval(order_id, current_user.id):
            return jsonify({
                'success': False,
                'message': '权限不足或订单状态不允许退回'
            })
        
        # 获取退回原因
        data = request.get_json()
        reason = data.get('reason', '') if data else ''
        
        # 执行退回操作
        success, message = rollback_order_approval(order_id, current_user.id, reason)
        
        if success:
            return jsonify({
                'success': True,
                'message': message
            })
        else:
            return jsonify({
                'success': False,
                'message': message
            })
            
    except Exception as e:
        current_app.logger.error(f"退回订单审批失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'退回失败：{str(e)}'
        }) 


def get_tab_display_name(tab):
    """获取标签页显示名称 - 已废弃，统一使用审批列表"""
    from flask_babel import gettext as _
    return _('审批列表')


def build_approval_list_config(tab, object_type=None, status=None, pending_count=0, created_pending_count=0, pricing_order_pending_count=0, order_pending_count=0, expense_pending_count=0):
    """构建审批中心的通用列表配置"""
    from flask import url_for
    from flask_babel import gettext as _
    from flask_login import current_user
    
    # 根据标签页提供合适的筛选选项，使用安全的静态配置
    def get_filter_options_for_tab(tab_type):
        """为不同标签页提供合适的筛选选项"""
        # 基础业务类型（所有标签页都可能有的）
        base_object_types = {'project', 'purchase_order'}
        
        # 基础状态（审批流程状态）
        base_statuses = {'pending', 'approved', 'rejected'}
        
        if tab_type == 'created':
            # "我发起的"可能包含所有类型，包括批价单的草稿状态
            return {
                'object_types': {'project', 'quotation', 'customer', 'purchase_order', 'pricing_order'},
                'statuses': {'draft', 'pending', 'approved', 'rejected'}
            }
        elif tab_type == 'pending':
            # "待我审批"主要是审批中状态
            return {
                'object_types': base_object_types,
                'statuses': {'pending'}
            }
        elif tab_type == 'pricing_order':
            # "批价单审批"只有批价单类型，包含草稿状态
            return {
                'object_types': {'pricing_order'},
                'statuses': {'draft', 'pending', 'approved'}
            }
        elif tab_type == 'order':
            # "订单审批"只有订单类型
            return {
                'object_types': {'purchase_order'},
                'statuses': {'pending', 'approved'}
            }
        elif tab_type == 'all':
            # "全部审批"包含所有可能的类型和状态
            return {
                'object_types': {'project', 'quotation', 'customer', 'purchase_order', 'pricing_order'},
                'statuses': {'draft', 'pending', 'approved', 'rejected'}
            }
        else:
            # 默认配置
            return {
                'object_types': base_object_types,
                'statuses': base_statuses
            }
    
    # 获取当前标签页的筛选选项
    actual_data = get_filter_options_for_tab(tab)
    
    # 筛选配置 - 使用翻译函数
    filter_config = {
        'action_url': url_for('approval.center'),
        'form_id': 'approvalFilterForm',
        'reset_url': url_for('approval.center'),
        
        'search_field': {
            'name': 'search',
            'label': _('搜索'),
            'placeholder': _('审批编号、流程名称或业务关键词'),
            'value': '',
            'col_width': 4
        },
        
        'filter_fields': [],
        
        'search_button_text': _('搜索'),
        'reset_button_text': _('重置')
    }
    
    # 动态生成业务类型筛选选项
    object_type_options = []
    business_type_labels = {
        'project': _('项目'),
        'quotation': _('报价单'),
        'customer': _('客户'),
        'purchase_order': _('采购订单'),
        'pricing_order': _('批价单')
    }
    
    for obj_type in actual_data['object_types']:
        if obj_type in business_type_labels:
            object_type_options.append({
                'value': obj_type,
                'label': business_type_labels[obj_type],
                'translate': True
            })
    
    # 只有当实际存在业务类型数据时才添加业务类型筛选
    if object_type_options:
        filter_config['filter_fields'].append({
            'name': 'object_type',
            'label': _('业务类型'),
            'all_option_text': _('全部类型'),
            'current_value': object_type,
            'col_width': 3,
            'options': object_type_options
        })
    
    # 动态生成状态筛选选项
    status_options = []
    status_labels = {
        'draft': _('草稿'),
        'pending': _('审批中'),
        'approved': _('已通过'),
        'rejected': _('已拒绝')
    }
    
    for status_value in actual_data['statuses']:
        if status_value in status_labels:
            status_options.append({
                'value': status_value,
                'label': status_labels[status_value],
                'translate': True
            })
    
    # 只有当实际存在状态数据时才添加状态筛选
    if status_options:
        # 确定状态筛选的标签
        if tab == 'order':
            status_label = _('订单状态')
        else:
            status_label = _('审批状态')
            
        filter_config['filter_fields'].append({
            'name': 'status',
            'label': status_label,
            'all_option_text': _('全部状态'),
            'current_value': status,
            'col_width': 3,
            'options': status_options
        })
    
    # 统计卡片配置 - 使用翻译函数
    
    stats_config = {
        'cards': [
            {
                'id': 'total',
                'title': _('全部审批'),
                'icon': 'fas fa-clipboard-check',
                'value': pending_count + created_pending_count + pricing_order_pending_count + order_pending_count,
                'unit': _('项'),
                'color': 'primary',
                'clickable': True,
                'click_params': {},
                'data_key': 'total'  # 添加data_key用于AJAX更新
            },
            {
                'id': 'pending',
                'title': _('待我审批'),
                'icon': 'fas fa-hourglass-half',
                'value': pending_count,
                'unit': _('项'),
                'color': 'warning',
                'clickable': True,
                'click_params': {'tab': 'pending'},
                'data_key': 'pending'  # 添加data_key用于AJAX更新
            },
            {
                'id': 'created',
                'title': _('我发起的'),
                'icon': 'fas fa-file-export',
                'value': created_pending_count,
                'unit': _('项'),
                'color': 'info',
                'clickable': True,
                'click_params': {'tab': 'created'},
                'data_key': 'created'  # 添加data_key用于AJAX更新
            },
            {
                'id': 'pricing_order',
                'title': _('批价单审批'),
                'icon': 'fas fa-file-invoice-dollar',
                'value': pricing_order_pending_count,
                'unit': _('项'),
                'color': 'success',
                'clickable': True,
                'click_params': {'tab': 'pricing_order'},
                'data_key': 'pricing_order'  # 添加data_key用于AJAX更新
            },
            {
                'id': 'order',
                'title': _('订单审批'),
                'icon': 'fas fa-shopping-cart',
                'value': order_pending_count,
                'unit': _('项'),
                'color': 'danger',
                'clickable': True,
                'click_params': {'tab': 'order'},
                'data_key': 'order'  # 添加data_key用于AJAX更新
            }
        ]
    }
    
    # 表格配置
    table_config = {
        'ajax_target': 'approvalTableBody',
        'title': _('审批列表'),
        'icon': 'fas fa-table',
        'enhanced_striping': True,
        'infinite_scroll': True,
        'max_height': '600px',
        'columns': [
            {
                'key': 'approval_number',
                'field': 'id',  # 用于排序的字段名
                'label': _('审批编号'),
                'type': 'link',
                'url_template': '/approval/detail/{id}',
                'width': '180px',
                'render': 'render_approval_code',
                'sortable': True,
                'sort_type': 'number'
            },
            {
                'key': 'related_project',
                'field': 'project_name',  # 用于排序的字段名
                'label': _('关联项目'),
                'type': 'link',
                'url_template': '/project/view/{project_id}',
                'width': '200px',
                'render': 'render_project_link',
                'sortable': True,
                'sort_type': 'string'
            },
            {
                'key': 'process_name',
                'field': 'process_name',  # 用于排序的字段名
                'label': _('流程名称'),
                'type': 'text',
                'width': '180px',
                'sortable': True,
                'sort_type': 'string'
            },
            {
                'key': 'business_info',
                'field': 'object_type',  # 用于排序的字段名
                'label': _('关联业务'),
                'type': 'badge',
                'render': 'render_business_object_badge',
                'width': '180px',
                'sortable': True,
                'sort_type': 'string'
            },
            {
                'key': 'creator',
                'field': 'creator_name',  # 用于排序的字段名
                'label': _('提交人'),
                'type': 'badge',
                'render': 'render_owner',
                'width': '150px',
                'sortable': True,
                'sort_type': 'string'
            },
            {
                'key': 'current_approver',
                'field': 'current_approver_name',  # 用于排序的字段名
                'label': _('当前审批人'),
                'type': 'badge',
                'render': 'render_owner',
                'width': '150px',
                'sortable': True,
                'sort_type': 'string'
            },
            {
                'key': 'status',
                'field': 'status',  # 用于排序的字段名
                'label': _('状态'),
                'type': 'badge',
                'render': 'render_approval_status_badge',
                'width': '120px',
                'sortable': True,
                'sort_type': 'string'
            },
            {
                'key': 'started_at',
                'field': 'started_at',  # 用于排序的字段名
                'label': _('发起时间'),
                'type': 'date',
                'format': '%Y-%m-%d %H:%M',
                'width': '180px',
                'sortable': True,
                'sort_type': 'date'
            }
        ]
    }
    
    # 根据标签页调整列配置
    if tab == 'pricing_order':
        table_config['columns'][0] = {
            'key': 'pricing_order_number',
            'field': 'order_number',  # 用于排序的字段名
            'label': _('批价单编号'),
            'type': 'link',
            'url_template': '/pricing_order/detail/{id}',
            'width': '180px',
            'render': 'render_pricing_order_number',
            'sortable': True,
            'sort_type': 'string'
        }
        # 项目列保持不变，批价单有项目关联
    elif tab == 'order':
        table_config['columns'][0] = {
            'key': 'order_number',
            'field': 'order_number',  # 用于排序的字段名
            'label': _('订单编号'),
            'type': 'link',
            'url_template': '/inventory/order/{id}',
            'width': '180px',
            'sortable': True,
            'sort_type': 'string'
        }
        # 项目列保持不变
        # 将公司信息移到第3列（业务信息列）
        table_config['columns'][3] = {
            'key': 'company_name',
            'field': 'company_name',  # 用于排序的字段名
            'label': _('供应商/客户'),
            'type': 'text',
            'width': '180px',
            'sortable': True,
            'sort_type': 'string'
        }
    elif tab == 'expense':
        table_config['columns'][0] = {
            'key': 'expense_number',
            'field': 'expense_number',  # 用于排序的字段名
            'label': _('报销单编号'),
            'type': 'link',
            'url_template': '/expense/expense_detail/{id}',
            'width': '180px',
            'sortable': True,
            'sort_type': 'string'
        }
        # 修改第二列为报销主题
        table_config['columns'][1] = {
            'key': 'title',
            'field': 'title',  # 用于排序的字段名
            'label': _('报销主题'),
            'type': 'text',
            'width': '200px',
            'sortable': True,
            'sort_type': 'string'
        }
        # 将报销金额信息移到第3列（业务信息列）
        table_config['columns'][3] = {
            'key': 'total_amount',
            'field': 'total_amount',  # 用于排序的字段名
            'label': _('报销金额'),
            'type': 'currency',
            'width': '120px',
            'sortable': True,
            'sort_type': 'number'
        }
    
    return {
        'module_name': 'approval',
        'title': _('审批中心'),
        'ajax_mode': True,
        'stats': stats_config,
        'filter': filter_config,
        'table': table_config,
        'infinite_scroll': {
            'enabled': True,
            'per_page': 20,
            'threshold': 200
        }
    }



def create_empty_pagination(per_page=20):
    """创建空分页对象的工具函数"""
    class EmptyPagination:
        def __init__(self, per_page):
            self.items = []
            self.total = 0
            self.pages = 0
            self.has_next = False
            self.has_prev = False
            self.page = 1
            self.per_page = per_page
    
    return EmptyPagination(per_page)


@approval_bp.route('/center_ajax')
@login_required
def center_ajax():
    """审批中心AJAX端点 - 支持通用数据列表组件"""
    try:
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        offset = request.args.get('offset', 0, type=int) 
        limit = request.args.get('limit', 20, type=int)
        object_type = request.args.get('object_type')
        status = request.args.get('status')
        search = request.args.get('search', '').strip()
        tab = request.args.get('tab', 'created')
        
        # 🔥 新增：获取排序参数
        sort_field = request.args.get('sort_field')
        sort_direction = request.args.get('sort_direction', 'asc')
        current_app.logger.info(f"收到排序参数: field={sort_field}, direction={sort_direction}, tab={tab}")
        
        # 计算分页参数
        if offset > 0:
            page = (offset // limit) + 1
            per_page = limit
        
        # 获取审批数据（复用原有逻辑）
        if tab == 'pending':
            # 对于待我审批标签页，只显示待审批状态的记录
            # 如果筛选其他状态，返回空结果
            if status and status not in ['', 'pending']:
                # 为非pending状态返回空结果
                approvals = create_empty_pagination(per_page)
            else:
                # 默认或筛选"审批中"，返回待审批列表
                try:
                    approvals = get_user_pending_approvals(
                        user_id=current_user.id,
                        object_type=object_type,
                        page=page,
                        per_page=per_page
                    )
                except Exception as e:
                    current_app.logger.error(f"get_user_pending_approvals调用失败: {str(e)}")
                    approvals = create_empty_pagination(per_page)
        elif tab == 'pricing_order':
            from app.helpers.approval_helpers import get_user_pricing_order_approvals
            try:
                approvals = get_user_pricing_order_approvals(
                    user_id=current_user.id,
                    status=status,
                    page=page,
                    per_page=per_page
                )
            except Exception as e:
                current_app.logger.error(f"get_user_pricing_order_approvals调用失败: {str(e)}")
                approvals = create_empty_pagination(per_page)
        elif tab == 'order':
            from app.helpers.approval_helpers import get_user_order_approvals
            try:
                approvals = get_user_order_approvals(
                    user_id=current_user.id,
                    status_filter=status,
                    page=page,
                    per_page=per_page
                )
            except Exception as e:
                current_app.logger.error(f"get_user_order_approvals调用失败: {str(e)}")
                approvals = create_empty_pagination(per_page)
        elif tab == 'expense':
            # 报销单审批
            try:
                approvals = get_user_created_approvals(
                    user_id=current_user.id,
                    object_type='expense',
                    status=status,
                    page=page,
                    per_page=per_page
                )
            except Exception as e:
                current_app.logger.error(f"get_expense_approvals调用失败: {str(e)}")
                approvals = create_empty_pagination(per_page)
        elif tab == 'department':
            from app.helpers.approval_helpers import get_user_department_approvals
            try:
                approvals = get_user_department_approvals(
                    user_id=current_user.id,
                    object_type=object_type,
                    status=status,
                    page=page,
                    per_page=per_page
                )
            except Exception as e:
                current_app.logger.error(f"get_user_department_approvals调用失败: {str(e)}")
                approvals = create_empty_pagination(per_page)
        elif tab == 'all' and has_permission('approval_management', 'all'):
            # 全部审批 - 简化状态处理
            status_param = status  # 直接使用字符串状态
            
            try:
                approvals = get_all_approvals(
                    object_type=object_type,
                    status=status_param,
                    page=page,
                    per_page=per_page
                )
            except Exception as e:
                current_app.logger.error(f"get_all_approvals调用失败: {str(e)}")
                approvals = create_empty_pagination(per_page)
        else:
            # 我发起的 - 特殊处理草稿状态
            if status == 'draft':
                # 草稿状态只存在于批价单中，强制设置object_type为pricing_order
                object_type = 'pricing_order'
                current_app.logger.info(f"草稿状态筛选，强制设置object_type=pricing_order")
            
            status_param = status  # 直接使用字符串状态，让get_user_created_approvals内部处理转换
            
            current_app.logger.info(f"调用get_user_created_approvals，参数: user_id={current_user.id}, object_type={object_type}, status={status_param}")
            
            try:
                approvals = get_user_created_approvals(
                    user_id=current_user.id,
                    object_type=object_type,
                    status=status_param,
                    page=page,
                    per_page=per_page
                )
                current_app.logger.info(f"get_user_created_approvals调用成功，结果数量: {len(approvals.items) if hasattr(approvals, 'items') else 'N/A'}")
            except Exception as e:
                current_app.logger.error(f"get_user_created_approvals调用失败: {str(e)}")
                import traceback
                current_app.logger.error(traceback.format_exc())
                
                # 返回空结果而不是抛出异常
                approvals = create_empty_pagination(per_page)
        
        # 应用搜索过滤（简单实现）
        items = approvals.items if hasattr(approvals, 'items') else approvals
        if search:
            # 这里可以实现搜索逻辑
            pass
        
        # 渲染行模板（需要创建）
        html_rows = []
        current_app.logger.info(f"开始渲染 {len(items)} 行数据，标签页: {tab}")
        
        for i, item in enumerate(items):
            try:
                # 根据标签页渲染不同的行内容
                if tab == 'pricing_order':
                    # 批价单行渲染
                    html_row = render_pricing_order_row(item)
                elif tab == 'order':
                    # 订单行渲染
                    html_row = render_order_row(item)
                elif tab == 'expense':
                    # 报销单行渲染
                    html_row = render_expense_row(item)
                else:
                    # 通用审批行渲染
                    html_row = render_approval_row(item, tab)
                
                if html_row:
                    html_rows.append(html_row)
                    current_app.logger.debug(f"成功渲染第 {i+1} 行数据")
                else:
                    current_app.logger.warning(f"第 {i+1} 行数据渲染结果为空")
                    
            except Exception as e:
                current_app.logger.error(f"渲染第 {i+1} 行数据失败: {str(e)}")
                # 添加一个错误行，避免破坏表格结构
                error_row = f'<tr><td colspan="8" class="text-center text-danger">第{i+1}行渲染失败: {str(e)}</td></tr>'
                html_rows.append(error_row)
        
        current_app.logger.info(f"完成渲染，生成了 {len(html_rows)} 行HTML")
        
        # 计算统计数据
        from app.helpers.approval_helpers import get_pending_approval_count, get_pending_created_count, get_pricing_order_pending_count, get_order_pending_count
        
        # 获取各项统计数据
        pending_count = get_pending_approval_count(current_user.id)
        created_count = get_pending_created_count(current_user.id)
        pricing_order_count = get_pricing_order_pending_count(current_user.id)
        order_count = get_order_pending_count(current_user.id)
        
        # 添加报销单统计（暂时使用created_count的一部分，后续可以独立统计）
        expense_count = 0  # 报销单待审批数量，可以后续实现专门的统计函数
        
        statistics = {
            'total': pending_count + created_count + pricing_order_count + order_count + expense_count,  # 统计总数
            'pending': pending_count,
            'created': created_count,
            'pricing_order': pricing_order_count,
            'order': order_count,
            'expense': expense_count
        }
        
        # 确保HTML输出干净
        html_output = ''.join(html_rows) if html_rows else '<tr><td colspan="8" class="text-center py-4">暂无数据</td></tr>'
        
        # 🔍 调试：记录HTML输出信息
        current_app.logger.info(f"最终HTML输出长度: {len(html_output)}")
        current_app.logger.info(f"HTML行数统计: 生成{len(html_rows)}行，总长度{len(html_output)}字符")
        if html_rows:
            current_app.logger.info(f"第一行HTML: {html_rows[0][:200]}...")
            if len(html_rows) > 1:
                current_app.logger.info(f"第二行HTML: {html_rows[1][:200]}...")
        
        return jsonify({
            'success': True,
            'html': html_output,
            'total_count': approvals.total if hasattr(approvals, 'total') else len(items),
            'loaded_count': len(items),
            'has_more': approvals.has_next if hasattr(approvals, 'has_next') else False,
            'statistics': statistics
        })
    
    except Exception as e:
        current_app.logger.error(f"审批中心AJAX加载失败: {str(e)}")
        import traceback
        current_app.logger.error(traceback.format_exc())
        return jsonify({
            'success': False,
            'message': f'数据加载失败: {str(e)}',
            'html': '<tr><td colspan="8" class="text-center text-danger py-4"><i class="fas fa-exclamation-triangle"></i> 数据加载失败，请刷新页面重试</td></tr>'
        }), 500


def render_approval_row(item, tab='created'):
    """渲染审批行HTML"""
    try:
        from app.helpers.approval_helpers import get_current_step_info, get_last_approver
        
        # 获取当前步骤和审批人信息
        current_step = None
        last_approver = None
        current_approver = None
        
        try:
            # 使用实例的get_current_step_info方法获取当前步骤
            current_step = item.get_current_step_info()
        except:
            current_step = None
        
        try:
            # 🔥 修复：兼容多种状态表示方式（数据库枚举值vs Python枚举对象）
            def is_completed_status(status):
                """检查审批是否已完成（兼容字符串和枚举对象）"""
                if isinstance(status, str):
                    # 数据库直接返回的字符串（通常是大写）
                    return status.upper() in ['APPROVED', 'REJECTED']
                elif hasattr(status, 'name'):
                    # SQLAlchemy枚举对象的name属性
                    return status.name in ['APPROVED', 'REJECTED']  
                elif hasattr(status, 'value'):
                    # SQLAlchemy枚举对象的value属性（小写）
                    return status.value in ['approved', 'rejected']
                return False
            
            if is_completed_status(item.status):
                last_approver = get_last_approver(item)
        except:
            last_approver = None
        
        # 🔥 修复：使用get_step_actual_approver来确定实际审批人
        if last_approver:
            current_approver = last_approver
        elif current_step:
            from app.helpers.approval_helpers import get_step_actual_approver
            try:
                current_approver = get_step_actual_approver(current_step, item)
            except:
                current_approver = None
    except Exception as e:
        current_app.logger.error(f"render_approval_row 严重错误: {e}")
        # 返回基本的错误行但不破坏表格结构
        return f'<tr><td colspan="8" class="text-center text-muted">数据渲染出错</td></tr>'
    
    # 状态徽章 - 使用映射的多语言显示
    from app.utils.dictionary_helpers import approval_status_label
    from app.utils.i18n import get_current_language
    
    try:
        lang_code = get_current_language()
    except:
        lang_code = 'zh'
    
    status_key = item.status.name.lower() if hasattr(item.status, 'name') else str(item.status).lower()
    status_display = approval_status_label(status_key, lang_code)
    status_badge = f'<span class="badge badge-pill badge-transparent approval-status-{status_key}">{status_display}</span>'
    
    # 审批编号 - 统一使用APV格式
    try:
        approval_id = int(item.id) if item.id else 0
        approval_code = f'<span class="badge badge-pill badge-transparent approval-code-badge">APV-{approval_id:04d}</span>'
    except (ValueError, TypeError):
        approval_code = f'<span class="badge badge-pill badge-transparent approval-code-badge">APV-{item.id}</span>'
    
    # 业务对象信息
    business_info = ""
    try:
        business_info = get_business_object_display(item)
    except Exception as e:
        current_app.logger.warning(f"获取业务对象信息失败: {e}")
        business_info = f'<span class="badge badge-pill badge-transparent">对象信息获取失败</span>'
    
    # 关联项目信息
    related_project = ""
    try:
        related_project = get_related_project_display(item)
    except Exception as e:
        current_app.logger.warning(f"获取关联项目信息失败: {e}")
        related_project = '<span class="text-muted">-</span>'
    
    # 创建人和当前审批人 - 使用render_owner逻辑生成徽章
    def render_user_badge(user):
        """生成用户徽章HTML，匹配render_owner宏的逻辑"""
        if not user:
            return '<span class="badge badge-user regular">未知</span>'
        
        # 获取显示名称
        display_name = user.real_name if hasattr(user, 'real_name') and user.real_name else (user.username if hasattr(user, 'username') else '未知')
        
        # 判断是否为厂商用户
        if hasattr(user, 'is_vendor_user') and callable(user.is_vendor_user):
            try:
                if user.is_vendor_user():
                    return f'<span class="badge badge-user vendor rounded-pill">{display_name}</span>'
                else:
                    return f'<span class="badge badge-user regular">{display_name}</span>'
            except:
                return f'<span class="badge badge-user regular">{display_name}</span>'
        else:
            return f'<span class="badge badge-user regular">{display_name}</span>'
    
    creator_badge = render_user_badge(item.creator)
    approver_badge = render_user_badge(current_approver) if current_approver else '<span class="badge badge-user regular">待分配</span>'
    
    # 发起时间 - 安全的日期格式化
    started_time = ''
    if item.started_at:
        try:
            if isinstance(item.started_at, str):
                # 如果是字符串，尝试解析
                from datetime import datetime
                dt = datetime.fromisoformat(item.started_at.replace('Z', '+00:00'))
                started_time = dt.strftime('%Y-%m-%d %H:%M')
            else:
                # 如果是datetime对象
                started_time = item.started_at.strftime('%Y-%m-%d %H:%M')
        except (ValueError, AttributeError) as e:
            current_app.logger.warning(f"日期格式化失败: {item.started_at}, 错误: {e}")
            started_time = str(item.started_at) if item.started_at else ''
    
    # 🔥 修复：使用业务对象的详情页URL而不是审批详情页
    from app.helpers.approval_helpers import get_approval_object_url
    try:
        object_url = get_approval_object_url(item)
    except Exception as e:
        current_app.logger.warning(f"获取业务对象URL失败: {e}")
        object_url = f"/approval/detail/{item.id}"  # 降级处理
    
    # 准备排序用的数据值，确保HTML安全
    from html import escape
    sort_values = {
        'id': item.id or 0,
        'project_name': '',
        'process_name': escape(item.process.name if item.process else ''),
        'object_type': escape(item.object_type or ''),
        'creator_name': escape(item.creator.real_name if item.creator and hasattr(item.creator, 'real_name') and item.creator.real_name else (item.creator.username if item.creator else '')),
        'current_approver_name': escape(current_approver.real_name if current_approver and hasattr(current_approver, 'real_name') and current_approver.real_name else (current_approver.username if current_approver else '')),
        'status': escape(status_key),
        'started_at': escape(item.started_at.isoformat() if item.started_at else '')
    }
    
    # 获取项目名称用于排序
    try:
        if item.object_type == 'project' and item.object_id:
            from app.helpers.approval_helpers import get_project_by_id
            project = get_project_by_id(item.object_id)
            sort_values['project_name'] = escape(project.project_name if project and hasattr(project, 'project_name') else '')
        elif item.object_type == 'quotation' and item.object_id:
            from app.helpers.approval_helpers import get_quotation_by_id
            quotation = get_quotation_by_id(item.object_id)
            sort_values['project_name'] = escape(quotation.project.project_name if quotation and quotation.project and hasattr(quotation.project, 'project_name') else '')
        elif item.object_type == 'pricing_order' and item.object_id:
            from app.models.pricing_order import PricingOrder
            pricing_order = PricingOrder.query.get(item.object_id)
            sort_values['project_name'] = escape(pricing_order.project.project_name if pricing_order and pricing_order.project and hasattr(pricing_order.project, 'project_name') else '')
    except Exception as e:
        current_app.logger.warning(f"获取项目名称用于排序失败: {e}")

    # 恢复正常的HTML渲染，包含徽章和链接
    try:
        # 安全的ID格式化
        item_id_int = int(item.id) if item.id else 0
        approval_code = f"APV-{item_id_int:04d}"
    except (ValueError, TypeError):
        approval_code = f"APV-{str(item.id)}"
    
    html_row = (
        f'<tr>'
        f'<td data-sort-value="{sort_values["id"]}"><a href="{object_url}" class="text-decoration-none">{approval_code}</a></td>'
        f'<td data-sort-value="{sort_values["project_name"]}">{related_project}</td>'
        f'<td data-sort-value="{sort_values["process_name"]}">{escape(item.process.name if item.process else "未知流程")}</td>'
        f'<td data-sort-value="{sort_values["object_type"]}">{business_info}</td>'
        f'<td data-sort-value="{sort_values["creator_name"]}">{creator_badge}</td>'
        f'<td data-sort-value="{sort_values["current_approver_name"]}">{approver_badge}</td>'
        f'<td data-sort-value="{sort_values["status"]}">{status_badge}</td>'
        f'<td data-sort-value="{sort_values["started_at"]}">{started_time}</td>'
        f'</tr>'
    )
    
    # 🔍 调试：检查单行HTML长度
    current_app.logger.debug(f"生成单行HTML长度: {len(html_row)}")
    return html_row


def render_pricing_order_row(item):
    """渲染批价单行HTML"""
    # 这里实现批价单特定的行渲染逻辑
    return render_approval_row(item, 'pricing_order')


def render_order_row(item):
    """渲染订单行HTML"""
    # 这里实现订单特定的行渲染逻辑  
    return render_approval_row(item, 'order')

def render_expense_row(item):
    """渲染报销单行HTML"""
    # 这里实现报销单特定的行渲染逻辑  
    return render_approval_row(item, 'expense')


def get_related_project_display(approval_item):
    """获取审批项关联项目的显示信息"""
    project = None
    project_id = None
    
    try:
        # 直接是项目审批
        if approval_item.object_type == 'project' and approval_item.object_id:
            from app.helpers.approval_helpers import get_project_by_id
            project = get_project_by_id(approval_item.object_id)
            project_id = approval_item.object_id
            
        # 报价单审批，获取关联项目
        elif approval_item.object_type == 'quotation' and approval_item.object_id:
            from app.helpers.approval_helpers import get_quotation_by_id
            quotation = get_quotation_by_id(approval_item.object_id)
            if quotation and quotation.project:
                project = quotation.project
                project_id = quotation.project.id
                
        # 批价单审批，获取关联项目
        elif approval_item.object_type == 'pricing_order' and approval_item.object_id:
            from app.models.pricing_order import PricingOrder
            pricing_order = PricingOrder.query.get(approval_item.object_id)
            if pricing_order and pricing_order.project:
                project = pricing_order.project
                project_id = pricing_order.project.id
                
        # 订单审批，获取关联项目（如果有的话）
        elif approval_item.object_type == 'purchase_order' and approval_item.object_id:
            from app.models.inventory import PurchaseOrder
            purchase_order = PurchaseOrder.query.get(approval_item.object_id)
            # 订单可能没有直接关联项目，这种情况显示为空
            
        # 如果找到项目，返回项目链接
        if project and project_id:
            from flask_babel import gettext as _
            
            project_name = project.project_name if hasattr(project, 'project_name') and project.project_name else _('未命名项目')
            
            # 使用项目名称，如果太长则截断
            display_text = project_name[:20] + '...' if len(project_name) > 20 else project_name
            
            return f'<a href="/project/view/{project_id}" class="text-decoration-none" title="{project_name}">{display_text}</a>'
            
    except Exception as e:
        current_app.logger.warning(f"获取关联项目失败: {str(e)}")
    
    # 没有关联项目或获取失败
    return '<span class="text-muted">-</span>'


def get_business_object_display(approval_item):
    """获取业务对象类型显示信息 - 显示业务模块类型而非具体内容"""
    from flask_babel import gettext as _
    
    # 业务对象类型的多语言显示名称和样式映射
    business_type_config = {
        'project': {
            'display': _('项目'),
            'icon': 'fas fa-project-diagram',
            'class': 'business-type-project'
        },
        'quotation': {
            'display': _('报价单'),
            'icon': 'fas fa-file-invoice',
            'class': 'business-type-quotation'
        },
        'customer': {
            'display': _('客户'),
            'icon': 'fas fa-building',
            'class': 'business-type-customer'
        },
        'purchase_order': {
            'display': _('采购订单'),
            'icon': 'fas fa-shopping-cart',
            'class': 'business-type-order'
        },
        'pricing_order': {
            'display': _('批价单'),
            'icon': 'fas fa-file-invoice-dollar',
            'class': 'business-type-pricing'
        },
        'order': {
            'display': _('订单'),
            'icon': 'fas fa-receipt',
            'class': 'business-type-order'
        },
        'inventory': {
            'display': _('库存'),
            'icon': 'fas fa-warehouse',
            'class': 'business-type-inventory'
        },
        'settlement': {
            'display': _('结算单'),
            'icon': 'fas fa-calculator',
            'class': 'business-type-settlement'
        },
        'expense': {
            'display': _('报销单'),
            'icon': 'fas fa-receipt',
            'class': 'business-type-expense'
        }
    }
    
    # 获取业务类型配置
    object_type = approval_item.object_type or 'unknown'
    type_config = business_type_config.get(object_type)
    
    if type_config:
        # 使用配置的显示名称、图标和样式
        display_name = type_config['display']
        icon = type_config['icon']
        css_class = type_config['class']
        
        return f'<span class="badge badge-pill badge-transparent {css_class}"><i class="{icon} me-1"></i>{display_name}</span>'
    else:
        # 未知类型的后备显示
        display_name = object_type.replace('_', ' ').title() if object_type != 'unknown' else _("未知类型")
        return f'<span class="badge badge-pill badge-transparent business-type-unknown"><i class="fas fa-question-circle me-1"></i>{display_name}</span>'
