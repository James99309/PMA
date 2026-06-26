"""报价明细加 is_reconfirm_change(再确认变更高亮标记, 2026-06-26)

- quotation_details 加布尔列 is_reconfirm_change(默认 false)
- 用途:已确认报价单被改动后,自上次确认以来"新增/替换(MN变化)"的行打标,
  reconfirm 期间在明细表加深底色;重新确认时清除。

幂等:列用 IF NOT EXISTS。

Revision ID: qd_reconfirm_change_20260626
Revises: user_hr_docs_20260623
Create Date: 2026-06-26
"""
from alembic import op

revision = 'qd_reconfirm_change_20260626'
down_revision = 'user_hr_docs_20260623'
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import text
    conn = op.get_bind()
    conn.execute(text(
        "ALTER TABLE quotation_details "
        "ADD COLUMN IF NOT EXISTS is_reconfirm_change BOOLEAN DEFAULT FALSE"
    ))


def downgrade():
    from sqlalchemy import text
    conn = op.get_bind()
    conn.execute(text(
        "ALTER TABLE quotation_details DROP COLUMN IF EXISTS is_reconfirm_change"
    ))
