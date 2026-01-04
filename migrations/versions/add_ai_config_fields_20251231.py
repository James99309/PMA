# -*- coding: utf-8 -*-
"""添加AI分析配置字段到员工薪资配置表

Revision ID: add_ai_config_fields
Revises:
Create Date: 2025-12-31
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'add_ai_config_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 添加AI分析配置字段
    op.add_column('employee_salary_config',
        sa.Column('ai_analysis_enabled', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('employee_salary_config',
        sa.Column('ai_personal_prompt', sa.Text(), nullable=True))
    op.add_column('employee_salary_config',
        sa.Column('ai_team_prompt', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('employee_salary_config', 'ai_team_prompt')
    op.drop_column('employee_salary_config', 'ai_personal_prompt')
    op.drop_column('employee_salary_config', 'ai_analysis_enabled')
