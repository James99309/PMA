"""add include_in_description to spec_template_items

为模板规格项增加"加入描述"开关（与参与编码解耦）。
存量数据按产品库中衍生产品的实际描述勾选回填：
  - 有衍生产品规格时，按多数票决定（平票回退 use_in_code）
  - 无衍生产品时，回退 use_in_code

Revision ID: spec_item_include_in_desc_20260609
Revises: product_pdf_original_name_20260608
Create Date: 2026-06-09

"""
from alembic import op
import sqlalchemy as sa

revision = 'spec_item_include_in_desc_20260609'
down_revision = 'product_pdf_original_name_20260608'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 新增列（默认 false，非空）
    op.add_column(
        'spec_template_items',
        sa.Column('include_in_description', sa.Boolean(),
                  nullable=False, server_default=sa.text('false'))
    )

    # 2. 存量回填：先默认沿用 use_in_code
    op.execute("""
        UPDATE spec_template_items
        SET include_in_description = COALESCE(use_in_code, false)
    """)

    # 3. 用产品库中衍生产品的实际描述勾选修正（仅在有明确多数时覆盖，平票/无数据保留 use_in_code）
    op.execute("""
        WITH agg AS (
            SELECT sti.id AS item_id,
                   COUNT(ps.id) AS total,
                   COUNT(ps.id) FILTER (WHERE ps.include_in_description) AS incl
            FROM spec_template_items sti
            JOIN specification_dictionary sd ON sd.id = sti.spec_dict_id
            JOIN product_configurations pc ON pc.template_id = sti.template_id
            JOIN products p ON p.source_configuration_id = pc.id
            JOIN product_specs ps ON ps.product_id = p.id AND ps.field_name = sd.name
            GROUP BY sti.id
        )
        UPDATE spec_template_items sti
        SET include_in_description = (agg.incl * 2 > agg.total)
        FROM agg
        WHERE sti.id = agg.item_id
          AND agg.total > 0
          AND agg.incl * 2 <> agg.total
    """)


def downgrade():
    op.drop_column('spec_template_items', 'include_in_description')
