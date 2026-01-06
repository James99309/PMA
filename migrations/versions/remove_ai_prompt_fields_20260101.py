"""删除employee_salary_config表中废弃的AI提示词字段

Revision ID: remove_ai_prompt_fields
Revises:
Create Date: 2026-01-01

删除字段:
- ai_personal_prompt: 个人分析自定义提示词（已废弃）
- ai_team_prompt: 团队分析自定义提示词（已废弃）

这些字段不再使用，AI分析现在完全依赖后端硬编码的标准提示词。
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'remove_ai_prompt_fields'
down_revision = None
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


def upgrade():
    # 检查表是否存在
    if not table_exists('employee_salary_config'):
        return

    # 删除废弃的AI提示词字段（只删除存在的列）
    columns_to_drop = ['ai_personal_prompt', 'ai_team_prompt']

    for col in columns_to_drop:
        if column_exists('employee_salary_config', col):
            with op.batch_alter_table('employee_salary_config', schema=None) as batch_op:
                batch_op.drop_column(col)


def downgrade():
    # 恢复AI提示词字段
    with op.batch_alter_table('employee_salary_config', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ai_team_prompt', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('ai_personal_prompt', sa.Text(), nullable=True))
