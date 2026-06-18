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

from flask_babel import gettext as _

from app import db
from app.models.task import Task, TaskReply, TaskReviewer, get_local_time
from app.models.user import User
from app.services import notification_service as notif
from app.services.translation_service import normalize_region_text

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
    title = normalize_region_text((data.get('title') or '').strip())
    if not title:
        raise ValueError('任务标题不能为空')
    assignee_id = data.get('assignee_id')
    if not assignee_id:
        raise ValueError('请选择指派人')

    # 任务类型(日常/岗位):越权选别岗位类型时回落 general
    from app.helpers.task_types import is_allowed_type
    task_type = (data.get('task_type') or 'general').strip() or 'general'
    if not is_allowed_type(actor, task_type):
        task_type = 'general'

    t = Task(
        title=title,
        description=normalize_region_text((data.get('description') or '').strip()) or None,
        creator_id=actor.id,
        assignee_id=int(assignee_id),
        priority=data.get('priority', 'normal'),
        external_link=(data.get('external_link') or '').strip() or None,
        external_link_label=(data.get('external_link_label') or '').strip() or None,
        project_id=data.get('project_id') or None,
        quotation_id=data.get('quotation_id') or None,
        customer_id=data.get('customer_id') or None,
        task_type=task_type,
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
    # 需审核类型(如招聘到岗)必须指定审核人,否则完成后无法计入绩效
    from app.helpers.task_types import requires_review as _req_rev
    if _req_rev(task_type) and not reviewer_ids:
        db.session.rollback()
        raise ValueError('该任务类型需指定审核人')
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
            notif.notify_task_review_request(actor.id, tr.reviewer_id, t)
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
    reason = normalize_region_text((reason or '').strip())
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
            task_id=t.id, author_id=actor.id, content=f'[任务暂停] {reason}', reply_type='update'))
    except Exception as e:
        logger.warning(f'记录暂停理由失败: {e}')
    db.session.commit()
    return t


def resume_task(actor, t):
    """从暂停恢复为进行中。"""
    if t.status != 'paused':
        return t
    t.status = 'in_progress'
    try:
        db.session.add(TaskReply(task_id=t.id, author_id=actor.id, content='[任务恢复]', reply_type='update'))
    except Exception as e:
        logger.warning(f'记录任务恢复失败: {e}')
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


def delete_reply(actor, reply):
    """软删除评论/进展。权限:作者本人 / 任务创建人 / 管理员。"""
    t = Task.query.get(reply.task_id)
    is_admin = getattr(actor, 'role', None) in ('admin', 'ceo')
    if reply.author_id != actor.id and not is_admin and not (t and t.creator_id == actor.id):
        raise ValueError('无权删除此评论')
    reply.is_deleted = True
    db.session.commit()
    return reply


def add_reply(actor, t, content, subtask_id=None, reply_type='comment'):
    """添加评论/进展(忠实抽取 add_reply)。返回 TaskReply。"""
    content = normalize_region_text((content or '').strip())
    if not content:
        raise ValueError('回复内容不能为空')
    if reply_type not in ('comment', 'update'):
        reply_type = 'comment'
    r = TaskReply(task_id=t.id, subtask_id=subtask_id, author_id=actor.id,
                  content=content, reply_type=reply_type)
    db.session.add(r)
    sub = None
    if subtask_id:
        sub = next((s for s in (t.subtasks or []) if s.id == subtask_id), None)
    notif.notify_task_reply(actor.id, t, content, subtask=sub)
    db.session.commit()
    _record_activity('reply', t, actor)
    return r


# 三档评价 → 加权权重(低于/符合/超出预期)
_RATING_WEIGHT = {'below': 0.5, 'meet': 1.0, 'exceed': 1.5}


def review_task(actor, t, action, comment='', rating=None):
    """会审(并行)评价/驳回。返回 (Task, msg_text)。
    通过(approve)须带三档评价 rating(below/meet/exceed);低于预期(below)须填原因。"""
    my = next((r for r in t.task_reviewers if r.reviewer_id == actor.id), None)
    if not my:
        raise ValueError('您不是此任务的审计对象')
    if t.review_status != 'pending_review':
        raise ValueError('任务不在待审核状态')
    if my.status != 'pending':
        raise ValueError('您已完成审核')
    comment = normalize_region_text((comment or '').strip())

    if action == 'approve':
        rating = (rating or '').strip()
        if rating not in _RATING_WEIGHT:
            raise ValueError('请选择评价(低于预期/符合预期/超出预期)')
        if rating == 'below' and not comment:
            raise ValueError('低于预期必须填写原因')
        my.status = 'approved'
        my.rating = rating
        my.comment = comment or None
        my.reviewed_at = get_local_time()
        if all(r.status == 'approved' for r in t.task_reviewers):
            # 会审取各审计人评价权重均值(无评价兜底 1.0,兼容旧数据)
            ws = [_RATING_WEIGHT.get(r.rating, 1.0) for r in t.task_reviewers]
            t.review_score = round(sum(ws) / len(ws), 3) if ws else 1.0
            t.review_status = 'approved'
            t.reviewed_at = get_local_time()
            t.status = 'completed'
            t.completed_at = get_local_time()
            msg_text = '任务审核通过'
            _award(t.assignee_id, 'task_complete', t)
            for r in t.task_reviewers:
                _award(r.reviewer_id, 'task_review_approved', t, source_type='task_review')
        else:
            msg_text = '您已评价,等待其他审计人'
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


# ─── 编辑 (忠实抽取 web update_task,web/mobile 共用) ──────────────────


def _fmt_dt(v):
    if not v:
        return _('（无）')
    if hasattr(v, 'strftime'):
        return v.strftime('%Y-%m-%d %H:%M') if isinstance(v, datetime) else v.strftime('%Y-%m-%d')
    return str(v)


def _user_names(user_ids):
    """user_id 列表 → 'A、B、C';找不到用 'ID:n' 兜底。"""
    if not user_ids:
        return _('（无）')
    users = User.query.filter(User.id.in_(list(user_ids))).all()
    name_map = {u.id: (u.real_name or u.username) for u in users}
    return '、'.join(name_map.get(uid, f'ID:{uid}') for uid in user_ids)


def _build_task_change_log(t, before):
    """对比修改前后关键字段,返回多行变更描述。空列表=无变更。"""
    PRIORITY_LABELS = {'normal': _('普通'), 'high': _('高'),
                       'urgent': _('紧急'), 'low': _('低')}
    lines = []

    def diff(label, old, new, formatter=None):
        if old == new:
            return
        f = formatter or (lambda v: v if v not in (None, '') else _('（无）'))
        lines.append(f'{label}：{f(old)} → {f(new)}')

    diff(_('标题'), before['title'], t.title)
    diff(_('描述'), before['description'], t.description)
    diff(_('优先级'), before['priority'], t.priority,
         lambda v: PRIORITY_LABELS.get(v, v) if v else _('（无）'))
    diff(_('截止时间'), before['due_date'], t.due_date, _fmt_dt)
    diff(_('开始时间'), before['start_date'], t.start_date, _fmt_dt)
    if before['project_id'] != t.project_id:
        old = before['project_name'] or _('（无）')
        new = (t.project.project_name if t.project else _('（无）'))
        lines.append(f"{_('关联项目')}：{old} → {new}")
    if before['quotation_id'] != t.quotation_id:
        old = before['quotation_number'] or _('（无）')
        new = (t.quotation.quotation_number if t.quotation else _('（无）'))
        lines.append(f"{_('关联报价单')}：{old} → {new}")
    if before['assignee_id'] != t.assignee_id:
        ids = [i for i in [before['assignee_id'], t.assignee_id] if i]
        name_map = {u.id: (u.real_name or u.username)
                    for u in User.query.filter(User.id.in_(ids)).all()} if ids else {}
        old_name = name_map.get(before['assignee_id'], _('（无）')) if before['assignee_id'] else _('（无）')
        new_name = name_map.get(t.assignee_id, _('（无）')) if t.assignee_id else _('（无）')
        lines.append(f"{_('负责人')}：{old_name} → {new_name}")
    if set(before['shared_with_users']) != set(t.shared_with_users or []):
        lines.append(f"{_('协助人')}：{_user_names(before['shared_with_users'])} → "
                     f"{_user_names(t.shared_with_users or [])}")
    new_reviewer_ids = sorted(r.reviewer_id for r in t.task_reviewers)
    if before['reviewer_ids'] != new_reviewer_ids:
        lines.append(f"{_('审计人')}：{_user_names(before['reviewer_ids'])} → "
                     f"{_user_names(new_reviewer_ids)}")
    return lines


def update_task(actor, t, data):
    """编辑任务(忠实抽取 web update_task)。actor=User,t=Task。返回 Task。

    校验由调用方(web/mobile 路由)在边缘做(_can_edit);本服务只管业务+
    变更日志副作用,自管 commit(与原 web 行为一致)。
    """
    before = {
        'title': t.title,
        'description': t.description,
        'priority': t.priority,
        'due_date': t.due_date,
        'start_date': t.start_date,
        'assignee_id': t.assignee_id,
        'shared_with_users': list(t.shared_with_users or []),
        'reviewer_ids': sorted(r.reviewer_id for r in t.task_reviewers),
        'project_id': t.project_id,
        'project_name': t.project.project_name if t.project else None,
        'quotation_id': t.quotation_id,
        'quotation_number': t.quotation.quotation_number if t.quotation else None,
    }

    if 'title' in data:
        t.title = normalize_region_text((data['title'] or '').strip())
    if 'description' in data:
        t.description = normalize_region_text((data['description'] or '').strip()) or None
    # priority=枚举, external_link=URL → 不翻译
    for field in ['priority', 'external_link', 'external_link_label']:
        if field in data:
            setattr(t, field, (data[field] or '').strip() or None)

    if 'task_type' in data:
        from app.helpers.task_types import is_allowed_type
        tt = (data['task_type'] or 'general').strip() or 'general'
        t.task_type = tt if is_allowed_type(actor, tt) else 'general'

    for fk_field in ['assignee_id', 'project_id', 'quotation_id', 'customer_id']:
        if fk_field in data:
            setattr(t, fk_field, data[fk_field] or None)

    if 'reviewer_ids' in data:
        new_ids = set(int(rid) for rid in (data['reviewer_ids'] or []) if rid)
        old_ids = set(r.reviewer_id for r in t.task_reviewers)
        for tr in list(t.task_reviewers):
            if tr.reviewer_id not in new_ids:
                db.session.delete(tr)
        for rid in new_ids - old_ids:
            db.session.add(TaskReviewer(task_id=t.id, reviewer_id=rid))

    if 'shared_with_users' in data:
        t.shared_with_users = [int(uid) for uid in (data['shared_with_users'] or []) if uid]

    if 'due_date' in data:
        if data['due_date']:
            try:
                t.due_date = datetime.fromisoformat(data['due_date'])
                t.calendar_date = t.due_date.date()
            except (ValueError, TypeError):
                pass
        else:
            t.due_date = None
            t.calendar_date = None

    if 'start_date' in data:
        if data['start_date']:
            try:
                t.start_date = date.fromisoformat(data['start_date'][:10])
                if t.status == 'pending' and t.start_date <= date.today():
                    t.status = 'in_progress'
                elif t.status == 'in_progress' and t.start_date > date.today():
                    t.status = 'pending'
            except (ValueError, TypeError):
                pass
        else:
            t.start_date = None
            if t.status == 'pending':
                t.status = 'in_progress'

    if 'status' in data and data['status'] in ('pending', 'in_progress', 'paused'):
        t.status = data['status']

    # 需审核类型必须有审核人(改类型/清空审核人时拦截)
    from app.helpers.task_types import requires_review as _req_rev
    if _req_rev(t.task_type) and not t.task_reviewers:
        db.session.rollback()
        raise ValueError('该任务类型需指定审核人')

    change_lines = _build_task_change_log(t, before)
    if change_lines:
        db.session.add(TaskReply(
            task_id=t.id, subtask_id=None, author_id=actor.id,
            content='\n'.join(change_lines), reply_type='update',
        ))

    # 通知:新指派人 + 新增协助人(审核人不在此通知,仅完成发起审批流程时才通知)
    if t.assignee_id and t.assignee_id != before['assignee_id'] and t.assignee_id != actor.id:
        notif.notify_task_assigned(actor.id, t.assignee_id, t)
    for uid in (set(t.shared_with_users or []) - set(before['shared_with_users'] or [])):
        if uid != actor.id:
            notif.notify_task_assigned(actor.id, uid, t)

    db.session.commit()
    return t


# ─── 附件 (忠实抽取 web upload/delete_attachment,web/mobile 共用) ──────


def add_attachment(actor, t, file, filename, file_size, file_ext, subtask_id=None):
    """上传任务附件。actor=User,t=Task。返回 TaskAttachment。失败抛 ValueError。"""
    from app.models.task import TaskAttachment
    from app.utils.smart_storage_manager import get_smart_storage
    result = get_smart_storage().upload_file(
        object_id=t.id, file=file, filename=filename,
        file_type='attachment', bucket_type='task', business_type='task')
    if not result:
        raise ValueError(_('文件上传失败'))
    att = TaskAttachment(
        task_id=t.id, subtask_id=subtask_id, filename=filename,
        storage_path=result.get('storage_path', ''), file_size=file_size,
        file_type=file_ext, uploaded_by=actor.id)
    db.session.add(att)
    db.session.commit()
    return att


def delete_attachment(actor, att):
    """删除任务附件(含存储文件)。仅上传者本人;否则抛 ValueError。"""
    if att.uploaded_by != actor.id:
        raise ValueError(_('只能删除自己上传的附件'))
    if att.storage_path:
        try:
            from app.utils.smart_storage_manager import get_smart_storage
            get_smart_storage().delete_file(att.storage_path, bucket_type='task')
        except Exception as e:
            logger.warning(f'删除附件文件失败: {e}')
    db.session.delete(att)
    db.session.commit()


def set_subtask_status(actor, t, subtask, action):
    """子任务开始/完成(忠实抽取 web update_subtask_status)。
    里程碑完成→待确认并经统一通知服务通知确认人;普通完成→发积分。"""
    today = date.today()
    if action == 'start':
        start = subtask.start_date or t.start_date
        if start and today < start:
            raise ValueError(_('该节点尚未到开始日期（%(date)s）',
                               date=start.strftime('%m/%d')))
        subtask.status = 'in_progress'
    elif action == 'complete':
        if subtask.is_milestone and subtask.milestone_reviewers:
            subtask.status = 'completed'
            subtask.completed_at = get_local_time()
            subtask.milestone_status = 'pending_confirmation'
            try:
                for mr in subtask.milestone_reviewers:
                    mr.status = 'pending'
                    mr.reviewed_at = None
                    mr.comment = None
                    notif.notify_task_assigned(actor.id, mr.reviewer_id, t)
            except Exception as e:
                logger.warning(f'发送里程碑通知失败: {e}')
        else:
            subtask.status = 'completed'
            subtask.completed_at = get_local_time()
            try:
                from app.services.points_service import award_points
                uid = subtask.assignee_id or t.assignee_id
                award_points(user_id=uid, behavior_code='subtask_complete',
                             source_type='subtask', source_id=subtask.id,
                             context=subtask.title)
            except Exception as _e:
                logger.warning(f'subtask_complete积分发放失败: {_e}')
    else:
        raise ValueError(_('无效操作'))
    db.session.commit()
    return subtask


def create_subtask(actor, t, data):
    """创建子任务/节点(忠实抽取 web create_subtask)。返回 SubTask。"""
    from app.models.subtask import SubTask, MilestoneReviewer
    title = normalize_region_text((data.get('title') or '').strip())
    if not title:
        raise ValueError(_('节点标题不能为空'))
    is_milestone = bool(data.get('is_milestone', False))
    max_order = db.session.query(db.func.max(SubTask.sort_order)).filter_by(
        task_id=t.id, is_deleted=False).scalar() or 0
    s = SubTask(
        task_id=t.id, title=title,
        description=normalize_region_text((data.get('description') or '').strip()) or None,
        assignee_id=data.get('assignee_id') or None,
        is_milestone=is_milestone, sort_order=max_order + 1)
    if data.get('start_date'):
        try:
            s.start_date = date.fromisoformat(data['start_date'][:10])
            s.status = 'in_progress' if s.start_date <= date.today() else 'pending'
        except (ValueError, TypeError):
            pass
    else:
        s.status = 'in_progress'
    if data.get('due_date'):
        try:
            s.due_date = date.fromisoformat(data['due_date'][:10])
        except (ValueError, TypeError):
            pass
    if is_milestone:
        s.milestone_criteria = (data.get('milestone_criteria') or '').strip() or None
    db.session.add(s)
    db.session.flush()
    if is_milestone:
        cids = data.get('milestone_confirmer_ids') or []
        if not cids and data.get('milestone_confirmer_id'):
            cids = [data['milestone_confirmer_id']]
        for cid in cids:
            db.session.add(MilestoneReviewer(subtask_id=s.id, reviewer_id=int(cid)))
    db.session.commit()
    _record_activity('subtask', t, actor)
    # 派子任务 → 通知子任务执行人(站内+站外,与派任务一致)
    if s.assignee_id and s.assignee_id != actor.id:
        notif.notify_task_assigned(actor.id, s.assignee_id, t)
        db.session.commit()
    return s


def update_subtask(actor, t, s, data):
    """更新子任务(忠实抽取 web update_subtask)。返回 SubTask。"""
    from app.models.subtask import MilestoneReviewer
    for field in ['title', 'description']:
        if field in data:
            setattr(s, field, normalize_region_text((data[field] or '').strip()) or None)
    if 'assignee_id' in data:
        s.assignee_id = data['assignee_id'] or None
    if 'start_date' in data:
        try:
            s.start_date = date.fromisoformat(data['start_date'][:10]) if data['start_date'] else None
        except (ValueError, TypeError):
            pass
    if 'due_date' in data:
        try:
            s.due_date = date.fromisoformat(data['due_date'][:10]) if data['due_date'] else None
        except (ValueError, TypeError):
            pass
    if 'is_milestone' in data:
        s.is_milestone = bool(data['is_milestone'])
    if 'milestone_criteria' in data:
        s.milestone_criteria = normalize_region_text((data['milestone_criteria'] or '').strip()) or None
    if 'milestone_confirmer_ids' in data:
        new_ids = set(int(c) for c in (data['milestone_confirmer_ids'] or []) if c)
        old_ids = set(r.reviewer_id for r in s.milestone_reviewers)
        for mr in list(s.milestone_reviewers):
            if mr.reviewer_id not in new_ids:
                db.session.delete(mr)
        for cid in new_ids - old_ids:
            db.session.add(MilestoneReviewer(subtask_id=s.id, reviewer_id=cid))
    db.session.commit()
    return s


def delete_subtask(actor, s):
    """软删除子任务(忠实抽取 web delete_subtask)。"""
    s.is_deleted = True
    db.session.commit()


def confirm_milestone(actor, t, s, action, comment=''):
    """里程碑确认/驳回(会审并行,忠实抽取 web confirm_milestone)。
    返回 (SubTask, msg_text)。校验失败抛 ValueError。"""
    if not s.is_milestone:
        raise ValueError(_('此节点不是里程碑'))
    my = next((r for r in s.milestone_reviewers if r.reviewer_id == actor.id), None)
    if not my:
        raise ValueError(_('您不是此里程碑的确认人'))
    if s.milestone_status != 'pending_confirmation':
        raise ValueError(_('里程碑不在待确认状态'))
    if my.status != 'pending':
        raise ValueError(_('您已完成确认'))
    comment = normalize_region_text((comment or '').strip())
    if action == 'confirm':
        my.status = 'confirmed'
        my.comment = comment or None
        my.reviewed_at = get_local_time()
        if all(r.status == 'confirmed' for r in s.milestone_reviewers):
            s.milestone_status = 'confirmed'
            s.milestone_confirmed_at = get_local_time()
            try:
                from app.services.points_service import award_points
                award_points(user_id=s.assignee_id or t.assignee_id,
                             behavior_code='task_milestone_confirmed',
                             source_type='subtask', source_id=s.id, context=s.title)
            except Exception as e:
                logger.warning(f'task_milestone_confirmed积分发放失败: {e}')
            msg_text = _('里程碑已确认通过')
        else:
            msg_text = _('您已确认，等待其他确认人')
    elif action == 'reject':
        if not comment:
            raise ValueError(_('驳回时必须填写意见'))
        my.status = 'rejected'
        my.comment = comment
        my.reviewed_at = get_local_time()
        s.milestone_status = 'rejected'
        s.milestone_confirmed_at = get_local_time()
        s.status = 'in_progress'
        msg_text = _('里程碑已被驳回')
    else:
        raise ValueError(_('无效操作'))
    if s.milestone_status in ('confirmed', 'rejected'):
        notify_uid = s.assignee_id or t.assignee_id
        notif.notify_task_assigned(actor.id, notify_uid, t)
    db.session.commit()
    return s, msg_text


def resubmit_review(actor, t):
    """被驳回后重新提交会审(忠实抽取 web resubmit_review)。返回 Task。"""
    if t.review_status != 'rejected':
        raise ValueError(_('任务不在被驳回状态'))
    t.status = 'pending_review'
    t.review_status = 'pending_review'
    t.reviewed_at = None
    for tr in t.task_reviewers:
        tr.status = 'pending'
        tr.comment = None
        tr.reviewed_at = None
        notif.notify_task_review_request(actor.id, tr.reviewer_id, t)
    db.session.commit()
    return t


def delete_task(actor, t):
    """彻底删除任务(含附件存储文件,忠实抽取 web delete_task)。
    级联删除 attachments + replies。actor 由调用方做权限校验(_can_edit)。"""
    from app.models.task import TaskAttachment
    attachments = TaskAttachment.query.filter_by(task_id=t.id).all()
    if attachments:
        from app.utils.smart_storage_manager import get_smart_storage
        storage = get_smart_storage()
        for att in attachments:
            if att.storage_path:
                try:
                    storage.delete_file(att.storage_path, bucket_type='task')
                except Exception as e:
                    logger.warning(f'删除附件文件失败: {e}')
    db.session.delete(t)
    db.session.commit()


def attachment_dict(a, nas_ok=None):
    """附件序列化(与 web 任务详情一致)。"""
    return {
        'id': a.id,
        'filename': a.filename,
        'storage_path': a.storage_path,
        'file_size': a.file_size,
        'file_type': a.file_type,
        'uploaded_by': a.uploaded_by,
        'uploader_name': (a.uploader.real_name or a.uploader.username) if a.uploader else None,
        'subtask_id': a.subtask_id,
        'subtask_title': a.subtask.title if a.subtask else None,
        'created_at': a.created_at.isoformat() if a.created_at else None,
        'is_cloud': bool(nas_ok) and not (a.storage_path or '').startswith('LOCAL-'),
    }
