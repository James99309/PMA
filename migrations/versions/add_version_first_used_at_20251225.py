"""add version_first_used_at to spec_templates

Revision ID: add_version_first_used_at
Revises: move_code_fields_to_template_items
Create Date: 2025-12-25

为 SpecTemplate 添加 version_first_used_at 字段，用于追踪当前版本首次生成MN编码的时间。
该字段用于判断版本是否已被"绑定"（即已经用于生成MN编码），从而决定是否需要在结构性变更时递增版本号。
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_version_first_used_at'
down_revision = 'add_code_rule_snapshot_20251224'
branch_labels = None
depends_on = None


def upgrade():
    # 添加 version_first_used_at 字段
    with op.batch_alter_table('spec_templates', schema=None) as batch_op:
        batch_op.add_column(sa.Column('version_first_used_at', sa.DateTime(), nullable=True))


def downgrade():
    # 删除 version_first_used_at 字段
    with op.batch_alter_table('spec_templates', schema=None) as batch_op:
        batch_op.drop_column('version_first_used_at')
