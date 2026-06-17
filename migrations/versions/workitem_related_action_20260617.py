"""工作项关联跟进记录(Action)字段

Revision ID: workitem_related_action_20260617
Revises: worklog_comments_20260617
Create Date: 2026-06-17
"""
from alembic import op
import sqlalchemy as sa


revision = 'workitem_related_action_20260617'
down_revision = 'worklog_comments_20260617'
branch_labels = None
depends_on = None


def _has_column(table, col):
    bind = op.get_bind()
    return col in [c['name'] for c in sa.inspect(bind).get_columns(table)]


def upgrade():
    if not _has_column('work_items', 'related_action_id'):
        op.add_column('work_items', sa.Column('related_action_id', sa.Integer(),
                                              sa.ForeignKey('actions.id'), nullable=True))


def downgrade():
    pass
