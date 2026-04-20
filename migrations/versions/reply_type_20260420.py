"""add reply_type to task_replies

Revision ID: reply_type_20260420
Revises: 3e191bbada67
Create Date: 2026-04-20

"""
from alembic import op
import sqlalchemy as sa

revision = 'reply_type_20260420'
down_revision = '3e191bbada67'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('task_replies',
        sa.Column('reply_type', sa.String(20), nullable=False,
                  server_default='comment')
    )


def downgrade():
    op.drop_column('task_replies', 'reply_type')
