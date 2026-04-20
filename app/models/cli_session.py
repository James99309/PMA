# -*- coding: utf-8 -*-
"""
CliSession 模型

一个 CliSession 对应 CLI 智能终端里的一个标签会话。
设计详见 docs/plans/2026-04-05-pma-cli-agent-design.md 第 4.1 节。
"""
import uuid
from datetime import datetime

from sqlalchemy.dialects.postgresql import JSONB, UUID

from app import db


class CliSession(db.Model):
    """CLI 智能终端的单个会话"""

    __tablename__ = 'cli_sessions'

    STATUS_ACTIVE = 'ACTIVE'
    STATUS_CLOSED = 'CLOSED'
    STATUS_ARCHIVED = 'ARCHIVED'

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    title = db.Column(db.String(120), nullable=True)
    status = db.Column(db.String(16), nullable=False, default=STATUS_ACTIVE, index=True)

    # ContentBlock 数组,每条消息形如
    # {"role": "user"|"assistant", "content": [{"type": "text", "text": "..."}, ...]}
    messages = db.Column(JSONB, nullable=False, default=list)

    # 累计 usage: {"input_tokens": N, "output_tokens": N, "cache_read_input_tokens": N, "cache_creation_input_tokens": N}
    usage_total = db.Column(JSONB, nullable=False, default=dict)

    # 最近使用的 LLM 模型名称（如 claude-3-5-sonnet-latest）
    model = db.Column(db.String(100), nullable=True)

    # 压缩元数据: {"count": N, "last_summary": "..."}
    compaction_meta = db.Column(JSONB, nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_active_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f'<CliSession {str(self.id)[:8]} user={self.user_id} status={self.status} msgs={len(self.messages or [])}>'

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': self.user_id,
            'title': self.title,
            'status': self.status,
            'model': self.model,
            'message_count': len(self.messages or []),
            'usage_total': self.usage_total or {},
            'compaction_count': (self.compaction_meta or {}).get('count', 0),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_active_at': self.last_active_at.isoformat() if self.last_active_at else None,
        }

    def append_message(self, role: str, blocks: list):
        """追加一条消息。调用方负责 commit。"""
        msgs = list(self.messages or [])
        msgs.append({'role': role, 'content': blocks})
        self.messages = msgs
        self.last_active_at = datetime.utcnow()

    def accumulate_usage(self, usage: dict):
        """累加一次 LLM 调用的 usage。"""
        total = dict(self.usage_total or {})
        for key in ('input_tokens', 'output_tokens',
                    'cache_creation_input_tokens', 'cache_read_input_tokens'):
            if key in usage:
                total[key] = total.get(key, 0) + (usage[key] or 0)
        self.usage_total = total

    def estimated_context_tokens(self) -> int:
        """当前消息历史占用的 token 数的粗估(用于压缩判断)。

        用"汉字数 * 1.5 + 其他字符数 / 4"的中文优化估算。
        """
        import re
        total = 0
        for msg in (self.messages or []):
            content = msg.get('content', [])
            if isinstance(content, str):
                texts = [content]
            else:
                texts = []
                for block in content:
                    if block.get('type') == 'text':
                        texts.append(block.get('text', ''))
                    elif block.get('type') == 'tool_use':
                        texts.append(str(block.get('input', '')))
                    elif block.get('type') == 'tool_result':
                        c = block.get('content', '')
                        texts.append(c if isinstance(c, str) else str(c))
            for text in texts:
                chinese = len(re.findall(r'[\u4e00-\u9fff]', text))
                other = len(text) - chinese
                total += int(chinese * 1.5 + other / 4)
        return total
