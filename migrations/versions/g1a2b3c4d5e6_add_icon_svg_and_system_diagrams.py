"""add icon_svg to products and create system_diagrams table

Revision ID: g1a2b3c4d5e6
Revises: ca8d42e860a8
Create Date: 2026-02-21 16:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'g1a2b3c4d5e6'
down_revision = 'f2a3b4c5d6e7'
branch_labels = None
depends_on = None


def upgrade():
    # Add icon_svg column to products
    op.add_column('products', sa.Column('icon_svg', sa.Text(), nullable=True, comment='产品SVG图标数据'))

    # Create system_diagrams table
    op.create_table('system_diagrams',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False, server_default='未命名系统图'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('diagram_data', sa.JSON(), nullable=True),
        sa.Column('thumbnail_svg', sa.Text(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_diagrams_owner_id'), 'system_diagrams', ['owner_id'], unique=False)
    op.create_index(op.f('ix_system_diagrams_project_id'), 'system_diagrams', ['project_id'], unique=False)
    op.create_index(op.f('ix_system_diagrams_is_deleted'), 'system_diagrams', ['is_deleted'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_system_diagrams_is_deleted'), table_name='system_diagrams')
    op.drop_index(op.f('ix_system_diagrams_project_id'), table_name='system_diagrams')
    op.drop_index(op.f('ix_system_diagrams_owner_id'), table_name='system_diagrams')
    op.drop_table('system_diagrams')
    op.drop_column('products', 'icon_svg')
