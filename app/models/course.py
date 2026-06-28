# -*- coding: utf-8 -*-
"""互动课程(self-contained HTML deck)登记表。

取代原先写死在 knowledge_wiki.py 的 INTERACTIVE_COURSES 列表。
课件 HTML / 缩略图 / 题库仍存文件系统(app/course_assets/),本表只存元数据。
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey

from app import db


def _local_now():
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


class InteractiveCourse(db.Model):
    __tablename__ = 'interactive_courses'

    id = Column(Integer, primary_key=True)
    key = Column(String(80), unique=True, nullable=False, index=True)   # 文件名 + URL 标识
    title = Column(String(200), nullable=False)
    subtitle = Column(String(200), nullable=True)
    desc = Column(Text, nullable=True)
    accent = Column(String(20), nullable=True, default='#1A0E3D')       # 封面底色(无缩略图时)

    topic = Column(String(100), nullable=True, default='产品技术')        # 知识析出归到哪个 wiki topic
    cover_page = Column(Integer, nullable=False, default=1)              # 封面取第几页缩略图
    page_count = Column(Integer, nullable=False, default=0)
    has_thumbs = Column(Boolean, nullable=False, default=False)         # 缩略图是否已生成
    article_id = Column(Integer, nullable=True)                         # 析出的 wiki 文章 id

    owner_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=_local_now, nullable=False)
    updated_at = Column(DateTime, default=_local_now, onupdate=_local_now, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'title': self.title,
            'subtitle': self.subtitle or '',
            'desc': self.desc or '',
            'accent': self.accent or '#1A0E3D',
            'topic': self.topic or '产品技术',
            'cover_page': self.cover_page or 1,
            'page_count': self.page_count or 0,
            'has_thumbs': bool(self.has_thumbs),
            'article_id': self.article_id,
        }
