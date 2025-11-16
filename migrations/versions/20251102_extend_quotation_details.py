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

    # 添加 pending_specs 字段
    op.add_column('quotation_details',
                  sa.Column('pending_specs', sa.JSON(), nullable=True,
                           comment='待定规格信息 JSON格式: {"pending_specs": ["频率"], "default_specs": {"频率": "800MHz"}}'))

    # 添加 parent_item_id 字段
    op.add_column('quotation_details',
                  sa.Column('parent_item_id', sa.Integer(), nullable=True,
                           comment='父级产品行ID（附加产品使用）'))

    # 添加 is_accessory 字段
    op.add_column('quotation_details',
                  sa.Column('is_accessory', sa.Boolean(), nullable=False, server_default='0',
                           comment='是否为附加产品'))

    # 添加 is_editable 字段
    op.add_column('quotation_details',
                  sa.Column('is_editable', sa.Boolean(), nullable=False, server_default='1',
                           comment='是否可编辑（附加产品不可编辑）'))

    # 添加外键约束
    op.create_foreign_key('fk_quotation_details_parent',
                         'quotation_details', 'quotation_details',
                         ['parent_item_id'], ['id'],
                         ondelete='CASCADE')

    # 添加索引
    op.create_index('idx_quotation_details_parent', 'quotation_details',
                    ['parent_item_id'], unique=False)

    print("✅ quotation_details 表扩展成功")
    print("   - 添加 pending_specs 字段（待定规格）")
    print("   - 添加 parent_item_id 字段（附加产品关联）")
    print("   - 添加 is_accessory 字段（附加产品标记）")
    print("   - 添加 is_editable 字段（编辑权限控制）")


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
