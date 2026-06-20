"""部门级费用预算表(总额 + 动态细分科目,科目键来自报销 EXPENSE_CATEGORIES)

Revision ID: dept_expense_budget_20260612
Revises: expense_budget_periods_20260611
Create Date: 2026-06-12
"""
from alembic import op

revision = 'dept_expense_budget_20260612'
down_revision = 'expense_budget_periods_20260611'
branch_labels = None
depends_on = None


def upgrade():
    # 幂等:IF NOT EXISTS,可在任意环境重复执行
    op.execute("""
        CREATE TABLE IF NOT EXISTS department_expense_budgets (
            id SERIAL PRIMARY KEY,
            department_id INTEGER NOT NULL REFERENCES departments(id),
            year INTEGER NOT NULL,
            total_budget NUMERIC(15, 2) DEFAULT 0,
            category_budgets JSON,
            period_budgets JSON,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            created_by INTEGER REFERENCES users(id),
            updated_by INTEGER REFERENCES users(id),
            CONSTRAINT uq_department_expense_budget UNIQUE (department_id, year)
        )
    """)


def downgrade():
    op.execute("DROP TABLE IF EXISTS department_expense_budgets")
