"""Add English fields (name_en) for product classification

Revision ID: add_product_names_en_20250117
Revises: add_expense_attributed_to_id_20260117
Create Date: 2026-01-17 12:30:00.000000

数据库变更说明：
此迁移仅添加中英文双语字段支持，支持产品分类的国际化需求。

字段变更：
1. 添加 product_categories.name_en - 分类的英文名称
2. 添加 product_subcategories.name_en - 子分类的英文名称

本地数据库专有 - 不影响云端 SP8D 数据库

注：ProductName 模型（product_names表）已删除，因为产品名称应该通过
ProductSubcategory.name 承载，而不是作为独立表管理。
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_product_names_en_20250117'
down_revision = 'add_expense_attributed_to_id_20260117'
branch_labels = None
depends_on = None


def upgrade():
    """添加英文名称字段"""
    from sqlalchemy import inspect

    bind = op.get_bind()
    inspector = inspect(bind)

    # 1. 检查并添加 product_categories 表的 name_en 字段
    existing_cols = [col['name'] for col in inspector.get_columns('product_categories')]
    if 'name_en' not in existing_cols:
        op.add_column('product_categories',
                      sa.Column('name_en', sa.String(100), nullable=True))
        print("✅ 添加 product_categories.name_en 字段成功")
    else:
        print("⏭️ product_categories.name_en 字段已存在，跳过")

    # 2. 检查并添加 product_subcategories 表的 name_en 字段
    existing_cols = [col['name'] for col in inspector.get_columns('product_subcategories')]
    if 'name_en' not in existing_cols:
        op.add_column('product_subcategories',
                      sa.Column('name_en', sa.String(100), nullable=True))
        print("✅ 添加 product_subcategories.name_en 字段成功")
    else:
        print("⏭️ product_subcategories.name_en 字段已存在，跳过")


def downgrade():
    """回滚：删除新字段和表"""

    # 1. 删除 product_names 表（由 SQLAlchemy 自动创建的）
    op.drop_table('product_names')

    # 2. 删除 product_subcategories 的 name_en 字段
    op.drop_column('product_subcategories', 'name_en')

    # 3. 删除 product_categories 的 name_en 字段
    op.drop_column('product_categories', 'name_en')
