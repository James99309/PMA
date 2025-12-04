"""扩展报价单明细表，支持待定规格和附加产品

Revision ID: 20251102_quotation_details
Revises: 20251102_product_relations
Create Date: 2025-11-02

业务说明:
- 扩展 quotation_details 表，支持产品规格待定状态
- 支持主产品+附加产品组合模式
- 附加产品数量自动联动，不可单独编辑

变更内容:
1. 添加 pending_specs 字段 - 待定规格信息（JSON）
2. 添加 parent_item_id 字段 - 父级产品行ID（附加产品使用）
3. 添加 is_accessory 字段 - 是否为附加产品
4. 添加 is_editable 字段 - 是否可编辑

依赖:
- quotation_details 表必须存在

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251102_quotation_details'
down_revision = '20251102_product_relations'
branch_labels = None
depends_on = None


def upgrade():
    """扩展报价单明细表"""
    from sqlalchemy import inspect, text
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = [col['name'] for col in inspector.get_columns('quotation_details')]

    # 添加 pending_specs 字段
    if 'pending_specs' not in existing_columns:
        op.add_column('quotation_details',
                      sa.Column('pending_specs', sa.JSON(), nullable=True,
                               comment='待定规格信息 JSON格式: {"pending_specs": ["频率"], "default_specs": {"频率": "800MHz"}}'))
        print("✅ 添加 pending_specs 字段成功")
    else:
        print("⏭️ pending_specs 字段已存在，跳过")

    # 添加 parent_item_id 字段
    if 'parent_item_id' not in existing_columns:
        op.add_column('quotation_details',
                      sa.Column('parent_item_id', sa.Integer(), nullable=True,
                               comment='父级产品行ID（附加产品使用）'))
        print("✅ 添加 parent_item_id 字段成功")
    else:
        print("⏭️ parent_item_id 字段已存在，跳过")

    # 添加 is_accessory 字段
    if 'is_accessory' not in existing_columns:
        op.add_column('quotation_details',
                      sa.Column('is_accessory', sa.Boolean(), nullable=False, server_default='0',
                               comment='是否为附加产品'))
        print("✅ 添加 is_accessory 字段成功")
    else:
        print("⏭️ is_accessory 字段已存在，跳过")

    # 添加 is_editable 字段
    if 'is_editable' not in existing_columns:
        op.add_column('quotation_details',
                      sa.Column('is_editable', sa.Boolean(), nullable=False, server_default='1',
                               comment='是否可编辑（附加产品不可编辑）'))
        print("✅ 添加 is_editable 字段成功")
    else:
        print("⏭️ is_editable 字段已存在，跳过")

    # 检查外键约束是否已存在
    result = bind.execute(text("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'quotation_details'
        AND constraint_type = 'FOREIGN KEY'
        AND constraint_name = 'fk_quotation_details_parent'
    """))
    fk_exists = result.fetchone() is not None

    if not fk_exists:
        op.create_foreign_key('fk_quotation_details_parent',
                             'quotation_details', 'quotation_details',
                             ['parent_item_id'], ['id'],
                             ondelete='CASCADE')
        print("✅ 添加外键约束成功")
    else:
        print("⏭️ 外键约束已存在，跳过")

    # 检查索引是否已存在
    result = bind.execute(text("""
        SELECT indexname FROM pg_indexes
        WHERE tablename = 'quotation_details'
        AND indexname = 'idx_quotation_details_parent'
    """))
    idx_exists = result.fetchone() is not None

    if not idx_exists:
        op.create_index('idx_quotation_details_parent', 'quotation_details',
                        ['parent_item_id'], unique=False)
        print("✅ 添加索引成功")
    else:
        print("⏭️ 索引已存在，跳过")


def downgrade():
    """回滚：删除新增字段"""

    # 删除索引
    op.drop_index('idx_quotation_details_parent', table_name='quotation_details')

    # 删除外键
    op.drop_constraint('fk_quotation_details_parent', 'quotation_details', type_='foreignkey')

    # 删除列
    op.drop_column('quotation_details', 'is_editable')
    op.drop_column('quotation_details', 'is_accessory')
    op.drop_column('quotation_details', 'parent_item_id')
    op.drop_column('quotation_details', 'pending_specs')

    print("✅ quotation_details 表扩展已回滚")
