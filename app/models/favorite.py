# -*- coding: utf-8 -*-
"""个人关注(收藏)——通用对象书签。

设计要点:
  - 纯个人维度:只认 user_id,别人看不到、也不影响任何权限判定。
  - 通用表:object_type 先用 'project',客户/报价单等以后直接复用,不再建表。
  - 不做外键到业务表(object_id 是多态列);业务对象被删/移出权限范围时,
    读取侧一律走 get_viewable_data 过滤,孤儿行不显示也无害。
"""
from datetime import datetime

from app import db


class UserFavorite(db.Model):
    __tablename__ = 'user_favorites'
    __table_args__ = (
        db.UniqueConstraint('user_id', 'object_type', 'object_id',
                            name='uq_user_favorite_object'),
        db.Index('ix_user_favorites_user_type', 'user_id', 'object_type'),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
                        nullable=False)
    object_type = db.Column(db.String(32), nullable=False)   # 'project' | 未来: 'customer'/'quotation'
    object_id = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now, nullable=False)

    def __repr__(self):
        return f'<UserFavorite u{self.user_id} {self.object_type}#{self.object_id}>'
