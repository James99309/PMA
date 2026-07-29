# -*- coding: utf-8 -*-
"""视频课程观看记录(轻量,与 HTML 课程的 TrainingModuleState 分离)。

一个 (user_id, course_key) 唯一一条:记播放位置(续播)+ 是否看完 + 看过百分比。
不做章节考核,语义只有"看到哪、看没看完"。
"""
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Index

from app import db


def _local_now():
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


class VideoWatchState(db.Model):
    __tablename__ = 'video_watch_state'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    course_key = Column(String(80), nullable=False, index=True)   # InteractiveCourse.key

    last_position = Column(Float, nullable=False, default=0.0)     # 上次播放位置(秒),续播用
    max_progress = Column(Float, nullable=False, default=0.0)      # 看过的最大进度百分比(0~1)
    completed = Column(Boolean, nullable=False, default=False)     # 是否看完(>=90%)
    completed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=_local_now, nullable=False)
    updated_at = Column(DateTime, default=_local_now, onupdate=_local_now, nullable=False)

    __table_args__ = (
        Index('ix_vws_user_course', 'user_id', 'course_key', unique=True),
    )

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'course_key': self.course_key,
            'last_position': self.last_position or 0.0,
            'max_progress': round(self.max_progress or 0.0, 3),
            'completed': bool(self.completed),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
