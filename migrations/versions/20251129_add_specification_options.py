"""add specification_options table and spec_option_id to field_options

Revision ID: 20251129_spec_options
Revises: 3358cee70c59
Create Date: 2025-11-29 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251129_spec_options'
down_revision = '3358cee70c59'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 创建 specification_options 表（检查是否已存在）
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_tables = inspector.get_table_names()

    if 'specification_options' not in existing_tables:
        op.create_table('specification_options',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('spec_id', sa.Integer(), nullable=False),
            sa.Column('value', sa.String(100), nullable=False),
            sa.Column('code', sa.String(10), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
            sa.Column('position', sa.Integer(), nullable=True, default=0),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['spec_id'], ['specification_dictionary.id'], name='fk_spec_options_spec_id'),
            sa.UniqueConstraint('spec_id', 'value', name='uq_spec_option_value')
        )

    # 2. 为 product_code_field_options 添加 spec_option_id 列（检查是否已存在）
    existing_columns = [col['name'] for col in inspector.get_columns('product_code_field_options')]
    if 'spec_option_id' in existing_columns:
        return  # 如果列已存在，跳过后续操作
    op.add_column('product_code_field_options',
        sa.Column('spec_option_id', sa.Integer(), nullable=True)
    )

    # 3. 添加外键约束
    op.create_foreign_key(
        'fk_field_options_spec_option_id',
        'product_code_field_options', 'specification_options',
        ['spec_option_id'], ['id']
    )

    # 4. 修改 value 和 code 列为可空（用于引用模式）
    op.alter_column('product_code_field_options', 'value',
        existing_type=sa.String(100),
        nullable=True
    )
    op.alter_column('product_code_field_options', 'code',
        existing_type=sa.String(10),
        nullable=True
    )


def downgrade():
    # 1. 恢复 value 和 code 列为不可空
    op.alter_column('product_code_field_options', 'value',
        existing_type=sa.String(100),
        nullable=False
    )
    op.alter_column('product_code_field_options', 'code',
        existing_type=sa.String(10),
        nullable=False
    )

    # 2. 删除外键约束
    op.drop_constraint('fk_field_options_spec_option_id', 'product_code_field_options', type_='foreignkey')

    # 3. 删除 spec_option_id 列
    op.drop_column('product_code_field_options', 'spec_option_id')

    # 4. 删除 specification_options 表
    op.drop_table('specification_options')
