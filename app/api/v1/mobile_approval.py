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
    submitter = User.query.get(inst.submitted_by) if inst.submitted_by else None
    return {
        'id': inst.id,
        'object_type': inst.object_type,
        'object_type_label': OBJECT_TYPE_LABEL.get(inst.object_type, inst.object_type),
        'object_id': inst.object_id,
        'object_name': _get_object_name(inst.object_type, inst.object_id),
        'current_step': inst.current_step,
        'submitted_by_name': submitter.real_name or submitter.username if submitter else '',
        'created_at': inst.created_at.isoformat() if inst.created_at else None,
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
        .order_by(ApprovalRecord.created_at.desc())
        .limit(50)
        .all()
    )

    items = []
    for r in records:
        instance = ApprovalInstance.query.get(r.approval_instance_id) if hasattr(r, 'approval_instance_id') else None
        items.append({
            'id': r.id,
            'action': r.action,
            'comment': r.comment,
            'object_type': instance.object_type if instance else '',
            'object_type_label': OBJECT_TYPE_LABEL.get(instance.object_type, '') if instance else '',
            'object_id': instance.object_id if instance else None,
            'object_name': _get_object_name(instance.object_type, instance.object_id) if instance else '',
            'created_at': r.created_at.isoformat() if r.created_at else None,
        })

    return api_response(success=True, data={'items': items, 'total': len(items)})
