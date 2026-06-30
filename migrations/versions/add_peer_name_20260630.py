"""add users.peer_name (对端账号显示名快照, 跨实例 KPI 合并绑定展示用)

Revision ID: add_peer_name_20260630
Revises: add_peer_user_binding_20260630
Create Date: 2026-06-30

幂等:ADD COLUMN IF NOT EXISTS,可重复执行。
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'add_peer_name_20260630'
down_revision = 'add_peer_user_binding_20260630'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS peer_name VARCHAR(80)")


def downgrade():
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS peer_name")
