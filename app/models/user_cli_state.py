# -*- coding: utf-8 -*-
"""
UserCliState 模型

每个用户一行,记录 CLI 终端的标签栏快照:打开了哪些 session、当前聚焦哪个。
用户切到 PMA 其他菜单再切回来时,根据这张表还原终端状态。

设计详见 docs/plans/2026-04-05-pma-cli-agent-design.md 第 4.1 节。
"""
from datetime import datetime

from sqlalchemy.dialects.postgresql import JSONB, UUID

from app import db


class UserCliState(db.Model):
    """每用户一行的 CLI 标签栏状态"""

    __tablename__ = 'user_cli_state'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)

    # 活跃 session ID 的有序数组(标签栏里从左到右)
    active_session_ids = db.Column(JSONB, nullable=False, default=list)

    # 当前聚焦的 session ID(UUID 字符串形式)
    current_session_id = db.Column(db.String(36), nullable=True)

    # UI 偏好 {font_size, theme, shortcuts_enabled, ...}
    ui_preferences = db.Column(JSONB, nullable=False, default=dict)

    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<UserCliState user={self.user_id} tabs={len(self.active_session_ids or [])}>'

    @classmethod
    def get_or_create(cls, user_id: int) -> 'UserCliState':
        """获取或创建用户的 CLI 状态。调用方负责 commit。"""
        state = cls.query.get(user_id)
        if state is None:
            state = cls(user_id=user_id, active_session_ids=[], ui_preferences={})
            db.session.add(state)
            db.session.flush()
        return state
