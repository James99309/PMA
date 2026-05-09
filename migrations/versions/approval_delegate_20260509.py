"""add approval_instance delegate fields (转交真实化)

Revision ID: approval_delegate_20260509
Revises: business_card_fields_20260508
Create Date: 2026-05-09

新增 ApprovalInstance.delegated_to_id / delegated_at / delegated_by_id 三列,
支持当前步骤的转交代审 (per-step 转交, 流程推进时清空).
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'approval_delegate_20260509'
down_revision = 'business_card_fields_20260508'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('approval_instance', schema=None) as batch_op:
        batch_op.add_column(sa.Column('delegated_to_id', sa.Integer(), nullable=True,
                                       comment='被转交目标审批人'))
        batch_op.add_column(sa.Column('delegated_at', sa.DateTime(), nullable=True,
                                       comment='转交时间'))
        batch_op.add_column(sa.Column('delegated_by_id', sa.Integer(), nullable=True,
                                       comment='发起转交的原审批人'))
        batch_op.create_foreign_key(
            'fk_approval_instance_delegated_to_users',
            'users', ['delegated_to_id'], ['id']
        )
        batch_op.create_foreign_key(
            'fk_approval_instance_delegated_by_users',
            'users', ['delegated_by_id'], ['id']
        )


def downgrade():
    with op.batch_alter_table('approval_instance', schema=None) as batch_op:
        batch_op.drop_constraint('fk_approval_instance_delegated_by_users', type_='foreignkey')
        batch_op.drop_constraint('fk_approval_instance_delegated_to_users', type_='foreignkey')
        batch_op.drop_column('delegated_by_id')
        batch_op.drop_column('delegated_at')
        batch_op.drop_column('delegated_to_id')
