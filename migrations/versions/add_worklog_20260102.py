"""添加工作日历和日志表

Revision ID: add_worklog_20260102
Revises:
Create Date: 2026-01-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'add_worklog_20260102'
down_revision = None
branch_labels = None
depends_on = None


def table_exists(table_name):
    """检查表是否存在"""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def index_exists(table_name, index_name):
    """检查索引是否存在"""
    bind = op.get_bind()
    inspector = inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    indexes = inspector.get_indexes(table_name)
    return any(idx['name'] == index_name for idx in indexes)


def upgrade():
    # 创建工作日志表（如果不存在）
    if not table_exists('worklogs'):
        op.create_table('worklogs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('log_date', sa.Date(), nullable=False),
        sa.Column('log_type', sa.String(20), default='daily'),
        sa.Column('week_number', sa.Integer(), nullable=True),
        sa.Column('year', sa.Integer(), nullable=True),
        sa.Column('summary', sa.Text(), nullable=True),
        sa.Column('total_hours', sa.Float(), default=0.0),
        sa.Column('additional_notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), default='draft'),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('owner_id', 'log_date', 'log_type', name='uq_worklog_owner_date_type')
        )

    if not index_exists('worklogs', 'ix_worklogs_log_date'):
        op.create_index(op.f('ix_worklogs_log_date'), 'worklogs', ['log_date'], unique=False)

    # 创建工作项表（如果不存在）
    if not table_exists('work_items'):
        op.create_table('work_items',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('planned_date', sa.Date(), nullable=False),
            sa.Column('start_time', sa.Time(), nullable=True),
            sa.Column('end_time', sa.Time(), nullable=True),
            sa.Column('is_all_day', sa.Boolean(), default=True),
            sa.Column('estimated_hours', sa.Float(), nullable=True),
            sa.Column('project_id', sa.Integer(), nullable=True),
            sa.Column('customer_id', sa.Integer(), nullable=True),
            sa.Column('work_type', sa.String(50), nullable=True),
            sa.Column('status', sa.String(20), default='planned'),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('actual_hours', sa.Float(), nullable=True),
            sa.Column('execution_notes', sa.Text(), nullable=True),
            sa.Column('worklog_id', sa.Integer(), nullable=True),
            sa.Column('owner_id', sa.Integer(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), default=False),
            sa.ForeignKeyConstraint(['customer_id'], ['companies.id'], ),
            sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
            sa.ForeignKeyConstraint(['worklog_id'], ['worklogs.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    if not index_exists('work_items', 'ix_work_items_planned_date'):
        op.create_index(op.f('ix_work_items_planned_date'), 'work_items', ['planned_date'], unique=False)
    if not index_exists('work_items', 'ix_work_items_status'):
        op.create_index(op.f('ix_work_items_status'), 'work_items', ['status'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_work_items_status'), table_name='work_items')
    op.drop_index(op.f('ix_work_items_planned_date'), table_name='work_items')
    op.drop_table('work_items')
    op.drop_index(op.f('ix_worklogs_log_date'), table_name='worklogs')
    op.drop_table('worklogs')
