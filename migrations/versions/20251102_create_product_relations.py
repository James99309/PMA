"""创建产品关联表

Revision ID: 20251102_product_relations
Revises:
Create Date: 2025-11-02

业务说明:
- 创建 product_relations 表，用于配置产品之间的关联关系
- 支持子分类级别和产品级别的关联配置
- 用于报价单配置时自动提示配套产品（馈电模块、冷却风扇等）

变更内容:
1. 创建 product_relations 表
2. 添加索引优化查询性能

依赖:
- products 表必须存在

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251102_product_relations'
down_revision = '20251101_add_code_snapshot'
branch_labels = None
depends_on = None


def upgrade():
    """创建产品关联表"""

    # 创建 product_relations 表
    op.create_table(
        'product_relations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('main_product_type', sa.String(length=20), nullable=False,
                  comment='主产品类型: subcategory(子分类级) 或 product(产品级)'),
        sa.Column('main_product_id', sa.Integer(), nullable=False,
                  comment='主产品ID: 子分类ID或产品ID'),
        sa.Column('related_product_id', sa.Integer(), nullable=False,
                  comment='关联产品ID: 指向products表'),
        sa.Column('relation_type', sa.String(length=50), nullable=False,
                  comment='关联类型: required_accessory, optional_accessory, recommended, alternative'),
        sa.Column('display_name', sa.String(length=100), nullable=True,
                  comment='显示名称（可选，为空则使用产品名称）'),
        sa.Column('default_quantity', sa.Integer(), nullable=False, server_default='1',
                  comment='默认数量: 主产品1台对应多少台配件'),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default='0',
                  comment='是否必选配件'),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0',
                  comment='显示顺序: 数字越小越靠前'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1',
                  comment='是否启用'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'),
                  comment='创建时间'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['related_product_id'], ['products.id'],
                               name='fk_product_relations_related_product',
                               ondelete='CASCADE'),
        comment='产品关联配置表'
    )

    # 创建索引
    op.create_index('idx_product_relations_main', 'product_relations',
                    ['main_product_type', 'main_product_id'], unique=False)
    op.create_index('idx_product_relations_related', 'product_relations',
                    ['related_product_id'], unique=False)

    print("✅ product_relations 表创建成功")


def downgrade():
    """回滚：删除产品关联表"""

    # 删除索引
    op.drop_index('idx_product_relations_related', table_name='product_relations')
    op.drop_index('idx_product_relations_main', table_name='product_relations')

    # 删除表
    op.drop_table('product_relations')

    print("✅ product_relations 表已删除")
