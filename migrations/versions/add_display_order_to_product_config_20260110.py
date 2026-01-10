"""add display_order to product_configurations

Revision ID: add_display_order_to_config
Revises: remove_ai_prompt_fields
Create Date: 2026-01-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_display_order_to_config'
down_revision = 'remove_ai_prompt_fields'
branch_labels = None
depends_on = None


def upgrade():
    """添加 display_order 字段到 product_configurations 表"""
    # 添加 display_order 字段，默认值为0
    op.add_column('product_configurations',
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='0'))

    # 为现有数据设置初始排序值（按创建时间顺序，每个模板内独立编号）
    # PostgreSQL语法
    conn = op.get_bind()
    conn.execute(sa.text("""
        WITH ranked AS (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY template_id ORDER BY created_at) - 1 as row_num
            FROM product_configurations
        )
        UPDATE product_configurations
        SET display_order = ranked.row_num
        FROM ranked
        WHERE product_configurations.id = ranked.id
    """))


def downgrade():
    """移除 display_order 字段"""
    op.drop_column('product_configurations', 'display_order')
