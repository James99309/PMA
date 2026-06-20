"""approval submitter-designate: add designate_pool to approval_step + designated_approvers to approval_instance

Revision ID: approval_submitter_designate_20260601
Revises: inventory_vendor_warehouse_20260531
Create Date: 2026-06-01

支持新审批人类型 'submitter_designate' — 提交时由提交者动态选择审批人。

新增字段:
  approval_step.designate_pool       JSON  — 限定提交者只能在某角色/部门内选(可选)
  approval_instance.designated_approvers  JSON  — 提交时绑定的 {step_id: user_id}

向后兼容:
  - 新字段都允许 NULL,旧步骤/旧实例不受影响
  - approver_type 仍是 String(20),只是合法值增加 'submitter_designate'
"""
from alembic import op
import sqlalchemy as sa


revision = 'approval_submitter_designate_20260601'
down_revision = 'inventory_vendor_warehouse_20260531'
branch_labels = None
depends_on = None


def upgrade():
    # 1) approval_step.designate_pool
    with op.batch_alter_table('approval_step') as batch_op:
        batch_op.add_column(sa.Column(
            'designate_pool', sa.JSON(), nullable=True,
            comment='submitter_designate 模式下的可选范围(roles/departments)'
        ))

    # 2) approval_instance.designated_approvers
    with op.batch_alter_table('approval_instance') as batch_op:
        batch_op.add_column(sa.Column(
            'designated_approvers', sa.JSON(), nullable=True,
            comment='提交时指定的审批人 {step_id: user_id}'
        ))


def downgrade():
    with op.batch_alter_table('approval_instance') as batch_op:
        batch_op.drop_column('designated_approvers')

    with op.batch_alter_table('approval_step') as batch_op:
        batch_op.drop_column('designate_pool')
