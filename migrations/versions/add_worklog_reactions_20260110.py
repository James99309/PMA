"""add worklog reactions table and count fields

Revision ID: add_worklog_reactions_20260110
Revises: d2731c6921bb
Create Date: 2026-01-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_worklog_reactions_20260110'
down_revision = 'd2731c6921bb'
branch_labels = None
depends_on = None


def upgrade():
    """添加日志反馈功能：
    1. worklogs 表添加 thumbs_up_count 和 thumbs_down_count 字段
    2. 创建 worklog_reactions 表记录用户反馈
    """
    # 1. 添加计数字段到 worklogs 表
    op.add_column('worklogs',
        sa.Column('thumbs_up_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('worklogs',
        sa.Column('thumbs_down_count', sa.Integer(), nullable=False, server_default='0'))

    # 2. 创建 worklog_reactions 表
    op.create_table('worklog_reactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('worklog_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('reaction_type', sa.String(10), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['worklog_id'], ['worklogs.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # 3. 创建索引
    op.create_index('ix_worklog_reactions_worklog_id', 'worklog_reactions', ['worklog_id'])
    op.create_index('ix_worklog_reactions_user_id', 'worklog_reactions', ['user_id'])

    # 4. 创建唯一约束（每个用户对每个日志只能有一条反馈）
    op.create_unique_constraint('uq_worklog_user_reaction', 'worklog_reactions', ['worklog_id', 'user_id'])


def downgrade():
    """回滚：删除 worklog_reactions 表和计数字段"""
    # 删除唯一约束
    op.drop_constraint('uq_worklog_user_reaction', 'worklog_reactions', type_='unique')

    # 删除索引
    op.drop_index('ix_worklog_reactions_user_id', table_name='worklog_reactions')
    op.drop_index('ix_worklog_reactions_worklog_id', table_name='worklog_reactions')

    # 删除表
    op.drop_table('worklog_reactions')

    # 删除计数字段
    op.drop_column('worklogs', 'thumbs_down_count')
    op.drop_column('worklogs', 'thumbs_up_count')
