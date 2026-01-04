"""add salary period snapshots table

Revision ID: add_salary_period_snapshots_20251230
Revises:
Create Date: 2025-12-30

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_salary_period_snapshots_20251230'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """创建薪资周期快照表"""
    op.create_table('salary_period_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('period_type', sa.String(20), nullable=False),
        sa.Column('period_value', sa.Integer(), nullable=False),

        # 系统计算值
        sa.Column('calculated_base_salary', sa.Numeric(12, 2), nullable=True),
        sa.Column('calculated_management_allowance', sa.Numeric(12, 2), nullable=True),
        sa.Column('calculated_performance_salary', sa.Numeric(12, 2), nullable=True),
        sa.Column('calculated_commission', sa.Numeric(12, 2), nullable=True),
        sa.Column('calculated_team_share', sa.Numeric(12, 2), nullable=True),
        sa.Column('calculated_total', sa.Numeric(12, 2), nullable=True),

        # 财务调整值
        sa.Column('adjusted_base_salary', sa.Numeric(12, 2), nullable=True),
        sa.Column('adjusted_management_allowance', sa.Numeric(12, 2), nullable=True),
        sa.Column('adjusted_performance_salary', sa.Numeric(12, 2), nullable=True),
        sa.Column('adjusted_commission', sa.Numeric(12, 2), nullable=True),
        sa.Column('adjusted_team_share', sa.Numeric(12, 2), nullable=True),
        sa.Column('adjusted_total', sa.Numeric(12, 2), nullable=True),

        # 计算参数快照
        sa.Column('calculation_params', sa.JSON(), nullable=True),

        # 调整信息
        sa.Column('adjustment_reason', sa.Text(), nullable=True),
        sa.Column('adjusted_by', sa.Integer(), nullable=True),
        sa.Column('adjusted_at', sa.DateTime(), nullable=True),

        # 状态管理
        sa.Column('status', sa.String(20), nullable=True, server_default='draft'),
        sa.Column('confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('confirmed_by', sa.Integer(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('published_by', sa.Integer(), nullable=True),

        # 时间戳
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),

        # 主键和外键
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['adjusted_by'], ['users.id']),
        sa.ForeignKeyConstraint(['confirmed_by'], ['users.id']),
        sa.ForeignKeyConstraint(['published_by'], ['users.id']),

        # 唯一约束
        sa.UniqueConstraint('user_id', 'year', 'period_type', 'period_value',
                           name='uq_salary_snapshot_user_period'),
    )

    # 创建索引
    op.create_index('idx_salary_snapshot_user_year', 'salary_period_snapshots',
                    ['user_id', 'year'])
    op.create_index('idx_salary_snapshot_status', 'salary_period_snapshots',
                    ['status'])


def downgrade():
    """删除薪资周期快照表"""
    op.drop_index('idx_salary_snapshot_status', table_name='salary_period_snapshots')
    op.drop_index('idx_salary_snapshot_user_year', table_name='salary_period_snapshots')
    op.drop_table('salary_period_snapshots')
