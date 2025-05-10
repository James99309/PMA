"""将actions表的company_id和contact_id字段改为可为空

Revision ID: 20240510_action_nullable
Revises: 07bd9afe4c03
Create Date: 2024-05-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20240510_action_nullable'
down_revision = '07bd9afe4c03'
branch_labels = None
depends_on = None

def upgrade():
    op.alter_column('actions', 'company_id',
               existing_type=sa.Integer(),
               nullable=True)
    op.alter_column('actions', 'contact_id',
               existing_type=sa.Integer(),
               nullable=True)

def downgrade():
    op.alter_column('actions', 'company_id',
               existing_type=sa.Integer(),
               nullable=False)
    op.alter_column('actions', 'contact_id',
               existing_type=sa.Integer(),
               nullable=False) 