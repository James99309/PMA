"""Add year field to employee_salary_config

Revision ID: add_year_to_salary_config
Revises:
Create Date: 2026-01-01

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'add_year_to_salary_config'
down_revision = None  # 将在运行时自动确定
branch_labels = None
depends_on = None


def table_exists(table_name):
    """检查表是否存在"""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def column_exists(table_name, column_name):
    """检查列是否存在"""
    bind = op.get_bind()
    inspector = inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns


def index_exists(table_name, index_name):
    """检查索引是否存在"""
    bind = op.get_bind()
    inspector = inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    indexes = inspector.get_indexes(table_name)
    return any(idx['name'] == index_name for idx in indexes)


def constraint_exists(table_name, constraint_name):
    """检查唯一约束是否存在"""
    bind = op.get_bind()
    inspector = inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    unique_constraints = inspector.get_unique_constraints(table_name)
    return any(uc.get('name') == constraint_name for uc in unique_constraints)


def upgrade():
    # 检查表是否存在
    if not table_exists('employee_salary_config'):
        return

    # 1. 添加 year 列（如果不存在）
    if not column_exists('employee_salary_config', 'year'):
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
    try:
        op.drop_constraint('employee_salary_config_user_id_key', 'employee_salary_config', type_='unique')
    except Exception:
        pass  # 约束可能不存在

    try:
        op.drop_index('ix_employee_salary_config_user_id', 'employee_salary_config')
    except Exception:
        pass  # 索引可能不存在

    # 5. 创建新的复合唯一约束（如果不存在）
    if not constraint_exists('employee_salary_config', 'uq_employee_salary_config_user_year'):
        op.create_unique_constraint(
            'uq_employee_salary_config_user_year',
            'employee_salary_config',
            ['user_id', 'year']
        )

    # 6. 创建索引（如果不存在）
    if not index_exists('employee_salary_config', 'idx_employee_salary_config_user_year'):
        op.create_index(
            'idx_employee_salary_config_user_year',
            'employee_salary_config',
            ['user_id', 'year']
        )

    if not index_exists('employee_salary_config', 'ix_employee_salary_config_year'):
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
