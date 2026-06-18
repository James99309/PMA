# -*- coding: utf-8 -*-
"""
通用任务模块 - 视图层

提供任务 CRUD、附件管理、回复和日历事件源 API
"""
import logging
from datetime import datetime, date
from zoneinfo import ZoneInfo
from flask import Blueprint, jsonify, request, render_template, redirect, url_for
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
    """创建者、被指派人、协助人、审计人或里程碑确认人可访问；管理员/CEO 全局可访问"""
    if current_user.role in ('admin', 'ceo'):
        return True
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
    """创建任务(薄壳:逻辑+副作用在 app.services.task_service,web/mobile 共用)"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400
        from app.services import task_service
        try:
            new_task = task_service.create_task(current_user, data)
        except ValueError as ve:
            return jsonify({'success': False, 'message': str(ve)}), 400
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
            'reply_type': r.reply_type,
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

        from app.services import task_service
        try:
            task_service.update_task(current_user, t, data)
        except ValueError as ve:
            return jsonify({'success': False, 'message': str(ve)}), 400
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

        from app.services import task_service
        task_service.complete_task(current_user, t)
        msg = _('任务已提交审核') if t.status == 'pending_review' else _('任务已完成')
        return jsonify({'success': True, 'message': msg, 'data': t.to_dict()})
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

        from app.services import task_service
        task_service.cancel_task(current_user, t)
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
        from app.services import task_service
        try:
            task_service.pause_task(current_user, t, data.get('reason'))
        except ValueError as ve:
            return jsonify({'success': False, 'message': str(ve)}), 400
        return jsonify({'success': True, 'message': _('任务已暂停'), 'data': t.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f"暂停任务失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@task.route('/api/<int:id>/resume', methods=['POST'])
@login_required
def resume_task(id):
    """从暂停恢复为进行中。"""
    try:
        t = Task.query.filter_by(id=id, is_deleted=False).first()
        if not t:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        if not _can_access(t):
            return jsonify({'success': False, 'message': '无权操作此任务'}), 403
        from app.services import task_service
        task_service.resume_task(current_user, t)
        return jsonify({'success': True, 'message': _('任务已恢复'), 'data': t.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f"恢复任务失败: {e}", exc_info=True)
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

        from app.services import task_service
        task_service.delete_task(current_user, t)
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

        subtask_id = request.form.get('subtask_id', type=int)

        from app.services import task_service
        try:
            attachment = task_service.add_attachment(
                current_user, t, file, filename, file_size, file_ext,
                subtask_id=subtask_id)
        except ValueError as ve:
            return jsonify({'success': False, 'message': str(ve)}), 400

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

        from app.services import task_service
        try:
            task_service.delete_attachment(current_user, att)
        except ValueError as ve:
            return jsonify({'success': False, 'message': str(ve)}), 403
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


@task.route('/api/<int:id>/attachments/<int:att_id>/preview', methods=['GET'])
@login_required
def preview_attachment(id, att_id):
    """内联预览附件(图片/PDF 直接渲染),供公用 ATFilePreview 组件使用。"""
    try:
        att = TaskAttachment.query.filter_by(id=att_id, task_id=id, is_deleted=False).first()
        if not att:
            return jsonify({'success': False, 'message': '附件不存在'}), 404
        t = Task.query.filter_by(id=id, is_deleted=False).first()
        if not t or not _can_access(t):
            return jsonify({'success': False, 'message': '无权操作'}), 403

        import mimetypes
        from flask import Response
        from urllib.parse import quote
        from app.utils.smart_storage_manager import get_smart_storage

        file_data = get_smart_storage().download_file(att.storage_path, bucket_type='task')
        if not file_data:
            return jsonify({'success': False, 'message': '文件不存在'}), 404

        mime = mimetypes.guess_type(att.filename)[0] or 'application/octet-stream'
        encoded = quote(att.filename)
        return Response(file_data, mimetype=mime, headers={
            'Content-Disposition': f"inline; filename*=UTF-8''{encoded}",
        })
    except Exception as e:
        logger.error(f"预览附件失败: {e}", exc_info=True)
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

        data = request.get_json() or {}
        from app.services import task_service
        try:
            reply = task_service.add_reply(
                current_user, t, data.get('content'),
                subtask_id=data.get('subtask_id'),
                reply_type=data.get('reply_type') or 'comment')
        except ValueError as ve:
            return jsonify({'success': False, 'message': str(ve)}), 400

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
                'reply_type': reply.reply_type,
                'created_at': reply.created_at.isoformat() if reply.created_at else None,
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"添加回复失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@task.route('/api/<int:id>/comments', methods=['GET'])
@login_required
def list_comments(id):
    """评论/进展线程(兼容 at-comments 公用组件契约)。
    query: subtask_id(空=任务级) + reply_type(comment|update)。"""
    t = Task.query.filter_by(id=id, is_deleted=False).first()
    if not t:
        return jsonify({'success': False, 'message': '任务不存在'}), 404
    if not _can_access(t):
        return jsonify({'success': False, 'message': '无权访问'}), 403
    subtask_id = request.args.get('subtask_id', type=int)
    reply_type = request.args.get('reply_type', 'comment')
    q = TaskReply.query.options(joinedload(TaskReply.author)).filter_by(
        task_id=id, is_deleted=False, reply_type=reply_type)
    q = q.filter_by(subtask_id=subtask_id) if subtask_id else q.filter(TaskReply.subtask_id.is_(None))
    is_admin = current_user.role in ('admin', 'ceo')
    out = [{
        'id': r.id, 'owner_id': r.author_id,
        'owner_name': (r.author.real_name or r.author.username) if r.author else None,
        'content': r.content,
        'created_at': r.created_at.strftime('%Y-%m-%d %H:%M') if r.created_at else '',
        'can_delete': (r.author_id == current_user.id or is_admin or t.creator_id == current_user.id),
    } for r in q.order_by(TaskReply.created_at.asc()).all()]
    return jsonify({'success': True, 'comments': out})


@task.route('/api/<int:id>/comments', methods=['POST'])
@login_required
def add_comment(id):
    """新增评论/进展(兼容 at-comments)。subtask_id/reply_type 走 query。"""
    t = Task.query.filter_by(id=id, is_deleted=False).first()
    if not t:
        return jsonify({'success': False, 'message': '任务不存在'}), 404
    if not _can_access(t):
        return jsonify({'success': False, 'message': '无权操作'}), 403
    subtask_id = request.args.get('subtask_id', type=int)
    reply_type = request.args.get('reply_type', 'comment')
    data = request.get_json() or {}
    from app.services import task_service
    try:
        task_service.add_reply(current_user, t, data.get('content'), subtask_id=subtask_id, reply_type=reply_type)
    except ValueError as ve:
        return jsonify({'success': False, 'message': str(ve)}), 400
    return jsonify({'success': True})


@task.route('/api/<int:id>/comments/<int:cid>/delete', methods=['POST'])
@login_required
def delete_comment(id, cid):
    """删除评论/进展(兼容 at-comments 的 POST 删除)。"""
    r = TaskReply.query.filter_by(id=cid, task_id=id, is_deleted=False).first()
    if not r:
        return jsonify({'success': False, 'message': '评论不存在'}), 404
    from app.services import task_service
    try:
        task_service.delete_reply(current_user, r)
    except ValueError as ve:
        return jsonify({'success': False, 'message': str(ve)}), 403
    return jsonify({'success': True})


@task.route('/api/<int:id>/replies/<int:reply_id>', methods=['DELETE'])
@login_required
def delete_reply(id, reply_id):
    """删除评论/进展(软删除)。权限:作者/创建人/管理员。"""
    try:
        r = TaskReply.query.filter_by(id=reply_id, task_id=id, is_deleted=False).first()
        if not r:
            return jsonify({'success': False, 'message': '评论不存在'}), 404
        from app.services import task_service
        try:
            task_service.delete_reply(current_user, r)
        except ValueError as ve:
            return jsonify({'success': False, 'message': str(ve)}), 403
        return jsonify({'success': True, 'message': _('已删除')})
    except Exception as e:
        db.session.rollback()
        logger.error(f"删除评论失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500


@task.route('/management')
@login_required
def task_management():
    """[已由 AT 任务替代] 老 TW 任务页 → 重定向到 AT 任务,保留 task_id 深链。"""
    tid = request.args.get('task_id', type=int) or request.args.get('open', type=int) or request.args.get('task', type=int)
    if tid:
        return redirect(url_for('task.at_detail_view', id=tid))
    return redirect(url_for('task.at_list_view'))


@task.route('/management/_legacy')
@login_required
def task_management_legacy():
    """旧 TW 任务页(保留可达,以防排查);正常入口已全部指向 AT。"""
    team_members = []
    can_view_team = False

    is_admin = current_user.role in ('admin', 'ceo')
    is_dept_mgr = getattr(current_user, 'is_department_manager', False)
    # 公司级 task 权限（如 HR）：可查看本公司全部成员的任务
    is_company_viewer = current_user.get_permission_level('task') in ('company', 'system')

    if is_admin or is_dept_mgr or is_company_viewer:
        can_view_team = True

        # 先把有活跃任务的 assignee_id 取成 Python list，避免 ORM 子查询兼容性问题
        active_ids = [
            row[0] for row in db.session.query(Task.assignee_id).filter(
                Task.is_deleted == False,
                Task.status.notin_(['completed', 'cancelled']),
            ).distinct().all()
            if row[0] is not None
        ]

        if not active_ids:
            users = []
        elif is_admin:
            users = User.query.filter(
                User.id.in_(active_ids),
                User._is_active == True,
            ).order_by(User.real_name).all()
        elif is_company_viewer and current_user.company_name:
            # 公司级：本公司全部成员（不限部门）
            users = User.query.filter(
                User.id.in_(active_ids),
                User.company_name == current_user.company_name,
                User._is_active == True,
            ).order_by(User.real_name).all()
        elif is_dept_mgr and current_user.department and current_user.company_name:
            users = User.query.filter(
                User.id.in_(active_ids),
                User.department == current_user.department,
                User.company_name == current_user.company_name,
                User._is_active == True,
            ).order_by(User.real_name).all()
        else:
            # 部门经理字段未配置，不显示团队成员
            users = []
            can_view_team = False

        for u in users:
            if u.id == current_user.id:
                continue
            name = u.real_name or u.username
            team_members.append({
                'id': u.id,
                'name': name,
                'initials': name[:2] if name else '?',
            })

    return render_template(
        'task/tw_task_management.html',
        can_view_team=can_view_team,
        team_members=team_members,
    )


def _resolve_proxy_uid():
    """代理查看他人任务的 uid 解析(管理员/公司级 task 权限/部门负责人);无权限回落本人。"""
    uid = current_user.id
    view_user_id = request.args.get('view_user_id', type=int)
    if view_user_id and view_user_id != uid:
        is_admin = current_user.role in ('admin', 'ceo')
        is_dept_mgr = getattr(current_user, 'is_department_manager', False)
        is_company_viewer = current_user.get_permission_level('task') in ('company', 'system')
        if is_admin:
            uid = view_user_id
        elif is_company_viewer and current_user.company_name:
            target = User.query.get(view_user_id)
            if target and target._is_active and target.company_name == current_user.company_name:
                uid = view_user_id
        elif is_dept_mgr and current_user.department and current_user.company_name:
            target = User.query.get(view_user_id)
            if target and target._is_active \
                    and target.department == current_user.department \
                    and target.company_name == current_user.company_name:
                uid = view_user_id
    return uid


def _build_task_list_query(uid, tab='my', status='', search=''):
    """构建任务列表查询(不含排序/分页)。tab: my/created/shared/review/all。
    API(management_list)与 AT 页面(at_list_view)共用,避免重复。"""
    from app.models.subtask import MilestoneReviewer, SubTask
    query = Task.query.filter(Task.is_deleted == False)

    reviewer_task_ids = db.session.query(TaskReviewer.task_id).filter(
        TaskReviewer.reviewer_id == uid).scalar_subquery()
    milestone_task_ids = db.session.query(SubTask.task_id).join(
        MilestoneReviewer, MilestoneReviewer.subtask_id == SubTask.id).filter(
        MilestoneReviewer.reviewer_id == uid,
        MilestoneReviewer.status == 'pending').scalar_subquery()

    if tab == 'my':
        query = query.filter(Task.assignee_id == uid)
    elif tab == 'created':
        query = query.filter(Task.creator_id == uid)
    elif tab == 'shared':
        query = query.filter(Task.shared_with_users.cast(db.Text).contains(str(uid)))
    elif tab == 'review':
        query = query.filter(db.or_(
            Task.id.in_(reviewer_task_ids), Task.id.in_(milestone_task_ids)))
    else:  # all
        query = query.filter(db.or_(
            Task.assignee_id == uid, Task.creator_id == uid,
            Task.shared_with_users.cast(db.Text).contains(str(uid)),
            Task.id.in_(reviewer_task_ids), Task.id.in_(milestone_task_ids)))

    if status:
        query = query.filter(Task.status == status)
    if search:
        query = query.filter(Task.title.ilike(f'%{search}%'))
    return query


def _apply_task_sort(query, sort='updated'):
    """统一排序:已完成/已取消沉底。"""
    completed_last = db.case((Task.status.in_(['completed', 'cancelled']), 1), else_=0)
    if sort == 'due_date':
        return query.order_by(completed_last, Task.due_date.asc().nullslast(), Task.updated_at.desc())
    if sort == 'priority':
        priority_order = db.case(
            (Task.priority == 'urgent', 1), (Task.priority == 'high', 2),
            (Task.priority == 'normal', 3), (Task.priority == 'low', 4), else_=5)
        return query.order_by(completed_last, priority_order, Task.updated_at.desc())
    if sort == 'created':
        return query.order_by(completed_last, Task.created_at.desc())
    return query.order_by(completed_last, Task.updated_at.desc())


def _task_team_members(uid):
    """代理查看下拉的团队成员(管理员/公司级/部门负责人可见;含本人)。返回 (can_view, members)。"""
    is_admin = current_user.role in ('admin', 'ceo')
    is_dept_mgr = getattr(current_user, 'is_department_manager', False)
    is_company_viewer = current_user.get_permission_level('task') in ('company', 'system')
    if not (is_admin or is_dept_mgr or is_company_viewer):
        return False, []
    active_ids = [r[0] for r in db.session.query(Task.assignee_id).filter(
        Task.is_deleted == False, Task.status.notin_(['completed', 'cancelled'])
    ).distinct().all() if r[0] is not None]
    if not active_ids:
        return True, []
    q = User.query.filter(User.id.in_(active_ids), User._is_active == True)
    if is_admin:
        pass
    elif is_company_viewer and current_user.company_name:
        q = q.filter(User.company_name == current_user.company_name)
    elif is_dept_mgr and current_user.department and current_user.company_name:
        q = q.filter(User.department == current_user.department,
                     User.company_name == current_user.company_name)
    else:
        return False, []
    members = [{'id': u.id, 'name': u.real_name or u.username} for u in q.order_by(User.real_name).all()]
    return True, members


@task.route('/at')
@login_required
def at_list_view():
    """AT 风格任务列表(服务端渲染,复用 management_list 同款查询/排序/代理查看)。"""
    _auto_promote_pending_tasks()
    tab = request.args.get('tab', 'my')
    sort = request.args.get('sort', 'updated')
    status = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip()
    page = max(request.args.get('page', 1, type=int), 1)
    per_page = 30

    uid = _resolve_proxy_uid()
    view_user_id = request.args.get('view_user_id', type=int)
    can_view_team, team_members = _task_team_members(current_user.id)

    # 各 tab 计数(不带 status/search)
    tab_counts = {k: _build_task_list_query(uid, k).count()
                  for k in ('all', 'my', 'created', 'shared', 'review')}

    query = _apply_task_sort(_build_task_list_query(uid, tab, status, search), sort)
    pagination = query.options(
        joinedload(Task.creator), joinedload(Task.assignee), joinedload(Task.project),
    ).paginate(page=page, per_page=per_page, error_out=False)

    # 保留筛选态用于翻页链接
    list_qs = {}
    if status:
        list_qs['status'] = status
    if search:
        list_qs['search'] = search
    if sort and sort != 'updated':
        list_qs['sort'] = sort
    if view_user_id:
        list_qs['view_user_id'] = view_user_id

    team_options = [{'value': str(m['id']), 'label': m['name']} for m in team_members]

    return render_template(
        'task/at_list.html',
        tasks=[t.to_dict() for t in pagination.items], pagination=pagination,
        tab_counts=tab_counts, current_tab=tab,
        status=status, search=search, sort=sort,
        can_view_team=can_view_team, team_options=team_options,
        view_user_id=view_user_id, list_qs=list_qs,
    )


@task.route('/api/generate-title', methods=['POST'])
@login_required
def api_generate_title():
    """根据任务描述用 AI 生成简短标题(复用通用 generate_title,domain=task)。
    入参 {description};出参 {success, title}。"""
    from flask import session as flask_session
    data = request.get_json(silent=True) or {}
    description = (data.get('description') or '').strip()
    if not description:
        return jsonify({'success': True, 'title': ''})
    from app.services.expense_title_generator import generate_title
    lang = 'en' if flask_session.get('language') == 'en' else 'zh'
    try:
        title = generate_title(description, fallback='', lang=lang, domain='task')
    except Exception as e:
        logger.warning(f'task auto-title failed: {e}')
        return jsonify({'success': False, 'message': str(e)})
    return jsonify({'success': True, 'title': title or ''})


@task.route('/at/new')
@login_required
def at_create_view():
    """AT 风格新建任务(复用详情页表单基础设施,创建模式)。"""
    from app.helpers.task_types import task_type_groups_for, task_type_labels_for
    return render_template('task/at_detail.html', task_id='new', task_title=_('新建任务'),
                           task_type_groups=task_type_groups_for(current_user),
                           task_type_labels=task_type_labels_for(current_user))


@task.route('/at/<int:id>')
@login_required
def at_detail_view(id):
    """AT 风格任务详情(独立页 + 选卡)。数据由 /task/api/<id> 客户端拉取渲染。"""
    from flask import abort
    from app.helpers.task_types import task_type_groups_for, task_type_labels_for
    t = Task.query.filter_by(id=id, is_deleted=False).first()
    if not t:
        abort(404)
    if not _can_access(t):
        abort(403)
    return render_template('task/at_detail.html', task_id=id, task_title=t.title,
                           task_type_groups=task_type_groups_for(current_user),
                           task_type_labels=task_type_labels_for(current_user))


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

        uid = _resolve_proxy_uid()
        query = _build_task_list_query(uid, tab, status, search)
        total = query.count()
        query = _apply_task_sort(query, sort)
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

        data = request.get_json() or {}
        from app.services import task_service
        try:
            t, msg_text = task_service.review_task(
                current_user, t, data.get('action'), data.get('comment'), data.get('rating'))
        except ValueError as ve:
            return jsonify({'success': False, 'message': str(ve)}), 400
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
        from app.services import task_service
        try:
            task_service.resubmit_review(current_user, t)
        except ValueError as ve:
            return jsonify({'success': False, 'message': str(ve)}), 400
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

        from app.services import task_service
        try:
            subtask = task_service.create_subtask(current_user, t, data)
        except ValueError as ve:
            return jsonify({'success': False, 'message': str(ve)}), 400
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
        from app.services import task_service
        try:
            task_service.update_subtask(current_user, t, subtask, data)
        except ValueError as ve:
            return jsonify({'success': False, 'message': str(ve)}), 400
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

        from app.services import task_service
        task_service.delete_subtask(current_user, subtask)
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
        from app.services import task_service
        try:
            task_service.set_subtask_status(
                current_user, t, subtask, data.get('action'))
        except ValueError as ve:
            return jsonify({'success': False, 'message': str(ve)}), 400
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

        data = request.get_json() or {}
        from app.services import task_service
        try:
            subtask, msg_text = task_service.confirm_milestone(
                current_user, t, subtask, data.get('action'),
                data.get('comment') or '')
        except ValueError as ve:
            return jsonify({'success': False, 'message': str(ve)}), 400
        return jsonify({'success': True, 'message': msg_text, 'data': subtask.to_dict()})
    except Exception as e:
        db.session.rollback()
        logger.error(f"里程碑确认失败: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500
