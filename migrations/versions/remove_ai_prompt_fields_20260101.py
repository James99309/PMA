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


# revision identifiers, used by Alembic.
revision = 'remove_ai_prompt_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 删除废弃的AI提示词字段
    with op.batch_alter_table('employee_salary_config', schema=None) as batch_op:
        batch_op.drop_column('ai_personal_prompt')
        batch_op.drop_column('ai_team_prompt')


def downgrade():
    # 恢复AI提示词字段
    with op.batch_alter_table('employee_salary_config', schema=None) as batch_op:
        batch_op.add_column(sa.Column('ai_team_prompt', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('ai_personal_prompt', sa.Text(), nullable=True))
