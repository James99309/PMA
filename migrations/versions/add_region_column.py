"""Add region column to companies table

Revision ID: add_region_column
Revises: country_region_update
Create Date: 2025-05-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_region_column'
down_revision = 'country_region_update'  # 设置为上一个迁移版本
branch_labels = None
depends_on = None


def upgrade():
    # 检查companies表是否存在region列，如果不存在则添加
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [column['name'] for column in inspector.get_columns('companies')]
    
    if 'region' not in columns:
        op.add_column('companies', sa.Column('region', sa.String(50), nullable=True))
        print("成功添加region列到companies表")


def downgrade():
    # 此处不执行任何操作，因为我们不希望在回滚时删除region列
    # 如果真的需要删除，可以取消下面的注释
    # op.drop_column('companies', 'region')
    pass 

Revision ID: add_region_column
Revises: country_region_update
Create Date: 2025-05-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_region_column'
down_revision = 'country_region_update'  # 设置为上一个迁移版本
branch_labels = None
depends_on = None


def upgrade():
    # 检查companies表是否存在region列，如果不存在则添加
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [column['name'] for column in inspector.get_columns('companies')]
    
    if 'region' not in columns:
        op.add_column('companies', sa.Column('region', sa.String(50), nullable=True))
        print("成功添加region列到companies表")


def downgrade():
    # 此处不执行任何操作，因为我们不希望在回滚时删除region列
    # 如果真的需要删除，可以取消下面的注释
    # op.drop_column('companies', 'region')
    pass 