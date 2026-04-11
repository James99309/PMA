# -*- coding: utf-8 -*-
"""
知识库数据模型

旧 RAG 向量方案（KnowledgeDocument / KnowledgeChunk / 向量嵌入）已在 2026-04-09 下线，
迁移至基于 Karpathy LLM Wiki 的方案。

当前保留 KnowledgeTag，作为未来 Wiki 文章分类标签预留。
Wiki 相关模型（KnowledgeRawFile / KnowledgeWikiArticle）在 Phase 2 新增。

参见实施方案 docs/plans/2026-04-09-wiki-knowledge-base.md。
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app import db


def get_local_time():
    """获取本地时间（北京时区）"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


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

    creator = relationship('User', foreign_keys=[created_by])

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
        }
