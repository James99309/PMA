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

def _mobile_project_query(user):
    """mobile 专用查询：基于 ownership 权限，不应用桌面端的 content_filters。"""
    base = Project.query.filter(Project.is_deleted == False)
    permission_level = user.get_permission_level('project')
    if not user.has_permission('project', 'view'):
        return base.filter(False)
    if permission_level == 'system':
        return base
    if permission_level == 'company' and user.company_name:
        from app.utils.access_control import get_company_user_ids
        ids = get_company_user_ids(user)
        return base.filter(
            db.or_(Project.owner_id.in_(ids), Project.vendor_sales_manager_id == user.id)
        )
    if permission_level == 'department' and user.department:
        from app.utils.access_control import get_department_user_ids
        ids = get_department_user_ids(user)
        return base.filter(
            db.or_(Project.owner_id.in_(ids), Project.vendor_sales_manager_id == user.id)
        )
    # personal
    from app.utils.access_control import get_personal_viewable_user_ids
    ids = get_personal_viewable_user_ids(user)
    return base.filter(
        db.or_(Project.owner_id.in_(ids), Project.vendor_sales_manager_id == user.id)
    )


from app.api.v1.utils import get_request_lang as _lang  # noqa: E402

def _stage_label(key):
    """直接使用 PMA 字典, 未知值原样返回; 按 Accept-Language 取 zh/en"""
    if not key:
        return ''
    return PROJECT_STAGE_LABELS.get(key, {}).get(_lang(), key)

def _activity_label(key):
    if not key:
        return ''
    return ACTIVITY_STATUS_LABELS.get(key, {}).get(_lang(), key)

def _project_type_label(key):
    if not key:
        return ''
    return PROJECT_TYPE_LABELS.get(key, {}).get(_lang(), key)

_PRODUCT_SITUATION_LABELS = {
    'qualified':    {'zh': '入围',     'en': 'Qualified'},
    'controlled':   {'zh': '受控',     'en': 'Controlled'},
    'not_required': {'zh': '无要求',   'en': 'Not required'},
    'unqualified':  {'zh': '未入围',   'en': 'Not qualified'},
}
def _product_situation_label(key):
    return _PRODUCT_SITUATION_LABELS.get(key, {}).get(_lang(), key or '')

AUTH_STATUS_LABELS = {
    None:       {'zh': '未申请',  'en': 'Not requested'},
    'pending':  {'zh': '申请中',  'en': 'Pending'},
    'rejected': {'zh': '已拒绝',  'en': 'Rejected'},
    'approved': {'zh': '已授权',  'en': 'Approved'},
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
        'city': p.city or '',
        'industry': p.industry or '',
        'updated_at': p.updated_at.isoformat() if p.updated_at else None,
    }


def _project_detail(p, current_user_id=None):
    d = _project_summary(p)
    # 通用审批引擎中是否有进行中实例(走模板9)
    from app.helpers.approval_helpers import get_object_approval_instance
    from app.models.approval import ApprovalStatus
    inst = get_object_approval_instance('project', p.id)
    has_pending_approval = bool(inst and inst.status == ApprovalStatus.PENDING)
    is_approval_rejected = bool(inst and inst.status == ApprovalStatus.REJECTED and not p.authorization_code)
    d.update({
        # 阶段与活跃度
        'stage_description': p.stage_description,
        'activity_status': p.activity_status,
        'activity_label': _activity_label(p.activity_status),
        # 通用审批引擎状态(优先于老的 authorization_status 字段使用)
        'has_pending_approval': has_pending_approval,
        'is_approval_rejected': is_approval_rejected,
        # 授权信息（authorization_code 有值才是真正已获授权）
        'authorization_status': p.authorization_status,
        'authorization_status_label': (
            ('已获授权' if _lang() == 'zh' else 'Authorized') if p.authorization_code else
            (('审批中' if _lang() == 'zh' else 'Under approval') if has_pending_approval else
             (('已驳回' if _lang() == 'zh' else 'Rejected') if is_approval_rejected else
              AUTH_STATUS_LABELS.get(p.authorization_status, AUTH_STATUS_LABELS[None]).get(_lang(), '未申请')))
        ),
        'authorization_code': p.authorization_code,
        # 项目基本信息
        'project_type': p.project_type,
        'project_type_label': _project_type_label(p.project_type),
        'end_user': p.end_user,
        'dealer': p.dealer,
        'contractor': p.contractor,
        'system_integrator': p.system_integrator,
        'product_situation': p.product_situation,
        'product_situation_label': _product_situation_label(p.product_situation),
        'design_issues': p.design_issues,
        # 厂商销售负责人
        'vendor_sales_manager_id': getattr(p, 'vendor_sales_manager_id', None),
        'vendor_sales_manager_name': (
            (p.vendor_sales_manager.real_name or p.vendor_sales_manager.username)
            if getattr(p, 'vendor_sales_manager', None) else ''
        ),
        'delivery_forecast': p.delivery_forecast.isoformat() if p.delivery_forecast else None,
        # 地理位置
        'address':   p.address or '',
        'country':   p.country or '',
        'region':    p.region or '',
        'latitude':  p.latitude,
        'longitude': p.longitude,
        # 锁定状态
        'is_locked': bool(p.is_locked),
        'locked_reason': p.locked_reason,
        # 负责人 ID（用于权限判断）
        'owner_id': p.owner_id,
        'vendor_sales_manager_id': getattr(p, 'vendor_sales_manager_id', None),
        # 时间
        'created_at': p.created_at.isoformat() if p.created_at else None,
    })
    # 当前用户对该项目的可操作权限（前端按此显示/隐藏按钮）
    try:
        if current_user_id:
            from app.models.user import User as _U
            _u = _U.query.get(current_user_id)
            d['can_edit'] = bool(_u and _u.has_permission('project', 'edit')) and not p.is_locked
            # 申请授权：项目负责人 / 厂商销售经理 / admin
            vendor_mgr_id = getattr(p, 'vendor_sales_manager_id', None)
            d['can_apply_auth'] = bool(_u and (
                _u.role == 'admin' or current_user_id == p.owner_id or current_user_id == vendor_mgr_id
            ))
        else:
            d['can_edit'] = False
            d['can_apply_auth'] = False
    except Exception:
        d['can_edit'] = False
        d['can_apply_auth'] = False

    # 项目讨论群：是否已绑定（None 则前端要走"创建讨论群"流程）
    try:
        from app.services import chat_service as _cs
        d['discussion_conversation_id'] = (
            _cs.find_project_conversation(current_user_id, p.id) if current_user_id else None
        )
    except Exception as e:
        logger.warning(f"查找讨论群失败 project={p.id}: {e}")
        d['discussion_conversation_id'] = None

    # 项目成员：owner + shared_with_users（用于项目群 / 讨论卡）
    try:
        member_ids = []
        if p.owner_id:
            member_ids.append(p.owner_id)
        for uid in (p.shared_with_users or []):
            if uid not in member_ids:
                member_ids.append(uid)
        members = []
        if member_ids:
            users = User.query.filter(User.id.in_(member_ids)).all()
            user_map = {u.id: u for u in users}
            for uid in member_ids:
                u = user_map.get(uid)
                if not u:
                    continue
                name = u.real_name or u.username or ''
                members.append({
                    'id': u.id,
                    'name': name,
                    'avatar': name[0] if name else '?',
                    'department': u.department or '',
                    'is_owner': uid == p.owner_id,
                })
        d['members'] = members
    except Exception as e:
        logger.warning(f"加载项目成员失败 project={p.id}: {e}")
        d['members'] = []

    try:
        assocs = p.customer_associations.all() if hasattr(p, 'customer_associations') else []
        d['customers'] = [
            {
                'id': a.company.id,
                'name': a.company.company_name,
                'type': a.customer_type,
            }
            for a in assocs if a.company
        ]
    except Exception:
        d['customers'] = []

    # 报价单（最近5条，Quotation 无 is_deleted 字段）
    try:
        from app.models.quotation import Quotation
        quotations = (
            Quotation.query
            .filter_by(project_id=p.id)
            .order_by(Quotation.created_at.desc())
            .limit(5).all()
        )
        d['quotations'] = [
            {
                'id': q.id,
                'number': q.quotation_number,
                'total': round((q.amount or 0) / 10000, 2),
                'currency': q.currency or 'CNY',
                'status': q.approval_status,
                'created_at': q.created_at.strftime('%Y-%m-%d') if q.created_at else None,
            }
            for q in quotations
        ]
        d['quotation_count'] = Quotation.query.filter_by(project_id=p.id).count()
    except Exception as e:
        logger.error(f"quotation query error: {e}")
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
                'company_name': next((c['name'] for c in d.get('customers', []) if c['id'] == ct.company_id), ''),
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
    industry = request.args.get('industry', '').strip()
    activity = request.args.get('activity', '').strip()
    # 多选: 兼容 axios indexes:false 默认带方括号 (owner_names[]=A) 和 indexes:null (owner_names=A)
    owner_names = request.args.getlist('owner_names') + request.args.getlist('owner_names[]')
    owner_name = request.args.get('owner_name', '').strip()  # 兼容旧单选
    region = request.args.get('region', '').strip()
    amount_min = request.args.get('amount_min', type=float)
    amount_max = request.args.get('amount_max', type=float)
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(50, int(request.args.get('per_page', 20)))

    query = _mobile_project_query(user)
    if search:
        query = query.filter(Project.project_name.ilike(f'%{search}%'))
    if stage:
        query = query.filter(Project.current_stage == stage)
    if industry:
        query = query.filter(Project.industry == industry)
    if activity:
        query = query.filter(Project.activity_status == activity)
    if region:
        # LIKE 兼容 "上海" vs "上海市"
        like = f'%{region}%'
        query = query.filter((Project.city.like(like)) | (Project.region.like(like)))
    if owner_names:
        query = query.join(User, User.id == Project.owner_id) \
                     .filter(User.real_name.in_(owner_names) | User.username.in_(owner_names))
    elif owner_name:
        query = query.join(User, User.id == Project.owner_id) \
                     .filter((User.real_name == owner_name) | (User.username == owner_name))
    # 金额单位：前端传万元，DB 存元
    if amount_min is not None and amount_min > 0:
        query = query.filter(Project.quotation_customer >= amount_min * 10000)
    if amount_max is not None and amount_max > 0:
        query = query.filter(Project.quotation_customer <= amount_max * 10000)

    # 汇总金额必须在 ORDER BY 之前计算，否则 PostgreSQL 报 GroupingError
    from sqlalchemy import func as sa_func
    total_amount_raw = query.with_entities(sa_func.sum(Project.quotation_customer)).scalar() or 0
    total_amount_wan = round(total_amount_raw / 10000, 2)

    sort = request.args.get('sort', 'updated_at')
    if sort == 'amount':
        query = query.order_by(Project.quotation_customer.desc().nullslast())
    elif sort == 'amount_asc':
        query = query.order_by(Project.quotation_customer.asc().nullslast())
    else:
        query = query.order_by(Project.updated_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return api_response(success=True, data={
        'items': [_project_summary(p) for p in pagination.items],
        'total': pagination.total,
        'total_amount': total_amount_wan,
        'page': page,
        'per_page': per_page,
        'pages': pagination.pages,
        'stages': [{'key': k, 'label': v} for k, v in STAGE_LABELS.items()],
    })


@api_v1_bp.route('/mobile/projects/owners', methods=['GET'])
@jwt_required()
def mobile_project_owners():
    """返回当前用户可见项目的 distinct owner 列表(供筛选下拉用)。
    复用 web 端 _get_project_owner_options, 与 web 端筛选数据口径一致。"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")
    try:
        from app.views.project import _get_project_owner_options
        return api_response(success=True, data=_get_project_owner_options(user))
    except Exception as e:
        logger.error(f"mobile_project_owners error: {e}", exc_info=True)
        return api_response(success=False, code=500, message=str(e))


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

    # 与列表口径一致（含权限级别 + content_filters + 共享）
    viewable = get_viewable_data(Project, user, [Project.id == project_id]).first()
    if not viewable:
        return api_response(success=False, code=403, message="无权访问此项目")

    return api_response(success=True, data=_project_detail(project, current_user_id=user_id))


# 厂商销售负责人候选列表（用于项目编辑）
@api_v1_bp.route('/mobile/projects/vendor-sales-managers', methods=['GET'])
@jwt_required()
def mobile_vendor_sales_managers():
    """返回所有可作为"厂商销售负责人"的用户（同公司 sales 系列角色）"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")
    try:
        # 同公司的所有 active 用户（排除 dealer/distributor 等外部角色）
        roles_external = ('dealer', 'distributor', 'customer_sales')
        q = User.query.filter(User._is_active == True)
        if user.company_name:
            q = q.filter(User.company_name == user.company_name)
        users = q.filter(~User.role.in_(roles_external)).order_by(User.real_name).all()
        return api_response(success=True, data=[{
            'id': u.id,
            'name': u.real_name or u.username,
            'username': u.username,
            'department': u.department or '',
            'role': u.role,
        } for u in users])
    except Exception as e:
        logger.error(f"vendor sales managers error: {e}", exc_info=True)
        return api_response(success=False, code=500, message=str(e))


# 编辑项目基本信息
@api_v1_bp.route('/mobile/projects/<int:project_id>', methods=['PATCH', 'PUT'])
@jwt_required()
def mobile_project_update(project_id):
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    project = Project.query.filter_by(id=project_id, is_deleted=False).first()
    if not project:
        return api_response(success=False, code=404, message="项目不存在")

    # 双层检查：可见 + 有 project:edit 权限
    viewable = get_viewable_data(Project, user, [Project.id == project_id]).first()
    if not viewable:
        return api_response(success=False, code=403, message="无权访问此项目")
    if not user.has_permission('project', 'edit'):
        return api_response(success=False, code=403, message="您只有查看权限，无法编辑项目")
    if project.is_locked:
        return api_response(success=False, code=403, message=f"项目已锁定: {project.locked_reason or '无法编辑'}")

    data = request.get_json() or {}

    # 允许编辑字段（不含 stage / authorization / status / lock / 客户关联）
    allowed = ['project_name', 'project_type', 'industry',
               'product_situation', 'design_issues', 'stage_description',
               'address', 'country', 'region', 'city',
               'latitude', 'longitude',
               'vendor_sales_manager_id']

    for k in allowed:
        if k in data:
            setattr(project, k, data[k] or None)

    # 日期字段单独处理
    if 'delivery_forecast' in data:
        from datetime import datetime as _dt
        v = data['delivery_forecast']
        if v:
            try:
                project.delivery_forecast = _dt.fromisoformat(v.replace('Z', '+00:00')).date() \
                    if 'T' in v else _dt.strptime(v, '%Y-%m-%d').date()
            except Exception:
                pass
        else:
            project.delivery_forecast = None

    try:
        db.session.commit()
        return api_response(success=True, data=_project_detail(project, current_user_id=user_id))
    except Exception as e:
        db.session.rollback()
        logger.error(f"项目更新失败 project={project_id}: {e}", exc_info=True)
        return api_response(success=False, code=500, message=f"更新失败: {str(e)}")


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

    viewable = get_viewable_data(Project, user, [Project.id == project_id]).first()
    if not viewable:
        return api_response(success=False, code=403, message="无权访问此项目")
    if not user.has_permission('project', 'edit'):
        return api_response(success=False, code=403, message="您只有查看权限，无法推进阶段")

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
    """提交项目审批 — 走通用流程引擎(模板9)，与 web 端「提交审批」按钮一致。"""
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
        return api_response(success=False, code=403, message="只有项目负责人或管理员可提交审批")

    if project.authorization_code:
        return api_response(success=False, code=400, message="此项目已有授权编号，无需重复申请")

    if not project.project_type or not project.project_type.strip():
        return api_response(success=False, code=400, message="项目类型未填写，无法提交申请，请在桌面端完善后再试")

    from app.helpers.approval_helpers import (
        start_approval_process, get_available_templates, get_object_approval_instance
    )
    from app.models.approval import ApprovalStatus, ApprovalRecord

    existing = get_object_approval_instance('project', project_id)
    if existing and existing.status == ApprovalStatus.PENDING:
        return api_response(success=False, code=400, message="此项目已有进行中的审批")

    templates = get_available_templates('project')
    if not templates:
        return api_response(success=False, code=400, message="未找到可用的项目审批模板，请联系管理员")

    data = request.get_json() or {}
    note = (data.get('note') or '').strip()

    try:
        instance = start_approval_process(
            object_type='project',
            object_id=project_id,
            template_id=templates[0].id,
            user_id=user_id,
            auto_commit=False,
        )
        if not instance:
            db.session.rollback()
            return api_response(success=False, code=500, message="启动审批流程失败")

        # 备注挂到首条 submit 记录的 comment 字段（如已自动写入 record，更新它；否则补写）
        if note:
            submit_rec = ApprovalRecord.query.filter_by(
                instance_id=instance.id, action='submit'
            ).order_by(ApprovalRecord.created_at.desc()).first()
            if submit_rec and not submit_rec.comment:
                submit_rec.comment = note

        # 与 web 端 start_project_approval 行为一致
        project.status = 'pending'
        db.session.commit()
        return api_response(
            success=True,
            data={'instance_id': instance.id},
            message="审批已提交"
        )
    except Exception as e:
        db.session.rollback()
        logger.exception(f"mobile auth request error: {e}")
        return api_response(success=False, code=500, message=f"提交失败: {e}")


@api_v1_bp.route('/mobile/projects/<int:project_id>/recall', methods=['POST'])
@jwt_required()
def mobile_project_recall(project_id):
    """召回项目审批 — 仿 web /project/api/approval/<id>/recall。"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message="用户不存在")

    project = Project.query.filter_by(id=project_id, is_deleted=False).first()
    if not project:
        return api_response(success=False, code=404, message="项目不存在")

    from app.helpers.approval_helpers import (
        get_object_approval_instance, can_recall_approval, recall_approval_process
    )
    inst = get_object_approval_instance('project', project_id)
    if not inst:
        return api_response(success=False, code=400, message="项目没有进行中的审批")

    if not can_recall_approval('project', project_id, user_id):
        return api_response(success=False, code=403, message="只有审批发起人或管理员可以召回")

    try:
        success, message = recall_approval_process('project', project_id, user_id)
        if success:
            return api_response(success=True, message=message or "召回成功")
        return api_response(success=False, code=500, message=message or "召回失败")
    except Exception as e:
        db.session.rollback()
        logger.exception(f"项目召回失败: {e}")
        return api_response(success=False, code=500, message=f"召回失败: {e}")


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

    viewable = get_viewable_data(Project, user, [Project.id == project_id]).first()
    if not viewable:
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


@api_v1_bp.route('/mobile/check-name/project', methods=['POST'])
@jwt_required()
def mobile_check_project_name():
    """项目名称实时查重"""
    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    if not name:
        return api_response(success=True, data={'similar': []})

    try:
        from app.utils.text_similarity import is_similar_project_name
        projects = Project.query.filter(
            Project.is_deleted == False,
            db.or_(Project.authorization_status != 'rejected', Project.authorization_status.is_(None))
        ).with_entities(Project.id, Project.project_name, Project.authorization_code).all()

        similar = []
        for p in projects:
            pn = p.project_name or ''
            if not pn:
                continue
            is_sim, score = is_similar_project_name(name, pn, threshold=55)
            if is_sim:
                similar.append({
                    'id': p.id,
                    'name': pn,
                    'auth_code': p.authorization_code,
                    'score': round(score),
                })
        similar.sort(key=lambda x: x['score'], reverse=True)
        return api_response(success=True, data={'similar': similar[:5]})
    except Exception as e:
        logger.error(f"mobile check project name error: {e}")
        return api_response(success=False, code=500, message=str(e))


@api_v1_bp.route('/mobile/projects', methods=['POST'])
@jwt_required()
def mobile_create_project():
    """新建项目"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    data = request.get_json() or {}
    name = (data.get('name') or '').strip()
    industry = (data.get('industry') or '').strip()
    description = (data.get('description') or '').strip()

    if not name:
        return api_response(success=False, code=400, message='项目名称不能为空')
    if not industry:
        return api_response(success=False, code=400, message='项目行业不能为空')
    if not description:
        return api_response(success=False, code=400, message='项目描述不能为空')

    from datetime import datetime, date as date_type
    delivery_forecast = None
    if data.get('delivery_forecast'):
        try:
            delivery_forecast = datetime.strptime(data['delivery_forecast'], '%Y-%m-%d').date()
        except ValueError:
            pass

    try:
        project = Project(
            project_name=name,
            industry=industry,
            stage_description=description,
            report_source=data.get('report_source') or None,
            project_type=data.get('project_type') or None,
            product_situation=data.get('product_situation') or None,
            delivery_forecast=delivery_forecast,
            country=data.get('country') or None,
            region=data.get('region') or None,
            city=data.get('city') or None,
            address=data.get('address') or None,
            latitude=data.get('latitude') or None,
            longitude=data.get('longitude') or None,
            current_stage='discover',
            created_by=user_id,
            owner_id=user_id,
        )
        db.session.add(project)
        db.session.commit()
        return api_response(success=True, message='项目已创建', data={'id': project.id})
    except Exception as e:
        db.session.rollback()
        logger.error(f"mobile create project error: {e}")
        return api_response(success=False, code=500, message='创建失败，请重试')
