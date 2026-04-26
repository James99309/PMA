"""add_prospect_project_progress

Revision ID: cf15777f3e83
Revises: a9ef06d49c9d
Create Date: 2026-04-26 13:26:38.188815

为 prospect_projects 表新增 progress 列保存项目进展信息(AI 调研填充)
"""
from alembic import op
import sqlalchemy as sa


revision = 'cf15777f3e83'
down_revision = 'a9ef06d49c9d'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('prospect_projects', schema=None) as batch_op:
        batch_op.add_column(sa.Column('progress', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('prospect_projects', schema=None) as batch_op:
        batch_op.drop_column('progress')
