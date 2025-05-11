"""Final merge all heads

Revision ID: e29e27c7aa89
Revises: 3cf37752a616, account_id_for_stats
Create Date: 2025-05-11 21:15:34.823039

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e29e27c7aa89'
down_revision = ('3cf37752a616', 'account_id_for_stats')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
