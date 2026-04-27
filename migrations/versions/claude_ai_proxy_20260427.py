"""add Claude AI proxy permission and usage tables

Revision ID: claude_ai_proxy_20260427
Revises: 4eb89347c0f8
Create Date: 2026-04-27 22:00:00.000000

新增字段（users 表）:
  - claude_ai_enabled       BOOLEAN  是否启用 Claude AI 代理
  - claude_ai_token         VARCHAR  代理认证 token，唯一
  - claude_ai_quota_tokens  BIGINT   月度配额（0 = 用全局默认）
  - claude_ai_enabled_at    TIMESTAMP 启用时间，审计用

新增表 ai_proxy_usage:
  - 缓存 Mac mini 上 oat_proxy 的用量数据，按 user_id + provider + date 唯一
"""
from alembic import op
import sqlalchemy as sa


revision = 'claude_ai_proxy_20260427'
down_revision = '4eb89347c0f8'
branch_labels = None
depends_on = None


def upgrade():
    # users 表加 4 个字段
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('claude_ai_enabled', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('claude_ai_token', sa.String(length=64), nullable=True))
        batch_op.add_column(sa.Column('claude_ai_quota_tokens', sa.BigInteger(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('claude_ai_enabled_at', sa.DateTime(), nullable=True))
        batch_op.create_unique_constraint('uq_users_claude_ai_token', ['claude_ai_token'])
        batch_op.create_index('ix_users_claude_ai_token', ['claude_ai_token'])

    # 新表 ai_proxy_usage
    op.create_table(
        'ai_proxy_usage',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(length=32), nullable=False, server_default='claude'),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('input_tokens', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('output_tokens', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('request_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_seen_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('user_id', 'provider', 'date', name='uq_ai_proxy_usage_user_provider_date'),
    )
    op.create_index('ix_ai_proxy_usage_user_id', 'ai_proxy_usage', ['user_id'])
    op.create_index('ix_ai_proxy_usage_date', 'ai_proxy_usage', ['date'])


def downgrade():
    op.drop_index('ix_ai_proxy_usage_date', table_name='ai_proxy_usage')
    op.drop_index('ix_ai_proxy_usage_user_id', table_name='ai_proxy_usage')
    op.drop_table('ai_proxy_usage')

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('ix_users_claude_ai_token')
        batch_op.drop_constraint('uq_users_claude_ai_token', type_='unique')
        batch_op.drop_column('claude_ai_enabled_at')
        batch_op.drop_column('claude_ai_quota_tokens')
        batch_op.drop_column('claude_ai_token')
        batch_op.drop_column('claude_ai_enabled')
