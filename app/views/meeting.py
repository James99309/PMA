# -*- coding: utf-8 -*-
"""
会议录音与纪要模块 - 视图层

提供会议录音、转录、纪要生成和管理功能
"""
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, url_for, redirect, abort
from flask_login import login_required, current_user
from flask_babel import gettext as _
from zoneinfo import ZoneInfo

from app import db
from app.models.meeting import (
    MeetingRecording, MeetingTranscript, MeetingSpeaker,
    MeetingMinutes, MeetingActionItem
)
from app.models.worklog import WorkItem
from app.models.user import User
from app.models.project import Project
from app.models.customer import Company
from app.utils.access_control import get_viewable_data

logger = logging.getLogger(__name__)

meeting = Blueprint('meeting', __name__, url_prefix='/meeting')


def get_local_time():
    """获取本地时间（北京时区）"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


# ===== 权限检查工具函数 =====

def can_view_recording(user, recording):
    """检查用户是否可以查看录音"""
    # 创建者
    if recording.owner_id == user.id:
        return True
    # 管理员
    if user.role in ['admin', 'ceo']:
        return True
    # 参与者（通过纪要的参与者列表检查）
    if recording.minutes and recording.minutes.participants:
        participant_ids = [p.get('user_id') for p in recording.minutes.participants if p.get('user_id')]
        if user.id in participant_ids:
            return True
    # 关联的工作项参与者
    if recording.work_item and recording.work_item.shared_with_users:
        if user.id in recording.work_item.shared_with_users:
            return True
    return False


def can_edit_recording(user, recording):
    """检查用户是否可以编辑录音/纪要"""
    # 创建者
    if recording.owner_id == user.id:
        return True
    # 管理员
    if user.role in ['admin', 'ceo']:
        return True
    # 参与者可以编辑纪要
    if recording.minutes and recording.minutes.participants:
        participant_ids = [p.get('user_id') for p in recording.minutes.participants if p.get('user_id')]
        if user.id in participant_ids:
            return True
    return False


def can_delete_recording(user, recording):
    """检查用户是否可以删除录音"""
    # 只有创建者和管理员可以删除
    if recording.owner_id == user.id:
        return True
    if user.role in ['admin', 'ceo']:
        return True
    return False


# ===== 页面视图 =====

@meeting.route('/minutes')
@login_required
def minutes_list():
    """会议纪要列表页"""
    return render_template('meeting/tw_meeting_minutes_list.html')


@meeting.route('/recording/<int:recording_id>')
@login_required
def recording_page(recording_id):
    """录音进行中页面"""
    recording = MeetingRecording.query.get_or_404(recording_id)

    if not can_view_recording(current_user, recording):
        abort(403)

    return render_template(
        'meeting/tw_meeting_recording.html',
        recording=recording
    )


@meeting.route('/minutes/<int:recording_id>')
@login_required
def minutes_detail(recording_id):
    """纪要详情页"""
    recording = MeetingRecording.query.get_or_404(recording_id)

    if not can_view_recording(current_user, recording):
        abort(403)

    return render_template(
        'meeting/tw_meeting_minutes_detail.html',
        recording=recording
    )


# ===== API 端点 =====

@meeting.route('/api/config-status', methods=['GET'])
@login_required
def api_config_status():
    """检查会议录音功能的配置状态"""
    try:
        from app.services.meeting_service import MeetingService
        status = MeetingService.validate_api_configuration()
        return jsonify({
            'success': True,
            **status
        })
    except Exception as e:
        logger.error(f'检查配置状态失败: {e}')
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@meeting.route('/api/recordings', methods=['GET'])
@login_required
def api_list_recordings():
    """获取录音列表"""
    # 筛选参数
    status = request.args.get('status', '')
    search = request.args.get('search', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # 基础查询
    query = MeetingRecording.query.filter(MeetingRecording.is_deleted == False)

    # 权限过滤：只显示用户可见的录音
    if current_user.role not in ['admin', 'ceo']:
        # 自己创建的 + 参与的（通过工作项共享）
        query = query.filter(
            db.or_(
                MeetingRecording.owner_id == current_user.id,
                # 通过工作项关联的参与者
                MeetingRecording.work_item_id.in_(
                    db.session.query(WorkItem.id).filter(
                        WorkItem.shared_with_users.contains([current_user.id])
                    )
                )
            )
        )

    # 状态筛选
    if status:
        if status == 'transcribing':
            query = query.filter(MeetingRecording.status.in_(['transcribing', 'uploaded']))
        elif status == 'pending_mapping':
            query = query.join(MeetingTranscript).filter(
                MeetingTranscript.status == 'completed',
                MeetingTranscript.speakers_mapped == False
            )
        elif status == 'draft':
            query = query.join(MeetingMinutes).filter(MeetingMinutes.status == 'draft')
        elif status == 'published':
            query = query.join(MeetingMinutes).filter(MeetingMinutes.status == 'published')
        else:
            query = query.filter(MeetingRecording.status == status)

    # 搜索
    if search:
        query = query.filter(
            db.or_(
                MeetingRecording.title.ilike(f'%{search}%'),
                MeetingRecording.owner.has(User.real_name.ilike(f'%{search}%'))
            )
        )

    # 排序和分页
    query = query.order_by(MeetingRecording.created_at.desc())
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    recordings = []
    for rec in pagination.items:
        rec_data = rec.to_dict()

        # 添加纪要信息
        if rec.minutes:
            rec_data['minutes'] = {
                'id': rec.minutes.id,
                'status': rec.minutes.status,
                'summary': rec.minutes.summary[:100] if rec.minutes.summary else None,
                'action_items_count': len([a for a in rec.minutes.action_items if not a.is_deleted])
            }

        # 添加转录状态
        if rec.transcript:
            rec_data['transcript'] = {
                'status': rec.transcript.status,
                'speakers_mapped': rec.transcript.speakers_mapped,
                'speaker_count': rec.transcript.speaker_count
            }

        # 添加项目和客户信息
        if rec.work_item:
            if rec.work_item.project:
                rec_data['project_name'] = rec.work_item.project.project_name
            if rec.work_item.customer:
                rec_data['customer_name'] = rec.work_item.customer.company_name
            # 参与者
            if rec.work_item.shared_with_users:
                participants = User.query.filter(User.id.in_(rec.work_item.shared_with_users)).all()
                rec_data['participants'] = [u.real_name or u.username for u in participants]

        recordings.append(rec_data)

    return jsonify({
        'success': True,
        'recordings': recordings,
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages
        }
    })


@meeting.route('/api/recordings', methods=['POST'])
@login_required
def api_create_recording():
    """创建新的录音记录"""
    data = request.get_json()

    work_item_id = data.get('work_item_id')
    title = data.get('title', '')
    recording_mode = data.get('recording_mode', 'microphone')

    # 如果关联工作项，获取工作项信息
    work_item = None
    if work_item_id:
        work_item = WorkItem.query.get(work_item_id)
        if work_item:
            if not title:
                title = work_item.title

    # 如果没有标题，生成默认标题
    if not title:
        title = f'{get_local_time().strftime("%Y-%m-%d %H:%M")} 会议录音'

    recording = MeetingRecording(
        work_item_id=work_item_id,
        title=title,
        meeting_time=get_local_time(),
        recording_mode=recording_mode,
        status='recording',
        owner_id=current_user.id
    )

    db.session.add(recording)
    db.session.commit()

    return jsonify({
        'success': True,
        'recording': recording.to_dict(),
        'redirect_url': url_for('meeting.recording_page', recording_id=recording.id)
    })


@meeting.route('/api/recordings/<int:recording_id>', methods=['GET'])
@login_required
def api_get_recording(recording_id):
    """获取录音详情"""
    recording = MeetingRecording.query.get_or_404(recording_id)

    if not can_view_recording(current_user, recording):
        return jsonify({'success': False, 'message': _('无权访问')}), 403

    data = recording.to_dict()

    # 添加详细信息
    if recording.transcript:
        data['transcript'] = recording.transcript.to_dict(include_segments=True)
        data['speakers'] = [s.to_dict() for s in recording.transcript.speakers]

    if recording.minutes:
        data['minutes'] = recording.minutes.to_dict(include_content=True)

    # 添加权限信息
    data['can_edit'] = can_edit_recording(current_user, recording)
    data['can_delete'] = can_delete_recording(current_user, recording)

    return jsonify({
        'success': True,
        'recording': data
    })


@meeting.route('/api/recordings/<int:recording_id>/upload-chunk', methods=['POST'])
@login_required
def api_upload_chunk(recording_id):
    """上传录音分块"""
    recording = MeetingRecording.query.get_or_404(recording_id)

    if recording.owner_id != current_user.id:
        return jsonify({'success': False, 'message': _('无权操作')}), 403

    chunk_index = request.form.get('chunk_index', 0, type=int)
    is_final = request.form.get('is_final', 'false').lower() == 'true'
    chunk_file = request.files.get('chunk')
    duration = request.form.get('duration', 0, type=int)

    if not chunk_file:
        return jsonify({'success': False, 'message': _('缺少文件')}), 400

    try:
        from app.services.meeting_service import MeetingService

        # 读取分块数据
        chunk_data = chunk_file.read()

        # 使用 MeetingService 上传
        result = MeetingService.upload_audio_chunk(
            recording_id=recording_id,
            chunk_data=chunk_data,
            chunk_index=chunk_index,
            is_final=is_final
        )

        if not result['success']:
            return jsonify(result), 500

        # 更新录音时长
        if duration > 0:
            recording.duration = duration

        if recording.status == 'recording':
            recording.status = 'uploading'

        db.session.commit()

        return jsonify({
            'success': True,
            'chunk_index': result.get('chunk_index'),
            'chunk_path': result.get('chunk_path')
        })

    except Exception as e:
        logger.error(f'上传录音分块失败: {e}')
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500


@meeting.route('/api/recordings/<int:recording_id>/stop', methods=['POST'])
@login_required
def api_stop_recording(recording_id):
    """停止录音"""
    recording = MeetingRecording.query.get_or_404(recording_id)

    if recording.owner_id != current_user.id:
        return jsonify({'success': False, 'message': _('无权操作')}), 403

    data = request.get_json()
    duration_seconds = data.get('duration_seconds', 0)

    recording.duration_seconds = duration_seconds
    recording.status = 'uploaded'

    db.session.commit()

    return jsonify({
        'success': True,
        'recording': recording.to_dict(),
        'redirect_url': url_for('meeting.minutes_detail', recording_id=recording.id)
    })


@meeting.route('/api/recordings/<int:recording_id>/transcribe', methods=['POST'])
@login_required
def api_start_transcription(recording_id):
    """开始转录"""
    recording = MeetingRecording.query.get_or_404(recording_id)

    if not can_edit_recording(current_user, recording):
        return jsonify({'success': False, 'message': _('无权操作')}), 403

    if recording.status not in ['uploaded', 'merged', 'transcription_failed']:
        return jsonify({'success': False, 'message': _('当前状态无法开始转录')}), 400

    try:
        from app.services.meeting_service import MeetingService

        # 如果还没合并音频，先合并
        if recording.status == 'uploaded' and recording.audio_chunks:
            merge_result = MeetingService.merge_audio_chunks(recording_id)
            if not merge_result['success']:
                return jsonify({
                    'success': False,
                    'message': _('音频合并失败：') + merge_result.get('error', '')
                }), 500

        # 调用 Whisper 转录
        result = MeetingService.transcribe_audio(recording_id)

        if result['success']:
            return jsonify({
                'success': True,
                'message': _('转录已完成'),
                'transcript_id': result.get('transcript_id'),
                'segments_count': result.get('segments_count', 0)
            })
        else:
            return jsonify({
                'success': False,
                'message': _('转录失败：') + result.get('error', '')
            }), 500

    except Exception as e:
        logger.error(f'转录失败: {e}')
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500


@meeting.route('/api/transcripts/<int:transcript_id>/identify-speakers', methods=['POST'])
@login_required
def api_identify_speakers(transcript_id):
    """识别说话人"""
    transcript = MeetingTranscript.query.get_or_404(transcript_id)
    recording = transcript.recording

    if not can_edit_recording(current_user, recording):
        return jsonify({'success': False, 'message': _('无权操作')}), 403

    data = request.get_json() or {}
    num_speakers = data.get('num_speakers')

    try:
        from app.services.meeting_service import MeetingService

        result = MeetingService.identify_speakers(
            transcript_id=transcript_id,
            num_speakers=num_speakers
        )

        if result['success']:
            return jsonify({
                'success': True,
                'message': _('说话人识别完成'),
                'speakers': result.get('speakers', []),
                'speakers_count': result.get('speakers_count', 0)
            })
        else:
            return jsonify({
                'success': False,
                'message': _('说话人识别失败：') + result.get('error', '')
            }), 500

    except Exception as e:
        logger.error(f'说话人识别失败: {e}')
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500


@meeting.route('/api/transcripts/<int:transcript_id>/speakers', methods=['POST'])
@login_required
def api_map_speakers(transcript_id):
    """映射说话人"""
    transcript = MeetingTranscript.query.get_or_404(transcript_id)
    recording = transcript.recording

    if not can_edit_recording(current_user, recording):
        return jsonify({'success': False, 'message': _('无权操作')}), 403

    data = request.get_json()
    mappings = data.get('mappings', [])  # [{speaker_id, user_id, external_name}]

    for mapping in mappings:
        speaker = MeetingSpeaker.query.get(mapping.get('speaker_id'))
        if speaker and speaker.transcript_id == transcript_id:
            speaker.user_id = mapping.get('user_id')
            speaker.external_name = mapping.get('external_name')

    transcript.speakers_mapped = True
    db.session.commit()

    # 更新纪要的参与者列表
    if recording.minutes:
        participants = []
        for speaker in transcript.speakers:
            if speaker.user_id:
                user = User.query.get(speaker.user_id)
                participants.append({
                    'user_id': speaker.user_id,
                    'name': user.real_name or user.username if user else speaker.speaker_label,
                    'is_external': False
                })
            elif speaker.external_name:
                participants.append({
                    'user_id': None,
                    'name': speaker.external_name,
                    'is_external': True
                })
        recording.minutes.participants = participants
        db.session.commit()

    return jsonify({
        'success': True,
        'message': _('说话人映射已保存')
    })


@meeting.route('/api/recordings/<int:recording_id>/generate-minutes', methods=['POST'])
@login_required
def api_generate_minutes(recording_id):
    """生成会议纪要"""
    recording = MeetingRecording.query.get_or_404(recording_id)

    if not can_edit_recording(current_user, recording):
        return jsonify({'success': False, 'message': _('无权操作')}), 403

    # 检查转录状态
    transcript = MeetingTranscript.query.filter_by(
        recording_id=recording_id
    ).order_by(MeetingTranscript.id.desc()).first()

    if not transcript or transcript.status != 'completed':
        return jsonify({'success': False, 'message': _('转录未完成')}), 400

    data = request.get_json() or {}
    generation_style = data.get('style', 'standard')  # standard, detailed, brief

    try:
        from app.services.meeting_service import MeetingService

        # 调用 AI 生成纪要
        result = MeetingService.generate_minutes(
            recording_id=recording_id,
            style=generation_style
        )

        if result['success']:
            return jsonify({
                'success': True,
                'message': _('纪要生成完成'),
                'minutes_id': result.get('minutes_id'),
                'title': result.get('title'),
                'summary': result.get('summary'),
                'action_items_count': result.get('action_items_count', 0)
            })
        else:
            return jsonify({
                'success': False,
                'message': _('纪要生成失败：') + result.get('error', '')
            }), 500

    except Exception as e:
        logger.error(f'生成纪要失败: {e}')
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500


@meeting.route('/api/minutes/<int:minutes_id>', methods=['PUT'])
@login_required
def api_update_minutes(minutes_id):
    """更新会议纪要"""
    minutes = MeetingMinutes.query.get_or_404(minutes_id)

    if not can_edit_recording(current_user, minutes.recording):
        return jsonify({'success': False, 'message': _('无权操作')}), 403

    data = request.get_json()

    # 更新字段
    if 'title' in data:
        minutes.title = data['title']
    if 'summary' in data:
        minutes.summary = data['summary']
    if 'key_points' in data:
        minutes.key_points = data['key_points']
    if 'decisions' in data:
        minutes.decisions = data['decisions']
    if 'project_id' in data:
        minutes.project_id = data['project_id'] if data['project_id'] else None
    if 'customer_id' in data:
        minutes.customer_id = data['customer_id'] if data['customer_id'] else None

    db.session.commit()

    return jsonify({
        'success': True,
        'minutes': minutes.to_dict()
    })


@meeting.route('/api/minutes/<int:minutes_id>/publish', methods=['POST'])
@login_required
def api_publish_minutes(minutes_id):
    """发布会议纪要"""
    minutes = MeetingMinutes.query.get_or_404(minutes_id)

    if not can_edit_recording(current_user, minutes.recording):
        return jsonify({'success': False, 'message': _('无权操作')}), 403

    minutes.status = 'published'
    minutes.published_at = get_local_time()

    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('纪要已发布')
    })


@meeting.route('/api/action-items/<int:action_id>', methods=['PUT'])
@login_required
def api_update_action_item(action_id):
    """更新行动项"""
    action = MeetingActionItem.query.get_or_404(action_id)
    minutes = action.minutes

    if not can_edit_recording(current_user, minutes.recording):
        return jsonify({'success': False, 'message': _('无权操作')}), 403

    data = request.get_json()

    if 'title' in data:
        action.title = data['title']
    if 'description' in data:
        action.description = data['description']
    if 'assignee_id' in data:
        action.assignee_id = data['assignee_id'] if data['assignee_id'] else None
    if 'assignee_name' in data:
        action.assignee_name = data['assignee_name']
    if 'due_date' in data:
        action.due_date = datetime.fromisoformat(data['due_date']) if data['due_date'] else None
    if 'status' in data:
        action.status = data['status']
        if data['status'] == 'completed':
            action.completed_at = get_local_time()

    db.session.commit()

    return jsonify({
        'success': True,
        'action_item': action.to_dict()
    })


@meeting.route('/api/action-items/<int:action_id>/add-to-calendar', methods=['POST'])
@login_required
def api_action_to_calendar(action_id):
    """将行动项添加到工作日历"""
    action = MeetingActionItem.query.get_or_404(action_id)
    minutes = action.minutes

    if not can_edit_recording(current_user, minutes.recording):
        return jsonify({'success': False, 'message': _('无权操作')}), 403

    # 创建工作项
    work_item = WorkItem(
        title=action.title,
        description=f"来源：{minutes.title}\n\n{action.description or ''}",
        planned_date=action.due_date.date() if action.due_date else get_local_time().date(),
        work_type='meeting',  # 会议类型
        status='planned',
        owner_id=action.assignee_id or current_user.id,
        project_id=minutes.project_id,
        customer_id=minutes.customer_id
    )

    db.session.add(work_item)
    db.session.flush()

    # 关联到行动项
    action.linked_work_item_id = work_item.id

    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('已添加到工作日历'),
        'work_item_id': work_item.id
    })


@meeting.route('/api/recordings/<int:recording_id>', methods=['DELETE'])
@login_required
def api_delete_recording(recording_id):
    """删除录音（软删除）"""
    recording = MeetingRecording.query.get_or_404(recording_id)

    if not can_delete_recording(current_user, recording):
        return jsonify({'success': False, 'message': _('无权操作')}), 403

    data = request.get_json() or {}
    delete_files = data.get('delete_files', False)

    # 软删除
    recording.is_deleted = True
    if recording.minutes:
        recording.minutes.is_deleted = True

    # TODO: 如果 delete_files=True，删除存储中的文件

    db.session.commit()

    return jsonify({
        'success': True,
        'message': _('已删除')
    })


# ===== 音频代理路由（用于群晖WebDAV存储） =====

@meeting.route('/audio/stream')
@login_required
def audio_stream():
    """
    音频流代理 - 从群晖WebDAV获取音频文件

    支持Range请求，用于音频seek功能
    Query参数:
    - path: 远程文件路径（相对于base_path）
    """
    from flask import Response, make_response
    import os

    remote_path = request.args.get('path', '')
    if not remote_path:
        abort(400, description='缺少文件路径参数')

    # 安全检查：防止路径遍历攻击
    if '..' in remote_path or remote_path.startswith('/'):
        if not remote_path.startswith('/meetings/'):
            abort(400, description='无效的文件路径')

    # 从路径中提取 recording_id 进行权限检查
    # 路径格式: /meetings/{recording_id}/xxx.webm
    path_parts = remote_path.strip('/').split('/')
    if len(path_parts) >= 2 and path_parts[0] == 'meetings':
        try:
            recording_id = int(path_parts[1])
            recording = MeetingRecording.query.get(recording_id)
            if recording and not can_view_recording(current_user, recording):
                abort(403, description='无权访问此录音')
        except (ValueError, IndexError):
            pass  # 无法解析ID，跳过权限检查

    storage_type = os.environ.get('MEETING_STORAGE_TYPE', 'synology').lower()

    if storage_type == 'synology':
        # 从群晖WebDAV获取
        from app.utils.synology_webdav_client import get_synology_webdav_client
        webdav = get_synology_webdav_client()

        if not webdav.is_configured:
            abort(503, description='群晖WebDAV未配置')

        # 获取文件信息
        file_info = webdav.get_file_info(remote_path)
        if not file_info:
            abort(404, description='文件不存在')

        content_length = file_info.get('content_length', 0)
        content_type = file_info.get('content_type', 'audio/webm')

        # 处理Range请求
        range_header = request.headers.get('Range')
        if range_header:
            # 解析Range头
            import re
            match = re.match(r'bytes=(\d+)-(\d*)', range_header)
            if match:
                start = int(match.group(1))
                end = int(match.group(2)) if match.group(2) else content_length - 1

                # 确保范围有效
                if start >= content_length:
                    abort(416, description='Range Not Satisfiable')

                end = min(end, content_length - 1)

                # 获取指定范围的数据
                data = webdav.download_file_range(remote_path, start, end)
                if data is None:
                    abort(500, description='下载文件失败')

                # 返回206 Partial Content
                response = make_response(data)
                response.status_code = 206
                response.headers['Content-Type'] = content_type
                response.headers['Content-Length'] = len(data)
                response.headers['Content-Range'] = f'bytes {start}-{end}/{content_length}'
                response.headers['Accept-Ranges'] = 'bytes'
                return response

        # 完整文件下载（流式）
        def generate():
            for chunk in webdav.download_file_stream(remote_path):
                yield chunk

        return Response(
            generate(),
            mimetype=content_type,
            headers={
                'Content-Length': str(content_length),
                'Accept-Ranges': 'bytes',
                'Cache-Control': 'no-cache'
            }
        )

    elif storage_type == 'local':
        # 本地文件
        from flask import send_file, current_app
        local_storage_root = current_app.config.get('LOCAL_STORAGE_ROOT', './storage')
        local_path = os.path.join(local_storage_root, remote_path.lstrip('/'))

        if not os.path.exists(local_path):
            abort(404, description='文件不存在')

        return send_file(
            local_path,
            mimetype='audio/webm',
            as_attachment=False
        )

    else:
        # Supabase - 直接重定向到公开URL
        recording_id = None
        path_parts = remote_path.strip('/').split('/')
        if len(path_parts) >= 2 and path_parts[0] == 'meetings':
            try:
                recording_id = int(path_parts[1])
            except ValueError:
                pass

        if recording_id:
            recording = MeetingRecording.query.get(recording_id)
            if recording and recording.audio_url:
                return redirect(recording.audio_url)

        abort(404, description='文件不存在')


@meeting.route('/audio/<int:recording_id>')
@login_required
def audio_by_recording(recording_id):
    """
    通过录音ID获取音频文件

    自动处理不同存储类型
    """
    from flask import Response, make_response, send_file
    import os

    recording = MeetingRecording.query.get_or_404(recording_id)

    if not can_view_recording(current_user, recording):
        abort(403, description='无权访问此录音')

    if not recording.audio_url:
        abort(404, description='音频文件不存在')

    storage_type = getattr(recording, 'storage_type', None) or \
                   os.environ.get('MEETING_STORAGE_TYPE', 'synology').lower()

    if storage_type == 'synology':
        # 从群晖WebDAV获取
        from app.utils.synology_webdav_client import get_synology_webdav_client
        webdav = get_synology_webdav_client()

        if not webdav.is_configured:
            abort(503, description='群晖WebDAV未配置')

        remote_path = recording.audio_url

        # 获取文件信息
        file_info = webdav.get_file_info(remote_path)
        if not file_info:
            abort(404, description='文件不存在')

        content_length = file_info.get('content_length', 0)
        content_type = file_info.get('content_type', 'audio/webm')

        # 处理Range请求
        range_header = request.headers.get('Range')
        if range_header:
            import re
            match = re.match(r'bytes=(\d+)-(\d*)', range_header)
            if match:
                start = int(match.group(1))
                end = int(match.group(2)) if match.group(2) else content_length - 1

                if start >= content_length:
                    abort(416, description='Range Not Satisfiable')

                end = min(end, content_length - 1)

                data = webdav.download_file_range(remote_path, start, end)
                if data is None:
                    abort(500, description='下载文件失败')

                response = make_response(data)
                response.status_code = 206
                response.headers['Content-Type'] = content_type
                response.headers['Content-Length'] = len(data)
                response.headers['Content-Range'] = f'bytes {start}-{end}/{content_length}'
                response.headers['Accept-Ranges'] = 'bytes'
                return response

        # 完整文件下载（流式）
        def generate():
            for chunk in webdav.download_file_stream(remote_path):
                yield chunk

        return Response(
            generate(),
            mimetype=content_type,
            headers={
                'Content-Length': str(content_length),
                'Accept-Ranges': 'bytes',
                'Cache-Control': 'no-cache'
            }
        )

    elif storage_type == 'local':
        from flask import current_app
        local_storage_root = current_app.config.get('LOCAL_STORAGE_ROOT', './storage')
        local_path = recording.audio_url.replace('/storage/', local_storage_root + '/')

        if not os.path.exists(local_path):
            abort(404, description='文件不存在')

        return send_file(
            local_path,
            mimetype='audio/webm',
            as_attachment=False
        )

    else:
        # Supabase - 重定向到公开URL
        return redirect(recording.audio_url)


@meeting.route('/audio/<int:recording_id>/info')
@login_required
def audio_info(recording_id):
    """获取音频文件信息"""
    import os

    recording = MeetingRecording.query.get_or_404(recording_id)

    if not can_view_recording(current_user, recording):
        return jsonify({'success': False, 'message': _('无权访问')}), 403

    if not recording.audio_url:
        return jsonify({'success': False, 'message': _('音频文件不存在')}), 404

    storage_type = getattr(recording, 'storage_type', None) or \
                   os.environ.get('MEETING_STORAGE_TYPE', 'synology').lower()

    info = {
        'recording_id': recording_id,
        'storage_type': storage_type,
        'duration': recording.duration,
        'file_size': recording.file_size
    }

    if storage_type == 'synology':
        from app.utils.synology_webdav_client import get_synology_webdav_client
        webdav = get_synology_webdav_client()

        if webdav.is_configured:
            file_info = webdav.get_file_info(recording.audio_url)
            if file_info:
                info['content_length'] = file_info.get('content_length')
                info['content_type'] = file_info.get('content_type')
                info['last_modified'] = file_info.get('last_modified')

    # 生成流式播放URL
    info['stream_url'] = url_for('meeting.audio_by_recording', recording_id=recording_id)

    return jsonify({
        'success': True,
        'info': info
    })
