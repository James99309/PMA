"""项目失败责任认定评语字段(CEO 补录,不依赖审批实例)

Revision ID: fail_attribution_note_20260616
Revises: se_implant_quality_20260614
Create Date: 2026-06-16
"""
from alembic import op
import sqlalchemy as sa


revision = 'fail_attribution_note_20260616'
down_revision = 'se_implant_quality_20260614'
branch_labels = None
depends_on = None


def _has_column(table, column):
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return column in [c['name'] for c in insp.get_columns(table)]


def upgrade():
    # 幂等:cherry-pick/重复执行时跳过已存在列
    if not _has_column('projects', 'fail_attribution_note'):
        op.add_column('projects', sa.Column('fail_attribution_note', sa.Text(), nullable=True))
    if not _has_column('projects', 'fail_attribution_by'):
        op.add_column('projects', sa.Column('fail_attribution_by', sa.Integer(), nullable=True))
    if not _has_column('projects', 'fail_attribution_at'):
        op.add_column('projects', sa.Column('fail_attribution_at', sa.DateTime(), nullable=True))


def downgrade():
    for col in ('fail_attribution_at', 'fail_attribution_by', 'fail_attribution_note'):
        if _has_column('projects', col):
            op.drop_column('projects', col)
