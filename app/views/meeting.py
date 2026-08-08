# -*- coding: utf-8 -*-
"""
会议录音与纪要模块 - 视图层

提供会议录音、转录、纪要生成和管理功能
"""
import logging
import os
import json
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, url_for, redirect, abort
from flask_login import login_required, current_user
from flask_babel import gettext as _
from zoneinfo import ZoneInfo

from sqlalchemy import cast, text
from sqlalchemy.dialects.postgresql import JSONB
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
from app.services.claude_vision_ocr import first_text

logger = logging.getLogger(__name__)

meeting = Blueprint('meeting', __name__, url_prefix='/meeting')


# 实时翻译滚动上下文：把上一段转录文本作为下一 chunk 的 Whisper prompt
# key: (recording_id, speaker)  value: str（最近一段原文，限制长度避免超 prompt token）
# 注：进程内字典，多 worker 不共享——单 worker dev 够用，prod 用 gunicorn 单 worker / 或后续换 Redis
_REALTIME_CTX_MAX_CHARS = 220   # Whisper prompt 上限 224 tokens，保守取字符数
_realtime_history = {}

# 跨 chunk 重复检测：保存最近 N 段的归一化文本，命中即判定为幻觉
_REALTIME_DEDUP_WINDOW = 3
_realtime_recent_texts = {}     # key: (recording_id, speaker)  value: list[str]


def _push_realtime_history(recording_id, speaker, text_chunk):
    if not text_chunk:
        return
    key = (recording_id, speaker)
    prev = _realtime_history.get(key, '')
    combined = (prev + ' ' + text_chunk).strip() if prev else text_chunk.strip()
    if len(combined) > _REALTIME_CTX_MAX_CHARS:
        combined = combined[-_REALTIME_CTX_MAX_CHARS:]
    _realtime_history[key] = combined


def _get_realtime_history(recording_id, speaker):
    return _realtime_history.get((recording_id, speaker), '')


def _clear_realtime_history(recording_id):
    for k in list(_realtime_history.keys()):
        if k[0] == recording_id:
            _realtime_history.pop(k, None)
    for k in list(_realtime_recent_texts.keys()):
        if k[0] == recording_id:
            _realtime_recent_texts.pop(k, None)


def _normalize_for_dedup(text):
    """归一化：去标点空白、小写，用于跨 chunk 比对"""
    import re
    return re.sub(r'[\s　\W_]+', '', (text or '').lower(), flags=re.UNICODE)


def _is_recent_duplicate(recording_id, speaker, text):
    """如果归一化后与最近 N 段任一相同 → True；否则把当前 push 进窗口并 False"""
    norm = _normalize_for_dedup(text)
    if not norm or len(norm) < 3:
        return False  # 太短不参与去重
    key = (recording_id, speaker)
    recent = _realtime_recent_texts.get(key, [])
    hit = norm in recent
    if not hit:
        recent.append(norm)
        if len(recent) > _REALTIME_DEDUP_WINDOW:
            recent = recent[-_REALTIME_DEDUP_WINDOW:]
        _realtime_recent_texts[key] = recent
    return hit


def _is_hallucinated_segment(text):
    """Whisper 对静音/低信噪比段会"幻觉"出重复填充词（中文最常见"嗯,嗯,嗯..."，
    英文是"Thank you. Thank you."）。这种段无信息价值，丢弃。

    判定（任一命中即丢）：
    - 去标点后单字符占比 > 70%（"嗯,嗯,嗯,嗯..."→"嗯"占 100%）
    - 去标点后不同字符数 ≤ 2 且 总长 ≥ 6
    - 英文同 token 重复 ≥ 5 次或占比 > 70%
    - 太短不判（< 6 字），保留真实的"嗯。"等简短回应
    """
    import re
    if not text or not text.strip():
        return True
    stripped = text.strip()
    if len(stripped) < 6:
        return False
    # 中文字符级
    clean = re.sub(r'[\s　\W_]+', '', stripped, flags=re.UNICODE)
    if len(clean) >= 6:
        counts = {}
        for c in clean:
            counts[c] = counts.get(c, 0) + 1
        top = max(counts.values())
        if top / len(clean) > 0.7:
            return True
        if len(counts) <= 2:
            return True
    # 英文 token 级
    tokens = re.findall(r'[A-Za-z]+', stripped.lower())
    if len(tokens) >= 5:
        tc = {}
        for t in tokens:
            tc[t] = tc.get(t, 0) + 1
        top = max(tc.values())
        if top >= 5 or top / len(tokens) > 0.7:
            return True
    return False


def get_local_time():
    """获取本地时间（北京时区）"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


# Whisper vocab prompt 缓存（recording_id -> prompt str）
# 录音生命周期内 owner + 邀请人列表基本不变；中途追加邀请人时通过 invite API 清缓存
_vocab_prompt_cache = {}


def _build_vocab_prompt(recording):
    """拼接参会人真实姓名作为 Whisper initial_prompt 前缀，
    针对人名同音字（如"倪捷"被识别成"你姐"）做硬纠正。

    A 方案：只用 real_name，不分语言。约 30-60 字符。
    """
    rid = getattr(recording, 'id', None)
    if rid and rid in _vocab_prompt_cache:
        return _vocab_prompt_cache[rid]

    names = []
    try:
        owner = getattr(recording, 'owner', None)
        if owner and getattr(owner, 'real_name', None):
            names.append(owner.real_name)
        invited_ids = recording.invited_user_ids or []
        if invited_ids:
            from app.models.user import User as _User
            for u in _User.query.filter(_User.id.in_(invited_ids)).all():
                if u.real_name and u.real_name not in names:
                    names.append(u.real_name)
    except Exception:
        pass

    prompt = f"参会人:{'、'.join(names)}。" if names else ''
    if rid is not None:
        _vocab_prompt_cache[rid] = prompt
    return prompt


def _clear_vocab_cache(recording_id):
    _vocab_prompt_cache.pop(recording_id, None)


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
    # 被邀请旁听的同事
    if recording.invited_user_ids and user.id in recording.invited_user_ids:
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
    """会议纪要列表页 - 服务端渲染"""
    from datetime import timedelta

    search = request.args.get('search', '').strip()
    status = request.args.get('status', '')
    mode = request.args.get('mode', '')
    owner_id = request.args.get('owner_id', '')
    time_range = request.args.get('time_range', '')

    query = MeetingRecording.query.filter(MeetingRecording.is_deleted == False)

    # 权限过滤（同 api_list_recordings）
    if current_user.role not in ['admin', 'ceo']:
        query = query.filter(
            db.or_(
                MeetingRecording.owner_id == current_user.id,
                MeetingRecording.work_item_id.in_(
                    db.session.query(WorkItem.id).filter(
                        cast(WorkItem.shared_with_users, JSONB).op('@>')(text(f"'[{current_user.id}]'::jsonb"))
                    )
                ),
                cast(MeetingRecording.invited_user_ids, JSONB).op('@>')(text(f"'[{current_user.id}]'::jsonb"))
            )
        )

    if status:
        # 4 个用户感知状态映射回原始 status：
        if status == 'recording':
            query = query.filter(MeetingRecording.status.in_(['recording', 'uploading']))
        elif status == 'processing':
            query = query.filter(MeetingRecording.status.in_(['uploaded', 'merged', 'transcribing']))
        elif status == 'completed':
            query = query.filter(MeetingRecording.status.in_(['transcribed', 'minutes_generated', 'published']))
        elif status == 'failed':
            query = query.filter(MeetingRecording.status.in_(['transcription_failed', 'failed']))
        else:
            query = query.filter(MeetingRecording.status == status)

    if mode:
        query = query.filter(MeetingRecording.recording_mode == mode)
    if owner_id:
        try:
            query = query.filter(MeetingRecording.owner_id == int(owner_id))
        except ValueError:
            pass
    if time_range:
        try:
            cutoff = get_local_time() - timedelta(days=int(time_range))
            query = query.filter(MeetingRecording.created_at >= cutoff)
        except ValueError:
            pass
    if search:
        query = query.filter(
            db.or_(
                MeetingRecording.title.ilike(f'%{search}%'),
                MeetingRecording.owner.has(User.real_name.ilike(f'%{search}%'))
            )
        )

    recordings = query.order_by(MeetingRecording.created_at.desc()).limit(200).all()

    # 从 transcript.segments 反推真实形式和语种
    # - 有 speaker='peer' segment → 用过系统音频 → 线上
    # - 收集所有 source_lang → 拼成"中 / EN"
    _lang_label = {'zh': '中', 'zh-CN': '中', 'en': 'EN', 'ms': '马', 'id': '印', 'ja': '日'}
    # 预加载用户名查 mapping（一次性查 user_id → real_name 避免 N+1）
    all_user_ids = set()
    for rec in recordings:
        if rec.transcript and rec.transcript.segments:
            for seg in rec.transcript.segments:
                uid = seg.get('speaker_user_id')
                if uid: all_user_ids.add(uid)
    user_name_map = {}
    if all_user_ids:
        for u in User.query.filter(User.id.in_(all_user_ids)).all():
            user_name_map[u.id] = u.real_name or u.username

    _avatar_palette = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444',
                       '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16']

    def _name_color(name: str) -> str:
        """跟前端 avatarColorForName 算法一致：char codepoint hash 取 palette index"""
        if not name:
            return _avatar_palette[0]
        h = 0
        for ch in name:
            h = (h * 31 + ord(ch)) | 0
            # JS bitwise int32 模拟
            h = ((h & 0xFFFFFFFF) ^ 0x80000000) - 0x80000000
        return _avatar_palette[abs(h) % 8]

    for rec in recordings:
        is_online = (rec.recording_mode == 'microphone_system')
        lang_set = set()
        # 收集参与人：来自 transcript.segments 的 speaker_display / speaker_user_id / speaker_external_name
        # 没 mapping 的 me/peer fallback 到 owner+'对方'
        participants = []  # [{name, color, user_id?, is_external?}]
        seen_names = set()
        if rec.transcript and rec.transcript.segments:
            for seg in rec.transcript.segments:
                if seg.get('speaker') == 'peer':
                    is_online = True
                src = seg.get('source_lang')
                if src:
                    lang_set.add(_lang_label.get(src, src))
                # 参与人识别
                uid = seg.get('speaker_user_id')
                ext = seg.get('speaker_external_name')
                disp = seg.get('speaker_display')
                if uid:
                    name = user_name_map.get(uid, disp or '?')
                    if name not in seen_names:
                        seen_names.add(name)
                        participants.append({'name': name, 'color': _name_color(name), 'user_id': uid, 'is_external': False})
                elif ext:
                    if ext not in seen_names:
                        seen_names.add(ext)
                        participants.append({'name': ext, 'color': _name_color(ext), 'user_id': None, 'is_external': True})
                elif disp:
                    if disp not in seen_names:
                        seen_names.add(disp)
                        participants.append({'name': disp, 'color': _name_color(disp), 'user_id': None, 'is_external': False})
        # 没 mapping 兜底：放 owner
        if not participants and rec.owner:
            n = rec.owner.real_name or rec.owner.username
            participants.append({'name': n, 'color': _name_color(n),
                                  'user_id': rec.owner_id, 'is_external': False})
        rec.form_display = '线上' if is_online else '线下'
        rec.lang_display = ' / '.join(sorted(lang_set)) if lang_set else '中'
        rec.participants_display = participants

    # 统计（基于已筛选的当前列表）
    now = get_local_time()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month = sum(1 for r in recordings if r.meeting_time and r.meeting_time >= month_start)
    total_seconds = sum((r.duration_seconds or 0) for r in recordings)
    published_count = sum(1 for r in recordings if r.minutes and r.minutes.status == 'published')
    pending_actions = sum(
        len([a for a in r.minutes.action_items if not a.is_deleted])
        for r in recordings if r.minutes
    )

    # 负责人下拉选项
    owner_options = []
    seen_owners = {}
    for r in recordings:
        if r.owner and r.owner_id not in seen_owners:
            seen_owners[r.owner_id] = True
            owner_options.append({
                'value': r.owner_id,
                'label': r.owner.real_name or r.owner.username
            })

    filter_config = {
        'action_url': url_for('meeting.minutes_list'),
        'search_field': {'name': 'search', 'value': search},
        'filter_fields': [
            {'name': 'owner_id', 'label': _('负责人'), 'all_option_text': _('全部负责人'),
             'options': owner_options, 'current_value': owner_id},
            {'name': 'mode', 'label': _('会议形式'), 'all_option_text': _('全部形式'),
             'options': [{'value': 'microphone', 'label': _('线下')},
                         {'value': 'microphone_system', 'label': _('线上')}],
             'current_value': mode},
            {'name': 'status', 'label': _('状态'), 'all_option_text': _('全部状态'),
             'options': [
                {'value': 'recording', 'label': _('录音中')},
                {'value': 'processing', 'label': _('处理中')},
                {'value': 'completed', 'label': _('完成')},
                {'value': 'failed', 'label': _('失败')},
             ], 'current_value': status},
            {'name': 'time_range', 'label': _('时间范围'), 'all_option_text': _('全部时间'),
             'options': [{'value': '7', 'label': _('最近 7 天')},
                         {'value': '30', 'label': _('最近 30 天')},
                         {'value': '90', 'label': _('最近 90 天')}],
             'current_value': time_range},
        ],
    }

    return render_template(
        'meeting/tw_meeting_minutes_list.html',
        recordings=recordings,
        total_count=len(recordings),
        stats={
            'this_month': this_month,
            'published_count': published_count,
            'pending_actions': pending_actions,
            'total_hours': round(total_seconds / 3600, 1),
        },
        filter_config=filter_config,
    )


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


def _build_recording_detail_payload(recording):
    """把 recording 详情打包成 dict，view 和 API 共用，
    避免详情页初次加载时空白等待 fetch。"""
    data = recording.to_dict()
    if recording.transcript:
        data['transcript'] = recording.transcript.to_dict(include_segments=True)
        data['speakers'] = [s.to_dict() for s in recording.transcript.speakers]
    if recording.minutes:
        data['minutes'] = recording.minutes.to_dict(include_content=True)
    data['can_edit'] = can_edit_recording(current_user, recording)
    data['can_delete'] = can_delete_recording(current_user, recording)
    available_users = User.query.filter(User._is_active == True).order_by(  # noqa
        User.real_name.asc().nullslast(), User.username.asc()
    ).limit(500).all()
    data['available_users'] = [
        {'id': u.id, 'username': u.username,
         'real_name': u.real_name or u.username, 'email': u.email}
        for u in available_users
    ]
    return data


@meeting.route('/minutes/<int:recording_id>')
@login_required
def minutes_detail(recording_id):
    """纪要详情页 — 直接 server-side 嵌入完整数据，避免首屏空白"""
    recording = MeetingRecording.query.get_or_404(recording_id)

    if not can_view_recording(current_user, recording):
        abort(403)

    import json as _json
    initial_data = _build_recording_detail_payload(recording)
    return render_template(
        'meeting/tw_meeting_minutes_detail.html',
        recording=recording,
        initial_data_json=_json.dumps(initial_data, ensure_ascii=False, default=str)
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
        # 自己创建的 + 参与的（通过工作项共享）+ 被邀请旁听的
        query = query.filter(
            db.or_(
                MeetingRecording.owner_id == current_user.id,
                # 通过工作项关联的参与者
                MeetingRecording.work_item_id.in_(
                    db.session.query(WorkItem.id).filter(
                        cast(WorkItem.shared_with_users, JSONB).op('@>')(text(f"'[{current_user.id}]'::jsonb"))
                    )
                ),
                cast(MeetingRecording.invited_user_ids, JSONB).op('@>')(text(f"'[{current_user.id}]'::jsonb"))
            )
        )

    # 状态筛选
    if status:
        # 4 个用户感知状态映射回原始 status：
        if status == 'recording':
            query = query.filter(MeetingRecording.status.in_(['recording', 'uploading']))
        elif status == 'processing':
            query = query.filter(MeetingRecording.status.in_(['uploaded', 'merged', 'transcribing']))
        elif status == 'completed':
            query = query.filter(MeetingRecording.status.in_(['transcribed', 'minutes_generated', 'published']))
        elif status == 'failed':
            query = query.filter(MeetingRecording.status.in_(['transcription_failed', 'failed']))
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
    # 现在只支持"接入第三方会议"一种模式：麦克风 + 系统音频（getDisplayMedia）
    recording_mode = data.get('recording_mode', 'microphone_system')

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

    # 邀请 PMA 同事旁听：限定 active 用户且非自己
    raw_invited = data.get('invited_user_ids') or []
    invited_ids = []
    if isinstance(raw_invited, list):
        from app.models.user import User as _User
        valid_ids = {row[0] for row in db.session.query(_User.id).filter(
            _User.id.in_([int(x) for x in raw_invited if str(x).isdigit()]),
            _User._is_active == True  # noqa: E712
        ).all()}
        invited_ids = [int(x) for x in raw_invited
                       if str(x).isdigit() and int(x) != current_user.id and int(x) in valid_ids]

    recording = MeetingRecording(
        work_item_id=work_item_id,
        title=title,
        meeting_time=get_local_time(),
        recording_mode=recording_mode,
        status='recording',
        owner_id=current_user.id,
        invited_user_ids=invited_ids
    )

    db.session.add(recording)
    db.session.commit()

    # 给每位被邀请人发站内通知
    if invited_ids:
        from app.models.message import Message
        for rid in invited_ids:
            try:
                db.session.add(Message.create_meeting_invite(current_user.id, rid, recording))
            except Exception as e:
                current_app.logger.warning(f"会议邀请通知发送失败 recording={recording.id} to={rid}: {e}")
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

    return jsonify({
        'success': True,
        'recording': _build_recording_detail_payload(recording)
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
    track = request.form.get('track', 'mixed')  # 'mixed' / 'system'

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
            is_final=is_final,
            track=track
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

    data = request.get_json() or {}
    duration_seconds = data.get('duration_seconds') or data.get('duration', 0)

    recording.duration_seconds = duration_seconds
    recording.status = 'uploaded'
    db.session.commit()

    # 清理实时翻译滚动上下文（避免长跑后内存累积）
    _clear_realtime_history(recording_id)

    # 合并 mixed 轨（回放用）→ 设置 storage_url（关键，否则回放永远 404）
    from app.services.meeting_service import MeetingService
    merge_result = MeetingService.merge_audio_chunks(recording_id, track='mixed')
    if not merge_result.get('success'):
        from flask import current_app
        current_app.logger.warning(
            f"合并 mixed 音频块失败 recording_id={recording_id}: {merge_result.get('error')}"
        )

    # 同步合并 system 轨（pyannote 用）— 失败不影响主流程
    sys_merge = MeetingService.merge_audio_chunks(recording_id, track='system')
    if not sys_merge.get('success'):
        current_app.logger.info(
            f"合并 system 音频块跳过/失败 recording_id={recording_id}: {sys_merge.get('error')}"
        )

    # 检查是否需要事后整段转录：
    # - 如果 transcript.segments 已经有内容 = 实时翻译模式累积过了，跳过
    # - 否则 = 纯录音模式，异步触发整段 Whisper 转录
    from app.models.meeting import MeetingTranscript
    from flask import current_app
    transcript = MeetingTranscript.query.filter_by(recording_id=recording_id).first()
    needs_post_transcribe = (
        merge_result.get('success')
        and (not transcript or len(transcript.segments or []) == 0)
    )

    # 实时翻译累积模式：segments 已经写满，把 transcript.status 推到 completed
    # 这样 /generate-minutes 才不会被 400 拒（它要求 status == 'completed'）
    if transcript and len(transcript.segments or []) > 0 and transcript.status != 'completed':
        transcript.status = 'completed'
        if not transcript.completed_at:
            transcript.completed_at = datetime.utcnow()
        # recording 状态也推进
        if recording.status in ('uploaded', 'merged'):
            recording.status = 'transcribed'
        db.session.commit()

    import threading
    app_obj = current_app._get_current_object()

    if needs_post_transcribe:
        def _bg_transcribe():
            with app_obj.app_context():
                try:
                    app_obj.logger.info(f"[stop] 自动触发整段转录 recording_id={recording_id}")
                    MeetingService.transcribe_audio(recording_id)
                    # 转录跑完，先用 Claude 二次纠错专有名词，再生成纪要
                    try:
                        fix_res = MeetingService.fix_transcript_with_vocab(recording_id)
                        app_obj.logger.info(f"[stop] 二次纠错: {fix_res}")
                    except Exception as fe:
                        app_obj.logger.warning(f"[stop] 二次纠错跳过 recording_id={recording_id}: {fe}")
                    MeetingService.generate_minutes(recording_id=recording_id, style='standard')
                except Exception as e:
                    app_obj.logger.error(f"[stop] 后台转录/纪要失败 recording_id={recording_id}: {e}")

        threading.Thread(target=_bg_transcribe, daemon=True).start()
    elif transcript and len(transcript.segments or []) > 0:
        # 实时翻译累积模式：transcript 已就绪
        # 串行后台任务：声纹分离（可选，PYANNOTE_SERVICE_URL 配置才跑）→ 生成纪要
        from app.models.meeting import MeetingMinutes
        from app.services.diarization_service import DiarizationService
        existing = MeetingMinutes.query.filter_by(recording_id=recording_id).first()
        if not existing:
            def _bg_post_processing():
                with app_obj.app_context():
                    # 1. 声纹分离（失败不阻塞纪要生成）
                    if DiarizationService.is_available():
                        try:
                            app_obj.logger.info(f"[stop] 触发声纹分离 recording_id={recording_id}")
                            diar_res = DiarizationService.run_for_recording(recording_id)
                            if diar_res.get('success'):
                                app_obj.logger.info(
                                    f"[stop] 声纹分离成功 recording_id={recording_id} "
                                    f"speakers={diar_res.get('speaker_count')} "
                                    f"耗时={diar_res.get('duration_ms')}ms"
                                )
                            else:
                                app_obj.logger.warning(f"[stop] 声纹分离失败但继续: {diar_res.get('error')}")
                        except Exception as e:
                            app_obj.logger.error(f"[stop] 声纹分离异常: {e}", exc_info=True)

                    # 1.5 二次纠错：用 Claude 按参会人姓名字典修正 Whisper 同音错字
                    try:
                        fix_res = MeetingService.fix_transcript_with_vocab(recording_id)
                        app_obj.logger.info(f"[stop] 二次纠错: {fix_res}")
                    except Exception as fe:
                        app_obj.logger.warning(f"[stop] 二次纠错跳过 recording_id={recording_id}: {fe}")

                    # 2. 生成纪要
                    try:
                        app_obj.logger.info(f"[stop] 触发纪要生成 recording_id={recording_id}")
                        result = MeetingService.generate_minutes(recording_id=recording_id, style='standard')
                        if not result.get('success'):
                            app_obj.logger.warning(f"[stop] 纪要生成失败 recording_id={recording_id}: {result.get('error')}")
                    except Exception as e:
                        app_obj.logger.error(f"[stop] 纪要生成异常 recording_id={recording_id}: {e}", exc_info=True)

            threading.Thread(target=_bg_post_processing, daemon=True).start()

    return jsonify({
        'success': True,
        'recording': recording.to_dict(),
        'redirect_url': url_for('meeting.minutes_detail', recording_id=recording.id),
        'auto_transcribe': needs_post_transcribe
    })


@meeting.route('/api/recordings/<int:recording_id>/realtime-translate', methods=['POST'])
@login_required
def api_realtime_translate(recording_id):
    """
    实时翻译端点：接收音频 chunk → Whisper 自动检测语种 + 转写 → 非母语时 GPT 翻译 → 返回 JSON

    multipart/form-data 参数：
    - chunk: 音频文件（webm/opus）
    - native_lang: 用户母语（zh-CN / en / ms / id / ja / ko / th / vi / tl）
    - speaker: 'me' (麦克风) | 'peer' (系统音频)，仅前端用于区分气泡

    返回：{success, original, translation, speaker, detected_lang, native_lang, was_translated, duration_ms}
    """
    import os, tempfile, time
    from flask import current_app

    recording = MeetingRecording.query.get_or_404(recording_id)
    if recording.owner_id != current_user.id:
        return jsonify({'success': False, 'message': _('无权操作')}), 403

    chunk_file = request.files.get('chunk')
    if not chunk_file:
        return jsonify({'success': False, 'message': '缺少音频 chunk'}), 400

    native_lang = request.form.get('native_lang', 'zh-CN')
    speaker = request.form.get('speaker', 'me')
    # 该 chunk 在录音中的起始毫秒（前端跟踪的真实 audio offset），用于回放同步字幕
    try:
        chunk_audio_offset_ms = int(request.form.get('chunk_audio_offset_ms', ''))
    except (TypeError, ValueError):
        chunk_audio_offset_ms = None

    # OpenAI Whisper ISO-639-1 代码映射
    lang_map = {'zh-CN': 'zh', 'zh': 'zh', 'en': 'en', 'ms': 'ms', 'id': 'id',
                'ja': 'ja', 'ko': 'ko', 'th': 'th', 'vi': 'vi', 'tl': 'tl'}
    native_whisper = lang_map.get(native_lang, 'zh')

    t_start = time.time()

    # initial_prompt 引导"商务会议"语境减少 hallucination；用母语提示帮助识别
    prompts_by_lang = {
        'zh': '以下是一段商务会议的录音对话。',
        'en': 'The following is a business meeting conversation.',
        'ms': 'Berikut adalah perbualan mesyuarat perniagaan.',
        'id': 'Berikut adalah percakapan rapat bisnis.',
        'ja': '以下はビジネスミーティングの会話です。',
        'ko': '다음은 비즈니스 회의 대화입니다。',
        'th': 'ต่อไปนี้เป็นการสนทนาในการประชุมทางธุรกิจ',
        'vi': 'Sau đây là cuộc trò chuyện trong cuộc họp kinh doanh.',
        'tl': 'Ang sumusunod ay isang pag-uusap sa business meeting.',
    }
    # 滚动上下文：把同一 recording+speaker 的上一段原文塞进 prompt
    rolling_ctx = _get_realtime_history(recording_id, speaker)
    base_prompt = prompts_by_lang.get(native_whisper, '')
    # PMA 业务词汇（参会人 real_name）— 提升同音字人名识别
    vocab_prompt = _build_vocab_prompt(recording)
    whisper_prompt = ' '.join(p for p in [vocab_prompt, base_prompt, rolling_ctx] if p).strip()

    # 路由：优先走 Mac mini whisper_proxy 服务（容器无需 ffmpeg 和 OPENAI_API_KEY）
    # 未配置 PMA_WHISPER_SERVICE_URL 时退回本地 ffmpeg+OpenAI SDK（本地开发用）
    whisper_service_url = os.environ.get('PMA_WHISPER_SERVICE_URL', '').rstrip('/')

    tmp_path = None  # 仅本地 fallback 路径使用，远程路径无 temp file
    try:
        if whisper_service_url:
            # ── 远程路径：直接发 webm bytes 给 Mac mini ──
            import requests as _http, types
            webm_bytes = chunk_file.read()
            try:
                resp = _http.post(
                    f"{whisper_service_url}/transcribe",
                    files={'audio': ('chunk.webm', webm_bytes, 'audio/webm')},
                    data={
                        'native_lang': native_whisper,
                        'prompt': whisper_prompt,
                        'temperature': '0',
                        'model': 'whisper-1',
                    },
                    timeout=90,
                )
            except _http.exceptions.RequestException as e:
                current_app.logger.error(f"[realtime-translate] whisper service unreachable: {e}")
                return jsonify({'success': False, 'message': f'Whisper 服务不可达: {e}'}), 502

            if resp.status_code != 200:
                current_app.logger.error(
                    f"[realtime-translate] whisper service error {resp.status_code}: {resp.text[:300]}"
                )
                return jsonify({'success': False, 'message': f'Whisper 服务错误 HTTP {resp.status_code}'}), resp.status_code

            data = resp.json()
            # ffmpeg 转码失败时,whisper_proxy 返回 _empty=True,语义同原静默丢弃
            if data.get('_empty'):
                return jsonify({
                    'success': True,
                    'empty': True,
                    'speaker': speaker,
                    'duration_ms': int((time.time() - t_start) * 1000)
                })

            # 包装成与 OpenAI SDK 同接口的对象（getattr 兼容）
            transcript_resp = types.SimpleNamespace(
                text=data.get('text', ''),
                language=data.get('language', native_whisper),
                segments=[types.SimpleNamespace(**s) for s in (data.get('segments') or [])],
            )
            current_app.logger.info(
                f"[realtime-translate] remote OK speaker={speaker} "
                f"webm={len(webm_bytes)} text_len={len(transcript_resp.text)} segs={len(transcript_resp.segments)}"
            )
        else:
            # ── 本地 fallback 路径：保留原有 ffmpeg + OpenAI SDK 实现 ──
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                return jsonify({'success': False, 'message': 'OpenAI API key 未配置 (或缺少 PMA_WHISPER_SERVICE_URL)'}), 503

            # 1. 写临时 webm 文件（可能是裸 chunk 无 header）
            with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as tmp:
                tmp.write(chunk_file.read())
                webm_path = tmp.name

            wav_path = webm_path.replace('.webm', '.wav')
            try:
                import subprocess
                result = subprocess.run(
                    ['ffmpeg', '-y', '-i', webm_path, '-f', 'wav', '-ar', '16000', '-ac', '1', wav_path],
                    capture_output=True, timeout=15
                )
                if result.returncode != 0:
                    stderr_text = result.stderr.decode(errors='ignore')
                    current_app.logger.warning(
                        f"[realtime-translate] ffmpeg 转码失败 speaker={speaker} "
                        f"webm_size={os.path.getsize(webm_path)} "
                        f"returncode={result.returncode} "
                        f"stderr_tail={stderr_text[-800:]}"
                    )
                    return jsonify({
                        'success': True,
                        'empty': True,
                        'speaker': speaker,
                        'duration_ms': int((time.time() - t_start) * 1000)
                    })
                current_app.logger.info(
                    f"[realtime-translate] ffmpeg OK speaker={speaker} "
                    f"webm={os.path.getsize(webm_path)} → wav={os.path.getsize(wav_path)}"
                )
            except Exception as e:
                current_app.logger.warning(f"ffmpeg 转码失败: {e}")
                return jsonify({
                    'success': True,
                    'empty': True,
                    'speaker': speaker,
                    'duration_ms': int((time.time() - t_start) * 1000)
                })
            finally:
                try:
                    os.unlink(webm_path)
                except Exception:
                    pass

            tmp_path = wav_path

            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            with open(tmp_path, 'rb') as f:
                transcript_resp = client.audio.transcriptions.create(
                    model='whisper-1',
                    file=f,
                    response_format='verbose_json',
                    prompt=whisper_prompt,
                    temperature=0
                )
        original_text = (transcript_resp.text if hasattr(transcript_resp, 'text') else '').strip()
        detected_lang = getattr(transcript_resp, 'language', None) or native_whisper
        # Whisper 返回的可能是英文 'chinese' / 'english' 或 ISO 'zh' / 'en'，做一次归一
        _full_to_iso = {
            'chinese': 'zh', 'english': 'en', 'malay': 'ms', 'indonesian': 'id',
            'japanese': 'ja', 'korean': 'ko', 'thai': 'th', 'vietnamese': 'vi', 'tagalog': 'tl'
        }
        detected_lang = _full_to_iso.get(detected_lang.lower(), detected_lang.lower())

        # 用 Whisper 自己的置信度信号过滤幻觉（verbose_json segments）
        # no_speech_prob > 0.6 → 模型认为这段就是噪音
        # avg_logprob < -1.0 → 模型对输出非常不自信
        # compression_ratio > 2.4 → 检测到 looping / 重复填充
        low_conf_segment = False
        try:
            segs = getattr(transcript_resp, 'segments', None) or []
            kept_texts = []
            for seg in segs:
                nsp = float(getattr(seg, 'no_speech_prob', 0.0) or 0.0)
                alp = float(getattr(seg, 'avg_logprob', 0.0) or 0.0)
                cr  = float(getattr(seg, 'compression_ratio', 1.0) or 1.0)
                if nsp > 0.6 or alp < -1.0 or cr > 2.4:
                    current_app.logger.info(
                        f"[realtime-translate] drop segment no_speech={nsp:.2f} "
                        f"avg_logprob={alp:.2f} compression_ratio={cr:.2f} "
                        f"text={getattr(seg, 'text', '')!r}"
                    )
                    low_conf_segment = True
                    continue
                kept_texts.append(getattr(seg, 'text', ''))
            if segs:
                rebuilt = ''.join(kept_texts).strip()
                # 只在所有 segment 都被丢弃时才覆盖；否则用 keep 的 segments 拼回
                if not rebuilt:
                    original_text = ''
                else:
                    original_text = rebuilt
        except Exception as _seg_err:
            current_app.logger.warning(f"[realtime-translate] segment 分析失败: {_seg_err}")

        # 过滤 Whisper 在静音/噪音上的常见 hallucination 模板
        HALLUCINATION_PATTERNS = [
            # 中文 YouTube 模板
            '请不吝点赞', '不吝点赞',
            '订阅 转发', '订阅、转发', '订阅转发',
            '打赏支持', '打赏', '小铃铛',
            '明镜', '点点栏目',
            '字幕由', '字幕组',
            '感谢观看', '感谢收看', '感谢您的观看', '感谢您的收看',
            '本期视频', '本期节目',
            '分享到这里', '分享到此',
            '欢迎订阅', '请订阅', '请点击订阅', '点击关注', '请点击',
            '欢迎关注', '记得关注',
            '我们下期再见', '下期见', '下次见',
            '点点关注', '一键三连',
            '请勿模仿', '请勿', '请勿转载',
            '其他事项', '本节目',
            '请按右下角', '点小铃铛',
            # 英文 YouTube 模板
            'Subscribe to', 'subscribe to my channel',
            'Thanks for watching', 'thank you for watching', 'thanks for watching',
            'Please subscribe', 'please subscribe',
            'like and subscribe', 'hit the bell',
            'see you next time', 'see you in the next',
            # 日韩
            'ご視聴ありがとうございました', 'チャンネル登録',
            'MBC 뉴스', 'mbc 뉴스', '구독', '좋아요',
        ]
        text_lower = original_text.lower()
        is_dup = _is_recent_duplicate(recording_id, speaker, original_text)
        is_hallucination = (
            any(p.lower() in text_lower for p in HALLUCINATION_PATTERNS)
            or _is_hallucinated_segment(original_text)
            or (low_conf_segment and not original_text)
            or is_dup
        )
        if is_dup:
            current_app.logger.info(
                f"[realtime-translate] drop duplicate text={original_text!r} speaker={speaker}"
            )

        # 调试日志
        current_app.logger.info(
            f"[realtime-translate] speaker={speaker} detected={detected_lang} "
            f"native={native_whisper} text={original_text!r} hallucination={is_hallucination}"
        )

        # 空白音频、太短、或被识别为 hallucination → 静默丢弃
        if not original_text or len(original_text) < 2 or is_hallucination:
            return jsonify({
                'success': True,
                'empty': True,
                'speaker': speaker,
                'reason': 'hallucination' if is_hallucination else 'empty',
                'duration_ms': int((time.time() - t_start) * 1000)
            })

        # 追加滚动上下文（hallucination 已在上面 return 不会到这里）
        _push_realtime_history(recording_id, speaker, original_text)

        # 检测语种 == 母语 → 不翻译，直接显示原文
        was_translated = (detected_lang != native_whisper)
        if not was_translated:
            translation_text = original_text
        else:
            lang_names = {'zh': 'Simplified Chinese', 'en': 'English',
                          'ms': 'Malay', 'id': 'Indonesian', 'ja': 'Japanese',
                          'ko': 'Korean', 'th': 'Thai', 'vi': 'Vietnamese', 'tl': 'Filipino/Tagalog'}
            target_name = lang_names.get(native_whisper, native_lang)
            # 走 Claude Haiku（通过 ANTHROPIC_BASE_URL 代理统一栈）
            # Haiku 不受 OAuth model gating 限制，但仍带 Claude Code system 前缀保持一致
            try:
                import anthropic
                ant_client = anthropic.Anthropic(
                    api_key=os.environ.get('ANTHROPIC_API_KEY') or 'sk-ant-placeholder',
                    base_url=os.environ.get('ANTHROPIC_BASE_URL') or None,
                )
                vocab_hint = _build_vocab_prompt(recording)
                user_msg = (
                    (f"会议参会人姓名（保留原名，遇到同音/形近请按此校正）：{vocab_hint}\n\n"
                     if vocab_hint else '')
                    + f"Translate the following text to {target_name}. "
                    f"Output ONLY the translation, no explanation, no quotes.\n\n{original_text}"
                )
                ant_resp = ant_client.messages.create(
                    model='claude-haiku-4-5-20251001',
                    max_tokens=500,
                    system=[
                        {'type': 'text', 'text': "You are Claude Code, Anthropic's official CLI for Claude."},
                        {'type': 'text', 'text': 'You are a precise translator for live business meetings. Output only the translation, no commentary.'},
                    ],
                    messages=[{'role': 'user', 'content': user_msg}],
                )
                translation_text = first_text(ant_resp).strip()
            except Exception as e:
                # Claude 失败兜底回 OpenAI（实时翻译不能中断）
                current_app.logger.warning(f"[realtime-translate] Claude 翻译失败，兜底 OpenAI: {e}")
                prompt = (f"Translate the following text to {target_name}. "
                          f"Output ONLY the translation, no explanation, no quotes.\n\n{original_text}")
                translation = client.chat.completions.create(
                    model='gpt-4o-mini',
                    messages=[{'role': 'user', 'content': prompt}],
                    max_tokens=500,
                    temperature=0.3
                )
                translation_text = translation.choices[0].message.content.strip()

        # 累积到 MeetingTranscript：让详情页"完整转录"tab 实时有内容
        # 同时存翻译，事后回看不丢
        try:
            from app.models.meeting import MeetingTranscript
            transcript = MeetingTranscript.query.filter_by(recording_id=recording_id).first()
            if not transcript:
                # language 字段记录首句检测到的语言；后续段落会有自己的 source_lang
                transcript = MeetingTranscript(
                    recording_id=recording_id,
                    language=detected_lang or native_whisper,
                    status='processing',
                    full_text='',
                    segments=[]
                )
                db.session.add(transcript)
                db.session.flush()  # 拿 id

            # SQLAlchemy JSON 字段必须重新赋值才会标记 dirty
            segments = list(transcript.segments or [])
            # 多语言翻译：写一个 dict，key 是语言 code，方便不同母语用户取自己的版本
            # 已知 host 母语版本 = translation_text；若原文语种 == host 母语则没翻译，留空字典
            translations_map = {}
            if was_translated and translation_text:
                translations_map[native_whisper] = translation_text
            new_seg = {
                'speaker': speaker,
                'text': original_text,
                'translation': translation_text,   # 旧字段兼容（前端老代码 = host 母语版本）
                'translations': translations_map,  # 新字段（多语言 dict，被邀请人按自己母语取）
                'source_lang': detected_lang,
                'target_lang': native_whisper,
                'was_translated': was_translated,
                'ts': datetime.utcnow().isoformat(),
            }
            # 用前端跟踪的真实 audio offset（精确）；缺失时不写，让前端 normalizer 兜底
            if chunk_audio_offset_ms is not None and chunk_audio_offset_ms >= 0:
                new_seg['start_time'] = chunk_audio_offset_ms / 1000.0
                # chunk 时长估计：用本次处理总时长（ffmpeg + Whisper + GPT 时间近似 ~= chunk 时长）
                # 不准但只用于显示当前段范围，回放高亮主要看 start_time
                chunk_dur_estimate = max(2.0, (time.time() - t_start) - 1.0)
                new_seg['end_time'] = new_seg['start_time'] + chunk_dur_estimate
            segments.append(new_seg)
            transcript.segments = segments
            speaker_label = '我' if speaker == 'me' else '对方'
            transcript.full_text = (
                (transcript.full_text or '')
                + ('\n' if transcript.full_text else '')
                + f"[{speaker_label}] {original_text}"
            )
            db.session.commit()
        except Exception as e:
            current_app.logger.warning(f"累积 transcript 失败 recording={recording_id}: {e}")
            db.session.rollback()

        return jsonify({
            'success': True,
            'original': original_text,
            'translation': translation_text,
            'speaker': speaker,
            'detected_lang': detected_lang,
            'native_lang': native_whisper,
            'was_translated': was_translated,
            'duration_ms': int((time.time() - t_start) * 1000)
        })

    except Exception as e:
        current_app.logger.error(f"实时翻译失败 recording={recording_id}: {e}", exc_info=True)
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


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
        if recording.status == 'uploaded' and recording.chunk_paths:
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


@meeting.route('/api/recordings/<int:recording_id>/translate-segments', methods=['POST'])
@login_required
def api_translate_segments(recording_id):
    """按需把 transcript 的 segments 翻译成指定语言并入库 segment.translations[to_lang]。

    body: { to_lang: 'en' }  必填
    只翻译当前缺失该语言版本的 segments；已有的不重复调 API。
    """
    from app.models.meeting import MeetingTranscript
    recording = MeetingRecording.query.get_or_404(recording_id)
    if not can_view_recording(current_user, recording):
        return jsonify({'success': False, 'message': _('无权访问')}), 403

    data = request.get_json(silent=True) or {}
    to_lang = (data.get('to_lang') or '').strip()
    if not to_lang:
        return jsonify({'success': False, 'message': 'to_lang required'}), 400

    transcript = MeetingTranscript.query.filter_by(recording_id=recording_id).first()
    if not transcript or not (transcript.segments or []):
        return jsonify({'success': True, 'translated': 0})

    segs = list(transcript.segments or [])
    # 找出需要翻译的（原语种 != to_lang 且 translations[to_lang] 缺失）
    pending_idx = []
    for i, s in enumerate(segs):
        src = (s.get('source_lang') or '').lower()
        if src == to_lang:
            continue  # 原文就是目标语种，跳过
        tr = s.get('translations') or {}
        if not tr.get(to_lang):
            pending_idx.append(i)

    if not pending_idx:
        return jsonify({'success': True, 'translated': 0, 'cached': True})

    # 调 Claude Haiku 批量翻译
    lang_names = {'zh': 'Simplified Chinese', 'en': 'English', 'ms': 'Malay',
                  'id': 'Indonesian', 'ja': 'Japanese', 'ko': 'Korean',
                  'th': 'Thai', 'vi': 'Vietnamese', 'tl': 'Filipino/Tagalog'}
    target_name = lang_names.get(to_lang, to_lang)
    vocab_hint = _build_vocab_prompt(recording)

    try:
        import anthropic
        client = anthropic.Anthropic(
            api_key=os.environ.get('ANTHROPIC_API_KEY') or 'sk-ant-placeholder',
            base_url=os.environ.get('ANTHROPIC_BASE_URL') or None,
        )
    except Exception as e:
        return jsonify({'success': False, 'message': f'Claude 初始化失败: {e}'}), 500

    BATCH = 30
    translated_count = 0
    for i in range(0, len(pending_idx), BATCH):
        batch_idx = pending_idx[i:i + BATCH]
        payload = [{'i': j, 'text': segs[j].get('text') or ''} for j in batch_idx]
        sys_text = (
            f"You are a precise translator for live business meetings. "
            f"Translate each segment's text into {target_name}. "
            f"Output JSON array, structure identical to input but with text replaced by translation. "
            f"Preserve speaker intent, do not add commentary."
            + (f"\n会议参会人姓名（保留原名，遇到同音/形近请按此校正）：{vocab_hint}" if vocab_hint else '')
        )
        user_msg = (
            "Input:\n```json\n"
            + json.dumps(payload, ensure_ascii=False)
            + "\n```\nOutput JSON array only, no markdown wrap, no explanation."
        )
        try:
            resp = client.messages.create(
                model='claude-haiku-4-5-20251001',
                max_tokens=4000,
                system=[
                    {'type': 'text', 'text': "You are Claude Code, Anthropic's official CLI for Claude."},
                    {'type': 'text', 'text': sys_text},
                ],
                messages=[{'role': 'user', 'content': user_msg}],
            )
            raw = first_text(resp).strip()
            if raw.startswith('```'):
                raw = raw.split('```', 2)[1]
                if raw.startswith('json'):
                    raw = raw[4:]
                raw = raw.rsplit('```', 1)[0].strip()
            parsed = json.loads(raw)
            if not isinstance(parsed, list):
                continue
            for item in parsed:
                j = item.get('i')
                tx = item.get('text')
                if not isinstance(j, int) or j < 0 or j >= len(segs) or not tx:
                    continue
                new_seg = dict(segs[j])
                tr = dict(new_seg.get('translations') or {})
                tr[to_lang] = tx
                new_seg['translations'] = tr
                segs[j] = new_seg
                translated_count += 1
        except Exception as e:
            current_app.logger.warning(f"[translate-segments] batch i={i} 失败: {e}")
            continue

    if translated_count > 0:
        transcript.segments = segs
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(transcript, 'segments')
        db.session.commit()

    return jsonify({'success': True, 'translated': translated_count, 'total': len(pending_idx)})


@meeting.route('/api/recordings/<int:recording_id>/translate-minutes', methods=['POST'])
@login_required
def api_translate_minutes(recording_id):
    """按需把整份 minutes 翻译成指定语言并入库 minutes.translations[to_lang]。
    body: { to_lang: 'en' }
    """
    from app.models.meeting import MeetingMinutes
    recording = MeetingRecording.query.get_or_404(recording_id)
    if not can_view_recording(current_user, recording):
        return jsonify({'success': False, 'message': _('无权访问')}), 403

    data = request.get_json(silent=True) or {}
    to_lang = (data.get('to_lang') or '').strip()
    if not to_lang:
        return jsonify({'success': False, 'message': 'to_lang required'}), 400

    minutes = MeetingMinutes.query.filter_by(recording_id=recording_id).first()
    if not minutes:
        return jsonify({'success': False, 'message': 'minutes not ready'}), 400

    cached = (minutes.translations or {}).get(to_lang)
    if cached:
        return jsonify({'success': True, 'cached': True, 'translation': cached})

    lang_names = {'zh': 'Simplified Chinese', 'en': 'English', 'ms': 'Malay',
                  'id': 'Indonesian', 'ja': 'Japanese', 'ko': 'Korean',
                  'th': 'Thai', 'vi': 'Vietnamese', 'tl': 'Filipino/Tagalog'}
    target_name = lang_names.get(to_lang, to_lang)

    # 准备纪要内容载荷
    payload = {
        'summary': minutes.summary or '',
        'key_points': minutes.key_points or [],
        'decisions': minutes.decisions or [],
        'key_quotes': minutes.key_quotes or [],
        'chapters': minutes.chapters or [],
        'highlights': minutes.highlights or [],
    }

    try:
        import anthropic
        client = anthropic.Anthropic(
            api_key=os.environ.get('ANTHROPIC_API_KEY') or 'sk-ant-placeholder',
            base_url=os.environ.get('ANTHROPIC_BASE_URL') or None,
        )
        sys_text = (
            f"You are a precise translator. Translate every text value into {target_name}. "
            f"Output JSON with identical structure to input. "
            f"Lists stay lists, dicts stay dicts. Only translate the text content. "
            f"For key_quotes items: translate the 'text' field, keep 'speaker'/'ts'/'category' as-is. "
            f"For chapters items: translate 'title' and 'summary', keep 't'/'speakers' as-is."
        )
        user_msg = (
            "Input:\n```json\n"
            + json.dumps(payload, ensure_ascii=False)
            + "\n```\nOutput JSON only."
        )
        resp = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=8000,
            system=[
                {'type': 'text', 'text': "You are Claude Code, Anthropic's official CLI for Claude."},
                {'type': 'text', 'text': sys_text},
            ],
            messages=[{'role': 'user', 'content': user_msg}],
        )
        raw = first_text(resp).strip()
        if raw.startswith('```'):
            raw = raw.split('```', 2)[1]
            if raw.startswith('json'):
                raw = raw[4:]
            raw = raw.rsplit('```', 1)[0].strip()
        translated = json.loads(raw)
    except Exception as e:
        return jsonify({'success': False, 'message': f'translate failed: {e}'}), 500

    tr_dict = dict(minutes.translations or {})
    tr_dict[to_lang] = translated
    minutes.translations = tr_dict
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(minutes, 'translations')
    db.session.commit()

    return jsonify({'success': True, 'translation': translated})


@meeting.route('/api/active-invites', methods=['GET'])
@login_required
def api_active_invites():
    """当前用户被邀请且会议正在进行中的列表（用于顶部 banner 提示）"""
    rows = MeetingRecording.query.filter(
        MeetingRecording.is_deleted == False,  # noqa: E712
        MeetingRecording.status.in_(['recording', 'uploading']),
        cast(MeetingRecording.invited_user_ids, JSONB).op('@>')(text(f"'[{current_user.id}]'::jsonb"))
    ).order_by(MeetingRecording.created_at.desc()).limit(5).all()

    return jsonify({
        'success': True,
        'invites': [
            {
                'id': r.id,
                'title': r.title,
                'owner_name': (r.owner.real_name or r.owner.username) if r.owner else '',
                'started_at': r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]
    })


@meeting.route('/api/available-users', methods=['GET'])
@login_required
def api_available_users():
    """浮窗"邀请同事"用 — 返回 PMA 在职用户（排除自己）。"""
    from app.models.user import User as _User
    users = _User.query.filter(_User._is_active == True).order_by(  # noqa: E712
        _User.real_name.asc().nullslast(), _User.username.asc()
    ).limit(500).all()
    return jsonify({
        'success': True,
        'users': [
            {'id': u.id, 'username': u.username, 'real_name': u.real_name or u.username}
            for u in users if u.id != current_user.id
        ]
    })


@meeting.route('/api/recordings/<int:recording_id>/invite', methods=['POST'])
@login_required
def api_invite_users(recording_id):
    """录音中/前邀请 PMA 同事旁听。
    body: { invited_user_ids: [int, ...] } —— 覆盖式替换
    对新增的人发 Message 通知，已经在列表里的人不再重复通知。
    """
    recording = MeetingRecording.query.get_or_404(recording_id)
    if recording.owner_id != current_user.id:
        return jsonify({'success': False, 'message': _('仅发起人可邀请')}), 403

    data = request.get_json(silent=True) or {}
    raw = data.get('invited_user_ids') or []
    if not isinstance(raw, list):
        return jsonify({'success': False, 'message': 'invited_user_ids must be list'}), 400

    from app.models.user import User as _User
    from app.models.message import Message
    candidate = [int(x) for x in raw if str(x).isdigit() and int(x) != current_user.id]
    valid_ids = {row[0] for row in db.session.query(_User.id).filter(
        _User.id.in_(candidate),
        _User._is_active == True  # noqa: E712
    ).all()}
    new_invited = [i for i in candidate if i in valid_ids]
    old_invited = set(recording.invited_user_ids or [])
    added = [i for i in new_invited if i not in old_invited]

    recording.invited_user_ids = new_invited
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(recording, 'invited_user_ids')
    db.session.flush()
    # 邀请名单变了，下次实时翻译 chunk 重新拼 vocab prompt
    _clear_vocab_cache(recording_id)

    for rid in added:
        try:
            db.session.add(Message.create_meeting_invite(current_user.id, rid, recording))
        except Exception as e:
            current_app.logger.warning(f"会议邀请通知失败 recording={recording_id} to={rid}: {e}")
    db.session.commit()

    return jsonify({
        'success': True,
        'invited_user_ids': new_invited,
        'notified': added
    })


@meeting.route('/api/recordings/<int:recording_id>/clean-hallucinations', methods=['POST'])
@login_required
def api_clean_hallucinations(recording_id):
    """一次性清理 transcript.segments 里的 Whisper hallucination 段
    （"嗯,嗯,嗯..." 等重复填充词）。仅作用于本 recording。"""
    recording = MeetingRecording.query.get_or_404(recording_id)
    if not can_edit_recording(current_user, recording):
        return jsonify({'success': False, 'message': _('无权操作')}), 403

    transcript = MeetingTranscript.query.filter_by(recording_id=recording_id).first()
    if not transcript or not (transcript.segments or []):
        return jsonify({'success': False, 'message': _('转录尚无内容')}), 400

    from sqlalchemy.orm.attributes import flag_modified
    segs = list(transcript.segments or [])
    kept = [s for s in segs if not _is_hallucinated_segment((s or {}).get('text', ''))]
    removed = len(segs) - len(kept)
    if removed > 0:
        transcript.segments = kept
        flag_modified(transcript, 'segments')
        # full_text 重新拼一遍
        lines = []
        for s in kept:
            spk = (s or {}).get('speaker', '')
            label = '我' if spk == 'me' else ('对方' if spk == 'peer' else (spk or ''))
            txt = (s or {}).get('text', '')
            lines.append(f"[{label}] {txt}" if label else txt)
        transcript.full_text = '\n'.join(lines)
        db.session.commit()

    return jsonify({
        'success': True,
        'removed': removed,
        'kept': len(kept),
        'message': _('已清理 %(n)d 段无效记录', n=removed)
    })


@meeting.route('/api/recordings/<int:recording_id>/regenerate-minutes', methods=['POST'])
@login_required
def api_regenerate_minutes(recording_id):
    """重新生成会议纪要：删旧 minutes（含 action_items）→ 重新跑 AI"""
    recording = MeetingRecording.query.get_or_404(recording_id)
    if not can_edit_recording(current_user, recording):
        return jsonify({'success': False, 'message': _('无权操作')}), 403

    transcript = MeetingTranscript.query.filter_by(recording_id=recording_id).first()
    if not transcript or not (transcript.segments or []):
        return jsonify({'success': False, 'message': _('转录尚无内容')}), 400

    from app.services.meeting_service import MeetingService
    import threading
    from flask import current_app
    app_obj = current_app._get_current_object()

    def _bg():
        with app_obj.app_context():
            try:
                app_obj.logger.info(f"[regen] recording_id={recording_id} 开始重新生成")
                MeetingService.generate_minutes(recording_id=recording_id, style='standard', force=True)
            except Exception as e:
                app_obj.logger.error(f"[regen] 失败 recording_id={recording_id}: {e}", exc_info=True)

    threading.Thread(target=_bg, daemon=True).start()
    return jsonify({'success': True, 'message': _('正在重新生成，30-60 秒后刷新查看')})


@meeting.route('/api/recordings/<int:recording_id>/ai-chat', methods=['POST'])
@login_required
def api_ai_chat(recording_id):
    """会议详情页右侧 AI 聊天面板：把 transcript+minutes 作 context 喂给 Claude 回答用户提问"""
    recording = MeetingRecording.query.get_or_404(recording_id)
    if not can_view_recording(current_user, recording):
        return jsonify({'success': False, 'message': _('无权访问')}), 403

    data = request.get_json() or {}
    user_question = (data.get('question') or '').strip()
    history = data.get('history') or []  # [{role, content}, ...]
    if not user_question:
        return jsonify({'success': False, 'message': '问题不能为空'}), 400

    transcript = MeetingTranscript.query.filter_by(recording_id=recording_id).first()
    minutes = recording.minutes if recording.minutes and not recording.minutes.is_deleted else None
    if not transcript and not minutes:
        return jsonify({'success': False, 'message': '会议尚无转录或纪要，无法回答'}), 400

    # 构造 context
    ctx_parts = [f"会议标题：{recording.title or '未命名会议'}"]
    if minutes:
        if minutes.summary:
            ctx_parts.append(f"\n【纪要摘要】\n{minutes.summary}")
        if minutes.decisions:
            ctx_parts.append(f"\n【决策事项】\n" + '\n'.join(f"- {d}" for d in minutes.decisions))
        if minutes.key_points:
            ctx_parts.append(f"\n【关键要点】\n" + '\n'.join(f"- {p}" for p in minutes.key_points))
        if minutes.chapters:
            chap_lines = [f"- {c.get('t', '')} {c.get('title', '')}: {c.get('summary', '')}"
                          for c in minutes.chapters]
            ctx_parts.append(f"\n【章节】\n" + '\n'.join(chap_lines))
    if transcript and transcript.full_text:
        # 截断防止 token 过长
        ft = transcript.full_text
        ctx_parts.append(f"\n【完整转录】\n{ft[:8000]}{'... [已截断]' if len(ft) > 8000 else ''}")
    context_text = '\n'.join(ctx_parts)

    # 调 AI
    from app.services.meeting_service import MeetingService
    config = MeetingService.get_ai_provider_config()
    if not config['api_key']:
        return jsonify({'success': False, 'message': 'AI 服务未配置'}), 503

    # 构造 messages：history + 当前提问（system 在 _call 时单独处理）
    messages = []
    for h in history[-6:]:  # 只带最近 6 轮
        if h.get('role') in ('user', 'assistant') and h.get('content'):
            messages.append({'role': h['role'], 'content': h['content'][:2000]})
    messages.append({
        'role': 'user',
        'content': f"{context_text}\n\n【我的问题】\n{user_question}\n\n请基于上面的会议内容简洁回答（中文，2-5 句话）。"
    })

    try:
        if config['provider'] == 'openai':
            client = MeetingService.get_openai_client()
            resp = client.chat.completions.create(
                model=config['model'],
                messages=[{'role': 'system', 'content': '你是会议助手，根据已有会议纪要和转录回答问题。'}] + messages,
                max_tokens=600,
                temperature=0.4,
            )
            answer = resp.choices[0].message.content.strip()
        else:
            import anthropic
            client = anthropic.Anthropic(
                api_key=config['api_key'],
                base_url=os.environ.get('ANTHROPIC_BASE_URL') or None,
            )
            resp = client.messages.create(
                model=config['model'],
                max_tokens=600,
                system=[
                    {'type': 'text', 'text': "You are Claude Code, Anthropic's official CLI for Claude."},
                    {'type': 'text', 'text': '你是会议助手，根据已有会议纪要和转录回答问题。回答简洁、有依据。'},
                ],
                messages=messages,
            )
            answer = first_text(resp).strip()
        return jsonify({'success': True, 'answer': answer})
    except Exception as e:
        logger.error(f'AI chat 失败 recording={recording_id}: {e}', exc_info=True)
        return jsonify({'success': False, 'message': f'AI 回答失败: {e}'}), 500


@meeting.route('/api/recordings/<int:recording_id>/diarize', methods=['POST'])
@login_required
def api_diarize(recording_id):
    """手动触发声纹分离（详情页"重新识别说话人"按钮用）"""
    recording = MeetingRecording.query.get_or_404(recording_id)
    if not can_edit_recording(current_user, recording):
        return jsonify({'success': False, 'message': _('无权操作')}), 403

    from app.services.diarization_service import DiarizationService
    if not DiarizationService.is_available():
        return jsonify({'success': False, 'message': _('声纹分离服务未配置')}), 503

    import threading
    from flask import current_app
    app_obj = current_app._get_current_object()

    def _bg():
        with app_obj.app_context():
            try:
                DiarizationService.run_for_recording(recording_id)
            except Exception as e:
                app_obj.logger.error(f"[diarize] 异常 recording_id={recording_id}: {e}", exc_info=True)

    threading.Thread(target=_bg, daemon=True).start()
    return jsonify({'success': True, 'message': _('声纹分离已在后台运行，30 秒后刷新查看')})


@meeting.route('/api/recordings/<int:recording_id>/speaker-mapping', methods=['POST'])
@login_required
def api_speaker_mapping(recording_id):
    """提交 SPEAKER_N → 真名 mapping，重写所有 segments 的 speaker_display"""
    recording = MeetingRecording.query.get_or_404(recording_id)
    if not can_edit_recording(current_user, recording):
        return jsonify({'success': False, 'message': _('无权操作')}), 403

    data = request.get_json() or {}
    mapping = data.get('mapping') or {}
    if not isinstance(mapping, dict):
        return jsonify({'success': False, 'message': 'mapping 必须是对象 {SPEAKER_00: "张三", ...}'}), 400

    from app.services.diarization_service import DiarizationService
    result = DiarizationService.apply_speaker_mapping(recording_id, mapping)
    return jsonify(result)


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
            if recording and recording.storage_url:
                return redirect(recording.storage_url)

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

    if not recording.storage_url:
        abort(404, description='音频文件不存在')

    storage_type = getattr(recording, 'storage_type', None) or \
                   os.environ.get('MEETING_STORAGE_TYPE', 'synology').lower()

    if storage_type == 'synology':
        # 从群晖WebDAV获取
        from app.utils.synology_webdav_client import get_synology_webdav_client
        webdav = get_synology_webdav_client()

        if not webdav.is_configured:
            abort(503, description='群晖WebDAV未配置')

        remote_path = recording.storage_url

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
        local_path = recording.storage_url.replace('/storage/', local_storage_root.rstrip('/') + '/')
        # 转绝对路径，避免 send_file 基于 app.root_path 错误解析
        local_path = os.path.abspath(local_path)

        if not os.path.exists(local_path):
            abort(404, description=f'文件不存在: {local_path}')

        return send_file(
            local_path,
            mimetype='audio/webm',
            as_attachment=False,
            conditional=True  # 支持 Range 请求，便于音频拖动进度条
        )

    else:
        # Supabase - 重定向到公开URL
        return redirect(recording.storage_url)


@meeting.route('/audio/<int:recording_id>/info')
@login_required
def audio_info(recording_id):
    """获取音频文件信息"""
    import os

    recording = MeetingRecording.query.get_or_404(recording_id)

    if not can_view_recording(current_user, recording):
        return jsonify({'success': False, 'message': _('无权访问')}), 403

    if not recording.storage_url:
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
            file_info = webdav.get_file_info(recording.storage_url)
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
