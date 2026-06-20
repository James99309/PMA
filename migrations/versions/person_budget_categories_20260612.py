"""expense_budgets 加动态细分科目列(与部门预算 category_budgets 同构)

Revision ID: person_budget_categories_20260612
Revises: dept_expense_budget_20260612
Create Date: 2026-06-12
"""
from alembic import op

revision = 'person_budget_categories_20260612'
down_revision = 'dept_expense_budget_20260612'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE expense_budgets ADD COLUMN IF NOT EXISTS category_budgets JSON")


def downgrade():
    op.execute("ALTER TABLE expense_budgets DROP COLUMN IF EXISTS category_budgets")
