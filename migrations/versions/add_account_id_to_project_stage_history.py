"""add account_id to project_stage_history

Revision ID: account_id_for_stats
Revises: 07bd9afe4c03
Create Date: 2025-05-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'account_id_for_stats'
down_revision = '07bd9afe4c03'
branch_labels = None
depends_on = None


def upgrade():
    # 添加account_id字段
    op.add_column('project_stage_history', 
                  sa.Column('account_id', sa.Integer(), nullable=True))
    
    # 创建索引，提高查询性能
    op.create_index('ix_project_stage_history_account_id', 
                   'project_stage_history', ['account_id'], unique=False)


def downgrade():
    # 删除索引
    op.drop_index('ix_project_stage_history_account_id', 
                  table_name='project_stage_history')
    
    # 删除字段
    op.drop_column('project_stage_history', 'account_id') 