"""成功锁定关联报价单 + 金额快照

Revision ID: win_lock_quotation_20260612
Revises: project_win_lock_20260612
Create Date: 2026-06-12
"""
from alembic import op

revision = 'win_lock_quotation_20260612'
down_revision = 'project_win_lock_20260612'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS win_locked_quotation_id INTEGER REFERENCES quotations(id)")
    op.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS win_locked_amount DOUBLE PRECISION")


def downgrade():
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS win_locked_amount")
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS win_locked_quotation_id")
