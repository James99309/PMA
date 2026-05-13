# -*- coding: utf-8 -*-
"""
会议录音与纪要模块 - 数据模型

MeetingRecording: 会议录音记录
MeetingTranscript: 转录文本
MeetingSpeaker: 说话人信息
MeetingMinutes: 会议纪要
MeetingActionItem: 行动项
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
import enum

from app import db


def get_local_time():
    """获取本地时间（北京时区）"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


class RecordingStatus(enum.Enum):
    """录音状态"""
    RECORDING = 'recording'      # 录音中
    UPLOADING = 'uploading'      # 上传中
    UPLOADED = 'uploaded'        # 已上传
    TRANSCRIBING = 'transcribing'  # 转录中
    TRANSCRIBED = 'transcribed'  # 已转录
    FAILED = 'failed'            # 失败


class MinutesStatus(enum.Enum):
    """纪要状态"""
    NONE = 'none'                # 无纪要
    GENERATING = 'generating'    # 生成中
    DRAFT = 'draft'              # 草稿
    PUBLISHED = 'published'      # 已发布


class MeetingRecording(db.Model):
    """会议录音记录"""
    __tablename__ = 'meeting_recordings'

    id = Column(Integer, primary_key=True)

    # 关联的工作项（会议行程）- 可选，从列表页发起时无关联
    work_item_id = Column(Integer, ForeignKey('work_items.id'), nullable=True, index=True)
    work_item = relationship('WorkItem', backref='meeting_recordings')

    # 会议基本信息（从工作项复制或手动填写）
    title = Column(String(200), nullable=False)  # 会议标题
    meeting_time = Column(DateTime, nullable=False)  # 会议时间

    # 录音信息
    recording_mode = Column(String(50))  # 'microphone' / 'microphone_system'
    duration_seconds = Column(Integer, default=0)  # 录音时长（秒）
    file_size_bytes = Column(Integer, default=0)  # 文件大小（字节）
    storage_path = Column(String(500))  # 混音轨存储路径（mic + system，回放用）
    storage_url = Column(String(1000))  # 访问URL

    # 仅对方端（系统音频）独立录音 — pyannote 在此轨道做声纹分离，
    # 避免把 mic（已知是当前用户）也卷入分离造成 SPEAKER_xx 与 me/peer 错乱
    system_storage_path = Column(String(500))
    system_storage_url = Column(String(1000))

    # 分块上传状态
    total_chunks = Column(Integer, default=0)  # 总块数（mixed 轨）
    uploaded_chunks = Column(Integer, default=0)  # 已上传块数（mixed 轨）
    chunk_paths = Column(JSON, default=list)  # 各块存储路径（mixed 轨）
    system_chunk_paths = Column(JSON, default=list)  # system 轨各块路径

    # 状态
    status = Column(String(20), default='recording', index=True)
    error_message = Column(Text)  # 错误信息

    # 系统字段
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    owner = relationship('User', backref='meeting_recordings')

    # 邀请旁听的 PMA 同事 user_id 列表
    # 被邀请人不录音不上传，仅订阅同一份 transcript；列表/详情页权限会放行
    invited_user_ids = Column(JSON, default=list)

    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)
    is_deleted = Column(Boolean, default=False)

    # 关联
    transcript = relationship('MeetingTranscript', back_populates='recording', uselist=False)
    minutes = relationship('MeetingMinutes', back_populates='recording', uselist=False)

    def get_status_display(self):
        """获取状态显示文本"""
        status_map = {
            'recording': '录音中',
            'uploading': '上传中',
            'uploaded': '已上传',
            'transcribing': '转录中',
            'transcribed': '已转录',
            'failed': '失败'
        }
        return status_map.get(self.status, self.status)

    def get_duration_display(self):
        """获取时长显示文本（HH:MM:SS 或 MM:SS）"""
        if not self.duration_seconds:
            return '00:00'
        hours = self.duration_seconds // 3600
        minutes = (self.duration_seconds % 3600) // 60
        seconds = self.duration_seconds % 60
        if hours > 0:
            return f'{hours:02d}:{minutes:02d}:{seconds:02d}'
        return f'{minutes:02d}:{seconds:02d}'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'work_item_id': self.work_item_id,
            'title': self.title,
            'meeting_time': self.meeting_time.isoformat() if self.meeting_time else None,
            'recording_mode': self.recording_mode,
            'duration_seconds': self.duration_seconds,
            'duration_display': self.get_duration_display(),
            'file_size_bytes': self.file_size_bytes,
            'storage_url': self.storage_url,
            'system_storage_url': self.system_storage_url,
            'status': self.status,
            'status_display': self.get_status_display(),
            'error_message': self.error_message,
            'owner_id': self.owner_id,
            'owner_name': self.owner.real_name or self.owner.username if self.owner else None,
            'invited_user_ids': self.invited_user_ids or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'has_transcript': self.transcript is not None,
            'has_minutes': self.minutes is not None
        }


class MeetingTranscript(db.Model):
    """会议转录文本"""
    __tablename__ = 'meeting_transcripts'

    id = Column(Integer, primary_key=True)

    # 关联的录音
    recording_id = Column(Integer, ForeignKey('meeting_recordings.id'), nullable=False, unique=True)
    recording = relationship('MeetingRecording', back_populates='transcript')

    # 转录状态
    status = Column(String(20), default='pending', index=True)  # pending, processing, completed, failed
    progress_percent = Column(Integer, default=0)  # 进度百分比
    error_message = Column(Text)

    # 转录结果
    full_text = Column(Text)  # 完整转录文本
    segments = Column(JSON, default=list)  # 分段数据 [{start, end, text, speaker_id}]
    language = Column(String(10), default='zh')  # 语言

    # 说话人识别
    speaker_count = Column(Integer, default=0)  # 识别到的说话人数量
    speakers_mapped = Column(Boolean, default=False)  # 说话人是否已映射

    # 系统字段
    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)
    completed_at = Column(DateTime)  # 转录完成时间

    # 关联
    speakers = relationship('MeetingSpeaker', back_populates='transcript', cascade='all, delete-orphan')

    def to_dict(self, include_segments=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'recording_id': self.recording_id,
            'status': self.status,
            'progress_percent': self.progress_percent,
            'error_message': self.error_message,
            'language': self.language,
            'speaker_count': self.speaker_count,
            'speakers_mapped': self.speakers_mapped,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
        if include_segments:
            data['full_text'] = self.full_text
            data['segments'] = self.segments
        return data


class MeetingSpeaker(db.Model):
    """会议说话人"""
    __tablename__ = 'meeting_speakers'

    id = Column(Integer, primary_key=True)

    # 关联的转录
    transcript_id = Column(Integer, ForeignKey('meeting_transcripts.id'), nullable=False, index=True)
    transcript = relationship('MeetingTranscript', back_populates='speakers')

    # 说话人标识（Pyannote 生成）
    speaker_label = Column(String(50), nullable=False)  # SPEAKER_00, SPEAKER_01 等

    # 映射的用户（可选，系统用户）
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    user = relationship('User', backref='meeting_speaker_mappings')

    # 外部人员姓名（非系统用户）
    external_name = Column(String(100))

    # 示例发言（用于映射时展示）
    sample_text = Column(Text)  # 典型发言文本
    sample_start_time = Column(Float)  # 示例开始时间（秒）
    sample_end_time = Column(Float)  # 示例结束时间（秒）

    # 统计
    total_duration_seconds = Column(Float, default=0)  # 总发言时长
    segment_count = Column(Integer, default=0)  # 发言段落数

    created_at = Column(DateTime, default=get_local_time)

    def get_display_name(self):
        """获取显示名称"""
        if self.user:
            return self.user.real_name or self.user.username
        if self.external_name:
            return self.external_name
        return self.speaker_label

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'transcript_id': self.transcript_id,
            'speaker_label': self.speaker_label,
            'user_id': self.user_id,
            'user_name': self.user.real_name or self.user.username if self.user else None,
            'external_name': self.external_name,
            'display_name': self.get_display_name(),
            'sample_text': self.sample_text,
            'sample_start_time': self.sample_start_time,
            'sample_end_time': self.sample_end_time,
            'total_duration_seconds': self.total_duration_seconds,
            'segment_count': self.segment_count
        }


class MeetingMinutes(db.Model):
    """会议纪要"""
    __tablename__ = 'meeting_minutes'

    id = Column(Integer, primary_key=True)

    # 关联的录音
    recording_id = Column(Integer, ForeignKey('meeting_recordings.id'), nullable=False, unique=True)
    recording = relationship('MeetingRecording', back_populates='minutes')

    # 纪要状态
    status = Column(String(20), default='generating', index=True)  # generating, draft, published
    version = Column(Integer, default=1)  # 版本号

    # 纪要内容
    title = Column(String(200))  # 会议标题（可编辑）
    summary = Column(Text)  # 会议摘要
    key_points = Column(JSON, default=list)  # 关键要点列表 ['要点1', '要点2']
    decisions = Column(JSON, default=list)  # 决策事项列表 ['决策1', '决策2']
    # V2 新增
    chapters = Column(JSON, default=list)     # AI 切分章节 [{t, title, summary, speakers}]
    key_quotes = Column(JSON, default=list)   # 金句 [{speaker, text, ts, category}]（整句原话）
    highlights = Column(JSON, default=list)   # 段落里高光短语 ["跨语种","浮窗形态",...]（3-12 字）
    # 多语言翻译版本（按需生成 + 缓存入库）
    # 结构：{ "en": {summary, key_points, key_quotes, chapters, highlights, decisions}, "ja": {...} }
    # 不含 host 母语本身 — 那是顶层字段
    translations = Column(JSON, default=dict)

    # 参与者（从说话人映射获取）
    participants = Column(JSON, default=list)  # [{user_id, name, is_external}]

    # 关联
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)
    project = relationship('Project', backref='meeting_minutes')

    customer_id = Column(Integer, ForeignKey('companies.id'), nullable=True)
    customer = relationship('Company', backref='meeting_minutes')

    # 生成配置
    generation_mode = Column(String(20), default='standard')  # standard, detailed, concise

    # 系统字段
    owner_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    owner = relationship('User', backref='meeting_minutes')

    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)
    published_at = Column(DateTime)  # 发布时间
    is_deleted = Column(Boolean, default=False)

    # 关联
    action_items = relationship('MeetingActionItem', back_populates='minutes', cascade='all, delete-orphan')

    def get_status_display(self):
        """获取状态显示文本"""
        status_map = {
            'generating': '生成中',
            'draft': '草稿',
            'published': '已发布'
        }
        return status_map.get(self.status, self.status)

    def to_dict(self, include_content=True):
        """转换为字典"""
        data = {
            'id': self.id,
            'recording_id': self.recording_id,
            'status': self.status,
            'status_display': self.get_status_display(),
            'version': self.version,
            'title': self.title,
            'participants': self.participants,
            'project_id': self.project_id,
            'project_name': self.project.project_name if self.project else None,
            'customer_id': self.customer_id,
            'customer_name': self.customer.company_name if self.customer else None,
            'owner_id': self.owner_id,
            'owner_name': self.owner.real_name or self.owner.username if self.owner else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'action_items_count': len([a for a in self.action_items if not a.is_deleted])
        }
        if include_content:
            data['summary'] = self.summary
            data['key_points'] = self.key_points
            data['decisions'] = self.decisions
            data['chapters'] = self.chapters or []
            data['key_quotes'] = self.key_quotes or []
            data['highlights'] = self.highlights or []
            data['translations'] = self.translations or {}
            data['action_items'] = [a.to_dict() for a in self.action_items if not a.is_deleted]
        return data


class MeetingActionItem(db.Model):
    """会议行动项"""
    __tablename__ = 'meeting_action_items'

    id = Column(Integer, primary_key=True)

    # 关联的纪要
    minutes_id = Column(Integer, ForeignKey('meeting_minutes.id'), nullable=False, index=True)
    minutes = relationship('MeetingMinutes', back_populates='action_items')

    # 行动项内容
    title = Column(String(500), nullable=False)  # 任务标题
    description = Column(Text)  # 详细描述

    # 负责人
    assignee_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    assignee = relationship('User', backref='assigned_meeting_actions')
    assignee_name = Column(String(100))  # 外部人员时使用

    # 时间
    due_date = Column(DateTime)  # 截止日期
    completed_at = Column(DateTime)  # 完成时间

    # 状态
    status = Column(String(20), default='pending')  # pending, completed, overdue

    # 关联的工作项（添加到日历后）
    linked_work_item_id = Column(Integer, ForeignKey('work_items.id'), nullable=True)
    linked_work_item = relationship('WorkItem', backref='source_action_items')

    # 系统字段
    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)
    is_deleted = Column(Boolean, default=False)

    def get_assignee_display(self):
        """获取负责人显示名称"""
        if self.assignee:
            return self.assignee.real_name or self.assignee.username
        return self.assignee_name or '未指定'

    def get_status_display(self):
        """获取状态显示"""
        from datetime import datetime
        if self.status == 'completed':
            return 'completed'
        if self.due_date and datetime.now() > self.due_date:
            return 'overdue'
        return 'pending'

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'minutes_id': self.minutes_id,
            'title': self.title,
            'description': self.description,
            'assignee_id': self.assignee_id,
            'assignee_name': self.get_assignee_display(),
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'status': self.get_status_display(),
            'linked_work_item_id': self.linked_work_item_id,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
