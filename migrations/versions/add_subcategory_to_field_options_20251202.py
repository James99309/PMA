"""在 ProductCodeFieldOption 表增加 subcategory_id 字段

将可配置字段选项从分类级别下沉到子分类级别：
- 新增 subcategory_id 字段：区分子分类级选项
- 新增 allow_quotation_config 字段：控制是否允许报价配置

Revision ID: add_subcategory_field_options
Revises:
Create Date: 2025-12-02
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_subcategory_field_options'
down_revision = '20251129_fix_region_fk'
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import inspect, text
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = [col['name'] for col in inspector.get_columns('product_code_field_options')]

    # 1. 在 ProductCodeFieldOption 表增加 subcategory_id 字段
    # NULL 表示分类级选项（用于产品编码），有值表示子分类级选项（用于报价可配置）
    if 'subcategory_id' not in existing_columns:
        op.add_column('product_code_field_options',
            sa.Column('subcategory_id', sa.Integer(), nullable=True)
        )
        print("✅ 添加 subcategory_id 列成功")
    else:
        print("⏭️ subcategory_id 列已存在，跳过")

    # 检查外键约束是否已存在
    result = bind.execute(text("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'product_code_field_options'
        AND constraint_type = 'FOREIGN KEY'
        AND constraint_name = 'fk_field_options_subcategory'
    """))
    fk_exists = result.fetchone() is not None

    # 创建外键约束
    if not fk_exists:
        op.create_foreign_key(
            'fk_field_options_subcategory',
            'product_code_field_options',
            'product_subcategories',
            ['subcategory_id'],
            ['id']
        )
        print("✅ 添加外键约束成功")
    else:
        print("⏭️ 外键约束已存在，跳过")

    # 检查索引是否已存在
    result = bind.execute(text("""
        SELECT indexname FROM pg_indexes
        WHERE tablename = 'product_code_field_options'
        AND indexname = 'ix_product_code_field_options_subcategory_id'
    """))
    idx_exists = result.fetchone() is not None

    # 创建索引以提高查询性能
    if not idx_exists:
        op.create_index(
            'ix_product_code_field_options_subcategory_id',
            'product_code_field_options',
            ['subcategory_id']
        )
        print("✅ 创建索引成功")
    else:
        print("⏭️ 索引已存在，跳过")

    # 2. 在 ProductCodeFieldOption 表增加 allow_quotation_config 字段
    # 仅子分类级选项使用，控制是否允许在报价单中配置
    if 'allow_quotation_config' not in existing_columns:
        op.add_column('product_code_field_options',
            sa.Column('allow_quotation_config', sa.Boolean(), server_default='false', nullable=True)
        )
        print("✅ 添加 allow_quotation_config 列成功")
    else:
        print("⏭️ allow_quotation_config 列已存在，跳过")


def downgrade():
    # 移除 allow_quotation_config 字段
    op.drop_column('product_code_field_options', 'allow_quotation_config')

    # 移除索引
    op.drop_index('ix_product_code_field_options_subcategory_id', table_name='product_code_field_options')

    # 移除外键约束
    op.drop_constraint('fk_field_options_subcategory', 'product_code_field_options', type_='foreignkey')

    # 移除 subcategory_id 字段
    op.drop_column('product_code_field_options', 'subcategory_id')
