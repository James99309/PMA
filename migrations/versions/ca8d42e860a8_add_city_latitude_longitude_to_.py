
"""Add city, latitude, longitude to companies table

Revision ID: ca8d42e860a8
Revises: a9b8c7d6e5f4
Create Date: 2026-02-20 12:45:30.046943

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'ca8d42e860a8'
down_revision = 'a9b8c7d6e5f4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('companies', sa.Column('city', sa.String(length=100), nullable=True))
    op.add_column('companies', sa.Column('latitude', sa.Float(), nullable=True))
    op.add_column('companies', sa.Column('longitude', sa.Float(), nullable=True))


def downgrade():
    op.drop_column('companies', 'longitude')
    op.drop_column('companies', 'latitude')
    op.drop_column('companies', 'city')
