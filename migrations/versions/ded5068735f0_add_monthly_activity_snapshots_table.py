"""add monthly_activity_snapshots table

Revision ID: ded5068735f0
Revises: freeze_terminal_stage_projects_20260207
Create Date: 2026-02-08 15:48:23.686450

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ded5068735f0'
down_revision = 'freeze_terminal_stage_projects_20260207'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('monthly_activity_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=False),
        sa.Column('customer_total', sa.Integer(), server_default='0'),
        sa.Column('customer_highly_active', sa.Integer(), server_default='0'),
        sa.Column('customer_active', sa.Integer(), server_default='0'),
        sa.Column('customer_normal', sa.Integer(), server_default='0'),
        sa.Column('customer_to_follow', sa.Integer(), server_default='0'),
        sa.Column('customer_dormant', sa.Integer(), server_default='0'),
        sa.Column('customer_churned', sa.Integer(), server_default='0'),
        sa.Column('customer_activity_rate', sa.Numeric(precision=10, scale=4), server_default='0'),
        sa.Column('project_total', sa.Integer(), server_default='0'),
        sa.Column('project_highly_active', sa.Integer(), server_default='0'),
        sa.Column('project_active', sa.Integer(), server_default='0'),
        sa.Column('project_normal', sa.Integer(), server_default='0'),
        sa.Column('project_to_follow', sa.Integer(), server_default='0'),
        sa.Column('project_dormant', sa.Integer(), server_default='0'),
        sa.Column('project_churned', sa.Integer(), server_default='0'),
        sa.Column('project_frozen', sa.Integer(), server_default='0'),
        sa.Column('project_activity_rate', sa.Numeric(precision=10, scale=4), server_default='0'),
        sa.Column('calculated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'year', 'month', name='uq_monthly_activity_snapshot')
    )
    op.create_index('idx_activity_snapshot_user_year', 'monthly_activity_snapshots', ['user_id', 'year'])


def downgrade():
    op.drop_index('idx_activity_snapshot_user_year', table_name='monthly_activity_snapshots')
    op.drop_table('monthly_activity_snapshots')
