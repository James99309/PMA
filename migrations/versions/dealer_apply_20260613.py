"""客户渠道身份(代理商/分销商)审批:pending_company_type 暂存列

新建/编辑客户选择 dealer/distributor 时不直接生效,暂存 pending_company_type
并发起审批(商务助理→渠道经理→总经理,缺位跳级);通过后写入 company_type。

Revision ID: dealer_apply_20260613
Revises: hold_step_rename_20260612
Create Date: 2026-06-13
"""
from alembic import op

revision = 'dealer_apply_20260613'
down_revision = 'hold_step_rename_20260612'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE companies ADD COLUMN IF NOT EXISTS pending_company_type VARCHAR(20)")


def downgrade():
    op.execute("ALTER TABLE companies DROP COLUMN IF EXISTS pending_company_type")
