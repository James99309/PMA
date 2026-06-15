"""add period_budgets JSON to expense budgets (季/月度预算分摊)

费用预算支持按季/月分摊(与绩效目标同语义:留空=年度均摊)。
结构: {category: {"gran": "Q"|"M", "periods": {"1": 金额, ...}}}
消费方现按年度额度对比不变;季/月数据供配置展示与后续月度管控使用。
幂等 IF NOT EXISTS。

Revision ID: expense_budget_periods_20260611
Revises: role_target_weight_20260611
Create Date: 2026-06-11

"""
from alembic import op

revision = 'expense_budget_periods_20260611'
down_revision = 'role_target_weight_20260611'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE role_expense_budgets ADD COLUMN IF NOT EXISTS period_budgets JSON")
    op.execute("ALTER TABLE expense_budgets ADD COLUMN IF NOT EXISTS period_budgets JSON")


def downgrade():
    op.execute("ALTER TABLE role_expense_budgets DROP COLUMN IF EXISTS period_budgets")
    op.execute("ALTER TABLE expense_budgets DROP COLUMN IF EXISTS period_budgets")
