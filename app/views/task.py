# -*- coding: utf-8 -*-
"""
通用任务模块 - 视图层

提供任务 CRUD、附件管理、回复和日历事件源 API
"""
import logging
from datetime import datetime, date
from zoneinfo import ZoneInfo
from flask import Blueprint, jsonify, request, render_template
from flask_login import login_required, current_user
from flask_babel import gettext as _
from sqlalchemy.orm import joinedload

from app import db, csrf
from app.models.task import Task, TaskAttachment, TaskReply, TaskReviewer
from app.models.subtask import SubTask, MilestoneReviewer
from app.models.user import User

logger = logging.getLogger(__name__)

task = Blueprint('task', __name__, url_prefix='/task')
csrf.exempt(task)


def get_local_time():
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


def _can_edit(t):
    """创建者可编辑/取消/删除"""
    return t.creator_id == current_user.id


def _auto_promote_pending_tasks():
    """将已到开始日期的 pending 任务批量升级为 in_progress（持久化）"""
    today = date.today()
    updated = Task.query.filter(
        Task.status == 'pending',
        Task.start_date.isnot(None),
        Task.start_date <= today,
        Task.is_deleted == False,
    ).update({Task.status: 'in_progress'}, synchronize_session='fetch')
    if updated:
        db.session.commit()


def _auto_promote_pending_subtasks(task_id=None):
    """将已到开始日期的 pending 子任务批量升级为 in_progress（持久化）"""
    today = date.today()
    q = SubTask.query.filter(
        SubTask.status == 'pending',
        SubTask.start_date.isnot(None),
        SubTask.start_date <= today,
        SubTask.is_deleted == False,
    )
    if task_id:
        q = q.filter(SubTask.task_id == task_id)
    updated = q.update({SubTask.status: 'in_progress'}, synchronize_session='fetch')
    if updated:
        db.session.commit()



def _can_access(t):
    """创建者、被指派人、协助人、审计人或里程碑确认人可访问"""
    if t.creator_id == current_user.id or t.assignee_id == current_user.id:
        return True
    # 审计人（会审）
    if any(r.reviewer_id == current_user.id for r in t.task_reviewers):
        return True
    shared = t.shared_with_users or []
    if current_user.id in shared:
        return True
    # 里程碑确认人
    from app.models.subtask import MilestoneReviewer, SubTask
    has_milestone = db.session.query(MilestoneReviewer.id).join(
        SubTask, MilestoneReviewer.subtask_id == SubTask.id
    ).filter(
        SubTask.task_id == t.id,
        MilestoneReviewer.reviewer_id == current_user.id,
    ).first()
    return has_milestone is not None


@task.route('/api/create', methods=['POST'])
@login_required
def create_task():
    """创建任务"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400

        title = (data.get('title') or '').strip()
        if not title:
            return jsonify({'success': False, 'message': '任务标题不能为空'}), 400

        assignee_id = data.get('assignee_id')
        if not assignee_id:
            return jsonify({'success': False, 'message': '请选择指派人'}), 400

        new_task = Task(
            title=title,
            description=(data.get('description') or '').strip() or None,
            creator_id=current_user.id,
            assignee_id=int(assignee_id),
            priority=data.get('priority', 'normal'),
            external_link=(data.get('external_link') or '').strip() or None,
            external_link_label=(data.get('external_link_label') or '').strip() or None,
            project_id=data.get('project_id') or None,
            quotation_id=data.get('quotation_id') or None,
            customer_id=data.get('customer_id') or None,
        )

        # 协助人
        shared_users = data.get('shared_with_users')
        if shared_users and isinstance(shared_users, list):
            new_task.shared_with_users = [int(uid) for uid in shared_users if uid]

        # 处理截止日期
        due_date_str = data.get('due_date')
        if due_date_str:
            try:
                new_task.due_date = datetime.fromisoformat(due_date_str)
            except (ValueError, TypeError):
                pass

        # 处理开始日期 → 决定初始状态
        start_date_str = data.get('start_date')
        if start_date_str:
            try:
                new_task.start_date = date.fromisoformat(start_date_str[:10])
                if new_task.start_date <= date.today():
                    new_task.status = 'in_progress'
                else:
                    new_task.status = 'pending'
            except (ValueError, TypeError):
                new_task.status = 'in_progress'
        else:
            # 没有开始日期 → 立即开始
            new_task.status = 'in_progress'

        # calendar_date 默认与 due_date 一致
        if new_task.due_date:
            new_task.calendar_date = new_task.due_date.date()

        db.session.add(new_task)
        db.session.flush()  # 获取 id

        # 审计对象（会审，支持多人）
        reviewer_ids = data.get('reviewer_ids') or []
        # 兼容旧的单审计人字段
        if not reviewer_ids and data.get('reviewer_id'):
            reviewer_ids = [data['reviewer_id']]
        for rid in reviewer_ids:
            rid = int(rid)
            tr = TaskReviewer(task_id=new_task.id, reviewer_id=rid)
            db.session.add(tr)

        # 发送通知给被指派人和协助人
        notify_ids = set()
        if new_task.assignee_id != current_user.id:
            notify_ids.add(new_task.assignee_id)
        for uid in (new_task.shared_with_users or []):
            if uid != current_user.id:
                notify_ids.add(uid)
        if notify_ids:
            try:
                from app.models.message import Message
                for uid in notify_ids:
                    msg = Message.create_task_assigned(
                        sender_id=current_user.id,
                        recipient_id=uid,
                        task=new_task
                    )
                    db.session.add(msg)
            except Exception as e:
                logger.warning(f"发送任务通知失败: {e}")

        try:
            from app.services.points_service import award_points
            award_points(user_id=current_user.id, behavior_code='task_create',
                         source_type='task', source_id=new_task.id,
                         memo=f'创建任务: {new_task.title}')
        except Exception as _pts_err:
            logger.warning(f'task_create积分发放失败: {_pts_err}')

        db.session.commit()

        try:
            from app.utils.work_item_recorder import record_task_activity
            record_task_activity(
                'create', new_task.id, new_task.title, current_user,
                project_id=new_task.project_id, customer_id=new_task.customer_id
            )
        except Exception as _log_err:
            logger.warning(f'task日志记录失败: {_log_err}')

        # 跨系统推送任务通知（异步，不阻塞）
        if new_task.assignee_id != current_user.id:
            try:
                from app.services.cross_sync_service import is_cross_sync_enabled, push_task_to_peer
                if is_cross_sync_enabled():
                    assignee = User.query.get(new_task.assignee_id)
                    if assignee and assignee.email:
                        creator_name = current_user.real_name or current_user.username
                        due_str = new_task.due_date.strftime('%Y-%m-%d') if new_task.due_date else None
                        push_task_to_peer(assignee.email, creator_name, title, due_str)
            except Exception as e:
                logger.warning(f"跨系统任务推送失败: {e}")

        return jsonify({
            'success': True,
            'message': _('任务创建成功'),
            'data': new_task.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建任务失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@task.route('/api/<int:id>', methods=['GET'])
@login_required
def get_task(id):
    """获取任务详情"""
    try:
        _auto_promote_pending_tasks()
        t = Task.query.options(
            joinedload(Task.creator),
            joinedload(Task.assignee),
            joinedload(Task.project),
            joinedload(Task.quotation),
            joinedload(Task.customer),
        ).filter_by(id=id, is_deleted=False).first()

        if not t:
            return jsonify({'success': False, 'message': '任务不存在'}), 404

        task_dict = t.to_dict()

        # 附件列表
        attachments = TaskAttachment.query.filter_by(
            task_id=id, is_deleted=False
        ).order_by(TaskAttachment.created_at.desc()).all()
        from app.utils.smart_storage_manager import get_smart_storage
        _storage = get_smart_storage()
        _nas_ok = _storage.nas_enabled and _storage.is_nas_available()

        task_dict['attachments'] = [{
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
            'is_cloud': _nas_ok and not (a.storage_path or '').startswith('LOCAL-'),
        } for a in attachments]

        # 回复列表
        replies = TaskReply.query.options(
            joinedload(TaskReply.author)
        ).filter_by(
            task_id=id, is_deleted=False
        ).order_by(TaskReply.created_at.asc()).all()
        task_dict['replies'] = [{
            'id': r.id,
            'author_id': r.author_id,
            'author_name': (r.author.real_name or r.author.username) if r.author else None,
            'subtask_id': r.subtask_id,
            'subtask_title': r.subtask.title if r.subtask else None,
            'content': r.content,
            'created_at': r.created_at.isoformat() if r.created_at else None,
        } for r in replies]

        # 子任务列表

        subtasks = SubTask.query.filter_by(
            task_id=id, is_deleted=False
        ).order_by(SubTask.sort_order, SubTask.created_at).all()
        task_dict['subtasks'] = [s.to_dict() for s in subtasks]

        # 权限标识
        task_dict['can_edit'] = _can_edit(t)
        task_dict['can_complete'] = t.assignee_id == current_user.id
        task_dict['is_creator'] = t.creator_id == current_user.id
        # 会审：当前用户是否为审计人之一，且自己尚未审核
        my_review = next((r for r in t.task_reviewers if r.reviewer_id == current_user.id), None)
        task_dict['is_reviewer'] = my_review is not None
        task_dict['can_review'] = (my_review is not None
                                   and my_review.status == 'pending'
                                   and t.review_status == 'pending_review')

        # 里程碑确认人标识（仅作为确认人，不是任务负责人/创建者/参与者）
        from app.models.subtask import MilestoneReviewer as MR
        is_milestone_only = (
            t.creator_id != current_user.id
            and t.assignee_id != current_user.id
            and not any(r.reviewer_id == current_user.id for r in t.task_reviewers)
            and current_user.id not in (t.shared_with_users or [])
            and db.session.query(MR.id).join(SubTask, MR.subtask_id == SubTask.id).filter(
                SubTask.task_id == t.id, MR.reviewer_id == current_user.id
            ).first() is not None
        )
        task_dict['is_milestone_reviewer_only'] = is_milestone_only

        return jsonify({'success': True, 'data': task_dict})
    except Exception as e:
        logger.error(f"获取任务详情失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@task.route('/api/<int:id>', methods=['PUT'])
@login_required
def update_task(id):
    """更新任务"""
    try:
        t = Task.query.filter_by(id=id, is_deleted=False).first()
        if not t:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        if not _can_edit(t):
            return jsonify({'success': False, 'message': '无权修改此任务'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400

        for field in ['title', 'description', 'priority', 'external_link', 'external_link_label']:
            if field in data:
                setattr(t, field, (data[field] or '').strip() or None if field != 'title' else (data[field] or '').strip())

        for fk_field in ['assignee_id', 'project_id', 'quotation_id', 'customer_id']:
            if fk_field in data:
                setattr(t, fk_field, data[fk_field] or None)

        # 会审审计人更新
        if 'reviewer_ids' in data:
            new_ids = set(int(rid) for rid in (data['reviewer_ids'] or []) if rid)
            old_ids = set(r.reviewer_id for r in t.task_reviewers)
            # 删除移除的审计人
            for tr in list(t.task_reviewers):
                if tr.reviewer_id not in new_ids:
                    db.session.delete(tr)
            # 添加新的审计人
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
                    # 根据开始时间自动调整状态
                    if t.status == 'pending' and t.start_date <= date.today():
                        t.status = 'in_progress'
                    elif t.status == 'in_progress' and t.start_date > date.today():
                        t.status = 'pending'
                except (ValueError, TypeError):
                    pass
            else:
                t.start_date = None
                # 没有开始日期且还在等待 → 立即开始
                if t.status == 'pending':
                    t.status = 'in_progress'

        if 'status' in data and data['status'] in ('pending', 'in_progress', 'paused'):
            t.status = data['status']

        db.session.commit()
        return jsonify({'success': True, 'message': _('任务已更新'), 'data': t.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新任务失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@task.route('/api/<int:id>/complete', methods=['POST'])
@login_required
def complete_task(id):
    """完成任务（审计类任务进入待审核状态）"""
    try:
        t = Task.query.filter_by(id=id, is_deleted=False).first()
        if not t:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        if t.assignee_id != current_user.id and t.creator_id != current_user.id:
            return jsonify({'success': False, 'message': '无权完成此任务'}), 403

        # 审计类任务（会审）：进入待审核状态而非直接完成
        if t.task_reviewers and not t.review_status:
            t.status = 'pending_review'
            t.review_status = 'pending_review'
            # 所有审计人重置为 pending 并通知
            try:
                from app.models.message import Message
                for tr in t.task_reviewers:
                    tr.status = 'pending'
                    tr.reviewed_at = None
                    tr.comment = None
                    msg = Message.create_task_assigned(
                        sender_id=current_user.id,
                        recipient_id=tr.reviewer_id,
                        task=t
                    )
                    db.session.add(msg)
            except Exception as e:
                logger.warning(f"发送审计通知失败: {e}")
            db.session.commit()
            return jsonify({'success': True, 'message': _('任务已提交审核'), 'data': t.to_dict()})

        t.status = 'completed'
        t.completed_at = get_local_time()

        # 通知创建人
        if t.creator_id != current_user.id:
            try:
                from app.models.message import Message
                msg = Message.create_task_completed(
                    sender_id=current_user.id,
                    recipient_id=t.creator_id,
                    task=t
                )
                db.session.add(msg)
            except Exception as e:
                logger.warning(f"发送完成通知失败: {e}")

        # 发放积分：任务完成
        try:
            from app.services.points_service import award_points
            assignee_id = t.assignee_id if t.assignee_id else current_user.id
            award_points(
                user_id=assignee_id,
                behavior_code='task_complete',
                source_type='task',
                source_id=t.id,
                memo=f'完成任务: {t.title}'
            )
        except Exception as pts_err:
            logger.warning(f"发放任务完成积分失败: {pts_err}")

        db.session.commit()
        return jsonify({'success': True, 'message': _('任务已完成'), 'data': t.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f"完成任务失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@task.route('/api/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_task(id):
    """取消任务"""
    try:
        t = Task.query.filter_by(id=id, is_deleted=False).first()
        if not t:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        if not _can_edit(t):
            return jsonify({'success': False, 'message': '无权取消此任务'}), 403

        t.status = 'cancelled'
        db.session.commit()
        return jsonify({'success': True, 'message': _('任务已取消'), 'data': t.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f"取消任务失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@task.route('/api/<int:id>/pause', methods=['POST'])
@login_required
def pause_task(id):
    """暂停任务（需要填写暂停理由，通知审计人）"""
    try:
        t = Task.query.filter_by(id=id, is_deleted=False).first()
        if not t:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        if not _can_access(t):
            return jsonify({'success': False, 'message': '无权操作此任务'}), 403

        data = request.get_json() or {}
        reason = (data.get('reason') or '').strip()
        if not reason:
            return jsonify({'success': False, 'message': _('请填写暂停理由')}), 400

        t.status = 'paused'

        # 通知审计人
        if t.task_reviewers:
            try:
                from app.models.message import Message
                for tr in t.task_reviewers:
                    msg = Message(
                        sender_id=current_user.id,
                        recipient_id=tr.reviewer_id,
                        message_type='task_notification',
                        title=_('任务已暂停'),
                        content=f'{t.title} - {_("暂停理由")}: {reason}',
                        related_object_type='task',
                        related_object_id=t.id,
                    )
                    db.session.add(msg)
            except Exception as e:
                logger.warning(f"发送暂停通知失败: {e}")

        # 记录暂停理由到回复中，便于追溯
        try:
            reply = TaskReply(
                task_id=t.id,
                author_id=current_user.id,
                content=f'[{_("任务暂停")}] {reason}',
            )
            db.session.add(reply)
        except Exception as e:
            logger.warning(f"记录暂停理由失败: {e}")

        db.session.commit()
        return jsonify({'success': True, 'message': _('任务已暂停'), 'data': t.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f"暂停任务失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@task.route('/api/<int:id>', methods=['DELETE'])
@login_required
def delete_task(id):
    """彻底删除任务（含附件存储文件）"""
    try:
        t = Task.query.filter_by(id=id, is_deleted=False).first()
        if not t:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        if not _can_edit(t):
            return jsonify({'success': False, 'message': '无权删除此任务'}), 403

        # 删除 NAS/本地存储中的附件文件
        attachments = TaskAttachment.query.filter_by(task_id=id).all()
        if attachments:
            from app.utils.smart_storage_manager import get_smart_storage
            storage = get_smart_storage()
            for att in attachments:
                if att.storage_path:
                    try:
                        storage.delete_file(att.storage_path, bucket_type='task')
                    except Exception as e:
                        logger.warning(f"删除附件文件失败: {e}")

        db.session.delete(t)  # cascade 删除 attachments + replies
        db.session.commit()
        return jsonify({'success': True, 'message': _('任务已删除')})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除任务失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@task.route('/api/<int:id>/attachments', methods=['POST'])
@login_required
def upload_attachment(id):
    """上传附件"""
    try:
        t = Task.query.filter_by(id=id, is_deleted=False).first()
        if not t:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        if not _can_access(t):
            return jsonify({'success': False, 'message': '无权操作此任务'}), 403

        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '请选择文件'}), 400

        file = request.files['file']
        if not file.filename:
            return jsonify({'success': False, 'message': '文件名为空'}), 400

        filename = file.filename
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

        # 获取文件大小
        file.seek(0, 2)
        file_size = file.tell()
        file.seek(0)

        from app.utils.smart_storage_manager import get_smart_storage
        smart_storage = get_smart_storage()
        result = smart_storage.upload_file(
            object_id=id,
            file=file,
            filename=filename,
            file_type='attachment',
            bucket_type='task',
            business_type='task'
        )

        if not result:
            return jsonify({'success': False, 'message': '文件上传失败'}), 500

        subtask_id = request.form.get('subtask_id', type=int)

        attachment = TaskAttachment(
            task_id=id,
            subtask_id=subtask_id,
            filename=filename,
            storage_path=result.get('storage_path', ''),
            file_size=file_size,
            file_type=file_ext,
            uploaded_by=current_user.id,
        )
        db.session.add(attachment)
        db.session.commit()

        subtask_title = None
        if attachment.subtask_id:
            st = SubTask.query.get(attachment.subtask_id)
            subtask_title = st.title if st else None

        return jsonify({
            'success': True,
            'message': _('附件上传成功'),
            'data': {
                'id': attachment.id,
                'filename': attachment.filename,
                'storage_path': attachment.storage_path,
                'file_size': attachment.file_size,
                'file_type': attachment.file_type,
                'uploaded_by': attachment.uploaded_by,
                'subtask_id': attachment.subtask_id,
                'subtask_title': subtask_title,
                'created_at': attachment.created_at.isoformat() if attachment.created_at else None,
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"上传附件失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@task.route('/api/<int:id>/attachments/<int:att_id>', methods=['DELETE'])
@login_required
def delete_attachment(id, att_id):
    """彻底删除附件（含存储文件）"""
    try:
        att = TaskAttachment.query.filter_by(id=att_id, task_id=id, is_deleted=False).first()
        if not att:
            return jsonify({'success': False, 'message': '附件不存在'}), 404

        # 只有上传者本人可以删除附件
        if att.uploaded_by != current_user.id:
            return jsonify({'success': False, 'message': _('只能删除自己上传的附件')}), 403

        # 删除存储文件
        if att.storage_path:
            try:
                from app.utils.smart_storage_manager import get_smart_storage
                storage = get_smart_storage()
                storage.delete_file(att.storage_path, bucket_type='task')
            except Exception as e:
                logger.warning(f"删除附件文件失败: {e}")

        db.session.delete(att)
        db.session.commit()
        return jsonify({'success': True, 'message': _('附件已删除')})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除附件失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@task.route('/api/<int:id>/attachments/<int:att_id>/download', methods=['GET'])
@login_required
def download_attachment(id, att_id):
    """下载附件"""
    try:
        att = TaskAttachment.query.filter_by(id=att_id, task_id=id, is_deleted=False).first()
        if not att:
            return jsonify({'success': False, 'message': '附件不存在'}), 404

        t = Task.query.filter_by(id=id, is_deleted=False).first()
        if not t or not _can_access(t):
            return jsonify({'success': False, 'message': '无权操作'}), 403

        from app.utils.smart_storage_manager import get_smart_storage
        from flask import Response
        from urllib.parse import quote

        smart_storage = get_smart_storage()
        file_data = smart_storage.download_file(att.storage_path, bucket_type='task')
        if not file_data:
            return jsonify({'success': False, 'message': '文件不存在'}), 404

        # RFC 5987 编码确保中文文件名正确
        encoded_filename = quote(att.filename)
        return Response(
            file_data,
            mimetype='application/octet-stream',
            headers={
                'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}",
            }
        )
    except Exception as e:
        logger.error(f"下载附件失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@task.route('/api/<int:id>/replies', methods=['POST'])
@login_required
def add_reply(id):
    """添加回复"""
    try:
        t = Task.query.filter_by(id=id, is_deleted=False).first()
        if not t:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        if not _can_access(t):
            return jsonify({'success': False, 'message': '无权操作此任务'}), 403

        data = request.get_json()
        content = (data.get('content') or '').strip() if data else ''
        if not content:
            return jsonify({'success': False, 'message': '回复内容不能为空'}), 400

        subtask_id = data.get('subtask_id') if data else None

        reply = TaskReply(
            task_id=id,
            subtask_id=subtask_id,
            author_id=current_user.id,
            content=content,
        )
        db.session.add(reply)
        db.session.commit()

        try:
            from app.utils.work_item_recorder import record_task_activity
            record_task_activity(
                'reply', t.id, t.title, current_user,
                project_id=t.project_id, customer_id=t.customer_id
            )
        except Exception as _log_err:
            logger.warning(f'task日志记录失败: {_log_err}')

        subtask_title = None
        if reply.subtask_id:
            st = SubTask.query.get(reply.subtask_id)
            subtask_title = st.title if st else None

        return jsonify({
            'success': True,
            'message': _('回复成功'),
            'data': {
                'id': reply.id,
                'author_id': reply.author_id,
                'author_name': (reply.author.real_name or reply.author.username) if reply.author else None,
                'subtask_id': reply.subtask_id,
                'subtask_title': subtask_title,
                'content': reply.content,
                'created_at': reply.created_at.isoformat() if reply.created_at else None,
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"添加回复失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@task.route('/management')
@login_required
def task_management():
    """任务管理页面"""
    return render_template('task/tw_task_management.html')


@task.route('/api/management/list', methods=['GET'])
@login_required
def management_list():
    """任务管理列表 API"""
    try:
        _auto_promote_pending_tasks()
        tab = request.args.get('tab', 'my')
        sort = request.args.get('sort', 'updated')
        status = request.args.get('status', '').strip()
        search = request.args.get('search', '').strip()
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)

        uid = current_user.id
        query = Task.query.filter(Task.is_deleted == False)

        # 作为审计人的任务ID
        reviewer_task_ids = db.session.query(TaskReviewer.task_id).filter(
            TaskReviewer.reviewer_id == uid
        ).scalar_subquery()

        # 作为里程碑确认人的任务ID（通过子任务关联）
        from app.models.subtask import MilestoneReviewer, SubTask
        milestone_task_ids = db.session.query(SubTask.task_id).join(
            MilestoneReviewer, MilestoneReviewer.subtask_id == SubTask.id
        ).filter(
            MilestoneReviewer.reviewer_id == uid,
            MilestoneReviewer.status == 'pending',
        ).scalar_subquery()

        # Tab 筛选
        if tab == 'my':
            query = query.filter(Task.assignee_id == uid)
        elif tab == 'created':
            query = query.filter(Task.creator_id == uid)
        elif tab == 'shared':
            query = query.filter(Task.shared_with_users.cast(db.Text).contains(str(uid)))
        elif tab == 'review':
            query = query.filter(db.or_(
                Task.id.in_(reviewer_task_ids),
                Task.id.in_(milestone_task_ids),
            ))
        else:
            # tab == 'all': 我能看到的全部
            query = query.filter(db.or_(
                Task.assignee_id == uid,
                Task.creator_id == uid,
                Task.shared_with_users.cast(db.Text).contains(str(uid)),
                Task.id.in_(reviewer_task_ids),
                Task.id.in_(milestone_task_ids),
            ))

        # 状态筛选
        if status:
            query = query.filter(Task.status == status)

        # 搜索
        if search:
            query = query.filter(Task.title.ilike(f'%{search}%'))

        # 统计
        total = query.count()

        # 排序：已完成/已取消 排到底部
        completed_last = db.case(
            (Task.status.in_(['completed', 'cancelled']), 1),
            else_=0
        )
        if sort == 'due_date':
            query = query.order_by(completed_last, Task.due_date.asc().nullslast(), Task.updated_at.desc())
        elif sort == 'priority':
            priority_order = db.case(
                (Task.priority == 'urgent', 1),
                (Task.priority == 'high', 2),
                (Task.priority == 'normal', 3),
                (Task.priority == 'low', 4),
                else_=5
            )
            query = query.order_by(completed_last, priority_order, Task.updated_at.desc())
        elif sort == 'created':
            query = query.order_by(completed_last, Task.created_at.desc())
        else:
            query = query.order_by(completed_last, Task.updated_at.desc())

        # 分页
        tasks = query.options(
            joinedload(Task.creator),
            joinedload(Task.assignee),
            joinedload(Task.project),
        ).offset((page - 1) * per_page).limit(per_page).all()

        return jsonify({
            'success': True,
            'data': [t.to_dict() for t in tasks],
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': (total + per_page - 1) // per_page,
        })
    except Exception as e:
        logger.error(f"获取任务管理列表失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@task.route('/api/calendar-events', methods=['GET'])
@login_required
def get_calendar_events():
    """日历事件源"""
    try:
        start_str = request.args.get('start')
        end_str = request.args.get('end')
        account_id = request.args.get('account_id', type=int)

        target_user_id = account_id or current_user.id

        query = Task.query.filter(
            Task.is_deleted == False,
            Task.calendar_date.isnot(None),
            db.or_(
                Task.assignee_id == target_user_id,
                Task.creator_id == target_user_id,
            )
        )

        if start_str:
            try:
                start_date = date.fromisoformat(start_str[:10])
                query = query.filter(Task.calendar_date >= start_date)
            except (ValueError, TypeError):
                pass

        if end_str:
            try:
                end_date = date.fromisoformat(end_str[:10])
                query = query.filter(Task.calendar_date <= end_date)
            except (ValueError, TypeError):
                pass

        tasks = query.all()
        events = []
        for t in tasks:
            event = t.to_calendar_event()
            if event:
                events.append(event)

        return jsonify({'success': True, 'events': events})
    except Exception as e:
        logger.error(f"获取日历事件失败: {e}", exc_info=True)
        return jsonify({'success': False, 'events': []})


@task.route('/api/my-tasks', methods=['GET'])
@login_required
def get_my_tasks():
    """我的待办任务"""
    try:
        _auto_promote_pending_tasks()
        # 作为审计人的任务ID
        reviewer_task_ids = db.session.query(TaskReviewer.task_id).filter(
            TaskReviewer.reviewer_id == current_user.id
        ).subquery()

        tasks = Task.query.filter(
            db.or_(
                Task.assignee_id == current_user.id,
                Task.creator_id == current_user.id,
                Task.shared_with_users.contains([current_user.id]),
                Task.id.in_(reviewer_task_ids)
            ),
            Task.is_deleted == False,
            Task.status.in_(['pending', 'in_progress', 'paused', 'pending_review'])
        ).order_by(
            Task.due_date.asc().nullslast(),
            Task.created_at.desc()
        ).limit(20).all()

        return jsonify({
            'success': True,
            'data': [t.to_dict() for t in tasks]
        })
    except Exception as e:
        logger.error(f"获取我的任务失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@task.route('/api/nav-summary', methods=['GET'])
@login_required
def nav_summary():
    """导航栏任务摘要 — 按紧急程度排前3"""
    try:
        _auto_promote_pending_tasks()
        priority_order = db.case(
            (Task.priority == 'urgent', 0),
            (Task.priority == 'high', 1),
            (Task.priority == 'normal', 2),
            (Task.priority == 'low', 3),
            else_=4
        )
        reviewer_task_ids = db.session.query(TaskReviewer.task_id).filter(
            TaskReviewer.reviewer_id == current_user.id
        ).subquery()

        uid = current_user.id
        base_filter = [
            db.or_(
                Task.assignee_id == uid,
                Task.shared_with_users.cast(db.Text).contains(str(uid)),
                Task.id.in_(reviewer_task_ids)
            ),
            Task.is_deleted == False,
            Task.status.in_(['pending', 'in_progress', 'paused'])
        ]

        tasks = Task.query.filter(*base_filter).order_by(
            priority_order,
            Task.due_date.asc().nullslast()
        ).limit(3).all()

        total_active = Task.query.filter(*base_filter).count()

        return jsonify({
            'success': True,
            'total': total_active,
            'tasks': [{
                'id': t.id,
                'title': t.title,
                'priority': t.priority,
                'status': t.effective_status,
                'due_date': t.due_date.isoformat() if t.due_date else None,
                'subtask_count': t.subtasks.filter_by(is_deleted=False).count(),
                'subtask_completed': t.subtasks.filter_by(is_deleted=False, status='completed').count(),
            } for t in tasks]
        })
    except Exception as e:
        logger.error(f"获取导航任务摘要失败: {e}", exc_info=True)
        return jsonify({'success': False, 'total': 0, 'tasks': []})


@task.route('/api/search-projects', methods=['GET'])
@login_required
def search_projects():
    """搜索项目（用于任务关联）"""
    try:
        keyword = request.args.get('keyword', '').strip()
        if not keyword:
            return jsonify({'results': []})

        from app.models.project import Project
        projects = Project.query.filter(
            Project.project_name.ilike(f'%{keyword}%')
        ).order_by(Project.created_at.desc()).limit(10).all()

        return jsonify({'results': [{
            'id': p.id,
            'project_name': p.project_name,
        } for p in projects]})
    except Exception as e:
        return jsonify({'results': []}), 500


@task.route('/api/project-quotations/<int:project_id>', methods=['GET'])
@login_required
def get_project_quotations(project_id):
    """获取项目下的报价单列表（用于二级联动）"""
    try:
        from app.models.quotation import Quotation
        quotations = Quotation.query.filter(
            Quotation.project_id == project_id,
        ).order_by(Quotation.created_at.desc()).limit(50).all()

        return jsonify({'success': True, 'data': [{
            'id': q.id,
            'quotation_number': q.quotation_number,
            'amount': q.formatted_amount,
        } for q in quotations]})
    except Exception as e:
        return jsonify({'success': False, 'data': []}), 500


# ============================================================
# 任务审计 API
# ============================================================

@task.route('/api/<int:id>/review', methods=['POST'])
@login_required
def review_task(id):
    """审计对象确认/驳回任务（会审：并行审核）"""
    try:
        t = Task.query.filter_by(id=id, is_deleted=False).first()
        if not t:
            return jsonify({'success': False, 'message': '任务不存在'}), 404

        # 找到当前用户的审计记录
        my_review = next((r for r in t.task_reviewers if r.reviewer_id == current_user.id), None)
        if not my_review:
            return jsonify({'success': False, 'message': _('您不是此任务的审计对象')}), 403
        if t.review_status != 'pending_review':
            return jsonify({'success': False, 'message': _('任务不在待审核状态')}), 400
        if my_review.status != 'pending':
            return jsonify({'success': False, 'message': _('您已完成审核')}), 400

        data = request.get_json() or {}
        action = data.get('action')  # 'approve' or 'reject'
        comment = (data.get('comment') or '').strip()

        if action == 'approve':
            my_review.status = 'approved'
            my_review.comment = comment or None
            my_review.reviewed_at = get_local_time()

            # 检查是否所有人都已通过 → 任务完成
            all_approved = all(r.status == 'approved' for r in t.task_reviewers)
            if all_approved:
                t.review_status = 'approved'
                t.reviewed_at = get_local_time()
                t.status = 'completed'
                t.completed_at = get_local_time()
                msg_text = _('任务审核通过')
                # 发放积分
                try:
                    from app.services.points_service import award_points
                    award_points(user_id=t.assignee_id, behavior_code='task_complete',
                                 source_type='task', source_id=t.id,
                                 memo=f'完成任务: {t.title}')
                    for r in t.task_reviewers:
                        award_points(user_id=r.reviewer_id, behavior_code='task_review_approved',
                                     source_type='task_review', source_id=t.id,
                                     memo=f'审计任务通过: {t.title}')
                except Exception as pts_err:
                    logger.warning(f"发放任务完成积分失败: {pts_err}")
            else:
                # 部分通过，等待其他审计人
                remaining = [r for r in t.task_reviewers if r.status == 'pending']
                msg_text = _('您已通过，等待其他审计人')

        elif action == 'reject':
            if not comment:
                return jsonify({'success': False, 'message': _('驳回时必须填写意见')}), 400
            my_review.status = 'rejected'
            my_review.comment = comment
            my_review.reviewed_at = get_local_time()
            # 任一驳回 → 整体驳回
            t.review_status = 'rejected'
            t.reviewed_at = get_local_time()
            t.status = 'in_progress'
            msg_text = _('任务审核被驳回')
        else:
            return jsonify({'success': False, 'message': _('无效的操作')}), 400

        # 通知执行人（全部通过或被驳回时）
        if t.review_status in ('approved', 'rejected'):
            try:
                from app.models.message import Message
                msg = Message.create_task_completed(
                    sender_id=current_user.id,
                    recipient_id=t.assignee_id,
                    task=t
                )
                db.session.add(msg)
            except Exception as e:
                logger.warning(f"发送审计结果通知失败: {e}")

        db.session.commit()
        return jsonify({'success': True, 'message': msg_text, 'data': t.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f"审计任务失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@task.route('/api/<int:id>/resubmit-review', methods=['POST'])
@login_required
def resubmit_review(id):
    """被驳回后重新提交审核（会审）"""
    try:
        t = Task.query.filter_by(id=id, is_deleted=False).first()
        if not t:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        if t.assignee_id != current_user.id and t.creator_id != current_user.id:
            return jsonify({'success': False, 'message': '无权操作'}), 403
        if t.review_status != 'rejected':
            return jsonify({'success': False, 'message': _('任务不在被驳回状态')}), 400

        t.status = 'pending_review'
        t.review_status = 'pending_review'
        t.reviewed_at = None

        # 重置所有审计人状态并通知
        try:
            from app.models.message import Message
            for tr in t.task_reviewers:
                tr.status = 'pending'
                tr.comment = None
                tr.reviewed_at = None
                msg = Message.create_task_assigned(
                    sender_id=current_user.id,
                    recipient_id=tr.reviewer_id,
                    task=t
                )
                db.session.add(msg)
        except Exception as e:
            logger.warning(f"发送重新提交通知失败: {e}")

        db.session.commit()
        return jsonify({'success': True, 'message': _('已重新提交审核'), 'data': t.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f"重新提交审核失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================================
# 子任务/节点 API
# ============================================================

@task.route('/api/<int:task_id>/subtasks', methods=['GET'])
@login_required
def list_subtasks(task_id):
    """获取任务的子任务列表"""
    try:
        _auto_promote_pending_subtasks(task_id)

        t = Task.query.filter_by(id=task_id, is_deleted=False).first()
        if not t:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        if not _can_access(t):
            return jsonify({'success': False, 'message': '无权访问'}), 403

        subtasks = SubTask.query.filter_by(
            task_id=task_id, is_deleted=False
        ).order_by(SubTask.sort_order, SubTask.created_at).all()

        return jsonify({'success': True, 'data': [s.to_dict() for s in subtasks]})
    except Exception as e:
        logger.error(f"获取子任务列表失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@task.route('/api/<int:task_id>/subtasks', methods=['POST'])
@login_required
def create_subtask(task_id):
    """创建子任务/节点"""
    try:

        t = Task.query.filter_by(id=task_id, is_deleted=False).first()
        if not t:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        if not _can_access(t):
            return jsonify({'success': False, 'message': '无权操作'}), 403

        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400

        title = (data.get('title') or '').strip()
        if not title:
            return jsonify({'success': False, 'message': '节点标题不能为空'}), 400

        is_milestone = bool(data.get('is_milestone', False))

        # 计算排序
        max_order = db.session.query(db.func.max(SubTask.sort_order)).filter_by(
            task_id=task_id, is_deleted=False
        ).scalar() or 0

        subtask = SubTask(
            task_id=task_id,
            title=title,
            description=(data.get('description') or '').strip() or None,
            assignee_id=data.get('assignee_id') or None,
            is_milestone=is_milestone,
            sort_order=max_order + 1,
        )

        # 日期 + 根据开始日期设初始状态
        if data.get('start_date'):
            try:
                subtask.start_date = date.fromisoformat(data['start_date'])
                if subtask.start_date <= date.today():
                    subtask.status = 'in_progress'
                else:
                    subtask.status = 'pending'
            except (ValueError, TypeError):
                pass
        else:
            subtask.status = 'in_progress'

        if data.get('due_date'):
            try:
                subtask.due_date = date.fromisoformat(data['due_date'])
            except (ValueError, TypeError):
                pass

        # 里程碑专属字段
        if is_milestone:
            subtask.milestone_criteria = (data.get('milestone_criteria') or '').strip() or None

        db.session.add(subtask)
        db.session.flush()

        # 里程碑确认人（会审，支持多人）
        if is_milestone:
            confirmer_ids = data.get('milestone_confirmer_ids') or []
            if not confirmer_ids and data.get('milestone_confirmer_id'):
                confirmer_ids = [data['milestone_confirmer_id']]
            for cid in confirmer_ids:
                mr = MilestoneReviewer(subtask_id=subtask.id, reviewer_id=int(cid))
                db.session.add(mr)

        db.session.commit()

        try:
            from app.utils.work_item_recorder import record_task_activity
            record_task_activity(
                'subtask', t.id, t.title, current_user,
                project_id=t.project_id, customer_id=t.customer_id
            )
        except Exception as _log_err:
            logger.warning(f'task日志记录失败: {_log_err}')

        return jsonify({'success': True, 'message': _('节点已创建'), 'data': subtask.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f"创建子任务失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@task.route('/api/<int:task_id>/subtasks/<int:subtask_id>', methods=['PUT'])
@login_required
def update_subtask(task_id, subtask_id):
    """更新子任务/节点"""
    try:

        t = Task.query.filter_by(id=task_id, is_deleted=False).first()
        if not t:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        if not _can_access(t):
            return jsonify({'success': False, 'message': '无权操作'}), 403

        subtask = SubTask.query.filter_by(id=subtask_id, task_id=task_id, is_deleted=False).first()
        if not subtask:
            return jsonify({'success': False, 'message': '节点不存在'}), 404

        data = request.get_json() or {}

        for field in ['title', 'description']:
            if field in data:
                setattr(subtask, field, (data[field] or '').strip() or None)

        if 'assignee_id' in data:
            subtask.assignee_id = data['assignee_id'] or None

        if 'start_date' in data:
            try:
                subtask.start_date = date.fromisoformat(data['start_date']) if data['start_date'] else None
            except (ValueError, TypeError):
                pass
        if 'due_date' in data:
            try:
                subtask.due_date = date.fromisoformat(data['due_date']) if data['due_date'] else None
            except (ValueError, TypeError):
                pass

        if 'is_milestone' in data:
            subtask.is_milestone = bool(data['is_milestone'])
        if 'milestone_criteria' in data:
            subtask.milestone_criteria = (data['milestone_criteria'] or '').strip() or None

        # 里程碑确认人更新（会审）
        if 'milestone_confirmer_ids' in data:
            new_ids = set(int(cid) for cid in (data['milestone_confirmer_ids'] or []) if cid)
            old_ids = set(r.reviewer_id for r in subtask.milestone_reviewers)
            for mr in list(subtask.milestone_reviewers):
                if mr.reviewer_id not in new_ids:
                    db.session.delete(mr)
            for cid in new_ids - old_ids:
                db.session.add(MilestoneReviewer(subtask_id=subtask.id, reviewer_id=cid))

        db.session.commit()
        return jsonify({'success': True, 'message': _('节点已更新'), 'data': subtask.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新子任务失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@task.route('/api/<int:task_id>/subtasks/<int:subtask_id>', methods=['DELETE'])
@login_required
def delete_subtask(task_id, subtask_id):
    """删除子任务/节点"""
    try:

        t = Task.query.filter_by(id=task_id, is_deleted=False).first()
        if not t:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        if not _can_access(t):
            return jsonify({'success': False, 'message': '无权操作'}), 403

        subtask = SubTask.query.filter_by(id=subtask_id, task_id=task_id, is_deleted=False).first()
        if not subtask:
            return jsonify({'success': False, 'message': '节点不存在'}), 404

        subtask.is_deleted = True
        db.session.commit()
        return jsonify({'success': True, 'message': _('节点已删除')})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除子任务失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@task.route('/api/<int:task_id>/subtasks/<int:subtask_id>/status', methods=['POST'])
@login_required
def update_subtask_status(task_id, subtask_id):
    """更新子任务状态（开始/完成）"""
    try:

        t = Task.query.filter_by(id=task_id, is_deleted=False).first()
        if not t:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        if not _can_access(t):
            return jsonify({'success': False, 'message': '无权操作'}), 403

        subtask = SubTask.query.filter_by(id=subtask_id, task_id=task_id, is_deleted=False).first()
        if not subtask:
            return jsonify({'success': False, 'message': '节点不存在'}), 404

        data = request.get_json() or {}
        action = data.get('action')  # 'start', 'complete'

        today = date.today()

        if action == 'start':
            # 检查子任务开始日期，未设则看任务开始日期
            start = subtask.start_date or t.start_date
            if start and today < start:
                return jsonify({'success': False,
                                'message': _('该节点尚未到开始日期（%(date)s）', date=start.strftime("%m/%d"))}), 400
            subtask.status = 'in_progress'
        elif action == 'complete':
            # 里程碑节点完成时进入待确认（会审）
            if subtask.is_milestone and subtask.milestone_reviewers:
                subtask.status = 'completed'
                subtask.completed_at = get_local_time()
                subtask.milestone_status = 'pending_confirmation'
                # 重置并通知所有确认人
                try:
                    from app.models.message import Message
                    for mr in subtask.milestone_reviewers:
                        mr.status = 'pending'
                        mr.reviewed_at = None
                        mr.comment = None
                        msg = Message.create_task_assigned(
                            sender_id=current_user.id,
                            recipient_id=mr.reviewer_id,
                            task=t
                        )
                        db.session.add(msg)
                except Exception as e:
                    logger.warning(f"发送里程碑通知失败: {e}")
            else:
                subtask.status = 'completed'
                subtask.completed_at = get_local_time()
                try:
                    from app.services.points_service import award_points
                    uid = subtask.assignee_id or t.assignee_id
                    award_points(user_id=uid, behavior_code='subtask_complete',
                                 source_type='subtask', source_id=subtask.id,
                                 memo=f'完成节点: {subtask.title}')
                except Exception as _pts_err:
                    logger.warning(f'subtask_complete积分发放失败: {_pts_err}')
        else:
            return jsonify({'success': False, 'message': '无效操作'}), 400

        db.session.commit()
        return jsonify({'success': True, 'data': subtask.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f"更新子任务状态失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@task.route('/api/<int:task_id>/subtasks/<int:subtask_id>/milestone', methods=['POST'])
@login_required
def confirm_milestone(task_id, subtask_id):
    """里程碑确认/驳回（会审：并行确认）"""
    try:
        t = Task.query.filter_by(id=task_id, is_deleted=False).first()
        if not t:
            return jsonify({'success': False, 'message': '任务不存在'}), 404

        subtask = SubTask.query.filter_by(id=subtask_id, task_id=task_id, is_deleted=False).first()
        if not subtask:
            return jsonify({'success': False, 'message': '节点不存在'}), 404
        if not subtask.is_milestone:
            return jsonify({'success': False, 'message': _('此节点不是里程碑')}), 400

        # 找到当前用户的确认记录
        my_review = next((r for r in subtask.milestone_reviewers if r.reviewer_id == current_user.id), None)
        if not my_review:
            return jsonify({'success': False, 'message': _('您不是此里程碑的确认人')}), 403
        if subtask.milestone_status != 'pending_confirmation':
            return jsonify({'success': False, 'message': _('里程碑不在待确认状态')}), 400
        if my_review.status != 'pending':
            return jsonify({'success': False, 'message': _('您已完成确认')}), 400

        data = request.get_json() or {}
        action = data.get('action')  # 'confirm' or 'reject'
        comment = (data.get('comment') or '').strip()

        if action == 'confirm':
            my_review.status = 'confirmed'
            my_review.comment = comment or None
            my_review.reviewed_at = get_local_time()

            # 检查是否所有人都已确认
            all_confirmed = all(r.status == 'confirmed' for r in subtask.milestone_reviewers)
            if all_confirmed:
                subtask.milestone_status = 'confirmed'
                subtask.milestone_confirmed_at = get_local_time()
                try:
                    from app.services.points_service import award_points
                    uid = subtask.assignee_id or t.assignee_id
                    award_points(user_id=uid, behavior_code='task_milestone_confirmed',
                                 source_type='subtask', source_id=subtask.id,
                                 memo=f'里程碑通过: {subtask.title}')
                except Exception as _pts_err:
                    logger.warning(f'task_milestone_confirmed积分发放失败: {_pts_err}')
                msg_text = _('里程碑已确认通过')
            else:
                msg_text = _('您已确认，等待其他确认人')

        elif action == 'reject':
            if not comment:
                return jsonify({'success': False, 'message': _('驳回时必须填写意见')}), 400
            my_review.status = 'rejected'
            my_review.comment = comment
            my_review.reviewed_at = get_local_time()
            # 任一驳回 → 整体驳回
            subtask.milestone_status = 'rejected'
            subtask.milestone_confirmed_at = get_local_time()
            subtask.status = 'in_progress'
            msg_text = _('里程碑已被驳回')
        else:
            return jsonify({'success': False, 'message': _('无效操作')}), 400

        # 通知任务执行人（全部确认或被驳回时）
        if subtask.milestone_status in ('confirmed', 'rejected'):
            notify_uid = subtask.assignee_id or t.assignee_id
            if notify_uid != current_user.id:
                try:
                    from app.models.message import Message
                    msg = Message.create_task_assigned(
                        sender_id=current_user.id,
                        recipient_id=notify_uid,
                        task=t
                    )
                    db.session.add(msg)
                except Exception as e:
                    logger.warning(f"发送里程碑结果通知失败: {e}")

        db.session.commit()
        return jsonify({'success': True, 'message': msg_text, 'data': subtask.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f"里程碑确认失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500
