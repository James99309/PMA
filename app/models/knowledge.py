# -*- coding: utf-8 -*-
"""
知识库系统数据模型

KnowledgeSpace: 知识空间
KnowledgeDocument: 文档标签关联（虚拟标记）
KnowledgeChunk: 文本分块 + 向量
KnowledgeChatSession: 问答会话
KnowledgeChatMessage: 问答消息
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship, backref

from app import db

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    # pgvector 未安装时的占位符，避免导入失败
    Vector = None


def get_local_time():
    """获取本地时间（北京时区）"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


class KnowledgeSpace(db.Model):
    """知识空间"""
    __tablename__ = 'knowledge_spaces'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), default='book')
    color = Column(String(20), default='blue')
    access_level = Column(String(20), default='all')  # all / department / role / admin_only
    allowed_departments = Column(JSON, nullable=True)
    allowed_roles = Column(JSON, nullable=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)

    # 关系
    creator = relationship('User', foreign_keys=[created_by])
    documents = relationship('KnowledgeDocument', back_populates='space', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'color': self.color,
            'access_level': self.access_level,
            'allowed_departments': self.allowed_departments,
            'allowed_roles': self.allowed_roles,
            'created_by': self.created_by,
            'creator_name': (self.creator.real_name or self.creator.username) if self.creator else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'document_count': self.documents.filter_by(status='ready').count() if self.documents else 0,
        }


class KnowledgeDocument(db.Model):
    """文档标签关联 — 虚拟标记，文件不移动"""
    __tablename__ = 'knowledge_documents'

    id = Column(Integer, primary_key=True)
    space_id = Column(Integer, ForeignKey('knowledge_spaces.id'), nullable=False, index=True)
    file_library_id = Column(Integer, ForeignKey('file_library.id'), nullable=False, index=True)
    user_file_ref_id = Column(Integer, ForeignKey('user_file_refs.id'), nullable=True)
    title = Column(String(500), nullable=False)
    status = Column(String(20), default='pending', nullable=False, index=True)
    # status: pending / processing / ready / error / expired
    is_authoritative = Column(Boolean, default=False)
    priority_weight = Column(Float, default=1.0)
    chunk_count = Column(Integer, default=0)
    processing_error = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    added_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    expired_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)

    # 关系
    space = relationship('KnowledgeSpace', back_populates='documents')
    file_library = relationship('FileLibrary', backref=backref('knowledge_docs', lazy='dynamic'))
    user_file_ref = relationship('UserFileRef', backref=backref('knowledge_docs', lazy='dynamic'))
    adder = relationship('User', foreign_keys=[added_by])
    chunks = relationship('KnowledgeChunk', back_populates='document',
                          cascade='all, delete-orphan', lazy='dynamic')

    __table_args__ = (
        Index('ix_knowledge_docs_space_status', 'space_id', 'status'),
        Index('ix_knowledge_docs_file_lib', 'file_library_id'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'space_id': self.space_id,
            'file_library_id': self.file_library_id,
            'user_file_ref_id': self.user_file_ref_id,
            'title': self.title,
            'status': self.status,
            'is_authoritative': self.is_authoritative,
            'priority_weight': self.priority_weight,
            'chunk_count': self.chunk_count,
            'processing_error': self.processing_error,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'added_by': self.added_by,
            'adder_name': (self.adder.real_name or self.adder.username) if self.adder else None,
            'expired_at': self.expired_at.isoformat() if self.expired_at else None,
            'version': self.version,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'file_name': self.file_library.original_filename if self.file_library else None,
            'file_size': self.file_library.file_size if self.file_library else None,
            'mime_type': self.file_library.mime_type if self.file_library else None,
        }


class KnowledgeChunk(db.Model):
    """文本分块 + 向量"""
    __tablename__ = 'knowledge_chunks'

    id = Column(Integer, primary_key=True)
    document_id = Column(Integer, ForeignKey('knowledge_documents.id', ondelete='CASCADE'),
                         nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    # embedding 列由迁移脚本用原生 SQL 创建（pgvector Vector(1024)）
    token_count = Column(Integer, default=0)
    metadata_ = Column('metadata', JSON, nullable=True)  # {"page": 5, "section": "..."}

    # 关系
    document = relationship('KnowledgeDocument', back_populates='chunks')

    __table_args__ = (
        Index('ix_knowledge_chunks_doc_idx', 'document_id', 'chunk_index'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'document_id': self.document_id,
            'chunk_index': self.chunk_index,
            'content': self.content,
            'token_count': self.token_count,
            'metadata': self.metadata_,
        }


class KnowledgeChatSession(db.Model):
    """问答会话"""
    __tablename__ = 'knowledge_chat_sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    title = Column(String(200), nullable=True)
    space_ids = Column(JSON, nullable=True)  # 搜索范围，null=全部
    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)

    # 关系
    user = relationship('User', foreign_keys=[user_id])
    messages = relationship('KnowledgeChatMessage', back_populates='session',
                            cascade='all, delete-orphan', lazy='dynamic',
                            order_by='KnowledgeChatMessage.created_at')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'space_ids': self.space_ids,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class KnowledgeChatMessage(db.Model):
    """问答消息"""
    __tablename__ = 'knowledge_chat_messages'

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey('knowledge_chat_sessions.id', ondelete='CASCADE'),
                        nullable=False, index=True)
    role = Column(String(10), nullable=False)  # user / assistant
    content = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)  # [{"doc_id":1, "title":"...", "score":0.92}]
    tokens_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=get_local_time)

    # 关系
    session = relationship('KnowledgeChatSession', back_populates='messages')

    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'sources': self.sources,
            'tokens_used': self.tokens_used,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
