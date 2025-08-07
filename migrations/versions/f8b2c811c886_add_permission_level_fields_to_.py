
"""add permission level fields to permissions table

Revision ID: f8b2c811c886
Revises: remove_share_related_projects
Create Date: 2025-08-07 14:07:15.708255

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f8b2c811c886'
down_revision = 'remove_share_related_projects'
branch_labels = None
depends_on = None


def upgrade():
    # 为permissions表添加权限级别相关字段
    op.add_column('permissions', sa.Column('permission_level', sa.String(20), server_default='personal', nullable=False))
    op.add_column('permissions', sa.Column('permission_level_description', sa.Text(), nullable=True))
    op.add_column('permissions', sa.Column('pricing_discount_limit', sa.Float(), nullable=True))
    op.add_column('permissions', sa.Column('settlement_discount_limit', sa.Float(), nullable=True))


def downgrade():
    # 移除添加的字段
    op.drop_column('permissions', 'settlement_discount_limit')
    op.drop_column('permissions', 'pricing_discount_limit')
    op.drop_column('permissions', 'permission_level_description')
    op.drop_column('permissions', 'permission_level')