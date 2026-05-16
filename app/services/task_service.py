# -*- coding: utf-8 -*-
"""任务写业务服务(鉴权无关) — web 路由与 mobile API 共用单一来源

从 app/views/task.py 的厚路由抽出,**忠实保留原行为与副作用顺序**:
通知 / 积分 / 跨区推送 / 工作项记录 全部经共享引擎在此统一触发,
使 web 与 mobile 行为 100% 一致(消除平行实现漂移)。

约定:
- `actor` 传 User 对象(web 传 current_user,mobile 传 User.query.get(uid))
- **鉴权由调用方(web 路由 / mobile 端点)在边缘做**,本服务只管业务+副作用
- 校验失败抛 ValueError,调用方映射 400
- 本服务自管 commit(与原 web 每路由 commit 一致)
"""
import logging
from datetime import datetime, date

from app import db
from app.models.task import Task, TaskReply, TaskReviewer, get_local_time
from app.models.user import User
from app.services import notification_service as notif

logger = logging.getLogger(__name__)


def _record_activity(action, t, actor):
    try:
        from app.utils.work_item_recorder import record_task_activity
        record_task_activity(action, t.id, t.title, actor,
                             project_id=t.project_id, customer_id=t.customer_id)
    except Exception as e:
        logger.warning(f'task日志记录失败: {e}')


def _award(user_id, code, t, source_type='task'):
    try:
        from app.services.points_service import award_points
        award_points(user_id=user_id, behavior_code=code,
                     source_type=source_type, source_id=t.id, context=t.title)
    except Exception as e:
        logger.warning(f'{code}积分发放失败: {e}')


def create_task(actor, data):
    """创建任务(忠实抽取 web create_task)。actor=User。返回 Task。"""
    title = (data.get('title') or '').strip()
    if not title:
        raise ValueError('任务标题不能为空')
    assignee_id = data.get('assignee_id')
    if not assignee_id:
        raise ValueError('请选择指派人')

    t = Task(
        title=title,
        description=(data.get('description') or '').strip() or None,
        creator_id=actor.id,
        assignee_id=int(assignee_id),
        priority=data.get('priority', 'normal'),
        external_link=(data.get('external_link') or '').strip() or None,
        external_link_label=(data.get('external_link_label') or '').strip() or None,
        project_id=data.get('project_id') or None,
        quotation_id=data.get('quotation_id') or None,
        customer_id=data.get('customer_id') or None,
    )
    shared = data.get('shared_with_users')
    if shared and isinstance(shared, list):
        t.shared_with_users = [int(u) for u in shared if u]

    due_s = data.get('due_date')
    if due_s:
        try:
            t.due_date = datetime.fromisoformat(due_s)
        except (ValueError, TypeError):
            pass
    start_s = data.get('start_date')
    if start_s:
        try:
            t.start_date = date.fromisoformat(start_s[:10])
            t.status = 'in_progress' if t.start_date <= date.today() else 'pending'
        except (ValueError, TypeError):
            t.status = 'in_progress'
    else:
        t.status = 'in_progress'
    if t.due_date:
        t.calendar_date = t.due_date.date()

    db.session.add(t)
    db.session.flush()

    reviewer_ids = data.get('reviewer_ids') or []
    if not reviewer_ids and data.get('reviewer_id'):
        reviewer_ids = [data['reviewer_id']]
    for rid in reviewer_ids:
        db.session.add(TaskReviewer(task_id=t.id, reviewer_id=int(rid)))

    # 通知被指派人 + 协助人(经统一通知服务)
    notif.notify_task_assigned(actor.id, t.assignee_id, t)
    for uid in (t.shared_with_users or []):
        notif.notify_task_assigned(actor.id, uid, t)

    _award(actor.id, 'task_create', t)
    db.session.commit()

    # commit 后:工作项记录 + 跨区推送(与 web 顺序一致)
    _record_activity('create', t, actor)
    if t.assignee_id != actor.id:
        try:
            from app.services.cross_sync_service import is_cross_sync_enabled, push_task_to_peer
            if is_cross_sync_enabled():
                a = User.query.get(t.assignee_id)
                if a and a.email:
                    push_task_to_peer(
                        a.email, actor.real_name or actor.username, t.title,
                        t.due_date.strftime('%Y-%m-%d') if t.due_date else None)
        except Exception as e:
            logger.warning(f'跨系统任务推送失败: {e}')
    return t


def complete_task(actor, t):
    """完成任务;审计类任务进入待审核并通知审计人(忠实抽取)。返回 Task。"""
    if t.task_reviewers and not t.review_status:
        t.status = 'pending_review'
        t.review_status = 'pending_review'
        for tr in t.task_reviewers:
            tr.status = 'pending'
            tr.reviewed_at = None
            tr.comment = None
            notif.notify_task_assigned(actor.id, tr.reviewer_id, t)
        db.session.commit()
        return t

    t.status = 'completed'
    t.completed_at = get_local_time()
    notif.notify_task_completed(actor.id, t.creator_id, t)
    _award(t.assignee_id or actor.id, 'task_complete', t)
    db.session.commit()
    return t


def cancel_task(actor, t):
    t.status = 'cancelled'
    db.session.commit()
    return t


def pause_task(actor, t, reason):
    reason = (reason or '').strip()
    if not reason:
        raise ValueError('请填写暂停理由')
    t.status = 'paused'
    if t.task_reviewers:
        for tr in t.task_reviewers:
            notif.notify_task_custom(
                actor.id, tr.reviewer_id, '任务已暂停',
                f'{t.title} - 暂停理由: {reason}', t.id)
    try:
        db.session.add(TaskReply(
            task_id=t.id, author_id=actor.id, content=f'[任务暂停] {reason}'))
    except Exception as e:
        logger.warning(f'记录暂停理由失败: {e}')
    db.session.commit()
    return t


def back_to_pending(actor, t):
    """改回待开始(mobile QuickStatus 用;web 无独立路由,行为最小)。"""
    t.status = 'pending'
    db.session.commit()
    return t


def change_status(actor, t, to, reason=''):
    """mobile QuickStatus 统一入口 → 分派到对应写动作,复用同一逻辑。"""
    if to in ('completed', 'pending_review'):
        return complete_task(actor, t)
    if to == 'cancelled':
        return cancel_task(actor, t)
    if to == 'paused':
        return pause_task(actor, t, reason)
    if to == 'pending':
        return back_to_pending(actor, t)
    raise ValueError('非法目标状态')


def add_reply(actor, t, content, subtask_id=None, reply_type='comment'):
    """添加评论/进展(忠实抽取 add_reply)。返回 TaskReply。"""
    content = (content or '').strip()
    if not content:
        raise ValueError('回复内容不能为空')
    if reply_type not in ('comment', 'update'):
        reply_type = 'comment'
    r = TaskReply(task_id=t.id, subtask_id=subtask_id, author_id=actor.id,
                  content=content, reply_type=reply_type)
    db.session.add(r)
    db.session.commit()
    _record_activity('reply', t, actor)
    return r


def review_task(actor, t, action, comment=''):
    """会审(并行)同意/驳回(忠实抽取 review_task)。返回 (Task, msg_text)。"""
    my = next((r for r in t.task_reviewers if r.reviewer_id == actor.id), None)
    if not my:
        raise ValueError('您不是此任务的审计对象')
    if t.review_status != 'pending_review':
        raise ValueError('任务不在待审核状态')
    if my.status != 'pending':
        raise ValueError('您已完成审核')
    comment = (comment or '').strip()

    if action == 'approve':
        my.status = 'approved'
        my.comment = comment or None
        my.reviewed_at = get_local_time()
        if all(r.status == 'approved' for r in t.task_reviewers):
            t.review_status = 'approved'
            t.reviewed_at = get_local_time()
            t.status = 'completed'
            t.completed_at = get_local_time()
            msg_text = '任务审核通过'
            _award(t.assignee_id, 'task_complete', t)
            for r in t.task_reviewers:
                _award(r.reviewer_id, 'task_review_approved', t, source_type='task_review')
        else:
            msg_text = '您已通过,等待其他审计人'
    elif action == 'reject':
        if not comment:
            raise ValueError('驳回时必须填写意见')
        my.status = 'rejected'
        my.comment = comment
        my.reviewed_at = get_local_time()
        t.review_status = 'rejected'
        t.reviewed_at = get_local_time()
        t.status = 'in_progress'
        msg_text = '任务审核被驳回'
    else:
        raise ValueError('无效的操作')

    if t.review_status in ('approved', 'rejected'):
        notif.notify_task_completed(actor.id, t.assignee_id, t)
    db.session.commit()
    return t, msg_text
