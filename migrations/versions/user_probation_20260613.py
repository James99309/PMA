"""试用期改为账户属性(2026-06-13)

users 增列 probation_start / probation_end(DATE):账户创建/编辑时设定试用期区间,
账户显示试用期徽章(试用期结束后自动消失);薪资页只读引用并高亮对应月份。
原 user_salary_profile 的试用期字段不再写入(保留兼容)。

幂等:ADD COLUMN IF NOT EXISTS。

Revision ID: user_probation_20260613
Revises: salary_monthly_20260613
Create Date: 2026-06-13
"""
from alembic import op

revision = 'user_probation_20260613'
down_revision = 'salary_monthly_20260613'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE users ADD COLUMN IF NOT EXISTS probation_start DATE;
        ALTER TABLE users ADD COLUMN IF NOT EXISTS probation_end DATE;
    """)


def downgrade():
    op.execute("""
        ALTER TABLE users DROP COLUMN IF EXISTS probation_start;
        ALTER TABLE users DROP COLUMN IF EXISTS probation_end;
    """)
