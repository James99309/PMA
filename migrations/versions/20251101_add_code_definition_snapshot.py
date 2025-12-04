"""添加产品编码定义快照字段

Revision ID: 20251101_add_code_snapshot
Revises: add_quotation_currency_20251031
Create Date: 2025-11-01 10:00:00.000000

添加code_definition_snapshot字段到products表，用于永久保存产品编码的完整定义
避免编码表变化导致历史产品编码含义丢失
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision = '20251101_add_code_snapshot'
down_revision = 'add_quotation_currency_20251031'
branch_labels = None
depends_on = None


def upgrade():
    """添加 code_definition_snapshot 字段到 products 表"""
    from sqlalchemy import inspect
    bind = op.get_bind()
    inspector = inspect(bind)
    existing_columns = [col['name'] for col in inspector.get_columns('products')]

    # 添加 JSON 字段存储编码定义快照
    if 'code_definition_snapshot' not in existing_columns:
        op.add_column('products',
            sa.Column('code_definition_snapshot', JSON, nullable=True)
        )
        print("✅ 已添加 code_definition_snapshot 字段到 products 表")
    else:
        print("⏭️ code_definition_snapshot 字段已存在，跳过")


def downgrade():
    """移除 code_definition_snapshot 字段"""
    op.drop_column('products', 'code_definition_snapshot')
    print("⚠️  已移除 code_definition_snapshot 字段")
