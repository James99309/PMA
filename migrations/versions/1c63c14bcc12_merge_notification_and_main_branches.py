"""merge notification and main branches

Revision ID: 1c63c14bcc12
Revises: add_notification_tables, d96fe0f6dc8e
Create Date: 2025-05-18 09:07:33.576314

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1c63c14bcc12'
down_revision = ('add_notification_tables', 'd96fe0f6dc8e')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
