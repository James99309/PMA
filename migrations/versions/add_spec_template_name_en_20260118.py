"""add name_en field to spec_templates table

Revision ID: add_spec_template_name_en_20260118
Revises: add_product_code_field_name_en_20260118
Create Date: 2026-01-18

为 SpecTemplate 添加 name_en 字段，用于存储规格模板的英文名称。
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_spec_template_name_en_20260118'
down_revision = 'add_product_code_field_name_en_20260118'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 name_en 字段
    with op.batch_alter_table('spec_templates', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name_en', sa.String(200), nullable=True))


def downgrade():
    # 删除 name_en 字段
    with op.batch_alter_table('spec_templates', schema=None) as batch_op:
        batch_op.drop_column('name_en')
