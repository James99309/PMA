# -*- coding: utf-8 -*-
"""
知识库数据模型

旧 RAG 向量方案（KnowledgeDocument / KnowledgeChunk / 向量嵌入）已在 2026-04-09 下线，
迁移至基于 Karpathy LLM Wiki 的方案。

当前模型：
- KnowledgeTag — 标签，未来可被 Wiki 复用作文章分类
- KnowledgeRawFile — Wiki 原始文件登记表（磁盘文件的数据库索引）
- KnowledgeWikiArticle — Wiki 文章元数据（Markdown 内容存磁盘）

参见实施方案 docs/plans/2026-04-09-wiki-knowledge-base.md。
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Index, JSON
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


# ──────────────────────────────────────────────────────────────────
# Wiki 知识库（Karpathy LLM Wiki 方案）
# ──────────────────────────────────────────────────────────────────


class KnowledgeRawFile(db.Model):
    """Wiki 原始文件登记表

    指向 file_library 中的文件 + 该文件在 Wiki 知识库中的 topic 和编译状态。
    实际文件会被拷贝到 storage/knowledge_base/raw/<topic>/<safe_name> 做独立留存，
    避免 file_library 被清理时误删。
    """
    __tablename__ = 'knowledge_raw_files'

    id = Column(Integer, primary_key=True)
    file_library_id = Column(Integer, ForeignKey('file_library.id'), nullable=False, index=True)
    topic = Column(String(100), nullable=False, index=True)
    raw_path = Column(String(500), nullable=False)  # 相对 wiki_root 的路径，如 raw/product/2026-04-09-xxx.pdf
    title = Column(String(500), nullable=False)
    ingest_status = Column(String(20), default='pending', nullable=False, index=True)
    # ingest_status: pending / processing / ingested / error
    ingest_error = Column(Text, nullable=True)
    ingested_at = Column(DateTime, nullable=True)
    added_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime, default=get_local_time)

    file_library = relationship('FileLibrary')
    adder = relationship('User', foreign_keys=[added_by])

    __table_args__ = (
        Index('ix_knowledge_raw_topic_status', 'topic', 'ingest_status'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'file_library_id': self.file_library_id,
            'topic': self.topic,
            'raw_path': self.raw_path,
            'title': self.title,
            'ingest_status': self.ingest_status,
            'ingest_error': self.ingest_error,
            'ingested_at': self.ingested_at.isoformat() if self.ingested_at else None,
            'added_by': self.added_by,
            'adder_name': (self.adder.real_name or self.adder.username) if self.adder else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'file_name': self.file_library.original_filename if self.file_library else None,
        }


class KnowledgeWikiArticle(db.Model):
    """Wiki 文章元数据

    文章的 Markdown 正文存于 storage/knowledge_base/wiki/<topic>/<slug>.md，
    本表只保存标题、摘要、引用关系等元数据，便于列表、检索和追踪。
    """
    __tablename__ = 'knowledge_wiki_articles'

    id = Column(Integer, primary_key=True)
    topic = Column(String(100), nullable=False, index=True)
    slug = Column(String(200), nullable=False)
    title = Column(String(500), nullable=False)
    file_path = Column(String(500), nullable=False, unique=True)  # 相对 wiki_root，如 wiki/product/gp328p.md
    summary = Column(Text, nullable=True)  # 用于 index.md 和全文检索
    content_length = Column(Integer, default=0)

    # 来源追踪：参与了本文编译的 raw_file.id 列表
    source_raw_ids = Column(JSON, nullable=True)

    # 出向引用：本文指向的其他文章 slug 列表，如 ["product/gp538"]
    outbound_refs = Column(JSON, nullable=True)

    last_compiled_at = Column(DateTime, nullable=True)
    compile_model = Column(String(100), nullable=True)  # 记录用了哪个 Claude 模型
    created_at = Column(DateTime, default=get_local_time)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)

    __table_args__ = (
        Index('ix_wiki_article_topic_slug', 'topic', 'slug', unique=True),
        # PG 全文检索 GIN 索引由 migration 里手写 SQL 创建
    )

    def to_dict(self, include_content: bool = False):
        d = {
            'id': self.id,
            'topic': self.topic,
            'slug': self.slug,
            'title': self.title,
            'file_path': self.file_path,
            'summary': self.summary,
            'content_length': self.content_length,
            'source_raw_ids': self.source_raw_ids or [],
            'outbound_refs': self.outbound_refs or [],
            'last_compiled_at': self.last_compiled_at.isoformat() if self.last_compiled_at else None,
            'compile_model': self.compile_model,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_content:
            from app.services.wiki.storage import read_article_content
            d['content'] = read_article_content(self.file_path)
        return d
