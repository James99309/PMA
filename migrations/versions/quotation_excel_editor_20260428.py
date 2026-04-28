"""add row_type/section_label/sort_order to quotation_details + letterhead/signature to users

Revision ID: quotation_excel_editor_20260428
Revises: claude_ai_proxy_20260427
Create Date: 2026-04-28 12:30:00.000000

quotation_details 加 3 列（支持 Excel-like 编辑器：标注行 + 拖动排序）:
  - row_type        VARCHAR(16) DEFAULT 'product'  行类型：product / section
  - section_label   VARCHAR(255) NULL              标注行的文字（仅 row_type='section' 时使用）
  - sort_order      INTEGER NULL                   显式排序，平迁时设为 id

users 加 2 列（保存账户级默认抬头/签名）:
  - quotation_letterhead JSON NULL  {logo_url, line1, line2, line3}
  - quotation_signature  JSON NULL  {left, right}
"""
from alembic import op
import sqlalchemy as sa


revision = 'quotation_excel_editor_20260428'
down_revision = 'claude_ai_proxy_20260427'
branch_labels = None
depends_on = None


def upgrade():
    # quotation_details: 加 3 列
    with op.batch_alter_table('quotation_details', schema=None) as batch_op:
        batch_op.add_column(sa.Column('row_type', sa.String(length=16), nullable=False, server_default='product'))
        batch_op.add_column(sa.Column('section_label', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('sort_order', sa.Integer(), nullable=True))

    # 平迁：sort_order = id（保留现有顺序）
    op.execute("UPDATE quotation_details SET sort_order = id WHERE sort_order IS NULL")

    # 加索引（按 quotation_id + sort_order 查）
    op.create_index('ix_quotation_details_quotation_sort', 'quotation_details', ['quotation_id', 'sort_order'])

    # users: 加 letterhead / signature
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('quotation_letterhead', sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column('quotation_signature', sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('quotation_signature')
        batch_op.drop_column('quotation_letterhead')

    op.drop_index('ix_quotation_details_quotation_sort', table_name='quotation_details')

    with op.batch_alter_table('quotation_details', schema=None) as batch_op:
        batch_op.drop_column('sort_order')
        batch_op.drop_column('section_label')
        batch_op.drop_column('row_type')
