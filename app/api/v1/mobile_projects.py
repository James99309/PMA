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
from app.utils.dictionary_helpers import (
    PROJECT_STAGE_LABELS, ACTIVITY_STATUS_LABELS, PROJECT_TYPE_LABELS
)

def _stage_label(key):
    """直接使用 PMA 字典，未知值原样返回"""
    if not key:
        return ''
    return PROJECT_STAGE_LABELS.get(key, {}).get('zh', key)

def _activity_label(key):
    if not key:
        return ''
    return ACTIVITY_STATUS_LABELS.get(key, {}).get('zh', key)

def _project_type_label(key):
    if not key:
        return ''
    return PROJECT_TYPE_LABELS.get(key, {}).get('zh', key)

AUTH_STATUS_LABELS = {
    None:       '未申请',
    'pending':  '申请中',
    'rejected': '已拒绝',
    'approved': '已授权',
}

# 保留供阶段选择器使用（标准可选阶段）
STAGE_LABELS = {k: v['zh'] for k, v in PROJECT_STAGE_LABELS.items()}


def _project_summary(p):
    amount = p.quotation_customer or 0
    return {
        'id': p.id,
        'name': p.project_name,
        'current_stage': p.current_stage,
        'stage_label': _stage_label(p.current_stage),
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
        'activity_label': _activity_label(p.activity_status),
        # 授权信息（authorization_code 有值才是真正已获授权，status 在批准后会被清为 None）
        'authorization_status': p.authorization_status,
        'authorization_status_label': (
            '已获授权' if p.authorization_code else
            AUTH_STATUS_LABELS.get(p.authorization_status, '未申请')
        ),
        'authorization_code': p.authorization_code,
        # 项目基本信息
        'project_type': p.project_type,
        'project_type_label': _project_type_label(p.project_type),
        'end_user': p.end_user,
        'dealer': p.dealer,
        'system_integrator': p.system_integrator,
        'delivery_forecast': p.delivery_forecast.isoformat() if p.delivery_forecast else None,
        # 锁定状态
        'is_locked': bool(p.is_locked),
        'locked_reason': p.locked_reason,
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

    # 报价单（最近5条）
    try:
        from app.models.quotation import Quotation
        quotations = (
            Quotation.query
            .filter_by(project_id=p.id, is_deleted=False)
            .order_by(Quotation.created_at.desc())
            .limit(5).all()
        )
        d['quotations'] = [
            {
                'id': q.id,
                'number': q.quotation_number,
                'total': round((q.total_amount or 0) / 10000, 2),
                'currency': q.currency or 'CNY',
                'status': q.approval_status,
                'created_at': q.created_at.strftime('%Y-%m-%d') if q.created_at else None,
            }
            for q in quotations
        ]
        d['quotation_count'] = Quotation.query.filter_by(project_id=p.id, is_deleted=False).count()
    except Exception:
        d['quotations'] = []
        d['quotation_count'] = 0

    # 关联客户联系人
    try:
        from app.models.customer import Contact
        company_ids = [c['id'] for c in d.get('customers', [])]
        contacts = Contact.query.filter(
            Contact.company_id.in_(company_ids)
        ).limit(20).all() if company_ids else []
        d['contacts'] = [
            {
                'id': ct.id,
                'name': ct.name,
                'title': ct.title,
                'phone': ct.phone,
                'email': ct.email,
                'company_id': ct.company_id,
                'company_name': next((c['name'] for c in d['customers'] if c['id'] == ct.company_id), ''),
            }
            for ct in contacts
        ]
    except Exception:
        d['contacts'] = []

    # 最近跟进记录（Action 表）
    try:
        from app.models.action import Action
        actions = (
            Action.query
            .filter_by(project_id=p.id)
            .order_by(Action.date.desc(), Action.created_at.desc())
            .limit(20)
            .all()
        )
        d['actions'] = [
            {
                'id': a.id,
                'date': a.date.isoformat() if a.date else None,
                'communication': a.communication,
                'owner_name': a.owner.real_name or a.owner.username if a.owner else '',
            }
            for a in actions
        ]
    except Exception:
        d['actions'] = []

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

    new_label = _stage_label(new_stage)
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
        from datetime import date
        from app.models.action import Action
        action = Action(
            date=date.today(),
            project_id=project_id,
            communication=content,
            owner_id=user_id,
            is_shared=True,
        )
        db.session.add(action)
        db.session.commit()
        return api_response(success=True, message="跟进记录已添加")
    except Exception as e:
        db.session.rollback()
        logger.error(f"mobile add note error: {e}")
        return api_response(success=False, code=500, message="添加失败，请重试")
