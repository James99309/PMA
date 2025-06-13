"""添加结算目标公司和结算状态字段

Revision ID: 0432e8af4418
Revises: 320d95e5b295
Create Date: 2025-06-12 12:11:59.535121

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0432e8af4418'
down_revision = '320d95e5b295'
branch_labels = None
depends_on = None


def upgrade():
    # 添加结算目标公司字段到 settlement_order_details 表
    with op.batch_alter_table('settlement_order_details', schema=None) as batch_op:
        batch_op.add_column(sa.Column('settlement_company_id', sa.Integer(), nullable=True, comment='结算目标公司ID'))
        batch_op.add_column(sa.Column('settlement_status', sa.String(length=20), nullable=True, default='pending', comment='结算状态: pending, completed'))
        batch_op.add_column(sa.Column('settlement_date', sa.DateTime(), nullable=True, comment='结算完成时间'))
        batch_op.add_column(sa.Column('settlement_notes', sa.Text(), nullable=True, comment='结算备注'))
        
        # 添加外键约束
        batch_op.create_foreign_key('fk_settlement_order_details_settlement_company', 'companies', ['settlement_company_id'], ['id'])


def downgrade():
    # 移除添加的字段
    with op.batch_alter_table('settlement_order_details', schema=None) as batch_op:
        batch_op.drop_constraint('fk_settlement_order_details_settlement_company', type_='foreignkey')
        batch_op.drop_column('settlement_notes')
        batch_op.drop_column('settlement_date')
        batch_op.drop_column('settlement_status')
        batch_op.drop_column('settlement_company_id')