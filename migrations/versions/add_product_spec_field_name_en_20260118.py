"""Add field_name_en to product_specs table

Revision ID: add_product_spec_field_name_en_20260118
Revises: add_spec_template_name_en_20260118
Create Date: 2026-01-18

为 product_specs 添加 field_name_en 字段，用于存储规格名称的英文翻译。
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_product_spec_field_name_en_20260118'
down_revision = 'add_spec_template_name_en_20260118'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('product_specs', schema=None) as batch_op:
        batch_op.add_column(sa.Column('field_name_en', sa.String(100), nullable=True))


def downgrade():
    with op.batch_alter_table('product_specs', schema=None) as batch_op:
        batch_op.drop_column('field_name_en')
