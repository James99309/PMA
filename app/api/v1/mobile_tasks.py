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


def _task_row(t):
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
        'updated_at': t.updated_at.isoformat() if t.updated_at else None,
    }


def _base_q():
    return Task.query.filter(Task.is_deleted == False)  # noqa: E712


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

    if tab == 'shared':
        rows = _base_q().filter(
            Task.assignee_id != uid, Task.creator_id != uid
        ).all()
        rows = [t for t in rows if uid in (t.shared_with_users or [])]
    else:
        q = _tab_query(uid, tab)
        rows = q.all()

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

    # 计数(tab badge + hero) — 轻量
    mine_all = _base_q().filter(Task.assignee_id == uid).all()
    created_n = _base_q().filter(Task.creator_id == uid).count()
    shared_cands = _base_q().filter(
        Task.assignee_id != uid, Task.creator_id != uid
    ).all()
    shared_n = sum(1 for t in shared_cands if uid in (t.shared_with_users or []))
    from app.models.task import TaskReviewer
    review_n = _base_q().filter(
        Task.status == 'pending_review',
        Task.id.in_(db.session.query(TaskReviewer.task_id).filter(TaskReviewer.reviewer_id == uid)),
    ).count()
    in_progress_n = sum(1 for t in mine_all if t.status == 'in_progress')
    overdue_n = sum(1 for t in mine_all if _is_overdue(t))

    return api_response(success=True, data={
        'items': [_task_row(t) for t in page_rows],
        'total': total,
        'page': page,
        'per': per,
        'counts': {
            'mine': len(mine_all),
            'created': created_n,
            'shared': shared_n,
            'review': review_n,
            'in_progress': in_progress_n,
            'overdue': overdue_n,
        },
    })
