# -*- coding: utf-8 -*-
"""
CliMemory 模型

CLI Agent 的记忆系统。三级 scope：
  - system:   管理员通过 /memory system add 创建，所有用户可见
  - role:xx:  管理员通过 /memory role xx add 创建，指定角色可见
  - personal: AI 对话中自动积累或 /memory add，仅创建者可见

每条记忆有 title（索引用，每次加载）和 content（详情，按需读取）。
"""
from datetime import datetime

from sqlalchemy.dialects.postgresql import JSONB

from app import db


class CliMemory(db.Model):
    """CLI Agent 记忆条目"""

    __tablename__ = 'cli_memories'

    SCOPE_SYSTEM = 'system'
    SCOPE_PERSONAL = 'personal'
    # role scope 格式: 'role:hr_manager', 'role:sales_manager' 等

    id = db.Column(db.Integer, primary_key=True)

    # 作用域: system / role:xxx / personal
    scope = db.Column(db.String(50), nullable=False, default=SCOPE_PERSONAL, index=True)

    # personal scope 时的所有者
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)

    # 记忆类型: rule(规则) / knowledge(知识) / preference(偏好) / feedback(反馈)
    type = db.Column(db.String(20), nullable=False, default='knowledge')

    # 索引层：每次对话都加载（短，<100字）
    title = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.String(500), nullable=False)

    # 详情层：recall_memory 时才读取
    content = db.Column(db.Text, nullable=False)

    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<CliMemory #{self.id} [{self.scope}] {self.title[:30]}>'

    def to_dict(self):
        return {
            'id': self.id,
            'scope': self.scope,
            'user_id': self.user_id,
            'type': self.type,
            'title': self.title,
            'summary': self.summary,
            'content': self.content,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

    def to_index_line(self) -> str:
        """返回索引行，用于注入 prompt（不含 content）"""
        scope_label = self.scope
        if self.scope == 'system':
            scope_label = '系统'
        elif self.scope == 'personal':
            scope_label = '个人'
        elif self.scope.startswith('role:'):
            scope_label = f'角色({self.scope[5:]})'
        return f"- #{self.id} [{scope_label}] {self.title} — {self.summary}"
