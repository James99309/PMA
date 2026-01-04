"""Remove default_options from spec_definitions

背景：编码管理归模板（SpecTemplateItem），不归规格字典（SpecDefinition）
- SpecDefinition 只存储元数据：名称、单位、类型
- SpecTemplateItem.options 存储值→编码映射

Revision ID: remove_default_options_20251224
Revises: move_code_fields_20251224
Create Date: 2025-12-24

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'remove_default_options_20251224'
down_revision = 'move_code_fields_20251224'
branch_labels = None
depends_on = None


def upgrade():
    """删除 spec_definitions 表的 default_options 列"""
    # 使用 batch_alter_table 以兼容 SQLite
    with op.batch_alter_table('spec_definitions', schema=None) as batch_op:
        batch_op.drop_column('default_options')


def downgrade():
    """恢复 spec_definitions 表的 default_options 列"""
    with op.batch_alter_table('spec_definitions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('default_options', sa.JSON(), nullable=True))
