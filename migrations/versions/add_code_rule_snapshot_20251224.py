"""Add code_rule_version and code_rule_snapshot to product_configurations

为 ProductConfiguration 添加编码规则快照字段：
- code_rule_version: 规则版本号（如 V1.0）
- code_rule_snapshot: 编码规则完整快照（JSON）

Revision ID: add_code_rule_snapshot_20251224
Revises: remove_default_options_20251224
Create Date: 2025-12-24

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_code_rule_snapshot_20251224'
down_revision = 'remove_default_options_20251224'
branch_labels = None
depends_on = None


def upgrade():
    """添加 code_rule_version 和 code_rule_snapshot 列"""
    # 使用 batch_alter_table 以兼容 SQLite
    with op.batch_alter_table('product_configurations', schema=None) as batch_op:
        batch_op.add_column(sa.Column('code_rule_version', sa.String(20), nullable=True))
        batch_op.add_column(sa.Column('code_rule_snapshot', sa.JSON(), nullable=True))


def downgrade():
    """删除 code_rule_version 和 code_rule_snapshot 列"""
    with op.batch_alter_table('product_configurations', schema=None) as batch_op:
        batch_op.drop_column('code_rule_snapshot')
        batch_op.drop_column('code_rule_version')
