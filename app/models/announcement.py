# -*- coding: utf-8 -*-
"""
公告模型 - 系统公告发布和管理

Announcement: 公告主表
AnnouncementRead: 公告阅读记录
AnnouncementAttachment: 公告附件
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON, Index

from app import db


def get_local_time():
    """获取本地时间（北京时区）"""
    return datetime.now(ZoneInfo('Asia/Shanghai')).replace(tzinfo=None)


def _website_preview_ready(link):
    """/website-preview/<lang>/ 的站点快照在不在本机。

    资产投放见 deploy/sync-website-preview.sh;目录与首页文件名以
    website_preview_routes._SITES 为准,不在这里重复定义。
    """
    import os
    from app.routes.website_preview_routes import _SITES, _APP_DIR
    parts = [p for p in link.split('/') if p]          # ['website-preview', 'cn', ...]
    lang = parts[1] if len(parts) > 1 else ''
    site = _SITES.get(lang)
    if not site:
        return False
    return os.path.isfile(os.path.join(_APP_DIR, site[0], site[1]))


class Announcement(db.Model):
    """公告模型"""
    __tablename__ = 'announcements'

    id = Column(Integer, primary_key=True)

    # 公告基本信息
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)

    # 公告类型: system(系统通知), business(业务公告), urgent(紧急通知)
    announcement_type = Column(String(20), nullable=False, default='system', index=True)

    # 发布范围数据（JSON格式存储用户ID列表）
    target_users = Column(JSON, default=list)

    # 发布状态: draft(草稿), published(已发布)
    status = Column(String(20), nullable=False, default='draft', index=True)

    # 定时发布时间（为空则立即发布）
    scheduled_time = Column(DateTime, nullable=True)

    # 实际发布时间
    published_at = Column(DateTime, nullable=True)

    # 创建者
    created_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    creator = db.relationship('User', backref='created_announcements')

    # ── 首页横幅 ──
    # 不另设"要不要上横幅"的开关:发布即上、撤回即下。曾经加过一个勾选框,
    # 结果两次都栽在同一件事上 —— 发了公告却不出现,因为没人记得去勾。
    # 代价是所有已发布公告都会滚,靠 BANNER_LIMIT 限条数 + 发布时间倒序自然淘汰。
    # 点击跳转地址。为空 = 纯告知(渲染成不可点的 div)。
    # 只存站内相对路径(如 /wiki/play/xxx)或 https:// 外链 —— 绝不存内网 IP 或
    # 公网域名:用户从内网/Tailscale/Cloudflare 进来的都有,写死地址会把人踢走,
    # 且 CN/SG 域名不同、IP 还会漂(见 .107→.124 那次)。校验在 views 层。
    banner_link = Column(String(500), nullable=True)

    # 系统字段
    created_at = Column(DateTime, default=get_local_time, index=True)
    updated_at = Column(DateTime, default=get_local_time, onupdate=get_local_time)
    is_deleted = Column(Boolean, default=False)

    # 关系
    attachments = db.relationship('AnnouncementAttachment', back_populates='announcement',
                                  cascade='all, delete-orphan')
    read_records = db.relationship('AnnouncementRead', back_populates='announcement',
                                   cascade='all, delete-orphan')

    __table_args__ = (
        Index('ix_announcements_status_published', 'status', 'published_at'),
    )

    # 首页横幅最多滚几条。没有已读淘汰,条目只会越攒越多,滚到第 8 条时没人会等。
    BANNER_LIMIT = 5

    @classmethod
    def banner_items(cls, user):
        """仪表盘顶部横幅要滚的条目(新→旧)。

        规则:已发布 + 未删 + (全员 / 该用户在目标名单里 / 该用户是发布人)。

        发布人无条件可见:发公告的人天然不会把自己勾进发布范围,结果就是
        永远看不到自己发的横幅、没法自查 —— 实测两次都栽在这里。
        指向 /website-preview/ 的条目额外体检一次本机资产 —— 官网快照每份 140M+
        不进 git、按区域单独投放(CN 只有中文站、SG 只有英文站),某台缺资产时
        点进去就是 404。这是目前唯一按机器投放的资产,故只此一条规则。
        """
        rows = cls.query.filter(
            cls.status == 'published',
            cls.is_deleted == False,          # noqa: E712
        ).order_by(cls.published_at.desc().nullslast(), cls.id.desc()).all()

        items = []
        for a in rows:
            targets = a.target_users or []
            if targets and user and user.id not in targets and a.created_by != user.id:
                continue
            if a.banner_link and a.banner_link.startswith('/website-preview/') \
                    and not _website_preview_ready(a.banner_link):
                continue
            # content 与 title 相同时不给详情(种子/短通知常把两者写成同一句,
            # 悬停展开看到重复的一行反而像 bug)
            detail = (a.content or '').strip()
            if detail == (a.title or '').strip():
                detail = ''
            items.append({'id': a.id, 'title': a.title,
                          'link': a.banner_link or '', 'content': detail})
            if len(items) >= cls.BANNER_LIMIT:
                break
        return items

    @property
    def is_readonly(self):
        """检查公告是否只读（已发布）"""
        return self.status == 'published'

    @property
    def read_count(self):
        """已读人数"""
        return sum(1 for r in self.read_records if r.is_read)

    @property
    def unread_count(self):
        """未读人数"""
        return sum(1 for r in self.read_records if not r.is_read)

    @property
    def target_user_count(self):
        """目标用户总数"""
        return len(self.read_records)

    @property
    def target_users_info(self):
        """获取目标用户详细信息"""
        if not self.target_users:
            return []
        from app.models.user import User
        users = User.query.filter(User.id.in_(self.target_users)).all()
        return [
            {
                'id': u.id,
                'name': u.real_name or u.username,
                'username': u.username
            }
            for u in users
        ]

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'announcement_type': self.announcement_type,
            'target_users': self.target_users,
            'target_users_info': self.target_users_info,
            'status': self.status,
            'banner_link': self.banner_link or '',
            'scheduled_time': self.scheduled_time.isoformat() if self.scheduled_time else None,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'created_by': self.created_by,
            'creator_name': self.creator.real_name or self.creator.username if self.creator else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_readonly': self.is_readonly,
            'read_count': self.read_count,
            'unread_count': self.unread_count,
            'target_user_count': self.target_user_count,
            'attachments': [a.to_dict() for a in self.attachments]
        }


class AnnouncementRead(db.Model):
    """公告阅读记录模型"""
    __tablename__ = 'announcement_reads'

    id = Column(Integer, primary_key=True)

    # 关联公告
    announcement_id = Column(Integer, ForeignKey('announcements.id'), nullable=False, index=True)
    announcement = db.relationship('Announcement', back_populates='read_records')

    # 目标用户
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    user = db.relationship('User', backref='announcement_reads')

    # 阅读状态
    is_read = Column(Boolean, default=False, index=True)
    read_at = Column(DateTime, nullable=True)

    # 创建时间（公告发布时创建记录）
    created_at = Column(DateTime, default=get_local_time)

    __table_args__ = (
        db.UniqueConstraint('announcement_id', 'user_id', name='uq_announcement_user'),
        Index('ix_announcement_reads_user_unread', 'user_id', 'is_read'),
    )

    @classmethod
    def mark_as_read(cls, announcement_id, user_id):
        """标记公告为已读"""
        record = cls.query.filter_by(
            announcement_id=announcement_id,
            user_id=user_id
        ).first()

        if record and not record.is_read:
            record.is_read = True
            record.read_at = get_local_time()
            return record
        return None

    @classmethod
    def get_unread_count(cls, user_id):
        """获取用户未读公告数量（仅计算已发布且未删除的公告）"""
        return cls.query.filter(
            cls.user_id == user_id,
            cls.is_read == False
        ).join(Announcement).filter(
            Announcement.status == 'published',
            Announcement.is_deleted == False
        ).count()


class AnnouncementAttachment(db.Model):
    """公告附件模型"""
    __tablename__ = 'announcement_attachments'

    id = Column(Integer, primary_key=True)

    # 关联公告
    announcement_id = Column(Integer, ForeignKey('announcements.id'), nullable=False, index=True)
    announcement = db.relationship('Announcement', back_populates='attachments')

    # 文件信息
    filename = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size = Column(Integer)
    file_type = Column(String(50))

    # 系统字段
    created_at = Column(DateTime, default=get_local_time)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'filename': self.filename,
            'file_url': self.file_url,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
