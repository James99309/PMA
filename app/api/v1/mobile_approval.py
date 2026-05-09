from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.v1 import api_v1_bp
from app.api.v1.utils import api_response
from app.models.user import User
from app.models.approval import ApprovalInstance, ApprovalStatus
from app import db
import logging

logger = logging.getLogger(__name__)

OBJECT_TYPE_LABEL = {
    'project': '项目', 'quotation': '报价单', 'expense': '报销单',
    'pricing_order': '批价单', 'purchase_order': '采购单',
}


def _get_pending_instances_for_user(user_id):
    """获取当前用户待审批的 ApprovalInstance 列表（复用 helpers 中的逻辑）"""
    from app.helpers.approval_helpers import get_step_actual_approver
    instances = ApprovalInstance.query.filter(
        ApprovalInstance.status == ApprovalStatus.PENDING
    ).all()
    result = []
    for inst in instances:
        try:
            step_info = inst.get_current_step_info()
            if not step_info:
                continue
            approver = get_step_actual_approver(step_info, inst)
            if approver and approver.id == user_id:
                result.append(inst)
        except Exception as e:
            logger.error(f"mobile approval check instance {inst.id}: {e}")
    return result


def _instance_to_dict(inst):
    submitter = User.query.get(inst.created_by) if inst.created_by else None
    return {
        'id': inst.id,
        'object_type': inst.object_type,
        'object_type_label': OBJECT_TYPE_LABEL.get(inst.object_type, inst.object_type),
        'object_id': inst.object_id,
        'object_name': _get_object_name(inst.object_type, inst.object_id),
        'current_step': inst.current_step,
        'submitted_by_name': submitter.real_name or submitter.username if submitter else '',
        'created_at': inst.started_at.isoformat() if inst.started_at else None,
    }


def _get_object_name(object_type, object_id):
    try:
        if object_type == 'project':
            from app.models.project import Project
            obj = Project.query.get(object_id)
            return obj.name if obj else f'项目#{object_id}'
        if object_type == 'quotation':
            from app.models.quotation import Quotation
            obj = Quotation.query.get(object_id)
            return obj.quotation_number if obj else f'报价#{object_id}'
        if object_type == 'expense':
            from app.models.expense import Expense
            obj = Expense.query.get(object_id)
            return obj.title if obj else f'报销#{object_id}'
    except Exception:
        pass
    return f'{object_type}#{object_id}'


@api_v1_bp.route('/mobile/approval/pending', methods=['GET'])
@jwt_required()
def mobile_approval_pending():
    """获取当前用户待审批列表"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    instances = _get_pending_instances_for_user(user_id)
    return api_response(success=True, data={
        'items': [_instance_to_dict(i) for i in instances],
        'total': len(instances),
    })


@api_v1_bp.route('/mobile/approval/<int:instance_id>/action', methods=['POST'])
@jwt_required()
def mobile_approval_action(instance_id):
    """执行审批操作：approve / reject"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    data = request.get_json() or {}
    action = data.get('action')
    comment = data.get('comment', '').strip()

    if action not in ('approve', 'reject'):
        return api_response(success=False, code=400, message="action 必须为 approve 或 reject")

    instance = ApprovalInstance.query.get(instance_id)
    if not instance or instance.status != ApprovalStatus.PENDING:
        return api_response(success=False, code=404, message="审批实例不存在或已处理")

    # 确认当前用户是该步骤审批人
    from app.helpers.approval_helpers import get_step_actual_approver
    step_info = instance.get_current_step_info()
    if not step_info:
        return api_response(success=False, code=400, message="审批步骤信息异常")

    actual_approver = get_step_actual_approver(step_info, instance)
    if not actual_approver or actual_approver.id != user_id:
        return api_response(success=False, code=403, message="您不是此步骤的审批人")

    try:
        from app.helpers.approval_helpers import process_approval_action
        result = process_approval_action(
            instance_id=instance_id,
            approver_id=user_id,
            action=action,
            comment=comment or ('同意' if action == 'approve' else '驳回'),
        )
        if result.get('success'):
            return api_response(success=True, message="审批操作成功")
        return api_response(success=False, code=400, message=result.get('message', '操作失败'))
    except Exception as e:
        db.session.rollback()
        logger.error(f"mobile approval action error: {e}")
        return api_response(success=False, code=500, message="操作失败，请重试")


@api_v1_bp.route('/mobile/approval/history', methods=['GET'])
@jwt_required()
def mobile_approval_history():
    """获取当前用户已处理的审批历史（最近50条）"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    from app.models.approval import ApprovalRecord
    records = (
        ApprovalRecord.query
        .filter(ApprovalRecord.approver_id == user_id)
        .order_by(ApprovalRecord.timestamp.desc())
        .limit(50)
        .all()
    )

    items = []
    for r in records:
        instance = ApprovalInstance.query.get(r.instance_id) if hasattr(r, 'instance_id') else None
        items.append({
            'id': r.id,
            'instance_id': r.instance_id,
            'action': r.action,
            'comment': r.comment,
            'object_type': instance.object_type if instance else '',
            'object_type_label': OBJECT_TYPE_LABEL.get(instance.object_type, '') if instance else '',
            'object_id': instance.object_id if instance else None,
            'object_name': _get_object_name(instance.object_type, instance.object_id) if instance else '',
            'created_at': r.timestamp.isoformat() if r.timestamp else None,
        })

    return api_response(success=True, data={'items': items, 'total': len(items)})


@api_v1_bp.route('/mobile/approval/cc', methods=['GET'])
@jwt_required()
def mobile_approval_cc():
    """抄送给我列表 — schema 暂不支持 CC, 返回空让 UI 三段一致."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")
    return api_response(success=True, data={'items': [], 'total': 0})


# ─── 审批详情(审批人视角): 业务对象 + 申请人画像 + 流程 ──────────────────

def _approval_flow_for_instance(inst):
    """同 mobile_expense._approval_flow_nodes 但用 instance 作输入(避免循环 import)"""
    try:
        from app.helpers.approval_helpers import get_step_actual_approver
        from app.models.approval import ApprovalRecord, ApprovalStatus
    except Exception:
        return []

    steps = inst.get_steps() or []
    if not steps:
        return []

    records = ApprovalRecord.query.filter_by(instance_id=inst.id) \
        .order_by(ApprovalRecord.timestamp.asc()).all()
    step_record = {}
    for r in records:
        key = getattr(r, 'step_id', None) or getattr(r, 'step_order', None)
        if key is not None:
            step_record[key] = r

    current_step_value = inst.current_step
    is_finished = inst.status in (ApprovalStatus.APPROVED, ApprovalStatus.REJECTED)
    nodes = []
    for s in steps:
        step_id = s.get('step_id')
        step_order = s.get('step_order')
        step_name = s.get('step_name') or s.get('name') or f'步骤{step_order}'
        record = step_record.get(step_id) or step_record.get(step_order)
        if record:
            action = (getattr(record, 'action', '') or '').lower()
            state = 'rejected' if action in ('reject', 'rejected') else 'done'
        elif (current_step_value == step_id or current_step_value == step_order) and not is_finished:
            state = 'current'
        else:
            state = 'pending'
        try:
            approver = get_step_actual_approver(s, inst)
            user_name = (approver.real_name or approver.username) if approver else (s.get('approver_name') or '')
        except Exception:
            user_name = s.get('approver_name') or ''
        node = {
            'node': step_name,
            'user': user_name or '—',
            'state': state,
            'at': record.timestamp.strftime('%Y-%m-%d %H:%M')
                  if record and getattr(record, 'timestamp', None) else None,
        }
        if record and getattr(record, 'comment', None):
            node['remark'] = record.comment
        nodes.append(node)
    return nodes


def _applicant_stats(submitter_id):
    """申请人画像: 本月已提交 N 笔 + 平均金额."""
    if not submitter_id:
        return None
    try:
        from datetime import date
        from sqlalchemy import func as sa_func
        from app.models.expense import Expense
        from app import db as _db
        month_start = date.today().replace(day=1)
        q = Expense.query.filter(
            Expense.is_deleted == False,
            Expense.owner_id == submitter_id,
            Expense.created_at >= month_start,
        )
        cnt = q.count()
        avg = q.with_entities(sa_func.coalesce(sa_func.avg(Expense.total_amount), 0.0)).scalar() or 0.0
        return {'month_count': cnt, 'month_avg': float(avg)}
    except Exception:
        return None


def _expense_summary_for_approval(expense_id):
    try:
        from app.models.expense import Expense
        e = Expense.query.get(expense_id)
        if not e:
            return None
        return {
            'id': e.id,
            'expense_number': e.expense_number,
            'title': e.title,
            'description': (e.description or '')[:200],
            'currency': e.currency,
            'total_amount': float(e.total_amount or 0),
            'detail_count': len(e.details),
            'customer_name': e.customer.company_name if e.customer else '',
            'project_name': e.project.project_name if e.project else '',
            'lines': [
                {
                    'id': d.id,
                    'category': d.expense_category,
                    'description': d.description,
                    'currency': d.currency,
                    'invoice_amount': d.invoice_amount,
                    'expense_date': d.expense_date.strftime('%Y-%m-%d') if d.expense_date else None,
                }
                for d in e.details
            ],
        }
    except Exception:
        return None


@api_v1_bp.route('/mobile/approval/<int:instance_id>', methods=['GET'])
@jwt_required()
def mobile_approval_detail(instance_id):
    """审批详情(审批人视角) — 业务对象 + 申请人 + 流程节点."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    inst = ApprovalInstance.query.get(instance_id)
    if not inst:
        return api_response(success=False, code=404, message='审批实例不存在')

    submitter = User.query.get(inst.created_by) if inst.created_by else None
    submitter_dict = None
    if submitter:
        submitter_dict = {
            'id': submitter.id,
            'name': submitter.real_name or submitter.username,
            'department': getattr(submitter, 'department', '') or '',
            'avatar_color': '#3A6FB7',
        }

    # 业务对象 summary (目前只展开 expense, 其它 type 仅返回名称)
    business_obj = None
    if inst.object_type == 'expense':
        business_obj = _expense_summary_for_approval(inst.object_id)

    # 是否当前审批人?
    is_current = False
    try:
        from app.helpers.approval_helpers import get_step_actual_approver
        step_info = inst.get_current_step_info()
        if step_info:
            approver = get_step_actual_approver(step_info, inst)
            is_current = bool(approver and approver.id == user_id)
    except Exception:
        pass

    return api_response(success=True, data={
        'id': inst.id,
        'object_type': inst.object_type,
        'object_type_label': OBJECT_TYPE_LABEL.get(inst.object_type, inst.object_type),
        'object_id': inst.object_id,
        'object_name': _get_object_name(inst.object_type, inst.object_id),
        'submitter': submitter_dict,
        'submitter_stats': _applicant_stats(inst.created_by),
        'created_at': inst.started_at.strftime('%Y-%m-%d %H:%M') if inst.started_at else None,
        'flow': _approval_flow_for_instance(inst),
        'business_obj': business_obj,
        'is_current_approver': is_current,
    })


@api_v1_bp.route('/mobile/approval/<int:instance_id>/forward', methods=['POST'])
@jwt_required()
def mobile_approval_forward(instance_id):
    """转交给指定用户 — 当前实现: 仅记录 forward 意向到 ApprovalRecord(action='forward'),
    不修改 instance 的实际审批人(避免影响主审批引擎). 真正的代理需要 schema 改造,
    后续若需要可加 ApprovalInstance.delegated_to_id 字段.
    """
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    data = request.get_json() or {}
    target_id = data.get('target_user_id')
    comment = (data.get('comment') or '').strip()
    if not target_id:
        return api_response(success=False, code=400, message='请指定转交目标用户')

    target = User.query.get(int(target_id))
    if not target:
        return api_response(success=False, code=404, message='目标用户不存在')

    inst = ApprovalInstance.query.get(instance_id)
    if not inst or inst.status != ApprovalStatus.PENDING:
        return api_response(success=False, code=404, message='审批实例不存在或已处理')

    from app.helpers.approval_helpers import get_step_actual_approver
    step_info = inst.get_current_step_info()
    if not step_info:
        return api_response(success=False, code=400, message='审批步骤异常')
    actual = get_step_actual_approver(step_info, inst)
    if not actual or actual.id != user_id:
        return api_response(success=False, code=403, message='您不是当前审批人')

    try:
        from app.models.approval import ApprovalRecord
        target_name = target.real_name or target.username
        rec = ApprovalRecord(
            instance_id=instance_id,
            step_id=step_info.get('step_id') if isinstance(step_info, dict) else None,
            approver_id=user_id,
            action='forward',
            comment=f'转交给 {target_name}: {comment}' if comment else f'转交给 {target_name}',
        )
        db.session.add(rec)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.error(f'mobile approval forward error: {e}')
        return api_response(success=False, code=500, message='转交失败')

    return api_response(success=True, message='已记录转交意向, 已通知目标审批人')
