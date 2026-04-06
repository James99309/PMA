# -*- coding: utf-8 -*-
"""
CliSkill 模型

CLI Agent 的「技能」注册表。每条记录定义一个可被 Agent 调用的技能,
包括参数声明、SQL 查询列表和输出模板。

设计详见 docs/plans/2026-04-05-pma-cli-agent-design.md 技能系统章节。
"""
from datetime import datetime

from sqlalchemy.dialects.postgresql import JSONB

from app import db


class CliSkill(db.Model):
    """CLI Agent 可调用的技能定义"""

    __tablename__ = 'cli_skills'

    SCOPE_GLOBAL = 'global'
    SCOPE_TEAM = 'team'
    SCOPE_PERSONAL = 'personal'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=False)

    # 参数声明: [{name, type, required, default_value, description}, ...]
    parameters = db.Column(JSONB, nullable=False, default=list)

    # SQL 查询列表: [{sql, as_name, description}, ...]
    queries = db.Column(JSONB, nullable=False)

    # 输出格式模板(Markdown),使用 {step_name.field} 占位符
    output_format = db.Column(db.Text, nullable=True)

    # 作用域: global / team / personal
    scope = db.Column(db.String(20), nullable=False, default=SCOPE_GLOBAL)

    is_active = db.Column(db.Boolean, nullable=False, default=True)

    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<CliSkill {self.name} scope={self.scope} active={self.is_active}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'title': self.title,
            'description': self.description,
            'parameters': self.parameters or [],
            'queries': self.queries or [],
            'output_format': self.output_format,
            'scope': self.scope,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    def to_prompt_description(self) -> str:
        """返回一行摘要,用于拼入 Agent 的 system prompt。

        格式: skill_name — 标题（参数: a, b）
        注意: skill_name 不带括号，invoke_skill 的 skill_name 参数只传这个名字。
        """
        params = self.parameters or []
        param_info = ''
        if params:
            parts = []
            for p in params:
                name = p.get('name', '?')
                req = '必填' if p.get('required') else '可选'
                parts.append(f'{name}[{req}]')
            param_info = f'（参数: {", ".join(parts)}）'
        return f"{self.name} — {self.title}{param_info}"
