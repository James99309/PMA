"""在spec_definitions表中添加allow_attachment字段

Revision ID: add_allow_attachment_field
Revises:
Create Date: 2026-01-10

添加字段:
- allow_attachment: 是否允许上传附件（用于标识内标签、外标签、说明书等需要附件的规格项）
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = 'add_allow_attachment_field'
down_revision = None
branch_labels = None
depends_on = None


def table_exists(table_name):
    """检查表是否存在"""
    bind = op.get_bind()
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def column_exists(table_name, column_name):
    """检查列是否存在"""
    bind = op.get_bind()
    inspector = inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    columns = [c['name'] for c in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    # 检查表是否存在
    if not table_exists('spec_definitions'):
        return

    # 添加allow_attachment字段（只添加不存在的列）
    if not column_exists('spec_definitions', 'allow_attachment'):
        with op.batch_alter_table('spec_definitions', schema=None) as batch_op:
            batch_op.add_column(sa.Column('allow_attachment', sa.Boolean(), nullable=True, server_default='false'))


def downgrade():
    # 删除allow_attachment字段
    if column_exists('spec_definitions', 'allow_attachment'):
        with op.batch_alter_table('spec_definitions', schema=None) as batch_op:
            batch_op.drop_column('allow_attachment')
