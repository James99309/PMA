"""项目成功锁定(锁单预判)字段

Revision ID: project_win_lock_20260612
Revises: person_budget_categories_20260612
Create Date: 2026-06-12
"""
from alembic import op

revision = 'project_win_lock_20260612'
down_revision = 'person_budget_categories_20260612'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS win_locked BOOLEAN NOT NULL DEFAULT FALSE")
    op.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS win_lock_reason TEXT")
    op.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS win_locked_by INTEGER REFERENCES users(id)")
    op.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS win_locked_at TIMESTAMP")


def downgrade():
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS win_locked_at")
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS win_locked_by")
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS win_lock_reason")
    op.execute("ALTER TABLE projects DROP COLUMN IF EXISTS win_locked")
