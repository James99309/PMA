
"""允许报销单不关联客户和联系人

Revision ID: e75c868b86a3
Revises: f8b2c811c886
Create Date: 2025-08-08 21:14:30.700725

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e75c868b86a3'
down_revision = 'f8b2c811c886'
branch_labels = None
depends_on = None


def upgrade():
    # 允许报销单的customer_id和contact_id字段为空，以支持不关联客户模式
    op.alter_column('expenses', 'customer_id', nullable=True)
    op.alter_column('expenses', 'contact_id', nullable=True)


def downgrade():
    # 回滚：要求customer_id和contact_id字段不为空
    op.alter_column('expenses', 'customer_id', nullable=False)
    op.alter_column('expenses', 'contact_id', nullable=False)