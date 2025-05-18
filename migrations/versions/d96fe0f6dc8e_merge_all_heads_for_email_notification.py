"""merge all heads for email notification

Revision ID: d96fe0f6dc8e
Revises: 1237d43dcdd8, 2a8d58e077f8, add_email_notification
Create Date: 2025-05-17 17:43:00.350233

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd96fe0f6dc8e'
down_revision = ('1237d43dcdd8', '2a8d58e077f8')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
