
"""add_source_field_to_company

Revision ID: c9a7b9ea3a42
Revises: 8cceb1f66801
Create Date: 2025-10-18 08:40:07.484957

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c9a7b9ea3a42'
down_revision = '8cceb1f66801'
branch_labels = None
depends_on = None


def upgrade():
    # 添加source字段到companies表
    op.add_column('companies', sa.Column('source', sa.String(length=20), nullable=True))


def downgrade():
    # 回滚：删除source字段
    op.drop_column('companies', 'source')