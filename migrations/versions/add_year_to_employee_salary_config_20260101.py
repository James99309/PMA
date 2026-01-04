"""Add year field to employee_salary_config

Revision ID: add_year_to_salary_config
Revises:
Create Date: 2026-01-01

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'add_year_to_salary_config'
down_revision = None  # 将在运行时自动确定
branch_labels = None
depends_on = None


def upgrade():
    # 1. 添加 year 列（可空）
    op.add_column('employee_salary_config',
        sa.Column('year', sa.Integer(), nullable=True)
    )

    # 2. 将现有数据的 year 设置为当前年份
    current_year = datetime.now().year
    op.execute(f"UPDATE employee_salary_config SET year = {current_year} WHERE year IS NULL")

    # 3. 将 year 列设置为非空
    op.alter_column('employee_salary_config', 'year',
        existing_type=sa.Integer(),
        nullable=False
    )

    # 4. 移除旧的唯一约束（如果存在）
    # 注意：约束名可能因数据库而异
    try:
        op.drop_constraint('employee_salary_config_user_id_key', 'employee_salary_config', type_='unique')
    except Exception:
        pass  # 约束可能不存在

    try:
        op.drop_index('ix_employee_salary_config_user_id', 'employee_salary_config')
    except Exception:
        pass  # 索引可能不存在

    # 5. 创建新的复合唯一约束
    op.create_unique_constraint(
        'uq_employee_salary_config_user_year',
        'employee_salary_config',
        ['user_id', 'year']
    )

    # 6. 创建索引
    op.create_index(
        'idx_employee_salary_config_user_year',
        'employee_salary_config',
        ['user_id', 'year']
    )

    op.create_index(
        'ix_employee_salary_config_year',
        'employee_salary_config',
        ['year']
    )


def downgrade():
    # 移除索引
    op.drop_index('ix_employee_salary_config_year', 'employee_salary_config')
    op.drop_index('idx_employee_salary_config_user_year', 'employee_salary_config')

    # 移除复合唯一约束
    op.drop_constraint('uq_employee_salary_config_user_year', 'employee_salary_config', type_='unique')

    # 恢复 user_id 的唯一约束
    op.create_unique_constraint(
        'employee_salary_config_user_id_key',
        'employee_salary_config',
        ['user_id']
    )

    # 移除 year 列
    op.drop_column('employee_salary_config', 'year')
