"""add role expense budget table

Revision ID: add_role_expense_budget_20251228
Revises:
Create Date: 2025-12-28

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_role_expense_budget_20251228'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """创建角色级别费用预算表"""
    op.create_table('role_expense_budgets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('role_code', sa.String(50), nullable=False),
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
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('role_code', 'year', name='uq_role_expense_budget')
    )

    # 创建索引提高查询性能
    op.create_index('ix_role_expense_budgets_role_code', 'role_expense_budgets', ['role_code'])
    op.create_index('ix_role_expense_budgets_year', 'role_expense_budgets', ['year'])


def downgrade():
    """删除角色级别费用预算表"""
    op.drop_index('ix_role_expense_budgets_year', table_name='role_expense_budgets')
    op.drop_index('ix_role_expense_budgets_role_code', table_name='role_expense_budgets')
    op.drop_table('role_expense_budgets')
