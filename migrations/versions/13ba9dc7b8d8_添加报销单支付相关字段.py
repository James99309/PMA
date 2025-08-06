
"""添加报销单支付相关字段

Revision ID: 13ba9dc7b8d8
Revises: 10477a187e6e
Create Date: 2025-08-05 13:55:54.965094

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '13ba9dc7b8d8'
down_revision = '10477a187e6e'
branch_labels = None
depends_on = None


def upgrade():
    # 添加支付相关字段到报销单表
    with op.batch_alter_table('expenses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('payment_status', sa.String(length=20), nullable=False, server_default='unpaid'))
        batch_op.add_column(sa.Column('payment_amount', sa.Float(), nullable=True))
        batch_op.add_column(sa.Column('payment_date', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('payment_method', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('payment_reference', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('payment_notes', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('paid_by', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('fk_expenses_paid_by', 'users', ['paid_by'], ['id'])


def downgrade():
    # 移除支付相关字段
    with op.batch_alter_table('expenses', schema=None) as batch_op:
        batch_op.drop_constraint('fk_expenses_paid_by', type_='foreignkey')
        batch_op.drop_column('paid_by')
        batch_op.drop_column('payment_notes')
        batch_op.drop_column('payment_reference')
        batch_op.drop_column('payment_method')
        batch_op.drop_column('payment_date')
        batch_op.drop_column('payment_amount')
        batch_op.drop_column('payment_status')