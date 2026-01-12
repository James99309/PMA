"""add project address fields

Revision ID: add_project_address_fields_20260111
Revises:
Create Date: 2026-01-11

添加项目地址相关字段：address, country, region, city
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_project_address_fields_20260111'
down_revision = 'add_order_module_tables_20260110'
branch_labels = None
depends_on = None


def upgrade():
    """添加项目地址字段"""
    # 检查并添加 address 字段
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('projects')]

    if 'address' not in columns:
        op.add_column('projects', sa.Column('address', sa.String(500), nullable=True))
        print("✓ 已添加 address 字段")
    else:
        print("- address 字段已存在，跳过")

    if 'country' not in columns:
        op.add_column('projects', sa.Column('country', sa.String(10), nullable=True))
        print("✓ 已添加 country 字段")
    else:
        print("- country 字段已存在，跳过")

    if 'region' not in columns:
        op.add_column('projects', sa.Column('region', sa.String(100), nullable=True))
        print("✓ 已添加 region 字段")
    else:
        print("- region 字段已存在，跳过")

    if 'city' not in columns:
        op.add_column('projects', sa.Column('city', sa.String(100), nullable=True))
        print("✓ 已添加 city 字段")
    else:
        print("- city 字段已存在，跳过")


def downgrade():
    """移除项目地址字段"""
    op.drop_column('projects', 'city')
    op.drop_column('projects', 'region')
    op.drop_column('projects', 'country')
    op.drop_column('projects', 'address')
