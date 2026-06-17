"""日报评论表

Revision ID: worklog_comments_20260617
Revises: workitem_comments_20260617
Create Date: 2026-06-17
"""
from alembic import op
import sqlalchemy as sa


revision = 'worklog_comments_20260617'
down_revision = 'workitem_comments_20260617'
branch_labels = None
depends_on = None


def _has_table(name):
    bind = op.get_bind()
    return name in sa.inspect(bind).get_table_names()


def upgrade():
    if _has_table('work_log_comments'):
        return
    op.create_table(
        'work_log_comments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('worklog_id', sa.Integer(), sa.ForeignKey('worklogs.id'), nullable=False, index=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.false()),
    )


def downgrade():
    if _has_table('work_log_comments'):
        op.drop_table('work_log_comments')
