
"""merge chat-system and knowledge-base heads

Revision ID: e5e82350daec
Revises: 1bec60c80118, a1b2c3d4e5f6
Create Date: 2026-02-15 23:12:44.460030

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e5e82350daec'
down_revision = ('1bec60c80118', 'a1b2c3d4e5f6')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass