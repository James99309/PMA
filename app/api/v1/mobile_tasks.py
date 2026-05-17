# -*- coding: utf-8 -*-
"""移动端 任务中心 — 列表 + 计数(P1)

设计稿: Claude Design「PMA Task EN / 任务中心」task-list。
i18n 纪律: 数据值(状态/优先级)由后端按 Accept-Language 出 *_label,
前端只消费 label,不自建中文 map(见 CLAUDE-I18N.md 移动端纪律)。
"""
from datetime import datetime, date
from flask import request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.api.v1 import api_v1_bp
from app.api.v1.utils import api_response, get_request_lang as _lang
from app.models.user import User
from app.models.task import Task
from app.models.subtask import SubTask
from app import db
import logging

logger = logging.getLogger(__name__)

# 状态 / 优先级 zh-en(与设计 task-base / task-base-en 一致)。前端按 key 取色。
_TASK_STATUS = {
    'pending':        {'zh': '待开始', 'en': 'To Do'},
    'in_progress':    {'zh': '进行中', 'en': 'In Progress'},
    'paused':         {'zh': '已暂停', 'en': 'Paused'},
    'pending_review': {'zh': '待审核', 'en': 'In Review'},
    'completed':      {'zh': '已完成', 'en': 'Completed'},
    'cancelled':      {'zh': '已取消', 'en': 'Cancelled'},
}
_TASK_PRIORITY = {
    'urgent': {'zh': '紧急', 'en': 'Urgent'},
    'high':   {'zh': '高',   'en': 'High'},
    'normal': {'zh': '普通', 'en': 'Normal'},
    'low':    {'zh': '低',   'en': 'Low'},
}


def _status_label(k):
    m = _TASK_STATUS.get(k or 'pending', _TASK_STATUS['pending'])
    return m.get(_lang(), m['zh'])


def _priority_label(k):
    m = _TASK_PRIORITY.get(k or 'normal', _TASK_PRIORITY['normal'])
    return m.get(_lang(), m['zh'])


def _initials(name):
    if not name:
        return '?'
    name = name.strip()
    # 英文取首字母,中文取末一字(姓名习惯)
    if name[0].isascii() and name[0].isalpha():
        parts = [p for p in name.split() if p]
        return ((parts[0][0] + (parts[1][0] if len(parts) > 1 else '')) or '?').upper()
    return name[-1]


def _due_disp(dt):
    """设计里截止日是 'M/D' 短格式;逾期由前端按颜色,文本给短日期。"""
    if not dt:
        return None
    d = dt.date() if isinstance(dt, datetime) else dt
    return f'{d.month}/{d.day}'


def _sub_progress(task_id):
    total = SubTask.query.filter(SubTask.task_id == task_id).count()
    if not total:
        return {'done': 0, 'total': 0}
    done = SubTask.query.filter(
        SubTask.task_id == task_id, SubTask.status == 'completed'
    ).count()
    return {'done': done, 'total': total}


def _is_overdue(t):
    if t.status in ('completed', 'cancelled') or not t.due_date:
        return False
    due = t.due_date
    now = datetime.now()
    if isinstance(due, datetime):
        return due < now
    return due < date.today()


def _task_row(t, uid=None):
    a = t.assignee
    a_name = (a.real_name or a.username) if a else ''
    return {
        'id': t.id,
        'title': t.title,
        'desc': (t.description or '').strip(),
        'status': t.status,
        'status_label': _status_label(t.status),
        'priority': t.priority,
        'priority_label': _priority_label(t.priority),
        'assignee_name': a_name,
        'assignee_short': _initials(a_name),
        'due': _due_disp(t.due_date),
        'overdue': _is_overdue(t),
        'sub': _sub_progress(t.id),
        'project': (t.project.project_name if t.project else None),
        'customer': (t.customer.company_name if t.customer else None),
        'mention': 0,  # P1: @我 计数后续接(评论 mention 解析),先 0 不显示徽章
        'can_delete': (uid is not None and t.creator_id == uid),
        'updated_at': t.updated_at.isoformat() if t.updated_at else None,
    }


def _base_q():
    return Task.query.filter(Task.is_deleted == False)  # noqa: E712


def _viewable_account_ids(user):
    """当前用户有权限查看其任务的账户 id 集合:本人 + 归属下属 + 管辖部门;
    若 task 权限级别为 company/department 再相应扩展。"""
    from app.utils.access_control import (
        get_personal_viewable_user_ids, get_company_user_ids,
        get_department_user_ids)
    ids = set(get_personal_viewable_user_ids(user))
    ids.add(user.id)
    try:
        lvl = user.get_permission_level('task')
    except Exception:
        lvl = 'personal'
    if lvl == 'company':
        ids |= set(get_company_user_ids(user))
    elif lvl == 'department':
        ids |= set(get_department_user_ids(user))
    return ids


def _subordinate_ids(user):
    """直接归属下属(Affiliation viewer→owner)。"""
    from app.models.user import Affiliation
    return {a.owner_id for a in Affiliation.query.filter_by(viewer_id=user.id).all()}


def _acct_stat(aid):
    """某账户进行中(未完成/取消)的任务数与逾期数。"""
    rows = _base_q().filter(
        Task.assignee_id == aid,
        Task.status.notin_(['completed', 'cancelled'])
    ).all()
    return {'count': len(rows), 'overdue': sum(1 for t in rows if _is_overdue(t))}


def _tab_query(uid, tab):
    q = _base_q()
    if tab == 'created':
        return q.filter(Task.creator_id == uid)
    if tab == 'review':
        # 待我审核: 状态待审 且 我是审核人
        from app.models.task import TaskReviewer
        rid = db.session.query(TaskReviewer.task_id).filter(
            TaskReviewer.reviewer_id == uid
        )
        return q.filter(Task.status == 'pending_review', Task.id.in_(rid))
    if tab == 'shared':
        # 协助人列表是 JSON,跨库可移植做法: 取候选再 python 过滤
        return None  # 交由调用方走 python 过滤分支
    # 默认 mine = 我负责的
    return q.filter(Task.assignee_id == uid)


@api_v1_bp.route('/mobile/tasks', methods=['GET'])
@jwt_required()
def mobile_tasks_list():
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')

    tab = (request.args.get('tab') or 'mine').strip()
    status_f = (request.args.get('status') or '').strip()  # all/in_progress/pending_review/completed/overdue
    sort = (request.args.get('sort') or 'due_desc').strip()
    page = max(1, request.args.get('page', 1, type=int))
    per = min(50, max(1, request.args.get('per', 20, type=int)))

    # 切换视角:?owner_id=<uid> 查看他人任务(需在可见范围内)
    owner_id = request.args.get('owner_id', type=int)
    viewing_other = False
    eff = uid
    if owner_id and owner_id != uid:
        if owner_id not in _viewable_account_ids(user):
            return api_response(success=False, code=403, message='无权查看该账户的任务')
        eff = owner_id
        viewing_other = True
        if tab == 'review':  # 他人视角无"待我审核"
            tab = 'mine'

    if tab == 'shared':
        rows = _base_q().filter(
            Task.assignee_id != eff, Task.creator_id != eff
        ).all()
        rows = [t for t in rows if eff in (t.shared_with_users or [])]
    else:
        q = _tab_query(eff, tab)
        rows = q.all()

    # 关键词搜索(标题/描述)
    kw = (request.args.get('q') or '').strip().lower()
    if kw:
        rows = [t for t in rows if kw in (t.title or '').lower()
                or kw in (t.description or '').lower()]

    # 状态/逾期筛选
    if status_f and status_f != 'all':
        if status_f == 'overdue':
            rows = [t for t in rows if _is_overdue(t)]
        else:
            rows = [t for t in rows if t.status == status_f]

    # 排序
    def _due_key(t):
        return (t.due_date or datetime.max)
    if sort == 'due_asc':
        rows.sort(key=_due_key)
    elif sort == 'priority':
        order = {'urgent': 0, 'high': 1, 'normal': 2, 'low': 3}
        rows.sort(key=lambda t: order.get(t.priority, 9))
    elif sort == 'updated':
        rows.sort(key=lambda t: (t.updated_at or datetime.min), reverse=True)
    else:  # due_desc 默认
        rows.sort(key=_due_key)

    total = len(rows)
    start = (page - 1) * per
    page_rows = rows[start:start + per]

    # 计数(tab badge + hero) — 按 effective 账户;review 仅本人视角
    mine_all = _base_q().filter(Task.assignee_id == eff).all()
    created_n = _base_q().filter(Task.creator_id == eff).count()
    shared_cands = _base_q().filter(
        Task.assignee_id != eff, Task.creator_id != eff
    ).all()
    shared_n = sum(1 for t in shared_cands if eff in (t.shared_with_users or []))
    if viewing_other:
        review_n = 0
    else:
        from app.models.task import TaskReviewer
        review_n = _base_q().filter(
            Task.status == 'pending_review',
            Task.id.in_(db.session.query(TaskReviewer.task_id).filter(
                TaskReviewer.reviewer_id == uid)),
        ).count()
    in_progress_n = sum(1 for t in mine_all if t.status == 'in_progress')
    overdue_n = sum(1 for t in mine_all if _is_overdue(t))

    data = {
        'items': [_task_row(t, uid) for t in page_rows],
        'total': total,
        'page': page,
        'per': per,
        'viewing_other': viewing_other,
        'counts': {
            'mine': len(mine_all),
            'created': created_n,
            'shared': shared_n,
            'review': review_n,
            'in_progress': in_progress_n,
            'overdue': overdue_n,
        },
    }
    if viewing_other:
        ou = User.query.get(eff)
        oname = (ou.real_name or ou.username) if ou else ''
        data['owner'] = {
            'id': eff, 'name': oname, 'short': _initials(oname),
            'department': (ou.department or '') if ou else '',
            'total': len(mine_all),
        }
    return api_response(success=True, data=data)


# ─── P1④ 详情 / 新建 / 改状态 / 评论 / 审核 (写侧走 task_service) ──────


def _sub_rows(task, uid=None):
    from app.models.task import TaskReply
    out = []
    for s in task.subtasks.filter_by(is_deleted=False):
        owner = s.assignee
        oname = (owner.real_name or owner.username) if owner else ''
        notes = TaskReply.query.filter_by(
            subtask_id=s.id, is_deleted=False
        ).count()
        mrs = list(s.milestone_reviewers) if s.is_milestone else []
        my_mr = next((r for r in mrs if r.reviewer_id == uid), None) if uid else None
        out.append({
            'id': s.id, 'title': s.title,
            'description': s.description or '',
            'assignee_id': s.assignee_id,
            'owner_name': oname, 'owner_short': _initials(oname),
            'start': _due_disp(s.start_date), 'due': _due_disp(s.due_date),
            'start_date': s.start_date.isoformat() if s.start_date else None,
            'due_date': s.due_date.isoformat() if s.due_date else None,
            'status': s.status,
            'status_label': _status_label(s.status),
            'is_milestone': bool(s.is_milestone),
            'milestone_status': s.milestone_status,
            'milestone_criteria': s.milestone_criteria or '',
            'milestone_reviewers': [{
                'reviewer_id': r.reviewer_id,
                'reviewer_name': (r.reviewer.real_name or r.reviewer.username) if r.reviewer else '',
                'status': r.status,
            } for r in mrs],
            'my_milestone_state': my_mr.status if my_mr else None,
            'can_confirm_milestone': bool(
                my_mr and my_mr.status == 'pending'
                and s.milestone_status == 'pending_confirmation'),
            'progress_notes': notes,
        })
    return out


def _timeline(task):
    out = []
    for r in task.replies.filter_by(is_deleted=False):
        au = r.author
        aname = (au.real_name or au.username) if au else (r.reply_type == 'system' and 'System' or '')
        rt = r.reply_type or 'comment'
        kind = 'system' if rt == 'system' else ('progress' if rt in ('update', 'progress') else 'reply')
        out.append({
            'kind': kind,
            'author': aname,
            'author_short': _initials(aname),
            'at': r.created_at.strftime('%m/%d %H:%M') if r.created_at else '',
            'text': r.content or '',
            'sub': (r.subtask.title if getattr(r, 'subtask', None) else None),
        })
    return out




def _attachment_rows(t):
    """任务附件列表(序列化复用 task_service.attachment_dict + 下载代理 url)。"""
    from urllib.parse import quote
    from app.models.task import TaskAttachment
    from app.services import task_service
    from app.utils.smart_storage_manager import get_smart_storage
    st = get_smart_storage()
    nas_ok = st.nas_enabled and st.is_nas_available()
    rows = TaskAttachment.query.filter_by(
        task_id=t.id, is_deleted=False
    ).order_by(TaskAttachment.created_at.desc()).all()
    out = []
    for a in rows:
        ad = task_service.attachment_dict(a, nas_ok=nas_ok)
        ad['url'] = '/api/v1/mobile/tasks/file?path=' + quote(a.storage_path or '')
        out.append(ad)
    return out


def _can_see(t, uid, user):
    if t.creator_id == uid or t.assignee_id == uid:
        return True
    if uid in (t.shared_with_users or []):
        return True
    if any(rv.reviewer_id == uid for rv in t.task_reviewers):
        return True
    role = (getattr(user, 'role', '') or '').lower()
    return role in ('admin', 'ceo')


@api_v1_bp.route('/mobile/tasks/<int:tid>', methods=['GET'])
@jwt_required()
def mobile_task_detail(tid):
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')
    t = Task.query.filter_by(id=tid, is_deleted=False).first()
    if not t or not _can_see(t, uid, user):
        return api_response(success=False, code=404, message='任务不存在或无权限')
    d = t.to_dict()
    d['status_label'] = _status_label(t.status)
    d['priority_label'] = _priority_label(t.priority)
    d['subtasks'] = _sub_rows(t, uid)
    d['timeline'] = _timeline(t)
    d['overdue'] = _is_overdue(t)
    d['attachments'] = _attachment_rows(t)
    my_rv = next((rv for rv in t.task_reviewers if rv.reviewer_id == uid), None)
    d['my_review_state'] = my_rv.status if my_rv else None
    # 与 web _can_edit 单一来源一致:仅创建人可编辑
    d['can_edit'] = (t.creator_id == uid)
    d['can_review'] = bool(my_rv and my_rv.status == 'pending'
                           and t.status == 'pending_review')
    # 子任务增改删:与 web _can_access 一致(可访问者)
    d['can_subtask'] = _can_see(t, uid, user)
    # 重新提交会审:创建人/负责人 且 被驳回
    d['can_resubmit'] = ((t.creator_id == uid or t.assignee_id == uid)
                         and t.review_status == 'rejected')
    return api_response(success=True, data=d)


@api_v1_bp.route('/mobile/tasks', methods=['POST'])
@jwt_required()
def mobile_task_create():
    """薄壳:逻辑+副作用走共享 task_service(与 web 同一来源)。"""
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')
    from app.services import task_service
    try:
        t = task_service.create_task(user, request.get_json() or {})
    except ValueError as ve:
        return api_response(success=False, code=400, message=str(ve))
    except Exception as e:
        db.session.rollback()
        logger.error(f'task create error: {e}')
        return api_response(success=False, code=500, message='创建失败')
    return api_response(success=True, data={'id': t.id})


@api_v1_bp.route('/mobile/tasks/<int:tid>', methods=['PATCH'])
@jwt_required()
def mobile_task_update(tid):
    """薄壳:编辑走共享 task_service.update_task(与 web 同一来源)。
    权限与 web _can_edit 一致:仅创建人。"""
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')
    t = Task.query.filter_by(id=tid, is_deleted=False).first()
    if not t:
        return api_response(success=False, code=404, message='任务不存在')
    if t.creator_id != uid:
        return api_response(success=False, code=403, message='仅创建人可编辑此任务')
    from app.services import task_service
    try:
        task_service.update_task(user, t, request.get_json() or {})
    except ValueError as ve:
        return api_response(success=False, code=400, message=str(ve))
    except Exception as e:
        db.session.rollback()
        logger.error(f'task update error: {e}')
        return api_response(success=False, code=500, message='更新失败')
    return api_response(success=True, data={'id': t.id})


@api_v1_bp.route('/mobile/tasks/<int:tid>/status', methods=['POST'])
@jwt_required()
def mobile_task_status(tid):
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')
    t = Task.query.filter_by(id=tid, is_deleted=False).first()
    if not t:
        return api_response(success=False, code=404, message='任务不存在')
    if t.creator_id != uid and t.assignee_id != uid:
        return api_response(success=False, code=403, message='仅创建人或负责人可改状态')
    data = request.get_json() or {}
    from app.services import task_service
    try:
        task_service.change_status(user, t, (data.get('to') or '').strip(),
                                   reason=data.get('reason') or '')
    except ValueError as ve:
        return api_response(success=False, code=400, message=str(ve))
    except Exception as e:
        db.session.rollback()
        logger.error(f'task status error: {e}')
        return api_response(success=False, code=500, message='操作失败')
    return api_response(success=True, data={'status': t.status,
                                            'status_label': _status_label(t.status)})


@api_v1_bp.route('/mobile/tasks/<int:tid>/replies', methods=['POST'])
@jwt_required()
def mobile_task_reply(tid):
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')
    t = Task.query.filter_by(id=tid, is_deleted=False).first()
    if not t or not _can_see(t, uid, user):
        return api_response(success=False, code=404, message='任务不存在或无权限')
    body = request.get_json() or {}
    from app.services import task_service
    try:
        task_service.add_reply(user, t, body.get('content'),
                               subtask_id=body.get('subtask_id'),
                               reply_type=body.get('reply_type') or 'comment')
    except ValueError as ve:
        return api_response(success=False, code=400, message=str(ve))
    except Exception as e:
        db.session.rollback()
        logger.error(f'task reply error: {e}')
        return api_response(success=False, code=500, message='发送失败')
    return api_response(success=True, data={'timeline': _timeline(t)})


@api_v1_bp.route('/mobile/tasks/<int:tid>/review', methods=['POST'])
@jwt_required()
def mobile_task_review(tid):
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')
    t = Task.query.filter_by(id=tid, is_deleted=False).first()
    if not t:
        return api_response(success=False, code=404, message='任务不存在')
    data = request.get_json() or {}
    from app.services import task_service
    try:
        t, _msg = task_service.review_task(
            user, t, (data.get('action') or '').strip(), data.get('comment') or '')
    except ValueError as ve:
        return api_response(success=False, code=403, message=str(ve))
    except Exception as e:
        db.session.rollback()
        logger.error(f'task review error: {e}')
        return api_response(success=False, code=500, message='操作失败')
    return api_response(success=True, data={'status': t.status,
                                            'status_label': _status_label(t.status)})


@api_v1_bp.route('/mobile/tasks/<int:tid>/attachments', methods=['POST'])
@jwt_required()
def mobile_task_attach(tid):
    """薄壳:上传附件走共享 task_service.add_attachment。"""
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')
    t = Task.query.filter_by(id=tid, is_deleted=False).first()
    if not t or not _can_see(t, uid, user):
        return api_response(success=False, code=404, message='任务不存在或无权限')
    f = request.files.get('file')
    if not f or not f.filename:
        return api_response(success=False, code=400, message='请选择文件')
    filename = f.filename
    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    f.seek(0, 2)
    file_size = f.tell()
    f.seek(0)
    subtask_id = request.form.get('subtask_id', type=int)
    from app.services import task_service
    try:
        att = task_service.add_attachment(user, t, f, filename, file_size,
                                          file_ext, subtask_id=subtask_id)
    except ValueError as ve:
        return api_response(success=False, code=400, message=str(ve))
    except Exception as e:
        db.session.rollback()
        logger.error(f'task attach error: {e}')
        return api_response(success=False, code=500, message='上传失败')
    from urllib.parse import quote
    ad = task_service.attachment_dict(att)
    ad['url'] = '/api/v1/mobile/tasks/file?path=' + quote(att.storage_path or '')
    return api_response(success=True, data=ad)


@api_v1_bp.route('/mobile/tasks/<int:tid>/attachments/<int:aid>', methods=['DELETE'])
@jwt_required()
def mobile_task_attach_delete(tid, aid):
    """薄壳:删除附件走共享 task_service.delete_attachment(仅上传者)。"""
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')
    from app.models.task import TaskAttachment
    att = TaskAttachment.query.filter_by(id=aid, task_id=tid, is_deleted=False).first()
    if not att:
        return api_response(success=False, code=404, message='附件不存在')
    from app.services import task_service
    try:
        task_service.delete_attachment(user, att)
    except ValueError as ve:
        return api_response(success=False, code=403, message=str(ve))
    except Exception as e:
        db.session.rollback()
        logger.error(f'task attach delete error: {e}')
        return api_response(success=False, code=500, message='删除失败')
    return api_response(success=True, data={'id': aid})


@api_v1_bp.route('/mobile/tasks/file', methods=['GET'])
def mobile_task_file():
    """任务附件下载代理(JWT header 或 ?token=)。镜像 chat,bucket=task。"""
    from flask_jwt_extended import decode_token
    from flask import Response
    token = request.headers.get('Authorization', '').replace('Bearer ', '') \
        or request.args.get('token', '')
    if not token:
        return api_response(success=False, code=401, message='缺少 token')
    try:
        decode_token(token)
    except Exception:
        return api_response(success=False, code=401, message='token 无效')
    rel_path = request.args.get('path', '')
    if not rel_path or '..' in rel_path:
        return api_response(success=False, code=400, message='非法路径')
    try:
        from app.utils.smart_storage_manager import get_smart_storage
        data = get_smart_storage().download_file(rel_path, bucket_type='task')
        if not data:
            return api_response(success=False, code=404, message='文件不存在')
        ext = (rel_path.rsplit('.', 1)[-1] or '').lower()
        ct = {
            'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
            'gif': 'image/gif', 'webp': 'image/webp', 'pdf': 'application/pdf',
            'mp4': 'video/mp4', 'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        }.get(ext, 'application/octet-stream')
        from urllib.parse import quote
        fn = quote(rel_path.split('/')[-1])
        return Response(data, mimetype=ct, headers={
            'Cache-Control': 'private, max-age=3600',
            'Content-Disposition': f"inline; filename*=UTF-8''{fn}",
        })
    except Exception as e:
        logger.error(f'mobile task file error: {e}', exc_info=True)
        return api_response(success=False, code=500, message=str(e))


@api_v1_bp.route('/mobile/tasks/<int:tid>/subtasks/<int:sid>/status', methods=['POST'])
@jwt_required()
def mobile_subtask_status(tid, sid):
    """薄壳:子任务开始/完成走共享 task_service.set_subtask_status。"""
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')
    t = Task.query.filter_by(id=tid, is_deleted=False).first()
    if not t or not _can_see(t, uid, user):
        return api_response(success=False, code=404, message='任务不存在或无权限')
    s = SubTask.query.filter_by(id=sid, task_id=tid, is_deleted=False).first()
    if not s:
        return api_response(success=False, code=404, message='子任务不存在')
    from app.services import task_service
    try:
        task_service.set_subtask_status(
            user, t, s, (request.get_json() or {}).get('action'))
    except ValueError as ve:
        return api_response(success=False, code=400, message=str(ve))
    except Exception as e:
        db.session.rollback()
        logger.error(f'subtask status error: {e}')
        return api_response(success=False, code=500, message='操作失败')
    return api_response(success=True, data={'id': s.id, 'status': s.status})


@api_v1_bp.route('/mobile/tasks/<int:tid>', methods=['DELETE'])
@jwt_required()
def mobile_task_delete(tid):
    """薄壳:删除任务走共享 task_service.delete_task。权限同 web _can_edit:仅创建人。"""
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')
    t = Task.query.filter_by(id=tid, is_deleted=False).first()
    if not t:
        return api_response(success=False, code=404, message='任务不存在')
    if t.creator_id != uid:
        return api_response(success=False, code=403, message='仅创建人可删除此任务')
    from app.services import task_service
    try:
        task_service.delete_task(user, t)
    except Exception as e:
        db.session.rollback()
        logger.error(f'task delete error: {e}')
        return api_response(success=False, code=500, message='删除失败')
    return api_response(success=True, data={'id': tid})


@api_v1_bp.route('/mobile/tasks/perspectives', methods=['GET'])
@jwt_required()
def mobile_task_perspectives():
    """切换视角:本人 + 直接下属(归属) + 其他可见账户,各含任务数/逾期数。"""
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')
    viewable = _viewable_account_ids(user)
    sub_ids = _subordinate_ids(user) & viewable
    us = {u.id: u for u in User.query.filter(User.id.in_(list(viewable))).all()}

    def _ent(u):
        nm = u.real_name or u.username
        st = _acct_stat(u.id)
        return {'id': u.id, 'name': nm, 'short': _initials(nm),
                'department': u.department or '',
                'count': st['count'], 'overdue': st['overdue']}

    me = _ent(user)
    me['is_self'] = True
    subs = [_ent(us[i]) for i in sub_ids if i in us and i != uid]
    other_ids = [i for i in viewable if i != uid and i not in sub_ids]
    others = [_ent(us[i]) for i in other_ids if i in us]
    subs.sort(key=lambda e: (-e['overdue'], -e['count'], e['name']))
    others.sort(key=lambda e: (-e['overdue'], -e['count'], e['name']))
    return api_response(success=True, data={
        'self': me,
        'subordinates': subs,
        'subordinate_total': sum(e['count'] for e in subs),
        'others': others,
    })


def _task_uo(tid):
    """取 (uid, user, task);返回 (None, err_resp) 表示失败。"""
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return None, api_response(success=False, code=401, message='用户不存在')
    t = Task.query.filter_by(id=tid, is_deleted=False).first()
    if not t or not _can_see(t, uid, user):
        return None, api_response(success=False, code=404, message='任务不存在或无权限')
    return (uid, user, t), None


@api_v1_bp.route('/mobile/tasks/<int:tid>/subtasks', methods=['POST'])
@jwt_required()
def mobile_subtask_create(tid):
    """薄壳:创建子任务走共享 task_service.create_subtask。"""
    ctx, err = _task_uo(tid)
    if err:
        return err
    _uid, user, t = ctx
    from app.services import task_service
    try:
        s = task_service.create_subtask(user, t, request.get_json() or {})
    except ValueError as ve:
        return api_response(success=False, code=400, message=str(ve))
    except Exception as e:
        db.session.rollback()
        logger.error(f'subtask create error: {e}')
        return api_response(success=False, code=500, message='创建失败')
    return api_response(success=True, data={'id': s.id})


@api_v1_bp.route('/mobile/tasks/<int:tid>/subtasks/<int:sid>', methods=['PATCH'])
@jwt_required()
def mobile_subtask_update(tid, sid):
    """薄壳:更新子任务走共享 task_service.update_subtask。"""
    ctx, err = _task_uo(tid)
    if err:
        return err
    _uid, user, t = ctx
    s = SubTask.query.filter_by(id=sid, task_id=tid, is_deleted=False).first()
    if not s:
        return api_response(success=False, code=404, message='子任务不存在')
    from app.services import task_service
    try:
        task_service.update_subtask(user, t, s, request.get_json() or {})
    except ValueError as ve:
        return api_response(success=False, code=400, message=str(ve))
    except Exception as e:
        db.session.rollback()
        logger.error(f'subtask update error: {e}')
        return api_response(success=False, code=500, message='更新失败')
    return api_response(success=True, data={'id': s.id})


@api_v1_bp.route('/mobile/tasks/<int:tid>/subtasks/<int:sid>', methods=['DELETE'])
@jwt_required()
def mobile_subtask_delete(tid, sid):
    """薄壳:删除子任务走共享 task_service.delete_subtask。"""
    ctx, err = _task_uo(tid)
    if err:
        return err
    _uid, user, t = ctx
    s = SubTask.query.filter_by(id=sid, task_id=tid, is_deleted=False).first()
    if not s:
        return api_response(success=False, code=404, message='子任务不存在')
    from app.services import task_service
    try:
        task_service.delete_subtask(user, s)
    except Exception as e:
        db.session.rollback()
        logger.error(f'subtask delete error: {e}')
        return api_response(success=False, code=500, message='删除失败')
    return api_response(success=True, data={'id': sid})


@api_v1_bp.route('/mobile/tasks/<int:tid>/subtasks/<int:sid>/milestone', methods=['POST'])
@jwt_required()
def mobile_subtask_milestone(tid, sid):
    """薄壳:里程碑确认/驳回走共享 task_service.confirm_milestone。"""
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')
    t = Task.query.filter_by(id=tid, is_deleted=False).first()
    if not t:
        return api_response(success=False, code=404, message='任务不存在')
    s = SubTask.query.filter_by(id=sid, task_id=tid, is_deleted=False).first()
    if not s:
        return api_response(success=False, code=404, message='子任务不存在')
    data = request.get_json() or {}
    from app.services import task_service
    try:
        s, msg = task_service.confirm_milestone(
            user, t, s, data.get('action'), data.get('comment') or '')
    except ValueError as ve:
        return api_response(success=False, code=400, message=str(ve))
    except Exception as e:
        db.session.rollback()
        logger.error(f'milestone confirm error: {e}')
        return api_response(success=False, code=500, message='操作失败')
    return api_response(success=True, data={
        'id': s.id, 'milestone_status': s.milestone_status, 'message': msg})


@api_v1_bp.route('/mobile/tasks/<int:tid>/resubmit-review', methods=['POST'])
@jwt_required()
def mobile_task_resubmit(tid):
    """薄壳:被驳回后重新提交会审走共享 task_service.resubmit_review。
    权限同 web:创建人或负责人。"""
    uid = int(get_jwt_identity())
    user = User.query.get(uid)
    if not user:
        return api_response(success=False, code=401, message='用户不存在')
    t = Task.query.filter_by(id=tid, is_deleted=False).first()
    if not t:
        return api_response(success=False, code=404, message='任务不存在')
    if t.creator_id != uid and t.assignee_id != uid:
        return api_response(success=False, code=403, message='仅创建人或负责人可重新提交')
    from app.services import task_service
    try:
        task_service.resubmit_review(user, t)
    except ValueError as ve:
        return api_response(success=False, code=400, message=str(ve))
    except Exception as e:
        db.session.rollback()
        logger.error(f'resubmit review error: {e}')
        return api_response(success=False, code=500, message='操作失败')
    return api_response(success=True, data={
        'status': t.status, 'status_label': _status_label(t.status)})


# ─── 通知中心(站内 Message,任务类)──────────────────────────────

def _notif_base(uid):
    from app.models.message import Message
    return Message.query.filter(
        Message.recipient_id == uid,
        Message.related_object_type == 'task',
    )


def _notif_row(m):
    return {
        'id': m.id,
        'type': m.message_type,
        'title': m.title or '',
        'content': m.content or '',
        'task_id': m.related_object_id,
        'is_read': bool(m.is_read),
        'created_at': m.created_at.isoformat() if m.created_at else None,
    }


@api_v1_bp.route('/mobile/notifications', methods=['GET'])
@jwt_required()
def mobile_notifications():
    uid = int(get_jwt_identity())
    if not User.query.get(uid):
        return api_response(success=False, code=401, message='用户不存在')
    from app.models.message import Message
    page = max(1, request.args.get('page', 1, type=int))
    per = min(50, max(1, request.args.get('per', 20, type=int)))
    q = _notif_base(uid).order_by(Message.created_at.desc())
    total = q.count()
    rows = q.offset((page - 1) * per).limit(per).all()
    return api_response(success=True, data={
        'items': [_notif_row(m) for m in rows],
        'total': total, 'page': page, 'per': per,
    })


@api_v1_bp.route('/mobile/notifications/unread-count', methods=['GET'])
@jwt_required()
def mobile_notifications_unread():
    uid = int(get_jwt_identity())
    if not User.query.get(uid):
        return api_response(success=False, code=401, message='用户不存在')
    from app.models.message import Message
    n = _notif_base(uid).filter(Message.is_read == False).count()  # noqa: E712
    return api_response(success=True, data={'count': n})


@api_v1_bp.route('/mobile/notifications/<int:mid>/read', methods=['POST'])
@jwt_required()
def mobile_notification_read(mid):
    uid = int(get_jwt_identity())
    if not User.query.get(uid):
        return api_response(success=False, code=401, message='用户不存在')
    from app.models.message import Message
    m = Message.query.filter_by(id=mid, recipient_id=uid).first()
    if not m:
        return api_response(success=False, code=404, message='通知不存在')
    if not m.is_read:
        m.is_read = True
        db.session.commit()
    return api_response(success=True, data={'id': mid})


@api_v1_bp.route('/mobile/notifications/read-all', methods=['POST'])
@jwt_required()
def mobile_notifications_read_all():
    uid = int(get_jwt_identity())
    if not User.query.get(uid):
        return api_response(success=False, code=401, message='用户不存在')
    from app.models.message import Message
    _notif_base(uid).filter(Message.is_read == False).update(  # noqa: E712
        {Message.is_read: True}, synchronize_session=False)
    db.session.commit()
    return api_response(success=True, data={})


@api_v1_bp.route('/mobile/tasks/<int:tid>/notifications/read', methods=['POST'])
@jwt_required()
def mobile_task_notifs_read(tid):
    """打开任务详情时,把该任务相关的未读站内通知标已读(数字随之减)。"""
    uid = int(get_jwt_identity())
    if not User.query.get(uid):
        return api_response(success=False, code=401, message='用户不存在')
    from app.models.message import Message
    n = _notif_base(uid).filter(
        Message.related_object_id == tid,
        Message.is_read == False,  # noqa: E712
    ).update({Message.is_read: True}, synchronize_session=False)
    db.session.commit()
    return api_response(success=True, data={'cleared': n})
