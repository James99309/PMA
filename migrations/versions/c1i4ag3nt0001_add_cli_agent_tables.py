"""add cli agent tables (cli_sessions + user_cli_state)

Revision ID: c1i4ag3nt0001
Revises: 5ed9cf9a28eb
Create Date: 2026-04-05 19:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'c1i4ag3nt0001'
down_revision = '5ed9cf9a28eb'
branch_labels = None
depends_on = None


def upgrade():
    # cli_sessions 表
    op.create_table(
        'cli_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True),
                  server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=120), nullable=True),
        sa.Column('status', sa.String(length=16), nullable=False, server_default='ACTIVE'),
        sa.Column('messages', postgresql.JSONB(astext_type=sa.Text()),
                  nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('usage_total', postgresql.JSONB(astext_type=sa.Text()),
                  nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('compaction_meta', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('last_active_at', sa.DateTime(),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cli_sessions_user_id', 'cli_sessions', ['user_id'])
    op.create_index('ix_cli_sessions_status', 'cli_sessions', ['status'])
    op.create_index('ix_cli_sessions_last_active_at', 'cli_sessions', ['last_active_at'])
    op.create_index(
        'ix_cli_sessions_user_status_active',
        'cli_sessions',
        ['user_id', 'status', 'last_active_at'],
    )

    # user_cli_state 表
    op.create_table(
        'user_cli_state',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('active_session_ids', postgresql.JSONB(astext_type=sa.Text()),
                  nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('current_session_id', sa.String(length=36), nullable=True),
        sa.Column('ui_preferences', postgresql.JSONB(astext_type=sa.Text()),
                  nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column('updated_at', sa.DateTime(),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('user_id'),
    )


def downgrade():
    op.drop_table('user_cli_state')
    op.drop_index('ix_cli_sessions_user_status_active', table_name='cli_sessions')
    op.drop_index('ix_cli_sessions_last_active_at', table_name='cli_sessions')
    op.drop_index('ix_cli_sessions_status', table_name='cli_sessions')
    op.drop_index('ix_cli_sessions_user_id', table_name='cli_sessions')
    op.drop_table('cli_sessions')
