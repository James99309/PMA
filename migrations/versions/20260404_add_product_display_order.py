"""add product_display_order table

Revision ID: 4bd148e53cbe
Revises: dc05c44c29e9
Create Date: 2026-04-04 19:43:21.405895

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '4bd148e53cbe'
down_revision = 'dc05c44c29e9'
branch_labels = None
depends_on = None


def upgrade():
    # 检查表是否已存在（Flask create_all 可能已自动创建）
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'product_display_order' in inspector.get_table_names():
        # 表已存在，跳过建表，只填充数据
        _populate_data(conn)
        return

    # 创建 product_display_order 表
    op.create_table('product_display_order',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category_code', sa.String(length=1), nullable=False),
        sa.Column('category_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('subcategory_code', sa.String(length=1), nullable=False),
        sa.Column('subcategory_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('model_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('category_code', 'subcategory_code', 'model',
                            name='uq_display_order_cat_sub_model')
    )
    op.create_index('ix_display_order_cat_sub', 'product_display_order',
                     ['category_code', 'subcategory_code'], unique=False)

    _populate_data(op.get_bind())


def _populate_data(conn):
    """从现有分类/子分类/产品数据填充初始排序"""
    # 检查是否已有数据
    existing = conn.execute(sa.text(
        "SELECT EXISTS(SELECT 1 FROM product_display_order LIMIT 1)"
    )).scalar()
    if existing:
        return

    # 检查 product_categories 表是否有数据（SG 可能没有）
    has_data = conn.execute(sa.text(
        "SELECT EXISTS(SELECT 1 FROM product_categories LIMIT 1)"
    )).scalar()

    if not has_data:
        return

    categories = conn.execute(sa.text(
        "SELECT id, code_letter, display_order FROM product_categories ORDER BY display_order"
    )).fetchall()

    for cat in categories:
        subcategories = conn.execute(sa.text(
            "SELECT id, code_letter, display_order FROM product_subcategories "
            "WHERE category_id = :cid ORDER BY display_order"
        ), {'cid': cat[0]}).fetchall()

        for sub in subcategories:
            models = conn.execute(sa.text(
                "SELECT DISTINCT COALESCE(model, product_name, '未指定型号') as effective_model "
                "FROM products WHERE subcategory_id = :sid AND is_deleted = false "
                "ORDER BY effective_model"
            ), {'sid': sub[0]}).fetchall()

            for idx, m in enumerate(models):
                conn.execute(sa.text(
                    "INSERT INTO product_display_order "
                    "(category_code, category_order, subcategory_code, subcategory_order, "
                    "model, model_order, updated_at) "
                    "VALUES (:cc, :co, :sc, :so, :model, :mo, NOW())"
                ), {
                    'cc': cat[1], 'co': cat[2],
                    'sc': sub[1], 'so': sub[2],
                    'model': m[0], 'mo': idx + 1
                })


def downgrade():
    op.drop_index('ix_display_order_cat_sub', table_name='product_display_order')
    op.drop_table('product_display_order')
