
"""添加报销模块缺失的货币相关字段

Revision ID: 10477a187e6e
Revises: afb642ad7071
Create Date: 2025-08-03 23:14:16.064584

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '10477a187e6e'
down_revision = 'afb642ad7071'
branch_labels = None
depends_on = None


def upgrade():
    # 为expenses表添加currency字段
    with op.batch_alter_table('expenses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('currency', sa.VARCHAR(length=10), nullable=True, server_default='CNY'))
    
    # 为expense_details表添加货币相关字段
    with op.batch_alter_table('expense_details', schema=None) as batch_op:
        batch_op.add_column(sa.Column('currency', sa.VARCHAR(length=10), nullable=True, server_default='CNY'))
        batch_op.add_column(sa.Column('invoice_amount', sa.NUMERIC(precision=15, scale=2), nullable=True, server_default='0.00'))
        batch_op.add_column(sa.Column('current_amount', sa.NUMERIC(precision=15, scale=2), nullable=True, server_default='0.00'))
        batch_op.add_column(sa.Column('exchange_rate', sa.NUMERIC(precision=10, scale=4), nullable=True, server_default='1.0000'))
    
    # 数据迁移：将现有的amount值复制到新字段
    connection = op.get_bind()
    connection.execute(sa.text("""
        UPDATE expense_details 
        SET invoice_amount = amount, 
            current_amount = amount 
        WHERE invoice_amount IS NULL OR current_amount IS NULL
    """))
    
    # 创建索引
    op.create_index('idx_expenses_currency', 'expenses', ['currency'])
    op.create_index('idx_expense_details_currency', 'expense_details', ['currency'])
    op.create_index('idx_expense_details_expense_currency', 'expense_details', ['expense_id', 'currency'])


def downgrade():
    # 删除索引
    op.drop_index('idx_expense_details_expense_currency', 'expense_details')
    op.drop_index('idx_expense_details_currency', 'expense_details')
    op.drop_index('idx_expenses_currency', 'expenses')
    
    # 删除expense_details表的新字段
    with op.batch_alter_table('expense_details', schema=None) as batch_op:
        batch_op.drop_column('exchange_rate')
        batch_op.drop_column('current_amount')
        batch_op.drop_column('invoice_amount')
        batch_op.drop_column('currency')
    
    # 删除expenses表的currency字段
    with op.batch_alter_table('expenses', schema=None) as batch_op:
        batch_op.drop_column('currency')