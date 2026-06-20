"""试用期改用开始/结束日期(2026-06-13)

user_salary_profile 增列 probation_start / probation_end(DATE),
替代原 probation_months(列保留不用)。

幂等:ADD COLUMN IF NOT EXISTS。

Revision ID: salary_probation_dates_20260613
Revises: salary_global_structure_20260613
Create Date: 2026-06-13
"""
from alembic import op

revision = 'salary_probation_dates_20260613'
down_revision = 'salary_global_structure_20260613'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE user_salary_profile ADD COLUMN IF NOT EXISTS probation_start DATE;
        ALTER TABLE user_salary_profile ADD COLUMN IF NOT EXISTS probation_end DATE;
    """)


def downgrade():
    op.execute("""
        ALTER TABLE user_salary_profile DROP COLUMN IF EXISTS probation_start;
        ALTER TABLE user_salary_profile DROP COLUMN IF EXISTS probation_end;
    """)
