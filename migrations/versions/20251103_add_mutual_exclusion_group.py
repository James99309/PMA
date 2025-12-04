"""添加产品关联互斥组功能

Revision ID: 20251103_mutual_exclusion
Create Date: 2025-11-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251103_mutual_exclusion'
down_revision = '20251102_quotation_details'
branch_labels = None
depends_on = None


def upgrade():
    """添加互斥组相关字段"""
    from sqlalchemy import inspect, text
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = [col['name'] for col in inspector.get_columns('product_relations')]

    # 添加互斥组ID字段
    if 'mutual_exclusion_group' not in existing_columns:
        op.add_column('product_relations',
            sa.Column('mutual_exclusion_group', sa.String(length=100), nullable=True,
                     comment='互斥组标识，同组内只能选择一个产品'))
        print("✅ 添加 mutual_exclusion_group 字段成功")
    else:
        print("⏭️ mutual_exclusion_group 字段已存在，跳过")

    # 添加组显示名称字段
    if 'group_display_name' not in existing_columns:
        op.add_column('product_relations',
            sa.Column('group_display_name', sa.String(length=200), nullable=True,
                     comment='互斥组显示名称，如"电源线规格"'))
        print("✅ 添加 group_display_name 字段成功")
    else:
        print("⏭️ group_display_name 字段已存在，跳过")

    # 添加组是否必选字段
    if 'is_group_required' not in existing_columns:
        op.add_column('product_relations',
            sa.Column('is_group_required', sa.Boolean(), nullable=True, default=False,
                     comment='该互斥组是否必选'))
        print("✅ 添加 is_group_required 字段成功")
    else:
        print("⏭️ is_group_required 字段已存在，跳过")

    # 添加组选择模式字段
    if 'group_selection_mode' not in existing_columns:
        op.add_column('product_relations',
            sa.Column('group_selection_mode', sa.String(length=20), nullable=True, default='single',
                     comment='组选择模式: single(单选), multiple(多选), none(无限制)'))
        print("✅ 添加 group_selection_mode 字段成功")
    else:
        print("⏭️ group_selection_mode 字段已存在，跳过")

    # 添加是否为默认选项字段
    if 'is_default' not in existing_columns:
        op.add_column('product_relations',
            sa.Column('is_default', sa.Boolean(), nullable=True, default=False,
                     comment='是否为该互斥组的默认选项'))
        print("✅ 添加 is_default 字段成功")
    else:
        print("⏭️ is_default 字段已存在，跳过")

    # 为互斥组字段创建索引，提高查询性能
    result = bind.execute(text("SELECT indexname FROM pg_indexes WHERE tablename = 'product_relations' AND indexname = 'idx_mutual_exclusion_group'"))
    if not result.fetchone():
        op.create_index('idx_mutual_exclusion_group', 'product_relations',
                       ['mutual_exclusion_group'],
                       unique=False)
        print("✅ 创建索引 idx_mutual_exclusion_group 成功")
    else:
        print("⏭️ 索引 idx_mutual_exclusion_group 已存在，跳过")


def downgrade():
    """回滚互斥组功能"""

    # 删除索引
    op.drop_index('idx_mutual_exclusion_group', table_name='product_relations')

    # 删除字段
    op.drop_column('product_relations', 'is_default')
    op.drop_column('product_relations', 'group_selection_mode')
    op.drop_column('product_relations', 'is_group_required')
    op.drop_column('product_relations', 'group_display_name')
    op.drop_column('product_relations', 'mutual_exclusion_group')

    print("✅ 成功回滚互斥组功能")
