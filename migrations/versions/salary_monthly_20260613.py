"""个人薪资改为月度实发(2026-06-13)

user_salary_items 增列 monthly_amounts(JSON {"1":x,...,"12":y}),
HR 按月回填各薪资项实发金额;原 amount/probation_amount 列保留兼容不再使用。

幂等:ADD COLUMN IF NOT EXISTS。

Revision ID: salary_monthly_20260613
Revises: salary_probation_dates_20260613
Create Date: 2026-06-13
"""
from alembic import op

revision = 'salary_monthly_20260613'
down_revision = 'salary_probation_dates_20260613'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE user_salary_items ADD COLUMN IF NOT EXISTS monthly_amounts JSON;
    """)


def downgrade():
    op.execute("""
        ALTER TABLE user_salary_items DROP COLUMN IF EXISTS monthly_amounts;
    """)
