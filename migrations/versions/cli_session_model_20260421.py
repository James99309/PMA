"""add model column to cli_sessions

Revision ID: cli_session_model_20260421
Revises: xlsx_skill_system_20260420
Create Date: 2026-04-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'cli_session_model_20260421'
down_revision = 'quotation_excel_tool_skill_20260420'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('cli_sessions', sa.Column('model', sa.String(100), nullable=True))


def downgrade():
    op.drop_column('cli_sessions', 'model')
