"""add_prospect_stakeholder_extras_email_website_scope_alt_addrs

Revision ID: a9ef06d49c9d
Revises: prospect_tables_20260426
Create Date: 2026-04-26 12:04:14.149809

为 prospect_stakeholders 表新增 4 列以支持结构化的 AI 调研结果保存:
- email: 公司/部门通用邮箱
- website: 官网 URL
- business_scope: 主营业务/营业范围
- alternative_addresses: 备选地址(多个用换行分隔)
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a9ef06d49c9d'
down_revision = 'prospect_tables_20260426'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('prospect_stakeholders', schema=None) as batch_op:
        batch_op.add_column(sa.Column('email', sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column('website', sa.String(length=300), nullable=True))
        batch_op.add_column(sa.Column('business_scope', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('alternative_addresses', sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table('prospect_stakeholders', schema=None) as batch_op:
        batch_op.drop_column('alternative_addresses')
        batch_op.drop_column('business_scope')
        batch_op.drop_column('website')
        batch_op.drop_column('email')
