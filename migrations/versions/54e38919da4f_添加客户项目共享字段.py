
"""添加客户项目共享字段

Revision ID: 54e38919da4f
Revises: 518ff52d32d0
Create Date: 2025-08-01 02:13:46.665998

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '54e38919da4f'
down_revision = '518ff52d32d0'
branch_labels = None
depends_on = None


def upgrade():
    # 为companies表添加share_related_projects字段，默认值为True
    op.add_column('companies', sa.Column('share_related_projects', sa.Boolean(), nullable=True, default=True))
    
    # 为现有记录设置默认值
    op.execute("UPDATE companies SET share_related_projects = true WHERE share_related_projects IS NULL")
    
    # 设置字段为非空
    op.alter_column('companies', 'share_related_projects', nullable=False)


def downgrade():
    # 删除share_related_projects字段
    op.drop_column('companies', 'share_related_projects')