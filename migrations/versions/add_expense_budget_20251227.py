"""add expense budget table

Revision ID: add_expense_budget_20251227
Revises:
Create Date: 2025-12-27

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_expense_budget_20251227'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """创建报销预算表"""
    op.create_table('expense_budgets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('total_budget', sa.Numeric(precision=15, scale=2), server_default='0', nullable=True),
        sa.Column('entertainment_budget', sa.Numeric(precision=15, scale=2), server_default='0', nullable=True, comment='招待费预算'),
        sa.Column('travel_budget', sa.Numeric(precision=15, scale=2), server_default='0', nullable=True, comment='差旅费预算'),
        sa.Column('transport_budget', sa.Numeric(precision=15, scale=2), server_default='0', nullable=True, comment='交通费预算'),
        sa.Column('office_budget', sa.Numeric(precision=15, scale=2), server_default='0', nullable=True, comment='办公费预算'),
        sa.Column('communication_budget', sa.Numeric(precision=15, scale=2), server_default='0', nullable=True, comment='通讯费预算'),
        sa.Column('other_budget', sa.Numeric(precision=15, scale=2), server_default='0', nullable=True, comment='其他费用预算'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('updated_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['updated_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'year', name='uq_expense_budget_user_year')
    )

    # 创建索引提高查询性能
    op.create_index('ix_expense_budgets_user_id', 'expense_budgets', ['user_id'])
    op.create_index('ix_expense_budgets_year', 'expense_budgets', ['year'])


def downgrade():
    """删除报销预算表"""
    op.drop_index('ix_expense_budgets_year', table_name='expense_budgets')
    op.drop_index('ix_expense_budgets_user_id', table_name='expense_budgets')
    op.drop_table('expense_budgets')
