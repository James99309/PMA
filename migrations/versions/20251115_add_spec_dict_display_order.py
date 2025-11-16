"""添加规格字典display_order字段用于拖拽排序

Revision ID: 20251115_add_spec_dict_display_order
Revises:
Create Date: 2025-11-15 21:45:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251115_add_spec_dict_display_order'
down_revision = '20251115_add_category_display_order'  # 依赖上一个迁移
branch_labels = None
depends_on = None


def upgrade():
    """添加display_order字段并初始化现有数据"""
    # 1. 添加display_order字段（允许NULL）
    op.add_column('specification_dictionary',
                  sa.Column('display_order', sa.Integer(), nullable=True))

    # 2. 为现有记录初始化display_order值（使用ID作为初始排序）
    op.execute("""
        UPDATE specification_dictionary
        SET display_order = id
        WHERE display_order IS NULL
    """)

    # 3. 将字段设置为NOT NULL
    op.alter_column('specification_dictionary', 'display_order',
                    existing_type=sa.Integer(),
                    nullable=False)

    # 4. 添加索引以提升查询性能
    op.create_index(op.f('ix_specification_dictionary_display_order'),
                    'specification_dictionary', ['display_order'],
                    unique=False)


def downgrade():
    """回滚迁移"""
    # 删除索引
    op.drop_index(op.f('ix_specification_dictionary_display_order'),
                  table_name='specification_dictionary')

    # 删除字段
    op.drop_column('specification_dictionary', 'display_order')
