"""add qualified_at to companies/projects (合格新增「达标时间」,冻结历史归属)

Revision ID: qualified_at_20260621
Revises: workitem_related_action_20260617
Create Date: 2026-06-21

合格新客户/项目按"达标月"归属(首次满足合格口径的时刻),一旦写入永不重算,
避免事后补资料改变过去月份的新增统计。数据回填由 kpi_actual_service 盖戳任务完成,
本迁移仅加列与索引(幂等)。
"""
from alembic import op
import sqlalchemy as sa


revision = 'qualified_at_20260621'
down_revision = 'workitem_related_action_20260617'
branch_labels = None
depends_on = None


def _has_column(table, col):
    bind = op.get_bind()
    insp = sa.inspect(bind)
    return col in [c['name'] for c in insp.get_columns(table)]


def upgrade():
    if not _has_column('companies', 'qualified_at'):
        op.add_column('companies', sa.Column('qualified_at', sa.DateTime(), nullable=True))
        op.create_index('ix_companies_qualified_at', 'companies', ['qualified_at'])
    if not _has_column('projects', 'qualified_at'):
        op.add_column('projects', sa.Column('qualified_at', sa.DateTime(), nullable=True))
        op.create_index('ix_projects_qualified_at', 'projects', ['qualified_at'])


def downgrade():
    if _has_column('projects', 'qualified_at'):
        op.drop_index('ix_projects_qualified_at', table_name='projects')
        op.drop_column('projects', 'qualified_at')
    if _has_column('companies', 'qualified_at'):
        op.drop_index('ix_companies_qualified_at', table_name='companies')
        op.drop_column('companies', 'qualified_at')
