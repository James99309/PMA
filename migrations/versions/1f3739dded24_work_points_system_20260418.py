
"""work_points_system_20260418

Revision ID: 1f3739dded24
Revises: subtask_tables_20260418
Create Date: 2026-04-18 09:24:27.374190

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '1f3739dded24'
down_revision = 'subtask_tables_20260418'
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy.dialects import postgresql

    # 1. 行为配置表
    op.create_table('points_behavior_config',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('behavior_code', sa.String(64), nullable=False),
        sa.Column('behavior_name', sa.String(128), nullable=False),
        sa.Column('category', sa.String(32), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('daily_cap', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('behavior_code', name='uq_behavior_code'),
    )

    # 2. 积分流水表
    op.create_table('points_transaction',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('behavior_code', sa.String(64), nullable=False),
        sa.Column('source_type', sa.String(64), nullable=True),
        sa.Column('source_id', sa.Integer(), nullable=True),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('memo', sa.String(256), nullable=True),
        sa.Column('year', sa.SmallInteger(), nullable=False),
        sa.Column('month', sa.SmallInteger(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_pt_user_year_month', 'points_transaction', ['user_id', 'year', 'month'])
    op.create_index('ix_pt_year_month', 'points_transaction', ['year', 'month'])
    op.create_index('ix_pt_source', 'points_transaction', ['source_type', 'source_id'])

    # 3. 汇总缓存表
    op.create_table('user_points_summary',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.SmallInteger(), nullable=False),
        sa.Column('month', sa.SmallInteger(), nullable=False),
        sa.Column('total_points', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('behavior_breakdown', postgresql.JSONB(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('user_id', 'year', 'month'),
    )

    # 4. 预置行为配置数据
    op.execute("""
        INSERT INTO points_behavior_config (behavior_code, behavior_name, category, points, daily_cap) VALUES
        ('wiki_share', '共享Wiki文章', 'knowledge', 30, 90),
        ('wiki_cited', 'Wiki文章被引用', 'knowledge', 10, 50),
        ('project_create', '新建项目', 'business', 50, NULL),
        ('project_stage_advance', '推进项目阶段', 'business', 20, NULL),
        ('customer_create', '发现新客户', 'business', 40, NULL),
        ('daily_log_submit', '提交工作日志', 'content', 10, 10),
        ('task_complete', '完成任务', 'task', 15, NULL)
    """)

    # 5. 清除旧的产品积分台账表
    op.execute("DROP TABLE IF EXISTS user_points_ledger CASCADE")


def downgrade():
    op.drop_table('user_points_summary')
    op.drop_index('ix_pt_source', 'points_transaction')
    op.drop_index('ix_pt_year_month', 'points_transaction')
    op.drop_index('ix_pt_user_year_month', 'points_transaction')
    op.drop_table('points_transaction')
    op.drop_table('points_behavior_config')
