# -*- coding: utf-8 -*-
"""
通用任务模块 - 视图层

提供任务 CRUD、附件管理、回复和日历事件源 API
"""
import logging
from datetime import datetime, date
from zoneinfo import ZoneInfo
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from flask_babel import gettext as _
from sqlalchemy.orm import joinedload

from app import db, csrf
from app.models.task import Task, TaskAttachment, TaskReply

logger = logging.getLogger(__name__)

task = Blueprint('task', __name__, url_prefix='/task')
csrf.exempt(task)


def get_local_time():
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


def _can_edit(t):
    """创建者可编辑/取消/删除"""
    return t.creator_id == current_user.id


def _can_access(t):
    """创建者或被指派人可访问"""
    return t.creator_id == current_user.id or t.assignee_id == current_user.id


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

        # 处理截止日期
        due_date_str = data.get('due_date')
        if due_date_str:
            try:
                new_task.due_date = datetime.fromisoformat(due_date_str)
            except (ValueError, TypeError):
                pass

        # calendar_date 默认与 due_date 一致
        if new_task.due_date:
            new_task.calendar_date = new_task.due_date.date()

        db.session.add(new_task)
        db.session.flush()  # 获取 id

        # 发送通知给被指派人
        if new_task.assignee_id != current_user.id:
            try:
                from app.models.message import Message
                msg = Message.create_task_assigned(
                    sender_id=current_user.id,
                    recipient_id=new_task.assignee_id,
                    task=new_task
                )
                db.session.add(msg)
            except Exception as e:
                logger.warning(f"发送任务通知失败: {e}")

        db.session.commit()

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
            'content': r.content,
            'created_at': r.created_at.isoformat() if r.created_at else None,
        } for r in replies]

        # 权限标识
        task_dict['can_edit'] = _can_edit(t)
        task_dict['can_complete'] = t.assignee_id == current_user.id
        task_dict['is_creator'] = t.creator_id == current_user.id

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

        if 'status' in data and data['status'] in ('pending', 'in_progress'):
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
    """完成任务"""
    try:
        t = Task.query.filter_by(id=id, is_deleted=False).first()
        if not t:
            return jsonify({'success': False, 'message': '任务不存在'}), 404
        if t.assignee_id != current_user.id and t.creator_id != current_user.id:
            return jsonify({'success': False, 'message': '无权完成此任务'}), 403

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

        attachment = TaskAttachment(
            task_id=id,
            filename=filename,
            storage_path=result.get('storage_path', ''),
            file_size=file_size,
            file_type=file_ext,
            uploaded_by=current_user.id,
        )
        db.session.add(attachment)
        db.session.commit()

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

        reply = TaskReply(
            task_id=id,
            author_id=current_user.id,
            content=content,
        )
        db.session.add(reply)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': _('回复成功'),
            'data': {
                'id': reply.id,
                'author_id': reply.author_id,
                'author_name': (reply.author.real_name or reply.author.username) if reply.author else None,
                'content': reply.content,
                'created_at': reply.created_at.isoformat() if reply.created_at else None,
            }
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"添加回复失败: {e}", exc_info=True)
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
        tasks = Task.query.filter(
            db.or_(Task.assignee_id == current_user.id, Task.creator_id == current_user.id),
            Task.is_deleted == False,
            Task.status.in_(['pending', 'in_progress'])
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
