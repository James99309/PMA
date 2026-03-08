"""add spec_dict_id to spec_template_items

Revision ID: 4e121e39a998
Revises: 20d4b0658fcf
Create Date: 2026-03-07 20:48:33.995173

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4e121e39a998'
down_revision = '20d4b0658fcf'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('spec_template_items',
                  sa.Column('spec_dict_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_spec_template_items_spec_dict_id',
        'spec_template_items', 'specification_dictionary',
        ['spec_dict_id'], ['id'])


def downgrade():
    op.drop_constraint('fk_spec_template_items_spec_dict_id',
                       'spec_template_items', type_='foreignkey')
    op.drop_column('spec_template_items', 'spec_dict_id')
