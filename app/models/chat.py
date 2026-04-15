# -*- coding: utf-8 -*-
"""
聊天系统模型 - 用于实时聊天、群组对话和AI翻译

ChatConversation: 对话/群组
ChatParticipant: 对话参与者
ChatMessage: 聊天消息
ChatTranslation: 消息翻译
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Index, UniqueConstraint

from app import db


class ChatConversation(db.Model):
    """对话/群组模型"""
    __tablename__ = 'chat_conversations'

    id = Column(Integer, primary_key=True)
    type = Column(String(20), nullable=False, default='private')  # 'private', 'group', 'ai'
    name = Column(String(100), nullable=True)  # 群组名称，私聊时为空
    topic = Column(String(100), nullable=True)  # AI 自动生成的话题标题
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))
    is_deleted = Column(Boolean, default=False)

    # 关系
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_conversations')
    participants = db.relationship('ChatParticipant', backref='conversation', lazy='dynamic',
                                   cascade='all, delete-orphan')
    messages = db.relationship('ChatMessage', backref='conversation', lazy='dynamic',
                                cascade='all, delete-orphan')

    __table_args__ = (
        Index('ix_chat_conv_type', 'type'),
        Index('ix_chat_conv_created_by', 'created_by'),
    )

    def to_dict(self, current_user_id=None):
        """转换为字典，包含未读消息数"""
        result = {
            'id': self.id,
            'type': self.type,
            'name': self.name,
            'topic': self.topic,
            'created_by': self.created_by,
            'creator_name': self.creator.real_name or self.creator.username if self.creator else None,
            'created_at': (self.created_at.isoformat() + 'Z') if self.created_at else None,
            'updated_at': (self.updated_at.isoformat() + 'Z') if self.updated_at else None,
        }

        # 计算未读消息数
        if current_user_id:
            participant = self.participants.filter_by(user_id=current_user_id).first()
            if participant and participant.last_read_at:
                unread_count = self.messages.filter(
                    ChatMessage.created_at > participant.last_read_at,
                    ChatMessage.sender_id != current_user_id,
                    ChatMessage.is_deleted == False
                ).count()
            else:
                # 没有 last_read_at 则所有非自己发的消息都未读
                unread_count = self.messages.filter(
                    ChatMessage.sender_id != current_user_id,
                    ChatMessage.is_deleted == False
                ).count() if participant else 0
            result['unread_count'] = unread_count

        # 获取最后一条消息
        last_message = self.messages.filter(
            ChatMessage.is_deleted == False
        ).order_by(ChatMessage.created_at.desc()).first()
        if last_message:
            # 附件消息显示类型标签
            lm_content = last_message.content[:50] if last_message.content else ''
            if not lm_content and last_message.message_type == 'image':
                lm_content = '[图片]'
            elif not lm_content and last_message.message_type == 'video':
                lm_content = '[视频]'
            elif not lm_content and last_message.message_type == 'file':
                lm_content = f'[文件] {last_message.file_name or ""}'
            elif last_message.message_type == 'customer_card':
                lm_content = '[客户卡片]'
            elif last_message.message_type == 'project_card':
                lm_content = '[项目卡片]'
            elif last_message.message_type == 'form_result_card':
                try:
                    import json
                    card = json.loads(last_message.content or '{}')
                    lm_content = f'[已创建: {card.get("entity_name", "记录")}]'
                except (json.JSONDecodeError, TypeError):
                    lm_content = '[表单操作]'
            result['last_message'] = {
                'id': last_message.id,
                'content': lm_content,
                'sender_id': last_message.sender_id,
                'created_at': (last_message.created_at.isoformat() + 'Z') if last_message.created_at else None,
            }

        # 参与者列表
        result['participants'] = [
            {
                'user_id': p.user_id,
                'role': p.role,
                'user_name': p.user.real_name or p.user.username if p.user else None,
            }
            for p in self.participants.all()
        ]

        return result


class ChatParticipant(db.Model):
    """对话参与者模型"""
    __tablename__ = 'chat_participants'

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('chat_conversations.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    role = Column(String(20), default='member')  # 'owner', 'member'
    joined_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_read_at = Column(DateTime, nullable=True)

    # 关系
    user = db.relationship('User', foreign_keys=[user_id], backref='chat_participations')

    __table_args__ = (
        UniqueConstraint('conversation_id', 'user_id', name='uq_chat_participant_conv_user'),
        Index('ix_chat_participant_user_id', 'user_id'),
    )


class ChatMessage(db.Model):
    """聊天消息模型"""
    __tablename__ = 'chat_messages'

    id = Column(Integer, primary_key=True)
    conversation_id = Column(Integer, ForeignKey('chat_conversations.id'), nullable=False)
    sender_id = Column(Integer, ForeignKey('users.id'), nullable=True)  # NULL 表示 AI 消息
    content = Column(Text, nullable=True)  # 附件消息时可为空
    message_type = Column(String(20), default='text')  # text / image / video / file
    file_url = Column(String(500), nullable=True)       # NAS 存储路径
    file_name = Column(String(255), nullable=True)      # 原始文件名
    file_size = Column(Integer, nullable=True)           # 文件大小(bytes)
    source_language = Column(String(10), default='zh')  # 消息原始语言
    is_ai_response = Column(Boolean, default=False)
    ai_model = Column(String(50), nullable=True)  # AI 模型名称
    ai_prompt_tokens = Column(Integer, nullable=True)  # AI prompt token 数量
    ai_completion_tokens = Column(Integer, nullable=True)  # AI completion token 数量
    reply_to_id = Column(Integer, ForeignKey('chat_messages.id'), nullable=True)  # 回复的消息ID
    ai_processed = Column(Boolean, default=False)  # 文件消息是否已被 AI 处理
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_deleted = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

    # 关系
    sender = db.relationship('User', foreign_keys=[sender_id], backref='chat_messages_sent')
    reply_to = db.relationship('ChatMessage', remote_side=[id], backref='replies')
    translations = db.relationship('ChatTranslation', backref='message', lazy='dynamic',
                                    cascade='all, delete-orphan')

    __table_args__ = (
        Index('ix_chat_msg_conv_created', 'conversation_id', 'created_at'),
        Index('ix_chat_msg_sender_id', 'sender_id'),
    )

    def to_dict(self, viewer_language='zh'):
        """转换为字典，如果查看者语言与源语言不同则包含翻译"""
        result = {
            'id': self.id,
            'conversation_id': self.conversation_id,
            'sender_id': self.sender_id,
            'sender_name': (self.sender.real_name or self.sender.username if self.sender
                            else '' if self.message_type == 'cross_system' else 'AI'),
            'content': self.content,
            'message_type': self.message_type or 'text',
            'file_url': self.file_url,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'source_language': self.source_language,
            'is_ai_response': self.is_ai_response,
            'ai_model': self.ai_model,
            'reply_to_id': self.reply_to_id,
            'created_at': (self.created_at.isoformat() + 'Z') if self.created_at else None,
            'is_deleted': self.is_deleted,
        }

        # 如果查看者语言与源语言不同，附带翻译
        if viewer_language and viewer_language != self.source_language:
            translation = self.translations.filter_by(target_language=viewer_language).first()
            if translation:
                result['translation'] = translation.translated_content
                result['translation_label'] = 'Original (English)' if self.source_language == 'en' else '原文（中文）'

        # 卡片消息解析
        if self.message_type in ('customer_card', 'project_card', 'form_result_card'):
            try:
                import json
                result['card_data'] = json.loads(self.content) if self.content else {}
            except (json.JSONDecodeError, TypeError):
                result['card_data'] = {}
            # 项目卡片：翻译阶段 key + 注入阶段进度条数据
            if self.message_type == 'project_card':
                try:
                    from app.utils.dictionary_helpers import project_stage_label
                    stage = result['card_data'].get('current_stage', '')
                    if stage:
                        translated = project_stage_label(stage)
                        if translated != stage:
                            result['card_data']['current_stage'] = translated
                    # 注入阶段进度条数据（实时从数据库读取）
                    project_id = result['card_data'].get('project_id')
                    if project_id:
                        from app.models.chat import _build_project_stages_for_card
                        stages_info = _build_project_stages_for_card(project_id)
                        if stages_info:
                            result['card_data'].update(stages_info)
                except Exception:
                    pass

        # 回复消息预览
        if self.reply_to_id and self.reply_to:
            result['reply_to'] = {
                'id': self.reply_to.id,
                'content': self.reply_to.content[:50] if self.reply_to.content else '',
                'sender_name': (self.reply_to.sender.real_name or self.reply_to.sender.username
                                if self.reply_to.sender else 'AI'),
                'message_type': self.reply_to.message_type or 'text',
                'file_name': self.reply_to.file_name,
                'file_url': self.reply_to.file_url,
            }

        return result


class ChatTranslation(db.Model):
    """消息翻译模型"""
    __tablename__ = 'chat_translations'

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey('chat_messages.id'), nullable=False)
    target_language = Column(String(10), nullable=False)  # 目标语言代码
    translated_content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint('message_id', 'target_language', name='uq_chat_translation_msg_lang'),
    )


# ---------------------------------------------------------------------------
# 项目阶段进度条数据构建（供 project_card 消息使用）
# ---------------------------------------------------------------------------

_MAIN_STAGES = ['discover', 'embed', 'pre_tender', 'tendering', 'awarded', 'quoted', 'signed']


def _build_project_stages_for_card(project_id):
    """构建项目阶段进度条数据，包含权限判断

    Returns:
        dict with keys: stages, can_edit, stage_key; or None on failure
    """
    try:
        from flask_login import current_user
        from app.models.project import Project
        from app.utils.dictionary_helpers import PROJECT_STAGE_LABELS
        from app.utils.i18n import get_current_language

        project = Project.query.get(project_id)
        if not project:
            return None

        lang = get_current_language()
        current = project.current_stage or 'discover'
        is_terminal = current in ('lost', 'paused')
        current_idx = _MAIN_STAGES.index(current) if current in _MAIN_STAGES else -1

        # 权限判断
        can_edit = False
        try:
            if current_user and current_user.is_authenticated:
                from app.permissions import is_admin_or_ceo
                if is_admin_or_ceo():
                    can_edit = True
                elif project.owner_id == current_user.id:
                    can_edit = True
                elif hasattr(project, 'vendor_sales_manager_id') and project.vendor_sales_manager_id == current_user.id:
                    can_edit = True
                else:
                    viewable_ids = current_user.get_viewable_user_ids() if hasattr(current_user, 'get_viewable_user_ids') else [current_user.id]
                    can_edit = project.owner_id in viewable_ids

                # signed 阶段锁定
                if current == 'signed':
                    can_edit = False
                # 项目锁定检查
                if can_edit and current != 'signed':
                    from app.helpers.project_helpers import is_project_editable
                    is_editable, _ = is_project_editable(project.id, current_user.id)
                    if not is_editable and not is_admin_or_ceo():
                        can_edit = False
        except Exception:
            can_edit = False

        # 终端状态：找最后活跃阶段
        last_active_idx = -1
        if is_terminal:
            try:
                from app.models.projectpm_stage_history import ProjectStageHistory
                histories = ProjectStageHistory.query.filter_by(project_id=project_id).order_by(
                    ProjectStageHistory.change_date.desc()
                ).all()
                for h in histories:
                    stage_key = h.to_stage
                    if stage_key in _MAIN_STAGES:
                        last_active_idx = _MAIN_STAGES.index(stage_key)
                        break
            except Exception:
                pass

        # 构建 stages 数组
        stages = []
        for idx, key in enumerate(_MAIN_STAGES):
            label = PROJECT_STAGE_LABELS.get(key, {}).get(lang, key)
            if is_terminal:
                status = 'completed' if idx <= last_active_idx else 'pending'
                clickable = False
            elif idx < current_idx:
                status = 'completed'
                clickable = False
            elif idx == current_idx:
                status = 'current'
                clickable = False
            else:
                status = 'pending'
                # 只有下一个阶段可点击
                clickable = can_edit and idx == current_idx + 1

            stages.append({
                'key': key,
                'label': label,
                'status': status,
                'clickable': clickable,
            })

        return {
            'stages': stages,
            'can_edit': can_edit,
            'stage_key': current,  # 原始英文 key，供前端更新使用
        }
    except Exception:
        return None
