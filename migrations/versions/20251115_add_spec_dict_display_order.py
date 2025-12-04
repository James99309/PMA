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
    from sqlalchemy import inspect, text
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = [col['name'] for col in inspector.get_columns('specification_dictionary')]

    if 'display_order' not in existing_columns:
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
        print("✅ 添加 display_order 字段成功")
    else:
        print("⏭️ display_order 字段已存在，跳过")

    # 4. 添加索引以提升查询性能（检查是否存在）
    result = bind.execute(text("SELECT indexname FROM pg_indexes WHERE tablename = 'specification_dictionary' AND indexname = 'ix_specification_dictionary_display_order'"))
    if not result.fetchone():
        op.create_index(op.f('ix_specification_dictionary_display_order'),
                        'specification_dictionary', ['display_order'],
                        unique=False)
        print("✅ 创建索引成功")
    else:
        print("⏭️ 索引已存在，跳过")


def downgrade():
    """回滚迁移"""
    # 删除索引
    op.drop_index(op.f('ix_specification_dictionary_display_order'),
                  table_name='specification_dictionary')

    # 删除字段
    op.drop_column('specification_dictionary', 'display_order')
