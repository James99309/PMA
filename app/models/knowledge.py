# -*- coding: utf-8 -*-
"""
知识库系统数据模型 (Phase 2 — 标签模式)

KnowledgeTag: 知识库标签（管理员预定义）
KnowledgeDocument: 文档标签关联（虚拟标记，文件不移动）
KnowledgeChunk: 文本分块 + 向量
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, ForeignKey, Index, JSON, Table
from sqlalchemy.orm import relationship, backref

from app import db

try:
    from pgvector.sqlalchemy import Vector
except ImportError:
    Vector = None


def get_local_time():
    """获取本地时间（北京时区）"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


# 多对多关联表
knowledge_document_tags = Table(
    'knowledge_document_tags',
    db.Model.metadata,
    Column('document_id', Integer, ForeignKey('knowledge_documents.id', ondelete='CASCADE'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('knowledge_tags.id', ondelete='CASCADE'), primary_key=True),
)


class KnowledgeTag(db.Model):
    """知识库标签（管理员预定义）"""
    __tablename__ = 'knowledge_tags'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    color = Column(String(20), default='blue')
    description = Column(String(500), nullable=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=get_local_time)

    # 关系
    creator = relationship('User', foreign_keys=[created_by])
    documents = relationship('KnowledgeDocument', secondary=knowledge_document_tags,
                             back_populates='tags', lazy='dynamic')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'description': self.description,
            'created_by': self.created_by,
            'creator_name': (self.creator.real_name or self.creator.username) if self.creator else None,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'document_count': 0,  # 由 API 端点计算，避免 N+1
        }


class KnowledgeDocument(db.Model):
    """文档标签关联 — 虚拟标记，文件不移动"""
    __tablename__ = 'knowledge_documents'

    id = Column(Integer, primary_key=True)
    file_library_id = Column(Integer, ForeignKey('file_library.id'), nullable=False, index=True)
    user_file_ref_id = Column(Integer, ForeignKey('user_file_refs.id'), nullable=True)
    title = Column(String(500), nullable=False)
    status = Column(String(20), default='pending', nullable=False, index=True)
    # status: pending / processing / ready / error / expired
    chunk_count = Column(Integer, default=0)
    processing_error = Column(Text, nullable=True)
    processed_at = Column(DateTime, nullable=True)
    added_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    expired_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)

    # 关系
    file_library = relationship('FileLibrary', backref=backref('knowledge_docs', lazy='dynamic'))
    user_file_ref = relationship('UserFileRef', backref=backref('knowledge_docs', lazy='dynamic'))
    adder = relationship('User', foreign_keys=[added_by])
    tags = relationship('KnowledgeTag', secondary=knowledge_document_tags,
                        back_populates='documents', lazy='joined')
    chunks = relationship('KnowledgeChunk', back_populates='document',
                          cascade='all, delete-orphan', lazy='dynamic')

    __table_args__ = (
        Index('ix_knowledge_docs_status', 'status'),
        Index('ix_knowledge_docs_file_lib', 'file_library_id'),
        Index('ix_knowledge_docs_added_by', 'added_by'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'file_library_id': self.file_library_id,
            'user_file_ref_id': self.user_file_ref_id,
            'title': self.title,
            'status': self.status,
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
            'tags': [{'id': t.id, 'name': t.name, 'color': t.color} for t in self.tags] if self.tags else [],
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
