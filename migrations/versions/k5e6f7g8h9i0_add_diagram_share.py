"""add diagram share tokens and external sessions

Revision ID: k5e6f7g8h9i0
Revises: j4d5e6f7g8h9
Create Date: 2026-02-25 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'k5e6f7g8h9i0'
down_revision = 'j4d5e6f7g8h9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('diagram_share_tokens',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=64), nullable=False),
        sa.Column('project_name', sa.String(length=200), nullable=True),
        sa.Column('designated_email', sa.String(length=200), nullable=False),
        sa.Column('source_diagram_id', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id']),
        sa.ForeignKeyConstraint(['source_diagram_id'], ['system_diagrams.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_diagram_share_tokens_token', 'diagram_share_tokens', ['token'], unique=True)

    op.create_table('diagram_external_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('share_token_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=200), nullable=False),
        sa.Column('diagram_id', sa.Integer(), nullable=True),
        sa.Column('access_count', sa.Integer(), server_default='0'),
        sa.Column('last_accessed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['diagram_id'], ['system_diagrams.id']),
        sa.ForeignKeyConstraint(['share_token_id'], ['diagram_share_tokens.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('share_token_id', 'email', name='uq_share_token_email')
    )
    op.create_index('ix_diagram_external_sessions_email', 'diagram_external_sessions', ['email'])


def downgrade():
    op.drop_table('diagram_external_sessions')
    op.drop_table('diagram_share_tokens')
