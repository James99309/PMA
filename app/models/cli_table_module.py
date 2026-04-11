"""CLI 可查表归属注册

每张业务表必须在 cli_table_modules 登记一条记录,否则 CLI 禁止查询。
- mode='module': 独立归属某个权限模块 (module 字段生效)
- mode='follow': 跟随主表权限 (parent_table 字段生效, 递归解析到最终 module)

这张表是数据库驱动的 CLI 表级白名单,管理员只读查看,变更走 migration。
"""
import time

from app import db


class CliTableModule(db.Model):
    __tablename__ = 'cli_table_modules'

    MODE_MODULE = 'module'
    MODE_FOLLOW = 'follow'

    id = db.Column(db.Integer, primary_key=True)
    table_name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100))
    mode = db.Column(db.String(20), nullable=False)
    module = db.Column(db.String(50), nullable=True)
    parent_table = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(300))
    sort_order = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.Float, default=time.time)
    updated_at = db.Column(db.Float, default=time.time, onupdate=time.time)

    def to_dict(self):
        return {
            'id': self.id,
            'table_name': self.table_name,
            'display_name': self.display_name,
            'mode': self.mode,
            'module': self.module,
            'parent_table': self.parent_table,
            'description': self.description,
            'sort_order': self.sort_order,
            'is_active': self.is_active,
        }

    def __repr__(self):
        if self.mode == self.MODE_MODULE:
            return f'<CliTableModule {self.table_name} → {self.module}>'
        return f'<CliTableModule {self.table_name} follow {self.parent_table}>'
