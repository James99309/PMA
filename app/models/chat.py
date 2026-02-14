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
            'created_by': self.created_by,
            'creator_name': self.creator.real_name or self.creator.username if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
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
            result['last_message'] = {
                'id': last_message.id,
                'content': last_message.content[:50] if last_message.content else '',
                'sender_id': last_message.sender_id,
                'created_at': last_message.created_at.isoformat() if last_message.created_at else None,
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
    content = Column(Text, nullable=False)
    source_language = Column(String(10), default='zh')  # 消息原始语言
    is_ai_response = Column(Boolean, default=False)
    ai_model = Column(String(50), nullable=True)  # AI 模型名称
    ai_prompt_tokens = Column(Integer, nullable=True)  # AI prompt token 数量
    ai_completion_tokens = Column(Integer, nullable=True)  # AI completion token 数量
    reply_to_id = Column(Integer, ForeignKey('chat_messages.id'), nullable=True)  # 回复的消息ID
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
            'sender_name': self.sender.real_name or self.sender.username if self.sender else 'AI',
            'content': self.content,
            'source_language': self.source_language,
            'is_ai_response': self.is_ai_response,
            'ai_model': self.ai_model,
            'reply_to_id': self.reply_to_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_deleted': self.is_deleted,
        }

        # 如果查看者语言与源语言不同，附带翻译
        if viewer_language and viewer_language != self.source_language:
            translation = self.translations.filter_by(target_language=viewer_language).first()
            if translation:
                result['translated_content'] = translation.translated_content
                result['translation_language'] = viewer_language

        # 回复消息预览
        if self.reply_to_id and self.reply_to:
            result['reply_to'] = {
                'id': self.reply_to.id,
                'content': self.reply_to.content[:50] if self.reply_to.content else '',
                'sender_name': (self.reply_to.sender.real_name or self.reply_to.sender.username
                                if self.reply_to.sender else 'AI'),
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
