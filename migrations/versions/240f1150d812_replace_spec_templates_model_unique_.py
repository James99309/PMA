
"""replace spec_templates model unique constraint with partial index

Revision ID: 240f1150d812
Revises: a1742ee99753
Create Date: 2026-03-10 11:16:57.679900

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '240f1150d812'
down_revision = 'a1742ee99753'
branch_labels = None
depends_on = None


def upgrade():
    # Drop the old unique constraint on model column
    op.drop_constraint('spec_templates_model_key', 'spec_templates', type_='unique')

    # Create partial unique index: only enforce uniqueness for active records
    op.execute(
        "CREATE UNIQUE INDEX uix_spec_templates_model_active "
        "ON spec_templates (model) WHERE is_active = true"
    )


def downgrade():
    # Drop the partial unique index
    op.drop_index('uix_spec_templates_model_active', table_name='spec_templates')

    # Restore the old unique constraint
    op.create_unique_constraint('spec_templates_model_key', 'spec_templates', ['model'])
