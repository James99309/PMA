
"""add_customer_id_to_quotations

Revision ID: bccffbe037d7
Revises: 7ad5fc6d3bac
Create Date: 2025-10-18 23:43:41.090376

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bccffbe037d7'
down_revision = '7ad5fc6d3bac'
branch_labels = None
depends_on = None


def upgrade():
    # 检查列是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('quotations')]

    # 添加customer_id字段（可为空，因为旧数据需要先迁移）
    if 'customer_id' not in columns:
        op.add_column('quotations', sa.Column('customer_id', sa.Integer(), nullable=True))

    # 检查外键约束是否已存在
    existing_fks = [fk['name'] for fk in inspector.get_foreign_keys('quotations')]
    if 'fk_quotations_customer_id' not in existing_fks:
        op.create_foreign_key('fk_quotations_customer_id', 'quotations', 'companies', ['customer_id'], ['id'])


def downgrade():
    # 删除外键约束和字段
    op.drop_constraint('fk_quotations_customer_id', 'quotations', type_='foreignkey')
    op.drop_column('quotations', 'customer_id')