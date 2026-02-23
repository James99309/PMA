"""add access_requests table

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-02-20

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c4d5e6f7a8b9'
down_revision = 'b3c4d5e6f7a8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('access_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('requester_id', sa.Integer(), nullable=False),
        sa.Column('approver_id', sa.Integer(), nullable=False),
        sa.Column('entity_type', sa.String(length=20), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('request_message', sa.Text(), nullable=True),
        sa.Column('share_options', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['approver_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['requester_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_access_requests_requester_status', 'access_requests', ['requester_id', 'status'])
    op.create_index('ix_access_requests_approver_status', 'access_requests', ['approver_id', 'status'])
    op.create_index('ix_access_requests_entity', 'access_requests', ['entity_type', 'entity_id'])


def downgrade():
    op.drop_index('ix_access_requests_entity', table_name='access_requests')
    op.drop_index('ix_access_requests_approver_status', table_name='access_requests')
    op.drop_index('ix_access_requests_requester_status', table_name='access_requests')
    op.drop_table('access_requests')
