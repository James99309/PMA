"""empty message

Revision ID: 25af362bc651
Revises: 7dc4a4210ad4, 7ca40c445fb1, add_subcategory_display_order
Create Date: 2025-04-26 19:36:09.896578

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '25af362bc651'
down_revision = ('7dc4a4210ad4', '7ca40c445fb1', 'add_subcategory_display_order')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
