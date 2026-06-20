"""薪资试用期(2026-06-13,个人级):试用期开关 + 周期 + 逐项试用期金额

试用期完全是个人配置层面的事,岗位薪资结构(role_salary_items)不涉及:
- user_salary_items 增列 probation_amount(单期试用期金额;留空=与标准相同)
- 新表 user_salary_profile:个人试用期开关(is_probation)+ 周期(probation_months),按年存

幂等:ADD COLUMN IF NOT EXISTS / CREATE TABLE IF NOT EXISTS。

Revision ID: salary_probation_20260613
Revises: salary_structure_20260613
Create Date: 2026-06-13
"""
from alembic import op

revision = 'salary_probation_20260613'
down_revision = 'salary_structure_20260613'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE user_salary_items ADD COLUMN IF NOT EXISTS probation_amount NUMERIC(15,2);

        CREATE TABLE IF NOT EXISTS user_salary_profile (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            year INTEGER NOT NULL,
            is_probation BOOLEAN DEFAULT FALSE,
            probation_months INTEGER,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW(),
            created_by INTEGER REFERENCES users(id),
            updated_by INTEGER REFERENCES users(id),
            CONSTRAINT uq_user_salary_profile UNIQUE (user_id, year)
        );
    """)


def downgrade():
    op.execute("""
        DROP TABLE IF EXISTS user_salary_profile;
        ALTER TABLE user_salary_items DROP COLUMN IF EXISTS probation_amount;
    """)
