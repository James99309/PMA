"""add monthly_targets to employee_salary_config

Revision ID: add_monthly_targets_20251228
Revises:
Create Date: 2025-12-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_monthly_targets_20251228'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """添加 monthly_targets JSON 字段到 employee_salary_config 表"""
    # 检查列是否存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('employee_salary_config')]

    if 'monthly_targets' not in columns:
        op.add_column('employee_salary_config',
                      sa.Column('monthly_targets', sa.JSON(), nullable=True,
                               comment='月度目标配置 {"1": 10, "2": 12, ...} 单位：万元'))


def downgrade():
    """移除 monthly_targets 字段"""
    op.drop_column('employee_salary_config', 'monthly_targets')
