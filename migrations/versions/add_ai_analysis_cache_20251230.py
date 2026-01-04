"""Add AI analysis cache tables

Revision ID: add_ai_analysis_cache_20251230
Revises:
Create Date: 2025-12-30

这个迁移创建两个表：
1. ai_analysis_cache - AI分析结果缓存表
2. user_daily_login_records - 用户每日登录记录表
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_ai_analysis_cache_20251230'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # AI分析缓存表
    op.create_table('ai_analysis_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('analysis_date', sa.Date(), nullable=False),
        sa.Column('analysis_type', sa.String(50), server_default='daily_report'),
        sa.Column('analysis_result', sa.JSON(), nullable=True),
        sa.Column('raw_data_snapshot', sa.JSON(), nullable=True),
        sa.Column('data_hash', sa.String(64), nullable=True),
        sa.Column('ai_provider', sa.String(50), server_default='anthropic'),
        sa.Column('ai_model', sa.String(100), nullable=True),
        sa.Column('tokens_used', sa.Integer(), server_default='0'),
        sa.Column('status', sa.String(20), server_default='pending'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.Float(), nullable=True),
        sa.Column('updated_at', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'analysis_date', 'analysis_type', name='uix_user_date_type')
    )
    op.create_index('ix_ai_analysis_cache_user_id', 'ai_analysis_cache', ['user_id'])
    op.create_index('ix_ai_analysis_cache_analysis_date', 'ai_analysis_cache', ['analysis_date'])
    op.create_index('ix_ai_analysis_cache_status', 'ai_analysis_cache', ['status'])

    # 用户每日登录记录表
    op.create_table('user_daily_login_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('login_date', sa.Date(), nullable=False),
        sa.Column('first_login_time', sa.Float(), nullable=False),
        sa.Column('report_shown', sa.Boolean(), server_default='false'),
        sa.Column('report_dismissed', sa.Boolean(), server_default='false'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'login_date', name='uix_user_login_date')
    )
    op.create_index('ix_user_daily_login_user_id', 'user_daily_login_records', ['user_id'])
    op.create_index('ix_user_daily_login_date', 'user_daily_login_records', ['login_date'])


def downgrade():
    op.drop_table('user_daily_login_records')
    op.drop_table('ai_analysis_cache')
