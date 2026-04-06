"""add cli_skills table

Revision ID: c1i5ki110001
Revises: c1i4ag3nt0001
Create Date: 2026-04-06 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'c1i5ki110001'
down_revision = 'c1i4ag3nt0001'
branch_labels = None
depends_on = None


def upgrade():
    # 检查表是否已存在(支持重复执行)
    conn = op.get_bind()
    result = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'cli_skills')"
    ))
    if result.scalar():
        return

    op.create_table(
        'cli_skills',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=80), nullable=False),
        sa.Column('title', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('parameters', postgresql.JSONB(astext_type=sa.Text()),
                  nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('queries', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('output_format', sa.Text(), nullable=True),
        sa.Column('scope', sa.String(length=20), nullable=False, server_default='global'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(),
                  server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_cli_skills_name', 'cli_skills', ['name'], unique=True)
    op.create_index('ix_cli_skills_scope', 'cli_skills', ['scope'])
    op.create_index('ix_cli_skills_is_active', 'cli_skills', ['is_active'])


def downgrade():
    op.drop_index('ix_cli_skills_is_active', table_name='cli_skills')
    op.drop_index('ix_cli_skills_scope', table_name='cli_skills')
    op.drop_index('ix_cli_skills_name', table_name='cli_skills')
    op.drop_table('cli_skills')
