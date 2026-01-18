"""Add name_en field to product_code_fields table

Revision ID: add_product_code_field_name_en_20260118
Revises: add_product_names_en_20250117
Create Date: 2026-01-18 12:00:00.000000

数据库变更说明：
此迁移为 product_code_fields 表添加英文名称字段，用于区域信息的国际化支持。

字段变更：
1. 添加 product_code_fields.name_en - 字段名称（英文）

主要用于销售区域（origin_location 类型）的英文显示。
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_product_code_field_name_en_20260118'
down_revision = 'add_product_names_en_20250117'
branch_labels = None
depends_on = None


def upgrade():
    """添加 name_en 字段到 product_code_fields 表"""
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)

    # 检查 product_code_fields 表是否存在
    if 'product_code_fields' not in inspector.get_table_names():
        print("⏭️ product_code_fields 表不存在，跳过")
        return

    # 检查并添加 name_en 字段
    existing_cols = [col['name'] for col in inspector.get_columns('product_code_fields')]
    if 'name_en' not in existing_cols:
        op.add_column('product_code_fields',
                      sa.Column('name_en', sa.String(100), nullable=True))
        print("✅ 添加 product_code_fields.name_en 字段成功")
    else:
        print("⏭️ product_code_fields.name_en 字段已存在，跳过")


def downgrade():
    """回滚：删除 name_en 字段"""
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)

    # 检查 product_code_fields 表是否存在
    if 'product_code_fields' not in inspector.get_table_names():
        print("⏭️ product_code_fields 表不存在，跳过")
        return

    # 检查并删除 name_en 字段
    existing_cols = [col['name'] for col in inspector.get_columns('product_code_fields')]
    if 'name_en' in existing_cols:
        op.drop_column('product_code_fields', 'name_en')
        print("✅ 删除 product_code_fields.name_en 字段成功")
    else:
        print("⏭️ product_code_fields.name_en 字段不存在，跳过")
