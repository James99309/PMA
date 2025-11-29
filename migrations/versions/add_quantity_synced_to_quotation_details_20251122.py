"""add quantity_synced to quotation_details

Revision ID: add_quantity_synced_20251122
Revises: 20251115_add_spec_dict_display_order
Create Date: 2025-11-22

添加 quantity_synced 字段到 quotation_details 表
用于记录配置产品是否同步主产品数量
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_quantity_synced_20251122'
down_revision = '20251115_add_spec_dict_display_order'
branch_labels = None
depends_on = None


def upgrade():
    # 检查列是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('quotation_details')]

    # 添加 quantity_synced 字段，默认值为 True（同步）
    if 'quantity_synced' not in columns:
        op.add_column('quotation_details',
            sa.Column('quantity_synced', sa.Boolean(),
                      nullable=False, server_default='1'))
        print('✅ 成功添加 quantity_synced 字段到 quotation_details 表')
    else:
        print('⏭️ quantity_synced 字段已存在，跳过')


def downgrade():
    # 回滚：删除 quantity_synced 字段
    op.drop_column('quotation_details', 'quantity_synced')
    print('✅ 成功删除 quantity_synced 字段从 quotation_details 表')
