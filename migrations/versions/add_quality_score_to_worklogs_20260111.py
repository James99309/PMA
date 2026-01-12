"""添加日志质量评分字段到worklogs表

Revision ID: add_quality_score_to_worklogs_20260111
Revises: add_order_module_tables_20260110
Create Date: 2026-01-11

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_quality_score_to_worklogs_20260111'
down_revision = 'add_order_module_tables_20260110'
branch_labels = None
depends_on = None


def upgrade():
    # 添加质量评分字段
    op.add_column('worklogs', sa.Column('quality_score', sa.Integer(), nullable=True))
    op.add_column('worklogs', sa.Column('quality_issues', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('worklogs', 'quality_issues')
    op.drop_column('worklogs', 'quality_score')
