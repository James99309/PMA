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

    # 内容类型分流:html=deck 课件(默认,存量不变) / video=视频课程 / ppt=PPT/PDF 下载
    media_type = Column(String(20), nullable=False, default='html')
    # 视频来源:webdav=NAS WebDAV 流(默认,走隧道) / gdrive=Google Drive iframe(境外用户,绕隧道)
    video_source = Column(String(20), nullable=True, default='webdav')
    media_url = Column(String(500), nullable=True)   # webdav:NAS 相对路径 / gdrive:Drive 文件ID / ppt:NAS路径;html 留空
    cover_url = Column(String(500), nullable=True)   # 自定义封面 NAS 路径(video/ppt 上传封面);空则用默认
    duration = Column(Integer, nullable=True)        # 视频时长(秒)
    file_size = Column(Integer, nullable=True)       # 文件字节数(ppt 下载显示大小)
    chapters = Column(Text, nullable=True)           # 视频章节 JSON: [{"page":1,"start":0,"title":"..."}]

    topic = Column(String(100), nullable=True, default='产品技术')        # 知识析出归到哪个 wiki topic
    cover_page = Column(Integer, nullable=False, default=1)              # 封面取第几页缩略图
    page_count = Column(Integer, nullable=False, default=0)
    has_thumbs = Column(Boolean, nullable=False, default=False)         # 缩略图是否已生成
    article_id = Column(Integer, nullable=True)                         # 析出的 wiki 文章 id

    owner_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=_local_now, nullable=False)
    updated_at = Column(DateTime, default=_local_now, onupdate=_local_now, nullable=False)

    def to_dict(self):
        import json as _json
        chapters = []
        if self.chapters:
            try:
                chapters = _json.loads(self.chapters)
            except (ValueError, TypeError):
                chapters = []
        return {
            'id': self.id,
            'key': self.key,
            'title': self.title,
            'subtitle': self.subtitle or '',
            'desc': self.desc or '',
            'accent': self.accent or '#1A0E3D',
            'media_type': self.media_type or 'html',
            'video_source': self.video_source or 'webdav',
            'media_url': self.media_url or '',
            'cover_url': self.cover_url or '',
            'duration': self.duration or 0,
            'file_size': self.file_size or 0,
            'chapters': chapters,
            'topic': self.topic or '产品技术',
            'cover_page': self.cover_page or 1,
            'page_count': self.page_count or 0,
            'has_thumbs': bool(self.has_thumbs),
            'article_id': self.article_id,
        }
