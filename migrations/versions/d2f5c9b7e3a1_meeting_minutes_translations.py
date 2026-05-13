"""add translations multilingual dict to meeting_minutes

Revision ID: d2f5c9b7e3a1
Revises: c1e4b8d9a2f6
Create Date: 2026-05-12 18:30:00

多语言纪要支持：被邀请人母语和发起人不同 → 按需翻译并缓存到此字段，
避免每次打开重新调用 Claude。

结构：{lang_code: {summary, key_points, key_quotes, chapters, highlights, decisions}}
"""
from alembic import op
import sqlalchemy as sa


revision = 'd2f5c9b7e3a1'
down_revision = 'c1e4b8d9a2f6'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('meeting_minutes', sa.Column('translations', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('meeting_minutes', 'translations')
