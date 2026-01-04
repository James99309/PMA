"""添加工作日历和日志表

Revision ID: add_worklog_20260102
Revises:
Create Date: 2026-01-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_worklog_20260102'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 创建工作日志表
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
    op.create_index(op.f('ix_worklogs_log_date'), 'worklogs', ['log_date'], unique=False)

    # 创建工作项表
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
    op.create_index(op.f('ix_work_items_planned_date'), 'work_items', ['planned_date'], unique=False)
    op.create_index(op.f('ix_work_items_status'), 'work_items', ['status'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_work_items_status'), table_name='work_items')
    op.drop_index(op.f('ix_work_items_planned_date'), table_name='work_items')
    op.drop_table('work_items')
    op.drop_index(op.f('ix_worklogs_log_date'), table_name='worklogs')
    op.drop_table('worklogs')
