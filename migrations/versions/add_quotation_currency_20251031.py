"""add quotation_currency to projects table

Revision ID: add_quotation_currency_20251031
Revises: unify_performance_targets_constraints
Create Date: 2025-10-31 00:00:00.000000

添加quotation_currency字段到projects表，用于存储最新报价单的货币类型
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_quotation_currency_20251031'
down_revision = 'c9a7b9ea3a42'  # add_source_field_to_company
branch_labels = None
depends_on = None


def upgrade():
    """添加quotation_currency字段"""
    # 添加字段
    op.add_column('projects', sa.Column('quotation_currency', sa.String(length=10), nullable=True, server_default='CNY'))

    # 从现有报价单更新货币字段
    op.execute("""
        UPDATE projects
        SET quotation_currency = (
            SELECT COALESCE(currency, 'CNY')
            FROM quotations
            WHERE project_id = projects.id
            ORDER BY created_at DESC
            LIMIT 1
        )
        WHERE EXISTS (
            SELECT 1 FROM quotations WHERE project_id = projects.id
        )
    """)


def downgrade():
    """移除quotation_currency字段"""
    op.drop_column('projects', 'quotation_currency')
