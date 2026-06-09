"""add Product.has_serial_number column

Revision ID: a7d5b1c3e2f4
Revises: ecc58026c4eb
Create Date: 2026-05-21 09:00:00.000000

新增字段 products.has_serial_number(default True):
- True (默认):该产品按 SN 管理,发货时需要填序列号
- False:无 SN 的产品(如耦合器、功分器、线缆),发货时跳过 SN 输入

所有现有产品默认 True(与之前行为一致),小附件类产品可在产品维护页改为 False。
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a7d5b1c3e2f4'
down_revision = 'ecc58026c4eb'
branch_labels = None
depends_on = None


def upgrade():
    # 幂等:该列可能已由 cherry-pick 直接加到生产(未走迁移),存在则跳过
    insp = sa.inspect(op.get_bind())
    if 'has_serial_number' not in [c['name'] for c in insp.get_columns('products')]:
        op.add_column(
            'products',
            sa.Column('has_serial_number', sa.Boolean(), nullable=False, server_default=sa.text('true'))
        )


def downgrade():
    op.drop_column('products', 'has_serial_number')
