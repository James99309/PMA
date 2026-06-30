"""跨实例双真实账号绑定:users 加 peer_user_id / peer_system(KPI 合并用)

Revision ID: add_peer_user_binding_20260630
Revises: qd_reconfirm_change_20260626
Create Date: 2026-06-30

幂等(ADD COLUMN IF NOT EXISTS)——防 cherry-pick 重复加列致 DuplicateColumn。
"""
from alembic import op

# revision identifiers, used by Alembic.
revision = 'add_peer_user_binding_20260630'
down_revision = 'qd_reconfirm_change_20260626'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS peer_user_id INTEGER")
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS peer_system VARCHAR(20)")


def downgrade():
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS peer_system")
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS peer_user_id")
