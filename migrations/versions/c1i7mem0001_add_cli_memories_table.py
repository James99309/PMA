"""add cli_memories table

Revision ID: c1i7mem0001
Revises: c1i5ki110001
Create Date: 2026-04-07

"""
from alembic import op
import sqlalchemy as sa

revision = 'c1i7mem0001'
down_revision = 'c1i5ki110001'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'cli_memories' in inspector.get_table_names():
        return

    op.create_table(
        'cli_memories',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('scope', sa.String(50), nullable=False, server_default='personal'),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('type', sa.String(20), nullable=False, server_default='knowledge'),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('summary', sa.String(500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )
    op.create_index('ix_cli_memories_scope', 'cli_memories', ['scope'])
    op.create_index('ix_cli_memories_user_id', 'cli_memories', ['user_id'])
    op.create_index('ix_cli_memories_is_active', 'cli_memories', ['is_active'])


def downgrade():
    op.drop_index('ix_cli_memories_is_active', table_name='cli_memories')
    op.drop_index('ix_cli_memories_user_id', table_name='cli_memories')
    op.drop_index('ix_cli_memories_scope', table_name='cli_memories')
    op.drop_table('cli_memories')
