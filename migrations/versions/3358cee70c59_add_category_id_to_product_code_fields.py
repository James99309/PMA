
"""add_category_id_to_product_code_fields

Revision ID: 3358cee70c59
Revises: 77cc9d8fabcc
Create Date: 2025-11-29 12:28:12.789997

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3358cee70c59'
down_revision = '77cc9d8fabcc'
branch_labels = None
depends_on = None


def upgrade():
    # 检查列是否已存在
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('product_code_fields')]

    # 添加 category_id 列
    if 'category_id' not in columns:
        op.add_column('product_code_fields',
            sa.Column('category_id', sa.Integer(), nullable=True)
        )
        print("✅ 添加 category_id 列成功")
    else:
        print("⏭️ category_id 列已存在，跳过")

    # 检查外键约束是否已存在
    from sqlalchemy import text
    result = conn.execute(text("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name = 'product_code_fields'
        AND constraint_type = 'FOREIGN KEY'
        AND constraint_name = 'fk_product_code_fields_category_id'
    """))
    fk_exists = result.fetchone() is not None

    # 添加外键约束
    if not fk_exists:
        op.create_foreign_key(
            'fk_product_code_fields_category_id',
            'product_code_fields', 'product_categories',
            ['category_id'], ['id']
        )
        print("✅ 添加外键约束成功")
    else:
        print("⏭️ 外键约束已存在，跳过")


def downgrade():
    # 删除外键约束
    op.drop_constraint('fk_product_code_fields_category_id', 'product_code_fields', type_='foreignkey')
    # 删除列
    op.drop_column('product_code_fields', 'category_id')