
"""add user_points_ledger table

Revision ID: 2bc2f14f94fe
Revises: 6831979cdbe4
Create Date: 2026-02-12 07:59:26.335600

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '2bc2f14f94fe'
down_revision = '6831979cdbe4'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    table_exists = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'user_points_ledger')"
    )).scalar()

    if not table_exists:
        op.create_table('user_points_ledger',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
            sa.Column('year', sa.Integer(), nullable=False),
            sa.Column('source_type', sa.String(length=50), nullable=False, server_default='quotation'),
            sa.Column('source_id', sa.Integer(), nullable=True),
            sa.Column('points', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('memo', sa.String(length=200), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.UniqueConstraint('user_id', 'source_type', 'source_id', name='uq_user_points_source'),
        )
        op.create_index('ix_user_points_ledger_user_id', 'user_points_ledger', ['user_id'])
        op.create_index('ix_user_points_year', 'user_points_ledger', ['user_id', 'year'])


def downgrade():
    op.drop_index('ix_user_points_year', table_name='user_points_ledger')
    op.drop_index('ix_user_points_ledger_user_id', table_name='user_points_ledger')
    op.drop_table('user_points_ledger')
