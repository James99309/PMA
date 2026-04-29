from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.v1 import api_v1_bp
from app.api.v1.utils import api_response
from app.models.project import Project
from app.models.user import User
from app.utils.access_control import get_viewable_data
from app import db
import logging

logger = logging.getLogger(__name__)

# 实际使用的阶段值（来自 dictionary_helpers.py）
STAGE_LABELS = {
    'discover':   '发现',
    'embed':      '植入',
    'pre_tender': '标前',
    'tendering':  '标中',
    'awarded':    '中标',
    'quoted':     '批价',
    'signed':     '签约',
    'lost':       '失败',
    'paused':     '搁置',
}

ACTIVITY_LABELS = {
    'highly_active': '非常活跃',
    'active':        '活跃',
    'normal':        '正常',
    'low_active':    '低活跃',
    'inactive':      '不活跃',
    'frozen':        '冻结',
}

AUTH_STATUS_LABELS = {
    None:       '未申请',
    'pending':  '申请中',
    'rejected': '已拒绝',
    'approved': '已授权',
}


def _project_summary(p):
    amount = p.quotation_customer or 0
    return {
        'id': p.id,
        'name': p.project_name,
        'current_stage': p.current_stage,
        'stage_label': STAGE_LABELS.get(p.current_stage, p.current_stage or ''),
        'status': p.status,
        'amount': round(amount / 10000, 2) if amount else 0,
        'currency': getattr(p, 'quotation_currency', 'CNY') or 'CNY',
        'owner_name': p.owner.real_name or p.owner.username if p.owner else '',
        'updated_at': p.updated_at.isoformat() if p.updated_at else None,
    }


def _project_detail(p):
    d = _project_summary(p)
    d.update({
        # 阶段与活跃度
        'stage_description': p.stage_description,
        'activity_status': p.activity_status,
        'activity_label': ACTIVITY_LABELS.get(p.activity_status, p.activity_status or ''),
        # 授权信息
        'authorization_status': p.authorization_status,
        'authorization_status_label': AUTH_STATUS_LABELS.get(p.authorization_status, ''),
        'authorization_code': p.authorization_code,
        # 项目基本信息
        'project_type': p.project_type,
        'end_user': p.end_user,
        'dealer': p.dealer,
        'system_integrator': p.system_integrator,
        'delivery_forecast': p.delivery_forecast.isoformat() if p.delivery_forecast else None,
        # 负责人 ID（用于权限判断）
        'owner_id': p.owner_id,
        'vendor_sales_manager_id': getattr(p, 'vendor_sales_manager_id', None),
        # 时间
        'created_at': p.created_at.isoformat() if p.created_at else None,
    })
    try:
        assocs = p.customer_associations if hasattr(p, 'customer_associations') else []
        d['customers'] = [
            {'id': a.company.id, 'name': a.company.name}
            for a in assocs if a.company
        ]
    except Exception:
        d['customers'] = []
    return d


@api_v1_bp.route('/mobile/projects', methods=['GET'])
@jwt_required()
def mobile_project_list():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    search = request.args.get('search', '').strip()
    stage = request.args.get('stage', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(50, int(request.args.get('per_page', 20)))

    query = get_viewable_data(Project, user, [Project.is_deleted == False])
    if search:
        query = query.filter(Project.project_name.ilike(f'%{search}%'))
    if stage:
        query = query.filter(Project.current_stage == stage)

    query = query.order_by(Project.updated_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return api_response(success=True, data={
        'items': [_project_summary(p) for p in pagination.items],
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages,
        'stages': [{'key': k, 'label': v} for k, v in STAGE_LABELS.items()],
    })


@api_v1_bp.route('/mobile/projects/<int:project_id>', methods=['GET'])
@jwt_required()
def mobile_project_detail(project_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    project = Project.query.filter_by(id=project_id, is_deleted=False).first()
    if not project:
        return api_response(success=False, code=404, message="项目不存在")

    from app.utils.access_control import can_view_project
    if not can_view_project(user, project):
        return api_response(success=False, code=403, message="无权访问此项目")

    return api_response(success=True, data=_project_detail(project))


@api_v1_bp.route('/mobile/projects/<int:project_id>/stage', methods=['POST'])
@jwt_required()
def mobile_project_update_stage(project_id):
    """推进/更新项目阶段"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    project = Project.query.filter_by(id=project_id, is_deleted=False).first()
    if not project:
        return api_response(success=False, code=404, message="项目不存在")

    from app.utils.access_control import can_view_project
    if not can_view_project(user, project):
        return api_response(success=False, code=403, message="无权访问此项目")

    data = request.get_json() or {}
    new_stage = data.get('stage', '').strip()
    if new_stage not in STAGE_LABELS:
        return api_response(success=False, code=400, message=f"无效阶段值")

    if new_stage == project.current_stage:
        return api_response(success=False, code=400, message="与当前阶段相同，无需更新")

    # 复用现有的锁定检查（与桌面端一致）
    from app.helpers.project_helpers import is_project_editable
    from app.permissions import is_admin_or_ceo
    is_editable, lock_reason = is_project_editable(project_id, user_id)
    if not is_editable and not (user.role in ('admin', 'ceo')):
        return api_response(success=False, code=403, message=f"项目已锁定无法推进：{lock_reason}")

    # 权限：负责人、厂商销售经理或管理员
    vendor_mgr_id = getattr(project, 'vendor_sales_manager_id', None)
    if user.role not in ('admin', 'ceo') and user_id != project.owner_id and user_id != vendor_mgr_id:
        return api_response(success=False, code=403, message="只有项目负责人可推进阶段")

    # 复用现有的业务逻辑函数（包含批价单/报价单流程检查）
    from app.views.project import update_project_stage_business_logic
    result = update_project_stage_business_logic(project_id, new_stage, user_id)

    if result.get('error'):
        return api_response(success=False, code=400, message=result['error'])

    new_label = STAGE_LABELS.get(new_stage, new_stage)
    return api_response(success=True, message=f"阶段已更新为「{new_label}」", data={
        'current_stage': new_stage,
        'stage_label': new_label,
    })


@api_v1_bp.route('/mobile/projects/<int:project_id>/auth-request', methods=['POST'])
@jwt_required()
def mobile_project_auth_request(project_id):
    """提交授权编号申请"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    project = Project.query.filter_by(id=project_id, is_deleted=False).first()
    if not project:
        return api_response(success=False, code=404, message="项目不存在")

    # 权限：项目负责人、厂商销售经理或管理员
    vendor_mgr_id = getattr(project, 'vendor_sales_manager_id', None)
    if user.role != 'admin' and user_id != project.owner_id and user_id != vendor_mgr_id:
        return api_response(success=False, code=403, message="只有项目负责人或管理员可提交授权申请")

    if project.authorization_code:
        return api_response(success=False, code=400, message="此项目已有授权编号，无需重复申请")

    if project.authorization_status == 'pending':
        return api_response(success=False, code=400, message="此项目已提交申请，正在审批中")

    if not project.project_type or not project.project_type.strip():
        return api_response(success=False, code=400, message="项目类型未填写，无法提交申请，请在桌面端完善后再试")

    data = request.get_json() or {}
    note = data.get('note', '').strip()

    try:
        project.authorization_status = 'pending'
        project.feedback = f"申请备注: {note}" if note else None
        db.session.commit()
        return api_response(success=True, message="授权申请已提交，等待审批")
    except Exception as e:
        db.session.rollback()
        logger.error(f"mobile auth request error: {e}")
        return api_response(success=False, code=500, message="提交失败，请重试")


@api_v1_bp.route('/mobile/projects/<int:project_id>/notes', methods=['POST'])
@jwt_required()
def mobile_project_add_note(project_id):
    """添加项目跟进记录"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    project = Project.query.filter_by(id=project_id, is_deleted=False).first()
    if not project:
        return api_response(success=False, code=404, message="项目不存在")

    from app.utils.access_control import can_view_project
    if not can_view_project(user, project):
        return api_response(success=False, code=403, message="无权访问此项目")

    data = request.get_json()
    content = (data or {}).get('content', '').strip()
    if not content:
        return api_response(success=False, code=400, message="跟进内容不能为空")
    if len(content) > 500:
        return api_response(success=False, code=400, message="跟进内容不超过500字")

    try:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo('Asia/Shanghai')).strftime('%Y/%m/%d %H:%M')
        name = user.real_name or user.username
        entry = f'{now} {name} 【移动端跟进】：{content}'
        existing = project.stage_description or ''
        project.stage_description = (existing + ' ' + entry).strip() if existing else entry
        db.session.commit()
        return api_response(success=True, message="跟进记录已添加")
    except Exception as e:
        db.session.rollback()
        logger.error(f"mobile add note error: {e}")
        return api_response(success=False, code=500, message="添加失败，请重试")
