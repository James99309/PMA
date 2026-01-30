"""Add execution_condition to approval_step table

Revision ID: add_step_execution_condition_20260129
Revises: add_product_spec_field_name_en_20260118
Create Date: 2026-01-29

为 approval_step 表添加 execution_condition JSON 字段，
用于配置步骤执行条件：满足条件时才执行此步骤，为空则无条件执行。
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_step_execution_condition_20260129'
down_revision = 'add_product_spec_field_name_en_20260118'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('approval_step', schema=None) as batch_op:
        batch_op.add_column(sa.Column('execution_condition', sa.JSON(), nullable=True,
                                       comment='步骤执行条件：满足条件时才执行此步骤，为空则无条件执行'))


def downgrade():
    with op.batch_alter_table('approval_step', schema=None) as batch_op:
        batch_op.drop_column('execution_condition')
