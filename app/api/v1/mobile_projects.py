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

STAGE_LABEL = {
    'lead': '线索', 'opportunity': '商机', 'proposal': '投标/方案',
    'negotiation': '谈判', 'won': '赢单', 'lost': '丢单', 'suspended': '暂停',
}

def _project_summary(p):
    amount = p.quotation_customer or 0  # 已是元单位，转万元
    return {
        'id': p.id,
        'name': p.project_name,
        'current_stage': p.current_stage,
        'stage_label': STAGE_LABEL.get(p.current_stage, p.current_stage or ''),
        'status': p.status,
        'amount': round(amount / 10000, 2) if amount else 0,
        'currency': getattr(p, 'quotation_currency', 'CNY') or 'CNY',
        'owner_name': p.owner.real_name or p.owner.username if p.owner else '',
        'updated_at': p.updated_at.isoformat() if p.updated_at else None,
    }

def _project_detail(p):
    d = _project_summary(p)
    d.update({
        'stage_description': p.stage_description,
        'activity_status': p.activity_status,
        'authorization_status': p.authorization_status,
        'created_at': p.created_at.isoformat() if p.created_at else None,
    })
    # 关联客户
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


@api_v1_bp.route('/mobile/projects/<int:project_id>/notes', methods=['POST'])
@jwt_required()
def mobile_project_add_note(project_id):
    """添加项目跟进记录（纯文本，仅限查看权限用户）"""
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
        from app.models.work_item import WorkItem
        note = WorkItem(
            project_id=project_id,
            created_by=user_id,
            content=f'[移动端] {content}',
            item_type='follow_up',
        )
        db.session.add(note)
        db.session.commit()
        return api_response(success=True, message="跟进记录已添加")
    except Exception as e:
        db.session.rollback()
        logger.error(f"mobile add note error: {e}")
        return api_response(success=False, code=500, message="添加失败，请重试")
