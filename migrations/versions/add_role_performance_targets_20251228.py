"""add role_performance_targets and user_performance_targets tables

Revision ID: add_role_performance_targets_20251228
Revises:
Create Date: 2025-12-28

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_role_performance_targets_20251228'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """创建角色绩效目标和用户绩效目标表"""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # 1. 创建角色绩效目标表
    if 'role_performance_targets' not in existing_tables:
        op.create_table('role_performance_targets',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('role_code', sa.String(50), nullable=False),
            sa.Column('year', sa.Integer(), nullable=False),
            sa.Column('item_code', sa.String(50), nullable=False),

            # 目标值
            sa.Column('annual_target', sa.Numeric(15, 2), nullable=True),

            # 季度目标
            sa.Column('enable_quarterly', sa.Boolean(), default=False),
            sa.Column('q1_target', sa.Numeric(15, 2), nullable=True),
            sa.Column('q2_target', sa.Numeric(15, 2), nullable=True),
            sa.Column('q3_target', sa.Numeric(15, 2), nullable=True),
            sa.Column('q4_target', sa.Numeric(15, 2), nullable=True),

            # 月度目标
            sa.Column('enable_monthly', sa.Boolean(), default=False),
            sa.Column('monthly_targets', sa.JSON(), nullable=True),

            # 单位配置
            sa.Column('target_unit', sa.String(20), default='万元'),

            # 审计字段
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),

            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['created_by'], ['users.id']),
            sa.ForeignKeyConstraint(['updated_by'], ['users.id']),
            sa.UniqueConstraint('role_code', 'year', 'item_code',
                              name='uq_role_perf_target_role_year_item')
        )
        op.create_index('idx_role_perf_target_role_year', 'role_performance_targets',
                       ['role_code', 'year'])
        op.create_index('idx_role_perf_target_role_code', 'role_performance_targets',
                       ['role_code'])
        print("✓ 创建表 role_performance_targets")
    else:
        print("- 表 role_performance_targets 已存在，跳过")

    # 2. 创建用户绩效目标表
    if 'user_performance_targets' not in existing_tables:
        op.create_table('user_performance_targets',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('year', sa.Integer(), nullable=False),
            sa.Column('item_code', sa.String(50), nullable=False),

            # 覆盖值
            sa.Column('annual_target_override', sa.Numeric(15, 2), nullable=True),
            sa.Column('enable_quarterly_override', sa.Boolean(), nullable=True),
            sa.Column('q1_target_override', sa.Numeric(15, 2), nullable=True),
            sa.Column('q2_target_override', sa.Numeric(15, 2), nullable=True),
            sa.Column('q3_target_override', sa.Numeric(15, 2), nullable=True),
            sa.Column('q4_target_override', sa.Numeric(15, 2), nullable=True),
            sa.Column('enable_monthly_override', sa.Boolean(), nullable=True),
            sa.Column('monthly_targets_override', sa.JSON(), nullable=True),

            # 审计字段
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.Column('updated_by', sa.Integer(), nullable=True),

            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.ForeignKeyConstraint(['created_by'], ['users.id']),
            sa.ForeignKeyConstraint(['updated_by'], ['users.id']),
            sa.UniqueConstraint('user_id', 'year', 'item_code',
                              name='uq_user_perf_target_user_year_item')
        )
        op.create_index('idx_user_perf_target_user_year', 'user_performance_targets',
                       ['user_id', 'year'])
        print("✓ 创建表 user_performance_targets")
    else:
        print("- 表 user_performance_targets 已存在，跳过")


def downgrade():
    """删除表"""
    op.drop_table('user_performance_targets')
    op.drop_table('role_performance_targets')
