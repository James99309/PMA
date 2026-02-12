
"""Add export email permission fields

Revision ID: d2269307de93
Revises: a7f3e1c9d024
Create Date: 2026-02-12 22:52:35.191666

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd2269307de93'
down_revision = 'a7f3e1c9d024'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('permission_modules', sa.Column('supports_export_email', sa.Boolean(), nullable=True, server_default=sa.text('false')))
    op.add_column('permissions', sa.Column('can_export_email', sa.Boolean(), nullable=True, server_default=sa.text('false')))
    op.add_column('role_permissions', sa.Column('can_export_email', sa.Boolean(), nullable=True, server_default=sa.text('false')))

    # 设置 customer 模块的 supports_export_email 为 True
    op.execute("UPDATE permission_modules SET supports_export_email = true WHERE module_id = 'customer'")


def downgrade():
    op.drop_column('role_permissions', 'can_export_email')
    op.drop_column('permissions', 'can_export_email')
    op.drop_column('permission_modules', 'supports_export_email')
