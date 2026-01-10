
"""merge heads 20260110

Revision ID: d2731c6921bb
Revises: add_allow_attachment_field, add_display_order_to_config, add_user_settlement_currency_20260108, add_worklog_comments_20260110, merge_heads_20260105
Create Date: 2026-01-10 18:51:23.563014

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd2731c6921bb'
down_revision = ('add_allow_attachment_field', 'add_display_order_to_config', 'add_user_settlement_currency_20260108', 'add_worklog_comments_20260110', 'merge_heads_20260105')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass