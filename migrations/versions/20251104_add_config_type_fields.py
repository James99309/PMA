"""为报价单明细添加配置产品类型和基础数量字段

Revision ID: 20251104_config_type
Revises: 20251103_add_mutual_exclusion_group
Create Date: 2025-11-04

业务说明:
- 扩展已有的配置产品功能，添加配置类型和基础数量跟踪
- 配合产品关联系统，支持必选、推荐、互斥等配置类型
- 支持配置数量自动计算（主产品数量 × 配置基础数量）

变更内容:
1. 添加 config_type 字段 - 配置类型（必选/推荐/互斥等）
2. 添加 config_base_quantity 字段 - 配置基础数量

依赖:
- quotation_details 表必须存在
- parent_item_id, is_accessory, is_editable 字段已存在（由 20251102_extend_quotation_details 创建）

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251104_config_type'
down_revision = '20251103_mutual_exclusion'
branch_labels = None
depends_on = None


def upgrade():
    """添加配置产品类型和基础数量字段"""
    from sqlalchemy import inspect, text
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = [col['name'] for col in inspector.get_columns('quotation_details')]

    # 添加 config_type 字段
    if 'config_type' not in existing_columns:
        op.add_column('quotation_details',
                      sa.Column('config_type', sa.String(50), nullable=True,
                               comment='配置类型: required_accessory/required_mutual/recommended/optional_mutual'))
        print("✅ 添加 config_type 字段成功")
    else:
        print("⏭️ config_type 字段已存在，跳过")

    # 添加 config_base_quantity 字段
    if 'config_base_quantity' not in existing_columns:
        op.add_column('quotation_details',
                      sa.Column('config_base_quantity', sa.Integer(), nullable=True,
                               comment='配置基础数量（用于计算: 主产品数量 × 配置基础数量）'))
        print("✅ 添加 config_base_quantity 字段成功")
    else:
        print("⏭️ config_base_quantity 字段已存在，跳过")

    # 添加索引以提升查询性能
    result = bind.execute(text("SELECT indexname FROM pg_indexes WHERE tablename = 'quotation_details' AND indexname = 'idx_quotation_details_config_type'"))
    if not result.fetchone():
        op.create_index('idx_quotation_details_config_type', 'quotation_details',
                        ['config_type'], unique=False)
        print("✅ 创建索引 idx_quotation_details_config_type 成功")
    else:
        print("⏭️ 索引 idx_quotation_details_config_type 已存在，跳过")


def downgrade():
    """回滚：删除配置字段"""

    # 删除索引
    op.drop_index('idx_quotation_details_config_type', table_name='quotation_details')

    # 删除列
    op.drop_column('quotation_details', 'config_base_quantity')
    op.drop_column('quotation_details', 'config_type')

    print("✅ quotation_details 表配置字段已回滚")
