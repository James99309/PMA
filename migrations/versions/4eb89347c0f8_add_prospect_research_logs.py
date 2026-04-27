"""add_prospect_research_logs

Revision ID: 4eb89347c0f8
Revises: cf15777f3e83
Create Date: 2026-04-27 08:45:00.000000

新增 prospect_research_logs 表，用于：
- 批量调研每日配额跟踪（非管理员每天最多3次）
- 所有调研任务的并发状态追踪（崩溃恢复）
"""
from alembic import op
import sqlalchemy as sa


revision = '4eb89347c0f8'
down_revision = 'da26751ef991'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'prospect_research_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('job_type', sa.String(20), nullable=False),  # 'batch' | 'intel' | 'lost'
        sa.Column('status', sa.String(20), nullable=False, server_default='running'),  # 'running' | 'done' | 'failed'
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_prl_user_created', 'prospect_research_logs', ['user_id', 'created_at'])
    op.create_index('ix_prl_status', 'prospect_research_logs', ['status'])


def downgrade():
    op.drop_index('ix_prl_status', 'prospect_research_logs')
    op.drop_index('ix_prl_user_created', 'prospect_research_logs')
    op.drop_table('prospect_research_logs')
