"""update points ledger unique constraint to include year

Revision ID: a7f3e1c9d024
Revises: 2bc2f14f94fe
Create Date: 2026-02-12 13:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a7f3e1c9d024'
down_revision = '2bc2f14f94fe'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()

    # Drop old constraint (if exists)
    if conn.dialect.name == 'postgresql':
        conn.execute(sa.text(
            "ALTER TABLE user_points_ledger "
            "DROP CONSTRAINT IF EXISTS uq_user_points_source"
        ))
    else:
        # SQLite: skip constraint changes
        return

    # Add new constraint with year
    op.create_unique_constraint(
        'uq_user_points_source_year',
        'user_points_ledger',
        ['user_id', 'source_type', 'source_id', 'year']
    )


def downgrade():
    conn = op.get_bind()

    if conn.dialect.name == 'postgresql':
        conn.execute(sa.text(
            "ALTER TABLE user_points_ledger "
            "DROP CONSTRAINT IF EXISTS uq_user_points_source_year"
        ))

    op.create_unique_constraint(
        'uq_user_points_source',
        'user_points_ledger',
        ['user_id', 'source_type', 'source_id']
    )
